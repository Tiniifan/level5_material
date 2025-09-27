from io import BytesIO

def compress(indata: bytes) -> bytes:
    outstream = BytesIO()

    length = len(indata)
    compression_header = bytes([
        (length << 3) & 0xFF,
        (length >> 5) & 0xFF,
        (length >> 13) & 0xFF,
        (length >> 21) & 0xFF
    ])

    outstream.write(compression_header)
    outstream.write(indata)

    return outstream.getvalue()
