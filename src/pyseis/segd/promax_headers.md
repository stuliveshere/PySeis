# ProMAX / SeisSpace SEG-Y Input — Default Header Reference

Reference of the ProMAX / SeisSpace trace headers that the **SEG-Y Input** tool
populates by default. This is the target header set used on the left-hand side
of the gather-keyed `mappings:` tables in
`etc/segd/rev<X.Y>/<manufacturer>/{standard,versionNNN}.map.yaml`.

Source: [javadocs/segd/SegYInput.pdf](../../javadocs/segd/SegYInput.pdf)

---

## 1. Ensemble-grouping headers

SEG-Y Input can group traces into ensembles by any one of these headers (set
by the operator at import time):

| Header      | Purpose                                                    |
|-------------|------------------------------------------------------------|
| `FFID`      | File / field record number — shot gathers                  |
| `CDP`       | Common depth point number — CDP gathers                    |
| `SOURCE`    | Sequential source number — shot gathers                    |
| `SOU_XD`    | Source X coordinate (changes) — shot gathers               |
| `SOU_YD`    | Source Y coordinate (changes) — shot gathers               |
| `REC_XD`    | Receiver X coordinate (changes) — receiver gathers         |
| `REC_YD`    | Receiver Y coordinate (changes) — receiver gathers         |
| `OFFSET`    | Source-receiver offset — common offset gathers             |
| *(NONE)*    | Keep the SEG-Y file's native ensemble boundaries           |

Any header used for ensembling must be populated correctly on import or
downstream sorts will be wrong.

---

## 2. Default SEG-Y trace header → SeisSpace mapping

The SEG-Y standard trace header is 240 bytes. SeisSpace's default behaviour
for each byte range:

### 2.1 Populated trace headers

| Bytes   | SEG-Y meaning                         | SeisSpace header |
|---------|---------------------------------------|------------------|
| 9-12    | Original field record number          | `FFID`           |
| 13-16   | Trace number within field record      | `CHAN`           |
| 17-20   | Energy source point number            | `SOURCE`         |
| 21-24   | CDP ensemble number                   | `CDP`            |
| 29-30   | Trace identification code             | `TRC_TYPE`       |
| 33-34   | Horizontally stacked traces (fold)    | `TR_FOLD`        |
| 37-40   | Distance source → receiver            | `OFFSET`, `AOFFSET` |
| 41-44   | Receiver group elevation              | `REC_ELEV`       |
| 45-48   | Surface elevation at source           | `SOU_ELEV`       |
| 49-52   | Source depth below surface            | `DEPTH`          |
| 61-64   | Water depth at source                 | `SOU_H2OD`       |
| 65-68   | Water depth at receiver               | `REC_H2OD`       |
| 73-76   | Source X coordinate                   | `SOU_XD` (8-byte real, ~7-digit precision) |
| 77-80   | Source Y coordinate                   | `SOU_YD` (8-byte real) |
| 81-84   | Receiver X coordinate                 | `REC_XD` (8-byte real) |
| 85-88   | Receiver Y coordinate                 | `REC_YD` (8-byte real) |
| 95-96   | Uphole time at source                 | `UPHOLE`         |
| 99-100  | Source static correction              | `SOU_STAT`       |
| 101-102 | Receiver static correction            | `REC_STAT`       |
| 103-104 | Total static applied                  | `TOT_STAT`       |
| 111-112 | Mute time start                       | `TLIVE_S`        |
| 113-114 | Mute time end                         | `TFULL_S`        |

### 2.2 Read but not stored as a trace header

| Bytes   | SEG-Y meaning                     | Effect                              |
|---------|-----------------------------------|-------------------------------------|
| 69-70   | Scalar for bytes 41-68            | Applied on input; computed on output |
| 71-72   | Scalar for bytes 73-88            | Applied on input; computed on output |
| 89-90   | Coordinates units                 | Goes to dataset **data context**    |
| 115-116 | Samples per trace                 | Goes to data context (cannot vary)  |
| 117-118 | Sample interval                   | Goes to data context (cannot vary)  |
| 169-170 | Trace weighting factor            | Used only for 16/32-bit integer formats |
| 181-240 | Optional use (60 bytes)           | Carried through transparently       |

### 2.3 Ignored on input (60 + bytes)

`1-4` (trace seq within line), `5-8` (trace seq within reel), `25-28` (trace
within CDP), `31-32` (vertically summed), `35-36` (prod/test flag), `53-56`
(datum elev at rec), `57-60` (datum elev at src), `91-94` (weathering vel),
`97-98` (uphole at rec), `105-110` (lag times A/B, delay), `119-156` (gain &
sweep metadata), `157-168` (year / day / h / m / s / time basis), `171-178`
(geophone roll / group indices, gap size), `179-180` (overtravel taper).

These are still present in the SEG-Y file; SeisSpace just doesn't bind them
to a named header. Several of them are useful metadata we may want to expose
via custom-header mapping (see §4).

---

## 3. Trace format options (SEG-Y binary reel header)

The sample format is declared in the 400-byte binary reel header but can be
overridden at import time. Supported formats:

- **IBM Real** — 4-byte IBM floating point (traditional SEG-Y)
- **IEEE Real** — 4-byte IEEE floating point (non-standard but common)
- **4 byte Integer** — 4-byte signed integer
- **2 byte Integer** — 2-byte signed integer
- **4 byte w/Gain** — 4-byte fixed-point with gain code

SmartSolo SEG-D uses format code `0x8058` = 32-bit IEEE float, which maps
cleanly to **IEEE Real** when rewritten as SEG-Y.

---

## 4. Non-standard / custom header mapping  *(future UI work)*

SeisSpace's SEG-Y Input exposes a **Non-Standard Headers** submenu that lets
the operator define additional trace-header bindings. Per-override fields:

| Parameter                              | Purpose                              |
|----------------------------------------|--------------------------------------|
| *Starting byte number*                 | 1-240 within the SEG-Y trace header  |
| *Format of the non-standard header*    | `4 byte Integer` / `2 byte Integer` / `IEEE Float` / `IBM Float` |
| *Output SeisSpace header*              | Pick existing, or type a new name    |
| *New header description* (if user-defined) | Free-text description             |
| *New header format*                    | `4 byte Integer` / `8 byte Integer` / `4 byte Float` / `2 byte Float` |

We will need the same override capability for SmartSolo SEG-D import so the
operator can:

1. **Add** a mapping for a SEG-D field we haven't bound in
   `versionNNN.yaml` (e.g. a site-specific field in a trace extension).
2. **Override** a default mapping for a given job (e.g. pull `SOURCE` from
   an alternate location because the default is zero in this vintage of
   files).
3. **Define** a new SeisSpace header that doesn't exist in the standard set.

### 4.1 UI sketch — deferred

The dialog needs at minimum:

- Block selector (e.g. `general_header_3`, `external_header`, `extension_1`)
- Byte offset within the block
- Field type (from `FieldType` enum: BCD, integer widths, IEEE, etc.)
- Target SeisSpace header name — dropdown of existing + free-text for new
- Override semantics — "add" vs "replace default binding"

Exact layout and wiring belong in a later design pass. This section is a
placeholder so the requirement is tracked alongside the default-header
reference.

### 4.2 Interaction with the schema stack

Custom mappings should layer on top of the YAML-declared `mappings:` bindings
the same way the variant map layers on top of the mfr standard map. Two
reasonable shapes:

- **Per-run overrides** — carried in the import-tool parameter set, stored
  with the imported dataset's metadata.
- **Local YAML fragment** — written to a user-owned directory and merged
  as a final `.map.yaml` layer after `versionNNN.map.yaml`.

The second form is more portable (reproducible imports) but heavier. To
decide when the UI work lands.

---

## 5. Cross-reference — SEG-D → ProMAX concept sources

Placeholder table to fill in once `resolvers:` lands in the SmartSolo schema
(see `quirky-singing-pascal.md` Step 4):

| ProMAX header | SEG-D source (SmartSolo Rev 2.1)                                  | Notes |
|---------------|-------------------------------------------------------------------|-------|
| `FFID`        | `general_header_2.expanded_file_number`                           |       |
| `CHAN`        | `demux_trace_header.trace_number`                                 |       |
| `TRC_TYPE`    | `channel_set_descriptor.channel_type`                             |       |
| `SOURCE`      | (Source point number — from GH3 or extended header)               | TBD   |
| `CDP`         | Not in SEG-D field record; computed downstream                    |       |
| `SOU_XD`      | `external_header.source_easting` (in cm; scale to metres)         | SG only |
| `SOU_YD`      | `external_header.source_northing`                                 | SG only |
| `SOU_ELEV`    | `external_header.source_elevation`                                |       |
| `REC_XD`      | `receiver_coords` trace-ext block                                 | RG/CG or per-trace |
| `REC_YD`      | `receiver_coords` trace-ext block                                 |       |
| `OFFSET`      | Computed from source + receiver coordinates                       |       |
| `UPHOLE`      | TBD — field present in some firmware variants                     |       |
| `SOU_STAT`, `REC_STAT`, `TOT_STAT` | Not in SEG-D; defaulted on import                |       |
| `TLIVE_S`, `TFULL_S` | Derived from CSD start/end time                            |       |
| (sample interval, sample count) | `file_extended_header.sample_rate_us`, `file_extended_header.samples_per_trace` | data context, not header |

Fill out as the resolver schema matures.
