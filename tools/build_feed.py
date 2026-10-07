#!/usr/bin/env python3
"""Builds the desktop front page and the sidebar feed from the site's own pages.

    python tools/build_feed.py

It reads the event index pages, book reviews, writer pages and the veettumuttam table, makes
small thumbnails in images/thumbs/, writes feed.json (used by the sidebar on article pages)
and refreshes the front-page block in index.html (shown on desktop only).
Run it after adding events, book reviews or writers, then run tools/seo_build.py.
"""
import collections
import html
import json
import os
import re
import sys
import urllib.parse

from PIL import Image, ImageOps

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
THUMBS = os.path.join("images", "thumbs")
os.makedirs(THUMBS, exist_ok=True)
EVENT_INDEXES = ["2026/index.html", "before2026/index.html", "before2026/index_01.html", "before2026/index_02.html"]
LIST_PAGES = [("സിനിമ", "films/index.html"), ("നാടകം", "drama/index.html"), ("ശാസ്ത്രം", "science/index.html"),
              ("കഥകളും കവിതകളും", "literature/index.html"), ("യാത്ര", "travel/index.html")]
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]")


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def txt(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = EMOJI.sub("", html.unescape(s))
    return re.sub(r"\s+", " ", s).strip()


def esc(s):
    return html.escape(s, quote=True)


def resolve(page, src):
    """Site-relative path of an image referenced from a page (browsers clamp ../ at the root)."""
    parts = [x for x in os.path.dirname(page).replace("\\", "/").split("/") if x]
    for part in urllib.parse.unquote(src).split("/"):
        if part == "..":
            if parts:
                parts.pop()
        elif part not in (".", ""):
            parts.append(part)
    return "/".join(parts)


def first_image(page, only_cover=False):
    if not os.path.exists(page):
        return None
    for tag in re.findall(r"<img\b[^>]*>", read(page), re.S):
        if only_cover and "max-width:300px" not in tag:
            continue
        m = re.search(r'src="([^"]+)"', tag)
        if m and not m.group(1).startswith("http"):
            path = resolve(page, m.group(1))
            if os.path.exists(path):
                return path
    return None


def thumb(src, name, width=640):
    if not src:
        return None
    dest = os.path.join(THUMBS, name + ".jpg")
    if not os.path.exists(dest) or os.path.getmtime(dest) < os.path.getmtime(src):
        img = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        if img.width > width:
            img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
        img.save(dest, "JPEG", quality=78, optimize=True, progressive=True)
    return dest.replace("\\", "/")


def pdf_thumb(href, name, width=640):
    """Thumbnail for an event that links straight to a PDF: the lead photo of the
    newspaper page (the largest embedded image, minus the side strip and the
    blank area under the picture)."""
    if not os.path.exists(href):
        return None
    dest = os.path.join(THUMBS, name + ".jpg")
    if not os.path.exists(dest) or os.path.getmtime(dest) < os.path.getmtime(href):
        try:
            import pypdf
        except ImportError:
            return None
        best = None
        for im in pypdf.PdfReader(href).pages[0].images:
            if im.image.mode == "L":  # soft masks
                continue
            if best is None or im.image.width * im.image.height > best.width * best.height:
                best = im.image
        if best is None:
            return None
        if best.mode == "RGBA":
            flat = Image.new("RGB", best.size, (255, 255, 255))
            flat.paste(best, mask=best.split()[3])
            best = flat
        w, h = best.size
        img = best.convert("RGB").crop((int(w * 0.153), 0, w, int(h * 0.585)))
        img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS)
        img.save(dest, "JPEG", quality=78, optimize=True, progressive=True)
    return dest.replace("\\", "/")


def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")


def iso(d):
    m = re.match(r"(\d{2})[/-](\d{2})[/-](\d{4})", d or "")
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else ""


def category(title):
    t = title.replace("‌", "")
    if "വീട്ടുമുറ്റ" in t:
        return "വീട്ടുമുറ്റ ചർച്ച"
    if "പുരസ്കാര" in t:
        return "പുരസ്കാരം"
    if "അനുസ്മരണ" in t:
        return "അനുസ്മരണം"
    if "പ്രകാശന" in t and "പുസ്തക ചർച്ച" not in t:
        return "പുസ്തക പ്രകാശനം"
    if "പുസ്തക" in t:
        return "പുസ്തക ചർച്ച"
    if "ജാലകം" in t or "ആകാശവാണി" in t:
        return "പ്രക്ഷേപണം"
    if "സർഗ സായാഹ്നം" in t:
        return "സർഗ സായാഹ്നം"
    if "വായന" in t:
        return "വായന"
    return "പരിപാടി"


def events():
    out = []
    for idx in EVENT_INDEXES:
        base = idx.rsplit("/", 1)[0]
        for href, body in re.findall(r'<a href="([^"]+)"[^>]*class="month-card">(.*?)</a>', read(idx), re.S):
            href = href.replace("\\", "/")
            if not href.endswith(".html") and not href.endswith(".pdf"):
                continue
            target = resolve(base + "/x", href)
            smalls = [txt(x) for x in re.findall(r"<small>(.*?)</small>", body, re.S)]
            title = txt(re.search(r"<b>(.*?)</b>", body, re.S).group(1))
            dates = re.findall(r"\d{2}[/-]\d{2}[/-]\d{4}", " ".join(smalls))
            date = iso(dates[-1]) if dates else ""
            label = dates[-1].replace("-", "/") if dates else ""
            ymatch = re.search(r"Year\s*(\d{4})", " ".join(smalls))
            if not date and ymatch:
                date, label = ymatch.group(1) + "-01-01", ymatch.group(1)
            if len(dates) >= 2 and "മുതൽ" in " ".join(smalls):
                date = iso(dates[0])
                label = dates[0].replace("-", "/") + " – " + dates[1].replace("-", "/")
            venue = next((re.sub(r"^സ്ഥലം:\s*", "", s) for s in smalls if s.startswith("സ്ഥലം:")), "")
            sub = next((s for s in smalls if not s.startswith("സ്ഥലം:") and not re.fullmatch(r"[\d/\-, ]+", s)), "")
            cat = category(title)
            if sub and title in ("പുസ്തക ചർച്ച", "സർഗ സായാഹ്നം"):
                title = sub if sub.startswith(title) else title + " – " + sub
            ev = dict(title=title, sub=sub, date=date, label=label, venue=venue, href=target, cat=cat,
                      slug=slug(target.rsplit(".", 1)[0]))
            if target.endswith(".pdf"):
                ev["cat"] = "ദേശാഭിമാനി" if "Deshabhimani" in target else "മാധ്യമം"
            out.append(ev)
    out.sort(key=lambda e: e["date"], reverse=True)
    return out


def books():
    out = []
    for p in sorted([x for x in os.listdir("books/Books") if re.fullmatch(r"book\d+\.html", x)],
                    key=lambda x: -int(re.search(r"\d+", x).group(0))):
        path = "books/Books/" + p
        s = read(path)
        title = re.sub(r"\s*\(.*?\)\s*$", "", txt(re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S).group(1)))
        h2 = re.search(r"<header class=\"hero\">.*?<h2[^>]*>(.*?)</h2>", s, re.S)
        tag = re.search(r'class="tagline">(.*?)</p>', s, re.S)
        by = re.sub(r"^Review by:?\s*", "", txt(tag.group(1))) if tag else ""
        out.append(dict(title=title, author=txt(h2.group(1)) if h2 else "", by=by, href=path,
                        slug=slug(path.rsplit(".", 1)[0]), img=first_image(path, only_cover=True)))
    return out


COVER_PAGES = [("films/index.html", " – പോസ്റ്റർ"), ("drama/index.html", " – പോസ്റ്റർ"),
               ("science/index.html", ""), ("travel/index.html", ""),
               ("books/Writters/world-writers.html", " – ചിത്രം")]


def card_items(idx):
    """Cards of a list page with a thumbnail made from the picture on each linked page
    (the cover/poster image if the page marks one, otherwise its first image)."""
    base = idx.rsplit("/", 1)[0]
    out = []
    for href, body in re.findall(r'<a href="([^"]+\.html)"[^>]*class="month-card">(.*?)</a>', read(idx), re.S):
        path = resolve(base + "/x", href.replace("\\", "/"))
        b = re.search(r"<strong>(.*?)</strong>", body, re.S) or re.search(r"<b>(.*?)</b>", body, re.S)
        src = first_image(path, only_cover=True) or first_image(path)
        out.append(dict(title=txt(b.group(1) if b else body), href=path,
                        thumb=thumb(src, slug(path.rsplit(".", 1)[0]), 400)))
    return out


def writers():
    s = read("books/Writters/world-writers.html")
    out = []
    for href, body in re.findall(r'<a href="(writer-[^"]+)"[^>]*class="month-card">(.*?)</a>', s, re.S):
        path = "books/Writters/" + href
        name = txt(re.search(r"<b>(.*?)</b>", body, re.S).group(1))
        name = re.sub(r"\s*\(.*?\)\s*$", "", name)
        smalls = [txt(x) for x in re.findall(r"<small>(.*?)</small>", body, re.S)]
        out.append(dict(title=name, sub=smalls[0] if smalls else "", href=path, slug=slug(path.rsplit(".", 1)[0]),
                        img=first_image(path)))
    return out


def lists():
    out = []
    for label, page in LIST_PAGES:
        base = page.rsplit("/", 1)[0]
        items = []
        for href, body in re.findall(r'<a href="([^"]+\.html)"[^>]*class="month-card">(.*?)</a>', read(page), re.S):
            b = re.search(r"<strong>(.*?)</strong>", body, re.S) or re.search(r"<b>(.*?)</b>", body, re.S)
            title = txt(b.group(1) if b else body)
            if title:
                items.append(dict(title=title, href=resolve(base + "/x", href)))
        out.append(dict(label=label, href=page, items=items))
    return out


def fmt_date(iso_date):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso_date or "")
    return "%s/%s/%s" % (m.group(3), m.group(2), m.group(1)) if m else ""


def img_tag(path, alt=""):
    return '<img src="%s" alt="%s" loading="lazy">' % (esc(path), esc(alt)) if path else ""


def card(item, kind):
    th = item.get("thumb")
    if kind == "event":
        meta = fmt_date(item["date"]) + (" · " + item["venue"] if item.get("venue") else "")
        return ('<a class="fcard" href="%s"><span class="fthumb">%s</span><span class="fcat">%s</span>'
                '<span class="ftitle">%s</span><span class="fmeta">%s</span></a>'
                % (esc(item["href"]), img_tag(th, item["title"]), esc(item["cat"]), esc(item["title"]), esc(meta)))
    if kind == "book":
        return ('<a class="fcard fbook" href="%s"><span class="fthumb">%s</span><span class="ftitle">%s</span>'
                '<span class="fmeta">%s</span></a>'
                % (esc(item["href"]), img_tag(th, item["title"] + " – പുസ്തകത്തിന്റെ കവർ"), esc(item["title"]), esc(item["author"])))
    return ('<a class="fcard fbook" href="%s"><span class="fthumb">%s</span><span class="ftitle">%s</span>'
            '<span class="fmeta">%s</span></a>'
            % (esc(item["href"]), img_tag(th, item["title"]), esc(item["title"]), esc(item.get("sub", ""))))


def front_html(evs, bks, wrs, veet, lsts):
    lead = evs[0]
    rest = evs[1:5]
    more = evs[5:11]
    lead_html = ('<a class="lead" href="%s"><span class="lead-img">%s</span><span class="fcat">%s</span>'
                 '<span class="lead-title">%s</span><span class="fmeta">%s</span></a>'
                 % (esc(lead["href"]), img_tag(lead.get("thumb"), lead["title"]), esc(lead["cat"]), esc(lead["title"]),
                    esc(fmt_date(lead["date"]) + (" · " + lead["venue"] if lead["venue"] else ""))))
    side_list = "".join(
        '<a class="lrow" href="%s"><span class="lrow-text"><span class="fcat">%s</span><span class="ltitle">%s</span>'
        '<span class="fmeta">%s</span></span><span class="lrow-img">%s</span></a>'
        % (esc(e["href"]), esc(e["cat"]), esc(e["title"]), esc(fmt_date(e["date"])), img_tag(e.get("thumb"), e["title"]))
        for e in rest)
    text_cards = "".join(
        '<a class="tcard" href="%s">%s<span class="fcat">%s</span><span class="ttitle">%s</span><span class="fmeta">%s</span></a>'
        % (esc(e["href"]), '<span class="tthumb">%s</span>' % img_tag(e.get("thumb"), e["title"]) if e.get("thumb") else "",
           esc(e["cat"]), esc(e["title"]), esc(fmt_date(e["date"]))) for e in more)
    ticker = "".join('<a href="%s">%s</a>' % (esc(e["href"]), esc(e["title"])) for e in evs[:5])

    def band(title, href, items, kind, cls=""):
        cards = "".join(card(i, kind) for i in items)
        return ('<section class="band %s"><div class="band-head"><h2>%s</h2><a href="%s">കൂടുതൽ വായിക്കുക ›</a></div>'
                '<div class="band-row">%s</div></section>' % (cls, esc(title), esc(href), cards))

    lists_html = "".join(
        '<section class="llist"><h3><a href="%s">%s ›</a></h3><ul>%s</ul></section>'
        % (esc(l["href"]), esc(l["label"]), "".join('<li><a href="%s">%s</a></li>' % (esc(i["href"]), esc(i["title"])) for i in l["items"][:5]))
        for l in lsts if l["items"])

    counts = collections.OrderedDict()
    for e in evs:
        counts[e["date"][:4]] = counts.get(e["date"][:4], 0) + 1
    year_links = "\n".join('<li><a href="years.html#y%s">%s</a> <span class="fmeta">· %s</span></li>' % (y, y, "1 പരിപാടി" if n == 1 else "%d പരിപാടികൾ" % n) for y, n in list(counts.items())[:6])
    return """<!-- front:start -->
<div class="front" id="front">

<h1 class="sr-only">ആലക്കോട് സർഗവേദി റീഡേഴ്സ് ഫോറം</h1>

<div class="ticker"><span class="ticker-label">പുതിയത്</span><span class="ticker-items">%(ticker)s</span></div>

<div class="front-grid">

<main class="front-main">

<div class="lead-row">
%(lead)s
<div class="lead-list">%(side_list)s</div>
</div>

<div class="tcards">%(text_cards)s</div>
<p class="more-link"><a href="2026/index.html">2026-ലെ എല്ലാ പരിപാടികളും ›</a></p>

%(veet)s
%(books)s
%(writers)s

<div class="lists">%(lists)s</div>

</main>

<aside class="front-side">

<section class="box">
<h2>സർഗവേദിയെക്കുറിച്ച്</h2>
<p>2006 മുതൽ കണ്ണൂർ ജില്ലയിലെ ആലക്കോട് കേന്ദ്രീകരിച്ച് പ്രവർത്തിക്കുന്ന സാഹിത്യ-സാംസ്കാരിക കൂട്ടായ്മ. 2017 മുതൽ എഴുത്തുകാരെയും വായനക്കാരെയും വീട്ടുമുറ്റങ്ങളിൽ ഒരുമിപ്പിക്കുന്ന വീട്ടുമുറ്റ ചർച്ചകൾ ഫോറത്തിന്റെ സവിശേഷ പ്രവർത്തനമാണ്.</p>
<p class="box-links"><a href="about.html">കൂടുതൽ അറിയാൻ ›</a> <a href="history.html">ചരിത്രം ›</a></p>
</section>

<section class="box">
<h2>പുരസ്കാരങ്ങൾ</h2>
<ul class="plain-list">
<li><b>പി.ടി. തങ്കപ്പൻ മാസ്റ്റർ സാഹിത്യ പുരസ്കാരം 2026</b><br>ഡോ. സുനിൽ പി. ഇളയിടം</li>
<li><b>വായനാ പുരസ്കാരം 2026</b><br>ബെന്നി സെബാസ്റ്റ്യൻ കുറ്റിവേലിൽ</li>
<li><b>തങ്കപ്പൻ മാസ്റ്റർ പുരസ്കാരം 2025</b><br>വിനോയ് തോമസ്</li>
</ul>
<p class="box-links"><a href="awards.html">എല്ലാ പുരസ്കാരങ്ങളും ›</a></p>
</section>

<section class="box">
<h2>ഫോറത്തെ അറിയാൻ</h2>
<ul class="plain-list">
<li><a href="veettumuttam.html">വീട്ടുമുറ്റ ചർച്ചകൾ</a></li>
<li><a href="people.html">എഴുത്തുകാരും അതിഥികളും</a></li>
<li><a href="media.html">മാധ്യമങ്ങളിൽ സർഗവേദി</a></li>
</ul>
</section>

<section class="box">
<h2>പരിപാടികളുടെ ശേഖരം</h2>
<ul class="plain-list">
%(year_links)s
<li><a href="years.html">എല്ലാ വർഷങ്ങളും ›</a></li>
</ul>
</section>

</aside>

</div>

</div>
<!-- front:end -->""" % dict(
        ticker=ticker, lead=lead_html, side_list=side_list, text_cards=text_cards,
        veet=band("വീട്ടുമുറ്റ ചർച്ചകൾ", "veettumuttam.html", veet, "event"),
        books=band("പുസ്തക നിരൂപണങ്ങൾ", "books/Books/index_page01.html", bks[:5], "book", "band-books"),
        writers=band("ലോക പ്രശസ്ത എഴുത്തുകാർ", "books/Writters/world-writers.html", wrs[:5], "writer", "band-books"),
        lists=lists_html, year_links=year_links)


BLANK = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="


def poster_html(src, alt, w, h, cls="poster"):
    """Poster picture for event cards. Phones get a 1-pixel placeholder (the poster is hidden there
    anyway), so they never download the thumbnail."""
    return ('<span class="%s"><picture><source media="(max-width: 900px)" srcset="%s">'
            '<img src="%s" alt="%s" width="%d" height="%d" loading="lazy"></picture></span>'
            % (cls, BLANK, esc(src), esc(alt), w, h))


def archive_html(evs):
    years = collections.OrderedDict()
    for e in evs:
        years.setdefault(e["date"][:4], []).append(e)
    jump = " ".join('<a href="#y%s">%s</a>' % (y, y) for y in years)
    blocks = []
    for y, items in years.items():
        cards = []
        for e in items:
            pdf = e["href"].endswith(".pdf")
            meta = " · ".join(x for x in (e["cat"] if e["cat"] != "പരിപാടി" else "", e["venue"]) if x)
            poster = ""
            if e.get("thumb"):
                with Image.open(e["thumb"]) as im:
                    pw, ph = im.size
                poster = poster_html(e["thumb"], e["title"], pw, ph) + "\n"
            cards.append(
                '<a href="%s" class="month-card"%s>\n%s\U0001F3A4 <b>%s</b><br>\n<small>%s</small>\n<small>%s</small>\n</a>'
                % (esc(e["href"]), ' target="_blank"' if pdf else "", poster, esc(e["title"]), esc(meta), esc(e["label"] or fmt_date(e["date"]))))
        blocks.append('<section class="months year-block" id="y%s">\n<h2>%s <span class="year-count">· %s</span></h2>\n<div class="month-grid numbered">\n\n%s\n\n</div>\n</section>'
                      % (y, y, "1 പരിപാടി" if len(items) == 1 else "%d പരിപാടികൾ" % len(items), "\n\n".join(cards)))
    return ('<!-- archive:start -->\n<nav class="year-jump" aria-label="വർഷങ്ങൾ">%s</nav>\n\n%s\n<!-- archive:end -->'
            % (jump, "\n\n".join(blocks)))


def add_posters(page, evs, cls="poster", suffix=""):
    """Puts each item's poster (events) or cover (books, cls="cover") inside its card on an index page
    (desktop only, see style.css). An existing one is replaced, so this can be re-run safely."""
    text = read(page)
    nlc = "\r\n" if "\r\n" in text else "\n"
    base = page.rsplit("/", 1)[0]
    by_href = {e["href"]: e for e in evs}

    def repl(m):
        head, href, body = m.group(1), m.group(2), m.group(3)
        body = re.sub(r'\s*<span class="%s">(?:<picture>.*?</picture>|<img[^>]*>)</span>' % cls, "", body, count=1, flags=re.S)
        e = by_href.get(resolve(base + "/x", href.replace("\\", "/")))
        if not e or not e.get("thumb"):
            return head + body
        with Image.open(e["thumb"]) as im:
            pw, ph = im.size
        src = os.path.relpath(e["thumb"], base).replace("\\", "/")
        return head + nlc + poster_html(src, e["title"] + suffix, pw, ph, cls) + body

    new = re.sub(r'(<a href="([^"]+)"[^>]*class="month-card">)(.*?)(?=</a>)', repl, text, flags=re.S)
    if new != text:
        with open(page, "w", encoding="utf-8", newline="") as f:
            f.write(new)


def write_archive(evs):
    s = read("years.html")
    nl = "\r\n" if "\r\n" in s else "\n"
    block = archive_html(evs).replace("\n", nl)
    if "<!-- archive:start -->" in s:
        s = re.sub(r"<!-- archive:start -->.*?<!-- archive:end -->", lambda m: block, s, count=1, flags=re.S)
    else:
        raise SystemExit("years.html has no archive markers")
    with open("years.html", "w", encoding="utf-8", newline="") as f:
        f.write(s)


def main():
    evs = events()
    bks = books()
    wrs = writers()
    lsts = lists()

    for e in evs[:16]:
        page = e["href"]
        if page.endswith(".html"):
            e["thumb"] = thumb(first_image(page), e["slug"])
        elif page.endswith(".pdf"):
            e["thumb"] = pdf_thumb(page, e["slug"])
    # every event gets a poster for the year-wise archive (smaller than the front-page ones)
    for e in evs:
        if not e.get("thumb"):
            if e["href"].endswith(".html"):
                e["thumb"] = thumb(first_image(e["href"]), e["slug"], 480)
            elif e["href"].endswith(".pdf"):
                e["thumb"] = pdf_thumb(e["href"], e["slug"], 480)
    # veettumuttam sessions: events whose title says so, newest first
    veet = [e for e in evs if e["cat"] == "വീട്ടുമുറ്റ ചർച്ച"][:4]
    for e in veet:
        if not e.get("thumb"):
            e["thumb"] = thumb(first_image(e["href"]), e["slug"])
    for b in bks:
        b["thumb"] = thumb(b["img"], b["slug"], 400)
    for w in wrs:
        w["thumb"] = thumb(w["img"], w["slug"], 400)

    # lead story needs a picture; otherwise take the newest event that has one
    with_pic = [e for e in evs if e.get("thumb")]
    if not evs[0].get("thumb") and with_pic:
        evs.remove(with_pic[0])
        evs.insert(0, with_pic[0])

    feed = dict(
        events=[{k: e.get(k, "") for k in ("title", "cat", "date", "venue", "href", "thumb")} for e in evs[:12]],
        books=[{k: b.get(k, "") for k in ("title", "author", "href", "thumb")} for b in bks[:6]],
    )
    with open("feed.json", "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=1)

    write_archive(evs)
    for idx in EVENT_INDEXES:
        add_posters(idx, evs)
    for idx in ("books/Books/index_page01.html", "books/Books/index_page02.html"):
        add_posters(idx, bks, "cover", " – പുസ്തകത്തിന്റെ കവർ")
    for idx, suffix in COVER_PAGES:
        add_posters(idx, card_items(idx), "cover", suffix)
    block = front_html(evs, bks, wrs, veet, lsts)
    s = read("index.html")
    nl = "\r\n" if "\r\n" in s else "\n"
    block = block.replace("\n", nl)
    if "<!-- front:start -->" in s:
        s = re.sub(r"<!-- front:start -->.*?<!-- front:end -->", lambda m: block, s, count=1, flags=re.S)
    else:
        s = s.replace('<section class="about">', block + nl + nl + '<section class="about">', 1)
    with open("index.html", "w", encoding="utf-8", newline="") as f:
        f.write(s)
    print("events %d, books %d, writers %d; thumbs %d" % (len(evs), len(bks), len(wrs), len(os.listdir(THUMBS))))


if __name__ == "__main__":
    main()
