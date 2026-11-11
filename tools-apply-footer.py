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

BRAND_SVG = '<img src="/favicon.svg" alt="" width="22" height="22" style="display:block" />'

PRODUCT = [
    ("How it works", "/how.html"),
    ("All cases", "/cases.html"),
    ("Learning pathways", "/pathways.html"),
    ("Course packs", "/courses.html"),
    ("For college programs", "/programs.html"),
    ("MITRE ATT&amp;CK coverage", "/attack.html"),
    ("Student portal &amp; LMS", "/student-portal.html"),
    ("Scenario packs", "/packs.html"),
    ("Pricing", "/#pricing"),
]
RESOURCES = [
    ("Help &amp; getting started", "/help.html"),
    ("Tools &amp; setup", "/tools.html"),
    ("Free resources", "/resources.html"),
    ("Press kit", "/press.html"),
    ("Blog", "/blog/"),
    ("Compare", "/compare.html"),
    ("FAQ", "/#faq"),
    ("Trust &amp; security", "/trust.html"),
    ("Verify a certificate", "/verify.html"),
    ("Download", "/download.html"),
    ("Contact", "/contact.html"),
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
        <h2>{title}</h2>{items}
      </div>'''


def legal_links():
    return '\n        '.join(f'<a href="{href}">{label}</a>' for label, href in LEGAL)


FOOTER = f'''<footer>
  <div class="wrap">
    <div class="ftop">
      <div class="fbrand">
        <div class="brand"><a href="/" aria-label="Red Herrings home" style="display:inline-flex;align-items:center;gap:8px;text-decoration:none">{BRAND_SVG}<span style="font-size:16px">Red Herrings</span></a></div>
        <p>Real Evidence. Real Skills. Real Fast.</p>
        <p class="fsmall">Runs locally on Windows, macOS and Linux. No student data ever leaves your machine.</p>
        <a class="fmail" href="/contact.html">Contact us</a> &middot; <span class="fsmall">sales@redherrings.app</span>
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
    # pages opt in with a <footer>...</footer> block; an empty <footer></footer>
    # placeholder is enough for a new page to pick up the canonical footer
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
