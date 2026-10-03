#!/usr/bin/env python3
"""Replace the site footer on every page with the slim footer.

Brand + two columns (Product, Resources) + inline legal in the bottom bar.
Root-absolute links so it is byte-identical on every page including /blog/.
Rerunnable. The header now carries discovery, so the footer no longer needs
to be the full sitemap.
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))

BRAND_SVG = ('<svg width="22" height="22" viewBox="5.1 3 58 58" aria-hidden="true">'
             '<path fill-rule="evenodd" d="M6 32c9-11 20-16 30-16C40 16 44 19 48 25C51 22 56.5 15.5 62.25 11.75'
             'C58.38 18.12 55.69 25.81 54.44 32C55.69 38.19 58.38 45.88 62.25 52.25C56.5 48.5 51 42 48 39'
             'C44 45 40 48 36 48c-10 0-21-5-30-16z M20 24.8a5.6 5.6 0 1 0 0 11.2 5.6 5.6 0 1 0 0-11.2z" fill="var(--accent)"/>'
             '<circle cx="20" cy="30.4" r="3.2" fill="none" stroke="var(--accent)" stroke-width="2"/>'
             '<path d="M23 33.4l4 4" stroke="var(--accent)" stroke-width="2.6" stroke-linecap="round"/></svg>')

PRODUCT = [
    ("How it works", "/how.html"),
    ("All cases", "/cases.html"),
    ("Learning pathways", "/pathways.html"),
    ("MITRE ATT&amp;CK coverage", "/attack.html"),
    ("Student portal &amp; LMS", "/student-portal.html"),
    ("Pricing", "/#pricing"),
]
RESOURCES = [
    ("Help &amp; getting started", "/help.html"),
    ("Tools &amp; setup", "/tools.html"),
    ("Blog", "/blog/"),
    ("FAQ", "/#faq"),
    ("Trust &amp; security", "/trust.html"),
    ("Download", "/#download"),
]
LEGAL = [
    ("Privacy", "/privacy.html"),
    ("Terms", "/terms.html"),
    ("License agreement", "/eula.html"),
    ("Refund", "/refund.html"),
    ("Accessibility", "/accessibility.html"),
]


def col(title, links):
    items = "".join(f'\n        <a href="{href}">{label}</a>' for label, href in links)
    return f'''<div class="fcol">
        <h4>{title}</h4>{items}
      </div>'''


def legal_links():
    return '\n        '.join(f'<a href="{href}">{label}</a>' for label, href in LEGAL)


FOOTER = f'''<footer>
  <div class="wrap">
    <div class="ftop">
      <div class="fbrand">
        <div class="brand"><a href="/" aria-label="Red Herrings home" style="display:inline-flex;align-items:center;gap:8px;text-decoration:none">{BRAND_SVG}<span style="color:var(--ink);font-size:16px">Red Herrings</span></a></div>
        <p>Real Evidence. Real Skills. Real Fast.</p>
        <p class="fsmall">Runs locally on Windows and Linux. No student data ever leaves your machine.</p>
        <a class="fmail" href="mailto:sales@redherrings.app">sales@redherrings.app</a>
      </div>
      {col("Product", PRODUCT)}
      {col("Resources", RESOURCES)}
    </div>
    <div class="fbottom">
      <span>&copy; 2026 Red Herrings, a product of The Competence Collective, LLC. Prices in USD; institutional purchase orders welcome.</span>
      <nav class="flegal" aria-label="Legal">
        {legal_links()}
      </nav>
    </div>
  </div>
</footer>'''

FTR_RE = re.compile(r"<footer>.*?</footer>", re.S)


def apply(path):
    with open(path) as fh:
        s = fh.read()
    if "<footer>" not in s:
        return False
    s = FTR_RE.sub(lambda m: FOOTER, s, count=1)
    with open(path, "w") as fh:
        fh.write(s)
    return True


def main():
    n = 0
    for p in glob.glob(os.path.join(ROOT, "*.html")) + glob.glob(os.path.join(ROOT, "blog", "*.html")):
        if apply(p):
            n += 1
    print(f"updated {n} pages")


if __name__ == "__main__":
    main()
