import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from compression import *

def open_atr(data):
    compressed_offset = int.from_bytes(data[0x08:0x0C], "little")

    compressed_data = bytearray(data[compressed_offset:])

    result = decompress(compressed_data)

    if result:
        print(result.hex(" "))

    return result
