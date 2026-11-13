#!/usr/bin/env python3
"""Generate the three audience guides the download page's trial form promises.

    guide-educators.html       term plan, grading, LMS import
    guide-security-teams.html  drill plan, ATT&CK coverage, scored exercises
    guide-self-study.html      study path, tools, weekly cadence

Every case name, time budget, difficulty, technique and access level is read
from the engine, so the guides stay in step with the case library. Page chrome
is copied from contact.html; run tools-apply-nav.py / tools-apply-footer.py
afterwards as usual.
"""
import html
import math
import os
import re
import sys

# The product package comes from the sibling redherrings checkout (or RH_PRODUCT).
sys.path.insert(0, os.environ.get("RH_PRODUCT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "redherrings"))
from redherrings import attack, courses, licensing, packs, pathways  # noqa: E402
from redherrings.licensing import tiers  # noqa: E402

SITE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://redherrings.app"
E = lambda s: html.escape(str(s or ""), quote=True)

INDEX = {s["id"]: s for s in packs.all_scenarios() if "id" in s}
PATHS = {p["slug"]: p for p in pathways.catalog(INDEX)}
COURSES = {c["slug"]: c for c in courses.catalog(INDEX)}
TRIAL = set(licensing.TRIAL_SCENARIOS)
DIFF = {"easy": "Easy", "medium": "Medium", "hard": "Hard", "expert": "Expert"}
WEEK_BUDGET = 180  # minutes a working learner can give a week: two 90-minute sessions


def access(cid):
    s = INDEX[cid]
    if s.get("free"):
        return ("free", "Free")
    if cid in TRIAL:
        return ("trial", "Trial")
    tier = s.get("tier")
    return ("lic", tiers.tier_label(tier) if tier and tiers.known_tier(tier) else "Paid plan")


def access_tag(cid):
    cls, label = access(cid)
    return f'<span class="acc acc-{cls}">{E(label)}</span>'


def diff_tag(cid):
    s = INDEX[cid]
    if s.get("category") == "first-look":
        return '<span class="dt dt-fl">First Look</span>'
    d = s.get("difficulty") or "medium"
    return f'<span class="dt dt-{E(d)}">{E(DIFF.get(d, d.title()))}</span>'


def case_link(cid):
    return f'<a href="cases.html#{E(INDEX[cid].get("slug") or cid)}">{E(INDEX[cid]["name"])}</a>'


def minutes(m):
    m = int(m or 0)
    if m < 60:
        return f"{m} min"
    h, r = divmod(m, 60)
    return f"{h} h" + (f" {r} min" if r else "")


def cert_short(label):
    m = re.search(r"\(([^)]+)\)", label)
    return m.group(1) if m else label


def certs_for(cid):
    out = []
    for p in PATHS.values():
        if p.get("kind") == "cert" and any(s["id"] == cid for s in p["steps"]):
            out.append(cert_short(p["label"]))
    return out


def trial_counts(ids):
    free = sum(1 for i in ids if access(i)[0] == "free")
    trial = sum(1 for i in ids if access(i)[0] == "trial")
    return free, trial


LEGEND = ('<p class="legend"><span class="acc acc-free">Free</span> runs on download with no key. '
          '<span class="acc acc-trial">Trial</span> opens with the 30-day trial key. '
          '<span class="acc acc-lic">Paid plan</span> needs a license; a plan name such as '
          '<span class="acc acc-lic">Department</span> means that plan or above.</p>')


# ---------------------------------------------------------------- educators
def course_table(c, cert_col):
    rows = []
    for w in c["weeks"]:
        cid = w["case"]
        mode = f'Timed exam, {w["time_limit_min"]} min' if w.get("mode") == "exam" else "Practice"
        if w.get("report"):
            mode += ", report"
        cert = ", ".join(certs_for(cid)) or "&nbsp;"
        rows.append(f'<tr><td class="mono">{w["week"]}</td><td><b>{E(w["title"])}</b></td><td>{case_link(cid)}</td>'
                    f'<td>{diff_tag(cid)}</td><td>{E(mode)}</td>' + (f'<td>{E(cert) if cert != "&nbsp;" else cert}</td>' if cert_col else "")
                    + f'<td>{access_tag(cid)}</td></tr>')
    head = ('<tr><th>Wk</th><th>Topic</th><th>Case</th><th>Level</th><th>Mode</th>'
            + ("<th>Cert topic</th>" if cert_col else "") + "<th>Access</th></tr>")
    return f'<div class="tablewrap"><table class="gt"><thead>{head}</thead><tbody>{"".join(rows)}</tbody></table></div>'


def educator_main():
    df = COURSES["intro-digital-forensics-14"]
    ir = COURSES["incident-response-fundamentals-8"]
    df_ids = [w["case"] for w in df["weeks"]]
    ir_ids = [w["case"] for w in ir["weeks"]]
    f1, t1 = trial_counts(df_ids)
    f2, t2 = trial_counts(ir_ids)
    certs = sorted({c for i in df_ids for c in certs_for(i)})
    return f'''
  <section style="border-top:0">
    <div class="crumb"><a href="/">Home</a> / <a href="resources.html">Resources</a> / Guide for educators</div>
    <div class="secthead">
      <h1 class="opener">Teach a DFIR lab course <em>without building the labs</em></h1>
      <p class="osub">A term plan you can drop into a syllabus, how grading works, and the import steps for Canvas, Blackboard, Moodle and D2L Brightspace. Every student gets their own evidence and their own answer key, so a classmate's or last term's answer sheet scores about a quarter of the points.</p>
    </div>
    <div class="steps">
      <div class="card"><b>1. Before week one</b><p>Install the app and paste your trial key in Settings, Licensing. Import your roster with each student's id set to the identifier your LMS matches on (Canvas SIS Login ID, Blackboard and Moodle username, D2L Username or OrgDefinedId).</p></div>
      <div class="card"><b>2. Each week</b><p>Generate the week's case for the roster. Each student gets a zip with their own evidence, plus a link to the student portal where they answer in the browser. You keep the instructor key.</p></div>
      <div class="card"><b>3. After the deadline</b><p>Grade the class in one pass, read the per-question analytics, run the anti-collusion report, and export a grade file for your LMS.</p></div>
    </div>
  </section>

  <section>
    <div class="secthead"><h2 class="opener">The {df["weeks_total"]}-week forensics term</h2>
      <p class="osub">{E(df["label"])}: {E(df["level"])}. About {round(df["total_minutes"] / 60)} lab hours. The cert topic column names the prep track each case sits in ({E(", ".join(certs))}). A track is named for a certification, not mapped to it objective by objective. {f1} weeks run free and the trial opens {t1} more, so you can teach the first stretch of the term before buying anything.</p></div>
    {LEGEND}
    {course_table(df, True)}
    <p class="note">Learning outcomes, readings and the grading scheme are in the <a href="files/syllabus-{E(df["slug"])}.pdf">syllabus PDF</a>. The app's Courses screen generates every week's lab for a class size you set, numbered student-001 up. To keep your roster's ids, generate each week from the Generate screen.</p>
  </section>

  <section>
    <div class="secthead"><h2 class="opener">The {ir["weeks_total"]}-week incident-response course</h2>
      <p class="osub">{E(ir["label"])}: {E(ir["level"])}. Worked from EDR, SIEM, email and event-log evidence and graded against MITRE ATT&amp;CK. {f2} weeks run free and the trial opens {t2} more.</p></div>
    {course_table(ir, False)}
    <p class="note">Full outcomes and readings: <a href="files/syllabus-{E(ir["slug"])}.pdf">syllabus PDF</a>.</p>
  </section>

  <section>
    <div class="secthead"><h2 class="opener">How grading works</h2></div>
    <div class="two">
      <div class="card"><h3>One pass for the whole class</h3><p>Students answer in the portal, or you collect the grading sheet and import it on the Grading screen. Each answer is checked against that student's own key: hashes case-insensitive, timestamps within seconds, free text fuzzy-matched with a review flag. Every score shows why it was awarded.</p></div>
      <div class="card"><h3>What you see afterwards</h3><p>Mean, median and the score distribution, plus the correct rate per question, so you know what to reteach. The anti-collusion report shows how many distinct answers each question had and which student pairs were handed the most matching answers.</p></div>
      <div class="card"><h3>Reports and rubrics</h3><p>Turn on the investigation report template and mark each report against the rubric on the Grading screen. The export can blend the report into the lab score (30% by default) or put it in its own column.</p></div>
      <div class="card"><h3>Feedback students read</h3><p>Turn on feedback at export and each student gets a note listing the questions they missed, for example: "Scored 8.0/10.0 (80.0%). Missed 1: q2 (timestamp)."</p></div>
    </div>
  </section>

  <section>
    <div class="secthead"><h2 class="opener">Importing grades into your LMS</h2>
      <p class="osub">The app hands you a grade file to upload. It doesn't talk to your LMS over the network, so there's nothing for IT to approve. Choose the column name at export so it matches your gradebook, and raw points or percent.</p></div>
    <div class="tablewrap"><table class="gt"><thead><tr><th>LMS</th><th>File</th><th>Matches students by</th><th>Steps</th></tr></thead><tbody>
      <tr><td><b>Canvas</b></td><td class="mono">canvas-grades.csv</td><td>SIS Login ID</td><td>Gradebook, Import, upload the file. Map it to a new or existing assignment, review, save. The second row carries Points Possible.</td></tr>
      <tr><td><b>Blackboard</b></td><td class="mono">blackboard-grades.csv</td><td>Username</td><td>Grade Center, Work Offline, Upload. Map the grade column and submit.</td></tr>
      <tr><td><b>Moodle</b></td><td class="mono">moodle-grades.csv</td><td>username</td><td>Course gradebook, Import, CSV file. Map username to the user identifier and the grade column to the grade item. Feedback lands in the feedback column.</td></tr>
      <tr><td><b>D2L Brightspace</b></td><td class="mono">brightspace-grades.csv</td><td>Username or OrgDefinedId</td><td>Grades, Import, upload the file. The End-of-Line Indicator column is included. Feedback imports from the added Feedback column.</td></tr>
      <tr><td><b>Anything else</b></td><td class="mono">grades.csv</td><td>student_id</td><td>A plain id and score file, plus an optional per-question detail CSV.</td></tr>
    </tbody></table></div>
    <p class="note">Canvas and Blackboard grade uploads don't carry comments, so export the separate student-feedback.csv for those. You can also export a case as a Common Cartridge (.imscc) module.</p>
  </section>
'''


# ------------------------------------------------------------ security teams
TEAM_PLAN = ["ir-first-look-edr", "ir-first-look-siem", "easy-phish-triage", "ir-phish-to-foothold",
             "phishing-c2", "drill-insider-exfil-45", "medium-lateral-psexec", "ransomware-precursor",
             "drill-ransomware-45", "ir-ransomware-dawn", "ir-marquee-nightfall"]


def step_note(cid):
    for p in PATHS.values():
        for st in p["steps"]:
            if st["id"] == cid and st.get("note"):
                return st["note"]
    summ = INDEX[cid].get("summary") or ""
    return summ.split(". ")[0].rstrip(".") + "." if summ else ""


def team_main():
    steps = [{"id": c, "minutes": INDEX[c].get("estimated_minutes") or 0, "note": step_note(c)} for c in TEAM_PLAN]
    total = sum(st["minutes"] for st in steps)
    trial_names = " and ".join(INDEX[c]["name"] for c in TEAM_PLAN if access(c)[0] == "trial")
    rows = []
    for s in steps:
        cid = s["id"]
        tac = ", ".join(attack.tactic(t)["label"] for t in attack.tactics_for(cid, INDEX[cid].get("tactics")) if attack.known_tactic(t))
        rows.append(f'<tr><td>{case_link(cid)}<div class="obj">{E(s.get("note"))}</div></td><td>{diff_tag(cid)}</td>'
                    f'<td class="mono">{minutes(s["minutes"])}</td><td>{E(tac)}</td><td>{access_tag(cid)}</td></tr>')
    # ATT&CK coverage by tactic. Technique ids per case stay off the page: some
    # questions ask students to name the technique, so listing a case's
    # techniques here would hand them the answer.
    tech = {t for s in steps for t in attack.techniques_for(s["id"], INDEX[s["id"]].get("techniques"))}
    tactics = sorted({t for s in steps for t in attack.tactics_for(s["id"], INDEX[s["id"]].get("tactics")) if attack.known_tactic(t)},
                     key=attack.TACTIC_SLUGS.index)
    cov = []
    for t in tactics:
        n = sum(1 for s in steps if t in attack.tactics_for(s["id"], INDEX[s["id"]].get("tactics")))
        cov.append(f'<tr><td>{E(attack.tactic(t)["label"])}</td><td class="mono">{n}</td></tr>')
    ids = [s["id"] for s in steps]
    f, tr = trial_counts(ids)
    return f'''
  <section style="border-top:0">
    <div class="crumb"><a href="/">Home</a> / <a href="resources.html">Resources</a> / Guide for security teams</div>
    <div class="secthead">
      <h1 class="opener">Run scored IR drills <em>on your own evidence formats</em></h1>
      <p class="osub">A drill plan from First Look triage to a full intrusion, the MITRE ATT&amp;CK techniques it exercises, and how to run a timed, scored exercise. Each analyst gets a different variant of the same incident, so nobody can read answers off a neighbor's screen.</p>
    </div>
  </section>

  <section>
    <div class="secthead"><h2 class="opener">The drill plan</h2>
      <p class="osub">{len(steps)} cases, about {round(total / 60)} hours in total. Run one a week or one per on-call rotation. {f} run free on download and the trial opens {tr} more ({E(trial_names)}), so you can take a phish from the first alert to command and control before you buy.</p></div>
    {LEGEND}
    <div class="tablewrap"><table class="gt"><thead><tr><th>Case</th><th>Level</th><th>Time</th><th>ATT&amp;CK tactics</th><th>Access</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
  </section>

  <section>
    <div class="secthead"><h2 class="opener">ATT&amp;CK coverage</h2>
      <p class="osub">The plan touches {len(tactics)} of the {attack.ENTERPRISE_TACTIC_COUNT} Enterprise tactics through {len(tech)} techniques. The table counts the cases in the plan that exercise each tactic; the <a href="attack.html">ATT&amp;CK page</a> covers the whole library.</p></div>
    <div class="tablewrap"><table class="gt"><thead><tr><th>Tactic</th><th>Cases in the plan</th></tr></thead><tbody>{"".join(cov)}</tbody></table></div>
  </section>

  <section>
    <div class="secthead"><h2 class="opener">Running a scored exercise</h2></div>
    <div class="two">
      <div class="card"><h3>Set it up</h3><p>On Home, choose &ldquo;I train a security team&rdquo; and Generate starts at 8 analysts, exam mode, a 45-minute clock and integrity mode on. Change the headcount and clock to fit your shift. Hand out the portal link; analysts work the evidence in the tools they already use and answer in the browser.</p></div>
      <div class="card"><h3>Integrity logging</h3><p>In exam mode the portal records tab switches, full-screen exits and pastes for each analyst, with times, so a score you report up the chain comes with evidence it was earned under exam conditions.</p></div>
      <div class="card"><h3>When the clock stops</h3><p>A leaderboard ranked by score, then time. The hardest questions sorted by correct rate, with the most common wrong answer, so the debrief starts at the gap. Containment calls are graded too: who isolated the host, who scanned it, who emailed the user.</p></div>
      <div class="card"><h3>What you keep</h3><p>A completion certificate per analyst, and the drill's indicators exported as STIX 2.1 and CSV for your own detection content. Everything runs on your machines; no evidence leaves the network.</p></div>
    </div>
  </section>
'''


# ---------------------------------------------------------------- self-study
def weekly_plan(steps):
    """Group a pathway into weeks of at most WEEK_BUDGET minutes. A case
    longer than a week spans as many weeks as it needs."""
    weeks, cur, used = [], [], 0
    for s in steps:
        m = int(s["minutes"] or 0)
        if m > WEEK_BUDGET:
            if cur:
                weeks.append((cur, 1)); cur, used = [], 0
            weeks.append(([s], math.ceil(m / WEEK_BUDGET)))
            continue
        if used + m > WEEK_BUDGET and cur:
            weeks.append((cur, 1)); cur, used = [], 0
        cur.append(s); used += m
    if cur:
        weeks.append((cur, 1))
    rows, n = [], 1
    for group, span in weeks:
        label = f"{n}" if span == 1 else f"{n} to {n + span - 1}"
        n += span
        cases = "".join(f'<div class="wkcase">{case_link(s["id"])} {diff_tag(s["id"])} {access_tag(s["id"])} '
                        f'<span class="muted">{minutes(s["minutes"])}</span></div>' for s in group)
        tools = sorted({t for s in group for t in (INDEX[s["id"]].get("tools") or [])})
        rows.append(f'<tr><td class="mono">{label}</td><td>{cases}</td><td class="muted">{E(", ".join(tools))}</td></tr>')
    return n - 1, ('<div class="tablewrap"><table class="gt"><thead><tr><th>Week</th><th>Cases</th><th>Tools that week</th></tr></thead>'
                   f'<tbody>{"".join(rows)}</tbody></table></div>')


def learner_main():
    df = PATHS["gcfe-windows"]
    ir = PATHS["gcih-incident-handling"]
    df_weeks, df_table = weekly_plan(df["steps"])
    ir_weeks, ir_table = weekly_plan(ir["steps"])
    f1, t1 = trial_counts([s["id"] for s in df["steps"]])
    f2, t2 = trial_counts([s["id"] for s in ir["steps"]])
    return f'''
  <section style="border-top:0">
    <div class="crumb"><a href="/">Home</a> / <a href="resources.html">Resources</a> / Guide for self-study</div>
    <div class="secthead">
      <h1 class="opener">Learn DFIR on your own, <em>around a job</em></h1>
      <p class="osub">Two study paths from First Look to a capstone, the free tools each week needs, and a cadence of about three hours a week: two 90-minute sessions. Every run generates fresh evidence, so you can redo a case and still have to work it.</p>
    </div>
  </section>

  <section>
    <div class="secthead"><h2 class="opener">Path 1: Windows forensics</h2>
      <p class="osub">{E(df["label"])}. {len(df["steps"])} cases, about {round(df["total_minutes"] / 60)} hours, {df_weeks} weeks at this pace. {f1} cases run free and the trial opens {t1} more. Full notes are on the <a href="pathways/gcfe-windows.html">pathway page</a>.</p></div>
    {LEGEND}
    {df_table}
  </section>

  <section>
    <div class="secthead"><h2 class="opener">Path 2: incident response</h2>
      <p class="osub">{E(ir["label"])}. {len(ir["steps"])} cases, about {round(ir["total_minutes"] / 60)} hours, {ir_weeks} weeks at this pace. {f2} cases run free and the trial opens {t2} more. See the <a href="pathways/gcih-incident-handling.html">pathway page</a>.</p></div>
    {ir_table}
  </section>

  <section>
    <div class="secthead"><h2 class="opener">Tools to install, and why</h2>
      <p class="osub">All free. Install what the week needs; the <a href="tools.html">toolkit page</a> has a one-run installer for Windows and Linux.</p></div>
    <div class="two">
      <div class="card"><h3>Windows artifacts</h3><p><b>Eric Zimmerman's tools</b> (PECmd, LECmd, JLECmd, EvtxECmd, Timeline Explorer) parse Prefetch, LNK files, jump lists, event logs and timelines. <b>Registry Explorer</b> reads hives: USB history, UserAssist, Run keys.</p></div>
      <div class="card"><h3>Disk and memory</h3><p><b>Autopsy</b> opens disk images and recovers deleted files. <b>Volatility 3</b> lists processes, network connections and injected code in a memory image.</p></div>
      <div class="card"><h3>Browser, mail and databases</h3><p><b>DB Browser for SQLite</b> opens browser history and app databases. <b>Thunderbird</b> reads mailboxes and loose .eml files, headers included.</p></div>
      <div class="card"><h3>IR feeds</h3><p>EDR and SIEM evidence ships as JSON. <b>jq</b> or any JSON viewer filters it; Excel or LibreOffice sorts an alert queue. <b>Wireshark</b> handles packet captures.</p></div>
    </div>
  </section>

  <section>
    <div class="secthead"><h2 class="opener">When you're stuck</h2></div>
    <div class="two">
      <div class="card"><h3>Guided mode</h3><p>On the Solution screen, guided mode steps through one question at a time: where to look, then how to work it with the right tool, then the answer. The printable guided worksheet adds a hint under each question and a tool quick-start.</p></div>
      <div class="card"><h3>Redo it cold</h3><p>Generate the same case again with a new seed. Names, hashes, IPs and timestamps change, so the second run tests the method, not your memory of the answers.</p></div>
    </div>
  </section>
'''


# ------------------------------------------------------------------- pages
STYLE = '''<style>
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}@media(max-width:860px){.steps{grid-template-columns:1fr}}
.steps .card,.two .card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:18px 20px}
.steps .card b{display:block;margin-bottom:6px}.steps .card p,.two .card p{margin:0;font-size:14px;line-height:1.55;color:var(--ink-2,var(--ink))}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:760px){.two{grid-template-columns:1fr}}.two h3{margin:0 0 8px;font-size:16px}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:var(--radius);background:var(--card)}
.gt{width:100%;border-collapse:collapse;font-size:13.5px;min-width:680px}.gt th{text-align:left;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--faint);padding:10px 12px;border-bottom:1px solid var(--line)}
.gt td{padding:10px 12px;border-bottom:1px solid var(--line-2);vertical-align:top}.gt tr:last-child td{border-bottom:0}.gt .mono{font-family:var(--mono)}.gt a{color:var(--blue)}
.gt .obj{color:var(--muted);font-size:12.5px;line-height:1.45;margin-top:2px}.muted{color:var(--muted)}.wkcase{margin:2px 0}
.dt,.acc{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;padding:2px 7px;border-radius:999px;border:1px solid var(--line);white-space:nowrap}
.dt-fl{color:var(--blue)}.dt-easy{color:var(--ok)}.dt-medium{color:#b7791f}.dt-hard{color:var(--bad)}.dt-expert{color:#7c3aed}
.acc-free{background:var(--ok);border-color:var(--ok);color:#fff}.acc-trial{background:var(--blue);border-color:var(--blue);color:#fff}.acc-lic{color:var(--muted)}
.legend{font-size:13px;color:var(--muted);margin:0 0 12px;line-height:1.9}.note{font-size:13.5px;color:var(--muted);margin-top:12px}
</style>'''

PAGES = [
    {"file": "guide-educators.html", "main": educator_main,
     "title": "DFIR Lab Course Guide for Educators: Term Plan, Grading, LMS Import | Red Herrings",
     "desc": "A week-by-week forensics and incident-response term plan, how auto-grading works, and grade import steps for Canvas, Blackboard, Moodle and D2L Brightspace.",
     "og": "Teach a DFIR lab course without building the labs",
     "cta": ("Start the term on the trial.", "The First Look weeks run free. The trial opens the midterm, the capstone and the phishing exam for 30 days, for up to five students.", "guide-educators")},
    {"file": "guide-security-teams.html", "main": team_main,
     "title": "IR Drill Guide for Security Teams: Drill Plan, ATT&amp;CK Coverage, Scoring | Red Herrings",
     "desc": "A drill plan from First Look triage to a full intrusion, the MITRE ATT&CK techniques it exercises, and how to run timed, scored exercises with integrity logging.",
     "og": "Run scored IR drills on your own evidence formats",
     "cta": ("Run the first drill this week.", "The trial opens the phishing-to-C2 cases for 30 days, for up to five analysts. First Look stays free.", "guide-teams")},
    {"file": "guide-self-study.html", "main": learner_main,
     "title": "Self-Study DFIR Guide: Study Paths, Free Tools, Weekly Plan | Red Herrings",
     "desc": "Two DFIR study paths from First Look to a capstone, the free tools each week needs, and a three-hours-a-week plan that fits around a full-time job.",
     "og": "Learn DFIR on your own, around a job",
     "cta": ("Start with the free cases.", "First Look runs free on download. The trial key adds a medium and a hard case in each path for 30 days.", "guide-self-study")},
]


def build(page, head0, tail):
    head = head0.replace("<title>Contact Red Herrings | Sales, Quotes, Support</title>", f"<title>{page['title']}</title>")
    assert 120 <= len(html.unescape(page["desc"])) <= 170, (page["file"], len(page["desc"]))
    d = E(page["desc"])
    head = re.sub(r'<meta name="description" content="[^"]*">', lambda m: f'<meta name="description" content="{d}">', head)
    head = head.replace(f"{BASE}/contact.html", f"{BASE}/{page['file']}")
    head = re.sub(r'<meta property="og:title" content="[^"]*">', lambda m: f'<meta property="og:title" content="{E(page["og"])}">', head)
    head = re.sub(r'<meta property="og:description" content="[^"]*">', lambda m: f'<meta property="og:description" content="{d}">', head)
    head = re.sub(r'<meta name="twitter:description" content="[^"]*">', lambda m: f'<meta name="twitter:description" content="{d}">', head)
    head = re.sub(r"<style>.*?</style>", lambda m: STYLE, head, count=1, flags=re.S)
    h2, sub, click = page["cta"]
    body = f'''<main class="wrap" id="main">{page["main"]()}
  <section class="cta-band" aria-labelledby="cta-guide">
    <h2 id="cta-guide">{E(h2)}</h2>
    <p class="sub" style="margin-bottom:24px">{E(sub)}</p>
    <div class="cta-row">
      <a class="btn" href="/download.html" data-goatcounter-click="cta-{click}">Learn for free</a>
      <a class="btn ghost" href="cases.html">Browse the cases</a>
    </div>
  </section>
</main>'''
    doc = head + body + tail
    for bad in ("—", "–", "&mdash;", "&ndash;"):
        assert bad not in body, (page["file"], "dash in copy", bad)
    with open(os.path.join(SITE, page["file"]), "w") as f:
        f.write(doc)
    print(f"wrote {page['file']}")


def main():
    v = open(os.path.join(SITE, "contact.html")).read()
    head0, tail = v[:v.index("<main")], v[v.index("</main>") + len("</main>"):]
    tail = re.sub(r"<script>\n\(function\(\)\{\n  var f=document\.getElementById\('cform'\).*?</script>\n", "", tail, count=1, flags=re.S)
    assert "cform" not in tail, "contact form script left in the guide footer"
    for page in PAGES:
        build(page, head0, tail)


if __name__ == "__main__":
    main()
