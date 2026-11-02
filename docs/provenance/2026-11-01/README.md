# 2026-11-01: first tests on the wall

A Claude Code session in which Sterling ran the activity with the projector, the camera and a flashlight for
the first time, and Claude changed it from what the recordings and Sterling's comments showed.

- `transcript.md`: Sterling's messages, Claude's replies and a one-line description of each command or file
  change. Tool outputs are left out, since they held the downloaded church pictures, scripture and song data
  and camera frames.
- `session1-log.jsonl.gz`, `session2-log.jsonl.gz`, `session3-log.jsonl.gz`: the `--record` logs of the three
  runs, about ten lines a second: screen state, story, the detected light (screen coordinates), the detector's
  numbers (`det`: brightest difference, its level, spot area in 480 x 270 detection pixels), the walker's cell
  and route, buttons' progress, plus events (keys, presses, items gathered, goals, messages). Read with
  `python -c "import gzip,sys; sys.stdout.write(gzip.open(sys.argv[1],'rt').read())" session2-log.jsonl.gz`.

Not here, on purpose: the camera videos (they show the room and family) and the screen videos (they show the
*Old Testament Stories* pictures). Camera frames were face-blurred on the computer, with `deface` (an offline
model), before Claude looked at any of them.

What the runs showed:

1. Session 1: the first calibration failed and the second worked. The projector shows the computer's only
   display, so the terminal and the song's browser tab covered the activity, and the detector took their
   bright text and pages for the flashlight; the maze was never really played. On the story card, a picture's
   bright sunbeam was taken for the flashlight, because the detector learned its background before the camera
   saw the new picture and then never learned the spot.
2. Session 2: Jeremiah (3 ropes) and Daniel were finished. The flashlight spot was 1200-5000 detection pixels
   while steering (5th to 75th percentile); stray detections were mostly under 300. Holding the light on
   **Next** pressed **Start** on the next card (same place), and one press came from a 30-pixel speck.
3. Session 3: opened and closed (9 seconds).
