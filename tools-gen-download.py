#!/usr/bin/env python3
"""Generate download.html: an official download page with the current version,
per-OS downloads with sizes and SHA-256 checksums, system requirements, a trust
strip, and release notes from the product CHANGELOG.

Sources of truth:
  * CHANGELOG.md in the product repo (version headings `## vX.Y.Z — YYYY-MM-DD`)
  * the public GitHub releases on the site repo (dates, asset sizes)
  * the latest release's SHA256SUMS.txt (checksums)

Rerun after every release (it is on the release checklist in
docs/CODE_SIGNING.md), then run tools-apply-nav.py / tools-apply-footer.py and
commit. Download buttons use the stable /releases/latest/download/ URLs, so
they never go stale even if this page lags a release.
"""
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
CHANGELOG = os.environ.get("RH_CHANGELOG", os.path.join(ROOT, "..", "redherrings", "CHANGELOG.md"))
REPO = "Steve-is-IT/redherrings-site"
DL = f"https://github.com/{REPO}/releases/latest/download"
RELEASES_PAGE = f"https://github.com/{REPO}/releases"
PUBLISHER = "The Competence Collective, LLC"

# The first release tag whose Windows build is Authenticode-signed with the
# Certum certificate. None = no signed build published yet, so the page makes
# no signing claim. Set this (e.g. "v1.7.0") when the first signed release
# ships via packaging/scripts/release_windows_signed.ps1.
SIGNED_SINCE = "v1.7.0"
# First release tag whose macOS zips were notarized in CI (see docs/CODE_SIGNING.md). None = not yet.
MAC_NOTARIZED_SINCE = None

E = lambda s: html.escape(str(s or ""), quote=True)


def vt(tag):
    return tuple(int(x) for x in re.findall(r"\d+", str(tag))[:3]) or (0,)


def gh(url):
    req = urllib.request.Request(url, headers={"User-Agent": "redherrings-site-gen",
                                               "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def fetch_releases():
    data = json.loads(gh(f"https://api.github.com/repos/{REPO}/releases?per_page=50"))
    out = {}
    for rel in data:
        if rel.get("draft"):
            continue
        tag = rel["tag_name"]
        out[vt(tag)] = {
            "tag": tag,
            "date": (rel.get("published_at") or "")[:10],
            "assets": {a["name"]: a["size"] for a in rel.get("assets", [])},
            "url": rel.get("html_url"),
        }
    return out


def fetch_sums(tag):
    try:
        txt = gh(f"https://github.com/{REPO}/releases/download/{tag}/SHA256SUMS.txt").decode()
    except Exception:
        return {}
    sums = {}
    for line in txt.splitlines():
        parts = line.split()
        if len(parts) == 2:
            sums[parts[1].lstrip("*")] = parts[0].lower()
    return sums


def parse_changelog(path):
    """-> [(version_tuple, tag, date, body_md)] newest first."""
    text = open(path, encoding="utf-8").read()
    entries = []
    for m in re.finditer(r"^## (v?\d+\.\d+\.\d+)\s*[—–-]+\s*(\d{4}-\d{2}-\d{2})\s*$", text, re.M):
        entries.append((m, m.group(1), m.group(2)))
    for i, (m, tag, date) in enumerate(entries):
        end = entries[i + 1][0].start() if i + 1 < len(entries) else len(text)
        yield vt(tag), tag if tag.startswith("v") else "v" + tag, date, text[m.end():end].strip()


def inline(s):
    s = E(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def md_to_html(md):
    """A deliberately small Markdown subset: ### headings, - bullets (with
    indented continuation lines), paragraphs, inline bold/code/links."""
    out, para, bullets = [], [], []

    def flush_para():
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()

    def flush_bullets():
        if bullets:
            out.append("<ul>" + "".join(f"<li>{inline(b)}</li>" for b in bullets) + "</ul>")
            bullets.clear()

    for line in md.splitlines():
        if not line.strip():
            flush_para(); flush_bullets(); continue
        if line.startswith("### "):
            flush_para(); flush_bullets()
            out.append(f"<h4>{inline(line[4:].strip())}</h4>")
        elif re.match(r"^\s*[-*] ", line):
            flush_para()
            bullets.append(re.sub(r"^\s*[-*] ", "", line).strip())
        elif bullets and re.match(r"^\s{2,}\S", line):
            bullets[-1] += " " + line.strip()
        else:
            flush_bullets()
            para.append(line.strip())
    flush_para(); flush_bullets()
    return "\n".join(out)


def mb(n):
    return f"{n / 1_000_000:.0f} MB" if n else ""


def page(latest, releases, notes, sums):
    tag, date = latest["tag"], latest["date"]
    nice_date = dt.date.fromisoformat(date).strftime("%B %-d, %Y") if date else ""
    signed = bool(SIGNED_SINCE) and vt(tag) >= vt(SIGNED_SINCE) and "RedHerrings-windows.zip" in latest["assets"]
    win_size = mb(latest["assets"].get("RedHerrings-windows.zip"))
    lin_size = mb(latest["assets"].get("RedHerrings-linux.zip"))
    win_sha = sums.get("RedHerrings-windows.zip", "")
    lin_sha = sums.get("RedHerrings-linux.zip", "")
    has_win = "RedHerrings-windows.zip" in latest["assets"]
    mac_assets = [a for a in ("RedHerrings-macos-arm64.zip", "RedHerrings-macos-intel.zip") if a in latest["assets"]]
    mac_notarized = bool(MAC_NOTARIZED_SINCE) and vt(tag) >= vt(MAC_NOTARIZED_SINCE)

    def sha_block(sha, label):
        if not sha:
            return f'<p class="dl-muted">Checksum not published yet for {E(label)}.</p>'
        return f'<div class="dl-sha"><span class="dl-shalabel">SHA-256</span><code>{E(sha)}</code></div>'

    win_card = f'''
      <div class="dl-card">
        <div class="dl-os">Windows</div>
        <p class="dl-req">Windows 10 or 11, 64-bit. No installer: unzip and run <code>RedHerrings.exe</code>; it opens in your browser.</p>
        <a class="btn primary" href="{DL}/RedHerrings-windows.zip" data-goatcounter-click="download-windows">Download for Windows{(" · " + win_size) if win_size else ""}</a>
        {sha_block(win_sha, "Windows")}
        <details class="dl-verify"><summary>Verify the download</summary>
          <p>In PowerShell, in the folder you downloaded to:</p>
          <pre><code>(Get-FileHash .\\RedHerrings-windows.zip -Algorithm SHA256).Hash</code></pre>
          <p>The output must match the SHA-256 above (letter case doesn't matter).</p>
        </details>
        {('<p class="dl-signed">&#10003; Authenticode-signed by ' + E(PUBLISHER) + ' &mdash; Windows shows the publisher name on the run prompt.</p>') if signed else ''}
      </div>''' if has_win else f'''
      <div class="dl-card">
        <div class="dl-os">Windows</div>
        <p class="dl-req">The signed Windows build for {E(tag)} is being published. Check back shortly, or grab the <a href="{RELEASES_PAGE}">previous release</a>.</p>
      </div>'''

    lin_card = f'''
      <div class="dl-card">
        <div class="dl-os">Linux</div>
        <p class="dl-req">64-bit Linux with a recent glibc (Ubuntu 22.04, Debian 12, Fedora 38 or newer). Unzip and run <code>./RedHerrings</code>.</p>
        <a class="btn primary" href="{DL}/RedHerrings-linux.zip" data-goatcounter-click="download-linux">Download for Linux{(" · " + lin_size) if lin_size else ""}</a>
        {sha_block(lin_sha, "Linux")}
        <details class="dl-verify"><summary>Verify the download</summary>
          <p>In the folder you downloaded to:</p>
          <pre><code>curl -LO {DL}/SHA256SUMS.txt
sha256sum -c SHA256SUMS.txt --ignore-missing</code></pre>
          <p>It should print <code>RedHerrings-linux.zip: OK</code>.</p>
        </details>
      </div>'''

    mac_card = ""
    if mac_assets:
        links = "".join(
            f'<a class="btn primary" href="{DL}/{a}" data-goatcounter-click="download-{a[len("RedHerrings-"):-4]}">'
            f'Download for {"Apple silicon" if "arm64" in a else "Intel Mac"}{(" · " + mb(latest["assets"].get(a))) if latest["assets"].get(a) else ""}</a>'
            for a in mac_assets)
        shas = "".join(sha_block(sums.get(a, ""), a) for a in mac_assets)
        gate = ('<p class="dl-signed">&#10003; Signed with a Developer ID certificate and notarized by Apple.</p>' if mac_notarized else
                '<p class="dl-muted">First launch: right-click <code>RedHerrings</code> and choose <strong>Open</strong>, then Open again. macOS asks once for builds that are not yet notarized.</p>')
        mac_card = f'''
      <div class="dl-card">
        <div class="dl-os">macOS</div>
        <p class="dl-req">macOS 12 or newer. Pick the build for your Mac (Apple menu &rarr; About This Mac shows the chip). Unzip, then double-click <code>RedHerrings</code>; it opens Terminal and your browser.</p>
        <div class="dl-row">{links}</div>
        {shas}
        <details class="dl-verify"><summary>Verify the download</summary>
          <p>In Terminal, in the folder you downloaded to:</p>
          <pre><code>shasum -a 256 RedHerrings-macos-*.zip</code></pre>
          <p>The output must match the SHA-256 above.</p>
        </details>
        {gate}
      </div>'''

    it_signed = (f'allow it by <strong>publisher</strong> &mdash; an AppLocker, WDAC or Intune publisher rule for '
                 f'<em>{E(PUBLISHER)}</em> covers every release &mdash; or by the SHA-256 above.'
                 if signed else
                 'allow it by the SHA-256 above (a per-release hash rule), or ask us about publisher-signed builds.')

    # Release notes: latest open, older collapsed.
    notes_html = []
    for i, (v, ntag, ndate, body) in enumerate(notes):
        rel = releases.get(v, {})
        meta = dt.date.fromisoformat(ndate).strftime("%B %-d, %Y")
        link = f' &middot; <a href="{E(rel["url"])}">release</a>' if rel.get("url") else ""
        notes_html.append(
            f'<details class="dl-notes"{" open" if i == 0 else ""}>'
            f'<summary><strong>{E(ntag)}</strong> <span class="dl-muted">{E(meta)}{link}</span></summary>'
            f'<div class="dl-notesbody">{md_to_html(body)}</div></details>')

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Download Red Herrings {E(tag)} for Windows &amp; Linux | Red Herrings</title>
<meta name="description" content="Download Red Herrings {E(tag)} for Windows or Linux: a 30-day free trial with no key needed. Checksums, system requirements and release notes for every version.">
<link rel="canonical" href="https://redherrings.app/download.html">
<meta name="robots" content="index,follow">
<meta name="theme-color" content="#e3362b">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 64 64%27%3E%3Cpath fill=%27%23E5382F%27 d=%27M6 32c9-11 20-16 30-16 4 0 8 3 12 9 3-3 8.5-9.5 14.25-13.25C58.38 18.12 55.69 25.81 54.44 32c1.25 6.19 3.94 13.87 7.81 20.25C56.5 48.5 51 42 48 39c-4 6-8 9-12 9-10 0-21-5-30-16z%27/%3E%3C/svg%3E">
<link rel="icon" type="image/png" sizes="32x32" href="/img/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/img/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta property="og:title" content="Download Red Herrings {E(tag)}">
<meta property="og:description" content="Windows and Linux builds, checksums, requirements and release notes. 30-day free trial, no key needed.">
<meta property="og:url" content="https://redherrings.app/download.html">
<meta property="og:image" content="https://redherrings.app/img/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Red Herrings — randomized digital forensics and incident-response labs for the classroom.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://redherrings.app/img/og.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="site.css">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"SoftwareApplication","name":"Red Herrings","softwareVersion":"{E(tag.lstrip('v'))}","datePublished":"{E(date)}","operatingSystem":"Windows 10, Windows 11, Linux","applicationCategory":"EducationalApplication","offers":{{"@type":"Offer","price":"0","priceCurrency":"USD","description":"30-day free trial"}},"downloadUrl":"{DL}/RedHerrings-windows.zip","publisher":{{"@type":"Organization","name":"{E(PUBLISHER)}"}}}}
</script>
<style>
  .dl-head{{margin:8px 0 22px}}
  .dl-ver{{display:inline-flex;align-items:center;gap:10px;flex-wrap:wrap;font-size:15px;color:var(--ink-2,#5b6472)}}
  .dl-ver .chip{{font-weight:700}}
  .dl-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:18px;margin:18px 0 10px}}
  .dl-card{{border:1px solid var(--line,#e7e9ee);border-radius:16px;padding:22px 22px 18px;background:var(--panel,#fff)}}
  .dl-os{{font-size:22px;font-weight:800;letter-spacing:-.01em;margin-bottom:6px}}
  .dl-req{{color:var(--ink-2,#5b6472);font-size:14px;margin:0 0 14px}}
  .dl-card .btn{{display:inline-block;margin-bottom:14px}}
  .dl-sha{{display:flex;flex-direction:column;gap:4px;margin:0 0 10px}}
  .dl-shalabel{{font-size:11px;font-weight:700;letter-spacing:.06em;color:var(--ink-3,#8a93a3)}}
  .dl-sha code{{font-size:12px;word-break:break-all;padding:8px 10px;border-radius:8px;background:var(--panel2,rgba(127,127,127,.08));display:block}}
  .dl-verify summary{{cursor:pointer;font-weight:600;font-size:14px}}
  .dl-verify pre{{margin:8px 0;padding:10px 12px;border-radius:8px;background:var(--panel2,rgba(127,127,127,.08));overflow:auto;font-size:12.5px}}
  .dl-verify p{{font-size:14px;color:var(--ink-2,#5b6472);margin:6px 0}}
  .dl-signed{{font-size:14px;font-weight:600;color:#1c7a43;margin:10px 0 0}}
  .dl-lead{{margin:26px 0 0;padding:20px 22px;border:1px solid var(--line);border-radius:14px;background:var(--card);box-shadow:var(--shadow-sm)}}
  .dl-leadtext{{display:flex;flex-direction:column;gap:3px;margin-bottom:12px}}.dl-leadtext span{{color:var(--muted);font-size:14px;line-height:1.5}}
  .dl-leadrow{{display:flex;gap:10px;flex-wrap:wrap}}.dl-leadrow input[type=email]{{flex:1;min-width:220px;padding:11px 12px;border:1px solid var(--line);border-radius:10px;font:inherit;background:var(--card);color:var(--ink)}}
  .dl-hp{{position:absolute;left:-9999px;top:-9999px;height:0}}
  .dl-leadout{{display:none;margin-top:10px;font-weight:600;font-size:14px}}.dl-leadout.ok{{display:block;color:var(--ok)}}.dl-leadout.bad{{display:block;color:var(--bad)}}
  .dl-row{{display:flex;gap:10px;flex-wrap:wrap}}
  .dl-trust{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:26px 0}}
  .dl-trust div{{border-left:3px solid var(--accent,#E5382F);padding:4px 0 4px 14px;font-size:14px;color:var(--ink-2,#5b6472)}}
  .dl-trust strong{{display:block;color:var(--ink,#12151c);margin-bottom:2px}}
  .dl-notes{{border-top:1px solid var(--line,#e7e9ee);padding:14px 0}}
  .dl-notes summary{{cursor:pointer;font-size:17px}}
  .dl-notesbody{{padding:8px 0 4px 2px;font-size:15px}}
  .dl-notesbody h4{{margin:16px 0 6px;font-size:14px;letter-spacing:.04em;text-transform:uppercase;color:var(--ink-3,#8a93a3)}}
  .dl-notesbody ul{{padding-left:20px}} .dl-notesbody li{{margin:6px 0}}
  .dl-muted{{color:var(--ink-3,#8a93a3);font-weight:400;font-size:14px}}
  .dl-it{{margin:30px 0 10px;padding:18px 20px;border:1px solid var(--line,#e7e9ee);border-radius:14px;font-size:15px}}
</style>
<script>(function(){{try{{var t=localStorage.getItem('rh-theme');if(t==='dark'||t==='light')document.documentElement.setAttribute('data-theme',t);}}catch(e){{}}}})();</script>
</head>
<body>
<header></header>
<main class="wrap" id="main">
  <section>
    <div class="dl-head">
      <h1>Download Red Herrings</h1>
      <p class="sub">The desktop app runs entirely on your machine. It starts as a <strong>30-day free trial with no key needed</strong> &mdash; generate labs, run the student portal and grade a class before you buy.</p>
      <div class="dl-ver"><span class="chip">{E(tag)}</span><span>Released {E(nice_date)}</span><span>&middot;</span><a href="#release-notes">Release notes</a><span>&middot;</span><a href="{RELEASES_PAGE}">All versions</a></div>
    </div>

    <div class="dl-grid">{win_card}{mac_card}{lin_card}
    </div>

    <form class="dl-lead" id="dl-lead" novalidate>
      <div class="dl-leadtext"><strong>Want the getting-started guide in your inbox?</strong><span>Optional. One email now with the four steps from download to a graded class, a note a week in, and a reminder three days before the trial ends. Unsubscribe in one click.</span></div>
      <div class="dl-leadrow">
        <input type="email" name="email" placeholder="you@university.edu" autocomplete="email" aria-label="Email address" required>
        <input class="dl-hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
        <button class="btn" type="submit">Send the guide</button>
      </div>
      <div class="dl-leadout" role="status" aria-live="polite"></div>
    </form>

    <div class="dl-trust">
      <div><strong>Runs locally</strong>Generation and grading never leave your machine. The only network call is license activation. <a href="trust.html">Trust &amp; security</a></div>
      <div><strong>Verifiable</strong>Every release ships <a href="{DL}/SHA256SUMS.txt">SHA256SUMS.txt</a>. Certificates students earn can be checked at <a href="verify.html">verify</a>.</div>
      <div><strong>Then activate</strong>Buy a plan and paste the emailed key under <em>Settings &rarr; Licensing</em>. Air-gapped machines activate offline. <a href="/#pricing">See plans</a></div>
    </div>

    <div class="dl-it">
      <strong>Installing on a managed machine?</strong> Your IT team can {it_signed} The app needs no admin rights and no installer; it unzips to a folder and listens only on localhost. Full details on the <a href="trust.html">Trust &amp; security</a> page.
    </div>
  </section>

  <section id="release-notes">
    <h2>Release notes</h2>
    <p class="sub">What changed in each version. Every release keeps the full case library generating and verifying.</p>
    {"".join(notes_html)}
  </section>
</main>
<script>
(function(){{
  var f=document.getElementById('dl-lead');if(!f)return;
  var out=f.querySelector('.dl-leadout'),btn=f.querySelector('button');
  var plat=/Windows/i.test(navigator.userAgent)?'windows':/Linux/i.test(navigator.userAgent)?'linux':'';
  f.addEventListener('submit',function(e){{
    e.preventDefault();var email=f.email.value.trim();
    if(!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)){{out.className='dl-leadout bad';out.textContent='Please enter a valid email address.';return;}}
    btn.disabled=true;
    fetch('https://account.redherrings.app/api/v1/leads',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{email:email,platform:plat,website:f.website.value}})}})
    .then(function(r){{if(!r.ok)throw 0;out.className='dl-leadout ok';out.textContent='Sent. Check your inbox for the guide.';f.email.value='';
      if(window.goatcounter&&goatcounter.count)goatcounter.count({{path:'lead-download',event:true}});}})
    .catch(function(){{out.className='dl-leadout bad';out.textContent='Could not send right now. The guide is also at /help.html.';}})
    .finally(function(){{btn.disabled=false;}});
  }});
}})();
</script>
<footer></footer>
<script data-goatcounter="https://redherrings.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<script src="nav.js" defer></script>
<script src="theme.js" defer></script>
</body>
</html>
'''


def main():
    if not os.path.exists(CHANGELOG):
        sys.exit(f"CHANGELOG not found at {CHANGELOG} (set RH_CHANGELOG)")
    releases = fetch_releases()
    if not releases:
        sys.exit("no releases found")
    latest = releases[max(releases)]
    notes = sorted(parse_changelog(CHANGELOG), key=lambda e: e[0], reverse=True)
    sums = fetch_sums(latest["tag"])
    out = os.path.join(ROOT, "download.html")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page(latest, releases, notes, sums))
    print(f"wrote download.html: {latest['tag']} ({latest['date']}), {len(notes)} changelog entries, sums={'yes' if sums else 'no'}, signed={bool(SIGNED_SINCE) and max(releases) >= vt(SIGNED_SINCE)}")
    # Keep the homepage's version mention in sync.
    idx = os.path.join(ROOT, "index.html")
    s = open(idx, encoding="utf-8").read()
    s2 = re.sub(r'(<strong data-dl-version>)[^<]*(</strong>)', rf'\g<1>{E(latest["tag"])}\g<2>', s)
    if s2 != s:
        open(idx, "w", encoding="utf-8").write(s2); print("index.html version updated")


if __name__ == "__main__":
    main()
