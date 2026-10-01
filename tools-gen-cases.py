#!/usr/bin/env python3
"""Generate redherrings-site/cases.html from the live engine scenario metadata.

Produces the 3-axis taxonomy: Discipline (DF | IR) -> Difficulty -> topic row
(cert tracks for DF, ATT&CK tactics for IR). Keeps the site catalog in sync
with the real builtin library.
"""
import html
import sys
sys.path.insert(0, "/home/user/redherrings")
from redherrings import packs, tracks, attack  # noqa: E402

E = lambda s: html.escape(str(s or ""), quote=True)

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
        chips = "".join(f'<span class="chip trk-ir">{E(TACTICS.get(t, t))}</span>' for t in tactics_list[:4])
    else:
        chips = "".join(f'<span class="chip {TRACK_CHIP.get(t, ("", t))[0]}">{E(TRACK_CHIP.get(t, ("", t))[1])}</span>' for t in tracks_list)
    sub_html = f'\n      <div class="cc-sub">{E(sub)}</div>' if sub else ""
    return (
        f'    <article class="ccard" data-discipline="{E(disc)}" data-diff="{E(ed)}" '
        f'data-tracks="{E(" ".join(tracks_list))}" data-tactics="{E(" ".join(tactics_list))}">\n'
        f'      <div class="cc-top"><span class="dpill {pill_cls}">{E(pill_lbl)}</span>'
        f'<span class="cc-meta">{meta}</span></div>\n'
        f'      <h3 class="cc-title">{E(title)}</h3>{sub_html}\n'
        f'      <p class="cc-desc">{E(s.get("summary"))}</p>\n'
        f'      <div class="chips">{chips}</div>\n'
        f'    </article>'
    )


def main():
    scen = [s for s in packs.all_scenarios() if "id" in s and not s.get("error")]
    # Order: marquees first (showcase), then entry->expert ladder; IR after DF within a tier.
    scen.sort(key=lambda s: (0 if eff_diff(s) == "marquee" else 1,
                             DIFF_RANK.get(eff_diff(s), 9),
                             0 if s.get("discipline") != "incident-response" else 1,
                             s.get("name", "")))
    cards = "\n".join(card(s) for s in scen)
    n = len(scen)
    n_ir = sum(1 for s in scen if s.get("discipline") == "incident-response")
    n_df = n - n_ir

    import json
    diff_opts = "".join(f'<option value="{k}">{E(v)}</option>' for k, v in
                        [("first-look", "First Look"), ("easy", "Easy"), ("medium", "Medium"),
                         ("hard", "Hard"), ("expert", "Expert"), ("marquee", "Marquee")])
    tracks_json = json.dumps([{"v": sl, "l": lbl} for sl, (_, lbl) in TRACK_CHIP.items()])
    tactics_json = json.dumps([{"v": t["slug"], "l": t["label"]} for t in attack.catalog()])

    html_doc = TEMPLATE.format(
        n=n, n_df=n_df, n_ir=n_ir, cards=cards, diff_opts=diff_opts,
        tracks_json=tracks_json, tactics_json=tactics_json)
    html_doc = html_doc.replace("<<SP>>", " ")
    out = "/home/user/redherrings-site/cases.html"
    with open(out, "w") as f:
        f.write(html_doc)
    print(f"wrote {out}: {n} cases ({n_df} DF, {n_ir} IR)")


TEMPLATE = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>All Cases | Red Herrings DFIR Labs</title>
<meta name="description" content="Browse the full Red Herrings catalog of {n} digital forensics and incident response cases, across First Look, Easy, Medium, Hard, Expert and Marquee difficulty. Digital Forensics cases map to certification tracks (GCFE, GCFA, GNFA, GCFR); Incident Response cases map to MITRE ATT&CK tactics. Open any case to read its briefing and investigation questions.">
<link rel="canonical" href="https://redherrings.app/cases.html">
<meta name="robots" content="index,follow">
<meta name="theme-color" content="#E5382F">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 64 64%27%3E%3Cpath fill=%27%23E5382F%27 d=%27M6 32c9-11 20-16 30-16 4 0 8 3 12 9 3-3 8.5-9.5 14.25-13.25C58.38 18.12 55.69 25.81 54.44 32c1.25 6.19 3.94 13.87 7.81 20.25C56.5 48.5 51 42 48 39c-4 6-8 9-12 9-10 0-21-5-30-16z%27/%3E%3C/svg%3E">
<meta property="og:title" content="All Cases — Red Herrings">
<meta property="og:description" content="Every Red Herrings case: digital forensics across disk, registry, logs, memory, network, mobile and cloud, plus incident response mapped to MITRE ATT&CK.">
<meta property="og:url" content="https://redherrings.app/cases.html">
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
    <a class="link" href="/#pricing">Pricing</a>
    <a class="btn" href="/#download" data-goatcounter-click="cta-trial-nav">Start free trial</a>
  </div>
</header>
<main class="wrap">
  <div class="pagehead">
    <div class="crumb"><a href="/">Home</a> / Cases</div>
    <h1>The case library</h1>
    <p>{n} cases across two disciplines &mdash; <strong>Digital Forensics</strong> ({n_df}) and <strong>Incident Response</strong> ({n_ir}) &mdash; from single-artifact first-look triage to multi-hour capstones. Every case generates a different, auto-graded lab for each student. Filter by discipline, by difficulty, and by the certification path (forensics) or <a href="attack.html">MITRE ATT&amp;CK tactic</a> (incident response) it exercises.</p>
  </div>

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
    <div class="cta-row" style="margin-top:40px"><a class="btn" href="/#download">Start a free 14-day trial</a><a class="btn ghost" href="/#pricing">See pricing</a></div>
  </section>
</main>
<footer>
  <div class="wrap">
    <div class="fbottom">
      <span>&copy; 2026 Red Herrings, a product of The Competence Collective, LLC.</span>
      <span><a href="/">Home</a> &middot; <a href="help.html">Help</a> &middot; <a href="student-portal.html">Student portal</a> &middot; <a href="blog/">Blog</a> &middot; <a href="attack.html">ATT&amp;CK</a> &middot; <a href="/#pricing">Pricing</a> &middot; <a href="privacy.html">Privacy</a> &middot; <a href="terms.html">Terms</a> &middot; <a href="eula.html">EULA</a> &middot; <a href="refund.html">Refunds</a> &middot; <a href="mailto:sales@redherrings.app">sales@redherrings.app</a></span>
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
<script data-goatcounter="https://redherrings.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<script src="theme.js" defer></script>
</body>
</html>
'''

if __name__ == "__main__":
    main()
