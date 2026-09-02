"""
Vectorized Sample Decoders and Encoders for SEG-Y format codes.
Supports IBM float (1), Int32 (2), Int16 (3), IEEE float (5), Int8 (8), and IEEE double (16).
"""

from typing import Callable, Dict
import numpy as np
from pyseis_io.utils import ibm2ieee, ieee2ibm

def decode_ibm_float(raw_bytes: bytes, n_samples: int, endian: str = ">") -> np.ndarray:
    """Decode 32-bit IBM Float (format code 1)."""
    dtype = np.dtype(f"{endian}u4")
    raw_u4 = np.frombuffer(raw_bytes[:n_samples * 4], dtype=dtype, count=n_samples)
    return ibm2ieee(raw_u4).astype(np.float32)


def decode_ieee_float(raw_bytes: bytes, n_samples: int, endian: str = ">") -> np.ndarray:
    """Decode 32-bit IEEE Float (format code 5)."""
    dtype = np.dtype(f"{endian}f4")
    return np.frombuffer(raw_bytes[:n_samples * 4], dtype=dtype, count=n_samples).astype(np.float32)


def decode_int32(raw_bytes: bytes, n_samples: int, endian: str = ">") -> np.ndarray:
    """Decode 32-bit Integer (format code 2)."""
    dtype = np.dtype(f"{endian}i4")
    return np.frombuffer(raw_bytes[:n_samples * 4], dtype=dtype, count=n_samples).astype(np.float32)


def decode_int16(raw_bytes: bytes, n_samples: int, endian: str = ">") -> np.ndarray:
    """Decode 16-bit Integer (format code 3)."""
    dtype = np.dtype(f"{endian}i2")
    return np.frombuffer(raw_bytes[:n_samples * 2], dtype=dtype, count=n_samples).astype(np.float32)


def decode_int8(raw_bytes: bytes, n_samples: int, endian: str = ">") -> np.ndarray:
    """Decode 8-bit Integer (format code 8)."""
    return np.frombuffer(raw_bytes[:n_samples], dtype=np.int8, count=n_samples).astype(np.float32)


def decode_float64(raw_bytes: bytes, n_samples: int, endian: str = ">") -> np.ndarray:
    """Decode 64-bit IEEE Float (format code 16)."""
    dtype = np.dtype(f"{endian}f8")
    return np.frombuffer(raw_bytes[:n_samples * 8], dtype=dtype, count=n_samples).astype(np.float32)


# Encoders
def encode_ieee_float(samples: np.ndarray, endian: str = ">") -> bytes:
    """Encode float array to IEEE 32-bit float bytes."""
    dtype = np.dtype(f"{endian}f4")
    return samples.astype(dtype).tobytes()


def encode_ibm_float(samples: np.ndarray, endian: str = ">") -> bytes:
    """Encode float array to IBM 32-bit float bytes."""
    ibm_u4 = ieee2ibm(samples)
    dtype = np.dtype(f"{endian}u4")
    return ibm_u4.astype(dtype).tobytes()


def encode_int32(samples: np.ndarray, endian: str = ">") -> bytes:
    """Encode float array to 32-bit integer bytes."""
    dtype = np.dtype(f"{endian}i4")
    return samples.astype(dtype).tobytes()


def encode_int16(samples: np.ndarray, endian: str = ">") -> bytes:
    """Encode float array to 16-bit integer bytes."""
    dtype = np.dtype(f"{endian}i2")
    return samples.astype(dtype).tobytes()


SEGY_DECODERS: Dict[int, Callable[[bytes, int, str], np.ndarray]] = {
    1: decode_ibm_float,
    2: decode_int32,
    3: decode_int16,
    5: decode_ieee_float,
    8: decode_int8,
    16: decode_float64,
}

SEGY_ENCODERS: Dict[int, Callable[[np.ndarray, str], bytes]] = {
    1: encode_ibm_float,
    2: encode_int32,
    3: encode_int16,
    5: encode_ieee_float,
}


def get_segy_decoder(format_code: int) -> Callable[[bytes, int, str], np.ndarray]:
    return SEGY_DECODERS.get(format_code, decode_ieee_float)


def get_segy_encoder(format_code: int) -> Callable[[np.ndarray, str], bytes]:
    return SEGY_ENCODERS.get(format_code, encode_ieee_float)
