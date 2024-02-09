import struct
import numpy as np
import codecs

def get_int(blob, start_byte, num_bytes):
    # Extract whole number of bytes
    start = int(np.floor(start_byte))
    end = int(np.ceil(start_byte + num_bytes))
    packet = bytearray(blob[start:end])
    
    # If the field starts from the second nibble
    if start_byte % 1 != 0:
        packet[0] &= 0x0F  # Set the first nibble to zero

    # If the field ends at the first nibble
    if (start_byte + num_bytes) % 1 != 0:
        packet[-1] >>= 4  # Right-shift the last byte by 4 bits

    return int.from_bytes(packet, 'big', signed=True)

def set_int(blob, start_byte, num_bytes, value):
    packed_value = value.to_bytes(int(np.ceil(num_bytes)), 'big', signed=True)
    
    # If fractional bytes are involved, handle them
    if num_bytes % 1 != 0:
        if start_byte % 1 == 0.5:  # If starting from the middle of a byte
            packed_value = (blob[int(start_byte)] & 0xF0) | (packed_value[0] & 0x0F)
        else:
            packed_value = (packed_value[0] & 0xF0) | (blob[int(start_byte + num_bytes - 0.5)] & 0x0F)
    
    return blob[:int(start_byte)] + packed_value + blob[int(start_byte + np.ceil(num_bytes)):]

def get_uint(blob, start_byte, num_bytes):
    # Extract whole number of bytes
    start = int(np.floor(start_byte))
    end = int(np.ceil(start_byte + num_bytes))
    packet = bytearray(blob[start:end])
    
    # If the field starts from the second nibble
    if start_byte % 1 != 0:
        packet[0] &= 0x0F  # Set the first nibble to zero

    # If the field ends at the first nibble
    if (start_byte + num_bytes) % 1 != 0:
        packet[-1] >>= 4  # Right-shift the last byte by 4 bits

    return int.from_bytes(packet, 'big', signed=False)

def set_uint(blob, start_byte, num_bytes, value):
    packed_value = value.to_bytes(int(np.ceil(num_bytes)), 'big', signed=False)
    
    # If fractional bytes are involved, handle them
    if num_bytes % 1 != 0:
        if start_byte % 1 == 0.5:  # If starting from the middle of a byte
            packed_value = (blob[int(start_byte)] & 0xF0) | (packed_value[0] & 0x0F)
        else:
            packed_value = (packed_value[0] & 0xF0) | (blob[int(start_byte + num_bytes - 0.5)] & 0x0F)
    
    return blob[:int(start_byte)] + packed_value + blob[int(start_byte + np.ceil(num_bytes)):]


def get_bcd(blob, start_byte, num_bytes):
    start = np.floor(start_byte)
    end = np.ceil(start + num_bytes)
    data = blob[int(start):int(end)]
    nibbles = [n for byte in data for n in [(byte & 0xF0) >> 4, byte & 0x0F]]

    start_nibble = int(start_byte % 1 * 2)
    num_nibbles = int(num_bytes * 2)

    # Extract the relevant nibbles
    relevant_nibbles = nibbles[start_nibble:start_nibble + num_nibbles]

    if all(n == 0 for n in relevant_nibbles):
        return 0
    try:
        return int(''.join(map(str, relevant_nibbles)))
    except ValueError:
        return -int(''.join(map(str, relevant_nibbles)), 16)

def set_bcd(blob, start_byte, num_bytes, value):
    # Set up some variables
    start = np.floor(start_byte)
    end = np.ceil(start + num_bytes)
    data = blob[int(start):int(end)]
    nibbles = [n for byte in data for n in [(byte & 0xF0) >> 4, byte & 0x0F]]
    start_nibble = int(start_byte % 1 * 2)
    num_nibbles = int(num_bytes * 2)

    # Convert the value to a list of BCD nibbles
    if value < 0:
        bcd_str = format(-value, f'0{num_nibbles}X')  # Convert to hexadecimal string
    else:
        bcd_str = format(value, f'0{num_nibbles}d')  # Convert to decimal string
    new_nibbles = [int(n) for n in bcd_str]
    
    # Replace the relevant nibbles
    nibbles[start_nibble:start_nibble + num_nibbles] = new_nibbles
    # Pack the nibbles back into bytes
    
    updated_bytes = [(nibbles[i] << 4) | nibbles[i + 1] for i in range(0, len(nibbles), 2)]

    # Replace the relevant bytes in the blob and return the updated blob
    return blob[:int(start)] + bytes(updated_bytes) + blob[int(end):]

def get_str(blob, start_byte, num_bytes):
    decoded_chars = []

    for byte in blob[start_byte:start_byte + num_bytes]:
        try:
            char = bytes([byte]).decode('utf-8')
            decoded_chars.append(char)
        except UnicodeDecodeError:
            decoded_chars.append(f'0x{byte:02X}')

    return ''.join(decoded_chars)
    # return blob[start_byte:start_byte+num_bytes].decode('utf-8').rstrip('\x00')  # Assuming UTF-8 encoding and stripping null bytes

def set_str(blob, start_byte, num_bytes, value):
    encoded_value = value.encode('utf-8')
    if len(encoded_value) > num_bytes:
        raise ValueError("String too long for the specified number of bytes")
    return blob[:start_byte] + encoded_value.ljust(num_bytes, b'\x00') + blob[start_byte+num_bytes:]

def get_ieee_float32(blob, start_byte, num_bytes):
    if num_bytes == 4:  # float32
        return struct.unpack('>f', blob[start_byte:start_byte+num_bytes])[0]
    elif num_bytes == 8:  # float64
        return struct.unpack('>d', blob[start_byte:start_byte+num_bytes])[0]
    else:
        raise ValueError("Unsupported number of bytes for float")

def set_ieee_float32(blob, start_byte, num_bytes, value):
    if num_bytes == 4:  # float32
        return blob[:start_byte] + struct.pack('>f', value) + blob[start_byte+num_bytes:]
    elif num_bytes == 8:  # float64
        return blob[:start_byte] + struct.pack('>d', value) + blob[start_byte+num_bytes:]
    else:
        raise ValueError("Unsupported number of bytes for float")

def get_ebcdic(blob, start_byte, num_bytes):
    ebcdic_bytes = blob[start_byte:start_byte+num_bytes]
    value = codecs.decode(ebcdic_bytes, 'cp500')  # 'cp500' represents EBCDIC encoding
    return value

def set_ebcdic(blob, start_byte, num_bytes, value):
    # Truncate or pad the string to ensure it's of length num_bytes
    adjusted_value = value[:num_bytes].ljust(num_bytes)
    
    # Convert the adjusted string to EBCDIC encoding
    ebcdic_data = codecs.encode(adjusted_value, 'cp500')
    return blob[:start_byte] + ebcdic_data + blob[start_byte+num_bytes:]

def get_8036(blob, start_byte, num_bytes):
    # Convert bytearray into a list of 3-byte integers
    raw_ints = [int.from_bytes(blob[i:i+3], 'big') for i in range(0, len(blob), 3)]
    ints = [twos_complement(val, 24) for val in raw_ints]
    # Convert list of integers into a numpy array
    return np.array(ints)

def set_8036(blob, start_byte, num_bytes, value):
    return blob

def twos_complement(val, bits):
    """Compute the 2's complement of an integer value."""
    if val & (1 << (bits - 1)):
        val -= 1 << bits
    return val

DECODERS = {
    'bcd': {
        'get': get_bcd,
        'set': set_bcd
    },
    'uint': {
        'get': get_uint,
        'set': set_uint
    },
    'int': {
        'get': get_int,
        'set': set_int
    },
    'string': {
        'get': get_str,
        'set': set_str
    },
    'float32': {
        'get': get_ieee_float32,
        'set': set_ieee_float32
    },
    'ebcdic': {
        'get': get_ebcdic,
        'set': set_ebcdic
    },
    '8036': {
        'get': get_8036,
        'set': set_8036
    }
    # ... (similar entries for other data formats)
}
