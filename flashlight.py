"""Find the flashlight spot on the projected maze. OpenCV and NumPy only (no pygame).

The camera sees the projection. Four calibration points (the projection's corners in the
camera image, top-left, top-right, bottom-right, bottom-left) map each camera frame onto the
game's own coordinates. A slowly updated background of the warped frames holds whatever the
projector shows; the flashlight spot is a patch much brighter than that background and bright
in absolute terms. The game keeps its picture dim (dark sky, muted walls, dimmed portraits) so
that only the flashlight is that bright.
"""
import os
import threading
import time

import cv2
import numpy as np
import yaml

WORK = (480, 270)          # detection resolution (game is 1920 x 1080)
DIFF = 45                  # brighter than the background by at least this much (0-255)
MIN_LEVEL = 170            # and at least this bright in absolute terms
MIN_AREA = 12              # spot area in WORK pixels (about 4 x 3)
MAX_AREA = 9000            # a whole-screen change is not a spot (e.g. lights turned on)
BG_RATE = 0.06             # background learning rate away from the spot
SETTLE = 0.6               # seconds after a reset before spots are reported
SMOOTH = 0.5               # spot position smoothing (0 = none)


def order_corners(pts):
    """Sort four points into top-left, top-right, bottom-right, bottom-left."""
    pts = np.asarray(pts, np.float32).reshape(4, 2)
    s, d = pts.sum(1), pts[:, 1] - pts[:, 0]
    return np.array([pts[np.argmin(s)], pts[np.argmin(d)], pts[np.argmax(s)], pts[np.argmax(d)]], np.float32)


def load_calibration(path):
    """Projection corners in the camera image from a YAML file with `projector_points`
    (the same format as sgbaird/balloon-pop-game), or None."""
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    pts = data.get("projector_points")
    return order_corners(pts) if pts is not None and len(pts) == 4 else None


def save_calibration(path, pts, frame_shape=None):
    data = {"projector_points": [[round(float(x), 1), round(float(y), 1)] for x, y in order_corners(pts)]}
    if frame_shape is not None:
        data["camera_size"] = [int(frame_shape[1]), int(frame_shape[0])]
    with open(path, "w") as f:
        yaml.safe_dump(data, f)


def find_projection(black, white, min_fraction=0.03):
    """Corners of the projected area from a camera frame of an all-black and an all-white screen."""
    to_gray = lambda im: cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) if im.ndim == 3 else im
    diff = cv2.GaussianBlur(cv2.subtract(to_gray(white), to_gray(black)), (5, 5), 0)
    _, mask = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    c = max(contours, key=cv2.contourArea)
    if cv2.contourArea(c) < min_fraction * mask.size:
        return None
    hull = cv2.convexHull(c)
    peri = cv2.arcLength(hull, True)
    for eps in (0.02, 0.03, 0.05, 0.08):
        approx = cv2.approxPolyDP(hull, eps * peri, True)
        if len(approx) == 4:
            return order_corners(approx)
    return order_corners(cv2.boxPoints(cv2.minAreaRect(hull)))


class SpotDetector:
    def __init__(self, corners, game_size=(1920, 1080), work=WORK):
        self.game_size, self.work = game_size, work
        dst = np.array([[0, 0], [work[0], 0], [work[0], work[1]], [0, work[1]]], np.float32)
        self.H = cv2.getPerspectiveTransform(order_corners(corners), dst)
        self.reset()

    def reset(self):
        """Forget the background (call when the projected picture changes a lot)."""
        self.bg = None
        self.since = None   # time of the first frame after a reset
        self.pos = None

    def process(self, frame, now=None):
        """Spot centre in game coordinates for one camera frame, or None."""
        now = time.time() if now is None else now
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
        warped = cv2.warpPerspective(gray, self.H, self.work)
        warped = cv2.GaussianBlur(warped, (5, 5), 0).astype(np.float32)
        if self.bg is None:
            self.bg = warped.copy()
            self.since = now
            return None
        diff = warped - self.bg
        mask = ((diff > DIFF) & (warped > MIN_LEVEL)).astype(np.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, labels, stats, cents = cv2.connectedComponentsWithStats(mask)
        best, best_score = None, 0.0
        for i in range(1, n):
            area = stats[i, cv2.CC_STAT_AREA]
            if MIN_AREA <= area <= MAX_AREA:
                score = float(diff[labels == i].sum())
                if score > best_score:
                    best, best_score = i, score
        # learn the background everywhere except around the spot
        learn = np.ones(self.work[::-1], np.uint8)
        if best is not None:
            spot = (labels == best).astype(np.uint8)
            learn[cv2.dilate(spot, np.ones((15, 15), np.uint8)) > 0] = 0
        cv2.accumulateWeighted(warped, self.bg, BG_RATE, mask=learn)
        if best is None or now - self.since < SETTLE:
            self.pos = None
            return None
        sx = self.game_size[0] / self.work[0]
        sy = self.game_size[1] / self.work[1]
        x, y = cents[best][0] * sx, cents[best][1] * sy
        if self.pos is not None:
            x = SMOOTH * self.pos[0] + (1 - SMOOTH) * x
            y = SMOOTH * self.pos[1] + (1 - SMOOTH) * y
        self.pos = (x, y)
        return self.pos


def open_camera(index):
    backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
    cap = cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        return None
    for _ in range(5):
        ok, frame = cap.read()
        if ok and frame is not None:
            return cap
        time.sleep(0.1)
    cap.release()
    return None


class Camera(threading.Thread):
    """Reads frames in the background; runs the spot detector when there is one."""

    def __init__(self, cap):
        super().__init__(daemon=True)
        self.cap = cap
        self.detector = None
        self.frame = None
        self.spot = None          # (x, y, time) in game coordinates
        self.show_debug = False
        self.lock = threading.Lock()
        self.running = True

    def run(self):
        while self.running:
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.05)
                continue
            now = time.time()
            with self.lock:
                self.frame = frame
                det = self.detector
            if det is not None:
                pos = det.process(frame, now)
                if pos is not None:
                    self.spot = (pos[0], pos[1], now)
            if self.show_debug:
                view = frame.copy()
                if det is not None:
                    pts = np.linalg.inv(det.H)
                    corners = cv2.perspectiveTransform(
                        np.array([[[0, 0]], [[det.work[0], 0]], [[det.work[0], det.work[1]]], [[0, det.work[1]]]],
                                 np.float32), pts)
                    cv2.polylines(view, [corners.astype(np.int32)], True, (0, 200, 255), 2)
                    if self.spot and now - self.spot[2] < 0.3:
                        p = cv2.perspectiveTransform(np.array([[[self.spot[0] * det.work[0] / det.game_size[0],
                                                                  self.spot[1] * det.work[1] / det.game_size[1]]]],
                                                              np.float32), pts)[0][0]
                        cv2.circle(view, (int(p[0]), int(p[1])), 14, (0, 255, 0), 2)
                cv2.imshow("camera (D to hide)", view)
                cv2.waitKey(1)
                self._window = True
            elif getattr(self, "_window", False):
                cv2.destroyWindow("camera (D to hide)")
                cv2.waitKey(1)
                self._window = False

    def latest_frame(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def recent_spot(self, max_age=0.3):
        s = self.spot
        return (s[0], s[1]) if s and time.time() - s[2] <= max_age else None

    def stop(self):
        self.running = False
        self.join(timeout=1.0)
        self.cap.release()
        cv2.destroyAllWindows()
