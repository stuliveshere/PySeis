from construct import *
import numpy as np

class BCDField(Adapter):
    def __init__(self, subcon):
        super().__init__(subcon)
    
    def _encode(self, obj, context, path):
        """Convert hex string or number to binary
        e.g., "1234" or "FFFF" -> 0x1234 or 0xFFFF"""
        value = str(obj)
        return int(value, 16)
    
    def _decode(self, obj, context, path):
        """Convert binary to hex string or number
        e.g., 0x1234 -> 4660 (if valid number), "1234" (if not)"""
        num_digits = self.subcon.length // 4  # 4 bits = 1 hex digit
        hex_str = np.base_repr(obj, 16).zfill(num_digits)
        if "F" in hex_str:
            return hex_str
        else:
            return int(hex_str)

class HexField(Adapter):
    def __init__(self, subcon):
        super().__init__(subcon)
    
    def _encode(self, obj, context, path):
        """Convert number or hex string to binary
        e.g., 0x1234 or "1234" -> 0x1234"""
        if isinstance(obj, str):
            return int(obj.replace('0x', ''), 16)
        return obj
    
    def _decode(self, obj, context, path):
        return np.base_repr(obj, 16).zfill(self.subcon.length // 4)

class RawHeaderBlockField(Adapter):
    def __init__(self, subcon):
        super().__init__(subcon)
    
    def _encode(self, obj, context, path):
        """Convert dictionary back to bytes for writing"""
        if isinstance(obj, dict):
            # Convert hex string back to bytes
            return bytes.fromhex(obj['hex'])
        return obj
    
    def _decode(self, obj, context, path):
        """Return both hex and ASCII representations of the 32-byte block"""
        # Convert to hex
        hex_str = obj.hex().upper()
        
        # Convert to ASCII, replacing non-ASCII bytes with '.'
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in obj).rstrip('\x00')
        
        return {
            'hex': hex_str,
            'ascii': ascii_str
        }

class TraceDataAdapter(Adapter):
    def __init__(self, subcon, format_code):
        super().__init__(subcon)
        self.format_code = format_code
    
    def _encode(self, obj, context, path):
        """Convert numpy array to bytes"""
        if self.format_code != 8058:
            raise NotImplementedError(f"Format code {self.format_code} not yet implemented")
        
        # 8058: 32-bit IEEE float
        return obj.astype(np.float32).tobytes()
    
    def _decode(self, obj, context, path):
        """Convert bytes to numpy array based on format code"""
        if self.format_code != 8058:
            raise NotImplementedError(f"Format code {self.format_code} not yet implemented")
        
        # 8058: 32-bit IEEE float
        return np.frombuffer(obj, dtype=np.float32)

def get_format_description(context):
    # Lookup table for format codes
    FORMAT_LOOKUP = {
        8015: "20 bit binary demultiplexed",
        8022: "8 bit quaternary demultiplexed",
        8024: "16 bit quaternary demultiplexed",
        8036: "24 bit 2's complement integer demultiplexed",
        8038: "32 bit 2's complement integer demultiplexed",
        8042: "8 bit hexadecimal demultiplexed",
        8044: "16 bit hexadecimal demultiplexed",
        8048: "32 bit hexadecimal demultiplexed",
        8058: "32 bit IEEE demultiplexed",
        200: "Illegal, do not use",
        0: "Illegal, do not use"
    }
    format_raw = context.format_code
    return FORMAT_LOOKUP.get(format_raw, "Unknown format")

def get_channel_type(context):
    # Lookup table for channel type codes
    CHANNEL_TYPE_LOOKUP = {
        0b0111: "Other",
        0b0110: "External Data",
        0b0101: "Time counter",
        0b0100: "Water break",
        0b0011: "Up hole",
        0b0010: "Time break",
        0b0001: "Seis",
        0b0000: "Unused",
        0b1000: "Signature/unfiltered",
        0b1001: "Signature/filtered",
        0b1100: "Auxiliary Data Trailer"
    }
    channel_type_raw = context.channel_type_raw
    return CHANNEL_TYPE_LOOKUP.get(channel_type_raw, "Unknown type")

def get_gain_control_method(context):
    # Lookup table for gain control method codes
    GAIN_CONTROL_METHOD_LOOKUP = {
        0b0001: "Individual AGC",
        0b0010: "Ganged AGC",
        0b0011: "Fixed gain",
        0b0100: "Programmed gain",
        0b1000: "Binary gain control",
        0b1001: "IFP gain control"
    }
    gain_method = context.gain_control_method
    return GAIN_CONTROL_METHOD_LOOKUP.get(gain_method, "Unknown method")

def compute_descale_multiplier(ctx):
    raw = ctx.descale_multiplier_raw
    mps = (raw >> 7) & 0b1  # Extract sign bit (MPS)
    magnitude_bits = raw & 0b01111111  # Extract magnitude bits (MP4 to MP-2)

    # Convert magnitude bits to a fixed-point value with radix point between MP0 and MP-1
    integer_part = magnitude_bits >> 2  # Upper bits are the integer part
    fractional_part = (magnitude_bits & 0b11) / 4  # Lower 2 bits are fractional part (divide by 4)
    magnitude = integer_part + fractional_part

    # Apply the sign from MPS to get the final exponent
    exponent = -magnitude if mps == 1 else magnitude

    # Compute the descale multiplier as 2^exponent
    return 2 ** exponent

general_header1 = BitStruct(
    "file_number" / BCDField(BitsInteger(16)),  # F1-F4 (16 bits, BCD)
    "format_code" / BCDField(BitsInteger(16)),  # Y1-Y4 (16 bits, BCD)
    # "format_description" / Computed(lambda ctx: get_format_description(ctx)),  # Description based on format_code
    "general_constants" / HexField(BitsInteger(48)),  # K1-K12 (48 bits)
    "year" / BCDField(BitsInteger(8)),  # YR1-YR2 (8 bits, BCD)
    "additional_gh_blocks" / BitsInteger(4),  # GH3-GH0 (4 bits)
    "day" / BCDField(BitsInteger(12)),  # DY1-DY3 (12 bits, BCD)
    "hour" / BCDField(BitsInteger(8)),  # H1-H2 (8 bits, BCD)
    "minute" / BCDField(BitsInteger(8)),  # MI1-MI2 (8 bits, BCD)
    "second" / BCDField(BitsInteger(8)),  # SE1-SE2 (8 bits, BCD)
    "manufacturer_code" / BCDField(BitsInteger(8)),  # M1-M2 (8 bits, BCD)
    "manufacturer_serial" / BCDField(BitsInteger(16)),  # M3-M6 (16 bits, BCD)
    "empty1" / HexField(BitsInteger(24)),  # Empty bits (24 bits)
    "base_scan_interval_raw" / BitsInteger(8),  # I3-I-4 (8 bits, Binary)
    "base_scan_interval" / Computed(this.base_scan_interval_raw / 16.0),  # I3-I-4 (8 bits, Binary)
    "polarity" / BitsInteger(4),  # P (4 bits)
    "empty2" / HexField(BitsInteger(12)),  # Empty bits (12 bits)
    "record_type" / BitsInteger(4),  # Z (4 bits)
    "record_length" / BCDField(BitsInteger(12)),  # R1-R3 (12 bits, BCD)
    "scan_types_per_record" / BCDField(BitsInteger(8)),  # ST/R1-ST/R2 (8 bits, BCD)
    "channel_sets_per_scan_type" / BCDField(BitsInteger(8)),  # CS1-CS2 (8 bits, BCD)
    "skew_blocks" / BCDField(BitsInteger(8)),  # SK1-SK2 (8 bits, BCD)
    "extended_header_blocks" / BCDField(BitsInteger(8)),  # EC1-EC2 (8 bits, BCD)
    "external_header_blocks" / BCDField(BitsInteger(8))  # EX1-EX2 (8 bits, BCD)
)


general_header2 = Struct(
    "expanded_file_number" / Int24ub,
    "extended_channel_sets" / Int16ub,
    "extended_header_blocks" / Int16ub,
    "external_header_blocks" / Int16ub,
    "undefined1" / Bytes(1),
    "major_segd_revision" / Int8ub,
    "minor_segd_revision" / Int8ub,
    "general_trailer_blocks" / Int16ub,
    "extended_record_length" / Int24ub,
    "undefined2" / Bytes(1),
    "block_number" / Int8ub,
    "undefined3" / Bytes(1),
    "sequence_number" / Int16ub,
    "undefined4" / Bytes(10)
)

general_header_n = Struct(
    "expanded_file_number" / Int24ub,
    "source_line_number_int" / Int24sb,
    "source_line_number_frac" / Int16ub,
    "source_point_number_int" / Int24sb,
    "source_point_number_frac" / Int16ub,
    "source_point_index" / Int8ub,
    "phase_control" / Int8ub,
    "vibrator_type" / Int8ub,
    "phase_angle" / Int16sb,
    "block_number" / Int8ub,
    "source_set_number" / Int8ub,
    "undefined" / Bytes(12)
)

channel_set = BitStruct(
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

demux_format = BitStruct(
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
    "receiver_line_number" / Int24sb,                       # RLNS, RLN22-RLN0: Receiver Line Number (3 bytes, signed)
    "receiver_point_number" / Int24sb,                      # RPNS, RPN22-RPN0: Receiver Point Number (3 bytes, signed)
    "receiver_point_index" / Int8sb,                        # RPIS, RPI6-RPI0: Receiver Point Index (1 byte, signed)
    "samples_per_trace" / Int24ub,                          # NBS23-NBS0: Number of Samples per Trace (3 bytes, unsigned)
    "extended_receiver_line_number_int" / Int24sb,          # ERLN: Extended Receiver Line Number (3 bytes integer)
    "extended_receiver_line_number_frac" / Int16ub,         # ERLN: Extended Receiver Line Number (2 bytes fraction)
    "extended_receiver_point_number_int" / Int24sb,         # ERPN: Extended Receiver Point Number (3 bytes integer)
    "extended_receiver_point_number_frac" / Int16ub,        # ERPN: Extended Receiver Point Number (2 bytes fraction)
    "sensor_type" / Int8ub,                                 # SEN: Sensor Type (1 byte unsigned)
    "sensor_type_description" / Computed(lambda ctx: {
        0: "Not defined", 1: "Hydrophone", 2: "Geophone Vertical", 
        3: "Geophone Horizontal inline", 4: "Geophone Horizontal cross-line", 
        5: "Geophone Horizontal other", 6: "Accelerometer Vertical",
        7: "Accelerometer Horizontal inline", 8: "Accelerometer Horizontal cross-line",
        9: "Accelerometer Horizontal other"}.get(ctx.sensor_type, "Undefined")),
    "undefined" / Bytes(11)                                 # X: Undefined fields (11 bytes)
)

headers_format = Struct(
    # 1. General Headers
    "general_header1" / general_header1,
    "general_header2" / If(lambda this: this.general_header1.additional_gh_blocks >= 1, 
        general_header2
    ),
    "general_header_n" / If(lambda this: this.general_header1.additional_gh_blocks >= 2,
        Array(lambda this: this.general_header1.additional_gh_blocks - 1, 
            general_header_n
        )
    ),
    
    # 2. Scan Types and Channel Sets
    "scan_types" / Array(lambda this: this.general_header1.scan_types_per_record,
        Struct(
            "channel_sets" / Array(lambda this: this._root.general_header1.channel_sets_per_scan_type, 
                channel_set
            ),
            "skew_blocks" / Array(lambda this: this._root.general_header1.skew_blocks, 
                Bytes(32)  # Each skew block is 32 bytes
            )
        )
    ),
    
    # 3. Extended Headers (optional)
    "extended_headers" / Array(lambda this: (
        this.general_header2.extended_header_blocks if this.general_header1.extended_header_blocks == 'FF' 
        else this.general_header1.extended_header_blocks
    ),
        RawHeaderBlockField(Bytes(32))  # Each extended header block is 32 bytes
    ),
    
    # 4. External Headers (optional)
    "external_headers" / Array(lambda this: (
        this.general_header2.external_header_blocks if this.general_header1.external_header_blocks == 'FF' 
        else this.general_header1.external_header_blocks
    ),
        RawHeaderBlockField(Bytes(32))  # Each external header block is 32 bytes
    )
)


# First create a format for a single trace
single_trace_format = Struct(
    "demux_header" / demux_format,
    "trace_header_extensions" / Array(lambda this: this.demux_header.trace_header_extensions,
        trace_header_extension_format
    ),
    "trace_data" / TraceDataAdapter(
        Bytes(lambda this: this.trace_header_extensions[0].samples_per_trace * 4),  # 4 bytes per sample for IEEE
        format_code=8058
    )
)

# Then create a format that reads all traces based on scan types and channel sets
traces_format = Struct(
    "traces" / Array(lambda this: sum(
        channel_set.number_of_channels 
        for scan_type in this._.headers.scan_types
        for channel_set in scan_type.channel_sets
        if channel_set.number_of_channels != 0  # Skip unused channels
    ), single_trace_format)
)

