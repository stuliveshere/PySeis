from construct import *
from ..adapters import *
from ..utils import *

# Define format-specific structures
general_header1 = BitStruct(
    "file_number" / Default(BCDField(BitsInteger(16)), "FFFF"),  # Special value FFFF
    "format_code" / Default(BCDField(BitsInteger(16)), 8058),  # 32-bit IEEE
    "format_description" / Computed(lambda ctx: get_format_description(ctx)),
    "general_constants" / Default(HexField(BitsInteger(48)), 0),
    "year" / Default(BCDField(BitsInteger(8)), 80),  # GPS epoch year (1980)
    "additional_gh_blocks" / Default(BitsInteger(4), 2),
    "day" / Default(BCDField(BitsInteger(12)), 6),  # GPS epoch day (Jan 6)
    "hour" / Default(BCDField(BitsInteger(8)), 0),
    "minute" / Default(BCDField(BitsInteger(8)), 0),
    "second" / Default(BCDField(BitsInteger(8)), 0),
    "manufacturer_code" / Default(BCDField(BitsInteger(8)), "61"),
    "manufacturer_serial" / Default(BCDField(BitsInteger(16)), 0),
    "empty1" / Default(HexField(BitsInteger(24)), 0),
    "base_scan_interval_raw" / Default(BitsInteger(8), 16),  # 1.0 (16/16)
    "base_scan_interval" / Computed(this.base_scan_interval_raw / 16.0),
    "polarity" / Default(BitsInteger(4), 0),
    "empty2" / Default(HexField(BitsInteger(12)), 0),
    "record_type" / Default(BitsInteger(4), 8),
    "record_length" / Default(BCDField(BitsInteger(12)), "FFF"),
    "scan_types_per_record" / Default(BCDField(BitsInteger(8)), 1),
    "channel_sets_per_scan_type" / Default(BCDField(BitsInteger(8)), 16),
    "skew_blocks" / Default(BCDField(BitsInteger(8)), 0),
    "extended_header_blocks" / Default(BCDField(BitsInteger(8)), "FF"),  # Special value FF
    "external_header_blocks" / Default(BCDField(BitsInteger(8)), "FF")  # Special value FF
)


general_header2 = Struct(
    "expanded_file_number" / Default(Int24ub, 1),
    "extended_channel_sets" / Default(Int16ub, 0),
    "extended_header_blocks" / Default(Int16ub, 32),
    "external_header_blocks" / Default(Int16ub, 32),
    "undefined1" / Default(Bytes(1), b'\x00'),
    "major_segd_revision" / Default(Int8ub, 2),
    "minor_segd_revision" / Default(Int8ub, 1),
    "general_trailer_blocks" / Default(Int16ub, 0),
    "extended_record_length" / Default(Int24ub, 0),
    "undefined2" / Default(Bytes(1), b'\x00'),
    "block_number" / Default(Int8ub, 2),
    "undefined3" / Default(Bytes(1), b'\x00'),
    "sequence_number" / Default(Int16ub, 1),
    "undefined4" / Default(Bytes(10), b'\x00' * 10)
)

general_header_n = Struct(
    "expanded_file_number" / Default(Int24ub, 0),
    "source_line_number_int" / Default(Int24ub, 0),
    "source_line_number_frac" / Default(BinaryFractionAdapter(Int16ub, 2), 0.0),
    "source_point_number_int" / Default(Int24ub, 0),
    "source_point_number_frac" / Default(BinaryFractionAdapter(Int16ub, 2), 0.0),
    "source_point_index" / Default(Int8ub, 0),
    "phase_control" / Default(Int8ub, 0),
    "vibrator_type" / Default(Int8ub, 0),
    "phase_angle" / Default(Int16ub, 0),
    "block_number" / Default(Int8ub, 3),  # Block 3 for general_header_n
    "source_set_number" / Default(Int8ub, 0),
    "undefined" / Default(Bytes(12), b'\x00' * 12)
)

channel_set_header = BitStruct(
    "scan_type_number" / BCDField(BitsInteger(8)),  # ST1,ST2 (1-99)
    "channel_set_number" / BCDField(BitsInteger(8)),  # CN1,CN2 (1-99 or FF for extended)
    "start_time_raw" / BitsInteger(16),  # TF16-TF1 (binary, 2ms increments)
    "start_time" / Computed(this.start_time_raw * 2.0),  # TF16-TF1 (binary, 2ms increments)
    "end_time_raw" / BitsInteger(16),  # TE16-TE1 (binary, 2ms increments)
    "end_time" / Computed(this.end_time_raw * 2.0),  # TE16-TE1 (binary, 2ms increments)
    "descale_multiplier_extended" / BitsInteger(8),  # MP-3 to MP-10
    "descale_multiplier_raw" / BitsInteger(8),  # MPS, MP4-MP-2
    "descale_multiplier_calculated" / Computed(compute_descale_multiplier),
    "number_of_channels" / BCDField(BitsInteger(16)),  # C/S1-C/S4 (0-9999)
    "channel_type_raw" / BitsInteger(4),  # C1 (4 bits)
    "channel_type" / Computed(get_channel_type),
    "empty1" / HexField(BitsInteger(4)),  # Empty bits
    "subscans" / BCDField(BitsInteger(4)),  # S/C (4 bits)
    "gain_control_method" / BitsInteger(4),  # J (4 bits)
    "gain_control_description" / Computed(get_gain_control_method),  # Description based on gain method
    "alias_filter_freq" / BCDField(BitsInteger(16)),  # AF1-AF4 (0-9999 Hz)
    "empty2" / HexField(BitsInteger(4)),  # Empty bits
    "alias_filter_slope" / BCDField(BitsInteger(12)),  # AS1-AS3 (0-999 dB)
    "low_cut_freq" / BCDField(BitsInteger(16)),  # LC1-LC4 (0-9999 Hz)
    "empty3" / HexField(BitsInteger(4)),  # Empty bits
    "low_cut_slope" / BCDField(BitsInteger(12)),  # LS1-LS3 (0-999 dB)
    "notch_freq1" / BCDField(BitsInteger(16)),  # NT1-NT4 (0-999.9 Hz)
    "notch_freq2" / BCDField(BitsInteger(16)),  # NT1-NT4 (0-999.9 Hz)
    "notch_freq3" / BCDField(BitsInteger(16)),  # NT1-NT4 (0-999.9 Hz)
    "extended_channel_set_number" / BitsInteger(16),  # ECS15-ECS0 (binary)
    "extended_header_flag" / BitsInteger(4),  # EFH3-EFH0 (4 bits)
    "trace_header_extensions" / BitsInteger(4),  # THE3-THE0 (4 bits)
    "vertical_stack" / BitsInteger(8),  # VS7-VS0 (binary)
    "streamer_cable_number" / BitsInteger(8),  # CAB7-CAB0 (binary)
    "array_forming" / BitsInteger(8),  # ARY7-ARY0 (binary)
)

demux_header = BitStruct(
    "file_number" / BCDField(BitsInteger(16)),              # F1-F4: File Number (2 bytes, 4-digit BCD)
    "scan_type_number" / BCDField(BitsInteger(8)),          # ST1-ST2: Scan Type Number (1 byte, 2-digit BCD)
    "channel_set_number" / BCDField(BitsInteger(8)),        # CN1-CN2: Channel Set Number (1 byte, 2-digit BCD)
    "trace_number" / BCDField(BitsInteger(16)),             # TN1-TN4: Trace Number (2 bytes, 4-digit BCD)
    "first_timing_word" / BitsInteger(24),                  # T15-T-8: First Timing Word (3 bytes)
    "trace_header_extensions" / BitsInteger(8),             # THE7-THE0: Trace Header Extensions (1 byte, unsigned binary)
    "sample_skew" / BitsInteger(8),                         # SSK-1-SSK-8: Sample Skew (1 byte binary fraction)
    "trace_edit" / BitsInteger(8),                          # TR7-TR0: Trace edit (1 byte, unsigned binary)
    "trace_edit_description" / Computed(lambda ctx: {
        0: "No edit applied", 
        1: "Dead channel (roll-on/roll-off)", 
        2: "Intentionally zeroed", 
        3: "Trace has been edited"
    }.get(ctx.trace_edit, "Undefined")),
    "time_break_window_int" / BitsInteger(16),              # TW15-TW-8: Time Break Window (2 bytes integer)
    "time_break_window_frac" / BitsInteger(8),              # TW-8: Time Break Window (1 byte fraction)
    "extended_channel_set_number" / BitsInteger(16),        # EN15-EN0: Extended Channel Set Number (2 bytes, unsigned binary)
    "extended_file_number" / BitsInteger(24)                # EFN23-EFN0: Extended File Number (3 bytes, unsigned binary)
)

trace_header_extension_format = Struct(
    "receiver_line_number" / Int24ub,                       # RLNS, RLN22-RLN0: Receiver Line Number (3 bytes, unsigned)
    "receiver_point_number" / Int24ub,                      # RPNS, RPN22-RPN0: Receiver Point Number (3 bytes, unsigned)
    "receiver_point_index" / Int8ub,                        # RPIS, RPI6-RPI0: Receiver Point Index (1 byte, unsigned)
    "samples_per_trace" / Int24ub,                          # NBS23-NBS0: Number of Samples per Trace (3 bytes, unsigned)
    "extended_receiver_line_number_int" / Int24ub,          # ERLN: Extended Receiver Line Number (3 bytes integer)
    "extended_receiver_line_number_frac" / BinaryFractionAdapter(Int16ub, 2),  # ERLN: Extended Receiver Line Number (2 bytes fraction)
    "extended_receiver_point_number_int" / Int24sb,         # ERPN: Extended Receiver Point Number (3 bytes integer)
    "extended_receiver_point_number_frac" / BinaryFractionAdapter(Int16ub, 2),        # ERPN: Extended Receiver Point Number (2 bytes fraction)
    "sensor_type" / Int8ub,                                 # SEN: Sensor Type (1 byte signed)
    "sensor_type_description" / Computed(lambda ctx: {
        0: "Not defined", 1: "Hydrophone", 2: "Geophone Vertical", 
        3: "Geophone Horizontal inline", 4: "Geophone Horizontal cross-line", 
        5: "Geophone Horizontal other", 6: "Accelerometer Vertical",
        7: "Accelerometer Horizontal inline", 8: "Accelerometer Horizontal cross-line",
        9: "Accelerometer Horizontal other"}.get(ctx.sensor_type, "Undefined")),
    "undefined" / Bytes(11)                                 # X: Undefined fields (11 bytes)
)

