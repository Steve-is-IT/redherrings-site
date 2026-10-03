#!/usr/bin/env python3
"""Generate branded SVG cover art for each blog post.

One reusable 1600x1000 (16:10) SVG per post, cropped by CSS on both the index
media cards and the article hero. No title text is baked in (the HTML renders
the headline), so the art stays clean and reusable. Each category has its own
colour and a distinct geometric motif that hints at the topic; the slug seeds
small variations so the two Windows posts don't look identical.
"""
import hashlib
import math
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "blog")

# category -> (accent, deep base, motif key)
CATS = {
    "mobile":  ("#1fa85b", "#06281a", "bubbles"),
    "windows": ("#2f6fe0", "#0a1836", "panes"),
    "ir":      ("#e5382f", "#300a0a", "pulse"),
    "threat":  ("#8b5cf6", "#1b1038", "matrix"),
    "network": ("#0e9aa7", "#042026", "beacon"),
    "course":  ("#c7891a", "#2e1d05", "ladder"),
    "exam":    ("#db2777", "#2e0819", "shield"),
    "tools":   ("#4f6b8f", "#0c1622", "gears"),
}

# slug -> category
POSTS = {
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
}

W, H = 1600, 1000


def seed(slug):
    return int(hashlib.sha256(slug.encode()).hexdigest(), 16)


def lerp(a, b, t):
    return a + (b - a) * t


def motif(key, accent, s):
    """Return an SVG fragment for the topic motif (drawn over the gradient)."""
    r = s
    def rnd(n):
        nonlocal r
        r = (r * 1103515245 + 12345) & 0x7fffffff
        return (r / 0x7fffffff) * n
    out = []
    if key == "bubbles":  # iMessage threads
        for i in range(7):
            x = 180 + rnd(1000); y = 170 + rnd(620)
            w = 150 + rnd(230); h = 54 + rnd(26)
            op = 0.06 + rnd(0.10)
            out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="{h/2:.0f}" fill="#fff" opacity="{op:.2f}"/>')
    elif key == "panes":  # registry / window panes
        for i in range(5):
            x = 150 + i * 260 + rnd(40); y = 230 + rnd(380)
            w = 190; h = 150
            op = 0.05 + rnd(0.09)
            out.append(f'<rect x="{x:.0f}" y="{y:.0f}" width="{w}" height="{h}" rx="12" fill="none" stroke="#fff" stroke-width="2.5" opacity="{op:.2f}"/>')
            out.append(f'<line x1="{x:.0f}" y1="{y+38:.0f}" x2="{x+w:.0f}" y2="{y+38:.0f}" stroke="#fff" stroke-width="2.5" opacity="{op:.2f}"/>')
    elif key == "pulse":  # incident waveform
        pts = []
        for i in range(0, W + 1, 20):
            base = H * 0.55
            spike = 0
            if int(rnd(6)) == 0:
                spike = (rnd(2) - 1) * 150
            pts.append(f"{i},{base + math.sin(i/90.0)*22 + spike:.0f}")
        out.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="#fff" stroke-width="3" opacity="0.14"/>')
    elif key == "matrix":  # ATT&CK grid
        for cx in range(8):
            for cy in range(5):
                x = 150 + cx * 170; y = 210 + cy * 130
                op = 0.03 + rnd(0.11)
                out.append(f'<rect x="{x}" y="{y}" width="130" height="92" rx="9" fill="#fff" opacity="{op:.2f}"/>')
    elif key == "beacon":  # periodic beacon ticks on a timeline
        y = H * 0.6
        out.append(f'<line x1="120" y1="{y:.0f}" x2="{W-120}" y2="{y:.0f}" stroke="#fff" stroke-width="2" opacity="0.14"/>')
        x = 170
        while x < W - 150:
            jig = rnd(26) - 13
            hgt = 70 + rnd(120)
            out.append(f'<line x1="{x+jig:.0f}" y1="{y:.0f}" x2="{x+jig:.0f}" y2="{y-hgt:.0f}" stroke="#fff" stroke-width="4" opacity="0.20"/>')
            out.append(f'<circle cx="{x+jig:.0f}" cy="{y-hgt:.0f}" r="7" fill="#fff" opacity="0.22"/>')
            x += 150 + rnd(40)
    elif key == "ladder":  # stepped learning pathway
        steps = 5
        for i in range(steps):
            x = 220 + i * 240; y = H - 230 - i * 110
            op = 0.07 + i * 0.03
            out.append(f'<rect x="{x}" y="{y}" width="190" height="70" rx="12" fill="#fff" opacity="{op:.2f}"/>')
    elif key == "gears":  # tooling / how-to
        for i in range(3):
            cx = 300 + rnd(960); cy = 250 + rnd(480)
            R = 92 + rnd(64)
            op = 0.06 + rnd(0.07)
            out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R:.0f}" fill="none" stroke="#fff" stroke-width="10" opacity="{op:.2f}"/>')
            out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R*0.42:.0f}" fill="none" stroke="#fff" stroke-width="6" opacity="{op:.2f}"/>')
            for t in range(10):
                ang = t / 10.0 * 6.2832
                x1 = cx + math.cos(ang) * R; y1 = cy + math.sin(ang) * R
                x2 = cx + math.cos(ang) * (R + 22); y2 = cy + math.sin(ang) * (R + 22)
                out.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#fff" stroke-width="10" opacity="{op:.2f}"/>')
    elif key == "shield":  # exam integrity shield
        cx, cy = W * 0.5, H * 0.5
        out.append(
            f'<path d="M{cx} {cy-230} L{cx+180} {cy-150} L{cx+180} {cy+20} '
            f'Q{cx+180} {cy+180} {cx} {cy+250} Q{cx-180} {cy+180} {cx-180} {cy+20} '
            f'L{cx-180} {cy-150} Z" fill="none" stroke="#fff" stroke-width="3" opacity="0.14"/>'
        )
        out.append(f'<rect x="{cx-52:.0f}" y="{cy-20:.0f}" width="104" height="100" rx="12" fill="#fff" opacity="0.12"/>')
        out.append(f'<path d="M{cx-30} {cy-20} v-34 a30 30 0 0 1 60 0 v34" fill="none" stroke="#fff" stroke-width="3" opacity="0.14"/>')
    return "\n    ".join(out)


HOOK = (
    'M6 32c9-11 20-16 30-16C40 16 44 19 48 25C51 22 56.5 15.5 62.25 11.75'
    'C58.38 18.12 55.69 25.81 54.44 32C55.69 38.19 58.38 45.88 62.25 52.25'
    'C56.5 48.5 51 42 48 39C44 45 40 48 36 48c-10 0-21-5-30-16z '
    'M20 24.8a5.6 5.6 0 1 0 0 11.2 5.6 5.6 0 1 0 0-11.2z'
)


def build(slug, cat):
    accent, deep, key = CATS[cat]
    s = seed(slug)
    ang = 115 + (s % 40)  # vary gradient angle per slug
    rad = math.radians(ang)
    x2 = 0.5 + math.cos(rad) * 0.6
    y2 = 0.5 + math.sin(rad) * 0.6
    gx1, gy1 = 0.5 - math.cos(rad) * 0.6, 0.5 - math.sin(rad) * 0.6
    # glow positions seeded
    g1x = 0.2 + ((s >> 3) % 60) / 100.0
    g2x = 0.5 + ((s >> 7) % 45) / 100.0
    m = motif(key, accent, s)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Red Herrings">
  <defs>
    <linearGradient id="g" x1="{gx1:.3f}" y1="{gy1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}">
      <stop offset="0" stop-color="{deep}"/>
      <stop offset="0.62" stop-color="{accent}"/>
      <stop offset="1" stop-color="{accent}"/>
    </linearGradient>
    <radialGradient id="glow1" cx="{g1x:.2f}" cy="0.25" r="0.6">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.26"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glow2" cx="{g2x:.2f}" cy="0.9" r="0.7">
      <stop offset="0" stop-color="{deep}" stop-opacity="0.55"/>
      <stop offset="1" stop-color="{deep}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#g)"/>
  <rect width="{W}" height="{H}" fill="url(#glow2)"/>
  <g>
    {m}
  </g>
  <rect width="{W}" height="{H}" fill="url(#glow1)"/>
  <g transform="translate({W-330},{H-300}) scale(5.1)" opacity="0.10">
    <path fill-rule="evenodd" d="{HOOK}" fill="#ffffff"/>
  </g>
</svg>
'''


def main():
    os.makedirs(OUT, exist_ok=True)
    for slug, cat in POSTS.items():
        svg = build(slug, cat)
        p = os.path.join(OUT, slug + ".svg")
        with open(p, "w") as fh:
            fh.write(svg)
        print("wrote", p, len(svg), "bytes")


if __name__ == "__main__":
    main()
