"""Draw the 1200x630 share image (site/og.png) in the site's pulp-paperback style.

Usage: uv run --with pillow python scripts/make_og_image.py <fonts dir>
The fonts dir needs Anton-Regular.ttf and LibreFranklin.ttf (both SIL Open Font Licence, from Google Fonts).
"""

import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
PAPER, PAGE, INK, RED = (239, 237, 231), (255, 255, 255), (17, 17, 17), (200, 50, 31)
ROOT = Path(__file__).resolve().parents[1]
fonts = Path(sys.argv[1])


def franklin(size, weight="Bold"):
    f = ImageFont.truetype(str(fonts / "LibreFranklin.ttf"), size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


anton = lambda size: ImageFont.truetype(str(fonts / "Anton-Regular.ttf"), size)  # noqa: E731

img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img)

# Paper grain.
rng = random.Random(7)
for _ in range(26000):
    x, y = rng.randrange(W), rng.randrange(H)
    v = rng.randrange(-14, 6)
    r, g, b = img.getpixel((x, y))
    img.putpixel((x, y), (r + v, g + v, b + v))

# The "book": hard shadow, frame, red cover band with halftone, white page.
x0, y0, x1, y1 = 56, 44, 1132, 572
d.rectangle([x0 + 14, y0 + 14, x1 + 14, y1 + 14], fill=INK)
d.rectangle([x0, y0, x1, y1], fill=PAGE, outline=INK, width=6)
band_bottom = 352
d.rectangle([x0 + 6, y0 + 6, x1 - 6, band_bottom], fill=RED)
for yy in range(y0 + 10, band_bottom - 2, 9):
    for xx in range(x0 + 10 + (yy // 9 % 2) * 4, x1 - 8, 9):
        d.ellipse([xx - 1.6, yy - 1.6, xx + 1.6, yy + 1.6], fill=(170, 40, 25))
d.line([x0, band_bottom + 3, x1, band_bottom + 3], fill=INK, width=6)

# Cover text.
d.text((x0 + 44, y0 + 34), "THE NARRATED SELF", font=franklin(30, "ExtraBold"), fill=PAGE)
title = "WHO WROTE THIS?"
max_w = (x1 - x0) - 2 * 44
size = 200
while d.textlength(title, font=anton(size)) > max_w:
    size -= 2
d.text((x0 + 48, y0 + 86), title, font=anton(size), fill=INK)  # misregistered print layer
d.text((x0 + 42, y0 + 80), title, font=anton(size), fill=PAGE)

# Page text and the five answers.
line = "Short stories AI models wrote about themselves. Guess the author."
size = 34
while d.textlength(line, font=franklin(size, "SemiBold")) > max_w:
    size -= 1
d.text((x0 + 44, band_bottom + 30), line, font=franklin(size, "SemiBold"), fill=INK)
names = ["CLAUDE", "GPT", "GEMINI", "GROK", "MIMO"]
bx, by, bw, bh, gap = x0 + 44, band_bottom + 96, 178, 74, 20
for name in names:
    d.rectangle([bx + 6, by + 6, bx + bw + 6, by + bh + 6], fill=INK)
    d.rectangle([bx, by, bx + bw, by + bh], fill=PAGE, outline=INK, width=5)
    f = anton(40)
    tw = d.textlength(name, font=f)
    d.text((bx + (bw - tw) / 2, by + 11), name, font=f, fill=INK)
    bx += bw + gap

d.text((x1 - 44, y1 + 30), "narratedself.airiskpractice.org", font=franklin(26, "Bold"), fill=INK, anchor="rt")

out = ROOT / "site" / "og.png"
img.save(out, optimize=True)
print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")
