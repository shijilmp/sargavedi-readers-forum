#!/usr/bin/env python3
"""Turns a black-on-white picture of the "സർഗവേദി" brush lettering into wordmark.png
(black shape on a transparent background, tightly cropped). The site colours it with CSS
(see .mast-title in style.css), so the colour can be changed without a new image.

    python tools/make_wordmark.py path/to/lettering.jpg
"""
import os
import sys

from PIL import Image, ImageChops, ImageOps

src = sys.argv[1]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
img = Image.open(src).convert("L")
alpha = ImageOps.invert(img).point(lambda v: 0 if v < 40 else min(255, int((v - 40) * 255 / 175)))
box = alpha.getbbox()
alpha = alpha.crop(box)
pad = 6
canvas = Image.new("L", (alpha.width + 2 * pad, alpha.height + 2 * pad), 0)
canvas.paste(alpha, (pad, pad))
W = 640
canvas = canvas.resize((W, round(canvas.height * W / canvas.width)), Image.LANCZOS)
out = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
out.putalpha(canvas)
out.save(os.path.join(root, "wordmark.png"), optimize=True)
print("wordmark.png", out.size)
