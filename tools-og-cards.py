#!/usr/bin/env python3
"""Render the link-preview (Open Graph) cards and point the pages at them.

    python3 tools-og-cards.py

Three cards: home (used by every page that has no card of its own), cases and
download. Each is rendered from the template below with Playwright, saved as
img/og/<name>-<hash>.png where the hash is of the PNG bytes, and every page and
generator that referenced the previous file is rewritten to the new name. The
hash in the filename is what makes Discord, iMessage and Slack fetch a fresh
image: they cache by URL and never re-check. Old files are removed; previews
already cached keep their copy.
"""
import glob, hashlib, os, re, pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "img" / "og"
FONTS = "https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Public+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap"
MARK = """<svg width="44" height="44" viewBox="5.1 3 58 58" aria-hidden="true"><path fill-rule="evenodd" d="M6 32c9-11 20-16 30-16C40 16 44 19 48 25C51 22 56.5 15.5 62.25 11.75C58.38 18.12 55.69 25.81 54.44 32C55.69 38.19 58.38 45.88 62.25 52.25C56.5 48.5 51 42 48 39C44 45 40 48 36 48c-10 0-21-5-30-16z M20 24.8a5.6 5.6 0 1 0 0 11.2 5.6 5.6 0 1 0 0-11.2z" fill="#d32f26"/><circle cx="20" cy="30.4" r="3.2" fill="none" stroke="#d32f26" stroke-width="2"/><path d="M23 33.4l4 4" stroke="#d32f26" stroke-width="2.6" stroke-linecap="round"/></svg>"""

BASE_CSS = """
*{box-sizing:border-box;margin:0}html,body{width:1200px;height:630px;overflow:hidden}
body{font-family:"Public Sans",-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#111a26;background:#f3f6fa;position:relative;-webkit-font-smoothing:antialiased}
.wash{position:absolute;inset:0;background:radial-gradient(900px 420px at 85% -10%,rgba(31,95,191,.14),transparent 60%),radial-gradient(700px 380px at -5% 110%,rgba(211,47,38,.10),transparent 60%)}
.card{position:absolute;inset:0;padding:60px 0 0 68px;display:grid;grid-template-columns:560px 1fr;gap:36px}
.brand{display:flex;align-items:center;gap:14px;font-family:"Sora",sans-serif;font-weight:700;font-size:30px;letter-spacing:-.01em}
.kick{margin-top:44px;font-family:"JetBrains Mono",Menlo,Consolas,monospace;font-size:16px;letter-spacing:.14em;text-transform:uppercase;color:#d32f26;font-weight:600}
h1{margin-top:12px;font-family:"Sora",sans-serif;font-weight:700;font-size:62px;line-height:1.06;letter-spacing:-.025em}
h1 em{font-style:normal;color:#d32f26}
.lede{margin-top:22px;font-size:26px;line-height:1.4;color:#3e4a5a;max-width:520px}
.url{position:absolute;left:68px;bottom:40px;font-family:"Sora",sans-serif;font-weight:700;font-size:22px}
.shot{position:relative;margin-top:36px;height:560px;border-radius:14px 0 0 0;overflow:hidden;border:1px solid #cfd8e4;border-right:0;box-shadow:0 24px 60px -20px rgba(17,26,38,.35);background:#fff}
.shot .bar{height:30px;background:#eef2f7;border-bottom:1px solid #e3e9f1;display:flex;align-items:center;gap:7px;padding-left:14px}
.shot .bar i{width:10px;height:10px;border-radius:50%;display:block}
.shot img{display:block;width:1000px;height:auto}
.badges{margin-top:30px;display:flex;gap:12px;flex-wrap:wrap;max-width:520px}
.badge{font-size:19px;font-weight:600;padding:12px 20px;border-radius:999px;background:#fff;border:1px solid #cfd8e4;box-shadow:0 1px 2px rgba(17,26,38,.06)}
.badge.red{background:#d32f26;border-color:#d32f26;color:#fff}
.gold{color:#8a6508}
.bottom{position:absolute;left:0;right:0;bottom:0;height:8px;background:#d32f26}
"""

def shot(img):
    return ('<div class="shot"><div class="bar"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i>'
            f'<i style="background:#28c840"></i></div><img src="file://{ROOT}/img/{img}"></div>')

CARDS = {
    # name: (left column html, right column html, pages/generators that use it)
    "home": (
        '<div class="kick">Real Evidence. Real Skills. Real Fast.</div>'
        '<h1>Real DFIR evidence. <em>Labs graded for you.</em></h1>'
        '<p class="lede">Every student gets a different case.</p>',
        shot("slides/slide-results.jpg"),
        None,  # every page not claimed by another card
    ),
    "cases": (
        '<div class="kick gold">Case library</div>'
        '<h1>Dozens of DFIR cases. <em>One per student.</em></h1>'
        '<p class="lede">First Look to Marquee capstone, forensics and incident response.</p>',
        shot("slides/slide-library.jpg"),
        ["cases.html", "tools-gen-cases.py"],
    ),
    "download": (
        '<div class="kick">Download</div>'
        '<h1>Runs on your machine. <em>Nothing leaves it.</em></h1>'
        '<div class="badges"><span class="badge">Windows</span><span class="badge">macOS</span><span class="badge">Linux</span>'
        '<span class="badge red">30-day free trial, no key needed</span></div>',
        shot("slides/slide-generate.jpg"),
        ["download.html", "tools-gen-download.py"],
    ),
}

def page_html(left, right):
    return (f'<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{FONTS}">'
            f'<style>{BASE_CSS}</style></head><body><div class="wash"></div><div class="card">'
            f'<div><div class="brand">{MARK}<span>Red Herrings</span></div>{left}</div>{right}</div>'
            f'<div class="url">redherrings.app</div><div class="bottom"></div></body></html>')

REF = re.compile(r'https://redherrings\.app/img/(?:og[^"\s]*\.png)')

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = ROOT / "img" / "og" / "_render.html"
    names = {}
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("CHROME", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"))
        pg = b.new_page(viewport={"width": 1200, "height": 630})
        for name, (left, right, _) in CARDS.items():
            tmp.write_text(page_html(left, right), encoding="utf-8")
            pg.goto(tmp.as_uri()); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(600)
            png = pg.screenshot()
            h = hashlib.sha256(png).hexdigest()[:8]
            fn = f"{name}-{h}.png"
            (OUT / fn).write_bytes(png)
            names[name] = fn
            for old in OUT.glob(f"{name}-*.png"):
                if old.name != fn: old.unlink()
        b.close()
    tmp.unlink(missing_ok=True)
    # Point pages and generators at the new files.
    files = [f for f in glob.glob(str(ROOT / "**" / "*.html"), recursive=True) if "/node_modules/" not in f]
    files += glob.glob(str(ROOT / "tools-gen-*.py"))
    claimed = {}
    for name, (_, _, owners) in CARDS.items():
        for o in owners or []: claimed[str(ROOT / o)] = name
    changed = 0
    for f in files:
        name = claimed.get(f, "home")
        url = f"https://redherrings.app/img/og/{names[name]}"
        s = open(f, encoding="utf-8").read()
        t = REF.sub(url, s)
        if t != s:
            open(f, "w", encoding="utf-8").write(t); changed += 1
    for n, fn in names.items(): print(f"{n}: img/og/{fn}")
    print(f"updated {changed} files")

if __name__ == "__main__":
    main()
