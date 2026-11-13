#!/usr/bin/env python3
"""Set every sitemap.xml <lastmod> to the date its page last changed.

The date is the page's last commit (git log -1 --format=%cs), or today when the
page has uncommitted changes. A <url> with no <lastmod> gets one. Run it after
committing page changes, then commit sitemap.xml.
"""
import datetime
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://redherrings.app/"


def page_file(loc):
    path = loc[len(BASE):] if loc.startswith(BASE) else loc
    if path == "" or path.endswith("/"):
        path += "index.html"
    return path


def changed(path):
    def git(*a):
        return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True).stdout.strip()
    if git("status", "--porcelain", "--", path):
        return datetime.date.today().isoformat()
    return git("log", "-1", "--format=%cs", "--", path)


def main():
    out = os.path.join(ROOT, "sitemap.xml")
    xml = open(out, encoding="utf-8").read()
    missing = []

    def fix(m):
        url = m.group(0)
        loc = re.search(r"<loc>([^<]+)</loc>", url).group(1)
        path = page_file(loc)
        if not os.path.exists(os.path.join(ROOT, path)):
            missing.append(loc)
            return url
        day = changed(path)
        if not day:
            return url
        if "<lastmod>" in url:
            return re.sub(r"<lastmod>[^<]*</lastmod>", f"<lastmod>{day}</lastmod>", url)
        return url.replace("</loc>", f"</loc><lastmod>{day}</lastmod>", 1)

    xml = re.sub(r"<url>.*?</url>", fix, xml, flags=re.S)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(xml)
    n = xml.count("<url>")
    print(f"wrote sitemap.xml: {n} urls, {n - xml.count('<lastmod>')} without lastmod")
    for loc in missing:
        print(f"  ! no file for {loc}")


if __name__ == "__main__":
    main()
