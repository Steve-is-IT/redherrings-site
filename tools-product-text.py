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
#   case-summary  key: case id; the summary on its card and in course weeks
FIXES = {
    "course": {
        "incident-response-fundamentals-8": [
            # Week 2: all five alerts in ir-first-look-siem are one chain on one
            # user and host, so there's no noise to dismiss.
            ("Separate a true positive from noise.",
             "Tie the alerts to one intrusion by host, user and time."),
            ("a one-line triage note per alert: true positive, benign, or needs more data.",
             "a one-line triage note per alert that ties it to the others by host, user or time."),
            ("Most of the queue is noise by design; grade the dismissals as carefully as the escalation.",
             "Every alert in this queue belongs to one intrusion; grade whether students tie them together "
             "by host, user and time and escalate the critical one."),
            # Week 4: ir-phish-to-foothold has delivery, execution and a C2
            # beacon, and no persistence.
            ("Follow a phish through delivery, execution and persistence.",
             "Follow a phish through delivery, execution and command and control."),
        ],
        "intro-digital-forensics-14": [
            # hard-credential-theft is one workstation's logs, memory and capture.
            ("Work a multi-host intrusion end to end.",
             "Trace a stolen service account from one workstation to the server it reached."),
            ("a timed capstone on a multi-host intrusion",
             "a timed capstone on a credential theft traced from one workstation"),
            ("A 120-minute timed exam on a multi-host credential-theft intrusion.",
             "A 120-minute timed exam on a credential theft traced from one workstation."),
        ],
    },
    "standard": {
        "*": [
            # Most answers change per student; technique IDs, severities and
            # judgment calls are the same for the class.
            ("different names, hosts, timestamps and answers, generated from the same story.",
             "different names, hosts and timestamps, and most answers, generated from the same story."),
            # The collusion report compares the keys handed out; it never reads
            # a submission.
            ("is flagged by the collusion report and treated as academic misconduct.",
             "is treated as academic misconduct."),
        ],
    },
    "pathway-note": {
        # The case ships the Entra sign-in log, a mailbox, browser history and a
        # phone extraction; no workstation event log.
        "mfa-fatigue": [("Workstation event logs, mail and a phone on an off-hours login.",
                         "Entra sign-in log, mail, browser history and a phone on an off-hours login.")],
        # One text/plain phish with a link; no attachment or payload.
        "easy-phish-triage": [("Work a reported phish: header, link and payload.",
                               "Work a reported phish: headers, sender and link.")],
        # One workstation; the stolen account shows in the 4648 and the capture.
        "hard-credential-theft": [
            ("Correlate logs, memory and a capture across hosts.",
             "Correlate one workstation's logs, memory and capture."),
            ("Follow a service account across logs, memory and a capture.",
             "Trace a stolen service account through the logs and capture to the server it reached."),
        ],
    },
    "case-summary": {
    },
}

_hits = set()


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
    for kind in kinds:
        for key, pairs in FIXES.get(kind, {}).items():
            for old, _ in pairs:
                if (kind, key, old) not in _hits:
                    print(f"tools-product-text: stale {kind} swap for {key}, the product no longer says {old[:70]!r}",
                          file=sys.stderr)
