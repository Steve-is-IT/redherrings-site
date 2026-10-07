#!/usr/bin/env python3
"""Write the 'Tool guide' blog posts in final form (cover + head + body +
related), matching the existing transformed blog articles. Header/footer are
left as placeholders for tools-apply-nav.py / tools-apply-footer.py to fill.
Rerunnable (overwrites the files)."""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
BLOG = os.path.join(ROOT, "blog")
DATE = "2026-10-03"

ICON = ('<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 '
        'viewBox=%270 0 64 64%27%3E%3Cpath fill=%27%23E5382F%27 d=%27M6 32c9-11 20-16 30-16 4 0 8 3 12 9 '
        '3-3 8.5-9.5 14.25-13.25C58.38 18.12 55.69 25.81 54.44 32c1.25 6.19 3.94 13.87 7.81 20.25C56.5 48.5 '
        '51 42 48 39c-4 6-8 9-12 9-10 0-21-5-30-16z%27/%3E%3C/svg%3E">')
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" '
         'href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" '
         'href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">')
THEMEBOOT = ("<script>(function(){try{var t=localStorage.getItem('rh-theme');"
             "if(t==='dark'||t==='light')document.documentElement.setAttribute('data-theme',t);}catch(e){}})();</script>")
TAIL = ('<script data-goatcounter="https://redherrings.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>\n'
        '<script src="../theme.js" defer></script>\n</body>\n</html>\n')

CTA = ('<div class="cta">\n'
       '      <strong>Want to practice on real evidence?</strong>\n'
       '      <p style="margin:8px 0 14px">Download the free sample lab, or start the 30-day trial and generate a per-student case in a few minutes.</p>\n'
       '      <div class="cta-row">\n'
       '        <a class="btn" href="/sample.html">Get the free sample lab</a>\n'
       '        <a class="btn ghost" href="/download.html">Start a free trial</a>\n'
       '      </div>\n'
       '    </div>')

# slug -> (cls, category label, title) for related cards
META = {
    "autopsy-disk-image-analysis-walkthrough": ("c-tool", "Tool guide", "Analyze a disk image in Autopsy: a beginner's walkthrough"),
    "registry-explorer-windows-registry-forensics": ("c-tool", "Tool guide", "Read the Windows registry with Registry Explorer"),
    "evtxecmd-windows-event-log-timeline": ("c-tool", "Tool guide", "Turn Windows event logs into a timeline with EvtxECmd"),
    "volatility-3-memory-forensics-getting-started": ("c-tool", "Tool guide", "Getting started with memory forensics in Volatility 3"),
}

POSTS = [
    {
        "slug": "autopsy-disk-image-analysis-walkthrough",
        "title": "Analyze a disk image in Autopsy: a beginner's walkthrough",
        "metadesc": "A step-by-step guide to opening a disk image in Autopsy, running the right ingest modules, and finding the artifacts that answer a forensics question. Written for students starting out in DFIR.",
        "ogdesc": "Open a disk image in Autopsy, run the right ingest modules, and find the artifacts that answer the question. A beginner's DFIR walkthrough.",
        "lede": "Autopsy is where most people start in digital forensics. It's a free, open-source front end for The Sleuth Kit, so you can open a disk image and look through the file system, deleted files, web history and registry without a license or a long setup. Here's how to work a case in it.",
        "body": """<h2>Get Autopsy</h2>
    <p>Autopsy is free and open source. Download the installer from <a href="https://www.autopsy.com/">autopsy.com</a> and run it; on Windows it bundles everything you need. Our <a href="/tools.html">Tools &amp; setup</a> page lists it alongside the rest of the toolkit a case expects.</p>
    <h2>Create a case and add the evidence</h2>
    <p>Choose <strong>New Case</strong>, give it a name and a folder, then run <strong>Add Data Source</strong>. For a raw or E01 image (<code>.dd</code>, <code>.E01</code>), pick "Disk Image or VM File". For a folder of already-extracted artifacts, pick "Logical Files". The <a href="/sample.html">free sample lab</a> ships an <code>evidence.dd</code> that loads this way, so you can follow along on something real.</p>
    <h2>Run the right ingest modules</h2>
    <p>Ingest modules are the parsers Autopsy runs over the image. You don't need all of them on the first pass. These four cover most cases:</p>
    <ul>
      <li><strong>Recent Activity</strong>: web history, downloads, installed programs, USB device history.</li>
      <li><strong>File Type Identification</strong> and <strong>Extension Mismatch Detector</strong>: flag a file whose contents don't match its extension.</li>
      <li><strong>Hash Lookup</strong>: filter known-good files and flag known-bad ones.</li>
      <li><strong>Keyword Search</strong>: find a filename, user or string anywhere on the image.</li>
    </ul>
    <p>They run in the background, and the tree on the left fills in as each one finishes.</p>
    <h2>Where the answers usually are</h2>
    <ul>
      <li><strong>Data Artifacts, then Recent Activity</strong>: web history, downloads, USB history, programs that ran.</li>
      <li><strong>File System tree</strong>: browse to a user's folder. The Deleted Files node pulls entries back out of unallocated space.</li>
      <li><strong>Extension Mismatch</strong>: a <code>.jpg</code> that's really a <code>.7z</code> shows up here. It's a common way to hide a file.</li>
      <li><strong>Keyword Search</strong>: locate a string whether it's allocated or not.</li>
      <li><strong>Timeline</strong> (Tools, then Timeline): every file and artifact on one scrubber, in order.</li>
    </ul>
    <h2>Don't stop at the first hit</h2>
    <p>One artifact on its own is weak. A prefetch entry, a LNK file and a USB device record that all line up tell a much better story. Our disk cases plant realistic background activity on purpose, so a good part of the work is ruling things out rather than grabbing the one obvious thing.</p>
    <h2>How it fits a Red Herrings case</h2>
    <p>Our Windows and disk cases are written in real on-disk formats, so Autopsy opens them with no special setup. Every student gets a different image with their own files, timestamps and answers, and each one is re-solved and verified before it goes out. The <a href="/pathways.html">learning pathways</a> start at First Look triage and build up to a capstone.</p>""",
        "related": ["registry-explorer-windows-registry-forensics", "evtxecmd-windows-event-log-timeline", "volatility-3-memory-forensics-getting-started"],
    },
    {
        "slug": "registry-explorer-windows-registry-forensics",
        "title": "Read the Windows registry with Registry Explorer",
        "metadesc": "How to load Windows registry hives in Eric Zimmerman's Registry Explorer, use forensic bookmarks, handle dirty hives, and read the keys that prove USB use, program execution and persistence.",
        "ogdesc": "Load registry hives in Registry Explorer, use the forensic bookmarks, and read the keys that prove USB use, program execution and persistence.",
        "lede": "The Windows registry keeps a quiet record of what was plugged in, what ran, and what a user opened. Registry Explorer, one of Eric Zimmerman's tools, is the quickest way to read a hive, and its bookmarks point you straight at the keys worth looking at.",
        "body": """<h2>Get Registry Explorer</h2>
    <p>Registry Explorer is part of Eric Zimmerman's free tools and needs the .NET runtime. Download it from <a href="https://ericzimmerman.github.io/">ericzimmerman.github.io</a>. The <a href="/tools.html">Tools &amp; setup</a> page has the rest.</p>
    <h2>Load a hive, and its logs</h2>
    <p>Registry data lives in hive files, each covering a different part of the system:</p>
    <ul>
      <li><code>NTUSER.DAT</code>: one per user, holding their activity, recent files and run history.</li>
      <li><code>SYSTEM</code>: devices, services and the current control set.</li>
      <li><code>SOFTWARE</code>: installed programs and system-wide settings.</li>
      <li><code>SAM</code>: local accounts. <code>USRCLASS.DAT</code>: shellbags and more.</li>
    </ul>
    <p>When you open a hive, Registry Explorer may say it's "dirty", meaning recent changes are still sitting in the transaction logs (<code>.LOG1</code> and <code>.LOG2</code>). Point it at those logs when it asks, so you're reading the current state and not a stale one. The <a href="/sample.html">sample lab</a> includes <code>NTUSER.DAT</code>, <code>SYSTEM</code> and <code>SOFTWARE</code> to try this on.</p>
    <h2>Use the bookmarks</h2>
    <p>The Bookmarks panel is what makes Registry Explorer quick. It jumps to the keys that matter for each hive, already decoded, so you don't have to remember every path.</p>
    <h2>Keys worth knowing</h2>
    <ul>
      <li><strong>USB history</strong>: <code>SYSTEM\\...\\Enum\\USBSTOR</code> and <code>MountedDevices</code> show what was plugged in, and when.</li>
      <li><strong>UserAssist</strong>: GUI programs the user ran, with run counts. The values are ROT13-encoded, and Registry Explorer decodes them.</li>
      <li><strong>RecentDocs</strong> and <strong>RunMRU</strong>: files opened, and commands typed into the Run box.</li>
      <li><strong>Run and RunOnce</strong>: what launches at logon, a common place for persistence.</li>
      <li><strong>TypedURLs</strong>: addresses the user typed into the browser.</li>
    </ul>
    <h2>Two things to watch</h2>
    <p>Registry timestamps are in UTC, so convert them before you build a timeline. And a key's last-write time tells you when the key changed, not necessarily when one value inside it did.</p>
    <h2>How it fits a Red Herrings case</h2>
    <p>Our Windows cases put their answers in real hive files, so the keys you read here are the ones that solve the case. Every student gets a different device serial, user and run history, verified before release. The <a href="/pathways.html">Windows forensics pathway</a> is a good place to build the skill.</p>""",
        "related": ["autopsy-disk-image-analysis-walkthrough", "evtxecmd-windows-event-log-timeline", "volatility-3-memory-forensics-getting-started"],
    },
    {
        "slug": "evtxecmd-windows-event-log-timeline",
        "title": "Turn Windows event logs into a timeline with EvtxECmd",
        "metadesc": "How to parse Windows .evtx event logs into a clean CSV with Eric Zimmerman's EvtxECmd, open them in Timeline Explorer, and read the Event IDs that matter for DFIR.",
        "ogdesc": "Parse .evtx logs into a clean CSV with EvtxECmd, open them in Timeline Explorer, and read the Event IDs that matter for an investigation.",
        "lede": "Windows records a lot in its .evtx logs, but Event Viewer is a slow way to read them. EvtxECmd parses the logs into a CSV you can sort, filter and timeline, and its maps pull the useful fields out of each event for you.",
        "body": """<h2>Get EvtxECmd</h2>
    <p>EvtxECmd is another of Eric Zimmerman's free tools, and it ships with its maps. Download it from <a href="https://ericzimmerman.github.io/">ericzimmerman.github.io</a>. See <a href="/tools.html">Tools &amp; setup</a> for the rest.</p>
    <h2>Parse a log to CSV</h2>
    <p>One log at a time:</p>
    <p><code>EvtxECmd.exe -f Security.evtx --csv . --csvf security.csv</code></p>
    <p>Or a whole folder:</p>
    <p><code>EvtxECmd.exe -d "C:\\evidence\\winevt\\Logs" --csv . --csvf all.csv</code></p>
    <p>The <a href="/sample.html">sample lab</a> includes <code>Security.evtx</code> and <code>System.evtx</code> to try this on.</p>
    <h2>Open it in Timeline Explorer</h2>
    <p>Load the CSV in Timeline Explorer, also from Eric Zimmerman. You can sort by time, filter by Event ID, and pin the rows you care about, which beats clicking through Event Viewer one line at a time.</p>
    <h2>Event IDs worth knowing</h2>
    <ul>
      <li><strong>4624 / 4625</strong>: a logon that succeeded or failed. Check the Logon Type (3 is network, 10 is RDP).</li>
      <li><strong>4688</strong>: a process started, with the command line if auditing is on.</li>
      <li><strong>4720</strong>: an account was created. <strong>4728 / 4732</strong>: an account was added to a group.</li>
      <li><strong>7045</strong>: a service was installed, which is a common persistence step.</li>
      <li><strong>1102</strong>: the Security log was cleared.</li>
    </ul>
    <h2>Let the maps help</h2>
    <p>EvtxECmd's maps pull the useful fields out of each event's payload, so you get named columns instead of raw XML. One thing to keep straight on a Security event: <code>SubjectUserName</code> is who did it, and <code>TargetUserName</code> is who it was done to. Getting those backwards is the most common mistake we see when grading.</p>
    <h2>How it fits a Red Herrings case</h2>
    <p>Our event-log cases are written as real binary EVTX, so EvtxECmd reads them the same way it reads a live system's logs. For a worked example that chains logons to the processes they spawned, see <a href="/blog/detect-lateral-movement-windows-event-logs.html">detecting lateral movement in Windows event logs</a>.</p>""",
        "related": ["autopsy-disk-image-analysis-walkthrough", "registry-explorer-windows-registry-forensics", "volatility-3-memory-forensics-getting-started"],
    },
    {
        "slug": "volatility-3-memory-forensics-getting-started",
        "title": "Getting started with memory forensics in Volatility 3",
        "metadesc": "A beginner's guide to Volatility 3: install it, list running processes, follow a process to its network connections and command line, and spot injected code in a memory image.",
        "ogdesc": "Install Volatility 3, list processes, follow them to network connections and command lines, and spot injected code in a memory image.",
        "lede": "A memory image shows you things a disk never will: running processes, network connections, command lines, and injected code, all frozen at the moment of capture. Volatility 3 is the standard free tool for reading one, and unlike version 2 it works out the symbols on its own.",
        "body": """<h2>Get Volatility 3</h2>
    <p>Volatility 3 is free, open source, and written in Python. Install it with <code>pip install volatility3</code>, or clone it from <a href="https://github.com/volatilityfoundation/volatility3">the project repo</a>. The main change from version 2 is that you no longer pass <code>--profile</code>; version 3 figures out the symbols itself.</p>
    <h2>Start with the processes</h2>
    <p>A memory case usually starts with what was running:</p>
    <ul>
      <li><code>vol -f memory.dmp windows.pslist</code>: the active process list.</li>
      <li><code>vol -f memory.dmp windows.pstree</code>: the same list as a parent/child tree, so an odd pairing like a browser launching a shell stands out.</li>
      <li><code>vol -f memory.dmp windows.psscan</code>: scans for processes, including hidden or exited ones.</li>
    </ul>
    <p>Our memory cases ship a real image you can run these against.</p>
    <h2>Follow a process to the network and its command line</h2>
    <ul>
      <li><code>windows.netscan</code>: network connections and listening ports, tied back to a process.</li>
      <li><code>windows.cmdline</code>: the exact command line a process was started with.</li>
      <li><code>windows.dlllist</code>: the modules a process loaded.</li>
    </ul>
    <h2>Look for injected code</h2>
    <p><code>windows.malfind</code> finds memory regions that are both executable and private, which usually means injected or unpacked code. That's often where the payload is.</p>
    <h2>One common snag</h2>
    <p>A lot of tutorials online are written for Volatility 2, where commands look like <code>--profile=Win10x64 pslist</code>. Those won't run in version 3. Use the <code>windows.&lt;plugin&gt;</code> form instead.</p>
    <h2>How it fits a Red Herrings case</h2>
    <p>Our memory cases ship a real minidump, so these plugins return real answers: a different malicious process, beacon and injected region for every student. The First Look memory case on the <a href="/pathways.html">pathways</a> page is a good start.</p>""",
        "related": ["autopsy-disk-image-analysis-walkthrough", "registry-explorer-windows-registry-forensics", "evtxecmd-windows-event-log-timeline"],
    },
]


def related_html(slugs):
    cards = []
    for s in slugs:
        cls, cat, title = META[s]
        cards.append(f'''      <a class="rel" href="{s}.html">
        <div class="cover"><img src="../img/blog/{s}.svg" alt="" width="1600" height="1000"></div>
        <span class="cat {cls}">{cat}</span>
        <h3>{title}</h3>
      </a>''')
    return ('    <section class="related">\n'
            '      <h2>More teaching notes</h2>\n'
            '      <div class="rel-grid">\n'
            + "\n".join(cards) + "\n      </div>\n    </section>")


def jsonld(p):
    return ('<script type="application/ld+json">\n'
            '{"@context":"https://schema.org","@type":"BlogPosting","headline":"' + p["title"].replace('"', '\\"') + '",'
            '"description":"' + p["ogdesc"].replace('"', '\\"') + '","datePublished":"' + DATE + '",'
            '"author":{"@type":"Organization","name":"Red Herrings"},'
            '"publisher":{"@type":"Organization","name":"Red Herrings"},'
            '"mainEntityOfPage":"https://redherrings.app/blog/' + p["slug"] + '.html"}\n</script>')


def build(p):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{p["title"]} | Red Herrings</title>
<meta name="description" content="{p["metadesc"]}">
<link rel="canonical" href="https://redherrings.app/blog/{p["slug"]}.html">
<meta name="robots" content="index,follow">
<meta name="theme-color" content="#E5382F">
{ICON}
<meta property="og:type" content="article">
<meta property="og:title" content="{p["title"]}">
<meta property="og:description" content="{p["ogdesc"]}">
<meta property="og:url" content="https://redherrings.app/blog/{p["slug"]}.html">
<meta property="og:image" content="https://redherrings.app/img/og.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://redherrings.app/img/og.png">
{FONTS}
<link rel="stylesheet" href="../site.css">
<link rel="stylesheet" href="../blog.css">
{jsonld(p)}
  {THEMEBOOT}
</head>
<body>
<header></header>

<main class="wrap">
  <article class="post">
    <nav class="post-crumb"><a href="/">Home</a> / <a href="index.html">Blog</a></nav>
    <div class="post-cover"><img src="../img/blog/{p["slug"]}.svg" alt="" width="1600" height="1000"></div>
    <header class="post-head"><h1>{p["title"]}</h1></header>
    <p class="lede">{p["lede"]}</p>

    {p["body"]}

    {CTA}
{related_html(p["related"])}
  </article>
</main>

<footer></footer>
{TAIL}'''


def main():
    for p in POSTS:
        path = os.path.join(BLOG, p["slug"] + ".html")
        with open(path, "w") as fh:
            fh.write(build(p))
        print("wrote", p["slug"] + ".html")


if __name__ == "__main__":
    main()
