"""Download the Old Testament Stories pictures and text, and the songs' instrumental
accompaniments (Children's Songbook, no words), used by the activity into art/.

The pictures, text and music belong to Intellectual Reserve, Inc. (churchofjesuschrist.org), whose
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
import urllib.error
import urllib.request

from stories import STORIES

API = "https://www.churchofjesuschrist.org/study/api/v3/language-pages/type/content?lang=eng&uri={uri}"
IMG = "https://www.churchofjesuschrist.org/imgs/{id}/full/%21{w}%2C/0/default"
MANUAL = "/manual/old-testament-stories-2022/"
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "art")
MUSIC_DIR = os.path.join(ART, "music")
SONG = "https://www.churchofjesuschrist.org/media/music/songs/{slug}?lang=eng"
UA = {"User-Agent": "flashlight-scripture-maze (personal use; github.com/sgbaird/flashlight-scripture-maze)"}
# the music pages refuse requests without a browser-style agent
UA_MUSIC = {"User-Agent": "Mozilla/5.0 (compatible; flashlight-scripture-maze; personal use)"}


def _get(url, timeout=30, headers=UA, tries=4):
    for attempt in range(tries):  # the server sometimes resets connections; wait and try again
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except (urllib.error.URLError, ConnectionError):
            if attempt == tries - 1:
                raise
            time.sleep(2 * (attempt + 1))


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


BOOKS = {"Genesis": "gen", "Exodus": "ex", "Ruth": "ruth", "1 Samuel": "1-sam", "Esther": "esth",
         "Jeremiah": "jer", "Daniel": "dan", "Jonah": "jonah"}
SCRIPTURE = "/scriptures/ot/{book}/{chapter}"


def parse_ref(ref):
    """'Genesis 6:13-22; 7:1-16' -> [('gen', 6, [(13, 22)]), ('gen', 7, [(1, 16)])]."""
    out, book = [], None
    for part in ref.replace("–", "-").split(";"):
        m = re.match(r"\s*(?:(.*?)\s+)?(\d+):(.+)$", part)
        if not m:
            raise ValueError("cannot read reference %r" % ref)
        if m.group(1):
            book = BOOKS[m.group(1)]
        ranges = []
        for r in m.group(3).split(","):
            a, _, b = r.strip().partition("-")
            ranges.append((int(a), int(b or a)))
        out.append((book, int(m.group(2)), ranges))
    return out


def fetch_scripture(story):
    """The verses of the story's reference (scripture text) as art/<slug>/scripture.json."""
    verses = []
    for book, chapter, ranges in parse_ref(story.ref):
        uri = SCRIPTURE.format(book=book, chapter=chapter)
        body = json.loads(_get(API.format(uri=urllib.parse.quote(uri))))["content"]["body"]
        for m in re.finditer(r'<p[^>]*class="verse"[^>]*data-eng-ref="(\d+):(\d+)"[^>]*>(.*?)</p>', body, re.S):
            v = int(m.group(2))
            if any(a <= v <= b for a, b in ranges):
                text = re.sub(r'<span class="(verse-number|para-mark)">.*?</span>', "", m.group(3))
                text = re.sub(r"<sup[^>]*>.*?</sup>", "", text)
                text = html.unescape(re.sub(r"<[^>]+>", "", text))
                verses.append(["%d:%d" % (chapter, v), re.sub(r"\s+", " ", text).strip()])
    if not verses:
        raise ValueError("no verses found for %s" % story.ref)
    os.makedirs(os.path.join(ART, story.slug), exist_ok=True)
    with open(os.path.join(ART, story.slug, "scripture.json"), "w", encoding="utf-8") as f:
        json.dump({"ref": story.ref, "verses": verses,
                   "source": "https://www.churchofjesuschrist.org/study" + SCRIPTURE.format(
                       book=parse_ref(story.ref)[0][0], chapter=parse_ref(story.ref)[0][1])}, f, indent=1)
    return len(verses)


def fetch_song(title, slug):
    """The song's instrumental accompaniment (no words) as art/music/<slug>.mp3."""
    path = os.path.join(MUSIC_DIR, slug + ".mp3")
    if os.path.exists(path):
        return path
    page = _get(SONG.format(slug=slug), headers=UA_MUSIC).decode("utf-8", "replace")
    found = re.search(r"<title>([^<]*)", page)
    page_title = found and html.unescape(found.group(1)).strip().replace("’", "'")
    if not page_title or page_title.lower() != title.lower():
        raise ValueError("song page title is %r, not %r" % (found and found.group(1), title))
    url = re.search(r'"assetType":"AUDIO_ACCOMPANIMENT","distributionUrl":"([^"]+\.mp3)"', page)
    if not url:
        raise ValueError("no instrumental recording on the song page")
    os.makedirs(MUSIC_DIR, exist_ok=True)
    data = _get(url.group(1), timeout=120, headers=UA_MUSIC)
    with open(path, "wb") as f:
        f.write(data)
    return path


def main(argv):
    slugs = argv or [s.slug for s in STORIES]
    ok = True
    for slug in dict.fromkeys(slugs):
        try:
            n = fetch(slug)
            story = next((s for s in STORIES if s.slug == slug), None)
            v = fetch_scripture(story) if story else 0
            print("%-34s %d pictures, %d verses" % (slug, n, v))
        except Exception as e:  # keep going; the activity falls back to drawn figures
            ok = False
            print("%-34s FAILED: %s" % (slug, e))
    songs = {s.song for s in STORIES if s.slug in slugs}
    for title, song_slug in sorted(songs):
        try:
            fetch_song(title, song_slug)
            print("%-34s music" % song_slug)
            time.sleep(1)
        except Exception as e:  # keep going; the activity is quiet without it
            ok = False
            print("%-34s music FAILED: %s" % (song_slug, e))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
