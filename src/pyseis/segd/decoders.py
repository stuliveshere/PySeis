"""
Vectorized Sample Format Decoders and Encoders for SEG-D.
Supports IEEE 32-bit float (0x8058), 20-bit demux (0x8015), 24-bit int (0x8036),
32-bit int (0x8038), and 16-bit int (0x8048).
"""

import numpy as np
from typing import Callable, Dict, Tuple

def decode_ieee_float(raw_bytes: bytes, n_samples: int) -> np.ndarray:
    """Decode 32-bit IEEE floats (format code 0x8058 / 8058)."""
    if len(raw_bytes) < n_samples * 4:
        # Pad buffer if truncated
        padded = raw_bytes + b'\x00' * (n_samples * 4 - len(raw_bytes))
        arr = np.frombuffer(padded, dtype='>f4', count=n_samples)
    else:
        arr = np.frombuffer(raw_bytes, dtype='>f4', count=n_samples)
    return arr.astype(np.float32)


def decode_int32(raw_bytes: bytes, n_samples: int) -> np.ndarray:
    """Decode 32-bit signed integers (format code 0x8038 / 8038)."""
    if len(raw_bytes) < n_samples * 4:
        padded = raw_bytes + b'\x00' * (n_samples * 4 - len(raw_bytes))
        arr = np.frombuffer(padded, dtype='>i4', count=n_samples)
    else:
        arr = np.frombuffer(raw_bytes, dtype='>i4', count=n_samples)
    return arr.astype(np.float32)


def decode_int16(raw_bytes: bytes, n_samples: int) -> np.ndarray:
    """Decode 16-bit signed integers (format code 0x8048 / 8048)."""
    if len(raw_bytes) < n_samples * 2:
        padded = raw_bytes + b'\x00' * (n_samples * 2 - len(raw_bytes))
        arr = np.frombuffer(padded, dtype='>i2', count=n_samples)
    else:
        arr = np.frombuffer(raw_bytes, dtype='>i2', count=n_samples)
    return arr.astype(np.float32)


def decode_int24(raw_bytes: bytes, n_samples: int) -> np.ndarray:
    """Decode 24-bit signed integers (format code 0x8036 / 8036)."""
    buf = np.frombuffer(raw_bytes[:n_samples * 3], dtype=np.uint8)
    if len(buf) < n_samples * 3:
        padded_buf = np.zeros(n_samples * 3, dtype=np.uint8)
        padded_buf[:len(buf)] = buf
        buf = padded_buf

    b0 = buf[0::3].astype(np.int32)
    b1 = buf[1::3].astype(np.int32)
    b2 = buf[2::3].astype(np.int32)

    val = (b0 << 16) | (b1 << 8) | b2
    # Sign extend 24-bit to 32-bit
    val = np.where(val & 0x800000, val - 0x1000000, val)
    return val.astype(np.float32)


def decode_20bit_bcd(raw_bytes: bytes, n_samples: int) -> np.ndarray:
    """
    Decode 20-bit binary exponent demultiplexed format (0x8015 / 8015).
    Each 4-byte block contains 2 samples:
    Byte 0: Exponent 1 (high nibble), Exponent 2 (low nibble)
    Byte 1-2: Signed 12-bit mantissa 1 & byte split
    Byte 2-3: Signed 12-bit mantissa 2
    """
    n_blocks = (n_samples + 1) // 2
    block_bytes = raw_bytes[:n_blocks * 4]
    if len(block_bytes) < n_blocks * 4:
        block_bytes = block_bytes + b'\x00' * (n_blocks * 4 - len(block_bytes))

    buf = np.frombuffer(block_bytes, dtype=np.uint8).reshape(-1, 4)

    exp1 = (buf[:, 0] >> 4) & 0x0F
    exp2 = buf[:, 0] & 0x0F

    # Mantissa 1: byte 1 (high 8 bits) + byte 2 high nibble
    man1 = (buf[:, 1].astype(np.int32) << 4) | ((buf[:, 2] >> 4) & 0x0F)
    man1 = np.where(man1 & 0x800, man1 - 0x1000, man1)

    # Mantissa 2: byte 2 low nibble + byte 3
    man2 = ((buf[:, 2] & 0x0F).astype(np.int32) << 8) | buf[:, 3]
    man2 = np.where(man2 & 0x800, man2 - 0x1000, man2)

    # Calculate floats: mantissa * 2^(exp - 15)
    s1 = man1.astype(np.float32) * np.power(2.0, exp1.astype(np.float32) - 15.0)
    s2 = man2.astype(np.float32) * np.power(2.0, exp2.astype(np.float32) - 15.0)

    out = np.empty((n_blocks * 2,), dtype=np.float32)
    out[0::2] = s1
    out[1::2] = s2
    return out[:n_samples]


# Encoder functions for writing SEG-D data
def encode_ieee_float(samples: np.ndarray) -> bytes:
    """Encode float array to 32-bit IEEE float bytes (format code 0x8058)."""
    return samples.astype('>f4').tobytes()


def encode_int32(samples: np.ndarray) -> bytes:
    """Encode float array to 32-bit signed int bytes (format code 0x8038)."""
    return samples.astype('>i4').tobytes()


def encode_int16(samples: np.ndarray) -> bytes:
    """Encode float array to 16-bit signed int bytes (format code 0x8048)."""
    return samples.astype('>i2').tobytes()


# Registry Mapping
SAMPLE_DECODERS: Dict[int, Callable[[bytes, int], np.ndarray]] = {
    0x8058: decode_ieee_float,
    8058: decode_ieee_float,
    0x8038: decode_int32,
    8038: decode_int32,
    0x8048: decode_int16,
    8048: decode_int16,
    0x8036: decode_int24,
    8036: decode_int24,
    0x8015: decode_20bit_bcd,
    8015: decode_20bit_bcd,
}

SAMPLE_ENCODERS: Dict[int, Callable[[np.ndarray], bytes]] = {
    0x8058: encode_ieee_float,
    8058: encode_ieee_float,
    0x8038: encode_int32,
    8038: encode_int32,
    0x8048: encode_int16,
    8048: encode_int16,
}


def get_decoder(format_code: int) -> Callable[[bytes, int], np.ndarray]:
    """Resolve sample format decoder for given format code."""
    if format_code in SAMPLE_DECODERS:
        return SAMPLE_DECODERS[format_code]
    # Default to IEEE float
    return decode_ieee_float


def get_encoder(format_code: int) -> Callable[[np.ndarray], bytes]:
    """Resolve sample format encoder for given format code."""
    if format_code in SAMPLE_ENCODERS:
        return SAMPLE_ENCODERS[format_code]
    return encode_ieee_float
