"""
SEG-Y YAML Schema Engine, Endianness Auto-Detector, and Revision Manager.
Loads Rev 0, Rev 1, and Rev 2 specifications transcribed from SEG PDF standards.
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

class SEGYFieldSpec:
    def __init__(self, name: str, offset: int, length: int = 4, field_type: str = "int32", **kwargs):
        self.name = name
        self.offset = offset
        self.length = length
        self.type = field_type
        self.description: str = str(kwargs.get("description", ""))
        self.spec_ref: str = str(kwargs.get("spec_ref", ""))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SEGYFieldSpec:
        extra = {k: v for k, v in data.items() if k not in ("name", "offset", "length", "type")}
        return cls(
            name=data["name"],
            offset=data["offset"],
            length=data.get("length", 4),
            field_type=data.get("type", "int32"),
            **extra
        )


class SEGYBlockSpec:
    def __init__(self, name: str, number: int, size: int, fields: Optional[List[SEGYFieldSpec]] = None):
        self.name = name
        self.number = number
        self.size = size
        self.fields: List[SEGYFieldSpec] = fields or []

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> SEGYBlockSpec:
        fields = [SEGYFieldSpec.from_dict(f) for f in data.get("fields", [])]
        return cls(
            name=name,
            number=data.get("number", 1),
            size=data.get("size", 240),
            fields=fields
        )


class SEGYEffectiveSchema:
    def __init__(self, revision: str, endian: str, blocks: Dict[str, SEGYBlockSpec]):
        self.revision = revision
        self.endian = endian
        self.blocks = blocks

    def get_block(self, name: str) -> Optional[SEGYBlockSpec]:
        return self.blocks.get(name)


class SEGYSchemaManager:
    """Manages versioned SEG-Y YAML schema loading, merging, and auto-detection."""

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

    def load_revision_schema(self, revision: str = "rev1", endian: str = ">") -> SEGYEffectiveSchema:
        rev_str = revision.lower()
        if not rev_str.startswith("rev"):
            rev_str = f"rev{rev_str}"

        # Load Rev 0 base
        rev0_data = self.load_yaml("rev0/base.yaml")
        blocks_map: Dict[str, SEGYBlockSpec] = {
            role: SEGYBlockSpec.from_dict(role, bdata)
            for role, bdata in rev0_data.get("blocks", {}).items()
        }

        if rev_str in ("rev1", "rev2"):
            rev1_data = self.load_yaml("rev1/base.yaml")
            self._merge_blocks(blocks_map, rev1_data.get("blocks", {}))

        if rev_str == "rev2":
            rev2_data = self.load_yaml("rev2/base.yaml")
            self._merge_blocks(blocks_map, rev2_data.get("blocks", {}))

        return SEGYEffectiveSchema(revision=rev_str, endian=endian, blocks=blocks_map)

    def _merge_blocks(self, base_blocks: Dict[str, SEGYBlockSpec], delta_blocks_data: Dict[str, Any]) -> None:
        for role, bdata in delta_blocks_data.items():
            if role not in base_blocks:
                base_blocks[role] = SEGYBlockSpec.from_dict(role, bdata)
            else:
                existing_b = base_blocks[role]
                new_fields = [SEGYFieldSpec.from_dict(f) for f in bdata.get("fields", [])]
                field_dict = {f.name: idx for idx, f in enumerate(existing_b.fields)}
                for nf in new_fields:
                    if nf.name in field_dict:
                        existing_b.fields[field_dict[nf.name]] = nf
                    else:
                        existing_b.fields.append(nf)

    def auto_detect(self, buffer: bytes) -> SEGYEffectiveSchema:
        """
        Probe raw initial file bytes to detect endianness (Big '>' vs Little '<') and revision.
        EBCDIC: 3200B, Binary header: bytes 3200-3600.
        Format code at offset 3224 (0-indexed 3224).
        """
        if len(buffer) < 3600:
            return self.load_revision_schema("rev1", endian=">")

        # Check binary format code at byte offset 3224 (2 bytes)
        fmt_be = int.from_bytes(buffer[3224:3226], byteorder="big", signed=True)
        fmt_le = int.from_bytes(buffer[3224:3226], byteorder="little", signed=True)

        endian = ">"
        if 1 <= fmt_be <= 16:
            endian = ">"
        elif 1 <= fmt_le <= 16:
            endian = "<"

        # Read segyrev at byte offset 3500 (2 bytes)
        segyrev_val = int.from_bytes(buffer[3500:3502], byteorder="big" if endian == ">" else "little", signed=True)
        revision = "rev0"
        if segyrev_val == 0x0100 or segyrev_val == 256:
            revision = "rev1"
        elif segyrev_val == 0x0200 or segyrev_val == 512:
            revision = "rev2"

        return self.load_revision_schema(revision=revision, endian=endian)
