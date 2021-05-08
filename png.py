import zlib
import numpy as np

# http://www.libpng.org/pub/png/spec/1.2/PNG-Structure.html
png_header = bytes([137, 80, 78, 71, 13, 10, 26, 10])

# Generate crc table
crc_table = []
for n in range(256):
    c = n
    for k in range(8):
        if c & 1:
            c = (0xedb88320 ^ (c >> 1)) & 0xFFFFFFFF
        else:
            c = (c >> 1) & 0xFFFFFFFF
    crc_table.append(c)

def update_crc(crc, data):
    c = crc
    for b in data:
        c = (crc_table[(c ^ b) & 0xFF] ^ (c >> 8)) & 0xFFFFFFFF
    return c

def get_crc(data):
    crc = update_crc(0xffffffff, data) ^ 0xFFFFFFFF
    return crc.to_bytes(4, byteorder='big')

def create_chunk(type, data):
    len_bytes = len(data).to_bytes(4, byteorder='big')
    chunk = type.encode('latin-1')
    chunk += data
    crc = get_crc(chunk)
    return len_bytes + chunk + crc

def ihdr_chunk(width, height):
    data = width.to_bytes(4, byteorder='big')
    data += height.to_bytes(4, byteorder='big')
    data += bytes([8, 2, 0, 0, 0])
    return create_chunk("IHDR", data)

def idat_data(pixel_data):
    height, width, px_len = pixel_data.shape
    reshaped = pixel_data.reshape((height, width * px_len))
    with_filter = np.insert(reshaped, 0, 0, 1)
    return zlib.compress(bytes(with_filter), level=6)

def idat_chunk(pixel_data):
    return create_chunk("IDAT", idat_data(pixel_data))

def text_chunk(keyword, text):
    result = keyword.encode('latin-1') + bytes([0])
    result += text.encode('latin-1')
    return create_chunk("tEXt", result)

iend = create_chunk("IEND", bytes())
def iend_chunk():
    return iend

def actl_chunk(frames, plays):
    data = frames.to_bytes(4, byteorder='big')
    data += plays.to_bytes(4, byteorder='big')
    return create_chunk("acTL", data)

def fctl_chunk(seq, width, height, x_offset, y_offset, delay_num, delay_den):
    data = seq.to_bytes(4, byteorder='big')
    data += width.to_bytes(4, byteorder='big')
    data += height.to_bytes(4, byteorder='big')
    data += x_offset.to_bytes(4, byteorder='big')
    data += y_offset.to_bytes(4, byteorder='big')
    data += delay_num.to_bytes(2, byteorder='big')
    data += delay_den.to_bytes(2, byteorder='big')
    data += bytes([0, 0])
    return create_chunk("fcTL", data)

def fdat_chunk(seq, pixel_data):
    return create_chunk("fdAT", seq.to_bytes(4, byteorder='big') + idat_data(pixel_data))

# todo: make this smarter
def frame_chunks(seq, old_frame, new_frame, delay_num, delay_den):
    height, width, _ = new_frame.shape
    data = fctl_chunk(seq, width, height, 0, 0, delay_num, delay_den)
    data += fdat_chunk(seq + 1, new_frame)
    return data

def multi_frame_chunks(seq, old_frame, new_frames):
    result = bytes()
    for frame, delay_num, delay_den in new_frames:
        result += frame_chunks(seq, old_frame, frame, delay_num, delay_den)
        seq += 2
        old_frame = frame
    return result, old_frame, seq
