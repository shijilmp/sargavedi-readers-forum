#!/usr/bin/env python3
"""Adds alt text to <img> tags that have none (or only a copy-pasted placeholder).

    python tools/alt_text.py --dry     (report only)
    python tools/alt_text.py           (apply)

Only facts the page itself states are used, so nothing can be wrongly described:
  * book-review covers      ->  "<book> – <author> (പുസ്തകത്തിന്റെ കവർ)"
  * newspaper clippings     ->  "<page title> – പത്രവാർത്ത N"   (images under "പത്ര മാധ്യമങ്ങളിലൂടെ")
  * other event photos      ->  "<page title> (<date>) – ചിത്രം N"
Alt text you wrote yourself is never changed. To describe a specific photo, write its alt by hand;
the script will leave it alone on later runs.
"""
import html
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY = "--dry" in sys.argv
SKIP_DIRS = {".git", "tools", "node_modules"}
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]")
PLACEHOLDER = re.compile(r"Book Cover$", re.I)
NEWS = "പത്ര മാധ്യമങ്ങളിലൂടെ"
MORE = "ചിത്രങ്ങളിലൂടെ"
VIDEO = "ദൃശ്യ മാധ്യമങ്ങളിലൂടെ"


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = EMOJI.sub("", html.unescape(s))
    return re.sub(r"\s+", " ", s).strip(" -–|")


def trunc(s, n=140):
    if len(s) <= n:
        return s
    cut = s[:n]
    return (cut[: cut.rfind(" ")] if " " in cut else cut).rstrip(" ,.;:-–") + "…"


def page_info(src):
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", src, re.S)
    title = clean(h1.group(1)) if h1 else ""
    if not title:
        t = re.search(r"<title>(.*?)</title>", src, re.S)
        title = clean(t.group(1)).split(" | ")[0] if t else ""
    hero = re.search(r'<header class="hero">(.*?)</header>', src, re.S)
    hero_text = hero.group(1) if hero else ""
    date = re.search(r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b", hero_text)
    author = ""
    h2 = re.search(r"<h2[^>]*>(.*?)</h2>", hero_text, re.S)
    if h2:
        author = clean(h2.group(1))
    return title, (date.group(1).replace("-", "/") if date else ""), author


def process(rel, src):
    title, date, author = page_info(src)
    is_book = rel.startswith("books/Books/") and rel.endswith(".html") and "index_page" not in rel
    n_photo = 0
    n_news = 0
    out = []
    pos = 0
    changed = 0
    for m in re.finditer(r"<img\b[^>]*>", src, re.S):
        tag = m.group(0)
        alt = re.search(r'\balt="([^"]*)"', tag)
        before = src[: m.start()]
        # which labelled section are we in?
        marks = {k: before.rfind(k) for k in (NEWS, MORE, VIDEO)}
        section = max(marks, key=marks.get) if max(marks.values()) >= 0 else None
        is_cover = is_book and "max-width:300px" in tag
        placeholder = bool(alt and PLACEHOLDER.search(alt.group(1)))
        if alt and not placeholder:
            continue
        if is_cover:
            text = "%s – %s (പുസ്തകത്തിന്റെ കവർ)" % (title, author) if author else "%s (പുസ്തകത്തിന്റെ കവർ)" % title
        elif section == NEWS:
            n_news += 1
            text = "%s – പത്രവാർത്ത %d" % (title, n_news)
        else:
            n_photo += 1
            text = "%s%s – ചിത്രം %d" % (title, " (%s)" % date if date else "", n_photo)
        text = trunc(text).replace('"', "&quot;")
        if alt:
            new = tag.replace(alt.group(0), 'alt="%s"' % text, 1)
        else:
            new = re.sub(r"<img\b", '<img alt="%s"' % text, tag, count=1)
        out.append(src[pos : m.start()])
        out.append(new)
        pos = m.end()
        changed += 1
    out.append(src[pos:])
    return "".join(out), changed


def main():
    total = pages = 0
    samples = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if not name.endswith(".html"):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
            src = read(path)
            new, n = process(rel, src)
            if n:
                total += n
                pages += 1
                if len(samples) < 14:
                    m = re.search(r'<img alt="([^"]*)"', new) or re.search(r'alt="([^"]*)"', new)
                    samples.append((rel, m.group(1) if m else ""))
                if not DRY:
                    with open(path, "w", encoding="utf-8", newline="") as f:
                        f.write(new)
    print("%s: %d images on %d pages" % ("DRY RUN" if DRY else "DONE", total, pages))
    for rel, alt in samples:
        print("  %-52s %s" % (rel[:52], alt))


if __name__ == "__main__":
    main()
