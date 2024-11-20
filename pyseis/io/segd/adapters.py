from construct import Adapter, Subconstruct
import numpy as np
import hexdump


class BCDField(Adapter):
    """Adapter for Binary Coded Decimal (BCD) fields in SEG-D.
    
    Handles both regular BCD values (like "1234") and special values (like "FFFF").
    Each digit is stored in 4 bits, allowing values 0-9 and F.
    """
    def __init__(self, subcon):
        super().__init__(subcon)
    
    def _encode(self, obj, context, path):
        """Convert hex string or number to binary for writing.
        
        Args:
            obj: Input value (string or int)
                e.g., "1234" or "FFFF" -> 0x1234 or 0xFFFF
                      8058 -> 0x8058
        Returns:
            int: Binary representation of the BCD value
        """
        if isinstance(obj, str):
            return int(obj, 16)  # Handle hex strings like "FFFF"
        elif isinstance(obj, int):
            # Convert decimal to BCD, each digit becomes 4 bits
            # e.g., 8058 -> 0x8058
            bcd = 0
            for i, digit in enumerate(str(obj)[::-1]):
                bcd |= (int(digit) << (4 * i))
            return bcd
        return obj
    
    def _decode(self, obj, context, path):
        """Convert binary to hex string or number when reading.
        
        Args:
            obj: Binary value to decode
        Returns:
            Union[str, int]: Hex string if contains 'F', otherwise decimal number
                e.g., 0x1234 -> 4660 (if valid number)
                      0xFFFF -> "FFFF" (if contains F)
        """
        num_digits = self.subcon.length // 4  # 4 bits = 1 hex digit
        hex_str = np.base_repr(obj, 16).zfill(num_digits)
        # Special handling for values containing 'F'
        if "F" in hex_str:
            return hex_str
        else:
            return int(hex_str)

class HexField(Adapter):
    """Adapter for hexadecimal fields in SEG-D.
    
    Used for fields that should be preserved as hex values without BCD encoding.
    """
    def __init__(self, subcon):
        super().__init__(subcon)
    
    def _encode(self, obj, context, path):
        """Convert number or hex string to binary.
        
        Args:
            obj: Input value (string or int)
                e.g., 0x1234 or "1234" -> 0x1234
        Returns:
            int: Binary representation of the hex value
        """
        if isinstance(obj, str):
            return int(obj.replace('0x', ''), 16)
        return obj
    
    def _decode(self, obj, context, path):
        """Convert binary to zero-padded hex string.
        
        Args:
            obj: Binary value to decode
        Returns:
            str: Zero-padded hex string representation
        """
        return np.base_repr(obj, 16).zfill(self.subcon.length // 4)

class RawHeaderBlockField(Adapter):
    """Adapter for 32-byte header blocks in SEG-D.
    
    Provides both hex and ASCII representations of header blocks,
    useful for debugging and data inspection.
    """
    def __init__(self, subcon):
        super().__init__(subcon)
    
    def _encode(self, obj, context, path):
        """Convert dictionary back to bytes for writing.
        
        Args:
            obj: Dictionary with 'hex' and 'ascii' keys
        Returns:
            bytes: Raw 32-byte block
        """
        if isinstance(obj, dict):
            # Convert hex string back to bytes
            return bytes.fromhex(obj['hex'])
        return obj
    
    def _decode(self, obj, context, path):
        """Return both hex and ASCII representations of the 32-byte block.
        
        Args:
            obj: Raw bytes to decode
        Returns:
            dict: Contains 'hex' (string) and 'ascii' (string) representations
        """
        # Convert to hex
        hex_str = obj.hex().upper()
        
        # Convert to ASCII, replacing non-printable bytes with '.'
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in obj).rstrip('\x00')
        
        return {
            'hex': hex_str,
            'ascii': ascii_str
        }

class BinaryFractionAdapter(Adapter):
    """Adapter for binary fractions in SEG-D.
    
    Handles binary fractions of arbitrary byte length. The binary point is assumed
    to be at the start of the number, making all bits fractional positions.
    
    Args:
        subcon: The construct subconstructor (e.g., Int16ub)
        nbytes: Number of bytes in the fraction (e.g., 2 for 16-bit fraction)
    
    Example:
        For 16-bit fractions:
        "frac" / BinaryFractionAdapter(Int16ub, 2)
        0x8000 -> 0.5
        0x4000 -> 0.25
        0xC000 -> 0.75
        
        For 24-bit fractions:
        "frac" / BinaryFractionAdapter(Int24ub, 3)
        0x800000 -> 0.5
        0x400000 -> 0.25
    """
    def __init__(self, subcon, nbytes):
        super().__init__(subcon)
        self.nbytes = nbytes
        self.divisor = float(1 << (8 * nbytes))  # 2^(8*nbytes)
    
    def _decode(self, obj, context, path):
        """Convert binary fraction to float.
        
        Args:
            obj: Binary integer representing fraction
        Returns:
            float: Decimal representation of binary fraction
        """
        return obj / self.divisor
    
    def _encode(self, obj, context, path):
        """Convert float to binary fraction.
        
        Args:
            obj: Float value to encode
        Returns:
            int: Binary fraction representation
        """
        return int(obj * self.divisor)

class TraceDataAdapter(Adapter):
    """Adapter for trace data samples in SEG-D.
    
    Currently supports:
    - 8058: 32-bit IEEE float format

    need to check endianness
    
    Other formats will raise NotImplementedError.
    """
    def __init__(self, subcon, format_code):
        super().__init__(subcon)
        self.format_code = format_code
    
    def _encode(self, obj, context, path):
        """Convert numpy array to bytes for writing.
        
        Args:
            obj: Numpy array of trace samples
        Returns:
            bytes: Raw byte representation of samples
        Raises:
            NotImplementedError: If format_code not supported
        """
        if self.format_code != 8058:
            raise NotImplementedError(f"Format code {self.format_code} not yet implemented")
        
        # 8058: 32-bit IEEE float big-endian
        return obj.astype('>f4').tobytes()
    
    def _decode(self, obj, context, path):
        """Convert bytes to numpy array based on format code.
        
        Args:
            obj: Raw bytes to decode
        Returns:
            np.ndarray: Array of trace samples
        Raises:
            NotImplementedError: If format_code not supported
        """
        if self.format_code != 8058:
            raise NotImplementedError(f"Format code {self.format_code} not yet implemented")
        
        # 8058: 32-bit IEEE float big-endian
        return np.frombuffer(obj, dtype='>f4')  # >f4 is big-endian float32

class DiagnosticWrapper(Subconstruct):
    """Wrapper that prints diagnostic info during parsing"""
    def __init__(self, subcon, name=""):
        super().__init__(subcon)
        self.name = name
        self.depth = 0
        
    def _parse(self, stream, context, path):
        # Store current position
        pos = stream.tell()
        
        # Read ahead to get raw bytes (safely)
        try:
            size = self.subcon.sizeof()
            peek_bytes = stream.read(size)
            stream.seek(pos)  # Reset position
        except Exception:
            # If we can't determine size, just peek a reasonable amount
            peek_bytes = stream.read(32)
            stream.seek(pos)
        
        # Print diagnostic info
        indent = "  " * self.depth
        print(f"\n{indent}=== Parsing {self.name} at offset {pos} ===")
        print(f"{indent}Raw bytes:")
        print(hexdump.hexdump(peek_bytes, result='return'))
        
        # Increment depth for nested structures
        self.depth += 1
        
        try:
            # Parse the actual data
            result = self.subcon._parse(stream, context, path)
            print(f"{indent}Parsed value: {result}")
        except Exception as e:
            print(f"{indent}ERROR parsing {self.name}: {str(e)}")
            raise
        finally:
            self.depth -= 1
            
        return result

    def _build(self, obj, stream, context, path):
        return self.subcon._build(obj, stream, context, path)