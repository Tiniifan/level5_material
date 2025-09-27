import sys, os
import struct
import json

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from compression import compress, decompress

class MTRParser:
    def __init__(self, data):
        self.data = data
        self.mtr_data = {}
        self.lut_datas = []

    def parse(self):
        self._parse_header()
        self._parse_mtr_data()
        self._parse_luts()
        return {
            "MTRData": self.mtr_data,
            "LUTDatas": self.lut_datas
        }

    def _parse_header(self):
        header = self.data[0x00:0x08]
        if header != b'MTRC00\x00\x00':
            raise ValueError("Invalid MTR header")
        
        self.compressed_offset = struct.unpack('<H', self.data[0x08:0x0A])[0]
        self.lutc_first_offset = struct.unpack('<H', self.data[0x0A:0x0C])[0]
        self.lutc_second_offset = struct.unpack('<H', self.data[0x10:0x12])[0]
        self.lutc_third_offset = struct.unpack('<H', self.data[0x12:0x14])[0]

    def _parse_mtr_data(self):
        compressed_data = self.data[self.compressed_offset:]
        decompressed_data = decompress(compressed_data)
        
        # Extract integers
        mtr_ints = [struct.unpack('<I', decompressed_data[i:i+4])[0] for i in range(0, 0x80, 4)]
        
        # Extract floats
        mtr_floats = [round(struct.unpack('<f', decompressed_data[i:i+4])[0], 10) for i in range(0x80, 0xE4, 4)]
        
        # Extract CRC32
        crc32_bytes = decompressed_data[0xE4:0xE8]
        crc32_hex = crc32_bytes.hex().upper()
        
        self.mtr_data = {
            "integers": mtr_ints,
            "floats": mtr_floats,
            "CRC32": crc32_hex
        }

    def _parse_luts(self):
        # Determine number of LUT sections
        if self.lutc_first_offset == self.lutc_second_offset == self.lutc_third_offset:
            lut_offsets = [self.lutc_first_offset]
        elif self.lutc_first_offset != self.lutc_second_offset and self.lutc_second_offset == self.lutc_third_offset:
            lut_offsets = [self.lutc_first_offset, self.lutc_second_offset]
        else:
            lut_offsets = [self.lutc_first_offset, self.lutc_second_offset, self.lutc_third_offset]
        
        # Parse each LUT
        for lut_offset in lut_offsets:
            if lut_offset == 0x00:
                continue

            lut_header = self.data[lut_offset:lut_offset+8]
            if lut_header != b'LUTC00\x00\x00':
                raise ValueError(f"Invalid LUT header at offset {lut_offset}")
            
            lut_compressed_offset = struct.unpack('<H', self.data[lut_offset+0x0A:lut_offset+0x0C])[0]
            lut_compressed_data = self.data[lut_offset + lut_compressed_offset:]
            lut_decompressed = decompress(lut_compressed_data)
            
            lut_floats = [round(struct.unpack('<f', lut_decompressed[i:i+4])[0], 10)
                          for i in range(0, len(lut_decompressed), 4) if i + 4 <= len(lut_decompressed)]
            
            self.lut_datas.append(lut_floats)

class MTRSerializer:
    def __init__(self, data):
        self.data = data
        self.mtr_data = data.get("MTRData", {})
        self.lut_datas = data.get("LUTDatas", [])
    
    def serialize(self):
        # Build MTR data section
        mtr_section = self._build_mtr_section()
        
        # Compress MTR data
        compressed_mtr = compress(mtr_section)
        
        # Build LUT sections
        lut_sections = []
        for lut_data in self.lut_datas:
            lut_section = self._build_lut_section(lut_data)
            lut_sections.append(lut_section)
        
        # Calculate offsets (aligned on 4 bytes)
        header_size = 0x18  # MTR header is 24 bytes
        compressed_offset = header_size
        
        current_offset = header_size + len(compressed_mtr)
        # Align to 4 bytes boundary
        current_offset = (current_offset + 3) & ~3
        
        lut_offsets = []
        
        for lut_section in lut_sections:
            lut_offsets.append(current_offset)
            current_offset += len(lut_section)
            current_offset = (current_offset + 3) & ~3
        
        # Pad lut_offsets to 3 elements (duplicate last offset if needed)
        while len(lut_offsets) < 3:
            lut_offsets.append(lut_offsets[-1] if lut_offsets else 0)
        
        # Build header
        header = self._build_header(compressed_offset, lut_offsets)
        
        # Combine all sections with proper alignment
        result = header + compressed_mtr
        
        # Add padding to align first LUT section
        while len(result) % 4 != 0:
            result += b'\x00'
        
        for i, lut_section in enumerate(lut_sections):
            result += lut_section
            # Add padding between sections (except for the last one)
            if i < len(lut_sections) - 1:
                while len(result) % 4 != 0:
                    result += b'\x00'
        
        return result
    
    def _build_header(self, compressed_offset, lut_offsets):
        header = bytearray(0x18)
        
        # MTR signature
        header[0x00:0x08] = b'MTRC00\x00\x00'
        
        # Compressed offset
        struct.pack_into('<H', header, 0x08, compressed_offset)
        
        # LUT offsets
        struct.pack_into('<H', header, 0x0A, lut_offsets[0])
        struct.pack_into('<H', header, 0x10, lut_offsets[1])
        struct.pack_into('<H', header, 0x12, lut_offsets[2])
        
        return bytes(header)
    
    def _build_mtr_section(self):
        section = bytearray(0xE8)
        
        # Pack integers (0x00 to 0x7F)
        integers = self.mtr_data.get("integers", [])
        for i, int_val in enumerate(integers[:32]):  # Max 32 integers
            offset = i * 4
            struct.pack_into('<I', section, offset, int_val)
        
        # Pack floats (0x80 to 0xE3)
        floats = self.mtr_data.get("floats", [])
        for i, float_val in enumerate(floats[:25]):  # Max 25 floats
            offset = 0x80 + (i * 4)
            struct.pack_into('<f', section, offset, float_val)
        
        # Pack CRC32 (0xE4 to 0xE7)
        crc32_str = self.mtr_data.get("CRC32", "00000000")
        crc32_bytes = bytes.fromhex(crc32_str)
        section[0xE4:0xE8] = crc32_bytes
        
        return bytes(section)
    
    def _build_lut_section(self, lut_floats):
        # Build LUT data (just floats)
        lut_data = bytearray()
        for float_val in lut_floats:
            lut_data.extend(struct.pack('<f', float_val))
        
        # Compress LUT data
        compressed_lut = compress(bytes(lut_data))
        
        # Build LUT header
        lut_header = bytearray(0x10)  # 16 bytes header
        
        # LUT signature
        lut_header[0x00:0x08] = b'LUTC00\x00\x00'
        
        # Compressed offset (header size = 0x10)
        struct.pack_into('<H', lut_header, 0x0A, 0x10)
        
        # Combine header and compressed data
        return bytes(lut_header) + compressed_lut