import re

from maze import SIZES
from stories import STORIES

ICONS = {"rope", "stone", "vegetable", "grain", "heart"}


def test_stories_are_complete():
    slugs = [s.slug for s in STORIES]
    assert len(slugs) == len(set(slugs))
    for s in STORIES:
        assert re.fullmatch(r"[a-z0-9-]+", s.slug)
        assert re.fullmatch(r"[a-z0-9-]+", s.song[1])
        assert s.size in SIZES
        assert s.title and s.task and s.ending and s.ref
        if s.items:
            name, count, icon = s.items
            assert icon in ICONS and 1 <= count <= 6
        for crop in (s.player, s.goal):
            if crop:
                n, cx, cy, r = crop
                assert n >= 1 and 0 <= cx <= 1 and 0 <= cy <= 1 and 0 < r <= 0.5
