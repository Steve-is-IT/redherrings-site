#!/usr/bin/env python3
"""Generate a 1200x630 share card for each blog post and the blog index, and
point each page's og:image / twitter:image at it.

A link to a post on LinkedIn, Slack or X then shows that post's title and
category instead of the home page card. Cards are rendered with Chromium
(Node Playwright) from an HTML template in the site's fonts and the category colors
used by the blog covers. File names carry a content hash so a changed title
gets a new URL and social sites fetch it again.

    python3 tools-gen-blog-og.py            # all posts + index
    python3 tools-gen-blog-og.py --check    # report pages not pointing at their card

Rerun after adding or retitling a post.
"""
import hashlib
import html
import importlib.util
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BLOG = os.path.join(ROOT, "blog")
OUT = os.path.join(ROOT, "img", "og", "blog")
BASE_URL = "https://redherrings.app"
VERSION = "2"  # bump to force new file names for every card


def _load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


build = _load("tools_build_blog", "tools-build-blog.py")
covers = _load("tools_gen_blog_covers", "tools-gen-blog-covers.py")

LOCKUP = open(os.path.join(ROOT, "img", "brand", "lockup-dark-bg.svg"), encoding="utf-8").read()

# The line icon drawn behind each card's title, per cover category. The cover
# tool used to carry these; the cards still need them.
GLYPHS = {
    "mobile":  '<rect x="6" y="2" width="12" height="20" rx="2.4"/><line x1="10.2" y1="18.4" x2="13.8" y2="18.4"/>',
    "windows": '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="12" y1="3" x2="12" y2="21"/><line x1="3" y1="12" x2="21" y2="12"/>',
    "ir":      '<path d="M10.29 3.86 L1.82 18 a2 2 0 0 0 1.71 3 h16.94 a2 2 0 0 0 1.71-3 L13.71 3.86 a2 2 0 0 0-3.42 0 z"/><line x1="12" y1="9" x2="12" y2="13.5"/><line x1="12" y1="16.6" x2="12" y2="17.2"/>',
    "threat":  '<circle cx="12" cy="12" r="9.5"/><circle cx="12" cy="12" r="4"/><line x1="12" y1="0.8" x2="12" y2="4.5"/><line x1="12" y1="19.5" x2="12" y2="23.2"/><line x1="0.8" y1="12" x2="4.5" y2="12"/><line x1="19.5" y1="12" x2="23.2" y2="12"/>',
    "network": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.6" y1="13.5" x2="15.4" y2="17.5"/><line x1="15.4" y1="6.5" x2="8.6" y2="10.5"/>',
    "course":  '<path d="M12 3 L23 8 L12 13 L1 8 Z"/><path d="M5 10 V15.3 C5 17 8.1 18.3 12 18.3 C15.9 18.3 19 17 19 15.3 V10"/>',
    "exam":    '<path d="M12 22 s8-4 8-10 V5 l-8-3-8 3 v7 c0 6 8 10 8 10 z"/><rect x="9.4" y="11" width="5.2" height="4.4" rx="0.7"/><path d="M10.5 11 V9.6 a1.5 1.5 0 0 1 3 0 V11"/>',
    "tools":   '<path d="M14.7 6.3 a1 1 0 0 0 0 1.4 l1.6 1.6 a1 1 0 0 0 1.4 0 l3.77-3.77 a6 6 0 0 1-7.94 7.94 l-6.91 6.91 a2.12 2.12 0 0 1-3-3 l6.91-6.91 a6 6 0 0 1 7.94-7.94 l-3.76 3.76 z"/>',
    "secops":  '<rect x="2" y="4" width="20" height="13" rx="2"/><circle cx="12" cy="10.3" r="2.6"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>',
    "buying":  '<path d="M20.6 13.4 l-7.2 7.2 a2 2 0 0 1-2.8 0 l-6.4-6.4 a2 2 0 0 1 0-2.8 l7.2-7.2 h6.4 a2.8 2.8 0 0 1 2.8 2.8 z"/><circle cx="16.3" cy="7.7" r="1.3"/>',
}


def card_html(title, cat_label, accent, base, glyph):
    t = html.escape(title)
    size = 64 if len(title) <= 60 else 56 if len(title) <= 80 else 50
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@700;800&family=Public+Sans:wght@500;600&display=swap">
<style>
*{{box-sizing:border-box;margin:0}}
html,body{{width:1200px;height:630px;overflow:hidden}}
body{{font-family:'Public Sans',system-ui,sans-serif;color:#fff;position:relative;
  background:radial-gradient(900px 600px at 15% 10%, {accent}55, transparent 60%),
             radial-gradient(700px 500px at 100% 100%, {accent}33, transparent 60%),
             linear-gradient(135deg, {base} 0%, #0b0f17 100%)}}
.glyph{{position:absolute;right:-40px;top:70px;width:520px;height:520px;opacity:.13}}
.glyph svg{{width:100%;height:100%;fill:none;stroke:#fff;stroke-width:1.3;stroke-linecap:round;stroke-linejoin:round}}
.wrap{{position:absolute;inset:64px 72px 56px 72px;display:flex;flex-direction:column}}
.logo svg{{height:54px;width:auto;display:block}}
.bar{{position:absolute;left:0;top:0;right:0;height:8px;background:#d62b2b}}
.chip{{display:inline-block;margin-top:50px;align-self:flex-start;background:{accent};color:#fff;
  font:600 20px/1 'Public Sans',sans-serif;letter-spacing:.08em;text-transform:uppercase;padding:10px 16px;border-radius:999px}}
h1{{margin-top:26px;font:800 {size}px/1.1 'Sora',sans-serif;letter-spacing:-.02em;max-width:930px;
  display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}}
.foot{{margin-top:auto;font:500 22px/1 'Public Sans',sans-serif;color:#ffffffb3}}
.foot b{{color:#fff;font-weight:600}}
</style></head><body>
<div class="bar"></div>
<div class="glyph"><svg viewBox="0 0 24 24">{glyph}</svg></div>
<div class="wrap">
  <div class="logo">{LOCKUP}</div>
  <div class="chip">{html.escape(cat_label)}</div>
  <h1>{t}</h1>
  <div class="foot"><b>redherrings.app</b> / blog</div>
</div></body></html>"""


def cards():
    """(page file, title, category label, cover category key) per page."""
    out = []
    for p in build.POSTS:
        key = covers.POSTS.get(p["slug"], "tools")
        out.append((f"{p['slug']}.html", p["slug"], p["title"], p["cat"], key))
    out.append(("index.html", "index", "Teaching notes on hands-on DFIR labs and exams", "Blog", "course"))
    return out


def file_name(slug, title, cat):
    h = hashlib.sha256(f"{VERSION}|{slug}|{title}|{cat}".encode()).hexdigest()[:8]
    return f"{slug}-{h}.png"


def set_meta(page_path, url, alt):
    s = open(page_path, encoding="utf-8").read()
    n0 = s
    s = re.sub(r'(<meta property="og:image" content=")[^"]*(">)', lambda m: m.group(1) + url + m.group(2), s)
    s = re.sub(r'(<meta name="twitter:image" content=")[^"]*(">)', lambda m: m.group(1) + url + m.group(2), s)
    s = re.sub(r'(<meta property="og:image:alt" content=")[^"]*(">)',
               lambda m: m.group(1) + html.escape(alt, quote=True) + m.group(2), s)
    if s != n0:
        open(page_path, "w", encoding="utf-8").write(s)
        return True
    return False


def main():
    check = "--check" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    todo = []
    for page, slug, title, cat, key in cards():
        name = file_name(slug, title, cat)
        url = f"{BASE_URL}/img/og/blog/{name}"
        path = os.path.join(OUT, name)
        page_path = os.path.join(BLOG, page)
        if check:
            s = open(page_path, encoding="utf-8").read()
            if url not in s or not os.path.exists(path):
                print("stale:", page)
            continue
        todo.append((page_path, slug, title, cat, key, name, url, path))
    if check:
        return
    import json
    import subprocess
    import tempfile
    keep = {t[5] for t in todo}
    jobs = []
    tmp = tempfile.mkdtemp()
    for page_path, slug, title, cat, key, name, url, path in todo:
        if not os.path.exists(path):
            accent, base = covers.CATS[key]
            src = os.path.join(tmp, name + ".html")
            open(src, "w", encoding="utf-8").write(card_html(title, cat, accent, base, GLYPHS[key]))
            jobs.append({"src": src, "out": path})
    if jobs:
        # Chromium via Node's Playwright (the one preinstalled here and on dev machines).
        script = (
            "const {chromium}=require('playwright');const jobs=JSON.parse(process.argv[1]);"
            "(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1200,height:630}});"
            "for(const j of jobs){await p.goto('file://'+j.src,{waitUntil:'networkidle'});"
            "await p.evaluate(()=>document.fonts.ready);await p.screenshot({path:j.out,type:'png'});}"
            "await b.close();})().catch(e=>{console.error(e);process.exit(1)})"
        )
        subprocess.run(["node", "-e", script, json.dumps(jobs)], check=True)
    for page_path, slug, title, cat, key, name, url, path in todo:
        alt = f"{title}. Red Herrings blog." if slug != "index" else "Red Herrings blog: teaching notes on hands-on DFIR labs and exams."
        changed = set_meta(page_path, url, alt)
        print(("updated " if changed else "ok      ") + os.path.relpath(page_path, ROOT))
    for f in os.listdir(OUT):
        if f.endswith(".png") and f not in keep:
            os.remove(os.path.join(OUT, f))


if __name__ == "__main__":
    main()
