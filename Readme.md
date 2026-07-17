Optimized ImageLoad Library
===========================

**WORK IN PROGRESS**

This is a fork of <http://github.com/adafruit/Adafruit_CircuitPython_ImageLoad>.

Main changes
------------

  - support loading images directly from a `Response`-object
  - support reusing of `Bitmap`-objects

Status
------

  - implemented currently only for BMPs

The changes to the original library might or might not be merged into
the upstream project. This probably depends on Adafruit policy.


Rationale
---------

The original repository gives an example on how to load an image
from the web (in `examples/imageload_from_web.py`):

```
bytes_img = BytesIO(response.content)
image, palette = adafruit_imageload.load(bytes_img)
```

Here, `response.content` creates a `bytes`-object with the complete
image. `BytesIO(...)` *copies* the argument byte-string to a
bytearray-buffer. `adafruit_imageload.load(bytes_img)` then creates
a `Bitmap`-object of the required size and copies the contents
again.

Needless to say this wastes RAM and triggers a `MemoryError` on systems
with limited RAM.
