#!/usr/bin/env python3
"""Generate courses.html and the syllabus PDFs from the engine's course packs.

Page chrome is copied from contact.html so the header, footer and head stay in
step with the rest of the site.
"""
import html
import os
import re
import sys

# The product package comes from the sibling redherrings checkout (or RH_PRODUCT).
sys.path.insert(0, os.environ.get("RH_PRODUCT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "redherrings"))
from redherrings import courses, packs  # noqa: E402
from redherrings.config import load_branding  # noqa: E402
from redherrings.documents.syllabus import render_syllabus_pdf  # noqa: E402

SITE = os.path.dirname(os.path.abspath(__file__))
E = lambda s: html.escape(str(s or ""), quote=True)
SLUG = {}  # scenario id -> public slug, filled in main()



def _load_product_text():
    """tools-product-text.py: site corrections to product text the cases don't back up."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("tools_product_text", os.path.join(SITE, "tools-product-text.py"))
    mod = importlib.util.module_from_spec(spec)
    was = sys.dont_write_bytecode
    sys.dont_write_bytecode = True  # keep __pycache__ out of the site repo
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = was
    return mod


PT = _load_product_text()


def week_rows(c):
    out = []
    for w in c["weeks"]:
        mode = "Timed exam, %d min" % w["time_limit_min"] if w["mode"] == "exam" else "Practice"
        if w.get("report"):
            mode += ", with report"
        case = f'<a href="cases.html#{E(w.get("slug") or SLUG.get(w["case"], w["case"]))}">{E(w.get("name") or w["case"])}</a>'
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


def trial_weeks(cat):
    """Which weeks the trial key opens beyond the free First Looks, in words."""
    from redherrings.licensing.core import TRIAL_SCENARIOS
    parts = []
    for c in cat:
        wk = [str(w["week"]) for w in c["weeks"] if w["case"] in TRIAL_SCENARIOS and not str(w.get("name", "")).startswith("First Look")]
        if wk:
            nums = wk[0] if len(wk) == 1 else ", ".join(wk[:-1]) + " and " + wk[-1]
            parts.append(f'week{"s" if len(wk) > 1 else ""} {nums} of {E(c["label"])}')
    return " and ".join(parts) if parts else "sample cases from the paid library"


def apply_chrome(path):
    """Stamp the canonical header and footer so a regenerated page never carries a stale nav."""
    import importlib.util
    for name in ("tools-apply-nav", "tools-apply-footer"):
        spec = importlib.util.spec_from_file_location(name.replace("-", "_"), os.path.join(SITE, name + ".py"))
        mod = importlib.util.module_from_spec(spec)
        was = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            spec.loader.exec_module(mod)
        finally:
            sys.dont_write_bytecode = was
        mod.apply(path, False) if name == "tools-apply-nav" else mod.apply(path)


def main():
    index = {s["id"]: s for s in packs.all_scenarios() if "id" in s}
    for s in index.values():
        s["tools"] = PT.tools(s["id"], s.get("tools"))
    SLUG.update({k: v.get("slug") or k for k, v in index.items()})
    cat = [PT.fix_tree("course", c["slug"], c) for c in courses.catalog(index)]
    for c in cat:
        for w in c["weeks"]:
            w["summary"] = PT.fix("case-summary", w.get("case"), w.get("summary"))
    # The syllabus PDF reads the shared policy text from courses.STANDARD.
    for k in list(courses.STANDARD):
        courses.STANDARD[k] = PT.fix_tree("standard", "*", courses.STANDARD[k])
    # The renderer also writes text of its own. Its P() looks up sections._p
    # at call time, so wrapping that runs every paragraph through the
    # syllabus swaps.
    from redherrings.documents import sections
    para = sections._p
    sections._p = lambda text, style: para(PT.fix("syllabus", "*", text), style)
    os.makedirs(os.path.join(SITE, "files"), exist_ok=True)
    branding = load_branding(None)
    for c in cat:
        render_syllabus_pdf(c, branding, os.path.join(SITE, "files", f"syllabus-{c['slug']}.pdf"))
    v = open(os.path.join(SITE, "contact.html")).read()
    head, tail = v[:v.index("<main")], v[v.index("</main>") + len("</main>"):]
    tail = re.sub(r"<script>\n\(function\(\)\{\n  var f=document\.getElementById\('cform'\).*?</script>\n", "", tail, count=1, flags=re.S)
    head = head.replace("<title>Contact Red Herrings | Sales, Quotes, Support</title>", "<title>Digital Forensics and IR Course Syllabi | Red Herrings</title>")
    head = re.sub(r'<meta name="description" content="[^"]*">', lambda m: '<meta name="description" content="Two ready-to-teach courses: a 14-week Introduction to Digital Forensics and an 8-week Incident Response, with outcomes, a weekly case plan and a PDF.">', head)
    head = head.replace("https://redherrings.app/contact.html", "https://redherrings.app/courses.html")
    head = re.sub(r'<meta property="og:title" content="[^"]*">', lambda m: '<meta property="og:title" content="Digital Forensics and IR Course Syllabi | Red Herrings">', head)
    head = re.sub(r'<meta property="og:description" content="[^"]*">', lambda m: '<meta property="og:description" content="Two ready-to-teach courses: a 14-week Introduction to Digital Forensics and an 8-week Incident Response, with outcomes, a weekly case plan and a PDF.">', head)
    head = re.sub(r'<meta name="twitter:description" content="[^"]*">', lambda m: '<meta name="twitter:description" content="Two ready-to-teach courses: a 14-week Introduction to Digital Forensics and an 8-week Incident Response, with outcomes, a weekly case plan and a PDF.">', head)
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
      <h1 class="opener">A digital forensics course and an incident response course, ready to teach</h1>
      <p class="osub">Two complete courses built on the case library: learning outcomes, a grading scheme, the free tools, and a week-by-week plan that names the case, the mode and the time budget. Download the syllabus PDF, set the class size, and generate every week's lab in one click from the Courses screen in the app. To keep your roster's student ids, generate each week from the Generate screen instead. Every student still gets their own variant; every fact answer is still verified.</p>
    </div>
  </section>
{sections}
  <section class="cta-band" aria-labelledby="cta-courses">
    <h2 id="cta-courses">Teach the whole term from one download.</h2>
    <p class="sub" style="margin-bottom:24px">Every First Look week in both courses runs free, with no key, for up to five students per lab. The 30-day trial adds {trial_weeks(cat)}, and an Educator license runs every week.</p>
    <div class="cta-row">
      <a class="btn" href="/download.html" data-goatcounter-click="cta-trial-courses">Learn for free</a>
      <a class="btn ghost" href="pathways.html">See the learning pathways</a>
    </div>
  </section>
</main>'''
    out = os.path.join(SITE, "courses.html")
    with open(out, "w") as f:
        f.write(head + main_html + tail)
    apply_chrome(out)
    print(f"wrote courses.html: {len(cat)} courses; syllabus PDFs in files/")
    PT.report("course", "standard", "syllabus")


if __name__ == "__main__":
    main()
