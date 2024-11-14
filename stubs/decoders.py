from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Any, Dict
import struct
import codecs

class FormatType(Enum):
    BCD = "bcd"
    UINT = "uint"
    INT = "int"
    STRING = "string"
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    EBCDIC = "ebcdic"
    FORMAT_8036 = "8036"

class DecoderProtocol(Protocol):
    def get(self, blob: bytes, start_byte: float, num_bytes: float) -> Any: ...
    def set(self, blob: bytes, start_byte: float, num_bytes: float, value: Any) -> bytes: ...

@dataclass
class BinaryDecoder:
    """Base class for decoders."""

@dataclass
class IntDecoder(BinaryDecoder):
    signed: bool = True

    def get(self, blob: bytes, start_byte: float, num_bytes: float) -> int:
        start = int(start_byte)
        end = start + int(num_bytes)
        data = blob[start:end]

        fmt = {1: 'b', 2: 'h', 4: 'i', 8: 'q'}.get(int(num_bytes))
        if fmt is None:
            return int.from_bytes(data, byteorder='big', signed=self.signed)
        if not self.signed:
            fmt = fmt.upper()
        fmt = '>' + fmt  # Big-endian
        return struct.unpack(fmt, data)[0]

    def set(self, blob: bytes, start_byte: float, num_bytes: float, value: int) -> bytes:
        start = int(start_byte)
        end = start + int(num_bytes)

        fmt = {1: 'b', 2: 'h', 4: 'i', 8: 'q'}.get(int(num_bytes))
        if fmt is None:
            data = value.to_bytes(int(num_bytes), byteorder='big', signed=self.signed)
        else:
            if not self.signed:
                fmt = fmt.upper()
            fmt = '>' + fmt  # Big-endian
            data = struct.pack(fmt, value)

        return blob[:start] + data + blob[end:]

@dataclass
class StringDecoder(BinaryDecoder):
    encoding: str = 'utf-8'

    def get(self, blob: bytes, start_byte: float, num_bytes: float) -> str:
        start = int(start_byte)
        end = start + int(num_bytes)
        data = blob[start:end]
        return data.decode(self.encoding).rstrip('\x00')

    def set(self, blob: bytes, start_byte: float, num_bytes: float, value: str) -> bytes:
        encoded_value = value.encode(self.encoding)
        if len(encoded_value) > num_bytes:
            raise ValueError("String too long for the specified number of bytes.")
        padded_value = encoded_value.ljust(int(num_bytes), b'\x00')
        start = int(start_byte)
        end = start + int(num_bytes)
        return blob[:start] + padded_value + blob[end:]

@dataclass
class FloatDecoder(BinaryDecoder):
    size: int  # 4 for float32, 8 for float64

    def get(self, blob: bytes, start_byte: float, num_bytes: float) -> float:
        start = int(start_byte)
        data = blob[start:start + self.size]
        if self.size == 4:
            return struct.unpack('>f', data)[0]
        elif self.size == 8:
            return struct.unpack('>d', data)[0]
        else:
            raise ValueError("Unsupported float size.")

    def set(self, blob: bytes, start_byte: float, num_bytes: float, value: float) -> bytes:
        start = int(start_byte)
        if self.size == 4:
            data = struct.pack('>f', value)
        elif self.size == 8:
            data = struct.pack('>d', value)
        else:
            raise ValueError("Unsupported float size.")
        end = start + self.size
        return blob[:start] + data + blob[end:]

@dataclass
class EBCDICDecoder(BinaryDecoder):
    def get(self, blob: bytes, start_byte: float, num_bytes: float) -> str:
        start = int(start_byte)
        end = start + int(num_bytes)
        data = blob[start:end]
        return codecs.decode(data, 'cp500').rstrip('\x00')

    def set(self, blob: bytes, start_byte: float, num_bytes: float, value: str) -> bytes:
        encoded_value = codecs.encode(value.ljust(int(num_bytes)), 'cp500')
        start = int(start_byte)
        end = start + int(num_bytes)
        return blob[:start] + encoded_value[:int(num_bytes)] + blob[end:]

@dataclass
class BCDDecoder(BinaryDecoder):
    def get(self, blob: bytes, start_byte: float, num_bytes: float) -> int:
        start_nibble = int(start_byte * 2)
        num_nibbles = int(num_bytes * 2)
        end_nibble = start_nibble + num_nibbles

        byte_start = start_nibble // 2
        byte_end = (end_nibble + 1) // 2
        data = blob[byte_start:byte_end]

        digits = []
        for i in range(start_nibble, end_nibble):
            byte_index = (i - start_nibble) // 2
            byte = data[byte_index]
            if i % 2 == 0:
                # High nibble
                nibble = (byte >> 4) & 0x0F
            else:
                # Low nibble
                nibble = byte & 0x0F
            digits.append(str(nibble))

        return int(''.join(digits))

    def set(self, blob: bytes, start_byte: float, num_bytes: float, value: int) -> bytes:
        value_str = str(value)
        num_nibbles = int(num_bytes * 2)
        if len(value_str) > num_nibbles:
            raise ValueError("Value too large for the specified number of BCD digits.")
        # Pad with zeros if necessary
        value_str = value_str.zfill(num_nibbles)
        nibbles = [int(ch) for ch in value_str]

        start_nibble = int(start_byte * 2)
        end_nibble = start_nibble + num_nibbles

        byte_start = start_nibble // 2
        byte_end = (end_nibble + 1) // 2
        data = bytearray(blob[byte_start:byte_end])

        for i, nibble in enumerate(nibbles):
            nibble_index = start_nibble + i
            byte_index = (nibble_index - start_nibble) // 2
            if nibble_index % 2 == 0:
                # High nibble
                data[byte_index] &= 0x0F  # Clear high nibble
                data[byte_index] |= (nibble << 4)
            else:
                # Low nibble
                data[byte_index] &= 0xF0  # Clear low nibble
                data[byte_index] |= nibble

        start = byte_start
        end = byte_end
        return blob[:start] + data + blob[end:]

class DecoderFactory:
    _decoders: Dict[FormatType, DecoderProtocol] = {
        FormatType.BCD: BCDDecoder(),
        FormatType.UINT: IntDecoder(signed=False),
        FormatType.INT: IntDecoder(signed=True),
        FormatType.STRING: StringDecoder(),
        FormatType.FLOAT32: FloatDecoder(size=4),
        FormatType.FLOAT64: FloatDecoder(size=8),
        FormatType.EBCDIC: EBCDICDecoder(),
        # Add other decoders as necessary...
    }

    @classmethod
    def get_decoder(cls, format_type: FormatType) -> DecoderProtocol:
        decoder = cls._decoders.get(format_type)
        if decoder is None:
            raise ValueError(f"Unsupported format type: {format_type}")
        return decoder

# Usage Examples:
if __name__ == "__main__":  
    # Example binary blob
    blob = b'\x12\x34\x56\x78\x9A\xBC\xDE\xF0'

    # Decoding an unsigned integer
    decoder = DecoderFactory.get_decoder(FormatType.UINT)
    value = decoder.get(blob, start_byte=0, num_bytes=4)
    print(f"Unsigned Int Value: {value}")

    # Setting a new unsigned integer value
    new_blob = decoder.set(blob, start_byte=0, num_bytes=4, value=123456789)
    print(f"New Blob: {new_blob}")

    # Decoding a BCD value
    decoder = DecoderFactory.get_decoder(FormatType.BCD)
    bcd_value = decoder.get(blob, start_byte=1.0, num_bytes=2.0)
    print(f"BCD Value: {bcd_value}")

    # Setting a new BCD value
    new_blob = decoder.set(blob, start_byte=1.0, num_bytes=2.0, value=1234)
    print(f"New Blob after BCD set: {new_blob}")

    # Decoding a float32 value
    decoder = DecoderFactory.get_decoder(FormatType.FLOAT32)
    float_value = decoder.get(blob, start_byte=0, num_bytes=4)
    print(f"Float32 Value: {float_value}")

    # Setting a new float32 value
    new_blob = decoder.set(blob, start_byte=0, num_bytes=4, value=3.14)
    print(f"New Blob after Float32 set: {new_blob}")
