"""Small drawn pictures for the mazes: animals to gather, goal pictures and a little scenery.

Drawn with pygame shapes (no downloaded art), in muted colours so the flashlight stays the brightest
thing the camera sees. Each function draws centred on (x, y) at about `s` pixels across.
"""
import math
import random

import pygame


def _shade(color, k):
    return tuple(max(0, min(255, int(c * k))) for c in color)


# ----------------------------------------------------------------------------- animals for Noah

def sheep(surface, x, y, s):
    wool, dark = (175, 170, 160), (70, 60, 55)
    for dx in (-0.3, 0, 0.3):
        pygame.draw.line(surface, dark, (x + s * dx * 0.8, y + s * 0.1), (x + s * dx * 0.8, y + s * 0.38), max(2, s // 14))
    for dx, dy, r in ((-0.22, 0, 0.2), (0, -0.08, 0.22), (0.2, 0, 0.2), (0, 0.08, 0.2), (-0.1, 0.04, 0.2)):
        pygame.draw.circle(surface, wool, (int(x + s * dx), int(y + s * dy)), int(s * r))
    pygame.draw.ellipse(surface, dark, (x + s * 0.28, y - s * 0.2, s * 0.22, s * 0.17))


def elephant(surface, x, y, s):
    grey, dark = (120, 120, 128), (85, 85, 92)
    for dx in (-0.25, -0.08, 0.1, 0.25):
        pygame.draw.rect(surface, dark, (x + s * dx - s * 0.05, y + s * 0.05, s * 0.1, s * 0.33))
    pygame.draw.ellipse(surface, grey, (x - s * 0.38, y - s * 0.25, s * 0.7, s * 0.45))
    pygame.draw.circle(surface, grey, (int(x + s * 0.32), int(y - s * 0.12)), int(s * 0.16))
    pygame.draw.ellipse(surface, dark, (x + s * 0.18, y - s * 0.24, s * 0.16, s * 0.24))  # ear
    pygame.draw.line(surface, grey, (x + s * 0.44, y - s * 0.06), (x + s * 0.47, y + s * 0.3), max(3, s // 9))


def giraffe(surface, x, y, s):
    tan, spot = (190, 150, 80), (125, 90, 50)
    for dx in (-0.2, -0.07, 0.07, 0.2):
        pygame.draw.line(surface, tan, (x + s * dx, y + s * 0.05), (x + s * dx, y + s * 0.42), max(2, s // 14))
    pygame.draw.ellipse(surface, tan, (x - s * 0.28, y - s * 0.12, s * 0.52, s * 0.25))
    pygame.draw.line(surface, tan, (x + s * 0.18, y - s * 0.05), (x + s * 0.3, y - s * 0.42), max(4, s // 8))
    pygame.draw.ellipse(surface, tan, (x + s * 0.24, y - s * 0.5, s * 0.2, s * 0.12))
    for dx, dy in ((-0.15, -0.04), (0.0, 0.0), (0.12, -0.05)):
        pygame.draw.circle(surface, spot, (int(x + s * dx), int(y + s * dy)), max(2, int(s * 0.04)))


def dove(surface, x, y, s):
    white, grey = (180, 180, 175), (120, 120, 120)
    pygame.draw.ellipse(surface, white, (x - s * 0.3, y - s * 0.12, s * 0.55, s * 0.26))
    pygame.draw.circle(surface, white, (int(x + s * 0.25), int(y - s * 0.1)), int(s * 0.11))
    pygame.draw.polygon(surface, grey, [(x - s * 0.05, y - s * 0.05), (x - s * 0.35, y - s * 0.38), (x + s * 0.12, y - s * 0.08)])
    pygame.draw.polygon(surface, white, [(x - s * 0.28, y), (x - s * 0.48, y - s * 0.1), (x - s * 0.46, y + s * 0.1)])
    pygame.draw.polygon(surface, (170, 130, 60), [(x + s * 0.35, y - s * 0.12), (x + s * 0.44, y - s * 0.08), (x + s * 0.35, y - s * 0.05)])


ANIMALS = (sheep, elephant, giraffe, dove)


def animal(surface, x, y, s, variant=0):
    ANIMALS[variant % len(ANIMALS)](surface, x, y, s)


# ----------------------------------------------------------------------------- goals

def ark(surface, x, y, s, dim=1.0):
    wood, dark, roof = _shade((140, 100, 55), dim), _shade((95, 65, 35), dim), _shade((115, 80, 45), dim)
    pygame.draw.polygon(surface, wood, [(x - s * 0.5, y), (x + s * 0.5, y), (x + s * 0.36, y + s * 0.28),
                                         (x - s * 0.36, y + s * 0.28)])
    for k in (0.09, 0.18):
        pygame.draw.line(surface, dark, (x - s * 0.45, y + s * k), (x + s * 0.45, y + s * k), max(1, s // 30))
    pygame.draw.rect(surface, roof, (x - s * 0.26, y - s * 0.2, s * 0.52, s * 0.2))
    pygame.draw.polygon(surface, dark, [(x - s * 0.32, y - s * 0.2), (x, y - s * 0.38), (x + s * 0.32, y - s * 0.2)])
    pygame.draw.rect(surface, dark, (x - s * 0.05, y - s * 0.14, s * 0.1, s * 0.14))  # door


def tent(surface, x, y, s, dim=1.0):
    cloth, dark = _shade((170, 150, 115), dim), _shade((95, 80, 60), dim)
    pygame.draw.polygon(surface, cloth, [(x - s * 0.45, y + s * 0.3), (x, y - s * 0.35), (x + s * 0.45, y + s * 0.3)])
    pygame.draw.polygon(surface, dark, [(x - s * 0.1, y + s * 0.3), (x, y - s * 0.05), (x + s * 0.1, y + s * 0.3)])
    pygame.draw.line(surface, dark, (x, y - s * 0.35), (x, y - s * 0.48), max(2, s // 20))


def city(surface, x, y, s, dim=1.0):
    stone, dark = _shade((165, 145, 110), dim), _shade((95, 82, 62), dim)
    pygame.draw.rect(surface, stone, (x - s * 0.45, y - s * 0.12, s * 0.9, s * 0.4))
    for dx in (-0.45, 0.25):
        pygame.draw.rect(surface, stone, (x + s * dx, y - s * 0.32, s * 0.2, s * 0.6))
    for dx in (-0.45, -0.35, 0.25, 0.35):
        pygame.draw.rect(surface, stone, (x + s * dx, y - s * 0.4, s * 0.07, s * 0.08))
    pygame.draw.rect(surface, dark, (x - s * 0.09, y + s * 0.04, s * 0.18, s * 0.24), border_top_left_radius=int(s * 0.09),
                     border_top_right_radius=int(s * 0.09))


GOALS = {"ark": ark, "tent": tent, "city": city}


# ----------------------------------------------------------------------------- scenery (drawn dim, once per maze)

def reeds(surface, x, y, s, rng):
    for i in range(5):
        bx = x + (i - 2) * s * 0.12
        top = y - s * (0.3 + 0.15 * rng.random())
        lean = (rng.random() - 0.5) * s * 0.15
        pygame.draw.line(surface, (60, 90, 50), (bx, y + s * 0.3), (bx + lean, top), max(2, s // 18))
        if i % 2 == 0:
            pygame.draw.ellipse(surface, (95, 70, 45), (bx + lean - s * 0.03, top - s * 0.02, s * 0.06, s * 0.16))


def waves(surface, x, y, s, rng):
    for row in range(2):
        yy = y + row * s * 0.18
        pts = [(x - s * 0.4 + i * s * 0.1, yy + math.sin(i * 1.6 + row) * s * 0.05) for i in range(9)]
        pygame.draw.lines(surface, (55, 85, 120), False, pts, max(2, s // 16))


def sleeping_lion(surface, x, y, s, rng):
    body, mane, dark = (150, 115, 60), (115, 80, 40), (70, 50, 30)
    pygame.draw.ellipse(surface, body, (x - s * 0.35, y - s * 0.05, s * 0.6, s * 0.25))
    pygame.draw.circle(surface, mane, (int(x + s * 0.28), int(y + s * 0.02)), int(s * 0.16))
    pygame.draw.circle(surface, body, (int(x + s * 0.3), int(y + s * 0.05)), int(s * 0.1))
    for dx in (0.25, 0.34):  # closed eyes
        pygame.draw.line(surface, dark, (x + s * dx, y + s * 0.03), (x + s * (dx + 0.04), y + s * 0.03), max(1, s // 40))
    pygame.draw.line(surface, body, (x - s * 0.35, y + s * 0.1), (x - s * 0.48, y + s * 0.02), max(2, s // 20))


def grazing_sheep(surface, x, y, s, rng):
    sheep(surface, x, y, int(s * 0.8))


def palm(surface, x, y, s, rng):
    trunk, leaf = (110, 80, 50), (55, 95, 55)
    pygame.draw.line(surface, trunk, (x, y + s * 0.35), (x + s * 0.05, y - s * 0.25), max(3, s // 12))
    for a in (-2.6, -2.0, -1.2, -0.6, -1.6):
        ex, ey = x + s * 0.05 + math.cos(a) * s * 0.3, y - s * 0.25 + math.sin(a) * s * 0.12 + s * 0.1
        pygame.draw.line(surface, leaf, (x + s * 0.05, y - s * 0.25), (ex, ey), max(2, s // 14))


SCENERY = {"reeds": reeds, "waves": waves, "lions": sleeping_lion, "sheep": grazing_sheep, "palms": palm}


def scenery(surface, kind, spots, size, seed=0):
    """Draw a few pieces of scenery of one kind at the given centres."""
    draw = SCENERY.get(kind)
    if draw is None:
        return
    rng = random.Random(seed)
    for x, y in spots:
        draw(surface, x, y, size, rng)


# ----------------------------------------------------------------------------- icons for the map

def book(surface, x, y, s):
    """An open book (the scripture passage)."""
    page, edge = (170, 160, 135), (110, 90, 60)
    for side in (-1, 1):
        pts = [(x, y - s * 0.22), (x + side * s * 0.4, y - s * 0.3), (x + side * s * 0.4, y + s * 0.22), (x, y + s * 0.3)]
        pygame.draw.polygon(surface, page, pts)
        pygame.draw.polygon(surface, edge, pts, max(1, s // 30))
        for k in (-0.12, 0.0, 0.12):
            pygame.draw.line(surface, edge, (x + side * s * 0.08, y + s * (k - 0.06)), (x + side * s * 0.32, y + s * (k - 0.1)),
                             max(1, s // 40))


def maze_icon(surface, x, y, s, color=(150, 120, 62)):
    """A few maze walls."""
    t = max(2, s // 16)
    h = s * 0.4
    for a, b in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -0.3)),
                 ((-0.5, -0.5), (0.5, -0.5)), ((0.5, -0.5), (0.5, 0.5)), ((-0.5, 0), (-0.5, 0.5)), ((-0.5, 0.5), (0.2, 0.5))):
        pygame.draw.line(surface, color, (x + a[0] * h, y + a[1] * h), (x + b[0] * h, y + b[1] * h), t)
