#!/usr/bin/env python3
"""Generate courses.html and the syllabus PDFs from the engine's course packs.

Page chrome is copied from contact.html so the header, footer and head stay in
step with the rest of the site; run tools-apply-nav.py / tools-apply-footer.py
afterwards as usual.
"""
import html
import os
import re
import sys

sys.path.insert(0, "/home/user/redherrings")
from redherrings import courses, packs  # noqa: E402
from redherrings.config import load_branding  # noqa: E402
from redherrings.documents.syllabus import render_syllabus_pdf  # noqa: E402

SITE = os.path.dirname(os.path.abspath(__file__))
E = lambda s: html.escape(str(s or ""), quote=True)


def week_rows(c):
    out = []
    for w in c["weeks"]:
        mode = "Timed exam, %d min" % w["time_limit_min"] if w["mode"] == "exam" else "Practice"
        if w.get("report"):
            mode += ", with report"
        case = f'<a href="cases.html#{E(w["case"])}">{E(w.get("name") or w["case"])}</a>'
        out.append(f'<tr><td class="mono">{w["week"]}</td><td><b>{E(w["title"])}</b><div class="obj">{E(" ".join(w.get("objectives", [])))}</div></td>'
                   f'<td>{case}</td><td>{E(mode)}</td><td>{E(w.get("assessment", ""))}</td></tr>')
    return "".join(out)


def course_html(c):
    return f'''
    <section class="course" id="{E(c["slug"])}">
      <div class="secthead">
        <h2 class="opener">{E(c["label"])}</h2>
        <p class="osub">{E(c["short"])}</p>
      </div>
      <div class="cmeta"><span><b>{c["weeks_total"]} weeks</b></span><span>{E(c["level"])}</span><span>About {round(c["total_minutes"] / 60)} lab hours</span></div>
      <div class="ctwo">
        <div class="card"><h3>Learning outcomes</h3><ol>{"".join(f"<li>{E(o)}</li>" for o in c["outcomes"])}</ol></div>
        <div class="card"><h3>Assessment and tools</h3><p>{E(c["grading"])}</p><p class="muted">{E(", ".join(c["tools"]))}. All free.</p><p class="muted">Prerequisites: {E(c["prerequisites"])}</p></div>
      </div>
      <div class="tablewrap"><table class="wk"><thead><tr><th>Wk</th><th>Topic</th><th>Case</th><th>Mode</th><th>Assessment</th></tr></thead><tbody>{week_rows(c)}</tbody></table></div>
      <div class="cta-row" style="justify-content:flex-start;margin-top:18px">
        <a class="btn" href="files/syllabus-{E(c["slug"])}.pdf" data-goatcounter-click="syllabus-{E(c["slug"])}">Download the syllabus (PDF)</a>
        <a class="btn ghost" href="/download.html">Run it on the free trial</a>
      </div>
    </section>'''


def main():
    index = {s["id"]: s for s in packs.all_scenarios() if "id" in s}
    cat = courses.catalog(index)
    os.makedirs(os.path.join(SITE, "files"), exist_ok=True)
    branding = load_branding(None)
    for c in cat:
        render_syllabus_pdf(c, branding, os.path.join(SITE, "files", f"syllabus-{c['slug']}.pdf"))
    v = open(os.path.join(SITE, "contact.html")).read()
    head, tail = v[:v.index("<main")], v[v.index("</main>") + len("</main>"):]
    tail = re.sub(r"<script>\n\(function\(\)\{\n  var f=document\.getElementById\('cform'\).*?</script>\n", "", tail, count=1, flags=re.S)
    head = head.replace("<title>Contact Red Herrings | Sales, Quotes, Support</title>", "<title>Course Packs: Syllabus-Ready DFIR Courses | Red Herrings</title>")
    head = re.sub(r'<meta name="description" content="[^"]*">', lambda m: '<meta name="description" content="Two syllabus-ready courses built on Red Herrings: a 14-week Introduction to Digital Forensics and an 8-week Incident Response Fundamentals, with learning outcomes, a grading scheme, a week-by-week case plan and a downloadable syllabus PDF.">', head)
    head = head.replace("https://redherrings.app/contact.html", "https://redherrings.app/courses.html")
    head = re.sub(r'<meta property="og:title" content="[^"]*">', lambda m: '<meta property="og:title" content="Syllabus-ready DFIR course packs">', head)
    head = re.sub(r'<meta property="og:description" content="[^"]*">', lambda m: '<meta property="og:description" content="A 14-week forensics course and an 8-week incident-response course, week by week, with syllabus PDFs and one-click generation of every lab.">', head)
    head = re.sub(r'<meta name="twitter:description" content="[^"]*">', lambda m: '<meta name="twitter:description" content="A 14-week forensics course and an 8-week incident-response course with syllabus PDFs.">', head)
    head = re.sub(r"<style>.*?</style>", lambda m: '''<style>
.course{margin-bottom:10px}
.cmeta{display:flex;gap:18px;flex-wrap:wrap;color:var(--muted);font-size:14px;margin:-6px 0 18px}.cmeta b{color:var(--ink)}
.ctwo{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:18px}@media(max-width:760px){.ctwo{grid-template-columns:1fr}}
.ctwo .card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:20px 22px}.ctwo h3{margin:0 0 8px;font-size:16px}.ctwo ol{margin:0;padding-left:18px;font-size:14px;line-height:1.6}.ctwo p{margin:0 0 8px;font-size:14px;line-height:1.55}.ctwo .muted{color:var(--muted)}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:var(--radius);background:var(--card)}
.wk{width:100%;border-collapse:collapse;font-size:13.5px;min-width:720px}.wk th{text-align:left;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--faint);padding:10px 12px;border-bottom:1px solid var(--line)}
.wk td{padding:10px 12px;border-bottom:1px solid var(--line-2);vertical-align:top}.wk tr:last-child td{border-bottom:0}.wk .obj{color:var(--muted);font-size:12.5px;line-height:1.45;margin-top:2px}.wk .mono{font-family:var(--mono)}
.wk a{color:var(--blue)}
</style>''', head, flags=re.S)
    sections = "\n".join(course_html(c) for c in cat)
    main_html = f'''<main class="wrap" id="main">
  <section style="border-top:0">
    <div class="crumb"><a href="/">Home</a> / Course packs</div>
    <div class="secthead">
      <h1 class="opener">Courses that drop <em>into a syllabus</em></h1>
      <p class="osub">Two complete courses built on the case library: learning outcomes, a grading scheme, the free tools, and a week-by-week plan that names the case, the mode and the time budget. Download the syllabus PDF, then generate every week's lab for your roster in one click from the Courses screen in the app. Every student still gets their own variant; every answer is still verified.</p>
    </div>
  </section>
{sections}
  <section class="cta-band" aria-labelledby="cta-courses">
    <h2 id="cta-courses">Teach the whole term from one download.</h2>
    <p class="sub" style="margin-bottom:24px">The free 30-day trial includes the EDR first look and the USB first look, which open both courses. An Educator license runs every week.</p>
    <div class="cta-row">
      <a class="btn" href="/download.html" data-goatcounter-click="cta-trial-courses">Start a free 30-day trial</a>
      <a class="btn ghost" href="pathways.html">See the learning pathways</a>
    </div>
  </section>
</main>'''
    out = os.path.join(SITE, "courses.html")
    with open(out, "w") as f:
        f.write(head + main_html + tail)
    print(f"wrote courses.html: {len(cat)} courses; syllabus PDFs in files/")


if __name__ == "__main__":
    main()
