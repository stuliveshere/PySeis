"""
Header Fill Plan Compiler & Vectorized Execution Engine.
Merges 5-layer YAML schema mappings with Layer 6 custom byte overrides,
extracting header values from binary trace headers into pandas DataFrames/NumPy structured arrays.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

from .schema import EffectiveSchema, bcd_digits, bcd_nibble, bcd_to_hex, FieldSpec

class HeaderMappingRule:
    """Represents a single header field extraction and mapping rule."""
    def __init__(
        self,
        header_name: str,
        block_role: str,
        field_name: str,
        byte_offset: int,
        byte_length: int,
        data_type: str,
        scale: float = 1.0,
        offset_val: float = 0.0,
        nibble: Optional[str] = None
    ):
        self.header_name = header_name
        self.block_role = block_role
        self.field_name = field_name
        self.byte_offset = byte_offset
        self.byte_length = byte_length
        self.data_type = data_type
        self.scale = scale
        self.offset_val = offset_val
        self.nibble = nibble

    def extract_value(self, buffer: bytes, block_base_offset: int = 0) -> Any:
        """Extract and transform a scalar value from raw block bytes."""
        offset = block_base_offset + self.byte_offset
        if len(buffer) < offset + self.byte_length:
            return 0

        raw_val: Any = 0
        if self.data_type == "bcd_nibble":
            raw_val = bcd_nibble(buffer[offset], self.nibble or "low")
        elif self.data_type == "bcd_digits":
            raw_val = bcd_digits(buffer, offset, self.byte_length)
        elif self.data_type in ("int8", "int16", "int32", "int64"):
            raw_val = int.from_bytes(buffer[offset:offset + self.byte_length], byteorder="big", signed=True)
        elif self.data_type in ("uint8", "uint16", "uint32", "uint64"):
            raw_val = int.from_bytes(buffer[offset:offset + self.byte_length], byteorder="big", signed=False)
        elif self.data_type == "ieee_float":
            raw_val = float(np.frombuffer(buffer[offset:offset + 4], dtype=">f4")[0])
        elif self.data_type == "ascii":
            raw_val = buffer[offset:offset + self.byte_length].decode("ascii", errors="replace").strip()
        else:
            raw_val = int.from_bytes(buffer[offset:offset + self.byte_length], byteorder="big", signed=False)

        if isinstance(raw_val, (int, float)):
            return (raw_val * self.scale) + self.offset_val
        return raw_val


class TraceFillPlan:
    """Compiles mapping rules across YAML schema layers and user custom byte overrides."""

    def __init__(
        self,
        schema: EffectiveSchema,
        gather_type: str = "SG",
        custom_mappings: Optional[List[Dict[str, Any]]] = None,
        global_xref: float = 0.0,
        global_yref: float = 0.0
    ):
        self.schema = schema
        self.gather_type = gather_type.lower()
        self.custom_mappings = custom_mappings or []
        self.global_xref = global_xref
        self.global_yref = global_yref
        self.rules: List[HeaderMappingRule] = self._compile_plan()

    def _compile_plan(self) -> List[HeaderMappingRule]:
        rules: List[HeaderMappingRule] = []
        schema_mappings = self.schema.get_mapping(self.gather_type)

        # Layers 1-5: YAML Schema mappings
        for hdr_name, mapping_entry in schema_mappings.items():
            if mapping_entry is None:
                continue

            target_field_path = mapping_entry
            scale = 1.0
            offset_val = 0.0

            if isinstance(mapping_entry, dict):
                target_field_path = mapping_entry.get("field", "")
                scale = float(mapping_entry.get("scale", 1.0))
                offset_val = float(mapping_entry.get("offset", 0.0))

            if "." not in target_field_path:
                continue

            block_role, field_name = target_field_path.split(".", 1)
            block_spec = self.schema.get_block_by_role(block_role)

            if block_spec:
                target_f = next((f for f in block_spec.fields if f.name == field_name), None)
                if target_f:
                    rule = HeaderMappingRule(
                        header_name=hdr_name,
                        block_role=block_role,
                        field_name=field_name,
                        byte_offset=target_f.offset,
                        byte_length=target_f.length,
                        data_type=target_f.type,
                        scale=scale * target_f.scale,
                        offset_val=offset_val + target_f.offset_val,
                        nibble=target_f.nibble
                    )
                    rules.append(rule)

        # Layer 6: User UI/API Custom Byte Overrides
        for cust in self.custom_mappings:
            hdr_name = cust["header_name"]
            # Override any existing rule for this header_name
            rules = [r for r in rules if r.header_name != hdr_name]
            rule = HeaderMappingRule(
                header_name=hdr_name,
                block_role=cust.get("block_role", "demux_trace_header"),
                field_name=cust.get("field_name", "custom"),
                byte_offset=cust.get("offset", 0),
                byte_length=cust.get("length", 4),
                data_type=cust.get("type", "int32"),
                scale=float(cust.get("scale", 1.0)),
                offset_val=float(cust.get("offset_val", 0.0)),
                nibble=cust.get("nibble")
            )
            rules.append(rule)

        return rules

    def execute_single_trace(self, trace_hdr_bytes: bytes, trace_idx: int = 0) -> Dict[str, Any]:
        """Extract headers for a single trace header buffer into a dictionary."""
        out: Dict[str, Any] = {"tracl": trace_idx + 1}
        for rule in self.rules:
            # Demux trace header offset calculation
            block_offset = 0
            if rule.block_role not in ("demux_trace_header", "general_header_1"):
                # Trace extension blocks start after first 32-byte TH
                block_offset = 32

            val = rule.extract_value(trace_hdr_bytes, block_base_offset=block_offset)

            # Apply global coordinate reference subtractions
            if rule.header_name in ("SOU_X", "REC_X", "SOU_XD", "REC_XD") and isinstance(val, (int, float)):
                val = float(val) - self.global_xref
            elif rule.header_name in ("SOU_Y", "REC_Y", "SOU_YD", "REC_YD") and isinstance(val, (int, float)):
                val = float(val) - self.global_yref

            out[rule.header_name] = val
        return out

    def execute_bulk(self, trace_hdr_list: List[bytes]) -> pd.DataFrame:
        """Execute fill plan across a batch of trace header byte buffers into a pandas DataFrame."""
        rows = [self.execute_single_trace(hdr_b, idx) for idx, hdr_b in enumerate(trace_hdr_list)]
        return pd.DataFrame(rows)
