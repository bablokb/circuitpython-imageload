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
Load pixel colors into a bitmap from an truecolor BMP and return the correct colorconverter.

* Author(s): Scott Shawcroft, Matt Land, Bernhard Bablok
"""

import sys
from displayio import Bitmap, ColorConverter, Colorspace

bitfield_colorspaces = (
  {  # 16-bit RGB555
    "mask_values": (0x00007C00, 0x000003E0, 0x0000001F),
    "color_space": Colorspace.RGB555,
  },
  {  # 16-bit RGB565
    "mask_values": (0x0000F800, 0x000007E0, 0x0000001F),
    "color_space": Colorspace.RGB565,
  },
  {  # 24 or 32-bit RGB888 (Alpha ignored for 32-bit)
    "mask_values": (0x0000FF00, 0x00FF0000, 0xFF000000),
    "color_space": Colorspace.RGB888,
  },
)


def bitfield_format(bitfield_mask):
  """Returns the colorspace for the given bitfield mask"""
  mask = (bitfield_mask["red"], bitfield_mask["green"], bitfield_mask["blue"])
  for colorspace in bitfield_colorspaces:
    if colorspace["mask_values"] == mask:
      return colorspace["color_space"]
  return None

def load(
  file,
  width: int,
  height: int,
  data_start: int,
  color_depth: int,
  bitfield_masks,
  bitmap_obj,
):
  """Loads truecolor bitmap data into bitmap and palette objects. Due to the 16-bit limit
  that the bitmap object can hold, colors will be converted to 16-bit RGB565 values.

  :param file file: The open bmp file
  :param int width: Image width in pixels
  :param int height: Image height in pixels
  :param int data_start: Byte location where the data starts (after headers)
  :param int color_depth: Number of bits used to store a value
  :param dict bitfield_masks: The bitfield masks for each color if using bitfield compression
  :param bitmap_obj: used if not None. Must be of the correct size/type.
    """

  converter_obj = None

  # Set up a ColorConverter object and set appropriate colorspace
  # to convert from based on the color depth
  input_colorspace = Colorspace.RGB888
  if bitfield_masks is not None:
    colorspace = bitfield_format(bitfield_masks)
    if colorspace is not None:
      input_colorspace = colorspace
    else:
      raise NotImplementedError("Bitfield mask not supported")
  elif color_depth == 16:
    input_colorspace = Colorspace.RGB555
  converter_obj = ColorConverter(input_colorspace=input_colorspace)

  if sys.maxsize > 1073741823:
    from .negative_height_check import negative_height_check
    # convert unsigned int to signed int when height is negative
    height = negative_height_check(height)

  # create Bitmap object unless it is provided
  if not bitmap_obj:
    bitmap_obj = Bitmap(width, abs(height), 65535)

  file.seek(data_start)
  line_size = width * (color_depth // 8)
  # BMP scan lines are padded to a 4-byte boundary on disk; account
  # for that padding so subsequent row reads stay aligned.
  if line_size % 4 != 0:
    line_size += 4 - line_size % 4

  # Set the read direction based on whether the height value is negative or positive
  if height > 0:
    range1 = height - 1
    range2 = -1
    range3 = -1
  else:
    range1 = 0
    range2 = abs(height)
    range3 = 1

  chunk = bytearray(line_size)
  for y in range(range1, range2, range3):
    file.readinto(chunk)
    bytes_per_pixel = color_depth // 8
    offset = y * width
    for x in range(width):
      i = x * bytes_per_pixel
      if bitfield_masks is not None:
        color = 0
        for byte in range(bytes_per_pixel):
          color |= chunk[i + byte] << (8 * byte)
        mask = bitfield_masks["red"] | bitfield_masks["green"] | bitfield_masks["blue"]
        if color_depth in (24, 32):
          mask = mask >> 8
        pixel = color & mask
      elif color_depth == 16:
        pixel = chunk[i] | chunk[i + 1] << 8
      else:
        pixel = chunk[i + 2] << 16 | chunk[i + 1] << 8 | chunk[i]
      bitmap_obj[offset + x] = converter_obj.convert(pixel)

  return bitmap_obj, ColorConverter(input_colorspace=Colorspace.RGB565)
