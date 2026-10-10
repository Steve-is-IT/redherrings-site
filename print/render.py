"""Render the print/*.html resources to PDF with the pre-installed Chromium.
Usage: /home/user/venv/bin/python print/render.py [name ...]"""
import asyncio, glob, os, sys
from playwright.async_api import async_playwright
D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(D), "files")
async def main(names):
    srcs = [os.path.join(D, n + ".html") for n in names] if names else sorted(glob.glob(os.path.join(D, "*.html")))
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
        for src in srcs:
            name = os.path.basename(src)[:-5]
            pg = await b.new_page()
            await pg.goto("file://" + src, wait_until="networkidle")
            await pg.wait_for_timeout(500)
            out = os.path.join(OUT, name + ".pdf")
            await pg.pdf(path=out, width="8.5in", height="11in", print_background=True, prefer_css_page_size=True,
                         margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
            n = await pg.evaluate("document.querySelectorAll('.page').length")
            print(name, "->", os.path.relpath(out, os.path.dirname(D)), f"({n} page{'s' if n != 1 else ''})")
            await pg.close()
        await b.close()
asyncio.run(main(sys.argv[1:]))
