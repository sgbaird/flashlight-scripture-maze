"""The story-page parser, on made-up HTML shaped like the Old Testament Stories pages (no church text here)."""
from fetch_art import parse_panels, parse_ref_link

IMG_A = "a" * 40
IMG_B = "b" * 40
PAGE = f"""
<p class="title-number" id="title_number1"><a class="scripture-ref" href="/study/scriptures/ot/jer/1">Book 1</a></p>
<video poster="https://www.churchofjesuschrist.org/imgs/{'c' * 40}/full/x"></video>
<h1 id="title1">A Story</h1><p class="intro" id="intro1">An intro</p>
<div class="body-block">
<img alt="one" id="img1" src="https://www.churchofjesuschrist.org/imgs/{IMG_A}/full/x" data-img-id="{IMG_A}"/>
<p id="p1">First words.</p>
<p id="p2"><a class="scripture-ref" href="/study/scriptures/ot/jer/6?lang=eng&amp;id=p1-p19#p1">Jeremiah 6:1–19</a>;
<a class="scripture-ref" href="/study/scriptures/ot/jer/8?lang=eng">8–9</a>;
<a class="scripture-ref" href="/study/scriptures/ot/jer/36?lang=eng&amp;id=p1-p2%2C27-p32#p1">36:1–2, 27–32</a></p>
<img alt="two" id="img2" src="https://www.churchofjesuschrist.org/imgs/{IMG_B}/full/x" data-img-id="{IMG_B}"/>
<p id="p3">Second <em>words</em>.</p>
<p id="p4"><a class="scripture-ref" href="/study/scriptures/pgp/moses/8?lang=eng&amp;id=p25#p25">Moses 8:25</a></p>
</div>
"""


def test_panels_pair_each_picture_with_its_words_and_references():
    panels = parse_panels(PAGE)
    assert [p["image"] for p in panels] == [2, 3]   # picture 1 is the chapter's portrait (the video poster)
    assert panels[0]["text"] == ["First words."] and panels[1]["text"] == ["Second words."]
    labels = [r["label"] for r in panels[0]["refs"]]
    assert labels == ["Jeremiah 6:1–19", "Jeremiah 8–9", "Jeremiah 36:1–2, 27–32"]   # the book name filled in
    assert panels[0]["refs"][2]["ranges"] == [[1, 2], [27, 32]]
    assert panels[1]["refs"][0]["path"] == "/scriptures/pgp/moses/8"


def test_ref_link_without_verses_is_the_whole_chapter():
    ref = parse_ref_link("/study/scriptures/ot/jer/8?lang=eng", "Jeremiah 8")
    assert ref["chapter"] == 8 and ref["ranges"] == []
