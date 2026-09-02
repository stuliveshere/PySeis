# etc/segd — SEG-D standard and manufacturer extension tables

YAML files that drive the SmartSolo (and future) manufacturer plugins in the
Java SEG-D Reader (epic
[#16](https://github.com/velseis/velpro-seisspace-plugin/issues/16)).

**Status:** this directory is the authoritative specification until the Java
reader is written. Field tables here are transcribed from the SEG-D standard
PDFs under `javadocs/segd/` and will be validated against real SmartSolo
`.segd` files once the reader exists.

---

## 5-layer loading architecture

For every SEG-D file the Java loader applies two parallel stacks of YAML
layers — **structural** and **mapping** — merged in load order. Structural
layers describe the on-wire header format; mapping layers describe how
fields bind to ProMAX/SeisSpace header words.

```
── Structural stack ───────────────────────────────────────────────────────────
rev<n>/base.yaml                       ← SEG-D standard blocks (GH1, GH2, channel set, demux trace, …)
        ↓ merge
rev<n>/<manufacturer>/standard.yaml    ← manufacturer-common structural overrides (non-standard GH,
                                         file/external headers, common trace-extension blocks)
        ↓ merge
rev<n>/<manufacturer>/versionNNN.yaml  ← firmware-variant structural deltas, version_signal, firmware labels

── Mapping stack ──────────────────────────────────────────────────────────────
rev<n>/<manufacturer>/standard.map.yaml     ← manufacturer-common ProMAX bindings + resolvers
        ↓ merge
rev<n>/<manufacturer>/versionNNN.map.yaml   ← firmware-variant mapping deltas

        ═══════════════
        effective Schema   (flat ordered list of blocks and fields,
                            plus gather-keyed resolvers and mappings)
```

Variant files carry only the *delta* from the layer above. Structural layers
own `blocks:`, `trace_extensions:`, `gather_type:`, `version_signal:`.
Mapping layers own `resolvers:` and `mappings:` — and **only** those keys.
This separation means a variant that changes byte layout without changing
ProMAX bindings touches only its `versionNNN.yaml`, and a re-binding pass
across firmwares touches only the `.map.yaml` files.

**Java bootstrap** (≈15 lines, no YAML required):

```java
int manufacturerCode = bcd(buf, 16);          // GH1 byte 17 (0-based)
String segdRevision  = bcdRevision(buf, 10);  // GH2 bytes 11-12 (0-based)

SchemaSpec base     = loader.loadBase(segdRevision);
SchemaSpec standard = loader.loadStandard(manufacturerCode, segdRevision);
SchemaSpec variant  = selector.select(base, standard, buf);
Schema effective    = Schema.merge(base, standard, variant);
// All remaining parsing is table-driven from effective
```

`selector.select()` probes each candidate variant's `version_signal`; if
unique → auto-select; if ambiguous → default to latest + GUI confirm.

---

## Directory layout

```
etc/segd/
  README.md                                 ← this file (the spec)
  rev1.0/
    base.yaml                               SEG-D 1.0 standard blocks
    smartsolo/
      standard.yaml                         SmartSolo Rev1.0-on-wire common structural
      standard.map.yaml                     SmartSolo Rev1.0 common ProMAX bindings     (TBD)
      version001.yaml                       firmware 1.0 spec v1; GH2="1.0"; AUTO-DETECT
      version001.map.yaml                   mapping deltas for v1 (if any)              (TBD)
  rev2.1/
    base.yaml                               SEG-D 2.1 standard blocks
    smartsolo/
      standard.yaml                         SmartSolo Rev2.1-on-wire common structural
      standard.map.yaml                     SmartSolo Rev2.1 common ProMAX bindings
      version001.yaml                       firmware 2.1 spec v1 (no SPS)
      version002.yaml                       firmware 1.0/2.1 spec v2 (byte-identical); DEFAULT
      version002.map.yaml                   SPS_X/Y/Z mapping deltas for v2
  rev3.1/
    base.yaml                               SEG-D 3.1 standard blocks (GH3-GH8 Timestamp/Vessel/…)
    smartsolo/
      standard.yaml                         SmartSolo Rev3.1-on-wire common structural
      standard.map.yaml                     SmartSolo Rev3.1 common ProMAX bindings     (TBD)
      version001.yaml                       firmware 3.1 spec v1; GH2 byte 11=3; AUTO-DETECT
      version001.map.yaml                   mapping deltas for v1 (if any)              (TBD)
```

Variant filenames use `version<NNN>.yaml` — a zero-padded sequence within each
`rev<X.Y>/<manufacturer>/` directory. Higher numbers = newer firmware specs.
The mapping from a variant file to the real-world firmware label(s) it covers
lives in the YAML's `firmware_labels:` list (e.g. `fw2.1_v2`, `fw1.0_v2`).

---

## Schema v2 specification

### Top-level keys

Layer column values: `base` = SEG-D `rev<n>/base.yaml`; `standard` = manufacturer
`<mfr>/standard.yaml`; `version` = firmware variant `<mfr>/versionNNN.yaml`;
`map` = any `.map.yaml` file; `structural` = any of base/standard/version;
`any` = any layer.

| Key | Applies to | Type | Purpose |
|---|---|---|---|
| `id` | version | string | Stable identifier used by the variant selector |
| `extends` | structural | string | Relative path to parent schema (optional; load order usually makes this implicit) |
| `firmware_labels` | version | list | Operator-facing labels when a single wire format represents multiple firmware generations |
| `manufacturer`, `manufacturer_alias`, `code`, `format_codes` | standard | scalar/list | Identification and manufacturer-code lookup |
| `status` | any | string | `placeholder` = schema is incomplete; loader logs warning |
| `version_signal` | version | map | Byte pattern that uniquely identifies this variant for auto-selection |
| `gather_type` | standard | map | Where and how to read the SG/RG/CG gather-type flag |
| `resolvers` | map | map | Canonical source for each logical structural concept (gather-type keyed) |
| `mappings` | map | map | ProMAX/SeisSpace header bindings (gather-type keyed); see "Mapping rules" below |
| `blocks` | structural | map | Role-keyed block definitions; see "Blocks" below |
| `trace_extensions` | structural | map | Per-trace extension sub-schema with `count`, `block_size`, `blocks` |
| `computed` | base | list | Values derived from multiple blocks (e.g. NCHANS = Σ channel_count) |

### Blocks

Blocks are keyed by **role** (semantic name), not by number. The block
number is metadata — when a role shifts blocks between revisions, reader
code still looks it up by role.

```yaml
blocks:
  general_header_1:
    number: 1
    size: 32
    reserved:
      - { offset: 19, length: 3, note: "spec: not used; record as zero" }
    fields: [...]
  external_header:
    size: 1024
    fields: [...]
```

**Multiple roles per `number:`** — Trace-extension blocks may split a single
32-byte block number into two adjacent roles at non-overlapping byte ranges.
SmartSolo Rev3.1 uses this for its block 7, which carries both `igu_gps`
(offsets 0–15) and `node_identification` (offsets 16–23):

```yaml
trace_extensions:
  blocks:
    igu_gps:
      number: 7
      fields: [...offsets 0-15...]
    node_identification:
      number: 7
      fields: [...offsets 16-23...]
```

The loader merges all roles sharing a `number:` into one physical block and
rejects overlapping byte ranges across them.

**Size inheritance** — A block inside `trace_extensions:` omits `size:` and
inherits it from `trace_extensions.block_size` (always 32 for SEG-D). Only
top-level `blocks:` entries declare `size:` directly.

Standard block roles (fixed vocabulary):

| Role | SEG-D block | Typical contents |
|---|---|---|
| `general_header_1` | GH1, 32 B | Year, Julian day, time, manufacturer code, format code |
| `general_header_2` | GH2, 32 B | SEG-D revision, expanded file number, extended counts |
| `general_header_3` … `general_header_9` | GH3–GH9, 32 B each | Standard in Rev3.1 (Timestamp, Vessel, Survey, Client, Job, Line ID); manufacturer-defined in Rev1.0/2.1 |
| `channel_set_descriptor` | 32 B (Rev2.1) / 96 B (Rev3.1) | Per-channel-set fields: TRC_TYPE, SEGDGAIN, CABLE_NO, CHAN_SET |
| `demux_trace_header` | 32 B | Per-trace fields: SCANTYPE, trace number, timing |
| `file_extended_header` | N × 32 B | Acquisition metadata (length, sample rate, trace counts) |
| `external_header` | N × 32 B | External file number, coordinates, GPS |

Trace-extension block roles (the order manufacturers tend to use):

| Role | Typical contents | SmartSolo revs |
|---|---|---|
| `receiver_geometry` | Receiver line/point (int + frac) | 1.0, 2.1, 3.1 |
| `tb_gps` | TB GPS time (µs) | 1.0, 2.1, 3.1 |
| `receiver_coords` | Receiver easting/northing/elevation (cm); source coords added in some variants | 1.0, 2.1, 3.1 |
| `igu_gps` | IGU GPS lat/lon/height | 1.0, 2.1, 3.1 |
| `node_identification` | Unit serial number (+ per-trace FFID in Rev3.1) | 1.0, 2.1, 3.1 |
| `sensor_info` | Sensor sensitivity, equipment test metadata | 3.1 |
| `time_drift` | Deployment/retrieval timestamps and drift correction | 3.1 |
| `orientation` | Sensor rotation angles around X/Y/Z | 3.1 |

In SmartSolo Rev3.1 `igu_gps` and `node_identification` share block
number 7 (see "Multiple roles per `number:`" above).

### Fields

```yaml
fields:
  - name: rcvr_easting_cm
    offset: 0            # bytes from start of block (0-based)
    length: 4
    type: int32
    description: "Receiver easting in cm → m (RG mode: source easting; CG suppressed)"
    spec_ref: "smartsolo v2 §3.4 p.12"
    after: rcvr_line_int  # optional: pin position in merged order
```

| Attribute | Required | Description |
|---|---|---|
| `name` | yes | snake_case, unique within the block |
| `offset` | yes | 0-based byte offset from block start |
| `length` | yes for numeric/string types | Width in bytes (inferred for `bcd_nibble`) |
| `type` | yes | One of the type vocabulary tokens (see below) |
| `nibble` | bcd_nibble only | `high` or `low` |
| `digits` | bcd_digits only | Number of BCD digits this field spans |
| `mapping`, `maps_to` | legacy — being removed | Inline ProMAX bindings. New code goes in `.map.yaml` files. Remaining instances in rev1.0/rev3.1 are scheduled for lift-out. |
| `fraction_of` | fractional field | Name of the integer field this scales against 65535 |
| `scale` | when output ≠ raw | Multiplier applied before emission (e.g. 0.01 for cm → m) |
| `description` | yes | **Must be a double-quoted string** (enforced) |
| `spec_ref` | recommended | Spec section/page reference for PDF cross-check |
| `after` | structural override only | Anchor field name to control ordering in the merged block |
| `replace` | block-level, structural override only | `true` → replace the parent block wholesale instead of field-merging |
| `values` | enum fields (uint8, bcd_nibble, …) | Map of `<raw-int>: <label>` pairs; see "Enum values" below |

A field without `mapping` and without `maps_to` is parsed for offset
tracking only. (`skip: true` from v1 is gone — absence of a mapping is the
same signal.)

### Enum values

Fields whose on-wire byte encodes one of a small set of coded values carry
a `values:` map of `<raw-int>: <snake_case_label>` pairs. The loader
exposes the label to the Java reader as a typed enum and logs a warning
(not an error) when an on-wire byte falls outside the declared set —
unknown codes are surfaced but don't abort parsing.

```yaml
- name: channel_type
  offset: 3
  type: uint8
  values:
    0x00: unused
    0x10: seis
    0x11: em
    0x20: time_break
    # ...
    0xF0: calibration
  description: "Channel type identification (per-channel-set)"
```

Labels are case-sensitive snake_case. Keys can be decimal or hex integers —
hex is recommended for byte-coded fields. For `bcd_nibble` fields, keys
range 0–15.

### Type vocabulary

| Type | Bytes | Decoding |
|---|---|---|
| `bcd_digits` | variable (`length`) | Packed BCD; N bytes → 2N decimal digits |
| `bcd_nibble` | shares a byte | 4 bits at `nibble: high`/`low` of the byte at `offset` |
| `int8`, `int16`, `int24`, `int32`, `int64` | 1/2/3/4/8 | Signed big-endian |
| `uint8`, `uint16`, `uint24`, `uint32`, `uint64` | 1/2/3/4/8 | Unsigned big-endian |
| `float32` | 4 | IBM float (rare) |
| `ieee_float` | 4 | IEEE 754 32-bit |
| `ascii` | variable (`length`) | Space-padded text, trimmed on read |

### Mapping rules

ProMAX/SeisSpace bindings live in `.map.yaml` files as a gather-keyed
`mappings:` table. Top level is `sg`/`rg`/`cg`; inside each gather mode
the keys are ProMAX header names and the values are either a plain
`block.field` reference or a `{field, scale, offset}` transform.

```yaml
# rev2.1/smartsolo/standard.map.yaml
mappings:
  sg:
    FFID:     general_header_2.expanded_file_number
    SOU_XD:   { field: external_header.source_easting_cm, scale: 0.01 }   # cm → m
  rg:
    REC_XD:   { field: external_header.source_easting_cm, scale: 0.01 }   # RG swap
  cg:
    FFID:     general_header_2.expanded_file_number
    # source/receiver position bindings omitted — neither concept applies in CG
```

SmartSolo's SG↔RG coordinate swap is expressed by the sg/rg blocks assigning
the same on-wire field to different ProMAX headers. Each gather mode is a
self-contained binding list — no shared-definition indirection.

Variant map files add deltas: new header bindings, or overrides of
standard-layer entries. Setting a value to `null` removes the binding.

`resolvers:` follows the same shape but maps *logical structural concepts*
(`ffid`, `sample_interval_micros`, `samples_per_trace`, …) to their canonical
on-wire field for each gather mode. Resolvers feed the reader and validator;
mappings feed the ProMAX import contract.

### Merge rules (v2)

Four rules replace the v1 Rules 1–5.

| Rule | Applies to | Behaviour |
|---|---|---|
| 1 | Top-level scalars (`status`, `gather_type`, `version_signal`, …) | Later layer wins |
| 2 | `blocks:` entries (role-keyed) | **Field-level union by `name`**; same-name field in a later layer overrides; new fields appended (anchored by `after:` if present). A block with `replace: true` uses v1 all-or-nothing replacement. Roles sharing a `number:` are merged as one physical block and must not overlap byte-wise. |
| 3 | `mappings:` / `resolvers:` (gather-keyed, then name-keyed) | Union per gather mode; later layer overrides same-name entries; explicit `null` value removes the binding |
| 4 | `trace_extensions.blocks` (role-keyed) | Rule 2 applied to each sub-block |

### Loader validation

At schema load time the loader **must** reject a schema that:

- Has overlapping byte ranges within a block (except where `bcd_nibble`
  fields deliberately share a byte at different nibbles).
- Has bytes within a block's declared `size:` that are neither covered by a
  field (including nibble-shared bytes) nor listed in `reserved:`.
- Has two roles at the same `number:` whose fields overlap byte-wise.
- Has a `mappings:` or `resolvers:` entry whose `block.field` target does
  not resolve against the merged structural schema.
- Has an `after:` anchor that does not exist in the merged block.
- Uses a `type:` token outside the fixed vocabulary above.
- Declares a `description:` that is not a double-quoted scalar.
- Declares a `values:` map on a field whose `type:` is not an integer
  vocabulary member (`int8`/`uint8`, `int16`/`uint16`, `int24`/`uint24`,
  `int32`/`uint32`, `int64`/`uint64`, or `bcd_nibble`).

These are startup guarantees, not runtime checks — a mis-specified schema
prevents the reader from starting at all. Unknown on-wire values for a
`values:`-mapped field are a runtime **warning**, not a startup error.

### Reserved ranges

Blocks declare `reserved:` for byte ranges the spec explicitly marks as
unused. The entry below says bytes 19–21 of GH1 are reserved:

```yaml
blocks:
  general_header_1:
    size: 32
    reserved:
      - { offset: 19, length: 3, note: "spec: not used; record as zero" }
    fields: [...]
```

A child layer (manufacturer standard or variant) may claim bytes that the
parent layer marked reserved — this is how SmartSolo uses GH1 byte 23's
low nibble for `gather_type` even though SEG-D marks the nibble unused.
Nibble-level reservations are not expressible in `reserved:` today; they
stay in comments and the byte appears as "shared" when an adjacent nibble
field is declared.

---

## Gather-type conditional mapping

SmartSolo swaps source/receiver semantics in RG and CG gather modes. The
loader reads `gather_type` from GH1 before processing any field, then the
reader uses the field's mapping rule:

```java
String target = switch (gatherType) {
    case RG -> mapping.rgMapsTo() != null ? mapping.rgMapsTo() : mapping.mapsTo();
    case CG -> mapping.cgMapsTo();   // null → suppress (don't write header)
    default -> mapping.mapsTo();
};
if (target != null) hdr.set(target, scaledValue);
```

The eight fields carrying all three targets across every SmartSolo variant:

| Block role | Field | SG → | RG → | CG → |
|---|---|---|---|---|
| `external_header` | `source_easting_cm` | `SOU_X` | `REC_X` | null |
| `external_header` | `source_northing_cm` | `SOU_Y` | `REC_Y` | null |
| `external_header` | `source_elevation_cm` | `SOU_ELEV` | `REC_ELEV` | null |
| `receiver_geometry` | `rcvr_line_int` | `R_LINE` | `S_LINE` | null |
| `receiver_geometry` | `rcvr_point_int` | `SRF_SLOC` | `SOU_SLOC` | null |
| `receiver_coords` | `rcvr_easting_cm` | `REC_X` | `SOU_X` | null |
| `receiver_coords` | `rcvr_northing_cm` | `REC_Y` | `SOU_Y` | null |
| `receiver_coords` | `rcvr_elevation_cm` | `REC_ELEV` | `SOU_ELEV` | null |

(Block roles, not block numbers — receiver coordinates are `block_3` in
Rev2.1 but `block_6` in Rev3.1; role keys let the reader ignore the drift.)

---

## Top-level helper maps

### `version_signal`

```yaml
version_signal:
  block: general_header_2   # role key
  offset: 10
  length: 1
  type: uint8
  value: 3
```

If absent, the variant cannot be auto-detected and requires operator override.

### `gather_type`

```yaml
gather_type:
  block: general_header_1
  offset: 23                # 0-based
  nibble: low               # low or high
  type: bcd_nibble
  values:
    0: SG
    1: RG
    2: CG
```

---

## Adding a new manufacturer

1. Find the SEG-D revision the manufacturer writes on the wire. If
   `rev<n>/base.yaml` does not yet exist, create it from the spec PDF.
2. Create `rev<n>/<manufacturer_lc>/standard.yaml` (structural):
   - Include `manufacturer`, `code`, `format_codes`, `gather_type` if applicable.
   - Add any non-standard additional GH blocks (GH3+).
   - Add `file_extended_header`, `external_header`, and any trace-extension
     blocks common to all variants.
3. Create `rev<n>/<manufacturer_lc>/standard.map.yaml` (ProMAX bindings):
   - Define `resolvers:` (canonical field per structural concept, per gather mode).
   - Define `mappings:` (ProMAX header → field, per gather mode).
4. Write one `versionNNN.yaml` per distinct wire format (not per firmware
   generation — collapse wire-identical firmwares into one file with a
   `firmware_labels:` list). Structural deltas only.
   - If auto-detectable, add a `version_signal`.
   - Otherwise, document the override requirement in the file header comment.
5. If the variant needs binding changes, add a paired `versionNNN.map.yaml`.
6. Register the manufacturer plugin in the Java `ServiceLoader` manifest.
7. Add a Phase 3 GitHub issue following the pattern of
   issue [#44](https://github.com/velseis/velpro-seisspace-plugin/issues/44).
