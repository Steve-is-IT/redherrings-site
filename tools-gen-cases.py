#!/usr/bin/env python3
"""Generate redherrings-site/cases.html from the live engine scenario metadata.

Produces the 3-axis taxonomy: Discipline (DF | IR) -> Difficulty -> topic row
(cert tracks for DF, ATT&CK tactics for IR). Keeps the site catalog in sync
with the real builtin library.
"""
import html
import json
import sys
sys.path.insert(0, "/home/user/redherrings")
from redherrings import packs, tracks, attack, paths  # noqa: E402
from redherrings.engine.dsl import load_scenario  # noqa: E402
from redherrings.engine.variant import Variant  # noqa: E402

E = lambda s: html.escape(str(s or ""), quote=True)

EVIDENCE_LABEL = {
    "edr": "EDR detections", "siem": "SIEM alerts", "eventlog": "Windows event logs",
    "windows": "Windows artifacts", "memory": "Memory image", "network": "Packet capture",
    "mobile": "Mobile extraction", "cloud": "Cloud audit logs", "browser": "Browser history",
    "email": "Email / mailbox", "linux": "Linux host", "macos": "macOS host", "disk": "Disk image",
}

DIFF_RANK = {"first-look": 0, "easy": 1, "medium": 2, "hard": 3, "expert": 4, "marquee": 5}
DIFF_LABEL = {"first-look": "First Look", "easy": "Easy", "medium": "Medium",
              "hard": "Hard", "expert": "Expert", "marquee": "Marquee"}
DIFF_PILLCLASS = {"first-look": "cat-firstlook", "easy": "easy", "medium": "medium",
                  "hard": "hard", "expert": "expert", "marquee": "cat-marquee"}
TRACK_CHIP = {"foundations": ("trk-foundations", "Foundations"),
              "windows-forensics": ("trk-windows", "Windows Forensics"),
              "mobile-forensics": ("trk-mobile", "Mobile Forensics"),
              "network-forensics": ("trk-network", "Network Forensics"),
              "cloud": ("trk-cloud", "Cloud & SaaS"),
              "linux": ("trk-linux", "Linux Forensics"),
              "macos": ("trk-macos", "macOS Forensics"),
              "advanced-ir": ("trk-advanced", "Advanced Forensics & IR")}
TACTICS = {t["slug"]: t["label"] for t in attack.catalog()}


def eff_diff(s):
    return s.get("category") or s.get("difficulty") or "medium"


def _scenario_map():
    """id -> Scenario for every builtin case (for briefing + sample questions)."""
    out = {}
    for p in sorted(paths.builtin_scenarios_dir().glob("*.yaml")):
        try:
            sc = load_scenario(p)
            out[sc.id] = sc
        except Exception:
            pass
    return out


def _render_preview(sc, text):
    try:
        return Variant(sc.raw, {"id": "preview-001", "name": "Preview Student"}, "preview").render(text)
    except Exception:
        return text


def build_detail(meta, sc):
    """Public-facing detail payload for the lightbox: briefing + sample questions,
    with no answers or answer keys."""
    disc = meta.get("discipline", "digital-forensics")
    ir = disc == "incident-response"
    ed = eff_diff(meta)
    story = _render_preview(sc, sc.raw.get("story", "")) if sc else meta.get("summary", "")
    briefing = [p.replace("\n", " ").strip() for p in story.split("\n\n") if p.strip()]
    qs = []
    for q in (sc.questions if sc else [])[:6]:
        qs.append({"prompt": _render_preview(sc, q.prompt), "type": q.type,
                   "points": q.points, "phase": getattr(q, "phase", "")})
    total_q = len(sc.questions) if sc else meta.get("questions", 0)
    if ir:
        chips = [{"label": TACTICS.get(t, t), "cls": "tac-" + t} for t in (meta.get("tactics") or [])]
    else:
        chips = [{"label": TRACK_CHIP.get(t, ("", t))[1], "cls": TRACK_CHIP.get(t, ("", t))[0]} for t in (meta.get("tracks") or [])]
    return {
        "title": meta.get("codename") or meta.get("name"),
        "sub": meta.get("name") if meta.get("codename") else "",
        "disc": "Incident Response" if ir else "Digital Forensics",
        "discCls": "ir" if ir else "df",
        "diff": DIFF_LABEL.get(ed, ed.title()), "diffCls": DIFF_PILLCLASS.get(ed, ed),
        "est": meta.get("estimated_minutes"), "qcount": total_q, "points": round(meta.get("points") or 0),
        "evidence": [EVIDENCE_LABEL.get(a, a.title()) for a in (meta.get("artifact_types") or [])],
        "tools": meta.get("tools") or [], "chips": chips,
        "briefing": briefing, "questions": qs, "moreq": max(0, total_q - len(qs)),
    }


def card(s):
    disc = s.get("discipline", "digital-forensics")
    ir = disc == "incident-response"
    ed = eff_diff(s)
    pill_cls = DIFF_PILLCLASS.get(ed, ed)
    pill_lbl = DIFF_LABEL.get(ed, ed.title())
    qn, qtot = s.get("min_questions") or s.get("questions"), s.get("questions")
    qtxt = f"{qn}&ndash;{qtot} Q" if qn and qtot and qn != qtot else f"{qtot} Q"
    est = s.get("estimated_minutes")
    meta = qtxt + (f" &middot; ~{est} min" if est else "")
    title = s.get("codename") or s.get("name")
    sub = s.get("name") if s.get("codename") else ""
    tracks_list = s.get("tracks") or []
    tactics_list = s.get("tactics") or []
    if ir:
        chips = "".join(f'<span class="chip tac-{E(t)}">{E(TACTICS.get(t, t))}</span>' for t in tactics_list[:4])
    else:
        chips = "".join(f'<span class="chip {TRACK_CHIP.get(t, ("", t))[0]}">{E(TRACK_CHIP.get(t, ("", t))[1])}</span>' for t in tracks_list)
    sub_html = f'\n      <div class="cc-sub">{E(sub)}</div>' if sub else ""
    return (
        f'    <article class="ccard" id="{E(s.get("id"))}" data-id="{E(s.get("id"))}" tabindex="0" role="button" '
        f'aria-label="Open {E(title)}" data-discipline="{E(disc)}" data-diff="{E(ed)}" '
        f'data-tracks="{E(" ".join(tracks_list))}" data-tactics="{E(" ".join(tactics_list))}">\n'
        f'      <div class="cc-top"><span class="dpill {pill_cls}">{E(pill_lbl)}</span>'
        f'<span class="cc-meta">{meta}</span></div>\n'
        f'      <h3 class="cc-title">{E(title)}</h3>{sub_html}\n'
        f'      <p class="cc-desc">{E(s.get("summary"))}</p>\n'
        f'      <div class="chips">{chips}</div>\n'
        f'      <span class="cc-more">View case &amp; sample questions &rarr;</span>\n'
        f'    </article>'
    )


def featured_block(scen):
    """One wide card showing off a Marquee case. Every marquee is emitted; the
    page script shows one and rotates to the next on each visit or on Next."""
    ms = [s for s in scen if eff_diff(s) == "marquee"]
    if not ms:
        return ""
    slots = []
    for i, s in enumerate(ms):
        disc = "Incident Response" if s.get("discipline") == "incident-response" else "Digital Forensics"
        est = s.get("estimated_minutes")
        meta = f'{s.get("questions")} questions' + (f' &middot; ~{est} min' if est else "") + f' &middot; {disc}'
        slots.append(
            f'  <article class="feature-wide marquee fm-slot" data-i="{i}"{"" if i == 0 else " hidden"}>\n'
            f'    <div>\n'
            f'      <p class="fw-kick gold">Featured Marquee case</p>\n'
            f'      <h3>{E(s.get("codename") or s.get("name"))}</h3>\n'
            + (f'      <div class="cc-sub" style="margin:-4px 0 8px">{E(s.get("name"))}</div>\n' if s.get("codename") else "")
            + f'      <p>{E(s.get("summary"))}</p>\n'
            f'      <p class="fm-meta">{meta}</p>\n'
            f'    </div>\n'
            f'    <div class="fw-aside fm-actions">\n'
            f'      <a class="btn" href="#{E(s.get("id"))}">View case</a>\n'
            + ('      <button type="button" class="btn ghost fm-next">Next marquee</button>\n' if len(ms) > 1 else "")
            + f'    </div>\n'
            f'  </article>')
    return '  <div class="fm-wrap">\n' + "\n".join(slots) + '\n  </div>\n'


def main():
    scen = [s for s in packs.all_scenarios() if "id" in s and not s.get("error")]
    # Order: the difficulty ladder, first-look through marquee, the same order the
    # app's Case Library uses; IR after DF within a tier.
    scen.sort(key=lambda s: (DIFF_RANK.get(eff_diff(s), 9),
                             0 if s.get("discipline") != "incident-response" else 1,
                             s.get("name", "")))
    cards = "\n".join(card(s) for s in scen)
    featured = featured_block(scen)
    n = len(scen)
    n_ir = sum(1 for s in scen if s.get("discipline") == "incident-response")
    n_df = n - n_ir

    smap = _scenario_map()
    details = {s["id"]: build_detail(s, smap.get(s["id"])) for s in scen}

    diff_opts = "".join(f'<option value="{k}">{E(v)}</option>' for k, v in
                        [("first-look", "First Look"), ("easy", "Easy"), ("medium", "Medium"),
                         ("hard", "Hard"), ("expert", "Expert"), ("marquee", "Marquee")])
    tracks_json = json.dumps([{"v": sl, "l": lbl} for sl, (_, lbl) in TRACK_CHIP.items()])
    tactics_json = json.dumps([{"v": t["slug"], "l": t["label"]} for t in attack.catalog()])
    details_json = json.dumps(details)

    html_doc = TEMPLATE.format(
        featured=featured,
        n=n, n_df=n_df, n_ir=n_ir, cards=cards, diff_opts=diff_opts,
        tracks_json=tracks_json, tactics_json=tactics_json, details_json=details_json)
    html_doc = html_doc.replace("<<SP>>", " ")
    html_doc = html_doc.replace("<!--MODALJS-->", MODAL_JS.replace("__DATA__", details_json))
    out = "/home/user/redherrings-site/cases.html"
    with open(out, "w") as f:
        f.write(html_doc)
    print(f"wrote {out}: {n} cases ({n_df} DF, {n_ir} IR)")


TEMPLATE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Digital Forensics &amp; Incident Response Practice Cases with Answer Keys | Red Herrings</title>
<meta name="description" content="Dozens of digital forensics and incident response cases, from First Look triage to Marquee capstones. Forensics aligned to GCFE, GCFA, GNFA and GCFR; incident response mapped to MITRE ATT&CK.">
<link rel="canonical" href="https://redherrings.app/cases.html">
<meta name="robots" content="index,follow">
<meta name="theme-color" content="#D32F26">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 64 64%27%3E%3Cpath fill=%27%23E5382F%27 d=%27M6 32c9-11 20-16 30-16 4 0 8 3 12 9 3-3 8.5-9.5 14.25-13.25C58.38 18.12 55.69 25.81 54.44 32c1.25 6.19 3.94 13.87 7.81 20.25C56.5 48.5 51 42 48 39c-4 6-8 9-12 9-10 0-21-5-30-16z%27/%3E%3C/svg%3E">
<link rel="icon" type="image/png" sizes="32x32" href="/img/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/img/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta property="og:title" content="Case library | Red Herrings">
<meta property="og:description" content="Dozens of forensics and incident response cases, First Look to Marquee capstone. Every student gets their own variant, graded against its own key.">
<meta property="og:url" content="https://redherrings.app/cases.html">
<meta property="og:image" content="https://redherrings.app/img/og/cases-4b047723.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Red Herrings case library: dozens of DFIR cases, one variant per student.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://redherrings.app/img/og/cases-4b047723.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Public+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap">
<link rel="stylesheet" href="site.css">
</head>
<body>
<header>
  <a class="skip" href="#main">Skip to content</a>
  <div class="wrap nav">
    <a class="brand" href="/" aria-label="Red Herrings home">
      <svg width="28" height="28" viewBox="5.1 3 58 58" aria-hidden="true"><path fill-rule="evenodd" d="M6 32c9-11 20-16 30-16C40 16 44 19 48 25C51 22 56.5 15.5 62.25 11.75C58.38 18.12 55.69 25.81 54.44 32C55.69 38.19 58.38 45.88 62.25 52.25C56.5 48.5 51 42 48 39C44 45 40 48 36 48c-10 0-21-5-30-16z M20 24.8a5.6 5.6 0 1 0 0 11.2 5.6 5.6 0 1 0 0-11.2z" fill="var(--accent)"/><circle cx="20" cy="30.4" r="3.2" fill="none" stroke="var(--accent)" stroke-width="2"/><path d="M23 33.4l4 4" stroke="var(--accent)" stroke-width="2.6" stroke-linecap="round"/></svg>
      <span style="color:var(--ink)">Red Herrings</span>
    </a>
    <nav class="mainnav" aria-label="Primary">
      <div class="mnitem haspanel"><button type="button" class="mntrig" aria-expanded="false">Platform <svg class="mncaret" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M2 3.5L5 6.5L8 3.5"/></svg></button><div class="megapanel"><div class="mpcols"><div class="mpcol"><div class="mphead">Product</div><a class="mlink" href="/how.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h18v14H3z"/><path d="M8 21h8M12 17v4"/></svg></span><span><span class="mt">How it works</span><span class="md">One case, a different variant for every student</span></span></a><a class="mlink" href="/cases.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16v12H4z"/><path d="M9 7V5h6v2"/></svg></span><span><span class="mt">Case library</span><span class="md">Dozens of verified forensics and IR cases</span></span></a><a class="mlink" href="/packs.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7h14l-1 13H6zM9 7a3 3 0 0 1 6 0"/></svg></span><span><span class="mt">Scenario packs</span><span class="md">Add-on case sets, one-click install</span></span></a></div><div class="mpcol"><div class="mphead">Teaching</div><a class="mlink" href="/pathways.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 20V9a3 3 0 0 1 3-3h8M16 3l4 3-4 3"/></svg></span><span><span class="mt">Learning pathways</span><span class="md">From First Look to cert-prep capstone</span></span></a><a class="mlink" href="/courses.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">Course packs</span><span class="md">A 14-week DF and an 8-week IR syllabus, ready to run</span></span></a><a class="mlink" href="/student-portal.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v12H4zM2 21h20"/></svg></span><span><span class="mt">Student portal &amp; LMS</span><span class="md">Solve in the browser, auto-grade, LTI passback</span></span></a></div></div><a class="mppromo" href="/try.html"><span class="eye">Try it live</span><strong>Work two cases in your browser</strong><span class="pd">An EDR alert and a USB registry key. Press a button to see another student&rsquo;s variant. Nothing to install.</span><span class="pc"><span>EDR alert</span><span>USB registry</span></span><span class="go">Open the demo &rarr;</span></a></div></div><div class="mnitem haspanel"><button type="button" class="mntrig" aria-expanded="false">Solutions <svg class="mncaret" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M2 3.5L5 6.5L8 3.5"/></svg></button><div class="megapanel nopromo"><div class="mpcols"><div class="mpcol"><div class="mphead">Who it is for</div><a class="mlink" href="/#pricing"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">Educators</span><span class="md">One instructor, auto-graded labs</span></span></a><a class="mlink" href="/#pricing"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">Departments</span><span class="md">Several instructors, every case</span></span></a><a class="mlink" href="/programs.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">College and university programs</span><span class="md">Labs, syllabi and procurement for departments</span></span></a><a class="mlink" href="/#pricing"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v12H4zM2 21h20"/></svg></span><span><span class="mt">Students</span><span class="md">Self-practice at the personal rate</span></span></a></div><div class="mpcol"><div class="mphead">Organizations</div><a class="mlink" href="/security-teams.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0M17 11a3 3 0 0 0 0-6M21 20a6 6 0 0 0-5-5.9"/></svg></span><span><span class="mt">Security teams &amp; training</span><span class="md">45-minute incident drills, per seat</span></span></a><a class="mlink" href="/contact.html?topic=enterprise"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7h14l-1 13H6zM9 7a3 3 0 0 1 6 0"/></svg></span><span><span class="mt">Enterprise &amp; government</span><span class="md">White-label, volume, procurement</span></span></a></div></div></div></div><div class="mnitem haspanel"><button type="button" class="mntrig" aria-expanded="false">Resources <svg class="mncaret" viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M2 3.5L5 6.5L8 3.5"/></svg></button><div class="megapanel nopromo"><div class="mpcols"><div class="mpcol"><div class="mphead">Learn</div><a class="mlink" href="/help.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-1 .5-1 1.2-1 2M12 17h.01"/></svg></span><span><span class="mt">Getting started</span><span class="md">Install, activate and run your first lab</span></span></a><a class="mlink" href="/tools.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 7a4 4 0 0 1-5 5l-6 6 2 2 6-6a4 4 0 0 1 5-5z"/></svg></span><span><span class="mt">Tool setup</span><span class="md">Autopsy, Volatility, Wireshark and more</span></span></a><a class="mlink" href="/resources.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h10l4 4v14H5zM14 3v5h5"/></svg></span><span><span class="mt">Free resources</span><span class="md">Forms, checklists, rubrics and syllabi</span></span></a><a class="mlink" href="/blog/"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h10l4 4v14H5zM14 3v5h5"/></svg></span><span><span class="mt">Blog</span><span class="md">DFIR teaching notes and updates</span></span></a></div><div class="mpcol"><div class="mphead">Evaluate</div><a class="mlink" href="/sample.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="12" r="4"/><path d="M12 12h9l-2 2 2 2M11.5 12H21"/></svg></span><span><span class="mt">Sample lab</span><span class="md">A full case ZIP with its verified answer key</span></span></a><a class="mlink" href="/compare.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z"/></svg></span><span><span class="mt">Compare</span><span class="md">Hand-built labs, public images, ranges and us</span></span></a><a class="mlink" href="/attack.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z"/></svg></span><span><span class="mt">ATT&amp;CK coverage</span><span class="md">Which techniques the cases exercise</span></span></a><a class="mlink" href="/trust.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 3v6c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V6z"/></svg></span><span><span class="mt">Trust &amp; security</span><span class="md">Runs locally; no student data leaves</span></span></a><a class="mlink" href="/#faq"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-1 .5-1 1.2-1 2M12 17h.01"/></svg></span><span><span class="mt">FAQ</span><span class="md">Licensing, platforms, classroom use</span></span></a></div></div></div></div>
      <a class="mnitem mnflat" href="/#pricing">Pricing</a>
    </nav>
    <div class="spacer"></div>
    <a class="link navutil" href="https://account.redherrings.app/account" data-goatcounter-click="signin">Sign in</a>
    <a class="btn navcta" href="/download.html" data-goatcounter-click="cta-trial-nav">Start free trial</a>
    <button type="button" class="navburger" aria-label="Open menu" aria-expanded="false" aria-controls="mobilenav"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button>
  </div>
  <div class="mobilenav" id="mobilenav" hidden>
    <a class="btn" href="/download.html" data-goatcounter-click="cta-trial-nav" style="display:flex;justify-content:center;margin-bottom:6px">Start free trial</a>
    <div class="mnsection"><div class="mnsh">Platform</div><a class="mlink" href="/how.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h18v14H3z"/><path d="M8 21h8M12 17v4"/></svg></span><span><span class="mt">How it works</span><span class="md">One case, a different variant for every student</span></span></a><a class="mlink" href="/cases.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16v12H4z"/><path d="M9 7V5h6v2"/></svg></span><span><span class="mt">Case library</span><span class="md">Dozens of verified forensics and IR cases</span></span></a><a class="mlink" href="/packs.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7h14l-1 13H6zM9 7a3 3 0 0 1 6 0"/></svg></span><span><span class="mt">Scenario packs</span><span class="md">Add-on case sets, one-click install</span></span></a><a class="mlink" href="/pathways.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 20V9a3 3 0 0 1 3-3h8M16 3l4 3-4 3"/></svg></span><span><span class="mt">Learning pathways</span><span class="md">From First Look to cert-prep capstone</span></span></a><a class="mlink" href="/courses.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">Course packs</span><span class="md">A 14-week DF and an 8-week IR syllabus, ready to run</span></span></a><a class="mlink" href="/student-portal.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v12H4zM2 21h20"/></svg></span><span><span class="mt">Student portal &amp; LMS</span><span class="md">Solve in the browser, auto-grade, LTI passback</span></span></a></div><div class="mnsection"><div class="mnsh">Solutions</div><a class="mlink" href="/#pricing"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">Educators</span><span class="md">One instructor, auto-graded labs</span></span></a><a class="mlink" href="/#pricing"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">Departments</span><span class="md">Several instructors, every case</span></span></a><a class="mlink" href="/programs.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-5 9 5-9 5zM7 11v5c0 1 2.5 2 5 2s5-1 5-2v-5"/></svg></span><span><span class="mt">College and university programs</span><span class="md">Labs, syllabi and procurement for departments</span></span></a><a class="mlink" href="/#pricing"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h16v12H4zM2 21h20"/></svg></span><span><span class="mt">Students</span><span class="md">Self-practice at the personal rate</span></span></a><a class="mlink" href="/security-teams.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0M17 11a3 3 0 0 0 0-6M21 20a6 6 0 0 0-5-5.9"/></svg></span><span><span class="mt">Security teams &amp; training</span><span class="md">45-minute incident drills, per seat</span></span></a><a class="mlink" href="/contact.html?topic=enterprise"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 7h14l-1 13H6zM9 7a3 3 0 0 1 6 0"/></svg></span><span><span class="mt">Enterprise &amp; government</span><span class="md">White-label, volume, procurement</span></span></a></div><div class="mnsection"><div class="mnsh">Resources</div><a class="mlink" href="/help.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-1 .5-1 1.2-1 2M12 17h.01"/></svg></span><span><span class="mt">Getting started</span><span class="md">Install, activate and run your first lab</span></span></a><a class="mlink" href="/tools.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14 7a4 4 0 0 1-5 5l-6 6 2 2 6-6a4 4 0 0 1 5-5z"/></svg></span><span><span class="mt">Tool setup</span><span class="md">Autopsy, Volatility, Wireshark and more</span></span></a><a class="mlink" href="/resources.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h10l4 4v14H5zM14 3v5h5"/></svg></span><span><span class="mt">Free resources</span><span class="md">Forms, checklists, rubrics and syllabi</span></span></a><a class="mlink" href="/blog/"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3h10l4 4v14H5zM14 3v5h5"/></svg></span><span><span class="mt">Blog</span><span class="md">DFIR teaching notes and updates</span></span></a><a class="mlink" href="/sample.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="12" r="4"/><path d="M12 12h9l-2 2 2 2M11.5 12H21"/></svg></span><span><span class="mt">Sample lab</span><span class="md">A full case ZIP with its verified answer key</span></span></a><a class="mlink" href="/compare.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z"/></svg></span><span><span class="mt">Compare</span><span class="md">Hand-built labs, public images, ranges and us</span></span></a><a class="mlink" href="/attack.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z"/></svg></span><span><span class="mt">ATT&amp;CK coverage</span><span class="md">Which techniques the cases exercise</span></span></a><a class="mlink" href="/trust.html"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 3v6c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V6z"/></svg></span><span><span class="mt">Trust &amp; security</span><span class="md">Runs locally; no student data leaves</span></span></a><a class="mlink" href="/#faq"><span class="mi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-1 .5-1 1.2-1 2M12 17h.01"/></svg></span><span><span class="mt">FAQ</span><span class="md">Licensing, platforms, classroom use</span></span></a></div>
    <div class="mnsection"><a class="mnflat mnsolo" href="/#pricing">Pricing</a></div>
    <div class="mnrow">
      <a class="btn ghost" href="https://account.redherrings.app/account" data-goatcounter-click="signin">Sign in</a>
      <a class="btn ghost" href="/student-portal.html">Student portal</a>
    </div>
  </div>
</header>
<main class="wrap" id="main">
  <div class="crumb" style="margin-bottom:10px"><a href="/">Home</a> / Cases</div>
  <div class="secthead">
    <h1 class="opener">Dozens of forensics and incident response cases <em>for the classroom</em></h1>
    <p class="osub">Dozens of cases across two disciplines, <strong>Digital Forensics</strong> and <strong>Incident Response</strong>, from single-artifact First Look triage to multi-hour capstones. Every case generates a different, auto-graded lab for each student. Filter by discipline, by difficulty, and by the certification path (forensics) or <a href="attack.html">MITRE ATT&amp;CK tactic</a> (incident response) it exercises.</p>
  </div>
{featured}
  <section style="border-top:0;padding-top:24px">
    <div class="filterrow">
      <label class="fsel"><span class="fsel-l">Discipline</span>
        <select id="fDisc">
          <option value="all">All disciplines</option>
          <option value="digital-forensics">Digital Forensics</option>
          <option value="incident-response">Incident Response</option>
        </select></label>
      <label class="fsel"><span class="fsel-l">Difficulty</span>
        <select id="fDiff"><option value="all">All difficulty</option>{diff_opts}</select></label>
      <label class="fsel"><span class="fsel-l" id="fTopicLabel">Cert path</span>
        <select id="fTopic"><option value="all">All paths</option></select></label>
      <button type="button" class="fclear" id="clearf">Clear</button>
    </div>
    <p class="note" id="catcount" style="margin-top:14px"></p>
    <div class="caselist" id="caselist">
{cards}
    </div>
    <p class="emptymsg hide" id="empty">No cases match those filters. Use <strong>Clear</strong> to reset.</p>
    <div class="cta-row" style="margin-top:40px"><a class="btn" href="/download.html">Start a free 30-day trial</a><a class="btn ghost" href="/#pricing">See pricing</a></div>
  </section>
</main>
<div class="cmodal" id="cmodal" hidden>
  <div class="cmodal-backdrop" data-close></div>
  <div class="cmodal-panel" role="dialog" aria-modal="true" aria-labelledby="cm-title">
    <button class="cmodal-x" data-close aria-label="Close">&times;</button>
    <div class="cmodal-body" id="cmodal-body"></div>
  </div>
</div>
<footer>
  <div class="wrap">
    <div class="ftop">
      <div class="fbrand">
        <div class="brand"><a href="/" aria-label="Red Herrings home" style="display:inline-flex;align-items:center;gap:8px;text-decoration:none"><svg width="22" height="22" viewBox="5.1 3 58 58" aria-hidden="true"><path fill-rule="evenodd" d="M6 32c9-11 20-16 30-16C40 16 44 19 48 25C51 22 56.5 15.5 62.25 11.75C58.38 18.12 55.69 25.81 54.44 32C55.69 38.19 58.38 45.88 62.25 52.25C56.5 48.5 51 42 48 39C44 45 40 48 36 48c-10 0-21-5-30-16z M20 24.8a5.6 5.6 0 1 0 0 11.2 5.6 5.6 0 1 0 0-11.2z" fill="var(--accent)"/><circle cx="20" cy="30.4" r="3.2" fill="none" stroke="var(--accent)" stroke-width="2"/><path d="M23 33.4l4 4" stroke="var(--accent)" stroke-width="2.6" stroke-linecap="round"/></svg><span style="font-size:16px">Red Herrings</span></a></div>
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
  var TRACKS={tracks_json};
  var TACTICS={tactics_json};
  var cards=[].slice.call(document.querySelectorAll(".ccard"));
  var fDisc=document.getElementById("fDisc"), fDiff=document.getElementById("fDiff"),
      fTopic=document.getElementById("fTopic"), fTopicLabel=document.getElementById("fTopicLabel");
  function isIR()<<SP>>{{ return fDisc.value==="incident-response"; }}
  function fillTopic()<<SP>>{{
    var ir=isIR(), items=ir?TACTICS:TRACKS;
    fTopicLabel.textContent = ir ? "ATT&CK tactic" : "Cert path";
    var opts='<option value="all">'+(ir?"All tactics":"All paths")+'</option>';
    items.forEach(function(o)<<SP>>{{ opts+='<option value="'+o.v+'">'+o.l+'</option>'; }});
    fTopic.innerHTML=opts; fTopic.value="all";
  }}
  function apply()<<SP>>{{
    var disc=fDisc.value, diff=fDiff.value, topic=fTopic.value, ir=isIR(), shown=0;
    cards.forEach(function(c)<<SP>>{{
      var okdisc = disc==="all" || c.dataset.discipline===disc;
      var okd = diff==="all" || c.dataset.diff===diff;
      var field = ir ? c.dataset.tactics : c.dataset.tracks;
      var okt = topic==="all" || (" "+field+" ").indexOf(" "+topic+" ")>=0;
      var vis = okdisc && okd && okt; c.classList.toggle("hide", !vis); if(vis) shown++;
    }});
    document.getElementById("empty").classList.toggle("hide", shown>0);
    document.getElementById("catcount").textContent = (shown===cards.length ? cards.length+" cases" : shown+" of "+cards.length+" cases");
  }}
  fDisc.addEventListener("change", function()<<SP>>{{ fillTopic(); apply(); }});
  fDiff.addEventListener("change", apply);
  fTopic.addEventListener("change", apply);
  document.getElementById("clearf").addEventListener("click", function()<<SP>>{{
    fDisc.value="all"; fDiff.value="all"; fillTopic(); apply(); }});
  fillTopic(); apply();
</script>
<!--MODALJS-->
<script data-goatcounter="https://redherrings.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<script src="nav.js" defer></script>
</body>
</html>
'''

MODAL_JS = r'''<script>
(function(){
  var CASES = __DATA__;
  var modal=document.getElementById("cmodal"), body=document.getElementById("cmodal-body"), lastFocus=null;
  function esc(s){ var d=document.createElement("div"); d.textContent=(s==null?"":String(s)); return d.innerHTML; }
  function openCase(id){
    var c=CASES[id]; if(!c) return;
    var chips=(c.chips||[]).map(function(x){return '<span class="chip '+x.cls+'">'+esc(x.label)+'</span>';}).join("");
    var meta=[]; if(c.est)meta.push("~"+c.est+" min"); meta.push(c.qcount+" questions"); if(c.points)meta.push(c.points+" points");
    var ev=(c.evidence||[]).map(function(x){return '<span class="chip">'+esc(x)+'</span>';}).join("");
    var tools=(c.tools||[]).map(function(x){return '<span class="chip tool">'+esc(x)+'</span>';}).join("");
    var brief=(c.briefing||[]).map(function(p){return '<p>'+esc(p)+'</p>';}).join("");
    var qs=(c.questions||[]).map(function(q){
      var ph=q.phase?' &middot; '+esc(q.phase.replace(/-/g," ")):"";
      return '<li><span class="cm-qtext">'+esc(q.prompt)+'</span><span class="cm-qmeta">'+esc(q.type)+' &middot; '+q.points+' pts'+ph+'</span></li>';
    }).join("");
    var more=c.moreq>0?'<p class="cm-note">+ '+c.moreq+' more questions in the full case: you choose how many each student gets, drawn as a unique set per student.</p>':"";
    body.innerHTML =
      '<div class="cm-head"><span class="dpill '+c.diffCls+'">'+esc(c.diff)+'</span>'+
        '<span class="cm-disc disc-'+c.discCls+'">'+esc(c.disc)+'</span></div>'+
      '<h2 id="cm-title">'+esc(c.title)+'</h2>'+(c.sub?'<p class="cm-sub">'+esc(c.sub)+'</p>':"")+
      '<p class="cm-meta">'+meta.join(" &middot; ")+'</p>'+
      (chips?'<div class="chips cm-chips">'+chips+'</div>':"")+
      '<h3>Briefing</h3>'+(brief||'<p class="cm-note">No briefing preview.</p>')+
      '<h3>Sample questions</h3><ol class="cm-q">'+qs+'</ol>'+more+
      (ev?'<h3>Evidence</h3><div class="chips">'+ev+'</div>':"")+
      (tools?'<h3>Suggested tools</h3><div class="chips">'+tools+'</div>':"")+
      '<div class="cta-row cm-cta"><a class="btn" href="/download.html">Start a free trial</a><a class="btn ghost" href="/#pricing">See pricing</a></div>';
    lastFocus=document.activeElement; modal.hidden=false; document.body.style.overflow="hidden";
    body.scrollTop=0; modal.querySelector(".cmodal-x").focus();
  }
  function closeCase(){ modal.hidden=true; document.body.style.overflow=""; if(lastFocus&&lastFocus.focus)lastFocus.focus(); }
  [].forEach.call(document.querySelectorAll(".ccard"), function(c){
    c.addEventListener("click", function(){ openCase(c.dataset.id); });
    c.addEventListener("keydown", function(e){ if(e.key==="Enter"||e.key===" "){ e.preventDefault(); openCase(c.dataset.id); } });
  });
  modal.addEventListener("click", function(e){ if(e.target.hasAttribute("data-close")) closeCase(); });
  document.addEventListener("keydown", function(e){ if(e.key==="Escape"&&!modal.hidden) closeCase(); });
  // Deep links: /cases.html#<case-id> scrolls to the card and opens its detail.
  function openFromHash(){
    var id=(location.hash||"").replace(/^#/,""); if(!id||!CASES[id]) return;
    var card=document.getElementById(id);
    if(card){ card.scrollIntoView({block:"center"}); card.classList.add("linked"); }
    openCase(id);
  }
  window.addEventListener("hashchange", openFromHash);
  openFromHash();
  // Featured Marquee slot: show one, rotate on each visit and on Next.
  var slots=[].slice.call(document.querySelectorAll(".fm-slot"));
  if(slots.length>1){
    var idx=0; try{ idx=(parseInt(localStorage.getItem("rh-fm")||"0",10)||0)%slots.length; localStorage.setItem("rh-fm",String(idx+1)); }catch(e){}
    function showSlot(i){ slots.forEach(function(s,j){ s.hidden=(j!==i); }); }
    showSlot(idx);
    slots.forEach(function(s){ var b=s.querySelector(".fm-next"); if(b) b.addEventListener("click", function(){ idx=(idx+1)%slots.length; showSlot(idx); try{localStorage.setItem("rh-fm",String(idx+1));}catch(e){} }); });
  }
})();
</script>'''

if __name__ == "__main__":
    main()
