#!/usr/bin/env python3
"""Site corrections to product text the cases don't back up.

tools-gen-courses.py, tools-gen-pathways.py, tools-gen-guides.py and
tools-gen-cases.py publish course, pathway and case text straight from the
product. Where that text says something a case's evidence or questions don't
hold, an entry here swaps it on the site (pages and syllabus PDFs).

Each swap is an exact substring of the product's current text, so it only
applies while the product still says it. Once the product's wording changes the
entry stops matching, the generator prints it as stale, and it can be deleted.
Not a script: the generators import it.
"""
import sys

# kind -> key -> [(product text, site text)]
#   course        key: course slug; every string in the course and its weeks
#   standard      key: "*"; the policy and structure text every syllabus carries
#   pathway-note  key: case id; that case's step note in every pathway
#   pathway-blurb key: pathway slug; the one-line blurb on its cards
#   case-summary  key: case id; the summary on its card and in course weeks
#   case-story    key: case id; a paragraph of the briefing preview on cases.html
#   syllabus      key: "*"; text the syllabus PDF renderer writes itself
FIXES = {
    "course": {
        "incident-response-fundamentals-8": [
            # The final case's questions cover detection, containment and
            # eradication; none is tagged recovery or post-incident.
            ("to running a ransomware incident through every NIST 800-61 phase.",
             "to running a ransomware incident from first alert to containment, eradication and the breach report."),
            # Week 2: all five alerts in ir-first-look-siem are one chain on one
            # user and host, so there's no noise to dismiss.
            ("Separate a true positive from noise.",
             "Tie the alerts to one intrusion by host, user and time."),
            ("a one-line triage note per alert: true positive, benign, or needs more data.",
             "a one-line triage note per alert that ties it to the others by host, user or time."),
            ("Most of the queue is noise by design; grade the dismissals as carefully as the escalation.",
             "Every alert in this queue belongs to one intrusion; grade whether students tie them together "
             "by host, user and time and escalate the critical one."),
            # Week 8: ir-ransomware-dawn has detection, containment and
            # eradication questions and none tagged recovery.
            ("Run a live ransomware chain through detection, containment, eradication and recovery.",
             "Run a live ransomware chain through detection, containment and eradication."),
            # Course outcome: the cases' questions stop at eradication.
            ("Choose and justify containment, eradication and recovery actions.",
             "Choose and justify containment and eradication actions."),
        ],
    },
    "standard": {},
    "syllabus": {
        "*": [
            # The portal serves no evidence: the zip carries it, and the portal
            # link is where students answer. Courses generates every week with
            # the portal on, so each student gets both.
            ("handed out as a ZIP or through a private portal link each week.",
             "handed out as a ZIP each week, with a private portal link to answer in."),
            ("hand out the student ZIPs or the private portal links.",
             "hand out the student ZIPs and the private portal links."),
            # The syllabi are CC BY-NC-SA 4.0 (the CLARK .docx footers say so).
            ("Syllabus text, policies and the rubric may be copied into institutional templates without attribution.",
             "Syllabus text, policies and the rubric are licensed CC BY-NC-SA 4.0. You may copy them into "
             "institutional templates with attribution to The Competence Collective, LLC."),
        ],
    },
    "pathway-note": {
        # One text/plain phish with a link; no attachment or payload.
        "easy-phish-triage": [("Work a reported phish: header, link and payload.",
                               "Work a reported phish: headers, sender and link.")],
        # Nightfall's questions cover detection, containment and eradication.
        "ir-marquee-nightfall": [("Capstone: run a hospital-wide incident through every NIST phase.",
                                  "Capstone: run a hospital-wide incident from detection to eradication, then write the report.")],
    },
    "pathway-blurb": {
        # None of the five cases asks a recovery question; the last phase any
        # of them reaches is eradication.
        "ransomware-ir": [("from initial access to double-extortion and recovery.",
                           "from initial access through a double-extortion demand to containment and eradication.")],
    },
    "case-story": {},
    "case-summary": {},
}

# Tools a case's questions tell students to use that its tools list leaves out
# (case id -> tools). Added to the list on the site; once the product lists a
# tool itself, the entry is reported as stale.
TOOLS_ADD = {}

_hits = set()


def tools(cid, current):
    """The case's tools list with the tools its questions name added."""
    out = list(current or [])
    have = {t.lower() for t in out}
    for t in TOOLS_ADD.get(cid, []):
        if t.lower() in have:
            continue
        out.append(t)
        _hits.add(("tools", cid, t))
    return out


def fix(kind, key, text):
    """Apply the swaps for (kind, key) to one string."""
    if not isinstance(text, str):
        return text
    for old, new in FIXES.get(kind, {}).get(key, []):
        if old in text:
            text = text.replace(old, new)
            _hits.add((kind, key, old))
    return text


def fix_tree(kind, key, obj):
    """fix() on every string inside nested dicts, lists and tuples."""
    if isinstance(obj, str):
        return fix(kind, key, obj)
    if isinstance(obj, list):
        return [fix_tree(kind, key, x) for x in obj]
    if isinstance(obj, tuple):
        return tuple(fix_tree(kind, key, x) for x in obj)
    if isinstance(obj, dict):
        return {k: fix_tree(kind, key, v) for k, v in obj.items()}
    return obj


def report(*kinds):
    """Print the swaps of these kinds that matched nothing in this run."""
    if "tools" in kinds:
        for cid, names in TOOLS_ADD.items():
            for t in names:
                if ("tools", cid, t) not in _hits:
                    print(f"tools-product-text: stale tools entry for {cid}, the product already lists {t}",
                          file=sys.stderr)
    for kind in kinds:
        for key, pairs in FIXES.get(kind, {}).items():
            for old, _ in pairs:
                if (kind, key, old) not in _hits:
                    print(f"tools-product-text: stale {kind} swap for {key}, the product no longer says {old[:70]!r}",
                          file=sys.stderr)
