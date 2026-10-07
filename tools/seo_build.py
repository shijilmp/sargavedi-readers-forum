#!/usr/bin/env python3
"""Adds SEO metadata to every page and regenerates sitemap.xml.

Run from anywhere:  python tools/seo_build.py          (apply)
                    python tools/seo_build.py --dry    (report only)

Safe to re-run: generated tags sit between <!-- seo:start --> and <!-- seo:end -->
markers and are replaced each time. Tags you wrote by hand (a custom description,
or your own og:image) are left alone.
"""
import collections
import datetime
import html
import json
import os
import re
import subprocess
import sys
import urllib.parse

from PIL import Image, ImageFilter, ImageOps

sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.sargavedireadersforumalakode.in"
BRAND = "സർഗവേദി റീഡേഴ്സ് ഫോറം"
ORG_NAME = "ആലക്കോട് സർഗവേദി റീഡേഴ്സ് ഫോറം"
OG_IMAGE = BASE + "/images/og-default.jpg"
SHARE_DIR = os.path.join(ROOT, "images", "share")
DRY = "--dry" in sys.argv
TODAY = datetime.date.today().isoformat()

SKIP_DIRS = {".git", "tools", "node_modules"}
# search-engine ownership files (e.g. google0123abcd.html) must stay exactly as issued
VERIFY_FILE = re.compile(r"^google[0-9a-f]+\.html$")

TITLE_OVERRIDES = {
    "index.html": "ആലക്കോട് സർഗവേദി റീഡേഴ്സ് ഫോറം | Sargavedi Readers Forum, Alakode",
    "years.html": "പരിപാടികളുടെ ശേഖരം – വർഷം തിരിച്ച് | " + BRAND,
    "2026/index.html": "2026 പരിപാടികൾ | " + BRAND + ", ആലക്കോട്",
    "before2026/index.html": "2026-ന് മുമ്പുള്ള പരിപാടികൾ – പേജ് 1 | " + BRAND,
    "before2026/index_01.html": "2026-ന് മുമ്പുള്ള പരിപാടികൾ – പേജ് 2 | " + BRAND,
    "before2026/index_02.html": "2026-ന് മുമ്പുള്ള പരിപാടികൾ – പേജ് 3 | " + BRAND,
    "books/index_page01.html": "പുസ്തകങ്ങളും എഴുത്തുകാരും | " + BRAND,
    "books/Books/index_page01.html": "പുസ്തക നിരൂപണങ്ങൾ – പേജ് 1 | " + BRAND,
    "books/Books/index_page02.html": "പുസ്തക നിരൂപണങ്ങൾ – പേജ് 2 | " + BRAND,
    "drama/index.html": "നാടക നിരൂപണങ്ങൾ | " + BRAND,
    "films/index.html": "സിനിമ നിരൂപണങ്ങൾ | " + BRAND,
    "literature/index.html": "കഥകളും കവിതകളും | " + BRAND,
    "science/index.html": "ശാസ്ത്ര ലേഖനങ്ങൾ | " + BRAND,
    "travel/index.html": "യാത്രാനുഭവങ്ങൾ | " + BRAND,
}

DESC_OVERRIDES = {
    "index.html": (
        "2006 മുതൽ കണ്ണൂർ ജില്ലയിലെ ആലക്കോട് കേന്ദ്രീകരിച്ച് പ്രവർത്തിക്കുന്ന സാഹിത്യ-സാംസ്കാരിക കൂട്ടായ്മ: "
        "വീട്ടുമുറ്റ ചർച്ചകൾ, സാഹിത്യ പാഠശാല, പുസ്തക ചർച്ചകൾ, പുരസ്കാരങ്ങൾ. "
        "A literary and cultural forum in Alakode, Kannur, Kerala."
    ),
    "years.html": (
        "ആലക്കോട് സർഗവേദി റീഡേഴ്സ് ഫോറത്തിന്റെ 2006 മുതൽ 2026 വരെയുള്ള എല്ലാ പരിപാടികളും വർഷം തിരിച്ച്: "
        "വീട്ടുമുറ്റ ചർച്ചകൾ, പുസ്തക ചർച്ചകൾ, അനുസ്മരണങ്ങൾ, പുരസ്കാര സമർപ്പണങ്ങൾ."
    ),
    "about.html": (
        "ആലക്കോട് സർഗവേദി റീഡേഴ്സ് ഫോറത്തെക്കുറിച്ച്: 2006-ൽ രൂപീകൃതമായ കണ്ണൂർ ജില്ലയിലെ സാഹിത്യ-സാംസ്കാരിക "
        "കൂട്ടായ്മയുടെ ചരിത്രം, പ്രവർത്തനങ്ങൾ, ഭാരവാഹികൾ. About Alakode Sargavedi Readers Forum, Kannur, Kerala."
    ),
    "history.html": (
        "സർഗവേദി റീഡേഴ്സ് ഫോറത്തിന്റെ 2006 മുതൽ 2026 വരെയുള്ള ചരിത്രം: ഉദ്ഘാടനം, റീഡേഴ്സ് ഫോറം, "
        "സാഹിത്യ പാഠശാല, വീട്ടുമുറ്റ ചർച്ചകൾ, പുരസ്കാരങ്ങൾ."
    ),
    "veettumuttam.html": (
        "2017 മുതൽ ആലക്കോട്ടെ വീടുകളുടെ മുറ്റങ്ങളിൽ നടക്കുന്ന സർഗവേദിയുടെ സാഹിത്യ ചർച്ചകൾ: ആശയം, പങ്കാളിത്തം, "
        "ഇതുവരെ പങ്കെടുത്ത എഴുത്തുകാരുടെ പട്ടിക."
    ),
    "awards.html": (
        "പി.ടി. തങ്കപ്പൻ മാസ്റ്റർ സാഹിത്യ പുരസ്കാരം, വായനാ പുരസ്കാരം, നവരത്ന സാഹിത്യ പുരസ്കാരം: "
        "സർഗവേദി നൽകിയ പുരസ്കാരങ്ങളും ജേതാക്കളും."
    ),
    "people.html": (
        "സർഗവേദി റീഡേഴ്സ് ഫോറത്തിന്റെ വേദികളിൽ അതിഥികളായെത്തിയ എഴുത്തുകാരുടെയും പ്രഭാഷകരുടെയും "
        "പുസ്തക നിരൂപകരുടെയും പട്ടിക, പരിപാടികളുടെ പേജുകളിലേക്കുള്ള ലിങ്കുകളോടെ."
    ),
    "media.html": (
        "സർഗവേദി റീഡേഴ്സ് ഫോറത്തെക്കുറിച്ച് ദേശാഭിമാനി, ആകാശവാണി, ടെലിവിഷൻ ചാനലുകൾ തുടങ്ങിയ മാധ്യമങ്ങളിൽ "
        "വന്ന ലേഖനങ്ങളും വാർത്തകളും."
    ),
}

GENERIC_TITLES = {"Science Article", "Travel Article", "Article"}

INDEX_STYLE = re.compile(r"(^|/)index(_\d+|_page\d+)?\.html$|^years\.html$")
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]")
SKIP_LINE = re.compile(r"^(author|review by|written by|type)\b|^എഴുതിയത്", re.I)


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def clean_text(fragment):
    fragment = re.sub(r"<(script|style)\b.*?</\1>", " ", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<br\s*/?>", " ", fragment, flags=re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    fragment = EMOJI.sub("", html.unescape(fragment))
    return re.sub(r"\s+", " ", fragment).strip()


def truncate(text, limit=155):
    if len(text) <= limit:
        return text
    cut = text[:limit]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip(" ,.;:-–") + "…"


def page_url(rel):
    if rel == "index.html":
        return BASE + "/"
    if rel.endswith("/index.html"):
        return BASE + "/" + urllib.parse.quote(rel[: -len("index.html")], safe="/")
    return BASE + "/" + urllib.parse.quote(rel, safe="/")


def list_pages():
    pages = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(".html") and not VERIFY_FILE.match(name):
                full = os.path.join(dirpath, name)
                pages.append(os.path.relpath(full, ROOT).replace(os.sep, "/"))
    return sorted(pages)


def get_title(src):
    m = re.search(r"<title>(.*?)</title>", src, re.S)
    return html.unescape(m.group(1).strip()) if m else ""


MONTHS = {
    "january": "ജനുവരി", "february": "ഫെബ്രുവരി", "march": "മാർച്ച്", "april": "ഏപ്രിൽ",
    "may": "മേയ്", "june": "ജൂൺ", "july": "ജൂലൈ", "august": "ഓഗസ്റ്റ്",
    "september": "സെപ്റ്റംബർ", "october": "ഒക്ടോബർ", "november": "നവംബർ", "december": "ഡിസംബർ",
}


def folder_of(rel):
    parts = rel.split("/")
    return parts[-2] if len(parts) > 1 else ""


def year_of(rel):
    m = re.search(r"(?<!\d)(20\d\d)(?!\d)", folder_of(rel))
    if m:
        return m.group(1)
    return "2026" if rel.startswith("2026/") else ""


def when_of(rel):
    """'ജൂലൈ 2026' / '2019' / '' - used only to tell same-titled pages apart."""
    y = year_of(rel)
    for en, ml in MONTHS.items():
        if re.search(en, folder_of(rel), re.I):
            return (ml + " " + y).strip()
    return y


def page_no(rel):
    m = re.search(r"page(\d+)\.html$", rel)
    return int(m.group(1)) if m else 0


def plan_titles(pages, sources):
    titles = {}
    for rel in pages:
        t = TITLE_OVERRIDES.get(rel) or get_title(sources[rel]) or "Sargavedi Readers Forum"
        if t in GENERIC_TITLES:
            h1m = re.search(r"<h1[^>]*>(.*?)</h1>", sources[rel], re.S)
            if h1m and clean_text(h1m.group(1)):
                t = clean_text(h1m.group(1))
        if "sargavedi" not in t.lower() and "സർഗവേദി" not in t:
            t = t + " | " + BRAND
        titles[rel] = t

    groups = collections.defaultdict(list)
    for rel, t in titles.items():
        groups[t].append(rel)
    for t, rels in groups.items():
        if len(rels) < 2:
            continue
        for rel in rels:
            base, sep, brand = t.partition(" | ")
            parts = []
            y = when_of(rel)
            if y and y not in base:
                parts.append(y)
            n = page_no(rel)
            if n >= 2:
                parts.append("ഭാഗം %d" % n)
            if parts:
                base = base + " (" + ", ".join(parts) + ")"
            titles[rel] = base + (sep + brand if sep else "")

    seen = collections.Counter(titles.values())
    counters = collections.Counter()
    for rel in pages:
        t = titles[rel]
        if seen[t] > 1:
            counters[t] += 1
            if counters[t] > 1:
                base, sep, brand = t.partition(" | ")
                titles[rel] = "%s (%d)%s%s" % (base, counters[t], sep, brand)
    return titles


def make_description(rel, src):
    if rel in DESC_OVERRIDES:
        return DESC_OVERRIDES[rel]
    h1m = re.search(r"<h1[^>]*>(.*?)</h1>", src, re.S)
    h1 = clean_text(h1m.group(1)) if h1m else ""

    m = re.search(r'<div class="page"[^>]*>(.*?)(?:<div class="navigation"|<footer)', src, re.S)
    if m:
        for p in re.findall(r"<p[^>]*>(.*?)</p>", m.group(1), re.S):
            text = clean_text(p)
            if text.startswith("(") and text.endswith(")"):
                continue
            if len(text) >= 50 and not SKIP_LINE.match(text) and not text.startswith("അടുത്ത പേജിൽ"):
                return truncate(text)

    cards = re.findall(r'<a [^>]*class="month-card"[^>]*>(.*?)</a>', src, re.S)
    if len(cards) >= 3:
        names = []
        for c in cards[:6]:
            b = re.search(r"<b>(.*?)</b>", c, re.S)
            names.append(truncate(clean_text(b.group(1) if b else c), 45))
        return truncate(h1 + ": " + ", ".join(n for n in names if n))

    hero = re.search(r'<header class="hero">(.*?)</header>', src, re.S)
    parts = [h1]
    if hero:
        for frag in re.findall(r"<(?:h2|p)[^>]*>(.*?)</(?:h2|p)>", hero.group(1), re.S):
            text = clean_text(frag)
            if text and text not in parts:
                parts.append(text)
    desc = " – ".join(p for p in parts if p) or get_title(src)
    if "സർഗവേദി" not in desc:
        desc += " | " + BRAND
    return truncate(desc)


def first_image(rel, src):
    m = re.search(r'<img[^>]+src="([^"]+)"', src)
    if not m:
        return None
    path = os.path.normpath(os.path.join(os.path.dirname(rel), m.group(1))).replace(os.sep, "/")
    if path.startswith(".."):
        path = path.lstrip("./")
    if not re.search(r"\.(jpe?g|png|webp)$", path, re.I):
        return None
    return BASE + "/" + urllib.parse.quote(path, safe="/")


def local_page_image(rel, src):
    """File path (inside the project) of the first picture on a page, or None."""
    m = re.search(r'<img[^>]+src="([^"]+)"', src)
    if not m or m.group(1).startswith(("http", "data:")):
        return None
    path = os.path.normpath(os.path.join(os.path.dirname(rel), urllib.parse.unquote(m.group(1))))
    if path.startswith(".."):
        path = path.lstrip("./\\")
    full = os.path.join(ROOT, path)
    if not re.search(r"\.(jpe?g|png|webp)$", full, re.I) or not os.path.exists(full):
        return None
    return full


def make_share_image(source, dest):
    """1200x630 JPEG for link previews (WhatsApp, Facebook, X ...): the page picture on a
    blurred copy of itself, with the forum badge in the corner."""
    W, H = 1200, 630
    img = ImageOps.exif_transpose(Image.open(source)).convert("RGB")
    ratio = img.width / img.height
    if 1.5 <= ratio <= 2.4:  # already landscape: fill the frame
        canvas = ImageOps.fit(img, (W, H), Image.LANCZOS, centering=(0.5, 0.35))
    else:  # portrait posters, covers, near-square pictures: keep them whole
        back = ImageOps.fit(img, (W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(28))
        back = Image.eval(back, lambda v: int(v * 0.55))
        fg = ImageOps.contain(img, (W, H), Image.LANCZOS)
        canvas = back
        canvas.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
    badge_path = os.path.join(ROOT, "icon-192.png")
    if os.path.exists(badge_path):
        badge = Image.open(badge_path).convert("RGBA").resize((88, 88), Image.LANCZOS)
        canvas = canvas.convert("RGBA")
        canvas.alpha_composite(badge, (W - 88 - 22, H - 88 - 22))
        canvas = canvas.convert("RGB")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for quality in (82, 74, 66, 58):
        canvas.save(dest, "JPEG", quality=quality, optimize=True, progressive=True)
        if os.path.getsize(dest) <= 220 * 1024:
            break


def share_image(rel, src):
    """URL of the picture shown when this page is shared; the site-wide collage for the home page,
    list pages and pages without a usable picture."""
    if rel == "index.html" or INDEX_STYLE.search(rel):
        return OG_IMAGE
    source = local_page_image(rel, src)
    if not source:
        return OG_IMAGE
    name = re.sub(r"[^A-Za-z0-9]+", "-", rel.rsplit(".", 1)[0]).strip("-") + ".jpg"
    dest = os.path.join(SHARE_DIR, name)
    if not DRY and (not os.path.exists(dest) or os.path.getmtime(dest) < os.path.getmtime(source)):
        make_share_image(source, dest)
    return BASE + "/images/share/" + name


def event_data():
    """Event details for 2026 pages, read from the cards on 2026/index.html."""
    path = os.path.join(ROOT, "2026", "index.html")
    if not os.path.exists(path):
        return {}
    events = {}
    for href, body in re.findall(r'<a href="([^"]+\.html)"[^>]*class="month-card">(.*?)</a>', read(path), re.S):
        title = re.search(r"<b>(.*?)</b>", body, re.S)
        date = re.search(r"(\d{2})/(\d{2})/(\d{4})", body)
        place = re.search(r"സ്ഥലം:\s*(.*?)\s*</b>", body, re.S)
        if not (title and date and place):
            continue
        events["2026/" + href] = {
            "name": clean_text(title.group(1)),
            "date": "%s-%s-%s" % (date.group(3), date.group(2), date.group(1)),
            "place": clean_text(place.group(1)),
        }
    names = collections.Counter(e["name"] for e in events.values())
    for e in events.values():
        if names[e["name"]] > 1:
            d = e["date"].split("-")
            e["name"] += " (%s/%s/%s)" % (d[2], d[1], d[0])
    return events


def ld_block(data):
    body = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    return '<script type="application/ld+json">\n' + body + "\n</script>"


def org_node():
    return {
        "@type": "Organization",
        "@id": BASE + "/#organization",
        "name": ORG_NAME,
        "alternateName": ["Sargavedi Readers Forum", "Alakode Sargavedi Readers Forum"],
        "url": BASE + "/",
        "logo": BASE + "/icon-512.png",
        "foundingDate": "2006",
        "description": "2006 മുതൽ കണ്ണൂർ ജില്ലയിലെ ആലക്കോട് കേന്ദ്രീകരിച്ച് പ്രവർത്തിക്കുന്ന സാഹിത്യ-സാംസ്കാരിക കൂട്ടായ്മ. "
        "A literary and cultural community in Alakode, Kannur, Kerala, India.",
        "address": {
            "@type": "PostalAddress",
            "addressLocality": "Alakode",
            "addressRegion": "Kerala",
            "addressCountry": "IN",
        },
        "founder": {"@type": "Person", "name": "പി.ടി. തങ്കപ്പൻ മാസ്റ്റർ"},
        "email": "sargavedireadersforumalakode@gmail.com",
        "telephone": "+91-9495358978",
        "contactPoint": {
            "@type": "ContactPoint",
            "name": "എ.ആർ. പ്രസാദ്",
            "telephone": "+91-9495358978",
            "email": "sargavedireadersforumalakode@gmail.com",
            "contactType": "general enquiries",
            "areaServed": "IN",
            "availableLanguage": ["ml", "en"],
        },
        "sameAs": [
            "https://www.facebook.com/share/g/1DUciCBZVe/",
            "https://www.youtube.com/@SargavediReadersForumAlakode",
        ],
    }


def build_head_block(rel, title, desc, src, events, nl):
    url = page_url(rel)
    esc = lambda s: html.escape(s, quote=True)
    lines = ["<!-- seo:start -->"]
    if not re.search(r'<meta\s+name="description"', strip_blocks(src)):
        lines.append('<meta name="description" content="%s">' % esc(desc))
    lines.append('<link rel="canonical" href="%s">' % url)
    lines.append('<meta name="theme-color" content="#3c6e71">')
    lines.append('<link rel="icon" href="/favicon.ico" sizes="48x48">')
    lines.append('<link rel="icon" type="image/png" sizes="192x192" href="/icon-192.png">')
    lines.append('<link rel="apple-touch-icon" href="/apple-touch-icon.png">')
    if 'property="og:image"' not in strip_blocks(src):
        og_image = share_image(rel, src)
        og_type = "website" if INDEX_STYLE.search(rel) else "article"
        lines += [
            '<meta property="og:site_name" content="%s">' % esc(BRAND),
            '<meta property="og:locale" content="ml_IN">',
            '<meta property="og:type" content="%s">' % og_type,
            '<meta property="og:title" content="%s">' % esc(title),
            '<meta property="og:description" content="%s">' % esc(desc),
            '<meta property="og:url" content="%s">' % url,
            '<meta property="og:image" content="%s">' % og_image,
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            '<meta property="og:image:type" content="image/jpeg">',
            '<meta name="twitter:card" content="summary_large_image">',
            '<meta name="twitter:title" content="%s">' % esc(title),
            '<meta name="twitter:description" content="%s">' % esc(desc),
            '<meta name="twitter:image" content="%s">' % og_image,
        ]
    lines.append("<!-- seo:end -->")

    ld = []
    if rel == "index.html":
        ld.append(ld_block({
            "@context": "https://schema.org",
            "@graph": [
                org_node(),
                {
                    "@type": "WebSite",
                    "@id": BASE + "/#website",
                    "url": BASE + "/",
                    "name": "സർഗവേദി റീഡേഴ്സ് ഫോറം – ഡിജിറ്റൽ ശേഖരം",
                    "alternateName": "Sargavedi Readers Forum",
                    "inLanguage": "ml",
                    "publisher": {"@id": BASE + "/#organization"},
                },
            ],
        }))
    if rel == "about.html":
        about = org_node()
        about.pop("@id")
        ld.append(ld_block({
            "@context": "https://schema.org",
            "@type": "AboutPage",
            "url": url,
            "name": title,
            "inLanguage": "ml",
            "mainEntity": about,
        }))
    if rel in events:
        ev = events[rel]
        place = {"@type": "Place", "name": ev["place"]}
        if "ആലക്കോട്" in ev["place"]:
            place["address"] = {
                "@type": "PostalAddress",
                "addressLocality": "Alakode",
                "addressRegion": "Kerala",
                "addressCountry": "IN",
            }
        node = {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": ev["name"],
            "startDate": ev["date"],
            "eventStatus": "https://schema.org/EventScheduled",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "location": place,
            "organizer": {"@type": "Organization", "name": ORG_NAME, "url": BASE + "/"},
            "description": desc,
            "inLanguage": "ml",
            "url": url,
        }
        img = first_image(rel, src)
        if img:
            node["image"] = [img]
        ld.append(ld_block(node))
    if ld:
        lines.append("<!-- seo-ld:start -->")
        lines += ld
        lines.append("<!-- seo-ld:end -->")
    return nl.join(lines)


def strip_blocks(src):
    src = re.sub(r"<!-- seo:start -->.*?<!-- seo:end -->\s*", "", src, flags=re.S)
    return re.sub(r"<!-- seo-ld:start -->.*?<!-- seo-ld:end -->\s*", "", src, flags=re.S)


def process(rel, src, titles, events):
    nl = "\r\n" if "\r\n" in src else "\n"
    out = strip_blocks(src)
    title = titles[rel]
    desc = make_description(rel, out)

    if re.search(r"<title>.*?</title>", out, re.S):
        out = re.sub(r"<title>.*?</title>", lambda m: "<title>%s</title>" % html.escape(title, quote=False), out, count=1, flags=re.S)
        anchor = "</title>"
    else:
        anchor = "</head>"
    block = build_head_block(rel, title, desc, out, events, nl)
    if anchor == "</title>":
        out = out.replace("</title>", "</title>" + nl + nl + block, 1)
    else:
        out = out.replace("</head>", block + nl + "</head>", 1)

    out = re.sub(r"<html(?![^>]*\blang=)([^>]*)>", r'<html lang="ml"\1>', out, count=1)
    out = re.sub(r"<img\b(?![^>]*\bloading=)", '<img loading="lazy"', out)
    return out


def git_dates(paths):
    dirty = set()
    try:
        status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout
        for line in status.splitlines():
            dirty.add(line[3:].strip().strip('"').replace("\\", "/"))
    except OSError:
        pass
    dates = {}
    for p in paths:
        if p in dirty or any(d.endswith("/") and p.startswith(d) for d in dirty):
            dates[p] = TODAY
            continue
        try:
            d = subprocess.run(["git", "log", "-1", "--format=%cs", "--", p], cwd=ROOT, capture_output=True, text=True, encoding="utf-8").stdout.strip()
        except OSError:
            d = ""
        dates[p] = d or TODAY
    return dates


def build_sitemap(pages):
    pdfs = []
    pdf_dir = os.path.join(ROOT, "pdf")
    if os.path.isdir(pdf_dir):
        pdfs = ["pdf/" + n for n in sorted(os.listdir(pdf_dir)) if n.lower().endswith(".pdf")]
    dates = git_dates(pages + pdfs)
    rows = []
    home = [p for p in pages if p == "index.html"]
    rest = [p for p in pages if p != "index.html"]
    for rel in home + rest + pdfs:
        loc = page_url(rel) if rel.endswith(".html") else BASE + "/" + urllib.parse.quote(rel, safe="/")
        rows.append("  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n  </url>" % (html.escape(loc), dates[rel]))
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % "\n".join(rows)
    return xml, len(rows)


ROBOTS = """# Sargavedi Readers Forum, Alakode - crawlers are welcome, including AI search and answer engines.
User-agent: *
Allow: /
Disallow: /tools/

User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Applebot-Extended
Allow: /

Sitemap: %s/sitemap.xml
""" % BASE


def main():
    pages = list_pages()
    sources = {rel: read(os.path.join(ROOT, rel)) for rel in pages}
    titles = plan_titles(pages, {rel: strip_blocks(s) for rel, s in sources.items()})
    events = event_data()

    changed = 0
    for rel in pages:
        new = process(rel, sources[rel], titles, events)
        if new != sources[rel]:
            changed += 1
            if not DRY:
                write(os.path.join(ROOT, rel), new)

    sitemap, n = build_sitemap(pages)
    if not DRY:
        write(os.path.join(ROOT, "sitemap.xml"), sitemap)
        robots = os.path.join(ROOT, "robots.txt")
        if not os.path.exists(robots):
            write(robots, ROBOTS)
    print("pages: %d, changed: %d, sitemap urls: %d, event pages: %d%s" % (len(pages), changed, n, len(events), " (dry run)" if DRY else ""))


if __name__ == "__main__":
    main()
