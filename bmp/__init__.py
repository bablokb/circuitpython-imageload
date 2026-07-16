# SPDX-FileCopyrightText: 2026 Bernhard Bablok
# SPDX-FileCopyrightText: 2022-2023 Matt Land
# SPDX-FileCopyrightText: 2018 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# This is based on adafruit_imageload with modifications:
#   - only import modules that are actually used
#   - support loading directly from a socket (currently only supports BMPs)
#   - optionally (re) use a pre-allocated Bitmap-object

"""
Load pixel values (indices or colors) into a bitmap and colors
into a palette from a BMP file.

* Author(s): Scott Shawcroft, Matt Land, Bernhard Bablok
"""

def load(file, bitmap_obj):
  """Loads a bmp image from the open ``file``.

  Returns tuple of `displayio.Bitmap` object and
  `displayio.Palette` object, or `displayio.ColorConverter` object.

  :param file: Open file handle or compatible (like `io.BytesIO`)
  with the data of a BMP file.
  :param bitmap_obj: used if not None. Must be of the correct size/type.
  """

  # the caller has already read 3 bytes (header)
  offset = 0x02
  file.read(10-(offset+1))   # file.seek(10)
  offset = 0x0A
  data_start = int.from_bytes(file.read(4), "little")
  print(f"{data_start=}")
  offset = 0x0E
  #file.seek(14)        # redundant
  bmp_header_length = int.from_bytes(file.read(4), "little")
  offset = 0x12
  print(f"{bmp_header_length=}")
  #file.read(0x12-(offset+1)) # file.seek(0x12)
  # Width of the bitmap in pixels
  _width = int.from_bytes(file.read(4), "little")
  offset = 0x16
  try:
    _height = int.from_bytes(file.read(4), "little")
  except OverflowError as error:
    raise NotImplementedError(
      "Negative height BMP files are not supported on builds without longint"
      ) from error
  print(f"dimensions={_width}x{_height}")
  offset = 0x1A
  file.read(2)        # file.seek(0x1C)  # Number of bits per pixel
  color_depth = int.from_bytes(file.read(2), "little")
  print(f"{color_depth=}")
  offset = 0x1E
  # file.seek(0x1E)   # Compression type
  compression = int.from_bytes(file.read(2), "little")
  print(f"{compression=}")
  offset = 0x20
  file.read(14) #  file.seek(0x2E)  # Number of colors in the color palette
  colors = int.from_bytes(file.read(4), "little")
  print(f"{colors=}")
  offset = 0x32
  bitfield_masks = None
  if compression == 3 and bmp_header_length >= 56:
    bitfield_masks = {}
    endianess = "little" if color_depth == 16 else "big"
    file.read(18)  # file.seek(0x36)
    bitfield_masks["red"] = int.from_bytes(file.read(4), endianess)
    offset = 0x3A
    # file.seek(0x3A)       # redundant
    bitfield_masks["green"] = int.from_bytes(file.read(4), endianess)
    offset = 0x3E
    # file.seek(0x3E)       # redundant
    bitfield_masks["blue"] = int.from_bytes(file.read(4), endianess)
    offset = 0x42

  if compression > 3:
    raise NotImplementedError("bitmask compression unsupported")

  if colors == 0 and color_depth >= 16:
    from . import truecolor
    return truecolor.load(
      file,
      offset,
      _width,
      _height,
      data_start,
      color_depth,
      bitfield_masks,
      bitmap_obj,
      )

  if colors == 0:
    colors = 2**color_depth
  from . import indexed
  return indexed.load(
    file,
    offset,
    _width,
    _height,
    data_start,
    colors,
    color_depth,
    compression,
    bitmap_obj,
    )
