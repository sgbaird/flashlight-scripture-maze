"""Download the Old Testament Stories pictures and text used by the game into art/.

The pictures and text belong to Intellectual Reserve, Inc. (churchofjesuschrist.org), whose
terms allow personal, noncommercial use. They are downloaded onto your own computer and kept
out of the repository (art/ is git-ignored); the repository only holds the links.

    python fetch_art.py            # all stories in stories.py
    python fetch_art.py daniel-and-the-lions-den
"""
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

from stories import STORIES

API = "https://www.churchofjesuschrist.org/study/api/v3/language-pages/type/content?lang=eng&uri={uri}"
IMG = "https://www.churchofjesuschrist.org/imgs/{id}/full/%21{w}%2C/0/default"
MANUAL = "/manual/old-testament-stories-2022/"
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "art")
UA = {"User-Agent": "flashlight-scripture-maze (personal use; github.com/sgbaird/flashlight-scripture-maze)"}


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def story_page(slug):
    """(paragraphs, image ids in page order) for an Old Testament Stories chapter."""
    data = json.loads(_get(API.format(uri=urllib.parse.quote(MANUAL + slug))))
    body = data["content"]["body"]
    ids = []
    for m in re.finditer(r"/imgs/([0-9a-f]{40})/", body):
        if m.group(1) not in ids:
            ids.append(m.group(1))
    paras = []
    for p in re.findall(r"<p[^>]*>(.*?)</p>", body, re.S):
        text = html.unescape(re.sub(r"<[^>]+>", "", p)).strip()
        if text:
            paras.append(re.sub(r"\s+", " ", text))
    return paras, ids


def fetch(slug, width=1280):
    out = os.path.join(ART, slug)
    os.makedirs(out, exist_ok=True)
    paras, ids = story_page(slug)
    for i, img_id in enumerate(ids, 1):
        path = os.path.join(out, "%02d.jpg" % i)
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(_get(IMG.format(id=img_id, w=width)))
            time.sleep(0.3)
    with open(os.path.join(out, "story.json"), "w", encoding="utf-8") as f:
        json.dump({"slug": slug, "paragraphs": paras, "images": len(ids),
                   "source": "https://www.churchofjesuschrist.org/study" + MANUAL + slug}, f, indent=1)
    return len(ids)


def main(argv):
    slugs = argv or [s.slug for s in STORIES]
    ok = True
    for slug in dict.fromkeys(slugs):
        try:
            n = fetch(slug)
            print("%-34s %d pictures" % (slug, n))
        except Exception as e:  # keep going; the game falls back to drawn figures
            ok = False
            print("%-34s FAILED: %s" % (slug, e))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
