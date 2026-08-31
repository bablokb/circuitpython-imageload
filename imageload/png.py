# SPDX-FileCopyrightText: 2026 Bernhard Bablok
# SPDX-FileCopyrightText: 2022 Radomir Dopieralski
# SPDX-FileCopyrightText: 2023 Matt Land
# SPDX-FileCopyrightText: 2024 Channing Ramos
#
# SPDX-License-Identifier: MIT

# This is based on adafruit_imageload with modifications:
#   - only import modules that are actually used
#   - optionally (re) use a pre-allocated Bitmap-object

"""
`imageload.png`
====================================================

Load pixel values (indices or colors) into a bitmap and colors into a palette
from a PNG file.

* Author(s): Bernhard Bablok, Radomir Dopieralski, Matt Land, Channing Ramos

"""

import displayio
import struct
import zlib

def load(file, bitmap_obj):
    """
    Loads a PNG image from the open ``file``.
    Only supports indexed color images.

    Returns tuple of bitmap object and palette object.

    :param file: Open file handle or compatible (like `io.BytesIO`)
      with the data of a PNG file.
    :param bitmap_obj: used if not None, Must be of the correct size/type.
    """
    file.seek(8)
    data = bytearray()
    pal = None
    mode = None
    depth = 0
    width = 0
    height = 0
    while True:
        size, chunk = struct.unpack(">I4s", file.read(8))
        if chunk == b"IHDR":
            (
                width,
                height,
                depth,
                mode,
                compression,
                filters,
                interlaced,
            ) = struct.unpack(">IIBBBBB", file.read(13))
            if interlaced:
                raise NotImplementedError("Interlaced images unsupported")
            # compression and filters must be 0 with current spec
            assert compression == 0
            assert filters == 0
        elif chunk == b"PLTE":
            if mode != 3:
                raise NotImplementedError("Palette in non-indexed image")
            pal_size = size // 3
            pal = displayio.Palette(pal_size)
            for i in range(pal_size):
                pal[i] = file.read(3)
        elif chunk == b"tRNS":
            if size > len(pal):
                raise ValueError("More transparency entries than palette entries")
            trns_data = file.read(size)
            for i in range(len(trns_data)):
                if trns_data[i] == 0:
                    pal.make_transparent(i)
            del trns_data
        elif chunk == b"IDAT":
            data.extend(file.read(size))
        elif chunk == b"IEND":
            break
        else:
            file.seek(size, 1)  # skip unknown chunks
        file.seek(4, 1)  # skip CRC
    data_bytes = zlib.decompress(data)
    unit = (1, 0, 3, 1, 2, 0, 4)[mode]
    scanline = (width * depth * unit + 7) // 8
    if mode == 3:  # indexed
        if bitmap_obj:
            bmp = bitmap_obj
        else:
            bmp = displayio.Bitmap(width, height, 1 << depth)
        pixels_per_byte = 8 // depth
        src = 0
        pixmask = (1 << depth) - 1
        line = bytearray(scanline)
        prev = bytearray(scanline)
        for y in range(height):
            filter_ = data_bytes[src]
            src_b = src + 1
            for x in range(0, width, pixels_per_byte):
                # relative position on the line
                pos = x // pixels_per_byte
                byte = data_bytes[src_b]
                if filter_ == 0:
                    pass
                elif filter_ == 1:  # sub
                    prev_b = line[pos - unit] if pos >= unit else 0
                    byte = (byte + prev_b) & 0xFF
                elif filter_ == 2:  # up
                    byte = (byte + prev[pos]) & 0xFF
                elif filter_ == 3:  # average
                    prev_b = line[pos - unit] if pos >= unit else 0
                    byte = (byte + (prev_b + prev[pos]) // 2) & 0xFF
                elif filter_ == 4:  # paeth
                    a = line[pos - unit] if pos >= unit else 0
                    if y > 0:
                        b = prev[pos]
                        c = prev[pos - unit] if pos >= unit else 0
                    else:
                        b = c = 0
                    p = a + b - c
                    pa = abs(p - a)
                    pb = abs(p - b)
                    pc = abs(p - c)
                    if pa <= pb and pa <= pc:
                        p = a
                    elif pb <= pc:
                        p = b
                    else:
                        p = c
                    byte = (byte + p) & 0xFF
                else:
                    raise ValueError("Wrong filter.")
                line[pos] = byte
                for pixel in range(pixels_per_byte):
                    if x + pixel < width:
                        bmp[x + pixel, y] = (
                            byte >> ((pixels_per_byte - pixel - 1) * depth)
                        ) & pixmask
                src_b += 1
            src += scanline + 1
            prev, line = line, prev
        return bmp, pal
    # RGB, RGBA or Grayscale

    if depth != 8:
        raise ValueError("Must be 8bit depth.")
    pal = displayio.ColorConverter(input_colorspace=displayio.Colorspace.RGB888)
    if bitmap_obj:
        bmp = bitmap_obj
    else:
        bmp = displayio.Bitmap(width, height, 65536)
    prev = bytearray(scanline)
    line = bytearray(scanline)
    for y in range(height):
        src = y * (scanline + 1)
        filter_ = data_bytes[src]
        src += 1
        if filter_ == 0:
            line[0:scanline] = data_bytes[src : src + scanline]
        elif filter_ == 1:  # sub
            for i in range(scanline):
                a = line[i - unit] if i >= unit else 0
                line[i] = (data_bytes[src] + a) & 0xFF
                src += 1
        elif filter_ == 2:  # up
            for i in range(scanline):
                b = prev[i]
                line[i] = (data_bytes[src] + b) & 0xFF
                src += 1
        elif filter_ == 3:  # average
            for i in range(scanline):
                a = line[i - unit] if i >= unit else 0
                b = prev[i]
                line[i] = (data_bytes[src] + ((a + b) >> 1)) & 0xFF
                src += 1
        elif filter_ == 4:  # paeth
            for i in range(scanline):
                a = line[i - unit] if i >= unit else 0
                b = prev[i]
                c = prev[i - unit] if i >= unit else 0
                p = a + b - c
                pa = abs(p - a)
                pb = abs(p - b)
                pc = abs(p - c)
                if pa <= pb and pa <= pc:
                    p = a
                elif pb <= pc:
                    p = b
                else:
                    p = c
                line[i] = (data_bytes[src] + p) & 0xFF
                src += 1
        else:
            raise ValueError("Wrong filter.")
        if mode in (0, 4):  # grayscale
            for x in range(width):
                c = line[x * unit]
                bmp[x, y] = pal.convert((c << 16) | (c << 8) | c)
        elif mode in {2, 6}:  # rgb
            for x in range(width):
                bmp[x, y] = pal.convert(
                    (line[x * unit + 0] << 16) | (line[x * unit + 1] << 8) | line[x * unit + 2]
                )
        else:
            raise ValueError("Unsupported color mode.")

        prev, line = line, prev

    pal = displayio.ColorConverter(input_colorspace=displayio.Colorspace.RGB565)
    return bmp, pal
