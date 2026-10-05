# Red Herrings — website

The public website for **Red Herrings**, a DFIR teaching tool that turns one
authored case into a unique, auto-verified digital forensics and incident
response lab for every student. One case becomes a different, self-grading lab
per learner, so copied answers are wrong answers, and the whole class is graded
at once.

**Live site: https://redherrings.app**

- How it works: https://redherrings.app/how.html
- Case library (67 DF & IR cases): https://redherrings.app/cases.html
- Learning pathways & certification prep: https://redherrings.app/pathways.html
- MITRE ATT&CK coverage: https://redherrings.app/attack.html
- Free sample lab — a real Windows insider-USB case (disk image, registry,
  EVTX, prefetch, LNK, worksheet and a verified key):
  https://redherrings.app/sample.html
- Blog — DFIR teaching notes: https://redherrings.app/blog/

## About this repo

Static marketing site: plain HTML, CSS and vanilla JavaScript, deployed with
GitHub Pages from `main`. The shared header and footer are generated across all
pages by the `tools-apply-nav.py` and `tools-apply-footer.py` scripts; design
tokens live in `site.css`.
