#!/usr/bin/env python3
"""Generate redherrings-site/pathways.html from the live engine pathway data.

Groups the ordered learning pathways by discipline (Digital Forensics |
Incident Response), each with a Certification-prep and a By-role sub-section,
behind an All / DF / IR filter. Keeps the site in sync with the real
pathways.py so cert alignment and step lists never drift.
"""
import html
import sys

sys.path.insert(0, "/home/user/redherrings")
from redherrings import packs, pathways  # noqa: E402

E = lambda s: html.escape(str(s or ""), quote=True)

DISC = [
    {"id": "digital-forensics", "label": "Digital Forensics",
     "sub": "Disk, registry, logs, memory, network, mobile and cloud, mapped to certification tracks."},
    {"id": "incident-response", "label": "Incident Response",
     "sub": "Detection and response from the responder's own tooling - EDR, SIEM and host logs - mapped to MITRE ATT&CK."},
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
      <a class="btn ghost pwc-cta" href="cases.html">Browse the cases &rarr;</a>
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
    out = "/home/user/redherrings-site/pathways.html"
    with open(out, "w") as f:
        f.write(html_doc)
    print(f"wrote {out}: {len(cat)} pathways ({n_df} DF, {n_ir} IR)")


TEMPLATE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Learning Pathways | Red Herrings Digital Forensics &amp; Incident Response Labs</title>
<meta name="description" content="Guided Red Herrings learning pathways across two disciplines: Digital Forensics (GCFE, GASF, GNFA, SANS FOR577/FOR518) and Incident Response (GCIH, CompTIA CySA+, GCFR, GCFA). Ordered, case-by-case curricula from first-look triage to a capstone, plus analyst, insider-threat and ransomware IR role paths.">
<link rel="canonical" href="https://redherrings.app/pathways.html">
<meta name="robots" content="index,follow">
<meta name="theme-color" content="#E5382F">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 64 64%27%3E%3Cpath fill=%27%23E5382F%27 d=%27M6 32c9-11 20-16 30-16 4 0 8 3 12 9 3-3 8.5-9.5 14.25-13.25C58.38 18.12 55.69 25.81 54.44 32c1.25 6.19 3.94 13.87 7.81 20.25C56.5 48.5 51 42 48 39c-4 6-8 9-12 9-10 0-21-5-30-16z%27/%3E%3C/svg%3E">
<meta property="og:title" content="Learning Pathways &mdash; Red Herrings">
<meta property="og:description" content="Ordered, case-by-case curricula across Digital Forensics and Incident Response &mdash; certification prep and role paths.">
<meta property="og:url" content="https://redherrings.app/pathways.html">
<meta property="og:image" content="https://redherrings.app/img/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://redherrings.app/img/og.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="site.css">
  <script>(function(){{try{{var t=localStorage.getItem('rh-theme');if(t==='dark'||t==='light')document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}}})();</script>
</head>
<body>
<header>
  <div class="wrap nav">
    <a class="brand" href="/" aria-label="Red Herrings home">
      <svg width="28" height="28" viewBox="5.1 3 58 58" aria-hidden="true"><path fill-rule="evenodd" d="M6 32c9-11 20-16 30-16C40 16 44 19 48 25C51 22 56.5 15.5 62.25 11.75C58.38 18.12 55.69 25.81 54.44 32C55.69 38.19 58.38 45.88 62.25 52.25C56.5 48.5 51 42 48 39C44 45 40 48 36 48c-10 0-21-5-30-16z M20 24.8a5.6 5.6 0 1 0 0 11.2 5.6 5.6 0 1 0 0-11.2z" fill="var(--accent)"/><circle cx="20" cy="30.4" r="3.2" fill="none" stroke="var(--accent)" stroke-width="2"/><path d="M23 33.4l4 4" stroke="var(--accent)" stroke-width="2.6" stroke-linecap="round"/></svg>
      <span style="color:var(--ink)">Red Herrings</span>
    </a>
    <div class="spacer"></div>
    <a class="link" href="how.html">How it works</a>
    <a class="link" href="cases.html">Cases</a>
    <a class="link" href="pathways.html">Pathways</a>
    <a class="link" href="student-portal.html">Student portal</a>
    <a class="link" href="try.html">Try it</a>
    <a class="link" href="/#pricing">Pricing</a>
    <a class="btn" href="/download.html" data-goatcounter-click="cta-trial-nav">Start free trial</a>
  </div>
</header>
<main class="wrap">
  <div class="crumb" style="margin-bottom:10px"><a href="/">Home</a> / Pathways</div>
  <div class="secthead">
    <h1 class="opener">Learning <em>pathways</em></h1>
    <p class="osub">Ordered, case-by-case curricula that take a learner from first-look triage to a capstone, across both disciplines &mdash; <strong>Digital Forensics</strong> and <strong>Incident Response</strong>. Follow a certification-prep path or a role. Every case still generates a unique, auto-graded lab for each student.</p>
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
    <div class="cols">
      <div style="max-width:320px">
        <div class="brand" style="margin-bottom:8px"><svg width="22" height="22" viewBox="5.1 3 58 58" aria-hidden="true"><path fill-rule="evenodd" d="M6 32c9-11 20-16 30-16C40 16 44 19 48 25C51 22 56.5 15.5 62.25 11.75C58.38 18.12 55.69 25.81 54.44 32C55.69 38.19 58.38 45.88 62.25 52.25C56.5 48.5 51 42 48 39C44 45 40 48 36 48c-10 0-21-5-30-16z M20 24.8a5.6 5.6 0 1 0 0 11.2 5.6 5.6 0 1 0 0-11.2z" fill="var(--accent)"/><circle cx="20" cy="30.4" r="3.2" fill="none" stroke="var(--accent)" stroke-width="2"/><path d="M23 33.4l4 4" stroke="var(--accent)" stroke-width="2.6" stroke-linecap="round"/></svg><span style="color:var(--ink);font-size:16px">Red Herrings</span></div>
        <p style="margin:0 0 10px">Real Evidence. Real Skills. Real Fast.</p>
        <p style="margin:0;font-size:13px">Runs locally on Windows and Linux. No student data ever leaves your machine.</p>
      </div>
      <div class="fcol">
        <h4>Product</h4>
        <a href="how.html">How it works</a>
        <a href="cases.html">All cases</a>
        <a href="try.html">Try a sample</a>
        <a href="attack.html">MITRE ATT&amp;CK coverage</a>
        <a href="incident-response.html">Incident response</a>
        <a href="pathways.html">Learning pathways</a>
        <a href="student-portal.html">Student portal &amp; LMS</a>
        <a href="/#pricing">Pricing</a>
        <a href="/download.html">Download</a>
      </div>
      <div class="fcol">
        <h4>Support</h4>
        <a href="https://account.redherrings.app/account" data-goatcounter-click="signin">Activate a key</a>
        <a href="mailto:sales@redherrings.app?subject=Lost%20license%20key">Lost your key?</a>
        <a href="help.html">Help &amp; getting started</a>
        <a href="trust.html">Security &amp; trust</a>
        <a href="tools.html">Tools &amp; setup</a>
        <a href="blog/">Blog</a>
        <a href="/#faq">FAQ</a>
        <a href="mailto:sales@redherrings.app">sales@redherrings.app</a>
      </div>
      <div class="fcol">
        <h4>Buy</h4>
        <a href="/#pricing">Educators</a>
        <a href="/#pricing">Departments</a>
        <a href="/#pricing">Business and training</a>
        <a href="mailto:sales@redherrings.app?subject=Enterprise%20inquiry">Enterprise and government</a>
      </div>
      <div class="fcol">
        <h4>Legal</h4>
        <a href="privacy.html">Privacy Policy</a>
        <a href="terms.html">Terms of Service</a>
        <a href="eula.html">License agreement</a>
        <a href="refund.html">Refund Policy</a>
        <a href="accessibility.html">Accessibility</a>
      </div>
    </div>
    <div class="fbottom">
      <span>&copy; 2026 Red Herrings, a product of The Competence Collective, LLC. All rights reserved.</span>
      <span>Prices in USD. Institutional purchase orders welcome.</span>
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
<script src="theme.js" defer></script>
</body>
</html>
'''

if __name__ == "__main__":
    main()
