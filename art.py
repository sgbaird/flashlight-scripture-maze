"""Story pictures (from art/, see fetch_art.py) as pygame surfaces, with drawn stand-ins."""
import json
import os

import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "art")
GOLD = (190, 155, 80)
_cache = {}


def _image(slug, n):
    key = (slug, n)
    if key not in _cache:
        path = os.path.join(ART, slug, "%02d.jpg" % n)
        try:
            _cache[key] = pygame.image.load(path).convert()
        except (pygame.error, FileNotFoundError):
            _cache[key] = None
    return _cache[key]


def have_art(story):
    return _image(story.slug, 1) is not None


def story_text(story):
    try:
        with open(os.path.join(ART, story.slug, "story.json"), encoding="utf-8") as f:
            return json.load(f).get("paragraphs", [])
    except (OSError, ValueError):
        return []


def scripture(story):
    """[(label, text), ...] for the story's scripture reference (art/<slug>/scripture.json), or []."""
    try:
        with open(os.path.join(ART, story.slug, "scripture.json"), encoding="utf-8") as f:
            return [tuple(v) for v in json.load(f).get("verses", [])]
    except (OSError, ValueError):
        return []


def panels(story):
    """The chapter's panels as the book shows them: [{'image': n, 'text': [...], 'refs': [{'label',
    'verses': [[label, text], ...]}, ...]}, ...] from art/<slug>/story.json, or [] (run fetch_art.py)."""
    try:
        with open(os.path.join(ART, story.slug, "story.json"), encoding="utf-8") as f:
            return json.load(f).get("panels", [])
    except (OSError, ValueError):
        return []


def dimmed(surface, factor):
    """A copy of surface with its colours scaled by factor (keeps the flashlight the brightest thing)."""
    out = surface.copy()
    v = max(0, min(255, int(255 * factor)))
    out.fill((v, v, v, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return out


def picture(story, n, box, factor=0.85):
    """Picture n of the story scaled to fit box (w, h), dimmed, or None."""
    key = ("picture", story.slug, n, box, factor)
    if key not in _cache:
        img = _image(story.slug, n)
        if img is None:
            return None
        w, h = img.get_size()
        k = min(box[0] / w, box[1] / h)
        _cache[key] = dimmed(pygame.transform.smoothscale(img, (int(w * k), int(h * k))), factor)
    return _cache[key]


def aspect(story, n):
    img = _image(story.slug, n)
    return img.get_width() / img.get_height() if img is not None else 1.5


def card(story, box, factor=0.85):
    """The story picture scaled to fit box (w, h), or None."""
    return picture(story, story.card, box, factor) or picture(story, 1, box, factor)


def thumb(story, n, diameter, factor=0.75):
    """A round thumbnail of the middle of picture n, or None."""
    key = ("thumb", story.slug, n, diameter, factor)
    if key not in _cache:
        img = _image(story.slug, n)
        if img is None:
            return None
        w, h = img.get_size()
        side = min(w, h)
        _cache[key] = _round(img.subsurface(pygame.Rect((w - side) // 2, (h - side) // 2, side, side)), diameter, factor)
    return _cache[key]


def _round(square, diameter, factor):
    sq = pygame.transform.smoothscale(square, (diameter, diameter))
    mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    pygame.draw.circle(mask, (255, 255, 255, 255), (diameter // 2, diameter // 2), diameter // 2)
    surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    surf.blit(sq, (0, 0))
    surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return dimmed(surf, factor)


def figure(color, diameter, label=""):
    """Drawn stand-in for a portrait: a robed figure in a circle."""
    d = diameter
    s = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.circle(s, (30, 36, 70), (d // 2, d // 2), d // 2)
    pygame.draw.polygon(s, color, [(d * 0.5, d * 0.42), (d * 0.22, d * 0.92), (d * 0.78, d * 0.92)])
    pygame.draw.circle(s, (225, 190, 150), (d // 2, int(d * 0.33)), int(d * 0.15))
    pygame.draw.circle(s, GOLD, (d // 2, d // 2), d // 2, max(2, d // 18))
    if label:
        f = pygame.font.Font(None, max(14, d // 3))
        t = f.render(label[:1], True, (240, 230, 200))
        s.blit(t, t.get_rect(center=(d // 2, int(d * 0.7))))
    return s


def portrait(story, which, diameter, factor=0.7):
    """Circular crop of a story picture for the walker ('player') or the goal ('goal')."""
    crop = getattr(story, which)
    key = ("portrait", story.slug, which, diameter, factor)
    if key in _cache:
        return _cache[key]
    img = _image(story.slug, crop[0]) if crop else None
    if img is None:
        color = story.color if which == "player" else (200, 170, 80)
        surf = figure(color, diameter, story.player_name if which == "player" else "")
    else:
        n, cx, cy, r = crop
        w, h = img.get_size()
        rad = r * h
        src = pygame.Rect(int(cx * w - rad), int(cy * h - rad), int(2 * rad), int(2 * rad)).clip(img.get_rect())
        surf = _round(img.subsurface(src), diameter, factor)
        pygame.draw.circle(surf, GOLD, (diameter // 2, diameter // 2), diameter // 2, max(2, diameter // 18))
    _cache[key] = surf
    return surf
