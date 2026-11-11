#!/usr/bin/env python3
"""Generate the blog cover SVGs from real tool output.

One 1600x1000 SVG per post at img/blog/<slug>.svg. Each cover is a terminal
window on the post's category gradient, showing a few lines of real output
(Volatility 3, python-evtx, python-registry, scapy, sqlite3, pytsk3 and the
product's own CLI) captured from labs generated with Red Herrings. The
captured lines live in tools-blog-cover-data.json; only background rows are
used, never a case answer.

CSS crops the covers: 16:10 or 16:9 on index cards and 8:3 (about 1040x390)
on the article page, centered. The window is sized and centered so it always
sits inside the 8:3 band (y 200 to 800), and the type is as large as the
longest line allows so it stays readable on a 340px card.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "img", "blog")
DATA = os.path.join(HERE, "tools-blog-cover-data.json")

# category -> (accent, deep base)
CATS = {
    "mobile":  ("#1fa85b", "#06281a"),
    "windows": ("#2f6fe0", "#0a1836"),
    "ir":      ("#e5382f", "#300a0a"),
    "threat":  ("#8b5cf6", "#1b1038"),
    "network": ("#0e9aa7", "#042026"),
    "course":  ("#c7891a", "#2e1d05"),
    "exam":    ("#db2777", "#2e0819"),
    "tools":   ("#4f6b8f", "#0c1622"),
    "secops":  ("#5a67d8", "#161a40"),
    "buying":  ("#0e9e74", "#05271c"),
}

# slug -> category
POSTS = {
    "how-to-grade-a-digital-forensics-lab": "course",
    "prefetch-forensics-pecmd-walkthrough": "tools",
    "build-a-digital-forensics-course-syllabus": "course",
    "chain-of-custody-in-the-classroom": "course",
    "incident-response-tabletop-vs-hands-on-exercise": "ir",
    "wireshark-for-beginners-packet-capture-basics": "tools",
    "whats-new-student-portal-certificates": "course",
    "ios-imessage-forensics-cocoa-time": "mobile",
    "detect-lateral-movement-windows-event-logs": "windows",
    "gcfe-windows-forensics-practice-labs": "windows",
    "incident-response-exercise-edr-siem": "ir",
    "teaching-mitre-attack-hands-on": "threat",
    "detect-c2-beaconing-packet-capture": "network",
    "dfir-learning-pathways-first-look-to-capstone": "course",
    "forensics-exam-students-cant-copy": "exam",
    "autopsy-disk-image-analysis-walkthrough": "tools",
    "registry-explorer-windows-registry-forensics": "tools",
    "evtxecmd-windows-event-log-timeline": "tools",
    "volatility-3-memory-forensics-getting-started": "tools",
    "soc-analyst-onboarding-hands-on-labs": "secops",
    "blue-team-ctf-analysts-cant-google": "secops",
    "air-gapped-forensics-training-no-cloud": "secops",
    "white-label-dfir-training-resell-cases": "buying",
    "cyber-range-vs-generated-cases-cost": "buying",
    "digital-forensics-lab-platform-buyers-guide": "buying",
}

W, H = 1600, 1000
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
CHAR = 0.61                     # monospace advance as a fraction of font size
BAND_TOP, BAND_BOT = 230, 770   # inside the 8:3 article crop (y 200 to 800), with a margin
MAX_FS, MIN_W, MAX_W = 44, 1000, 1520
PADX, PADY, TB = 56, 30, 66     # inner padding and title bar height
LH = 1.38

HOOK = (
    'M6 32c9-11 20-16 30-16C40 16 44 19 48 25C51 22 56.5 15.5 62.25 11.75'
    'C58.38 18.12 55.69 25.81 54.44 32C55.69 38.19 58.38 45.88 62.25 52.25'
    'C56.5 48.5 51 42 48 39C44 45 40 48 36 48c-10 0-21-5-30-16z '
    'M20 24.8a5.6 5.6 0 1 0 0 11.2 5.6 5.6 0 1 0 0-11.2z'
)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def mix(hex_a, hex_b, t):
    a = [int(hex_a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(hex_b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def layout(lines):
    """Font size, window width and height: the biggest type that fits the
    longest line and keeps the window inside the 8:3 band."""
    n = len(lines)
    longest = max(len(t) for _, t in lines)
    room = (BAND_BOT - BAND_TOP) - TB - 2 * PADY
    fs = min(MAX_FS, (MAX_W - 2 * PADX) / (CHAR * longest), room / (n * LH))
    pw = max(MIN_W, min(MAX_W, CHAR * fs * longest + 2 * PADX))
    ph = TB + 2 * PADY + n * fs * LH
    return fs, pw, ph


def build(slug, cat, entry):
    accent, deep = CATS[cat]
    light = mix(accent, "#ffffff", 0.5)
    lines = entry["lines"]
    fs, pw, ph = layout(lines)
    px, py = (W - pw) / 2, (H - ph) / 2
    assert BAND_TOP <= py and py + ph <= BAND_BOT, slug

    color = {"": "#e6edf3", "head": light, "cmd": light, "dim": "#8b949e"}
    body = []
    y0 = py + TB + PADY + fs * 1.05
    for i, (style, text) in enumerate(lines):
        if not text:
            continue
        bold = ' font-weight="700"' if style == "head" else ""
        body.append(f'<text x="{px + PADX:.1f}" y="{y0 + i * fs * LH:.1f}" fill="{color[style]}"{bold} '
                    f'xml:space="preserve">{esc(text)}</text>')
    body = "\n      ".join(body)

    dots = "".join(
        f'<circle cx="{px + 40 + k * 30:.1f}" cy="{py + TB / 2:.1f}" r="9" fill="{c}"/>'
        for k, c in enumerate(("#ff5f57", "#febc2e", "#28c840")))
    r = 20
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(entry["title"])} output">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{deep}"/>
      <stop offset="0.72" stop-color="{accent}"/>
      <stop offset="1" stop-color="{light}"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.5" cy="0.5" r="0.62">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.16"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <pattern id="dots" width="40" height="40" patternUnits="userSpaceOnUse">
      <circle cx="20" cy="20" r="1.6" fill="#ffffff" fill-opacity="0.09"/>
    </pattern>
    <filter id="sh" x="-10%" y="-20%" width="120%" height="150%">
      <feDropShadow dx="0" dy="22" stdDeviation="28" flood-color="#000000" flood-opacity="0.5"/>
    </filter>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#g)"/>
  <rect width="{W}" height="{H}" fill="url(#dots)"/>
  <rect width="{W}" height="{H}" fill="url(#glow)"/>
  <rect x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="{ph:.1f}" rx="{r}" fill="#0d1117" fill-opacity="0.96" filter="url(#sh)"/>
  <path d="M{px:.1f} {py + TB:.1f}V{py + r:.1f}a{r} {r} 0 0 1 {r} -{r}H{px + pw - r:.1f}a{r} {r} 0 0 1 {r} {r}V{py + TB:.1f}Z" fill="#161b22"/>
  <line x1="{px:.1f}" y1="{py + TB:.1f}" x2="{px + pw:.1f}" y2="{py + TB:.1f}" stroke="#30363d" stroke-width="2"/>
  <rect x="{px:.1f}" y="{py:.1f}" width="{pw:.1f}" height="{ph:.1f}" rx="{r}" fill="none" stroke="#ffffff" stroke-opacity="0.14" stroke-width="2"/>
  {dots}
  <g transform="translate({px + pw - 84:.1f},{py + TB / 2 - 22.4:.1f}) scale(0.7)" opacity="0.65">
    <path fill-rule="evenodd" d="{HOOK}" fill="{light}"/>
  </g>
  <g font-family="{MONO}">
    <text x="{px + 150:.1f}" y="{py + TB / 2 + 10:.1f}" font-size="30" fill="#8b949e" xml:space="preserve">{esc(entry["title"])}</text>
    <g font-size="{fs:.1f}">
      {body}
    </g>
  </g>
</svg>
'''


def main():
    with open(DATA, encoding="utf-8") as fh:
        data = json.load(fh)
    os.makedirs(OUT, exist_ok=True)
    for slug, cat in POSTS.items():
        svg = build(slug, cat, data[slug])
        assert chr(0x2014) not in svg and chr(0x2013) not in svg, slug  # no em or en dashes
        with open(os.path.join(OUT, slug + ".svg"), "w", encoding="utf-8") as fh:
            fh.write(svg)
        print("wrote", slug + ".svg")


if __name__ == "__main__":
    main()
