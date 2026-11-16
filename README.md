# Red Herrings, website

The public website for **Red Herrings**, a DFIR teaching tool that turns one
authored case into a unique, auto-verified digital forensics and incident
response lab for every student. One case becomes a different, self-grading lab
per learner, so most copied answers are wrong answers, and the whole class is graded
at once.

**Live site: https://redherrings.app**

- How it works: https://redherrings.app/how.html
- Case library (83 DF & IR cases): https://redherrings.app/cases.html
- Learning pathways & certification prep: https://redherrings.app/pathways.html
- MITRE ATT&CK coverage: https://redherrings.app/attack.html
- Free sample lab, a real Windows insider-USB case (disk image, registry,
  EVTX, Prefetch, LNK and the worksheet):
  https://redherrings.app/sample.html
- Blog, DFIR teaching notes: https://redherrings.app/blog/

## About this repo

Static marketing site: plain HTML, CSS and vanilla JavaScript, deployed with
GitHub Pages from `main`. The shared header and footer are generated across all
pages by the `tools-apply-nav.py` and `tools-apply-footer.py` scripts; design
tokens live in `site.css`.

## Analytics

Pages count visits with GoatCounter. The tag loads GoatCounter's versioned
script, `https://gc.zgo.at/count.v5.js`, with `crossorigin="anonymous"` and a
SHA-384 `integrity` hash, so the browser runs it only if the bytes match.
GoatCounter never changes a versioned file. To move to a newer version, take
its URL and hash from https://www.goatcounter.com/help/countjs-versions, check
the hash against the downloaded file
(`openssl dgst -sha384 -binary count.vN.js | openssl base64 -A`), and replace
the tag on every page and in the `tools-*` generators that write it. Pages with
a query string that matters (`thanks.html`) carry a canonical link, so only the
path is counted.
