# SPDX-FileCopyrightText: 2026 Bernhard Bablok
#
# SPDX-License-Identifier: MIT
"""
Read data on-the-fly from a Response-object.

* Author(s): Bernhard Bablok
"""

# --- a minimalistic ResponseReader   ----------------------------------------

class ResponseReader:
  """ A minimalistic Response reader """
  def __init__(self, response):
    self._response = response
    self._index = 0
  def __enter__(self):
    return self

  def __exit__(self, exception_type, exception_value, traceback):
    try:
      self.close()
    except:
      pass
    return False

  def close(self):
    """ close the reader and the underlying Response """
    self._response.close()
    print(f"total bytes read: {self._index}")

  def read(self, n):
    buf = bytearray(n)
    count = self._response._readinto(buf)
    self._index += count 
    return bytes(buf)

  def readinto(self, buf):
    self._index += len(buf)
    return self._response._readinto(buf)

  def tell(self):
    """ return current position """
    return self._index

  def seek(self, offset, whence=0):
    """ seek to the given offset. Only forward seeks are allowed """
    if whence == 0:
      # absolute seek
      if offset > self._index:
        self.read(offset-self._index)
      elif offset < self._index:
        raise NotImplementedError("only forward seek possible")
    elif whence == 1:
      # relative seek
      if offset > 0:
        self.read(offset)
      elif offset < 0:
        raise NotImplementedError("only forward seek possible")
    elif whence == 2:
      # relative from end
      raise NotImplementedError("only forward seek possible")
    return self._index
