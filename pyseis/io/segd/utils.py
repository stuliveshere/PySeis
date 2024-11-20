def get_format_description(context):
    """Get human-readable description of trace data format.
    
    Args:
        context: Construct context containing format_code
    Returns:
        str: Description of the format
    """
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
