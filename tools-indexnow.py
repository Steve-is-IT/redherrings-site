#!/usr/bin/env python3
"""Submit the site's URLs to IndexNow (Bing, Yandex, et al.) for fast indexing.
Reads the loc entries from sitemap.xml and posts them in one batch. Re-run
after publishing new pages. The key file (<key>.txt) must be live first."""
import json
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
HOST = "redherrings.app"
KEY = "8dd77cac221c125ca3158c7be2c8f39c"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINT = "https://api.indexnow.org/indexnow"


def sitemap_urls():
    with open(os.path.join(ROOT, "sitemap.xml")) as fh:
        return re.findall(r"<loc>([^<]+)</loc>", fh.read())


def main():
    urls = sitemap_urls()
    body = json.dumps({
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }).encode()
    req = urllib.request.Request(ENDPOINT, data=body,
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"IndexNow submitted {len(urls)} URLs -> HTTP {r.status}")
    except urllib.error.HTTPError as e:
        print(f"IndexNow HTTP {e.code}: {e.read().decode(errors='replace')[:300]}")


if __name__ == "__main__":
    main()
