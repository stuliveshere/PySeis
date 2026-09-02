"""
5-Layer YAML Schema Engine, Merger, Auto-Detector, and Validator for SEG-D.
"""

from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# BCD Utilities
def bcd_nibble(byte_val: int, nibble: str) -> int:
    """Extract high or low nibble from a byte as integer (0-15)."""
    if nibble == "high":
        return (byte_val >> 4) & 0x0F
    elif nibble == "low":
        return byte_val & 0x0F
    else:
        raise ValueError(f"Invalid nibble specifier: '{nibble}', must be 'high' or 'low'")


def bcd_digits(buffer: bytes, offset: int, length: int) -> int:
    """Decode a range of bytes as packed BCD digits into an integer."""
    val = 0
    for i in range(length):
        b = buffer[offset + i]
        high = (b >> 4) & 0x0F
        low = b & 0x0F
        val = val * 100 + high * 10 + low
    return val


def bcd_to_hex(buffer: bytes, offset: int, length: int) -> int:
    """Decode a byte range as hex BCD value (e.g. 0x61 = 97 or hex integer)."""
    val = 0
    for i in range(length):
        val = (val << 8) | buffer[offset + i]
    return val


class FieldSpec:
    def __init__(self, name: str, offset: int, length: int = 1, field_type: str = "uint8", **kwargs):
        self.name = name
        self.offset = offset
        self.length = length
        self.type = field_type
        self.nibble: Optional[str] = kwargs.get("nibble")
        self.digits: Optional[int] = kwargs.get("digits")
        self.scale: float = float(kwargs.get("scale", 1.0))
        self.offset_val: float = float(kwargs.get("offset_val", kwargs.get("offset_adjustment", 0.0)))
        self.description: str = str(kwargs.get("description", ""))
        self.spec_ref: str = str(kwargs.get("spec_ref", ""))
        self.after: Optional[str] = kwargs.get("after")
        self.replace: bool = bool(kwargs.get("replace", False))
        self.values: Optional[Dict[Any, str]] = kwargs.get("values")
        self.extra: Dict[str, Any] = kwargs

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> FieldSpec:
        extra = {k: v for k, v in data.items() if k not in ("name", "offset", "length", "type")}
        return cls(
            name=data["name"],
            offset=data["offset"],
            length=data.get("length", 1),
            field_type=data.get("type", "uint8"),
            **extra
        )

    def to_dict(self) -> Dict[str, Any]:
        res = {
            "name": self.name,
            "offset": self.offset,
            "length": self.length,
            "type": self.type,
            "scale": self.scale,
            "description": self.description,
        }
        if self.nibble:
            res["nibble"] = self.nibble
        if self.values:
            res["values"] = self.values
        if self.after:
            res["after"] = self.after
        return res


    def read_value(self, buffer: bytes) -> Any:
        """Decode field value from raw buffer according to field spec type."""
        if self.offset + self.length > len(buffer):
            return 0
        if self.type in ("bcd_digits", "bcd"):
            return bcd_digits(buffer, self.offset, self.length)
        elif self.type == "bcd_nibble":
            return bcd_nibble(buffer[self.offset], self.nibble or "high")
        elif self.type == "uint8":
            return buffer[self.offset]
        elif self.type == "uint16":
            return (buffer[self.offset] << 8) | buffer[self.offset + 1]
        elif self.type == "uint24":
            return (buffer[self.offset] << 16) | (buffer[self.offset + 1] << 8) | buffer[self.offset + 2]
        elif self.type == "uint32":
            return (buffer[self.offset] << 24) | (buffer[self.offset + 1] << 16) | (buffer[self.offset + 2] << 8) | buffer[self.offset + 3]
        elif self.type == "int8":
            return int.from_bytes(buffer[self.offset:self.offset+1], byteorder="big", signed=True)
        elif self.type == "int16":
            return int.from_bytes(buffer[self.offset:self.offset+2], byteorder="big", signed=True)
        elif self.type == "int24":
            return int.from_bytes(buffer[self.offset:self.offset+3], byteorder="big", signed=True)
        elif self.type == "int32":
            return int.from_bytes(buffer[self.offset:self.offset+4], byteorder="big", signed=True)
        elif self.type == "ascii":
            return buffer[self.offset:self.offset+self.length].decode("ascii", errors="replace").strip()
        return 0


class BlockSpec:
    def __init__(self, name: str, number: Optional[int] = None, size: Optional[int] = None, fields: Optional[List[FieldSpec]] = None, reserved: Optional[List[Dict[str, Any]]] = None, replace: bool = False):
        self.name = name
        self.number = number
        self.size = size
        self.fields: List[FieldSpec] = fields or []
        self.reserved: List[Dict[str, Any]] = reserved or []
        self.replace = replace

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> BlockSpec:
        fields = [FieldSpec.from_dict(f) for f in data.get("fields", [])]
        return cls(
            name=name,
            number=data.get("number"),
            size=data.get("size"),
            fields=fields,
            reserved=data.get("reserved", []),
            replace=data.get("replace", False)
        )

    def parse_fields(self, buffer: bytes) -> Dict[str, Any]:
        """Parse all defined fields from a block buffer into a dict."""
        res = {}
        for f in self.fields:
            res[f.name] = f.read_value(buffer)
        return res


class EffectiveSchema:
    """Represents the fully merged, effective 5-layer SEG-D schema."""
    def __init__(self, revision: str, manufacturer: str, variant_id: str, blocks: Dict[str, BlockSpec], trace_extensions: Dict[str, Any], resolvers: Dict[str, Any], mappings: Dict[str, Any], metadata: Dict[str, Any]):
        self.revision = revision
        self.manufacturer = manufacturer
        self.variant_id = variant_id
        self.blocks = blocks
        self.trace_extensions = trace_extensions
        self.resolvers = resolvers
        self.mappings = mappings
        self.metadata = metadata

    def get_block_by_role(self, role: str) -> Optional[BlockSpec]:
        if role in self.blocks:
            return self.blocks[role]
        if self.trace_extensions and "blocks" in self.trace_extensions:
            if role in self.trace_extensions["blocks"]:
                return self.trace_extensions["blocks"][role]
        return None

    def get_mapping(self, gather_type: str = "sg") -> Dict[str, Any]:
        gather_key = gather_type.lower()
        if self.mappings and gather_key in self.mappings:
            return self.mappings[gather_key]
        return {}

    def get_resolvers(self, gather_type: str = "sg") -> Dict[str, Any]:
        gather_key = gather_type.lower()
        if self.resolvers and gather_key in self.resolvers:
            return self.resolvers[gather_key]
        return {}


class SchemaManager:
    """Manages loading, merging, validation, and auto-detecting SEG-D YAML schemas."""
    
    VALID_TYPES = {
        "bcd_digits", "bcd_nibble",
        "int8", "int16", "int24", "int32", "int64",
        "uint8", "uint16", "uint24", "uint32", "uint64",
        "float32", "float64", "ieee_float", "ascii"
    }

    # Standard manufacturer code mapping (Appendix A)
    MANUFACTURER_MAP = {
        0x61: "smartsolo",  # DTCC / SmartSolo (97 dec)
        97: "smartsolo",
        0x12: "sercel",     # Sercel (18 dec)
        18: "sercel",
        0x13: "sercel",     # Sercel (19 dec)
        19: "sercel",
        0x01: "io",         # Input/Output (1 dec)
        1: "io"
    }

    def __init__(self, schema_dir: Optional[Union[str, Path]] = None):
        if schema_dir is None:
            schema_dir = Path(__file__).parent
        self.schema_dir = Path(schema_dir)

    def load_yaml(self, rel_path: Union[str, Path]) -> Dict[str, Any]:
        full_path = self.schema_dir / rel_path
        if not full_path.exists():
            return {}
        with open(full_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def merge_block_fields(self, parent_fields: List[FieldSpec], child_fields: List[FieldSpec]) -> List[FieldSpec]:
        """Rule 2: Union fields by name with positional anchors ('after') and overrides."""
        merged: List[FieldSpec] = list(parent_fields)
        field_map = {f.name: idx for idx, f in enumerate(merged)}

        for child_f in child_fields:
            if child_f.name in field_map:
                # Override existing field
                idx = field_map[child_f.name]
                merged[idx] = child_f
            else:
                # Append or insert after specified anchor
                if child_f.after and child_f.after in field_map:
                    anchor_idx = field_map[child_f.after] + 1
                    merged.insert(anchor_idx, child_f)
                    # Rebuild map index
                    field_map = {f.name: idx for idx, f in enumerate(merged)}
                else:
                    merged.append(child_f)
                    field_map[child_f.name] = len(merged) - 1

        return merged

    def merge_blocks(self, parent_blocks: Dict[str, BlockSpec], child_blocks_data: Dict[str, Any]) -> Dict[str, BlockSpec]:
        """Rule 2: Role-keyed block merging."""
        merged: Dict[str, BlockSpec] = {k: v for k, v in parent_blocks.items()}

        for role, bdata in child_blocks_data.items():
            child_block = BlockSpec.from_dict(role, bdata)
            if child_block.replace or role not in merged:
                merged[role] = child_block
            else:
                parent_b = merged[role]
                # Merge size and number if specified in child
                new_number = child_block.number if child_block.number is not None else parent_b.number
                new_size = child_block.size if child_block.size is not None else parent_b.size
                merged_fields = self.merge_block_fields(parent_b.fields, child_block.fields)
                merged_reserved = parent_b.reserved + child_block.reserved
                merged[role] = BlockSpec(
                    name=role,
                    number=new_number,
                    size=new_size,
                    fields=merged_fields,
                    reserved=merged_reserved,
                    replace=False
                )
        return merged

    def merge_mappings(self, parent_map: Dict[str, Any], child_map: Dict[str, Any]) -> Dict[str, Any]:
        """Rule 3: Gather-keyed mappings/resolvers union with explicit null overrides."""
        merged: Dict[str, Any] = {}
        all_gathers = set(parent_map.keys()) | set(child_map.keys())
        for gather in all_gathers:
            p_g = parent_map.get(gather, {}) or {}
            c_g = child_map.get(gather, {}) or {}
            g_merged = dict(p_g)
            for k, v in c_g.items():
                if v is None:
                    g_merged.pop(k, None)
                else:
                    g_merged[k] = v
            merged[gather] = g_merged
        return merged

    def load_effective_schema(self, revision: str, manufacturer: str = "smartsolo", variant: Optional[str] = None) -> EffectiveSchema:
        """Load and merge the 5-layer dual-stack schema."""
        rev_dir = f"rev{revision}"
        
        # Layer 1: Base structural
        base_data = self.load_yaml(f"{rev_dir}/base.yaml")
        base_blocks = {role: BlockSpec.from_dict(role, b) for role, b in base_data.get("blocks", {}).items()}

        # Layer 2: Manufacturer structural
        mfr_struct_data = self.load_yaml(f"{rev_dir}/{manufacturer}/standard.yaml")
        mfr_blocks = self.merge_blocks(base_blocks, mfr_struct_data.get("blocks", {}))

        # Layer 3: Variant structural
        variant_struct_data = {}
        if variant:
            variant_struct_data = self.load_yaml(f"{rev_dir}/{manufacturer}/{variant}.yaml")
        variant_blocks = self.merge_blocks(mfr_blocks, variant_struct_data.get("blocks", {}))

        # Trace extensions merging
        trace_ext = base_data.get("trace_extensions", {})
        if "trace_extensions" in mfr_struct_data:
            mfr_ext_blocks = self.merge_blocks(
                {k: BlockSpec.from_dict(k, v) for k, v in trace_ext.get("blocks", {}).items()},
                mfr_struct_data["trace_extensions"].get("blocks", {})
            )
            trace_ext["blocks"] = mfr_ext_blocks
        if "trace_extensions" in variant_struct_data:
            var_ext_blocks = self.merge_blocks(
                trace_ext.get("blocks", {}),
                variant_struct_data["trace_extensions"].get("blocks", {})
            )
            trace_ext["blocks"] = var_ext_blocks

        # Layer 4: Manufacturer mapping stack
        mfr_map_data = self.load_yaml(f"{rev_dir}/{manufacturer}/standard.map.yaml")
        
        # Layer 5: Variant mapping stack
        variant_map_data = {}
        if variant:
            variant_map_data = self.load_yaml(f"{rev_dir}/{manufacturer}/{variant}.map.yaml")

        merged_resolvers = self.merge_mappings(
            mfr_map_data.get("resolvers", {}),
            variant_map_data.get("resolvers", {})
        )
        merged_mappings = self.merge_mappings(
            mfr_map_data.get("mappings", {}),
            variant_map_data.get("mappings", {})
        )

        metadata = {
            "id": variant_struct_data.get("id", variant or "standard"),
            "status": variant_struct_data.get("status", mfr_struct_data.get("status", "ok")),
            "gather_type": variant_struct_data.get("gather_type", mfr_struct_data.get("gather_type")),
            "firmware_labels": variant_struct_data.get("firmware_labels", []),
        }

        schema = EffectiveSchema(
            revision=revision,
            manufacturer=manufacturer,
            variant_id=variant or "standard",
            blocks=variant_blocks,
            trace_extensions=trace_ext,
            resolvers=merged_resolvers,
            mappings=merged_mappings,
            metadata=metadata
        )

        self.validate_schema(schema)
        return schema

    def validate_schema(self, schema: EffectiveSchema) -> None:
        """Validate startup invariants for the effective schema."""
        for role, block in schema.blocks.items():
            for f in block.fields:
                if f.type not in self.VALID_TYPES:
                    raise ValueError(f"Schema error in block '{role}', field '{f.name}': invalid type '{f.type}'")
            covered = {}
            for f in block.fields:
                for b in range(f.offset, f.offset + f.length):
                    if b in covered:
                        existing = covered[b]
                        if f.type == "bcd_nibble" or existing.type == "bcd_nibble":
                            continue # Allowed for nibble-shared bytes
                        raise ValueError(f"Byte overlap error in block '{role}': field '{f.name}' overlaps with '{existing.name}' at offset {b}")
                    covered[b] = f

    def auto_detect_schema(self, buffer: bytes) -> EffectiveSchema:
        """Probe raw initial 64-byte header buffer to detect SEG-D revision, manufacturer, and variant."""
        if len(buffer) < 32:
            raise ValueError("Buffer too short to auto-detect SEG-D schema (minimum 32 bytes required)")

        mfr_code = bcd_to_hex(buffer, 16, 1) & 0xFF
        manufacturer = self.MANUFACTURER_MAP.get(mfr_code, "smartsolo")

        rev_str = "2.1"
        if len(buffer) >= 64:
            gh2_rev_major = buffer[42]
            if gh2_rev_major == 3:
                rev_str = "3.1"
            elif gh2_rev_major == 2:
                rev_str = "2.1"
            elif gh2_rev_major == 1:
                rev_str = "1.0"
            elif gh2_rev_major == 0:
                rev_str = "0.0"

        rev_dir = self.schema_dir / f"rev{rev_str}" / manufacturer
        selected_variant = None

        if rev_dir.exists():
            for var_file in sorted(rev_dir.glob("version*.yaml")):
                var_data = self.load_yaml(f"rev{rev_str}/{manufacturer}/{var_file.name}")
                sig = var_data.get("version_signal")
                if sig:
                    role = sig.get("block", "general_header_2")
                    offset = sig.get("offset", 10)
                    block_offset = 32 if role == "general_header_2" else 0
                    buf_offset = block_offset + offset
                    if len(buffer) > buf_offset:
                        byte_val = buffer[buf_offset]
                        expected_val = sig.get("value")
                        if byte_val == expected_val:
                            selected_variant = var_file.stem
                            break

        if not selected_variant:
            if (rev_dir / "version002.yaml").exists():
                selected_variant = "version002"
            elif (rev_dir / "version001.yaml").exists():
                selected_variant = "version001"

        return self.load_effective_schema(revision=rev_str, manufacturer=manufacturer, variant=selected_variant)
