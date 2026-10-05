#!/usr/bin/env python3
"""Shrinks the photos in images/ so pages load fast, without visible quality loss.

    python tools/compress_images.py --dry     (report only, changes nothing)
    python tools/compress_images.py           (apply)

Rules
  * JPEGs are re-saved at quality 82 and limited to 1600 px wide (the page column is 800 px,
    so this still looks sharp on phones with 2x screens). Phone rotation is baked in.
  * Images used only as small book covers / portraits (max-width:300px in the HTML) are limited to 900 px.
  * PNG photos without transparency become JPEG (same name, .jpg) and every HTML/CSS reference is updated.
    PNGs that really use transparency stay PNG, only resized.
  * images/collage.png (the home-page background) is limited to 1200 px wide.
  * Files that are already small are left alone, so the script is safe to run again after you add photos.
Originals are in git history; commit before running if you want a restore point.
"""
import io
import json
import os
import re
import sys
import urllib.parse

from PIL import Image, ImageCms, ImageOps

sys.stdout.reconfigure(encoding="utf-8")
Image.MAX_IMAGE_PIXELS = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, "images")
DRY = "--dry" in sys.argv
LOG = None
if "--log" in sys.argv:
    LOG = sys.argv[sys.argv.index("--log") + 1]

MAX_W = 1600
MAX_W_SMALL = 900
MAX_W_COLLAGE = 1200
QUALITY = 82
SKIP_BELOW = 300 * 1024  # bytes; smaller files with sane dimensions are left as they are
TEXT_EXT = (".html", ".css", ".js", ".json", ".xml", ".txt", ".md")
SKIP_DIRS = {".git", "node_modules"}
SRGB = ImageCms.createProfile("sRGB")
# transparent PNGs that always sit on a known colour: flatten onto it and save as JPEG
FLATTEN = {"collage.png": (60, 110, 113)}  # the teal behind the home-page hero (#3c6e71)


def text_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for n in filenames:
            if n.lower().endswith(TEXT_EXT):
                yield os.path.join(dirpath, n)


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def small_display_names():
    """Image names that every <img> reference shows as a small (<=400px) cover or portrait."""
    seen = {}
    for path in text_files():
        if not path.endswith(".html"):
            continue
        for tag in re.findall(r"<img\b[^>]*>", read(path), re.S):
            m = re.search(r'src="[^"]*?/images/([^"/]+)"', tag)
            if not m:
                continue
            name = urllib.parse.unquote(m.group(1))
            mw = re.search(r"max-width:\s*(\d+)px", tag)
            small = bool(mw and int(mw.group(1)) <= 400)
            seen[name] = seen.get(name, True) and small
    return {n for n, v in seen.items() if v}


def to_srgb(img):
    icc = img.info.get("icc_profile")
    if not icc:
        return img
    try:
        src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        return ImageCms.profileToProfile(img, src, SRGB, outputMode="RGB")
    except Exception:
        return img


def has_transparency(img):
    if img.mode in ("RGBA", "LA"):
        return img.getchannel("A").getextrema()[0] < 255
    if img.mode == "P" and "transparency" in img.info:
        return img.convert("RGBA").getchannel("A").getextrema()[0] < 255
    return False


def plan_and_run(small_names):
    results = []
    renames = {}
    existing = {n.lower() for n in os.listdir(IMG_DIR)}
    for name in sorted(os.listdir(IMG_DIR)):
        stem, ext = os.path.splitext(name)
        low = ext.lower()
        if low not in (".jpg", ".jpeg", ".png"):
            continue
        path = os.path.join(IMG_DIR, name)
        old_size = os.path.getsize(path)
        try:
            img = Image.open(path)
            img.load()
        except Exception as e:
            results.append({"name": name, "action": "unreadable: %s" % e, "old": old_size, "new": old_size})
            continue

        limit = MAX_W_COLLAGE if name == "collage.png" else (MAX_W_SMALL if name in small_names else MAX_W)
        orientation_fix = low != ".png" and img.getexif().get(274, 1) != 1
        if old_size < SKIP_BELOW and img.width <= limit and not orientation_fix:
            results.append({"name": name, "action": "skip-small", "old": old_size, "new": old_size})
            continue

        img = ImageOps.exif_transpose(img)
        keep_png = low == ".png" and has_transparency(img)
        if keep_png and name in FLATTEN:
            flat = Image.new("RGB", img.size, FLATTEN[name])
            flat.paste(img.convert("RGBA"), mask=img.convert("RGBA").getchannel("A"))
            img, keep_png = flat, False
        if not keep_png:
            img = to_srgb(img)
            img = img.convert("RGB")
        elif img.mode not in ("RGBA", "LA"):
            img = img.convert("RGBA")
        resized = img.width > limit
        if resized:
            img = img.resize((limit, round(img.height * limit / img.width)), Image.LANCZOS)

        buf = io.BytesIO()
        if keep_png:
            img.save(buf, "PNG", optimize=True)
            new_name = name
        else:
            img.save(buf, "JPEG", quality=QUALITY, optimize=True, progressive=True)
            new_name = name
            if low == ".png":
                new_name = stem + ".jpg"
                if new_name.lower() in existing:
                    new_name = None
        data = buf.getvalue()

        if new_name is None:  # a same-named .jpg already exists: keep this one as a smaller PNG
            buf = io.BytesIO()
            img.save(buf, "PNG", optimize=True)
            data, new_name = buf.getvalue(), name
        if low != ".png" and len(data) >= old_size:
            results.append({"name": name, "action": "skip-no-gain", "old": old_size, "new": old_size})
            continue

        action = "recompress"
        if new_name != name:
            action = "png->jpg"
            renames[name] = new_name
            existing.add(new_name.lower())
        results.append({"name": name, "new_name": new_name, "action": action, "old": old_size, "new": len(data),
                        "size": "%dx%d" % img.size})
        if not DRY:
            with open(os.path.join(IMG_DIR, new_name), "wb") as f:
                f.write(data)
            if new_name != name:
                os.remove(path)
    return results, renames


def update_references(renames):
    if not renames:
        return 0
    forms = {}
    for old, new in renames.items():
        forms[old] = new
        forms[urllib.parse.quote(old)] = urllib.parse.quote(new)
    pattern = re.compile(r"(?<=/)(" + "|".join(re.escape(k) for k in sorted(forms, key=len, reverse=True)) + r")(?![\w.%-])")
    changed = 0
    for path in text_files():
        src = read(path)
        out = pattern.sub(lambda m: forms[m.group(1)], src)
        if out != src:
            changed += 1
            if not DRY:
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(out)
    return changed


def mb(n):
    return "%.1f MB" % (n / 1048576)


def main():
    small = small_display_names()
    results, renames = plan_and_run(small)
    refs = update_references(renames)
    old = sum(r["old"] for r in results)
    new = sum(r["new"] for r in results)
    acts = {}
    for r in results:
        acts[r["action"]] = acts.get(r["action"], 0) + 1
    print("%s: %d images, %s -> %s (saves %s)" % ("DRY RUN" if DRY else "DONE", len(results), mb(old), mb(new), mb(old - new)))
    print("actions:", acts)
    print("png->jpg renames: %d, files with updated references: %d" % (len(renames), refs))
    top = sorted(results, key=lambda r: r["old"] - r["new"], reverse=True)[:12]
    for r in top:
        print("  %-48s %7s -> %7s  %s" % (r["name"][:48], mb(r["old"]), mb(r["new"]), r.get("size", "")))
    if LOG:
        with open(LOG, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
