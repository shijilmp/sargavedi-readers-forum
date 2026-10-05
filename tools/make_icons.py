"""Draws the Sargavedi badge (same artwork as logo.svg) with Pillow and writes
favicon.ico, icon-192.png, icon-512.png and apple-touch-icon.png.

Run from the project root:  python tools/make_icons.py
Pillow has no SVG support, so the shapes below mirror logo.svg (120 x 120 grid).
"""
import math
import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SS = 8  # supersampling factor


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def bezier(p0, p1, p2, p3, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0]
        y = u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]
        pts.append((x, y))
    return pts


def badge(size, full_bleed=False, scale=1.0):
    """Return an RGBA image of the badge. full_bleed fills the whole square with teal."""
    S = size * SS
    k = S / 120.0 * scale
    off = (S - 120 * k) / 2

    def P(pt):
        return (off + pt[0] * k, off + pt[1] * k)

    teal_top, teal_bot = hexc("#36908f"), hexc("#1b5556")
    gold = hexc("#d9a73a")

    # background gradient, vertical over the badge
    grad = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    y0, y1 = off, off + 120 * k
    for y in range(S):
        t = min(1, max(0, (y - y0) / (y1 - y0)))
        gd.line([(0, y), (S, y)], fill=lerp(teal_top, teal_bot, t) + (255,))

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    mask = Image.new("L", (S, S), 0)
    md = ImageDraw.Draw(mask)
    if full_bleed:
        md.rectangle([0, 0, S, S], fill=255)
        # outer gold ring drawn inside the square as well
    else:
        cx, cy = P((60, 60))
        r = 58 * k
        md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)

    cx, cy = P((60, 60))
    # gold outer ring
    r = 58 * k
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=gold + (255,), width=max(1, int(3 * k)))
    # faint inner ring
    r = 51 * k
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=hexc("#f3d58b") + (140,), width=max(1, int(1 * k)))

    # sun rays
    ray = hexc("#f6cf6f") + (255,)
    sx, sy = P((60, 44))
    for ang in range(-80, 81, 20):
        a = math.radians(ang)
        for (r0, r1) in ((23, 30),):
            x0, y0_ = sx + math.sin(a) * r0 * k, sy - math.cos(a) * r0 * k
            x1, y1_ = sx + math.sin(a) * r1 * k, sy - math.cos(a) * r1 * k
            w = 2.6 * k
            d.line([(x0, y0_), (x1, y1_)], fill=ray, width=int(w))
            for (x, y) in ((x0, y0_), (x1, y1_)):
                d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=ray)
    # sun
    sr = 14 * k
    for i in range(int(2 * sr)):
        t = i / (2 * sr)
        col = lerp(hexc("#ffd87a"), hexc("#e6a82e"), t) + (255,)
        yy = sy - sr + i
        half = math.sqrt(max(0, sr * sr - (yy - sy) ** 2))
        d.line([(sx - half, yy), (sx + half, yy)], fill=col)

    # book pages
    left = [P(p) for p in ([(60, 100)] + bezier((60, 100), (48, 92), (33, 90), (18, 92))
                             + [(18, 62)] + bezier((18, 62), (33, 60), (48, 62), (60, 71)))]
    right = [P(p) for p in ([(60, 100)] + bezier((60, 100), (72, 92), (87, 90), (102, 92))
                              + [(102, 62)] + bezier((102, 62), (87, 60), (72, 62), (60, 71)))]
    d.polygon(left, fill=hexc("#fbf7ee") + (255,))
    d.polygon(right, fill=hexc("#efe8d8") + (255,))

    gw = max(1, int(2.4 * k))
    edge = bezier((18, 92), (33, 90), (48, 92), (60, 100)) + bezier((60, 100), (72, 92), (87, 90), (102, 92))[1:]
    d.line([P(p) for p in edge], fill=gold + (255,), width=gw, joint="curve")
    d.line([P((60, 71)), P((60, 100))], fill=gold + (255,), width=max(1, int(2.6 * k)))

    # page lines
    lc = hexc("#9db5b5") + (255,)
    lw = max(1, int(1.4 * k))
    for dy in (0, 7, 14):
        a = bezier((26, 71 + dy), (34, 70 + dy), (42, 71 + dy), (52, 76 + dy), 20)
        b = bezier((94, 71 + dy), (86, 70 + dy), (78, 71 + dy), (68, 76 + dy), 20)
        d.line([P(p) for p in a], fill=lc, width=lw, joint="curve")
        d.line([P(p) for p in b], fill=lc, width=lw, joint="curve")

    return img.resize((size, size), Image.LANCZOS)


def main():
    out = lambda n: os.path.join(ROOT, n)
    badge(512).save(out("icon-512.png"))
    badge(192).save(out("icon-192.png"))
    # iOS rounds the corners itself and shows transparency as black: fill the square.
    badge(180, full_bleed=True, scale=0.9).save(out("apple-touch-icon.png"))
    big = badge(256)
    big.save(out("favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
    print("icons written")


if __name__ == "__main__":
    main()
