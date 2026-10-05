#!/usr/bin/env python3
"""Generate branded SVG cover art for each blog post.

One reusable 1600x1000 (16:10) SVG per post, cropped by CSS on both the index
media cards and the article hero. Each category gets its own colour plus a
large, low-opacity glyph that signals the category (a phone for mobile, a
window for Windows, an alert for IR, and so on), with the Red Herrings hook
watermark kept in the bottom-right corner. The slug seeds small variations so
two posts in the same category don't look identical.
"""
import hashlib
import math
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "blog")

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
}

# category -> recognizable glyph (24x24 viewBox, stroke paths)
GLYPHS = {
    "mobile":  '<rect x="6" y="2" width="12" height="20" rx="2.4"/><line x1="10.2" y1="18.4" x2="13.8" y2="18.4"/>',
    "windows": '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="12" y1="3" x2="12" y2="21"/><line x1="3" y1="12" x2="21" y2="12"/>',
    "ir":      '<path d="M10.29 3.86 L1.82 18 a2 2 0 0 0 1.71 3 h16.94 a2 2 0 0 0 1.71-3 L13.71 3.86 a2 2 0 0 0-3.42 0 z"/><line x1="12" y1="9" x2="12" y2="13.5"/><line x1="12" y1="16.6" x2="12" y2="17.2"/>',
    "threat":  '<circle cx="12" cy="12" r="9.5"/><circle cx="12" cy="12" r="4"/><line x1="12" y1="0.8" x2="12" y2="4.5"/><line x1="12" y1="19.5" x2="12" y2="23.2"/><line x1="0.8" y1="12" x2="4.5" y2="12"/><line x1="19.5" y1="12" x2="23.2" y2="12"/>',
    "network": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.6" y1="13.5" x2="15.4" y2="17.5"/><line x1="15.4" y1="6.5" x2="8.6" y2="10.5"/>',
    "course":  '<path d="M12 3 L23 8 L12 13 L1 8 Z"/><path d="M5 10 V15.3 C5 17 8.1 18.3 12 18.3 C15.9 18.3 19 17 19 15.3 V10"/>',
    "exam":    '<path d="M12 22 s8-4 8-10 V5 l-8-3-8 3 v7 c0 6 8 10 8 10 z"/><rect x="9.4" y="11" width="5.2" height="4.4" rx="0.7"/><path d="M10.5 11 V9.6 a1.5 1.5 0 0 1 3 0 V11"/>',
    "tools":   '<path d="M14.7 6.3 a1 1 0 0 0 0 1.4 l1.6 1.6 a1 1 0 0 0 1.4 0 l3.77-3.77 a6 6 0 0 1-7.94 7.94 l-6.91 6.91 a2.12 2.12 0 0 1-3-3 l6.91-6.91 a6 6 0 0 1 7.94-7.94 l-3.76 3.76 z"/>',
}

# slug -> category
POSTS = {
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
}

W, H = 1600, 1000

HOOK = (
    'M6 32c9-11 20-16 30-16C40 16 44 19 48 25C51 22 56.5 15.5 62.25 11.75'
    'C58.38 18.12 55.69 25.81 54.44 32C55.69 38.19 58.38 45.88 62.25 52.25'
    'C56.5 48.5 51 42 48 39C44 45 40 48 36 48c-10 0-21-5-30-16z '
    'M20 24.8a5.6 5.6 0 1 0 0 11.2 5.6 5.6 0 1 0 0-11.2z'
)


def seed(slug):
    return int(hashlib.sha256(slug.encode()).hexdigest(), 16)


def build(slug, cat):
    accent, deep = CATS[cat]
    s = seed(slug)
    ang = 115 + (s % 40)  # vary gradient angle per slug
    rad = math.radians(ang)
    x2 = 0.5 + math.cos(rad) * 0.6
    y2 = 0.5 + math.sin(rad) * 0.6
    gx1, gy1 = 0.5 - math.cos(rad) * 0.6, 0.5 - math.sin(rad) * 0.6
    g1x = 0.2 + ((s >> 3) % 60) / 100.0
    g2x = 0.5 + ((s >> 7) % 45) / 100.0

    # glyph placement: large, low opacity, slightly seeded offset
    gscale = 18
    gcx = 720 + ((s >> 5) % 120)
    gcy = 440 + ((s >> 11) % 120)
    tx = gcx - 12 * gscale
    ty = gcy - 12 * gscale
    glyph = (f'<g transform="translate({tx:.0f},{ty:.0f}) scale({gscale})" '
             f'fill="none" stroke="#ffffff" stroke-width="0.85" stroke-linecap="round" '
             f'stroke-linejoin="round" opacity="0.10">{GLYPHS[cat]}</g>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Red Herrings">
  <defs>
    <linearGradient id="g" x1="{gx1:.3f}" y1="{gy1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}">
      <stop offset="0" stop-color="{deep}"/>
      <stop offset="0.62" stop-color="{accent}"/>
      <stop offset="1" stop-color="{accent}"/>
    </linearGradient>
    <radialGradient id="glow1" cx="{g1x:.2f}" cy="0.25" r="0.6">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.24"/>
      <stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glow2" cx="{g2x:.2f}" cy="0.9" r="0.7">
      <stop offset="0" stop-color="{deep}" stop-opacity="0.55"/>
      <stop offset="1" stop-color="{deep}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#g)"/>
  <rect width="{W}" height="{H}" fill="url(#glow2)"/>
  {glyph}
  <rect width="{W}" height="{H}" fill="url(#glow1)"/>
  <g transform="translate({W-330},{H-300}) scale(5.1)" opacity="0.10">
    <path fill-rule="evenodd" d="{HOOK}" fill="#ffffff"/>
  </g>
</svg>
'''


def main():
    os.makedirs(OUT, exist_ok=True)
    for slug, cat in POSTS.items():
        with open(os.path.join(OUT, slug + ".svg"), "w") as fh:
            fh.write(build(slug, cat))
        print("wrote", slug + ".svg")


if __name__ == "__main__":
    main()
