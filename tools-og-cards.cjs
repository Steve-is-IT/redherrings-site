#!/usr/bin/env node
/* Render the Open Graph link-preview cards with Playwright (Node) and point
   the pages at them. Node port of tools-og-cards.py (Python Playwright is not
   available in every environment; Node's is). Three cards: home (default),
   cases, download. Each saved as img/og/<name>-<hash>.png, with the hash of
   the PNG bytes forcing social scrapers to refetch. */
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const { chromium } = require("playwright");

const ROOT = __dirname;
const OUT = path.join(ROOT, "img", "og");
const FONTS = "https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Public+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600;800&display=swap";

// Brand mark (mosaic), sized for the card brand row.
let MARK = fs.readFileSync(path.join(ROOT, "img", "brand", "mark.svg"), "utf8")
  .replace('width="200" height="112"', 'width="96" height="54"')
  .replace(/\n/g, " ").trim();

const BASE_CSS = `
*{box-sizing:border-box;margin:0}html,body{width:1200px;height:630px;overflow:hidden}
body{font-family:"Public Sans",-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#111a26;background:#f3f6fa;position:relative;-webkit-font-smoothing:antialiased}
.wash{position:absolute;inset:0;background:radial-gradient(900px 420px at 85% -10%,rgba(31,95,191,.14),transparent 60%),radial-gradient(700px 380px at -5% 110%,rgba(212,42,42,.10),transparent 60%)}
.card{position:absolute;inset:0;padding:40px 0 0 68px;display:grid;grid-template-columns:560px 1fr;gap:36px}
.brand{display:flex;align-items:center;gap:14px;font-family:"Sora",sans-serif;font-weight:700;font-size:30px;letter-spacing:-.01em}
.kick{margin-top:28px;font-family:"JetBrains Mono",Menlo,Consolas,monospace;font-size:15px;letter-spacing:.14em;text-transform:uppercase;color:#d42a2a;font-weight:600}
h1{margin-top:10px;font-family:"JetBrains Mono",Menlo,Consolas,monospace;font-weight:800;font-size:43px;line-height:1.14;letter-spacing:-.02em}
h1 em{font-style:normal;color:#d42a2a}
.lede{margin-top:16px;font-size:22px;line-height:1.4;color:#3e4a5a;max-width:510px}
.url{position:absolute;left:68px;bottom:34px;font-family:"Sora",sans-serif;font-weight:700;font-size:20px}
.shot{position:relative;margin-top:36px;height:560px;border-radius:14px 0 0 0;overflow:hidden;border:1px solid #cfd8e4;border-right:0;box-shadow:0 24px 60px -20px rgba(17,26,38,.35);background:#fff}
.shot .bar{height:30px;background:#eef2f7;border-bottom:1px solid #e3e9f1;display:flex;align-items:center;gap:7px;padding-left:14px}
.shot .bar i{width:10px;height:10px;border-radius:50%;display:block}
.shot img{display:block;width:1000px;height:auto}
.badges{margin-top:22px;display:flex;gap:10px;flex-wrap:wrap;max-width:520px}
.badge{font-size:16px;font-weight:600;padding:9px 15px;border-radius:999px;background:#fff;border:1px solid #cfd8e4;box-shadow:0 1px 2px rgba(17,26,38,.06)}
.badge.red{background:#d42a2a;border-color:#d42a2a;color:#fff}
.gold{color:#8a6508}
.bottom{position:absolute;left:0;right:0;bottom:0;height:8px;background:#d42a2a}
`;

const shot = (img) =>
  `<div class="shot"><div class="bar"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i>` +
  `<i style="background:#28c840"></i></div><img src="file://${ROOT}/img/${img}"></div>`;

const CARDS = {
  home: [
    `<div class="kick">Digital Forensics &amp; Incident Response</div>` +
    `<h1>Investigate real evidence, and build the DFIR skills to show for it.</h1>` +
    `<p class="lede">Disk, memory, network, mobile and cloud evidence, worked in the real tools.</p>` +
    `<div class="badges"><span class="badge">Forensics &amp; incident response</span>` +
    `<span class="badge red">Runs fully offline</span></div>`,
    shot("slides/slide-results.jpg"),
    null,
  ],
  cases: [
    `<div class="kick gold">Case library</div>` +
    `<h1>Dozens of cases, one per student.</h1>` +
    `<p class="lede">First Look triage to Marquee capstone, in forensics and incident response, mapped to GIAC, CompTIA and MITRE ATT&amp;CK.</p>` +
    `<div class="badges"><span class="badge">First Look cases free</span>` +
    `<span class="badge">Windows &middot; macOS &middot; Linux</span></div>`,
    shot("slides/slide-library.jpg"),
    ["cases.html", "tools-gen-cases.py"],
  ],
  download: [
    `<div class="kick">Offline &amp; air-gapped</div>` +
    `<h1>Runs air-gapped, in a SOC or a secure facility.</h1>` +
    `<p class="lede">Generated and graded entirely on your own machines, with no account, cloud or network connection, so nothing ever leaves your environment.</p>` +
    `<div class="badges"><span class="badge red">No internet required</span>` +
    `<span class="badge">Windows &middot; macOS &middot; Linux</span></div>`,
    shot("slides/slide-generate.jpg"),
    ["download.html", "tools-gen-download.py"],
  ],
};

const pageHtml = (left, right) =>
  `<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="${FONTS}">` +
  `<style>${BASE_CSS}</style></head><body><div class="wash"></div><div class="card">` +
  `<div><div class="brand">${MARK}<span>Red Herrings</span></div>${left}</div>${right}</div>` +
  `<div class="url">redherrings.app</div><div class="bottom"></div></body></html>`;

const REF = /https:\/\/redherrings\.app\/img\/(?:og[^"\s]*\.png)/g;

function walk(dir, out) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === "node_modules" || e.name === ".git") continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else if (e.name.endsWith(".html") || /^tools-gen-.*\.py$/.test(e.name)) out.push(p);
  }
  return out;
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const tmp = path.join(OUT, "_render.html");
  const names = {};
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 1200, height: 630 } });
  for (const [name, [left, right]] of Object.entries(CARDS)) {
    fs.writeFileSync(tmp, pageHtml(left, right), "utf8");
    await pg.goto("file://" + tmp, { waitUntil: "networkidle" });
    await pg.waitForTimeout(600);
    const png = await pg.screenshot();
    const h = crypto.createHash("sha256").update(png).digest("hex").slice(0, 8);
    const fn = `${name}-${h}.png`;
    fs.writeFileSync(path.join(OUT, fn), png);
    names[name] = fn;
    for (const f of fs.readdirSync(OUT)) {
      if (f.startsWith(`${name}-`) && f.endsWith(".png") && f !== fn) fs.unlinkSync(path.join(OUT, f));
    }
  }
  await b.close();
  fs.existsSync(tmp) && fs.unlinkSync(tmp);

  const claimed = {};
  for (const [name, [, , owners]] of Object.entries(CARDS))
    for (const o of owners || []) claimed[path.join(ROOT, o)] = name;

  let changed = 0;
  for (const f of walk(ROOT, [])) {
    const name = claimed[f] || "home";
    const url = `https://redherrings.app/img/og/${names[name]}`;
    const s = fs.readFileSync(f, "utf8");
    const t = s.replace(REF, url);
    if (t !== s) { fs.writeFileSync(f, t, "utf8"); changed++; }
  }
  for (const [n, fn] of Object.entries(names)) console.log(`${n}: img/og/${fn}`);
  console.log(`updated ${changed} files`);
})();
