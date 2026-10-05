#!/usr/bin/env python3
"""Replace the site header on every page with the mega-menu (Direction A).

One canonical header, root-absolute links so it is byte-identical on every
page including /blog/. Also wires nav.js in beside theme.js. Rerunnable.
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))

HOOK = ('<svg width="28" height="28" viewBox="5.1 3 58 58" aria-hidden="true">'
        '<path fill-rule="evenodd" d="M6 32c9-11 20-16 30-16C40 16 44 19 48 25C51 22 56.5 15.5 62.25 11.75'
        'C58.38 18.12 55.69 25.81 54.44 32C55.69 38.19 58.38 45.88 62.25 52.25C56.5 48.5 51 42 48 39'
        'C44 45 40 48 36 48c-10 0-21-5-30-16z M20 24.8a5.6 5.6 0 1 0 0 11.2 5.6 5.6 0 1 0 0-11.2z" fill="var(--accent)"/>'
        '<circle cx="20" cy="30.4" r="3.2" fill="none" stroke="var(--accent)" stroke-width="2"/>'
        '<path d="M23 33.4l4 4" stroke="var(--accent)" stroke-width="2.6" stroke-linecap="round"/></svg>')

ICONS = {
    "how": '<path d="M3 3h18v14H3z"/><path d="M8 21h8M12 17v4"/>',
    "cases": '<path d="M4 7h16v12H4z"/><path d="M9 7V5h6v2"/>',
    "attack": '<path d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z"/>',
    "path": '<path d="M5 20V9a3 3 0 0 1 3-3h8M16 3l4 3-4 3"/>',
    "ir": '<path d="M3 12h4l2 6 4-14 2 8h6"/>',
    "portal": '<path d="M4 5h16v12H4zM2 21h20"/>',
    "blog": '<path d="M5 3h10l4 4v14H5zM14 3v5h5"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-1 .5-1 1.2-1 2M12 17h.01"/>',
    "tools": '<path d="M14 7a4 4 0 0 1-5 5l-6 6 2 2 6-6a4 4 0 0 1 5-5z"/>',
    "trust": '<path d="M12 3l8 3v6c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V6z"/>',
    "buy": '<path d="M5 7h14l-1 13H6zM9 7a3 3 0 0 1 6 0"/>',
    "edu": '<path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/>',
    "team": '<circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0M17 11a3 3 0 0 0 0-6M21 20a6 6 0 0 0-5-5.9"/>',
    "key": '<circle cx="8" cy="12" r="4"/><path d="M12 12h9l-2 2 2 2M11.5 12H21"/>',
    "faq": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-1 .5-1 1.2-1 2M12 17h.01"/>',
}


def icon(k):
    return ('<span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + ICONS[k] + "</svg></span>")


# link inventory: key -> (title, desc, href, icon)
L = {
    "how": ("How it works", "Author once, generate a unique case per student", "/how.html", "how"),
    "cases": ("Case library", "70 verified DF &amp; IR cases to browse", "/cases.html", "cases"),
    "attack": ("MITRE ATT&amp;CK coverage", "Techniques mapped to real evidence", "/attack.html", "attack"),
    "path": ("Learning pathways", "First Look on-ramp to cert-prep capstone", "/pathways.html", "path"),
    "ir": ("Incident response", "EDR, SIEM and triage exercises", "/incident-response.html", "ir"),
    "portal": ("Student portal &amp; LMS", "In-browser solve, grading, LMS passback", "/student-portal.html", "portal"),
    "blog": ("Blog", "DFIR teaching notes and updates", "/blog/", "blog"),
    "help": ("Help &amp; getting started", "Install, activate and run your first lab", "/help.html", "help"),
    "tools": ("Tools &amp; setup", "Autopsy, Volatility, Wireshark and more", "/tools.html", "tools"),
    "trust": ("Trust &amp; security", "Runs locally; no student data leaves", "/trust.html", "trust"),
    "faq": ("FAQ", "Licensing, platforms, classroom use", "/#faq", "faq"),
    "sample": ("Download a sample lab", "A full case ZIP with a verified key", "/sample.html", "key"),
    "edu": ("Educators", "One instructor, auto-graded labs", "/#pricing", "edu"),
    "dept": ("Departments", "Multiple instructors, all packs", "/#pricing", "edu"),
    "student": ("Students", "Self-practice at the personal rate", "/#pricing", "portal"),
    "team": ("Business &amp; training", "Commercial use, CTF mode, per seat", "/#pricing", "team"),
    "ent": ("Enterprise &amp; government", "White-label, volume, procurement", "mailto:sales@redherrings.app", "buy"),
}


def mlink(k):
    t, d, href, ic = L[k]
    return (f'<a class="mlink" href="{href}">{icon(ic)}'
            f'<span><span class="mt">{t}</span><span class="md">{d}</span></span></a>')


def mcol(head, keys):
    return (f'<div class="mpcol"><div class="mphead">{head}</div>'
            + "".join(mlink(k) for k in keys) + "</div>")


def promo():
    return ('<a class="mppromo" href="/try.html"><span class="eye">Try it live</span>'
            '<strong>Solve a case in the browser</strong>'
            '<span class="pd">A real sample case with a verified answer key. No install.</span>'
            '<span class="go">Open the demo &rarr;</span></a>')


CARET = ('<svg class="mncaret" viewBox="0 0 10 10" fill="none" stroke="currentColor" '
         'stroke-width="1.6"><path d="M2 3.5L5 6.5L8 3.5"/></svg>')

# menu structure (Direction A)
MENU = [
    ("Platform", [("Explore", ["how", "cases", "attack"]), ("Go deeper", ["path", "ir", "portal"])], True),
    ("Solutions", [("By role", ["edu", "dept", "student"]), ("For organizations", ["team", "ent"])], False),
    ("Resources", [("Learn", ["blog", "help", "tools"]), ("Evaluate", ["trust", "faq", "sample"])], False),
]


def desktop_item(label, cols, has_promo):
    colshtml = "".join(mcol(h, ks) for h, ks in cols)
    cls = "megapanel" if has_promo else "megapanel nopromo"
    inner = f'<div class="mpcols">{colshtml}</div>' + (promo() if has_promo else "")
    return (f'<div class="mnitem haspanel"><button type="button" class="mntrig" aria-expanded="false">'
            f'{label} {CARET}</button><div class="{cls}">{inner}</div></div>')


def mobile_section(label, cols):
    links = []
    for _, ks in cols:
        links += ks
    seen, ordered = set(), []
    for k in links:
        if k not in seen:
            seen.add(k); ordered.append(k)
    return (f'<div class="mnsection"><div class="mnsh">{label}</div>'
            + "".join(mlink(k) for k in ordered) + "</div>")


# Customer account portal (license server). Swap to a custom domain
# (e.g. https://account.redherrings.app/account) once its CNAME is set up.
ACCOUNT_URL = "https://account.redherrings.app/account"


def build_header():
    desktop = "".join(desktop_item(lbl, cols, p) for lbl, cols, p in MENU)
    mobile = "".join(mobile_section(lbl, cols) for lbl, cols, _ in MENU)
    burger = ('<button type="button" class="navburger" aria-label="Open menu" aria-expanded="false" '
              'aria-controls="mobilenav"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
              'stroke-width="2" stroke-linecap="round"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button>')
    return f'''<header>
  <a class="skip" href="#main">Skip to content</a>
  <div class="wrap nav">
    <a class="brand" href="/" aria-label="Red Herrings home">
      {HOOK}
      <span style="color:var(--ink)">Red Herrings</span>
    </a>
    <nav class="mainnav" aria-label="Primary">
      {desktop}
      <a class="mnitem mnflat" href="/#pricing">Pricing</a>
    </nav>
    <div class="spacer"></div>
    <a class="link navutil" href="{ACCOUNT_URL}">Sign in</a>
    <a class="link navutil" href="/student-portal.html">Student portal</a>
    <a class="btn navcta" href="/#download" data-goatcounter-click="cta-trial-nav">Start free trial</a>
    {burger}
  </div>
  <div class="mobilenav" id="mobilenav" hidden>
    <a class="btn" href="/#download" data-goatcounter-click="cta-trial-nav" style="display:flex;justify-content:center;margin-bottom:6px">Start free trial</a>
    {mobile}
    <div class="mnsection"><a class="mnflat mnsolo" href="/#pricing">Pricing</a></div>
    <div class="mnrow">
      <a class="btn ghost" href="{ACCOUNT_URL}">Sign in</a>
      <a class="btn ghost" href="/student-portal.html">Student portal</a>
    </div>
    <div class="mnrow">
      <a class="btn ghost" href="/#download">Activate a key</a>
    </div>
  </div>
</header>'''


HEADER = build_header()
HDR_RE = re.compile(r"<header>.*?</header>", re.S)


def apply(path, blog):
    with open(path) as fh:
        s = fh.read()
    if "<header>" not in s:
        return False
    s = HDR_RE.sub(lambda m: HEADER, s, count=1)
    # wire nav.js in front of theme.js (idempotent)
    if blog:
        if '"../nav.js"' not in s:
            s = s.replace('<script src="../theme.js" defer></script>',
                          '<script src="../nav.js" defer></script>\n<script src="../theme.js" defer></script>', 1)
    else:
        if '"nav.js"' not in s:
            s = s.replace('<script src="theme.js" defer></script>',
                          '<script src="nav.js" defer></script>\n<script src="theme.js" defer></script>', 1)
    with open(path, "w") as fh:
        fh.write(s)
    return True


def main():
    n = 0
    for p in glob.glob(os.path.join(ROOT, "*.html")):
        if apply(p, blog=False):
            n += 1; print("root ", os.path.basename(p))
    for p in glob.glob(os.path.join(ROOT, "blog", "*.html")):
        if apply(p, blog=True):
            n += 1; print("blog ", os.path.basename(p))
    print(f"updated {n} pages")


if __name__ == "__main__":
    main()
