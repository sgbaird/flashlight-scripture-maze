import cv2
import numpy as np

import flashlight
from flashlight import SpotDetector, find_projection, order_corners

CORNERS = np.array([[100, 120], [540, 110], [560, 400], [90, 380]], np.float32)  # camera pixels


def camera_view(screen_img):
    """What the camera would see of a 1920x1080 picture projected into CORNERS."""
    src = np.array([[0, 0], [1920, 0], [1920, 1080], [0, 1080]], np.float32)
    M = cv2.getPerspectiveTransform(src, CORNERS)
    frame = np.full((480, 640), 15, np.uint8)
    warped = cv2.warpPerspective(screen_img, M, (640, 480))
    mask = cv2.warpPerspective(np.ones_like(screen_img), M, (640, 480)) > 0
    frame[mask] = warped[mask]
    return frame


def scene(spot=None, token=None):
    img = np.full((1080, 1920), 30, np.uint8)               # dark maze background
    cv2.rectangle(img, (200, 200), (1700, 900), 90, 12)     # muted walls
    if token is not None:
        cv2.circle(img, token, 70, 120, -1)                  # dimmed walker portrait
    if spot is not None:
        cv2.circle(img, spot, 60, 255, -1)                   # flashlight
    return camera_view(img)


def test_order_corners():
    shuffled = CORNERS[[2, 0, 3, 1]]
    assert np.allclose(order_corners(shuffled), CORNERS)


def test_find_projection():
    black = np.full((480, 640), 15, np.uint8)
    white = camera_view(np.full((1080, 1920), 255, np.uint8))
    found = find_projection(black, white)
    assert found is not None
    assert np.abs(found - CORNERS).max() < 6


def test_find_markers_ignores_light_spilled_on_the_ceiling():
    # as on 2026-11-08: the projector's black is grey, and lighting the screen brightens the ceiling
    black = camera_view(np.full((1080, 1920), 90, np.uint8))
    squares = np.full((1080, 1920), 90, np.uint8)
    side = int(1080 * flashlight.MARKER_SIZE)
    for x, y in flashlight.marker_centres((1920, 1080)):
        cv2.rectangle(squares, (int(x) - side // 2, int(y) - side // 2), (int(x) + side // 2, int(y) + side // 2), 255, -1)
    white = camera_view(squares)
    white[:90] = cv2.add(white[:90], 12)                       # a little spill on the ceiling
    found = flashlight.find_markers(black, white, (1920, 1080))
    assert found is not None
    assert np.abs(found - CORNERS).max() < 6


def test_find_markers_ignores_reflections_of_the_squares():
    # as on 2026-11-08: a glossy ceiling and floor reflect each square as a bigger, taller smear
    black = camera_view(np.full((1080, 1920), 90, np.uint8))
    squares = np.full((1080, 1920), 90, np.uint8)
    side = int(1080 * flashlight.MARKER_SIZE)
    for x, y in flashlight.marker_centres((1920, 1080)):
        cv2.rectangle(squares, (int(x) - side // 2, int(y) - side // 2), (int(x) + side // 2, int(y) + side // 2), 255, -1)
    white = camera_view(squares)
    for x in (160, 470):                                        # smears above the picture, taller than the squares
        cv2.ellipse(white, (x, 60), (11, 24), 0, 0, 360, 230, -1)
    found = flashlight.find_markers(black, white, (1920, 1080))
    assert found is not None
    assert np.abs(found - CORNERS).max() < 6


def test_find_markers_fails_when_the_projector_shows_nothing():
    black = np.full((480, 640), 75, np.uint8)
    assert flashlight.find_markers(black, black.copy(), (1920, 1080)) is None


def test_spot_found_in_screen_coordinates():
    det = SpotDetector(CORNERS, (1920, 1080))
    t = 100.0
    for _ in range(10):
        det.process(scene(), t)
        t += 0.1
    pos = det.process(scene(spot=(1300, 400)), t + 1)
    assert pos is not None
    assert abs(pos[0] - 1300) < 40 and abs(pos[1] - 400) < 40


def test_moving_dim_walker_is_not_a_spot():
    det = SpotDetector(CORNERS, (1920, 1080))
    t = 100.0
    for i in range(30):
        assert det.process(scene(token=(400 + 20 * i, 500)), t) is None
        t += 0.1


def test_settle_after_reset():
    det = SpotDetector(CORNERS, (1920, 1080))
    det.process(scene(), 0.0)
    assert det.process(scene(spot=(900, 500)), flashlight.SETTLE / 2) is None


def test_picture_seen_late_after_reset_is_not_a_spot():
    """The camera shows the old picture for a moment after the screen changes; the new one is background."""
    det = SpotDetector(CORNERS, (1920, 1080))
    det.process(scene(), 0.0)                       # first frame after reset: still the old picture
    bright = scene(spot=(600, 400))                 # the new picture has a bright patch (e.g. a sunbeam)
    t = 0.2
    while t < 3.0:
        assert det.process(bright, t) is None
        t += 0.1


def test_still_bright_patch_fades_into_background():
    det = SpotDetector(CORNERS, (1920, 1080))
    t = 0.0
    for _ in range(12):
        det.process(scene(), t)
        t += 0.1
    seen = [det.process(scene(spot=(1300, 400)), t + 0.033 * i) for i in range(1500)]
    assert seen[0] is not None and seen[-1] is None
