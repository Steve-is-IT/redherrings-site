#!/usr/bin/env python3
"""Rebuild the blog: magazine index + transform the 8 article pages.

Index: featured (newest) + image-left media cards (cover, category pill, title,
dek, date / reading time).
Articles: full-bleed branded cover, strong H1, lede, refined body typography,
related posts. No author, date, category label, or comments on the article
itself (owner's instruction) — the index carries category/date/reading-time.
"""
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
BLOG = os.path.join(ROOT, "blog")

# newest -> oldest
POSTS = [
    dict(slug="ios-imessage-forensics-cocoa-time", cls="c-mobile", cat="Mobile forensics",
         date="October 2, 2026", read="7 min read",
         title="Reading an iPhone sms.db: the iMessage joins and the Cocoa-time trap",
         dek="Join message, handle, chat and chat_message_join into a real thread, then decode Apple Cocoa time (nanoseconds since 2001) the way that trips students up."),
    dict(slug="detect-lateral-movement-windows-event-logs", cls="c-windows", cat="Windows forensics",
         date="October 2, 2026", read="7 min read",
         title="Detecting lateral movement in Windows event logs: the 4624 to 4688 pivot",
         dek="Match a remote logon to the processes it spawned by logon session, read subject against target correctly, and trace an attacker host to host."),
    dict(slug="gcfe-windows-forensics-practice-labs", cls="c-windows", cat="Windows forensics",
         date="October 2, 2026", read="5 min read",
         title="GCFE practice: a different Windows forensics case for every student",
         dek="Registry, prefetch, USB history and event logs &mdash; one authored case becomes a per-student Windows box with a verified answer key."),
    dict(slug="incident-response-exercise-edr-siem", cls="c-ir", cat="Incident response",
         date="October 2, 2026", read="6 min read",
         title="Run an incident response exercise from real EDR and SIEM evidence",
         dek="Work an IR case from the responder's own tooling, mapped to MITRE ATT&amp;CK and the NIST 800-61 phases, with time pressure built in."),
    dict(slug="teaching-mitre-attack-hands-on", cls="c-threat", cat="Threat-informed teaching",
         date="October 2, 2026", read="5 min read",
         title="Teach MITRE ATT&amp;CK with hands-on labs, not slides",
         dek="ATT&amp;CK-tagged cases make a technique something you find in the evidence and detect, not a cell to memorize on a chart."),
    dict(slug="detect-c2-beaconing-packet-capture", cls="c-network", cat="Network forensics",
         date="October 2, 2026", read="5 min read",
         title="Spotting C2 beaconing in a packet capture",
         dek="Teach students to read a PCAP by timing &mdash; interval, jitter and payload &mdash; follow the stream, and tell the beacon from benign noise."),
    dict(slug="dfir-learning-pathways-first-look-to-capstone", cls="c-course", cat="Course design",
         date="October 2, 2026", read="5 min read",
         title="From first look to capstone: building a DFIR learning pathway",
         dek="Sequence a course from a First Look on-ramp up the difficulty ladder to a cert-prep capstone, with guided mode easing beginners in."),
    dict(slug="forensics-exam-students-cant-copy", cls="c-exam", cat="Exam integrity",
         date="October 1, 2026", read="5 min read",
         title="Run a forensics exam students can't copy",
         dek="Why shared evidence makes copying inevitable, and how per-student cases, an in-browser solve portal and LMS grade passback fix it."),
]

BY_SLUG = {p["slug"]: p for p in POSTS}


def read(slug):
    with open(os.path.join(BLOG, slug + ".html")) as fh:
        return fh.read()


def write(slug, s):
    with open(os.path.join(BLOG, slug + ".html"), "w") as fh:
        fh.write(s)


# Pull the shared header + footer straight from an existing page so they stay
# byte-identical to the rest of the site.
_src = read("detect-c2-beaconing-packet-capture")
HEADER = "<header>" + _src.split("<header>", 1)[1].split("</header>", 1)[0] + "</header>"
FOOTER = "<footer>" + _src.split("<footer>", 1)[1].split("</footer>", 1)[0] + "</footer>"
TAIL = _src.split("</footer>", 1)[1]  # goatcounter + theme.js + </body></html>

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Inter:wght@400;500;600;700;800&display=swap">')
ICON = ('<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 '
        'viewBox=%270 0 64 64%27%3E%3Cpath fill=%27%23E5382F%27 d=%27M6 32c9-11 20-16 30-16 4 0 8 3 12 9 '
        '3-3 8.5-9.5 14.25-13.25C58.38 18.12 55.69 25.81 54.44 32c1.25 6.19 3.94 13.87 7.81 20.25C56.5 48.5 '
        '51 42 48 39c-4 6-8 9-12 9-10 0-21-5-30-16z%27/%3E%3C/svg%3E">')
THEMEBOOT = ("<script>(function(){try{var t=localStorage.getItem('rh-theme');"
             "if(t==='dark'||t==='light')document.documentElement.setAttribute('data-theme',t);}catch(e){}})();</script>")


def card(p, featured=False):
    img = f'../img/blog/{p["slug"]}.svg'
    href = f'{p["slug"]}.html'
    meta = (f'<span class="cat {p["cls"]}">{p["cat"]}</span>'
            f'<span class="pmeta">{p["date"]} <i>&middot;</i> {p["read"]}</span>')
    if featured:
        return f'''      <a class="feat" href="{href}">
        <div class="cover"><img src="{img}" alt="" width="1600" height="1000"></div>
        <div>
          <div class="meta-top">{meta}</div>
          <h2>{p["title"]}</h2>
          <p>{p["dek"]}</p>
          <span class="more">Read the post &rarr;</span>
        </div>
      </a>'''
    return f'''      <a class="pcard" href="{href}">
        <div class="cover"><img src="{img}" alt="" width="1600" height="1000" loading="lazy"></div>
        <div>
          <div class="meta-top">{meta}</div>
          <h3>{p["title"]}</h3>
          <p>{p["dek"]}</p>
        </div>
      </a>'''


def build_index():
    feat = card(POSTS[0], featured=True)
    rest = "\n".join(card(p) for p in POSTS[1:])
    head = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blog | Red Herrings</title>
<meta name="description" content="Teaching notes and product updates from Red Herrings: running hands-on digital forensics and incident response labs and exams that stay honest.">
<link rel="canonical" href="https://redherrings.app/blog/">
<meta name="robots" content="index,follow">
<meta name="theme-color" content="#E5382F">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Red Herrings">
<meta property="og:url" content="https://redherrings.app/blog/">
<meta property="og:title" content="Red Herrings blog — DFIR teaching notes">
<meta property="og:description" content="Teaching notes on running hands-on digital forensics and incident response labs and exams that stay honest.">
<meta property="og:image" content="https://redherrings.app/img/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Red Herrings blog — DFIR teaching notes">
<meta name="twitter:description" content="Teaching notes on running hands-on digital forensics and incident response labs and exams that stay honest.">
<meta name="twitter:image" content="https://redherrings.app/img/og.png">
{ICON}
{FONTS}
<link rel="stylesheet" href="../site.css">
<link rel="stylesheet" href="../blog.css">
  {THEMEBOOT}
</head>
<body>
{HEADER}

<main class="wrap">
  <div class="blog-head">
    <div class="crumb"><a href="/">Home</a> / Blog</div>
    <h1>Teaching notes</h1>
    <p>Short, practical notes on running hands-on digital forensics and incident response labs and exams that stay honest.</p>
  </div>

  <section style="border-top:0;padding:0">
{feat}

    <div class="posts">
{rest}
    </div>
  </section>
</main>

{FOOTER}
{TAIL}'''
    write("index", head)
    print("rebuilt index.html")


def related_block(slug):
    i = next(k for k, p in enumerate(POSTS) if p["slug"] == slug)
    picks = [POSTS[(i + j) % len(POSTS)] for j in (1, 2, 3)]
    cards = []
    for p in picks:
        cards.append(f'''      <a class="rel" href="{p["slug"]}.html">
        <div class="cover"><img src="../img/blog/{p["slug"]}.svg" alt="" width="1600" height="1000" loading="lazy"></div>
        <span class="cat {p["cls"]}">{p["cat"]}</span>
        <h3>{p["title"]}</h3>
      </a>''')
    return ('    <section class="related">\n'
            '      <h2>More teaching notes</h2>\n'
            '      <div class="rel-grid">\n'
            + "\n".join(cards) +
            '\n      </div>\n    </section>')


def transform_post(slug):
    s = read(slug)
    p = BY_SLUG[slug]

    # 1) add blog.css after site.css
    if "../blog.css" not in s:
        s = s.replace('<link rel="stylesheet" href="../site.css">',
                      '<link rel="stylesheet" href="../site.css">\n<link rel="stylesheet" href="../blog.css">', 1)

    # 2) drop the per-post inline <style> block (blog.css owns it now)
    s = re.sub(r'\n<style>.*?</style>', '', s, count=1, flags=re.S)

    # 3) rewrite the article header (pagehead -> cover + h1 + lede, no byline/crumb-category)
    m = re.search(r'<div class="pagehead".*?<h1>(?P<h1>.*?)</h1>\s*'
                  r'<p class="lede">(?P<lede>.*?)</p>\s*</div>', s, flags=re.S)
    if not m:
        raise SystemExit(f"[{slug}] could not match pagehead block")
    h1 = m.group("h1").strip()
    lede = m.group("lede").strip()
    new_head = (
        f'<nav class="post-crumb"><a href="/">Home</a> / <a href="index.html">Blog</a></nav>\n'
        f'    <div class="post-cover"><img src="../img/blog/{slug}.svg" alt="" width="1600" height="1000"></div>\n'
        f'    <header class="post-head"><h1>{h1}</h1></header>\n'
        f'    <p class="lede">{lede}</p>'
    )
    s = s[:m.start()] + new_head + s[m.end():]

    # 4) insert related block before </article>
    if 'class="related"' not in s:
        s = s.replace('  </article>', related_block(slug) + '\n  </article>', 1)

    write(slug, s)
    print(f"transformed {slug}.html")


def main():
    build_index()
    for p in POSTS:
        transform_post(p["slug"])


if __name__ == "__main__":
    main()
