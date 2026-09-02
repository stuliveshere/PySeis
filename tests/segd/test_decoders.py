"""
Tests for sample format decoders and encoders.
"""

import pytest
import numpy as np
from pyseis_io.segd.decoders import (
    decode_ieee_float,
    encode_ieee_float,
    decode_int32,
    encode_int32,
    decode_int16,
    encode_int16,
    decode_int24,
    decode_20bit_bcd,
    get_decoder,
    get_encoder
)

def test_ieee_float_roundtrip():
    original = np.array([1.5, -3.2, 0.0, 1234.56], dtype=np.float32)
    encoded = encode_ieee_float(original)
    decoded = decode_ieee_float(encoded, n_samples=4)
    np.testing.assert_allclose(original, decoded, rtol=1e-6)

def test_int32_roundtrip():
    original = np.array([100, -500, 0, 99999], dtype=np.float32)
    encoded = encode_int32(original)
    decoded = decode_int32(encoded, n_samples=4)
    np.testing.assert_allclose(original, decoded, rtol=1e-6)

def test_int16_roundtrip():
    original = np.array([10, -50, 0, 3000], dtype=np.float32)
    encoded = encode_int16(original)
    decoded = decode_int16(encoded, n_samples=4)
    np.testing.assert_allclose(original, decoded, rtol=1e-6)

def test_20bit_bcd_decoder():
    # 4 bytes for 2 samples
    raw = b'\x00\x00\x00\x00'
    decoded = decode_20bit_bcd(raw, n_samples=2)
    assert len(decoded) == 2
