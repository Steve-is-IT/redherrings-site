#!/usr/bin/env python3
"""Generate redherrings-site/pathways.html from the live engine pathway data.

Groups the ordered learning pathways by discipline (Digital Forensics |
Incident Response), each with a Certification-prep and a By-role sub-section,
behind an All / DF / IR filter. Keeps the site in sync with the real
pathways.py so cert alignment and step lists never drift.

Also writes one landing page per pathway at pathways/<slug>.html for
certification-intent search (GCFE practice labs, CySA+ labs, ...). Those pages
live one folder down, so every link is root-absolute and the canonical
mega-menu header and footer are pulled straight from tools-apply-nav.py and
tools-apply-footer.py (which only walk the root and blog/ folders).
"""
import html
import importlib.util
import json
import os
import sys

# The product package comes from the sibling redherrings checkout (or RH_PRODUCT).
sys.path.insert(0, os.environ.get("RH_PRODUCT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "redherrings"))
from redherrings import packs, pathways  # noqa: E402
from redherrings.engine.util import up_to_questions  # noqa: E402

E = lambda s: html.escape(str(s or ""), quote=True)

DISC = [
    {"id": "digital-forensics", "label": "Digital Forensics",
     "sub": "Disk, registry, logs, memory, network, mobile and cloud, aligned to certification tracks."},
    {"id": "incident-response", "label": "Incident Response",
     "sub": "Detection and response from the responder's own tooling (EDR, SIEM and host logs), mapped to MITRE ATT&CK."},
]
KIND_LABEL = {"cert": "Cert prep", "role": "Role path"}
DIFF_TAG = {"easy": "easy", "medium": "medium", "hard": "hard", "expert": "expert",
            "first-look": "easy", "marquee": "expert"}


def fmt_time(minutes):
    if not minutes:
        return ""
    h = minutes / 60
    return f"~{round(h * 10) / 10:g} h" if h >= 1 else f"~{minutes} min"


def step_html(i, s):
    name = s.get("codename") or s.get("name") or s["id"]
    diff = s.get("difficulty") or "medium"
    tag = DIFF_TAG.get(diff, "medium")
    label = diff.replace("-", " ").upper()
    return (
        f'<li class="pwc-step"><span class="pwc-num">{i}</span><div>'
        f'<div class="pwc-name"><span>{E(name)}</span>'
        f'<span class="tag {tag}">{E(label)}</span></div>'
        f'<div class="pwc-note">{E(s["note"])}</div></div></li>'
    )


def card_html(p):
    aligned = (f'<p class="pwc-aligned">Aligned to {E(p["aligned"])}</p>'
               if p.get("aligned") else "")
    cases = p["count"]
    meta = f'{cases} case{"" if cases == 1 else "s"}'
    if p.get("total_minutes"):
        meta += "  &middot;  " + fmt_time(p["total_minutes"])
    steps = "\n".join(step_html(i + 1, s) for i, s in enumerate(p["steps"]))
    return f'''    <div class="pwc">
      <div class="pwc-head"><div><h3>{E(p["label"])}</h3>{aligned}</div><span class="pwc-kind {p["kind"]}">{KIND_LABEL[p["kind"]]}</span></div>
      <p class="pwc-blurb">{E(p["blurb"])}</p>
      <p class="pwc-meta">{meta}</p>
      <ol class="pwc-steps">
{steps}
      </ol>
      <div class="cta-row pwc-cta" style="justify-content:flex-start">
        <a class="btn" href="/pathways/{p["slug"]}.html">Open the full pathway &rarr;</a>
        <a class="btn ghost" href="cases.html">Browse the cases</a>
      </div>
    </div>'''


def discipline_html(d, cat):
    mine = [p for p in cat if p.get("discipline", "digital-forensics") == d["id"]]
    if not mine:
        return ""
    certs = [p for p in mine if p["kind"] == "cert"]
    roles = [p for p in mine if p["kind"] != "cert"]
    blocks = []
    if certs:
        blocks.append('<h3 class="pwsub">Certification prep</h3>\n    <div class="pwgrid">\n'
                      + "\n".join(card_html(p) for p in certs) + "\n    </div>")
    if roles:
        blocks.append('<h3 class="pwsub">By role</h3>\n    <div class="pwgrid">\n'
                      + "\n".join(card_html(p) for p in roles) + "\n    </div>")
    return (f'  <section class="pwdisc" data-disc="{d["id"]}">\n'
            f'    <div class="pwdisc-head"><h2>{E(d["label"])}</h2>'
            f'<p class="pwdisc-sub">{E(d["sub"])}</p></div>\n    '
            + "\n    ".join(blocks) + "\n  </section>")


def main():
    index = {r["id"]: r for r in packs.all_scenarios() if "id" in r}
    cat = pathways.catalog(index)
    n_df = sum(1 for p in cat if p.get("discipline") != "incident-response")
    n_ir = len(cat) - n_df
    sections = "\n".join(discipline_html(d, cat) for d in DISC)
    html_doc = TEMPLATE.format(sections=sections, n=len(cat), n_df=n_df, n_ir=n_ir)
    out = os.path.join(SITE, "pathways.html")
    with open(out, "w") as f:
        f.write(html_doc)
    # Stamp the canonical header and footer so the overview never carries a stale nav.
    _load_tool("tools-apply-nav").apply(out, False)
    _load_tool("tools-apply-footer").apply(out)
    print(f"wrote {out}: {len(cat)} pathways ({n_df} DF, {n_ir} IR)")
    write_pages(cat)


TEMPLATE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Learning Pathways | Red Herrings Digital Forensics &amp; Incident Response Labs</title>
<meta name="description" content="Case-by-case curricula for digital forensics (GCFE, GASF, GNFA, Linux, macOS) and incident response (GCIH, CySA+, GCFR, GCFA), from First Look to capstone, plus role paths.">
<link rel="canonical" href="https://redherrings.app/pathways.html">
<meta name="robots" content="index,follow">
<meta name="theme-color" content="#D42A2A">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 64 64%27%3E%3Cpath fill=%27%23E5382F%27 d=%27M6 32c9-11 20-16 30-16 4 0 8 3 12 9 3-3 8.5-9.5 14.25-13.25C58.38 18.12 55.69 25.81 54.44 32c1.25 6.19 3.94 13.87 7.81 20.25C56.5 48.5 51 42 48 39c-4 6-8 9-12 9-10 0-21-5-30-16z%27/%3E%3C/svg%3E">
<link rel="icon" type="image/png" sizes="32x32" href="/img/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/img/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta property="og:title" content="Learning Pathways | Red Herrings">
<meta property="og:description" content="Ordered, case-by-case curricula across Digital Forensics and Incident Response: certification prep and role paths.">
<meta property="og:url" content="https://redherrings.app/pathways.html">
<meta property="og:image" content="https://redherrings.app/img/og/home-f129ee30.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Red Herrings: randomized digital forensics and incident-response labs for the classroom.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://redherrings.app/img/og/home-f129ee30.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Public+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600;800&display=swap">
<link rel="stylesheet" href="site.css">
</head>
<body>
<header>
  <a class="annc" href="/cases.html#first-look" data-goatcounter-click="annc-free">Anyone can run the <strong>First Look cases</strong> &middot; free, no account and no watermark, in forensics and incident response. <span class="annc-go">Open a First Look case &rarr;</span></a>
  <a class="skip" href="#main">Skip to content</a>
  <div class="wrap nav">
    <a class="brand" href="/" aria-label="Red Herrings home">
      <img class="brandlogo" src="/img/brand/lockup.png" alt="Red Herrings" style="height:38px;width:auto;display:block" />
    </a>
    <nav class="mainnav" aria-label="Primary">
      <div class="mnitem haspanel"><button type="button" class="mntrig" aria-expanded="false">Platform <svg class="mncaret" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M2 3.5L5 6.5L8 3.5"/></svg></button><div class="megapanel"><div class="mpcols"><div class="mpcol"><div class="mphead">Product</div><a class="mlink" href="/how.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h18v14H3z"/><path d="M8 21h8M12 17v4"/></svg></span><span><span class="mt">How it works</span><span class="md">One case, a different variant for everyone</span></span></a><a class="mlink" href="/cases.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16v12H4z"/><path d="M9 7V5h6v2"/></svg></span><span><span class="mt">Case library</span><span class="md">Dozens of verified forensics and IR cases</span></span></a><a class="mlink" href="/packs.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7h14l-1 13H6zM9 7a3 3 0 0 1 6 0"/></svg></span><span><span class="mt">Scenario packs</span><span class="md">Add-on case sets, one-click install</span></span></a></div><div class="mpcol"><div class="mphead">Teaching</div><a class="mlink" href="/pathways.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 20V9a3 3 0 0 1 3-3h8M16 3l4 3-4 3"/></svg></span><span><span class="mt">Learning pathways</span><span class="md">From First Look to cert-prep capstone</span></span></a><a class="mlink" href="/courses.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">Course packs</span><span class="md">A 14-week DF and an 8-week IR syllabus, ready to run</span></span></a><a class="mlink" href="/student-portal.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v12H4zM2 21h20"/></svg></span><span><span class="mt">Student portal &amp; LMS</span><span class="md">Solve in the browser, auto-grade, LTI passback</span></span></a></div></div><a class="mppromo" href="/try.html"><span class="eye">Try it live</span><strong>Work two cases in your browser</strong><span class="pd">An EDR alert and a USB registry key. Press a button to see a different variant. Nothing to install.</span><span class="pc"><span>EDR alert</span><span>USB registry</span></span><span class="go">Open the demo &rarr;</span></a></div></div><div class="mnitem haspanel"><button type="button" class="mntrig" aria-expanded="false">Solutions <svg class="mncaret" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M2 3.5L5 6.5L8 3.5"/></svg></button><div class="megapanel nopromo"><div class="mpcols"><div class="mpcol"><div class="mphead">Who it's for</div><a class="mlink" href="/#pricing"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">Educators</span><span class="md">One instructor, auto-graded labs</span></span></a><a class="mlink" href="/#pricing"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">Departments</span><span class="md">Several instructors, every case</span></span></a><a class="mlink" href="/programs.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">College and university programs</span><span class="md">Labs, syllabi and procurement for departments</span></span></a><a class="mlink" href="/#pricing"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v12H4zM2 21h20"/></svg></span><span><span class="mt">Students</span><span class="md">Self-practice at the personal rate</span></span></a></div><div class="mpcol"><div class="mphead">Organizations</div><a class="mlink" href="/security-teams.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0M17 11a3 3 0 0 0 0-6M21 20a6 6 0 0 0-5-5.9"/></svg></span><span><span class="mt">Security teams &amp; training</span><span class="md">45-minute incident drills, per seat</span></span></a><a class="mlink" href="/contact.html?topic=enterprise"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7h14l-1 13H6zM9 7a3 3 0 0 1 6 0"/></svg></span><span><span class="mt">Enterprise &amp; government</span><span class="md">White-label, volume, procurement</span></span></a></div></div></div></div><div class="mnitem haspanel"><button type="button" class="mntrig" aria-expanded="false">Resources <svg class="mncaret" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M2 3.5L5 6.5L8 3.5"/></svg></button><div class="megapanel nopromo"><div class="mpcols"><div class="mpcol"><div class="mphead">Learn</div><a class="mlink" href="/help.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-1 .5-1 1.2-1 2M12 17h.01"/></svg></span><span><span class="mt">Getting started</span><span class="md">Install, activate and run your first lab</span></span></a><a class="mlink" href="/tools.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 7a4 4 0 0 1-5 5l-6 6 2 2 6-6a4 4 0 0 1 5-5z"/></svg></span><span><span class="mt">Tool setup</span><span class="md">Autopsy, Volatility, Wireshark and more</span></span></a><a class="mlink" href="/resources.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h10l4 4v14H5zM14 3v5h5"/></svg></span><span><span class="mt">Free resources</span><span class="md">Forms, checklists, rubrics and syllabi</span></span></a><a class="mlink" href="/blog/"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h10l4 4v14H5zM14 3v5h5"/></svg></span><span><span class="mt">Blog</span><span class="md">DFIR teaching notes and updates</span></span></a></div><div class="mpcol"><div class="mphead">Evaluate</div><a class="mlink" href="/sample.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="12" r="4"/><path d="M12 12h9l-2 2 2 2M11.5 12H21"/></svg></span><span><span class="mt">Sample lab</span><span class="md">A full case ZIP with its verified answer key</span></span></a><a class="mlink" href="/compare.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z"/></svg></span><span><span class="mt">Compare</span><span class="md">Hand-built labs, public images, ranges and us</span></span></a><a class="mlink" href="/attack.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z"/></svg></span><span><span class="mt">ATT&amp;CK coverage</span><span class="md">Which techniques the cases exercise</span></span></a><a class="mlink" href="/trust.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 3v6c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V6z"/></svg></span><span><span class="mt">Trust &amp; security</span><span class="md">Runs locally; no student data leaves</span></span></a><a class="mlink" href="/#faq"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-1 .5-1 1.2-1 2M12 17h.01"/></svg></span><span><span class="mt">FAQ</span><span class="md">Licensing, platforms, classroom use</span></span></a></div></div></div></div>
      <a class="mnitem mnflat" href="/#pricing">Pricing</a>
    </nav>
    <div class="spacer"></div>
    <a class="link navutil" href="https://account.redherrings.app/account" data-goatcounter-click="signin">Sign in</a>
    <a class="btn navcta" href="/download.html" data-goatcounter-click="cta-trial-nav">Start free</a>
    <button type="button" class="navburger" aria-label="Open menu" aria-expanded="false" aria-controls="mobilenav"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button>
  </div>
  <div class="mobilenav" id="mobilenav" hidden>
    <a class="btn" href="/download.html" data-goatcounter-click="cta-trial-nav" style="display:flex;justify-content:center;margin-bottom:6px">Start free</a>
    <div class="mnsection"><div class="mnsh">Platform</div><a class="mlink" href="/how.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h18v14H3z"/><path d="M8 21h8M12 17v4"/></svg></span><span><span class="mt">How it works</span><span class="md">One case, a different variant for everyone</span></span></a><a class="mlink" href="/cases.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16v12H4z"/><path d="M9 7V5h6v2"/></svg></span><span><span class="mt">Case library</span><span class="md">Dozens of verified forensics and IR cases</span></span></a><a class="mlink" href="/packs.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7h14l-1 13H6zM9 7a3 3 0 0 1 6 0"/></svg></span><span><span class="mt">Scenario packs</span><span class="md">Add-on case sets, one-click install</span></span></a><a class="mlink" href="/pathways.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 20V9a3 3 0 0 1 3-3h8M16 3l4 3-4 3"/></svg></span><span><span class="mt">Learning pathways</span><span class="md">From First Look to cert-prep capstone</span></span></a><a class="mlink" href="/courses.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">Course packs</span><span class="md">A 14-week DF and an 8-week IR syllabus, ready to run</span></span></a><a class="mlink" href="/student-portal.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v12H4zM2 21h20"/></svg></span><span><span class="mt">Student portal &amp; LMS</span><span class="md">Solve in the browser, auto-grade, LTI passback</span></span></a></div><div class="mnsection"><div class="mnsh">Solutions</div><a class="mlink" href="/#pricing"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">Educators</span><span class="md">One instructor, auto-graded labs</span></span></a><a class="mlink" href="/#pricing"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">Departments</span><span class="md">Several instructors, every case</span></span></a><a class="mlink" href="/programs.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">College and university programs</span><span class="md">Labs, syllabi and procurement for departments</span></span></a><a class="mlink" href="/#pricing"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v12H4zM2 21h20"/></svg></span><span><span class="mt">Students</span><span class="md">Self-practice at the personal rate</span></span></a><a class="mlink" href="/security-teams.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0M17 11a3 3 0 0 0 0-6M21 20a6 6 0 0 0-5-5.9"/></svg></span><span><span class="mt">Security teams &amp; training</span><span class="md">45-minute incident drills, per seat</span></span></a><a class="mlink" href="/contact.html?topic=enterprise"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7h14l-1 13H6zM9 7a3 3 0 0 1 6 0"/></svg></span><span><span class="mt">Enterprise &amp; government</span><span class="md">White-label, volume, procurement</span></span></a></div><div class="mnsection"><div class="mnsh">Resources</div><a class="mlink" href="/help.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-1 .5-1 1.2-1 2M12 17h.01"/></svg></span><span><span class="mt">Getting started</span><span class="md">Install, activate and run your first lab</span></span></a><a class="mlink" href="/tools.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 7a4 4 0 0 1-5 5l-6 6 2 2 6-6a4 4 0 0 1 5-5z"/></svg></span><span><span class="mt">Tool setup</span><span class="md">Autopsy, Volatility, Wireshark and more</span></span></a><a class="mlink" href="/resources.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h10l4 4v14H5zM14 3v5h5"/></svg></span><span><span class="mt">Free resources</span><span class="md">Forms, checklists, rubrics and syllabi</span></span></a><a class="mlink" href="/blog/"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h10l4 4v14H5zM14 3v5h5"/></svg></span><span><span class="mt">Blog</span><span class="md">DFIR teaching notes and updates</span></span></a><a class="mlink" href="/sample.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="12" r="4"/><path d="M12 12h9l-2 2 2 2M11.5 12H21"/></svg></span><span><span class="mt">Sample lab</span><span class="md">A full case ZIP with its verified answer key</span></span></a><a class="mlink" href="/compare.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z"/></svg></span><span><span class="mt">Compare</span><span class="md">Hand-built labs, public images, ranges and us</span></span></a><a class="mlink" href="/attack.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z"/></svg></span><span><span class="mt">ATT&amp;CK coverage</span><span class="md">Which techniques the cases exercise</span></span></a><a class="mlink" href="/trust.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 3v6c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V6z"/></svg></span><span><span class="mt">Trust &amp; security</span><span class="md">Runs locally; no student data leaves</span></span></a><a class="mlink" href="/#faq"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-1 .5-1 1.2-1 2M12 17h.01"/></svg></span><span><span class="mt">FAQ</span><span class="md">Licensing, platforms, classroom use</span></span></a></div>
    <div class="mnsection"><a class="mnflat mnsolo" href="/#pricing">Pricing</a></div>
    <div class="mnrow">
      <a class="btn ghost" href="https://account.redherrings.app/account" data-goatcounter-click="signin">Sign in</a>
      <a class="btn ghost" href="/student-portal.html">Student portal</a>
    </div>
  </div>
</header>
<main class="wrap" id="main">
  <div class="crumb" style="margin-bottom:10px"><a href="/">Home</a> / Pathways</div>
  <div class="secthead">
    <h1 class="opener">Learning pathways</h1>
    <p class="osub">Ordered, case-by-case curricula that take a learner from first-look triage to a capstone, across both disciplines, <strong>Digital Forensics</strong> and <strong>Incident Response</strong>. Follow a certification-prep path or a role. Every case still generates a unique, auto-graded lab for each student.</p>
  </div>
  <div class="pwfilter" role="group" aria-label="Filter pathways by discipline">
    <button type="button" class="pwtab on" data-disc="all">All pathways</button>
    <button type="button" class="pwtab" data-disc="digital-forensics">Digital Forensics</button>
    <button type="button" class="pwtab" data-disc="incident-response">Incident Response</button>
  </div>
{sections}
</main>
<footer>
  <div class="wrap">
    <div class="ftop">
      <div class="fbrand">
        <div class="brand"><a href="/" aria-label="Red Herrings home" style="display:inline-flex;align-items:center;gap:8px;text-decoration:none"><img src="/favicon.svg" alt="" width="22" height="22" style="display:block" /><span style="font-size:16px">Red Herrings</span></a></div>
        <p>Real Evidence. Real Skills. Real Fast.</p>
        <p class="fsmall">Runs locally on Windows, macOS and Linux. No student data ever leaves your machine.</p>
        <a class="fmail" href="/contact.html">Contact us</a> &middot; <span class="fsmall">sales@redherrings.app</span>
      </div>
      <div class="fcol">
        <h4>Product</h4>
        <a href="/how.html">How it works</a>
        <a href="/cases.html">All cases</a>
        <a href="/pathways.html">Learning pathways</a>
        <a href="/courses.html">Course packs</a>
        <a href="/programs.html">For college programs</a>
        <a href="/attack.html">MITRE ATT&amp;CK coverage</a>
        <a href="/student-portal.html">Student portal &amp; LMS</a>
        <a href="/packs.html">Scenario packs</a>
        <a href="/#pricing">Pricing</a>
      </div>
      <div class="fcol">
        <h4>Resources</h4>
        <a href="/help.html">Help &amp; getting started</a>
        <a href="/tools.html">Tools &amp; setup</a>
        <a href="/resources.html">Free resources</a>
        <a href="/press.html">Press kit</a>
        <a href="/blog/">Blog</a>
        <a href="/compare.html">Compare</a>
        <a href="/#faq">FAQ</a>
        <a href="/trust.html">Trust &amp; security</a>
        <a href="/verify.html">Verify a certificate</a>
        <a href="/download.html">Download</a>
        <a href="/contact.html">Contact</a>
      </div>
    </div>
    <div class="fbottom">
      <span>&copy; 2026 Red Herrings, a product of The Competence Collective, LLC. Prices in USD; institutional purchase orders welcome.</span>
      <nav class="flegal" aria-label="Legal">
        <a href="/privacy.html">Privacy</a>
        <a href="/terms.html">Terms</a>
        <a href="/eula.html">License agreement</a>
        <a href="/refund.html">Refund</a>
        <a href="/accessibility.html">Accessibility</a>
      </nav>
    </div>
  </div>
</footer>
<script>
(function(){{
  var tabs = Array.prototype.slice.call(document.querySelectorAll(".pwtab"));
  var secs = Array.prototype.slice.call(document.querySelectorAll(".pwdisc"));
  function pick(disc){{
    tabs.forEach(function(t){{ t.classList.toggle("on", t.getAttribute("data-disc")===disc); }});
    secs.forEach(function(s){{ s.classList.toggle("hide", disc!=="all" && s.getAttribute("data-disc")!==disc); }});
  }}
  tabs.forEach(function(t){{ t.addEventListener("click", function(){{ pick(t.getAttribute("data-disc")); }}); }});
}})();
</script>
<!-- Analytics: GoatCounter (cookieless, no personal data). Activate by registering the "redherrings" code at goatcounter.com. -->
<script data-goatcounter="https://redherrings.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<script src="nav.js" defer></script>
</body>
</html>
'''

# ---------------------------------------------------------------------------
# Per-pathway landing pages: pathways/<slug>.html
# ---------------------------------------------------------------------------
SITE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://redherrings.app"
# Case links use the public slug; the scenario id is internal.
SLUG = {r["id"]: r.get("slug") or r["id"] for r in packs.all_scenarios() if "id" in r}
OG_ALT = "Red Herrings: randomized digital forensics and incident-response labs for the classroom."
FAVICON = ("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 64 64%27%3E%3Cpath "
           "fill=%27%23E5382F%27 d=%27M6 32c9-11 20-16 30-16 4 0 8 3 12 9 3-3 8.5-9.5 14.25-13.25C58.38 18.12 55.69 "
           "25.81 54.44 32c1.25 6.19 3.94 13.87 7.81 20.25C56.5 48.5 51 42 48 39c-4 6-8 9-12 9-10 0-21-5-30-16z%27/%3E%3C/svg%3E")
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Public+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600;800&display=swap">')

TRACK_CHIP = {"foundations": ("trk-foundations", "Foundations"),
              "windows-forensics": ("trk-windows", "Windows Forensics"),
              "mobile-forensics": ("trk-mobile", "Mobile Forensics"),
              "network-forensics": ("trk-network", "Network Forensics"),
              "cloud": ("trk-cloud", "Cloud & SaaS"),
              "linux": ("trk-linux", "Linux Forensics"),
              "macos": ("trk-macos", "macOS Forensics"),
              "advanced-ir": ("trk-advanced", "Advanced Forensics & IR")}
DISC_LABEL = {d["id"]: d["label"] for d in DISC}

ATTACK_NOTE = ("ATT&amp;CK&reg; and MITRE ATT&amp;CK&reg; are registered trademarks of The MITRE Corporation. "
               "Red Herrings maps to published ATT&amp;CK tactics and techniques for teaching; it isn't affiliated "
               "with or endorsed by MITRE.")
CERT_NOTE = ("GIAC, GCFE, GASF, GNFA, GCIH, GCFR and GCFA are trademarks of GIAC. CompTIA and CySA+ are trademarks of "
             "CompTIA, Inc. SANS is a trademark of the SANS Institute. Red Herrings aligns its pathways to the published "
             "objectives of these programs for teaching; it's independent of, and not affiliated with or endorsed by, "
             "any certification body.")

# Search-intent copy per pathway. Everything else on the page is derived from the live data.
#   title: <title> (without the " | Red Herrings" suffix), h1: (plain, emphasized) halves,
#   desc: 150-160 char meta description, expects: what the cert/role asks for,
#   builds: how the ordered steps get there, who: audience bullets, chips: extra coverage chips.
COPY = {
    "gcfe-windows": {
        "title": "GCFE Windows Forensics Practice Labs",
        "h1": ("GCFE practice labs,", "one case at a time"),
        "desc": "Windows forensics labs aligned to the GCFE objectives: registry, Prefetch, USB, jump lists, browser and event logs, from five First Looks to an expert capstone.",
        "expects": "The GCFE objectives expect an examiner who can read Windows artifacts without a cheat sheet: program execution from Prefetch, UserAssist and Amcache; file knowledge from LNK files and jump lists; USB device history from the registry; persistence in Run keys, services and scheduled tasks; browser activity; and the Security event log, all pulled together into one defensible timeline.",
        "builds": "This pathway builds those skills in that order, all but Amcache and scheduled tasks, which its evidence doesn't include. Five First Look cases isolate one artifact family each, two medium cases apply them to a departing engineer's workstation and a customer export, two hard cases add a mailbox, memory and a packet capture, and the capstone rebuilds a quiet intrusion from disk, memory and cloud logs. Each case generates a different variant per student, so the practice is on reading evidence, not memorizing answers.",
        "who": [
            ("Candidates preparing for the GCFE", "who want hands-on reps against real registry hives, event logs and link files rather than another question bank."),
            ("Instructors running a Windows forensics unit", "who need labs that drop into a 14-week course and grade themselves across sections."),
            ("Analysts moving from triage into disk forensics", "who already know what Prefetch is and need to prove they can use it under time."),
        ],
    },
    "gasf-mobile": {
        "title": "GASF Mobile Forensics Practice Labs",
        "h1": ("GASF practice labs,", "one extraction at a time"),
        "desc": "Mobile forensics labs aligned to the GASF objectives: SMS, call logs, app databases, deleted SQLite records and location artifacts, to a multi-source capstone.",
        "expects": "The GASF objectives expect an examiner who can take a mobile extraction and recover what matters: messages, contacts and call logs; third-party app data in SQLite; deleted records still sitting in freelists and write-ahead logs; and the location and activity artifacts that place a device at a time and a place.",
        "builds": "This pathway starts with a single recovered phone and adds one skill per case: third-party app databases, tying messages to a complaint, deleted-record recovery, location artifacts, call detail records and an investment-fraud case that needs several of them. The capstone puts the phone evidence beside a workstation, a mailbox and cloud logs, so the final step is correlation across sources rather than one more parser.",
        "who": [
            ("Candidates preparing for the GASF", "who want to work real SQLite databases and extraction layouts, not screenshots of a commercial tool."),
            ("Instructors teaching a mobile forensics module", "who need graded, per-student labs that open in free tools."),
            ("Investigators who inherit phones", "and need a structured route from the first message to a report."),
        ],
    },
    "gnfa-network": {
        "title": "GNFA Network Forensics Practice Labs",
        "h1": ("GNFA practice labs,", "one capture at a time"),
        "desc": "Network forensics labs aligned to the GNFA objectives: packet captures, DNS, HTTP, scheduled outbound traffic and host correlation, through a breach capstone.",
        "expects": "The GNFA objectives expect an analyst who can open a packet capture and tell the story in it: follow streams, read protocols in the clear, find data leaving over HTTP, spot a beacon by its timing, recover cleartext credentials, and connect network evidence to what the hosts recorded.",
        "builds": "This pathway opens with a single capture and a few protocols. It then measures traffic in a capture and ties it to host artifacts, ties a remote-access login to scheduled outbound traffic, follows a host from an opened document to its outbound traffic, and follows a download from the browser into the network and memory. The capstone is a multi-department breach where the network evidence has to be reconciled with host and mobile artifacts.",
        "who": [
            ("Candidates preparing for the GNFA", "who want to work captures in Wireshark, Zeek or tshark with a verified answer to check against."),
            ("Instructors teaching network forensics", "who need captures that differ per student but grade to the same rubric."),
            ("SOC analysts moving into packet analysis", "who can read an alert and want to prove the traffic behind it."),
        ],
    },
    "linux-forensics": {
        "title": "Linux Forensics Practice Labs",
        "h1": ("Linux forensics labs,", "one case at a time"),
        "desc": "Linux forensics labs aligned to the FOR577 objectives: auth.log, a LiME memory image, a persistence sweep, a web-server intrusion and a five-artifact capstone.",
        "expects": "Linux incident response, as the FOR577 objectives frame it, expects an examiner who can work a server from what it recorded: read auth.log for failed and successful logins, read a memory image for what was running, find every place a Linux host can hide persistence, follow a web request from the access log into the shell history, and correlate one intrusion across every log on the box.",
        "builds": "This pathway is short and steep. It starts with a single auth.log and a First Look at a LiME memory image, sweeps a server for every way back in, reads access, auth and shell logs on a web-server intrusion from first request to last, and finishes with an expert capstone that correlates five host artifacts into one timeline.",
        "who": [
            ("Candidates preparing for a Linux forensics course or exam", "who want log-based reps that open in a terminal with grep and awk."),
            ("Instructors who need a Linux unit in a Windows-heavy course", "and want five graded labs that fit in two weeks."),
            ("Sysadmins and SREs moving into security", "who know the files and need practice reading them as evidence."),
        ],
    },
    "macos-forensics": {
        "title": "macOS Forensics Practice Labs",
        "h1": ("macOS forensics labs,", "one case at a time"),
        "desc": "macOS forensics labs aligned to the FOR518 objectives: the quarantine database, Safari history, TCC consent, persistence and a departing employee's Mac.",
        "expects": "Mac forensics, as the FOR518 objectives frame it, expects an examiner who knows where macOS keeps its own records: download provenance in the quarantine database and Safari history, privacy consent in the TCC database, persistence in LaunchAgents and LaunchDaemons, and the unified log entries that tie them together.",
        "builds": "This pathway starts with two First Look cases, one on where an app came from and one on what each app is allowed to see. It then traces persistence back to its download, correlates TCC, quarantine and unified-log records on a Mac whose user suspects monitoring, works a departing employee's Mac, and closes with a capstone that puts five macOS artifacts on one timeline.",
        "who": [
            ("Candidates preparing for a macOS forensics course or exam", "who want to work real plists, SQLite databases and log output rather than slides."),
            ("Instructors adding Apple endpoints to a forensics course", "who need graded labs that don't require a Mac to solve."),
            ("Enterprise responders with a Mac fleet", "who have never had to read a TCC database under pressure."),
        ],
    },
    "analyst-onboarding": {
        "title": "SOC Analyst Onboarding Labs",
        "h1": ("SOC analyst onboarding labs,", "one evidence family at a time"),
        "desc": "Onboarding labs for new SOC and DFIR analysts: execution, downloads, event logs, persistence, USB, packets, memory, mobile and a timeline, then a full case.",
        "expects": "A new analyst is expected to recognize every evidence family a ticket can throw at them: what ran on a host, where a file came from, what the Security log says about accounts and services, what's set to run at startup, which USB device was plugged in, what a packet capture shows, what's in memory, and what a phone holds, then to put several of those into a single timeline.",
        "builds": "This pathway is the first-look tour in the order a new hire should meet it. Nine First Look cases of about 35 minutes each isolate one artifact family, and the tenth is a full, if gentle, misconduct case that asks the analyst to use several of them together. It's the week-one curriculum we'd hand a new SOC or DFIR analyst.",
        "who": [
            ("Security teams onboarding new analysts", "who want a graded, repeatable first week instead of shadowing."),
            ("Instructors opening a DFIR course", "who need a survey of evidence types before the deeper units."),
            ("Career changers and students", "who want to find out which part of DFIR they like before specializing."),
        ],
    },
    "insider-threat": {
        "title": "Insider Threat Investigation Practice Labs",
        "h1": ("Insider threat investigation labs,", "one case at a time"),
        "desc": "Insider threat investigation labs: a records-access complaint, a departing engineer's USB use, a pricing leak, a DLP alert, a customer export and a capstone.",
        "expects": "Insider investigations ask different questions from intrusion cases. The suspect already had access, so the examiner has to prove intent and movement: which records were opened and when, what left on a USB drive, what was texted or pasted somewhere it shouldn't have been, what was exported and where it went, and who else was involved.",
        "builds": "This pathway runs through the common insider patterns one at a time, each as a complete case with a report to write: a records-access complaint, a departing engineer's workstation, a pricing leak on a phone, a DLP alert on an AI assistant and a customer export. The capstone follows one suspect across five evidence sources and asks for the full story, not one artifact.",
        "who": [
            ("Corporate investigators and HR-adjacent security staff", "who handle policy violations and need defensible, repeatable findings."),
            ("Instructors teaching an insider-threat or ethics unit", "who want realistic cases without a nation-state actor."),
            ("Candidates preparing for employment-law or e-discovery work", "who need practice with the evidence before the deposition."),
        ],
    },
    "gcih-incident-handling": {
        "title": "GCIH Incident Handling Practice Labs",
        "h1": ("GCIH practice labs,", "one incident at a time"),
        "desc": "Incident handling labs aligned to the GCIH objectives: EDR and SIEM triage, phishing, a web-facing server, lateral movement and ransomware, mapped to ATT&CK.",
        "expects": "The GCIH objectives expect a handler who can run an incident through its phases: triage a detection and decide what it means, trace the initial access, follow the move from a beachhead to the next host, catch an operator's setup before the payload, contain a live outbreak, and write up the lessons learned, with each behavior named by its ATT&CK technique.",
        "builds": "This pathway follows the incident-handling kill chain from the responder's own tooling. It opens with an EDR detection and a SIEM queue, then works a phish, an internet-facing server, a remote session and a server caught before impact as full cases, and closes the hard tier with a live outbreak and a timed ransomware drill. The capstone runs a hospital-wide incident through every NIST phase.",
        "who": [
            ("Candidates preparing for the GCIH", "who want to work real EDR and SIEM exports, not multiple-choice scenarios."),
            ("Instructors running an incident response course", "who need the 8-week IR course pack with labs that grade across sections."),
            ("Security teams drilling their on-call rotation", "who want a 45-minute ransomware exercise with a verified key."),
        ],
    },
    "cysa-soc-analyst": {
        "title": "CySA+ SOC Analyst Practice Labs",
        "h1": ("CySA+ practice labs,", "one alert at a time"),
        "desc": "SOC analyst labs aligned to the CySA+ objectives: SIEM and EDR triage, impossible travel, phishing, account takeover, BEC, lateral movement and detection rules.",
        "expects": "The CySA+ objectives expect an analyst who can work the daily queue: read a SIEM alert and an EDR detection, recognize an impossible-travel sign-in, triage a phishing report, correlate entities across host and log evidence, turn a confirmed behavior into a detection rule, and escalate a real incident with a severity verdict that holds up.",
        "builds": "This pathway is the SOC queue in order. Four First Look cases cover the alert types an analyst sees most. Medium cases work an EDR detection to a verdict, an off-hours sign-in, a misdirected wire, a timed insider drill and a lateral move. The hard steps correlate a handset, an inbox and exchange logs on an account loss, then turn the lateral move into a detection rule. The capstone scopes a weekend of alerts end to end.",
        "who": [
            ("Candidates preparing for the CySA+", "who want graded practice on the analysis domain with real alert exports."),
            ("Instructors teaching a SOC analyst or security operations course", "who need labs that fit a 50-minute class and grade themselves."),
            ("Tier 1 analysts working toward tier 2", "who want to prove they can correlate alerts, not only acknowledge them."),
        ],
    },
    "gcfr-cloud": {
        "title": "GCFR Cloud and Enterprise IR Practice Labs",
        "h1": ("GCFR practice labs,", "one tenant at a time"),
        "desc": "Cloud IR labs aligned to the GCFR objectives: sign-in logs, Microsoft 365 audit logs, GCP and Kubernetes audit logs, CloudTrail and an exchange capstone.",
        "expects": "The GCFR objectives expect a responder who can investigate identity and cloud audit logs without a disk image: anomalous sign-ins, MFA-fatigue takeovers, hidden mailbox rules and role abuse in Microsoft 365, leaked service-account keys and tokens across a project, and data pulled from the cloud by an account that shouldn't have had it.",
        "builds": "This pathway starts with a single cloud sign-in log and adds one identity or platform at a time: an off-hours login, mailbox changes in the Microsoft 365 Unified Audit Log, a Microsoft 365 account takeover, GCP Cloud Audit Logs after a key exposure, a rogue pod in Kubernetes, a departing employee's export and CloudTrail after an access-key exposure. The Marquee capstone runs a digital-asset exchange incident across mail, single sign-on, EDR and monitoring.",
        "who": [
            ("Candidates preparing for the GCFR", "who want to work real audit-log exports in JSON and CSV, not console screenshots."),
            ("Instructors adding cloud to an IR course", "who need labs that need no cloud account to solve."),
            ("Enterprise responders whose incidents now start in the identity provider", "and who want structured practice before the next one."),
        ],
    },
    "gcfa-advanced-ir": {
        "title": "GCFA Advanced Forensics and IR Practice Labs",
        "h1": ("GCFA practice labs,", "one intrusion at a time"),
        "desc": "Advanced forensics and IR labs aligned to the GCFA objectives: memory triage, injected code, a rogue admin, credential theft and a ransomware capstone.",
        "expects": "The GCFA objectives expect an examiner who can take a compromised host apart: baseline processes and connections in memory, find injected code and unlinked modules, trace a rogue admin across host artifacts, recognize an attacker's setup work before a payload, follow credential theft to lateral movement, and build the full intrusion timeline.",
        "builds": "This pathway is the host-based capstone track. It starts with memory because every later case depends on it, moves through a rogue admin account and injected code in memory, then works a server caught before impact, a service account followed across hosts and an encrypted file server. The capstone, Operation Ledger, is a complete ransomware intrusion that asks for the whole timeline with every technique named.",
        "who": [
            ("Candidates preparing for the GCFA", "who want full intrusions to take apart with Volatility, timeline tools and the event logs."),
            ("Instructors teaching an advanced forensics or IR capstone", "who need multi-hour cases that still grade themselves."),
            ("Experienced responders", "who want hard practice with a verified key to check their work against."),
        ],
    },
    "ransomware-ir": {
        "title": "Ransomware Incident Response Practice Labs",
        "h1": ("Ransomware incident response labs,", "the kill chain in order"),
        "desc": "Ransomware incident response labs in kill-chain order: initial access, a server caught mid-setup, a live outbreak in the EDR feed, a ransom note and a capstone.",
        "expects": "Ransomware response expects a team that can place itself on the kill chain at any moment: recognize the phish and the command-and-control that followed, spot the setup work before encryption, work a fast-moving outbreak live from the EDR feed, and handle the data-theft side of a double-extortion demand alongside recovery.",
        "builds": "This pathway is the ransomware arc end to end. Patient Zero covers initial access, Dry Run covers what an operator sets up before the payload, First Call is the live outbreak, Double Cross tests a ransom note's claims against the evidence, and Nightfall is the complete incident worked start to finish. All five are hard or expert; this is the path for a team that already knows the basics.",
        "who": [
            ("Security teams and on-call rotations", "who want a structured ransomware drill series with verified answer keys."),
            ("Instructors teaching the capstone weeks of an IR course", "who want one coherent arc instead of unrelated cases."),
            ("Responders preparing for tabletop or live exercises", "who want hands-on reps against the EDR, SIEM and host evidence."),
        ],
    },
}


def _load_tool(name):
    """Import a sibling tools-*.py so header/footer stay byte-identical with the site."""
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), os.path.join(SITE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    was = sys.dont_write_bytecode
    sys.dont_write_bytecode = True  # keep __pycache__ out of the site repo
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = was
    return mod


def fmt_minutes(m):
    if not m:
        return ""
    if m >= 60:
        h, r = divmod(m, 60)
        return f"~{h} h" if not r else f"~{h} h {r} min"
    return f"~{m} min"


def iso_duration(minutes):
    h, m = divmod(int(minutes or 0), 60)
    return "PT" + (f"{h}H" if h else "") + (f"{m}M" if m or not h else "")


def page_step_html(i, s):
    name = s.get("codename") or s.get("name") or s["id"]
    full = s.get("name") or ""
    sub = f' <span style="color:var(--faint);font-weight:500">({E(full)})</span>' if s.get("codename") and full and full != name else ""
    diff = s.get("difficulty") or "medium"
    tag = DIFF_TAG.get(diff, "medium")
    meta = [f'<span class="tag {tag}">{E(diff.replace("-", " ").upper())}</span>']
    if s.get("minutes"):
        meta.append(f'<span>{E(fmt_minutes(s["minutes"]))}</span>')
    if s.get("questions"):
        meta.append(f'<span>{E(up_to_questions(s["questions"]))}</span>')
    return (f'      <li class="rowitem">\n'
            f'        <div class="n">{i:02d}</div>\n'
            f'        <h3><a href="/cases.html#{E(SLUG.get(s["id"], s["id"]))}">{E(name)}</a>{sub}</h3>\n'
            f'        <div class="body"><p style="margin:0 0 10px">{E(s["note"])}</p>'
            f'<div class="chips" style="align-items:center;gap:10px;font-size:13px;color:var(--faint)">{"".join(meta)}</div></div>\n'
            f'      </li>')


def chips_html(p):
    seen, out = [], []
    for s in p["steps"]:
        for t in s.get("tracks") or []:
            if t not in seen:
                seen.append(t)
    for t in seen:
        cls, label = TRACK_CHIP.get(t, ("", t))
        out.append(f'<span class="chip {cls}">{E(label)}</span>')
    if p.get("discipline") == "incident-response":
        out.append('<span class="chip trk-ir">MITRE ATT&amp;CK mapped</span>')
    if p.get("aligned"):
        out.append(f'<span class="chip">Aligned to the published {E(p["aligned"])} objectives</span>')
    diffs = []
    for s in p["steps"]:
        d = s.get("difficulty") or "medium"
        if d not in diffs:
            diffs.append(d)
    out.append(f'<span class="chip">{E(" to ".join([diffs[0].replace("-", " ").title(), diffs[-1].replace("-", " ").title()]) if len(diffs) > 1 else diffs[0].title())}</span>')
    return "".join(out)


def related_html(p, cat):
    same = [q for q in cat if q.get("discipline") == p.get("discipline") and q["slug"] != p["slug"]]
    idx = [q["slug"] for q in cat if q.get("discipline") == p.get("discipline")].index(p["slug"])
    # the two that follow this one in the catalog order, wrapping
    picks = [same[(idx + k) % len(same)] for k in range(2)] if len(same) >= 2 else same
    cards = []
    for q in picks:
        meta = f'{q["count"]} cases &middot; {fmt_minutes(q.get("total_minutes"))}'
        al = f' &middot; {E(q["aligned"])}' if q.get("aligned") else ""
        cards.append(f'      <a class="card" href="/pathways/{q["slug"]}.html"><h3>{E(q["label"])}</h3>'
                     f'<p>{E(q["blurb"])}</p><p style="margin-top:12px;font-family:var(--mono);font-size:12px;color:var(--faint)">{meta}{al}</p></a>')
    cards.append('      <a class="card" href="/pathways.html"><h3>All learning pathways</h3>'
                 '<p>Every certification-prep and role pathway across Digital Forensics and Incident Response, side by side.</p>'
                 '<p style="margin-top:12px;font-weight:600;color:var(--accent)">Browse the overview &rarr;</p></a>')
    return "\n".join(cards)


def jsonld(p, c, url, desc):
    teaches = [s["note"] for s in p["steps"]]
    level = "Beginner to advanced" if any((s.get("difficulty") or "") in ("easy", "first-look") for s in p["steps"]) else "Intermediate to advanced"
    crumbs = {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Pathways", "item": BASE + "/pathways.html"},
        {"@type": "ListItem", "position": 3, "name": p["label"], "item": url}]}
    course = {"@type": "Course", "@id": url + "#course", "name": c["title"], "url": url, "description": desc,
              "provider": {"@type": "Organization", "name": "Red Herrings", "url": BASE + "/"},
              "educationalLevel": level, "teaches": teaches,
              "about": [TRACK_CHIP.get(t, ("", t))[1] for t in sorted({t for s in p["steps"] for t in (s.get("tracks") or [])})],
              "numberOfCredits": None, "isAccessibleForFree": False,
              "timeRequired": iso_duration(p.get("total_minutes")),
              "hasCourseInstance": {"@type": "CourseInstance", "courseMode": ["online", "self-paced"],
                                    "courseWorkload": iso_duration(p.get("total_minutes"))},
              "offers": {"@type": "Offer", "category": "Paid", "url": BASE + "/#pricing", "availability": "https://schema.org/InStock"}}
    course = {k: v for k, v in course.items() if v is not None}
    if p.get("aligned"):
        course["educationalAlignment"] = {"@type": "AlignmentObject", "alignmentType": "teaches",
                                          "educationalFramework": p["aligned"] + " published objectives",
                                          "targetName": p["aligned"]}
    doc = {"@context": "https://schema.org", "@graph": [crumbs, course]}
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":"))


def page_html(p, cat, header, footer):
    c = COPY[p["slug"]]
    url = f"{BASE}/pathways/{p['slug']}.html"
    desc = c["desc"]
    assert 150 <= len(desc) <= 160, (p["slug"], len(desc))
    disc = DISC_LABEL.get(p.get("discipline", "digital-forensics"), "Digital Forensics")
    kind = KIND_LABEL[p["kind"]]
    aligned = f' &middot; aligned to the published {E(p["aligned"])} objectives' if p.get("aligned") else ""
    steps = "\n".join(page_step_html(i + 1, s) for i, s in enumerate(p["steps"]))
    who = "\n".join(f'          <li><strong>{E(a)}</strong> {E(b)}</li>' for a, b in c["who"])
    total = fmt_minutes(p.get("total_minutes"))
    diffs = [s.get("difficulty") or "medium" for s in p["steps"]]
    proof = (f'{p["count"]} cases &middot; {total} of lab time &middot; '
             f'{diffs[0].replace("-", " ").title()} to {diffs[-1].replace("-", " ").title()} &middot; '
             f'a different variant for everyone &middot; verified answer keys')
    notes = ATTACK_NOTE + " " if p.get("discipline") == "incident-response" or "ATT&CK" in p["blurb"] else ""
    h1a, h1b = c["h1"]
    og_title = f'{c["title"]} | Red Herrings'
    return PAGE_TEMPLATE.format(
        title=E(c["title"]), desc=E(desc), url=url, og_title=og_title, og_alt=E(OG_ALT), favicon=FAVICON, fonts=FONTS,
        jsonld=jsonld(p, c, url, desc), header=header, footer=footer,
        label=E(p["label"]), kind=E(kind), disc=E(disc), aligned=aligned, h1a=E(h1a), h1b=E(h1b),
        lede=E(c["expects"]), builds=E(c["builds"]), proof=proof, slug=p["slug"], total_plain=total.lstrip("~"),
        steps=steps, chips=chips_html(p), who=who, related=related_html(p, cat), notes=notes, cert_note=CERT_NOTE,
        n=p["count"], total=total)


def write_pages(cat):
    header = _load_tool("tools-apply-nav").HEADER
    footer = _load_tool("tools-apply-footer").FOOTER
    outdir = os.path.join(SITE, "pathways")
    os.makedirs(outdir, exist_ok=True)
    for p in cat:
        if p["slug"] not in COPY:
            print(f"  ! no COPY entry for pathway {p['slug']}; skipped", file=sys.stderr)
            continue
        out = os.path.join(outdir, p["slug"] + ".html")
        with open(out, "w") as f:
            f.write(page_html(p, cat, header, footer))
        print(f"wrote pathways/{p['slug']}.html")


PAGE_TEMPLATE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | Red Herrings</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow">
<meta name="theme-color" content="#D42A2A">
<link rel="icon" href="{favicon}">
<link rel="icon" type="image/png" sizes="32x32" href="/img/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/img/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Red Herrings">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://redherrings.app/img/og/home-f129ee30.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{og_alt}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{og_title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="https://redherrings.app/img/og/home-f129ee30.png">
<meta name="twitter:image:alt" content="{og_alt}">
{fonts}
<link rel="stylesheet" href="/site.css">
<script type="application/ld+json">
{jsonld}
</script>
</head>
<body>
{header}
<main class="wrap" id="main">
  <section class="hero" style="border-top:0;text-align:left;padding-top:40px;padding-bottom:40px">
    <div class="crumb" style="margin-bottom:14px"><a href="/">Home</a> / <a href="/pathways.html">Pathways</a> / {label}</div>
    <span class="kicker">{kind} &middot; {disc}{aligned}</span>
    <h1 style="max-width:18ch">{h1a} {h1b}</h1>
    <p class="lede" style="margin-left:0">{lede}</p>
    <p class="lede" style="margin-left:0;font-size:17px">{builds}</p>
    <div class="cta-row hero-cta" style="justify-content:flex-start;margin-top:26px">
      <a class="btn" href="/download.html" data-goatcounter-click="cta-trial-pathway-{slug}">Start a free 30-day trial<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
      <a class="btn ghost" href="/sample.html">Download the sample lab</a>
    </div>
    <p class="hero-proof">{proof}</p>
  </section>

  <section>
    <div class="secthead">
      <h2 class="opener">The pathway, in order</h2>
      <p class="osub">{n} cases, about {total_plain} of lab time. Each step opens the case in the library, where you can read the brief, the evidence list and sample questions. Everyone gets a different variant of the same case, graded against a key that was verified in the evidence.</p>
    </div>
    <ol class="rows-list" style="list-style:none;margin:0;padding:0">
{steps}
    </ol>
  </section>

  <section>
    <div class="secthead solo" style="margin-bottom:18px">
      <h2 class="opener" style="font-size:clamp(24px,3vw,34px)">What this pathway covers</h2>
    </div>
    <div class="chips" style="gap:8px">{chips}</div>
  </section>

  <section>
    <div class="bigcards">
      <div class="bigcard">
        <div class="fh"><h3>Who it's for</h3></div>
        <ul>
{who}
        </ul>
      </div>
      <div class="bigcard">
        <div class="fh"><h3>What you get with every case</h3></div>
        <ul>
          <li><strong>A different variant per student.</strong> Same case, same rubric, different names, hashes, timestamps and answers, so students can talk about method without sharing answers.</li>
          <li><strong>Evidence in the real on-disk format.</strong> Registry hives, EVTX, PCAP, SQLite, JSON audit logs and memory images open in the tools the exam expects.</li>
          <li><strong>A verified answer key.</strong> Every answer is re-derived from the planted evidence before the lab ships, so grading disputes end at the artifact.</li>
          <li><strong>One-click grading and LMS export.</strong> Canvas, Blackboard, Moodle, D2L and LTI 1.3 grade passback, or a CSV. See the <a href="/student-portal.html">student portal</a>.</li>
          <li><strong>Runs on the instructor's machine.</strong> Windows installer plus macOS and Linux, fully offline after activation. Nothing to host and no student data leaves the room. Course packs on <a href="/courses.html">courses</a>.</li>
        </ul>
      </div>
    </div>
  </section>

  <section class="cta-band">
    <h2>Run this pathway with your own roster</h2>
    <p class="sub">Download the app, generate a three-student version of the first case in under five minutes, and grade it. First Look cases run free with no key, and the 30-day trial needs no card. Or open the sample lab first and work a student package in your own tools.</p>
    <div class="cta-row" style="justify-content:center;margin-top:22px">
      <a class="btn" href="/download.html" data-goatcounter-click="cta-trial-pathway-{slug}-bottom">Start a free 30-day trial</a>
      <a class="btn ghost" href="/sample.html">Open the sample lab</a>
    </div>
  </section>

  <section>
    <div class="secthead solo" style="margin-bottom:22px">
      <h2 class="opener" style="font-size:clamp(24px,3vw,34px)">Related pathways</h2>
    </div>
    <div class="grid">
{related}
    </div>
    <p class="note" style="margin-top:28px">{notes}{cert_note}</p>
  </section>
</main>
{footer}
<script data-goatcounter="https://redherrings.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<script src="/nav.js" defer></script>
</body>
</html>
'''

if __name__ == "__main__":
    main()
