"""Re-bake the grayscale portrait grid embedded in ../generate_profile.py.

Reads tools/headshot.png (an RGBA cut-out — background already removed) and
prints a `FACE = [...]` block: one (glyphs, levels) tuple per row, where each
level char '0'..'P' is a 0..25 brightness bucket. Paste the output over the
FACE list in generate_profile.py when the photo changes.

Dependencies: Pillow + numpy only (no ML / no network).

    python3 tools/bake_face.py > /tmp/face.py

Tunables below (COLS, CROP, CONTRAST, GAMMA, LOCAL) were chosen so the face
reads clearly at the card's 9px font. CROP focuses on head + shoulders.
"""
import os
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "headshot.png")

RAMP = " .`-:_,~^=+ilcvtxznuoJCYUXZO0Q4kdbphaw%#W@M"   # dark -> light density
LVL = "0123456789ABCDEFGHIJKLMNOP"                      # 26 brightness buckets

COLS = 88
CROP = (189, 66, 721, 712)     # head+shoulders window (for the 900px source)
CELL_ASPECT = 0.5
CONTRAST, GAMMA, LOCAL, SHARP, ALPHA_TH = 1.14, 0.96, 1.15, 150, 70


def bake():
    im = Image.open(SRC).convert("RGBA").crop(CROP)
    a0 = np.asarray(im.split()[3])
    ys, xs = np.where(a0 > ALPHA_TH)
    pad = 4
    im = im.crop((max(0, xs.min() - pad), max(0, ys.min() - pad),
                  min(im.width, xs.max() + pad), min(im.height, ys.max() + pad)))
    w, h = im.size
    rows = max(1, round(COLS * (h / w) * CELL_ASPECT))
    s = im.resize((COLS, rows), Image.LANCZOS)
    alpha = np.asarray(s.split()[3])
    lum = np.asarray(s.convert("RGB").convert("L")
                     .filter(ImageFilter.UnsharpMask(2, SHARP)), float)
    blur = np.asarray(Image.fromarray(lum.astype("uint8"))
                      .filter(ImageFilter.GaussianBlur(3)), float)
    lum = np.clip(lum + LOCAL * (lum - blur), 0, 255)
    lum = np.asarray(ImageEnhance.Contrast(Image.fromarray(lum.astype("uint8")))
                     .enhance(CONTRAST), float)
    lum = 255 * np.clip(lum / 255, 0, 1) ** GAMMA
    grid = []
    for y in range(rows):
        glyphs, levels = [], []
        for x in range(COLS):
            if alpha[y, x] < ALPHA_TH:
                glyphs.append(" "); levels.append("0")
                continue
            t = lum[y, x] / 255.0
            glyphs.append(RAMP[min(len(RAMP) - 1, int(t * len(RAMP)))])
            levels.append(LVL[min(25, round(t * 25))])
        g = "".join(glyphs).rstrip()
        grid.append((g, "".join(levels[:len(g)])))
    while grid and not grid[0][0].strip():
        grid.pop(0)
    while grid and not grid[-1][0].strip():
        grid.pop()
    return grid


if __name__ == "__main__":
    print("FACE = [")
    for g, l in bake():
        print(f"    ({g!r}, {l!r}),")
    print("]")
