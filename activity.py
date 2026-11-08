"""Flashlight Scripture Mazes: guide a scripture story figure through a projected maze with a flashlight.

    python activity.py                     # camera 0, projector = last display
    python activity.py --camera 1          # pick the camera
    python activity.py --mouse             # no camera: the mouse is the flashlight
    python activity.py --story baby-moses  # start with one story

Keys: N / P next / previous story, R new maze, M music on / off, S scripture, T story pages, O map,
B blank screen, C recalibrate, D camera view, arrow keys move the walker (or turn the story pages),
F11 fullscreen, Esc quit.
"""
import argparse
import io
import json
import math
import os
import random
import struct
import sys
import time
import wave

import pygame

import art
import pictures
from maze import Maze, SIZES
from stories import STORIES

W, H = 1920, 1080
FPS = 60
HERE = os.path.dirname(os.path.abspath(__file__))

SKY = (8, 12, 30)
STAR = (38, 44, 82)
CORRIDOR = (20, 28, 58)
WALL = (150, 120, 62)
TEXT = (205, 195, 165)
SOFT = (150, 145, 130)
GOLD = (190, 155, 80)

LEAD = 2.4        # the walker follows a light within this many cells of it...
MAX_STEPS = 4     # ...if it can get there in this many steps
SPEED = 3.2       # cells per second
DWELL = 1.6       # seconds of light on a button to press it
ARM = 0.5         # a new button counts the light only after it has been off the button this long
MUSIC_VOLUME = 0.3  # the songs' instrumental accompaniments (art/music, from fetch_art.py), kept soft
VERSE = ("“Thy word is a lamp unto my feet, and a light unto my path.”", "Psalm 119:105")


# ----------------------------------------------------------------------------- sounds

def _tones(notes, volume=0.25, rate=44100):
    """WAV bytes of soft bell notes: list of (frequency, start, length) in seconds."""
    total = max(s + l for _, s, l in notes)
    buf = [0.0] * int(rate * total)
    for f, start, length in notes:
        i0, n = int(start * rate), int(length * rate)
        for i in range(n):
            t = i / rate
            env = math.exp(-4.0 * t / length) * min(1.0, i / (0.005 * rate))
            buf[i0 + i] += env * (math.sin(2 * math.pi * f * t) + 0.3 * math.sin(4 * math.pi * f * t))
    peak = max(1e-6, max(abs(x) for x in buf))
    data = struct.pack("<%dh" % len(buf), *(int(32767 * volume * x / peak) for x in buf))
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(data)
    out.seek(0)
    return out


def make_sounds():
    try:
        return {
            "collect": pygame.mixer.Sound(file=_tones([(784, 0, 0.35), (1175, 0.09, 0.5)])),
            "goal": pygame.mixer.Sound(file=_tones([(523, 0, 0.6), (659, 0.15, 0.6), (784, 0.3, 0.6),
                                                    (1047, 0.45, 1.2)])),
            "press": pygame.mixer.Sound(file=_tones([(660, 0, 0.3)], 0.18)),
            "locked": pygame.mixer.Sound(file=_tones([(330, 0, 0.4)], 0.15)),
        }
    except pygame.error:
        return {}


# ----------------------------------------------------------------------------- drawing helpers

def wrap(font, text, width):
    lines, line = [], ""
    for word in text.split():
        trial = (line + " " + word).strip()
        if font.size(trial)[0] <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_text(surface, font, text, pos, color=TEXT, width=None, anchor="topleft", spacing=1.15):
    lines = wrap(font, text, width) if width else [text]
    x, y = pos
    for ln in lines:
        img = font.render(ln, True, color)
        r = img.get_rect(**{anchor: (x, y)})
        surface.blit(img, r)
        y += int(font.get_linesize() * spacing)
    return y


def draw_icon(surface, kind, center, size, variant=0):
    x, y = center
    s = size
    if kind == "animal":
        pictures.animal(surface, x, y, s, variant)
    elif kind == "rope":
        for k in range(3):
            pygame.draw.circle(surface, (150, 110, 60), (x, y), int(s * (0.45 - 0.12 * k)), max(2, s // 12))
    elif kind == "stone":
        pygame.draw.ellipse(surface, (120, 120, 125), (x - s * 0.45, y - s * 0.3, s * 0.9, s * 0.6))
        pygame.draw.ellipse(surface, (155, 155, 160), (x - s * 0.25, y - s * 0.22, s * 0.35, s * 0.18))
    elif kind == "vegetable":
        pygame.draw.polygon(surface, (200, 110, 40), [(x - s * 0.15, y - s * 0.2), (x + s * 0.15, y - s * 0.2),
                                                       (x, y + s * 0.45)])
        for dx in (-0.12, 0, 0.12):
            pygame.draw.ellipse(surface, (70, 140, 60), (x + s * dx - s * 0.06, y - s * 0.48, s * 0.12, s * 0.3))
    elif kind == "grain":
        pygame.draw.line(surface, (160, 130, 60), (x, y + s * 0.45), (x, y - s * 0.4), max(2, s // 14))
        for k in range(4):
            for side in (-1, 1):
                pygame.draw.ellipse(surface, (190, 150, 70),
                                    (x + side * s * 0.12 - s * 0.08, y - s * 0.38 + k * s * 0.17, s * 0.16, s * 0.12))
    else:  # heart
        r = s * 0.22
        pygame.draw.circle(surface, (190, 80, 110), (int(x - r), int(y - r * 0.4)), int(r))
        pygame.draw.circle(surface, (190, 80, 110), (int(x + r), int(y - r * 0.4)), int(r))
        pygame.draw.polygon(surface, (190, 80, 110), [(x - 2 * r, y - r * 0.2), (x + 2 * r, y - r * 0.2),
                                                       (x, y + s * 0.42)])


def bring_to_front():
    """Put the activity's window in front on Windows. Started from a terminal or another program, it can
    open behind other windows; with one display mirrored to the projector, the wall then shows those."""
    if os.name != "nt":
        return
    try:
        import ctypes
        hwnd = pygame.display.get_wm_info().get("window")
        user32 = ctypes.windll.user32
        user32.keybd_event(0x12, 0, 0, 0)   # tapping Alt lets this process take the foreground
        user32.keybd_event(0x12, 0, 2, 0)
        user32.ShowWindow(hwnd, 9)          # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
    except Exception:
        pass


class DwellButton:
    """A circle pressed by holding the flashlight (or the mouse) on it. With `image`, the picture fills the
    circle and the label goes under it; with `width`, it is a rounded bar that wide (a scripture reference)."""

    def __init__(self, center, radius, label, image=None, width=None, highlight=False):
        self.center, self.radius, self.label = (int(center[0]), int(center[1])), radius, label
        self.image, self.width, self.highlight = image, width, highlight
        self.progress = 0.0
        self.off_for = 0.0   # so a light left where the last screen's button was does not press this one

    def contains(self, light):
        if light is None:
            return False
        dx, dy = light[0] - self.center[0], light[1] - self.center[1]
        if self.width:
            return abs(dx) <= self.width / 2 and abs(dy) <= self.radius
        return math.hypot(dx, dy) <= self.radius

    def update(self, light, dt):
        inside = self.contains(light)
        if self.off_for < ARM:
            self.off_for = 0.0 if inside else self.off_for + dt
            return False
        # fills while the light stays on it and drains quickly, so a light passing over it does not add up
        self.progress = min(1.0, self.progress + dt / DWELL) if inside else max(0.0, self.progress - 3 * dt)
        if self.progress >= 1.0:
            self.progress = 0.0
            return True
        return False

    def draw(self, surface, font, now):
        x, y = self.center
        pulse = 4 * math.sin(now * 2.5)
        dim = (130, 112, 70)   # progress drawn dim, so it is not taken for the flashlight
        if self.width:
            rect = pygame.Rect(0, 0, int(self.width + 2 * pulse), 2 * self.radius)
            rect.center = (x, y)
            pygame.draw.rect(surface, (30, 38, 75), rect, border_radius=self.radius)
            pygame.draw.rect(surface, GOLD, rect, 3, border_radius=self.radius)
            if self.progress > 0:
                pygame.draw.line(surface, dim, (rect.left + 10, rect.bottom + 8),
                                 (rect.left + 10 + (rect.width - 20) * self.progress, rect.bottom + 8), 6)
            img = font.render(self.label, True, TEXT)
            surface.blit(img, img.get_rect(center=(x, y)))
            return
        r = self.radius + pulse
        if self.highlight:
            pygame.draw.circle(surface, (55, 50, 38), (x, y), int(r + 14))
        pygame.draw.circle(surface, (30, 38, 75), (x, y), int(r))
        if self.image is not None:
            surface.blit(self.image, self.image.get_rect(center=(x, y)))
        pygame.draw.circle(surface, GOLD, (x, y), int(r), 4)
        if self.progress > 0:
            rect = pygame.Rect(0, 0, 2 * r + 24, 2 * r + 24)
            rect.center = (x, y)
            pygame.draw.arc(surface, dim, rect, math.pi / 2, math.pi / 2 + 2 * math.pi * self.progress, 6)
        img = font.render(self.label, True, TEXT)
        if self.image is not None:
            surface.blit(img, img.get_rect(midtop=(x, y + self.radius + 14)))
        else:
            surface.blit(img, img.get_rect(center=(x, y)))


class Recorder:
    """--record DIR: the projected picture, the camera image and a log, to check a session afterwards.

    Everything stays in DIR on this computer. The camera video shows the room (and people in it).
    """

    def __init__(self, folder, fps=10):
        import queue
        import threading
        import cv2
        self.cv2, self.folder, self.dt = cv2, folder, 1.0 / fps
        os.makedirs(folder, exist_ok=True)
        self.log = open(os.path.join(folder, "log.jsonl"), "a", encoding="utf-8")
        self.screen_video = self.camera_video = None
        self.next, self.n, self.cam_n = 0.0, 0, 0
        self.fps = fps
        # videos are encoded on a background thread, so recording never makes the picture stutter
        self.queue, self.full = queue.Queue(maxsize=40), queue.Full
        self.thread = threading.Thread(target=self._work, daemon=True)
        self.thread.start()

    def _put(self, item):
        try:
            self.queue.put_nowait(item)
        except self.full:  # the disk cannot keep up: drop this one rather than slow the activity
            pass

    def _work(self):
        while True:
            item = self.queue.get()
            if item is None:
                return
            if item[0] == "log":
                self.log.write(json.dumps(item[1]) + "\n")
                continue
            _, now, screen, camera_frame, info = item
            if self.screen_video is None:
                self.screen_video = self._writer("screen.avi", screen)
            self.screen_video.write(screen)
            if camera_frame is not None:
                if self.camera_video is None:
                    self.camera_video = self._writer("camera.avi", camera_frame)
                self.camera_video.write(camera_frame)
                self.cam_n += 1
            cam = self.cam_n - 1 if camera_frame is not None else None
            self.log.write(json.dumps({"t": round(now, 3), "frame": self.n, "cam_frame": cam, **info}) + "\n")
            self.n += 1

    def _writer(self, name, frame):
        h, w = frame.shape[:2]
        return self.cv2.VideoWriter(os.path.join(self.folder, name), self.cv2.VideoWriter_fourcc(*"MJPG"),
                                    self.fps, (w, h))

    def event(self, kind, **info):
        self._put(("log", {"t": round(time.time(), 3), "event": kind, **info}))

    def tick(self, now, canvas, camera_frame, info):
        if now < self.next:
            return
        self.next = now + self.dt
        small = pygame.transform.smoothscale(canvas, (640, 360))
        screen = pygame.surfarray.array3d(small).swapaxes(0, 1)[:, :, ::-1].copy()
        self._put(("frame", now, screen, camera_frame, info))

    def close(self):
        self.queue.put(None)
        self.thread.join(timeout=10)
        for v in (self.screen_video, self.camera_video):
            if v is not None:
                v.release()
        self.log.close()


# ----------------------------------------------------------------------------- the activity

class Activity:
    def __init__(self, args):
        self.args = args
        pygame.init()
        self.window = self._open_window(not args.window)
        pygame.display.set_caption("Flashlight Scripture Mazes")
        self.canvas = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        try:
            pygame.mixer.init()
            self.sounds = make_sounds()
        except pygame.error:
            self.sounds = {}
        self.fonts = {k: pygame.font.SysFont("georgia,timesnewroman,serif", v) for k, v in
                      (("huge", 84), ("big", 58), ("mid", 40), ("small", 30), ("read", 29), ("tiny", 22))}
        self.reading = False
        self.pairs = []      # (button, action) on the current screen
        self.panel = 0       # the story page shown (state "panels")
        self.came_from = None  # the screen the map was opened from, to go back to
        self.maze = None
        self.maze_story = None
        self.blank = False   # B: a black screen, to stop and read from a book
        self.stars = [(random.randrange(W), random.randrange(H), random.choice((1, 1, 2))) for _ in range(140)]
        self.story_index = 0
        if args.story:
            slugs = [s.slug for s in STORIES]
            if args.story in slugs:
                self.story_index = slugs.index(args.story)
        self.camera = None
        self.calibration_path = args.calibration
        self.mouse_seen = -10.0
        self.message, self.message_until = "", 0.0
        self.show_title()
        self.rec = Recorder(args.record) if args.record else None
        self._start_camera()
        self.music_on, self.music_playing = not args.no_music, None
        self.update_music()

    # --- setup
    def _open_window(self, fullscreen):
        sizes = pygame.display.get_desktop_sizes()
        display = self.args.display if self.args.display is not None else len(sizes) - 1
        display = max(0, min(display, len(sizes) - 1))
        self.display = display
        if fullscreen:
            window = pygame.display.set_mode(sizes[display], pygame.FULLSCREEN, display=display)
            bring_to_front()
            return window
        return pygame.display.set_mode((W // 2, H // 2), pygame.RESIZABLE, display=display)

    def _start_camera(self):
        if self.args.mouse:
            return
        import flashlight
        cap = flashlight.open_camera(self.args.camera)
        if cap is None:
            self.say("No camera %d found: the mouse is the flashlight." % self.args.camera, 8)
            return
        self.camera = flashlight.Camera(cap)
        self.camera.start()
        corners = flashlight.load_calibration(self.calibration_path)
        if corners is None:
            self.begin_calibration(wait=4.0 if not self.args.window else 0.9)
        else:
            self.camera.detector = flashlight.SpotDetector(corners, (W, H))

    def say(self, text, seconds=4.0):
        self.message, self.message_until = text, time.time() + seconds
        if getattr(self, "rec", None):
            self.rec.event("say", text=text)

    def snapshot(self):
        """What the activity knows at this moment, for the --record log."""
        now = time.time()
        r = lambda p: None if p is None else [round(p[0]), round(p[1])]
        info = {"state": self.state, "story": self.story.slug, "light": r(self.light()),
                "mouse": now - self.mouse_seen < 2.0}
        if self.camera is not None:
            info["spot"] = r(self.camera.recent_spot())
            det = self.camera.detector
            info["det"] = det.stats if det is not None else None
            if not self.camera.is_alive() or self.camera.errors:
                info["camera"] = {"alive": self.camera.is_alive(), "errors": self.camera.errors}
        if self.state == "maze":
            info.update(cell=list(self.cur), pos=r(self.pos), route=[list(c) for c in self.route],
                        following=round(self.following, 2), collected=self.collected,
                        items=[list(c) for c in self.items], goal=list(self.maze.goal),
                        celebrating=self.celebrate is not None)
        elif self.state != "calibrate" and self.button is not None:
            info["button"] = [self.button.label, round(self.button.progress, 2)]
            busy = [[b.label, round(b.progress, 2)] for b, _ in self.buttons() if b.progress > 0]
            if busy:
                info["pressing"] = busy
        if self.state == "panels":
            info["panel"] = self.panel
        if self.reading:
            info["reading"] = self.read_title
        return info

    @property
    def story(self):
        return STORIES[self.story_index]

    def update_music(self):
        """Play the story's song (looping, soft) when music is on; fade out when it is off."""
        if not pygame.mixer.get_init():
            return
        title, slug = self.story.song
        if not self.music_on:
            pygame.mixer.music.fadeout(1500)
            self.music_playing = None
            return
        if self.music_playing == slug:
            return
        path = os.path.join(art.ART, "music", slug + ".mp3")
        if not os.path.exists(path):
            pygame.mixer.music.fadeout(1500)
            self.music_playing = None
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1, fade_ms=2500)
            self.music_playing = slug
        except pygame.error:
            self.music_playing = None

    def toggle_blank(self):
        """Black screen and paused (music too) until B is pressed again."""
        self.blank = not self.blank
        if pygame.mixer.get_init():
            (pygame.mixer.music.pause if self.blank else pygame.mixer.music.unpause)()
        if self.rec:
            self.rec.event("blank", on=self.blank)
        if not self.blank:
            self.last_light = time.time()
            for button, _ in self.buttons():
                button.off_for = 0.0   # the light has to leave the button before it counts again
            self.reset_detector()

    def toggle_music(self):
        self.music_on = not self.music_on
        self.update_music()
        if not self.music_on:
            self.say("Music off.", 2)
        elif self.music_playing:
            self.say("Music: “%s”" % self.story.song[0], 3)
        else:
            self.say("No music for this song yet: run fetch_art.py.", 5)

    def reset_detector(self):
        if self.camera and self.camera.detector:
            self.camera.detector.reset()

    # --- calibration: show black, then white, and find the bright quadrilateral
    def begin_calibration(self, wait=0.9, tries=3):
        """Show black, then white. `wait`: seconds before the first camera frame counts. Just after the
        activity goes full screen the projector shows nothing for a few seconds while it switches modes."""
        self.state = "calibrate"
        self.cal_phase, self.cal_t0, self.cal_frames = "black", time.time(), {"black": [], "white": []}
        self.cal_wait, self.cal_tries = wait, tries

    def update_calibration(self):
        import cv2
        import numpy as np
        import flashlight
        if not pygame.key.get_focused():
            # another window is in front, so the projector may be showing it: start over once we are back
            self.cal_phase, self.cal_t0, self.cal_frames = "black", time.time(), {"black": [], "white": []}
            self.cal_wait = max(self.cal_wait, 2.0)
            return
        t = time.time() - self.cal_t0
        wait = self.cal_wait if self.cal_phase == "black" else 0.9
        if self.cal_phase in ("black", "white") and t > wait:
            frame = self.camera.latest_frame()
            if frame is not None:
                self.cal_frames[self.cal_phase].append(frame.astype(np.float32))
            if t > wait + 0.6:
                if self.cal_phase == "black":
                    self.cal_phase, self.cal_t0 = "white", time.time()
                else:
                    black = np.mean(self.cal_frames["black"], 0).astype(np.uint8)
                    white = np.mean(self.cal_frames["white"], 0).astype(np.uint8)
                    corners = flashlight.find_markers(black, white, (W, H))
                    if corners is None and self.cal_tries > 1:  # try again, giving the projector more time
                        if self.rec:
                            self.rec.event("calibration_retry", tries_left=self.cal_tries - 1)
                        self.begin_calibration(wait=2.0, tries=self.cal_tries - 1)
                        return
                    if corners is None:
                        self.camera.detector = None
                        self.say("Calibration failed: make sure the camera sees the whole picture, then press C.", 10)
                    else:
                        flashlight.save_calibration(self.calibration_path, corners, black.shape)
                        self.camera.detector = flashlight.SpotDetector(corners, (W, H))
                        self.say("Calibrated. Press D to see the camera view.", 5)
                    self.show_title()

    # --- light source: flashlight, or the mouse when it moved recently
    def light(self):
        now = time.time()
        if self.camera is None or now - self.mouse_seen < 2.0:
            if pygame.mouse.get_focused():
                mx, my = pygame.mouse.get_pos()
                ww, wh = self.window.get_size()
                return (mx * W / ww, my * H / wh)
            return None
        return self.camera.recent_spot()

    # --- screens: each sets its buttons, (button, action) pairs
    def set_buttons(self, pairs):
        self.pairs = pairs
        self.button = pairs[0][0] if pairs else None
        self.reset_detector()

    def map_button(self):
        return (DwellButton((72, H - 66), 52, "Map"), self.open_map)

    def show_title(self):
        self.state, self.reading = "title", False
        self.set_buttons([(DwellButton((W // 2, int(H * 0.72)), 110, "Begin"), self.advance), self.map_button()])

    def show_card(self):
        self.state, self.reading = "card", False
        pairs = [(DwellButton((int(W * 0.835), int(H * 0.8)), 105, "Start"), self.advance)]
        if art.panels(self.story):
            pairs.append((DwellButton((int(W * 0.585), int(H * 0.8)), 75, "Story"), lambda: self.open_panels(0)))
        if art.scripture(self.story):
            pairs.append((DwellButton((int(W * 0.683), int(H * 0.8)), 75, "Read"), self.open_scripture))
        self.set_buttons(pairs + [self.map_button()])
        self.update_music()

    def show_done(self):
        self.state, self.reading = "done", False
        pairs = [(DwellButton((int(W * 0.835), int(H * 0.82)), 105, "Next"), self.advance)]
        if art.scripture(self.story):
            pairs.append((DwellButton((int(W * 0.683), int(H * 0.82)), 75, "Read"), self.open_scripture))
        self.set_buttons(pairs + [self.map_button()])

    # --- the story pages: the book's pictures and words, one panel at a time
    def open_panels(self, index):
        panels = art.panels(self.story)
        if not panels:
            self.say("No story pages yet: run fetch_art.py.", 5)
            return
        self.state, self.reading = "panels", False
        self.panel = max(0, min(index, len(panels) - 1))
        self.layout_panel()
        last = self.panel == len(panels) - 1
        pairs = [(DwellButton((int(W * 0.9), int(H * 0.87)), 85, "Maze" if last else "Next"),
                  self.start_maze if last else lambda: self.open_panels(self.panel + 1)),
                 (DwellButton((int(W * 0.765), int(H * 0.87)), 70, "Back"),
                  self.show_card if self.panel == 0 else lambda: self.open_panels(self.panel - 1))]
        for label, verses, center, width in self.panel_refs:
            pairs.append((DwellButton(center, 34, label, width=width),
                          lambda v=verses, t=label: self.open_scripture(v, t)))
        self.set_buttons(pairs + [self.map_button()])

    def layout_panel(self):
        """Where the picture, the words and the reference buttons go on this page."""
        panel = art.panels(self.story)[self.panel]
        n = panel.get("image")
        wide = n is not None and art.aspect(self.story, n) >= 1.9   # the book's wide strips go above the words
        if wide:
            self.panel_pic = art.picture(self.story, n, (W - 140, 470))
            pic_rect = self.panel_pic.get_rect(midtop=(W // 2, 95)) if self.panel_pic else pygame.Rect(70, 95, 0, 0)
            box = pygame.Rect(70, pic_rect.bottom + 30, W - 140, 0)
            refs_right = int(W * 0.765) - 70 - 30
        else:
            self.panel_pic = art.picture(self.story, n, (int(W * 0.48), int(H * 0.74))) if n else None
            pic_rect = self.panel_pic.get_rect(topleft=(70, 95)) if self.panel_pic else pygame.Rect(70, 95, 0, 0)
            box = pygame.Rect(pic_rect.right + 50, 110, W - pic_rect.right - 120, 0)
            refs_right = W - 70
        self.panel_pic_rect = pic_rect
        for font in (self.fonts["mid"], self.fonts["small"], self.fonts["read"]):   # the biggest words that fit
            lines = []
            for para in panel.get("text", []):
                lines += wrap(font, para, box.width) + [""]
            height = len(lines) * int(font.get_linesize() * 1.1)
            limit = H * 0.87 - 34 - 40 if wide else H * 0.62   # wide: the references go beside Back / Next
            if box.top + height < limit or font is self.fonts["read"]:
                break
        self.panel_font, self.panel_lines, self.panel_text_at = font, lines, box.topleft
        # the references as bars, in rows under the words (left of Back/Next when the picture is wide)
        refs, font = [], self.fonts["small"]
        x, y = (box.left if not wide else 200), box.top + height + 30
        if wide:
            y = max(y, int(H * 0.87) - 34)
        left = x
        for ref in panel.get("refs", []):
            if not ref.get("verses"):
                continue
            label = ref["label"].replace("-", "–")
            width = font.size(label)[0] + 44
            if x + width > refs_right and x > left:
                x, y = left, y + 84
            refs.append((label, ref["verses"], (x + width // 2, y + 34), width))
            x += width + 24
        self.panel_refs = refs

    # --- the map: every story, and this story's card, pages, scripture and maze
    def open_map(self):
        if self.state == "map":
            return self.close_map()
        self.came_from = (self.state, self.panel)
        self.state, self.reading = "map", False
        st, d = self.story, 92
        pairs = [(DwellButton((int(W * 0.92), int(H * 0.89)), 70, "Back"), self.close_map)]
        tiles = [("Card", art.thumb(st, st.card, d) or art.portrait(st, "player", d), self.show_card)]
        for i, panel in enumerate(art.panels(st)):
            img = art.thumb(st, panel["image"], d) if panel.get("image") else None
            tiles.append((str(i + 1), img, lambda i=i: self.open_panels(i)))
        if art.scripture(st):
            tiles.append(("Read", self.icon(pictures.book, d), self.read_from_map))
        tiles.append(("Maze", self.icon(pictures.maze_icon, d), self.maze_from_map))
        step = min(128, (W - 140) // len(tiles))
        x0 = W // 2 - step * (len(tiles) - 1) // 2
        here = {"card": "Card", "done": "Card", "maze": "Maze"}.get(self.came_from[0])
        if self.came_from[0] == "panels":
            here = str(self.came_from[1] + 1)
        for k, (label, img, action) in enumerate(tiles):
            pairs.append((DwellButton((x0 + k * step, 250), d // 2, label, image=img, highlight=label == here), action))
        per_row, d = 6, 120
        for k, other in enumerate(STORIES):
            row, col = divmod(k, per_row)
            count = min(per_row, len(STORIES) - row * per_row)
            x = W // 2 + (col - (count - 1) / 2) * 250
            y = 530 + row * 235
            pairs.append((DwellButton((x, y), d // 2, other.short, image=art.portrait(other, "player", d),
                                      highlight=other is st), lambda k=k: self.choose_story(k)))
        self.set_buttons(pairs)

    def icon(self, draw, d):
        surf = pygame.Surface((d, d), pygame.SRCALPHA)
        draw(surf, d // 2, d // 2, int(d * 0.8))
        return surf

    def close_map(self):
        state, panel = self.came_from or ("title", 0)
        if state == "maze" and self.maze is not None:
            self.state, self.reading = "maze", False
            self.set_buttons([self.maze_map_button()])
        elif state == "panels":
            self.open_panels(panel)
        elif state in ("card", "done"):
            (self.show_card if state == "card" else self.show_done)()
        else:
            self.show_title()

    def choose_story(self, k):
        self.story_index = k
        self.show_card()

    def read_from_map(self):
        self.show_card()
        self.open_scripture()

    def maze_from_map(self):
        if self.maze is not None and self.maze_story == self.story_index and self.celebrate is None:
            self.state, self.reading = "maze", False   # go back to the maze where it was
            self.set_buttons([self.maze_map_button()])
        else:
            self.start_maze()

    def maze_map_button(self):
        return (DwellButton((W - 62, 62), 44, "Map"), self.open_map)

    # --- the scripture passage, opened from the story card, the ending or a story page's reference
    def open_scripture(self, verses=None, title=None):
        verses = verses or art.scripture(self.story)
        if not verses:
            self.say("No scripture text yet: run fetch_art.py.", 5)
            return
        self.read_title = title or self.story.ref
        font, width = self.fonts["read"], (W - 260) // 2
        chapters = {v[0].split(":")[0] for v in verses}
        per_column = (H - 170 - 230) // font.get_linesize()
        columns = [[]]
        for label, text in verses:  # whole verses in each column, a blank line between them
            num = label if len(chapters) > 1 else label.split(":")[1]
            block = [(i == 0 and num, ln) for i, ln in enumerate(wrap(font, text, width - 70))]
            if columns[-1] and len(columns[-1]) + 1 + len(block) > per_column:
                columns.append([])
            columns[-1] += ([(False, "")] if columns[-1] else []) + block
        self.pages = [columns[i:i + 2] for i in range(0, len(columns), 2)]
        self.page = 0
        self.show_scripture_buttons()

    def show_scripture_buttons(self):
        self.reading = True
        pairs = [(DwellButton((int(W * 0.9), int(H * 0.88)), 80, "Back"), self.close_scripture)]
        if len(self.pages) > 1:
            pairs.append((DwellButton((int(W * 0.78), int(H * 0.88)), 80, "More"), self.more_scripture))
        self.set_buttons(pairs)

    def more_scripture(self):
        self.page = (self.page + 1) % len(self.pages)
        self.show_scripture_buttons()

    def close_scripture(self):
        """Back to the screen the passage was opened from."""
        self.reading = False
        if self.state == "panels":
            self.open_panels(self.panel)
        elif self.state == "done":
            self.show_done()
        else:
            self.show_card()

    def buttons(self):
        """(button, action) pairs on this screen."""
        return self.pairs

    def start_maze(self, seed=None):
        st = self.story
        cols, rows = SIZES.get(self.args.size or st.size, SIZES["medium"])
        self.maze = Maze(cols, rows, seed=seed)
        self.cell = min((W - 120) / cols, (H - 170) / rows)
        self.ox = (W - self.cell * cols) / 2
        self.oy = 130 + (H - 150 - self.cell * rows) / 2
        count = st.items[1] if st.items else 0
        self.items = self.maze.place_items(count)
        self.item_variants = {cell: i for i, cell in enumerate(self.items)}
        self.collected = 0
        self.cur = self.maze.start
        self.pos = list(self.center(self.cur))
        self.route = []
        self.following = 0.0
        self.last_light = time.time()
        self.celebrate = None
        self.maze_surface = self.render_maze()
        self.walker = art.portrait(st, "player", int(self.cell * 0.82))
        self.goal_img = art.portrait(st, "goal", int(self.cell * 0.82)) if st.goal else None
        self.state, self.reading = "maze", False
        self.maze_story = self.story_index
        self.set_buttons([self.maze_map_button()])

    def next_story(self, step=1):
        self.story_index = (self.story_index + step) % len(STORIES)
        self.show_card()

    def center(self, cell):
        return (self.ox + (cell[0] + 0.5) * self.cell, self.oy + (cell[1] + 0.5) * self.cell)

    def cell_at(self, x, y):
        c, r = int((x - self.ox) // self.cell), int((y - self.oy) // self.cell)
        return (c, r) if self.maze.inside((c, r)) else None

    def render_maze(self):
        s = pygame.Surface((W, H))
        self.draw_sky(s)
        m, k = self.maze, self.cell
        pygame.draw.rect(s, CORRIDOR, (self.ox, self.oy, k * m.cols, k * m.rows))
        t = max(6, int(k * 0.08))
        if self.story.scenery:  # a little scenery here and there, away from the start, goal and items
            taken = {m.start, m.goal, *self.items}
            free = [(c, r) for c in range(m.cols) for r in range(m.rows) if (c, r) not in taken]
            spots = m.rng.sample(free, min(5, len(free)))
            layer = pygame.Surface((W, H), pygame.SRCALPHA)
            pictures.scenery(layer, self.story.scenery, [self.center(c) for c in spots], int(k * 0.55), m.rng.random())
            layer.fill((255, 255, 255, 140), special_flags=pygame.BLEND_RGBA_MULT)  # faint: background, not things to gather
            s.blit(layer, (0, 0))

        def wall(a, b):  # a wall segment with rounded ends
            pygame.draw.line(s, WALL, a, b, t)
            for p in (a, b):
                pygame.draw.circle(s, WALL, (int(p[0]), int(p[1])), t // 2)

        for c in range(m.cols):
            for r in range(m.rows):
                x, y = self.ox + c * k, self.oy + r * k
                if r == 0 or not m.is_open((c, r), (c, r - 1)):
                    wall((x, y), (x + k, y))
                if c == 0 or not m.is_open((c, r), (c - 1, r)):
                    wall((x, y), (x, y + k))
                if r == m.rows - 1:
                    wall((x, y + k), (x + k, y + k))
                if c == m.cols - 1:
                    wall((x + k, y), (x + k, y + k))
        st = self.story
        draw_text(s, self.fonts["big"], st.title, (60, 30))
        draw_text(s, self.fonts["small"], st.task, (60, 95), SOFT)
        return s

    def draw_sky(self, s):
        s.fill(SKY)
        for x, y, r in self.stars:
            pygame.draw.circle(s, STAR, (x, y), r)

    # --- per-frame updates
    def update_maze(self, dt, now):
        light = self.light()
        for button, action in self.buttons():   # the map button in the corner
            if button.update(light, dt):
                self.play("press")
                action()
                return
        if self.celebrate is not None:
            if now - self.celebrate > 2.5:
                self.show_done()
            return
        if light is not None:
            self.last_light = now
            near = math.hypot(light[0] - self.pos[0], light[1] - self.pos[1]) <= LEAD * self.cell
            target = self.cell_at(*light)
            if near and target is not None and target != (self.route[-1] if self.route else self.cur):
                path = self.maze.path(self.cur, target, limit=MAX_STEPS)
                if path is not None:
                    self.route = path[1:]
            self.following = min(1.0, self.following + dt * 4) if near else max(0.0, self.following - dt * 2)
        else:
            self.following = max(0.0, self.following - dt * 2)
        self.walk(dt)

    def walk(self, dt):
        step = SPEED * self.cell * dt
        while self.route and step > 0:
            tx, ty = self.center(self.route[0])
            dx, dy = tx - self.pos[0], ty - self.pos[1]
            d = math.hypot(dx, dy)
            if d <= step:
                self.pos = [tx, ty]
                step -= d
                self.arrive(self.route.pop(0))
            else:
                self.pos[0] += dx / d * step
                self.pos[1] += dy / d * step
                step = 0

    def arrive(self, cell):
        self.cur = cell
        if cell in self.items:
            self.items.remove(cell)
            self.collected += 1
            self.play("collect")
            if self.rec:
                self.rec.event("collect", cell=list(cell), collected=self.collected)
        if cell == self.maze.goal:
            if self.items:
                self.play("locked")
                name = self.story.items[0]
                self.say("Gather %d more %s first!" % (len(self.items), name), 3)
            else:
                self.route = []
                self.celebrate = time.time()
                self.play("goal")
                if self.rec:
                    self.rec.event("goal", story=self.story.slug)

    def move_key(self, dc, dr):
        if self.state == "maze" and self.celebrate is None and not self.route:
            n = (self.cur[0] + dc, self.cur[1] + dr)
            if self.maze.inside(n) and self.maze.is_open(self.cur, n):
                self.route = [n]

    def play(self, name):
        snd = self.sounds.get(name)
        if snd:
            snd.play()

    # --- screens
    def draw_title(self, s, now):
        self.draw_sky(s)
        draw_text(s, self.fonts["huge"], "Flashlight Scripture Mazes", (W // 2, 170), TEXT, anchor="midtop")
        draw_text(s, self.fonts["mid"], VERSE[0], (W // 2, 330), SOFT, anchor="midtop")
        draw_text(s, self.fonts["small"], VERSE[1], (W // 2, 390), SOFT, anchor="midtop")
        cfm = self.story.cfm
        if cfm:
            draw_text(s, self.fonts["small"], cfm, (W // 2, 480), GOLD, anchor="midtop")
        draw_text(s, self.fonts["small"], "Shine your flashlight on the circle and hold it there.",
                  (W // 2, int(H * 0.88)), SOFT, anchor="midtop")
        self.draw_buttons(s, now)

    def draw_scripture(self, s, now):
        self.draw_sky(s)
        font = self.fonts["read"]
        title = self.read_title + ("   (%d / %d)" % (self.page + 1, len(self.pages)) if len(self.pages) > 1 else "")
        draw_text(s, self.fonts["mid"], title, (100, 70), GOLD)
        step = font.get_linesize()
        for col, lines in enumerate(self.pages[self.page]):
            for row, (num, line) in enumerate(lines):
                x, y = 100 + col * ((W - 260) // 2 + 60), 170 + row * step
                if num:
                    draw_text(s, self.fonts["tiny"], num, (x, y + 4), GOLD)
                draw_text(s, font, line, (x + 70, y), TEXT)
        self.draw_buttons(s, now)

    def draw_buttons(self, s, now):
        for button, _ in self.buttons():
            button.draw(s, self.fonts["mid" if button.radius >= 100 else "small"], now)

    def draw_panel(self, s, now):
        self.draw_sky(s)
        st, panels = self.story, art.panels(self.story)
        draw_text(s, self.fonts["small"], "%s   %d / %d" % (st.title, self.panel + 1, len(panels)), (70, 30), SOFT)
        if self.panel_pic is not None:
            s.blit(self.panel_pic, self.panel_pic_rect)
            pygame.draw.rect(s, GOLD, self.panel_pic_rect.inflate(10, 10), 4)
        font, (x, y) = self.panel_font, self.panel_text_at
        for line in self.panel_lines:
            if line:
                draw_text(s, font, line, (x, y), TEXT)
            y += int(font.get_linesize() * 1.1)
        self.draw_buttons(s, now)

    def draw_map(self, s, now):
        self.draw_sky(s)
        draw_text(s, self.fonts["mid"], self.story.title, (70, 70), GOLD)
        draw_text(s, self.fonts["small"], "Stories", (70, 385), GOLD)
        self.draw_buttons(s, now)

    def draw_card(self, s, now, ending=False):
        self.draw_sky(s)
        st = self.story
        pic = art.card(st, (int(W * 0.5), int(H * 0.72)))
        x0 = 70
        if pic is not None:
            r = pic.get_rect(midleft=(x0, H // 2))
            s.blit(pic, r)
            pygame.draw.rect(s, GOLD, r.inflate(10, 10), 4)
            x0 = r.right + 60
        width = W - x0 - 70
        y = draw_text(s, self.fonts["big"], st.title, (x0, 110), TEXT, width)
        if st.cfm and not ending:
            y = draw_text(s, self.fonts["small"], st.cfm, (x0, y + 10), GOLD, width)
        body = st.ending if ending else st.task
        y = draw_text(s, self.fonts["mid"], body, (x0, y + 30), TEXT, width)
        y = draw_text(s, self.fonts["small"], st.ref, (x0, y + 15), SOFT, width)
        if st.items and not ending:
            y = draw_text(s, self.fonts["small"], "Gather %d %s on the way." % (st.items[1], st.items[0]),
                          (x0, y + 15), SOFT, width)
        draw_text(s, self.fonts["small"], "♪ %s  (M: music on / off)" % st.song[0],
                  (x0, y + 30), SOFT, width)
        self.draw_buttons(s, now)

    def draw_maze(self, s, now):
        s.blit(self.maze_surface, (0, 0))
        k = self.cell
        for cell in self.items:
            draw_icon(s, self.story.items[2], [int(v) for v in self.center(cell)], int(k * 0.6),
                      self.item_variants.get(cell, 0))
        gx, gy = [int(v) for v in self.center(self.maze.goal)]
        locked = bool(self.items)
        glow = int(k * (0.5 + 0.04 * math.sin(now * 3)))
        pygame.draw.circle(s, (60, 55, 40) if locked else (95, 85, 50), (gx, gy), glow)
        if self.goal_img is not None:
            s.blit(self.goal_img, self.goal_img.get_rect(center=(gx, gy)))
        elif self.story.goal_icon in pictures.GOALS:
            pictures.GOALS[self.story.goal_icon](s, gx, gy, int(k * 0.8), dim=0.6 if locked else 1.0)
        else:
            self.draw_star(s, (gx, gy), k * 0.32, (120, 110, 70) if locked else (200, 170, 90))
        label = self.fonts["small"].render(self.story.goal_name, True, SOFT)
        s.blit(label, label.get_rect(midtop=(gx, gy + k * 0.42)) if gy + k < H else label.get_rect(midbottom=(gx, gy - k * 0.42)))
        if self.story.items:
            name, count, icon = self.story.items
            draw_icon(s, icon, (W - 260, 70), 48)
            draw_text(s, self.fonts["mid"], "%d / %d" % (self.collected, count), (W - 220, 48), TEXT)
        # the walker, with a soft ring while it follows the light
        px, py = int(self.pos[0]), int(self.pos[1])
        if self.following > 0:
            pygame.draw.circle(s, (70, 75, 120), (px, py), int(k * 0.5 + 6), max(2, int(6 * self.following)))
        s.blit(self.walker, self.walker.get_rect(center=(px, py)))
        if now - self.last_light > 6 and self.celebrate is None:
            ring = int(k * (0.6 + 0.08 * math.sin(now * 4)))
            pygame.draw.circle(s, (90, 90, 130), (px, py), ring, 3)
            draw_text(s, self.fonts["small"], "Shine your light on %s" % self.story.player_name,
                      (W // 2, H - 48), SOFT, anchor="midtop")
        if self.celebrate is not None:
            t = now - self.celebrate
            for i in range(12):
                a = i * math.pi / 6 + t * 0.6
                r0, r1 = k * 0.6, k * (0.8 + t * 1.2)
                pygame.draw.line(s, (200, 180, 110), (gx + math.cos(a) * r0, gy + math.sin(a) * r0),
                                 (gx + math.cos(a) * r1, gy + math.sin(a) * r1), 4)
        self.draw_buttons(s, now)

    @staticmethod
    def draw_star(s, c, r, color):
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rr = r if i % 2 == 0 else r * 0.45
            pts.append((c[0] + math.cos(a) * rr, c[1] + math.sin(a) * rr))
        pygame.draw.polygon(s, color, pts)

    def draw_calibration(self, s):
        s.fill((0, 0, 0))
        if self.cal_phase == "white":  # four white squares (flashlight.find_markers), not a whole white screen
            import flashlight
            side = int(H * flashlight.MARKER_SIZE)
            for x, y in flashlight.marker_centres((W, H)):
                s.fill((255, 255, 255), pygame.Rect(int(x) - side // 2, int(y) - side // 2, side, side))

    # --- main loop
    def handle_event(self, e):
        if e.type == pygame.QUIT:
            return False
        if e.type == pygame.MOUSEMOTION or e.type == pygame.MOUSEBUTTONDOWN:
            self.mouse_seen = time.time()
        if e.type == pygame.KEYDOWN:
            k = e.key
            if self.rec:
                self.rec.event("key", key=pygame.key.name(k), state=self.state)
            if k == pygame.K_ESCAPE:
                return False
            if k == pygame.K_F11:
                self.window = self._open_window(not (self.window.get_flags() & pygame.FULLSCREEN))
            elif k == pygame.K_m:
                self.toggle_music()
            elif k == pygame.K_b:
                self.toggle_blank()
            elif k == pygame.K_c and self.camera is not None:
                self.begin_calibration()
            elif k == pygame.K_d and self.camera is not None:
                self.camera.show_debug = not self.camera.show_debug
            elif k == pygame.K_n:
                self.next_story(1)
            elif k == pygame.K_p:
                self.next_story(-1)
            elif k == pygame.K_r and self.state == "maze":
                self.start_maze()
            elif k in (pygame.K_SPACE, pygame.K_RETURN):
                self.play("press")
                if self.reading:
                    self.close_scripture()
                elif self.state in ("panels", "map"):
                    self.button_action(0)
                else:
                    self.advance()
            elif k == pygame.K_s and self.state in ("card", "done", "panels"):
                if self.reading:
                    self.close_scripture()
                else:
                    self.open_scripture()
            elif k == pygame.K_t and self.state in ("card", "done", "panels", "maze") and not self.reading:
                self.open_panels(0) if self.state != "panels" else self.show_card()
            elif k in (pygame.K_o, pygame.K_TAB) and self.state not in ("calibrate",) and not self.reading:
                self.open_map()
            elif k == pygame.K_LEFT and self.state == "panels" and not self.reading:
                self.button_action(1)
            elif k == pygame.K_RIGHT and self.state == "panels" and not self.reading:
                self.button_action(0)
            elif k == pygame.K_LEFT:
                self.move_key(-1, 0)
            elif k == pygame.K_RIGHT:
                self.move_key(1, 0)
            elif k == pygame.K_UP:
                self.move_key(0, -1)
            elif k == pygame.K_DOWN:
                self.move_key(0, 1)
        return True

    def button_action(self, i):
        pairs = self.buttons()
        if i < len(pairs):
            pairs[i][1]()

    def advance(self):
        if self.state == "title":
            self.show_card()
        elif self.state == "card":
            self.start_maze(seed=self.args.seed)
        elif self.state == "done":
            self.next_story(1)

    def run(self):
        running = True
        last = time.time()
        while running:
            for e in pygame.event.get():
                running = running and self.handle_event(e)
            now = time.time()
            dt, last = min(0.1, now - last), now
            if self.blank:
                pass
            elif self.state == "calibrate":
                self.update_calibration()
            elif self.state == "maze":
                self.update_maze(dt, now)
            else:
                light = self.light()
                for button, action in self.buttons():
                    if button.update(light, dt):
                        self.play("press")
                        if self.rec:
                            self.rec.event("press", label=button.label, state=self.state, story=self.story.slug)
                        action()
                        break
            s = self.canvas
            if self.blank:
                s.fill((0, 0, 0))
            elif self.state == "calibrate":
                self.draw_calibration(s)
            elif self.reading:
                self.draw_scripture(s, now)
            elif self.state == "title":
                self.draw_title(s, now)
            elif self.state == "panels":
                self.draw_panel(s, now)
            elif self.state == "map":
                self.draw_map(s, now)
            elif self.state == "card":
                self.draw_card(s, now)
            elif self.state == "done":
                self.draw_card(s, now, ending=True)
            else:
                self.draw_maze(s, now)
            if self.message and now < self.message_until and self.state != "calibrate" and not self.blank:
                draw_text(s, self.fonts["small"], self.message, (W // 2, H - 95), GOLD, anchor="midtop")
            size = self.window.get_size()
            if size == (W, H):
                self.window.blit(s, (0, 0))
            else:  # smooth scaling: plain scaling drops rows and columns unevenly, so moving figures shimmer
                self.window.blit(pygame.transform.smoothscale(s, size), (0, 0))
            pygame.display.flip()
            if self.rec:
                self.rec.tick(now, s, self.camera.latest_frame() if self.camera else None, self.snapshot())
            self.clock.tick(FPS)
        if self.camera:
            self.camera.stop()
        if self.rec:
            self.rec.close()
        pygame.quit()


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--camera", type=int, default=int(os.environ.get("MAZE_CAMERA", 0)),
                   help="camera index (default 0, or MAZE_CAMERA)")
    p.add_argument("--display", type=int, default=None, help="display to show it on (default: the last one)")
    p.add_argument("--calibration", default=os.path.join(HERE, "calibration.yaml"),
                   help="projection corners in the camera image (projector_points, as in balloon-pop-game)")
    p.add_argument("--mouse", action="store_true", help="no camera; the mouse is the flashlight")
    p.add_argument("--window", action="store_true", help="a window instead of fullscreen")
    p.add_argument("--no-music", action="store_true", help="start with the music off (M turns it on)")
    p.add_argument("--story", help="start with this story (its slug in stories.py)")
    p.add_argument("--size", choices=sorted(SIZES), help="maze size for every story")
    p.add_argument("--seed", type=int, help="maze random seed")
    p.add_argument("--record", metavar="DIR", help="save the projected picture, camera video and a log to DIR (stays local)")
    return p.parse_args(argv)


if __name__ == "__main__":
    Activity(parse_args()).run()
    sys.exit(0)
