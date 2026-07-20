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
Load pixel values (indices or colors) into a bitmap and colors into a palette.

* Author(s): Scott Shawcroft, Matt Land, Bernhard Bablok
"""

# import ResponseReader into the namespace of this module
from .responsereader import ResponseReader

# --- load multiplexer   -----------------------------------------------------

def load(file_or_filename,
         bitmap_obj=None):
  """Load pixel values (indices or colors) into a bitmap and
  colors into a palette.

  :param file_or_filename: Filename or open file handle or compatible
  (like `io.BytesIO`) with the data of a BMP file.
  :param bitmap_obj: used if not None. Must be of the correct size/type.
  """
  if isinstance(file_or_filename, str):
    open_file = open(file_or_filename, "rb")
  else:
    open_file = file_or_filename

  with open_file as file:
    header = file.read(3)
    #print(f"{header=}")
    if header.startswith(b"BM"):
      from . import bmp
      return bmp.load(file, bitmap_obj)
    if header.startswith(b"\x89PN"):
      from . import png
      return png.load(file, bitmap_obj)

    # use adafruit_imageload as is
    import displayio

    if header.startswith(b"P"):
      from . import pnm
      return pnm.load(file, header,
                      bitmap=displayio.Bitmap,
                      palette=displayio.Palette,
                      )
    if header.startswith(b"GIF"):
      from . import gif
      return gif.load(file,
                      bitmap=displayio.Bitmap,
                      palette=displayio.Palette,
                      )
    if header.startswith(b"\xff\xd8"):
      from . import jpg
      return jpg.load(file,
                      bitmap=displayio.Bitmap,
                      )
    raise RuntimeError("Unsupported image format")
