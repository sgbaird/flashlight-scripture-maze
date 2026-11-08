# Flashlight Scripture Mazes

A Sunday activity for families: a maze is projected on the wall, and children guide a figure from a
scripture story through it by shining a flashlight just ahead of them. Each maze goes with a story from
[Old Testament Stories](https://www.churchofjesuschrist.org/study/manual/old-testament-stories-2022?lang=eng),
starting with this week's [Come Follow Me](https://www.churchofjesuschrist.org/study/manual/come-follow-me-for-home-and-church-old-testament-2026?lang=eng)
lesson, and a song from the [Children's Songbook](https://www.churchofjesuschrist.org/media/music/collections/childrens-songbook?lang=eng)
playing softly (the instrumental accompaniment, without the words).

> "Thy word is a lamp unto my feet, and a light unto my path." (Psalm 119:105)

## How it plays

1. **Title screen.** Hold the flashlight on the circle to begin.
2. **Story card.** The story's picture, what to do, the scripture reference and the song, which plays
   softly in the background (**M** turns the music off and on). Hold the light on **Story** to step
   through the story as the book tells it, on **Read** for the scripture passage itself (**More** for the
   next page, **Back** to return), or on **Start**. A button counts the light only after it has been off
   the button for a moment, so a light left where the last button was does not press the next one.
3. **Story pages.** The *Old Testament Stories* chapter one panel at a time: its picture and words, with
   **Next** and **Back**. The verses a panel cites are buttons too (e.g. **Jeremiah 38:6**): hold the light on
   one to read those verses, then **Back** to the page. **Next** on the last page goes to the maze.
4. **The maze.** Shine the light near the figure, a little ahead of where it should go, and it walks
   there along the paths (it follows a light up to about two squares away and never walks through
   walls). Some stories have things to gather on the way (ropes, smooth stones, grain...) before the
   goal opens.
5. **The ending.** The story's picture again with how the story ends. Hold the light on **Next** for
   the next story (or **Read** for the passage).

**Map**, in the bottom left corner (top right in the maze), goes anywhere: this story's card, each story
page (with its picture), the passage and the maze (back where you left it), or any other story (its
portrait and a word or two). **Back** returns to where you were.

| Story | Scripture | Gather | Song |
|---|---|---|---|
| Daniel and His Friends (Come Follow Me, Nov 9–15) | Daniel 1 | 4 vegetables | The Word of Wisdom |
| Daniel and the King's Dream (Nov 9–15) | Daniel 2 | | Search, Ponder, and Pray |
| The Fiery Furnace (Nov 9–15) | Daniel 3 | | Stand for the Right |
| Daniel and the Lions' Den (Nov 9–15) | Daniel 6 | | A Child's Prayer |
| Jeremiah in the Dungeon (Oct 26–Nov 1) | Jeremiah 38:6–13 | 3 ropes | Follow the Prophet |
| David's Five Smooth Stones | 1 Samuel 17 | 5 stones | I Will Be Valiant |
| Noah's Ark | Genesis 6–7 | 4 animals | Follow the Prophet |
| Baby Moses | Exodus 2 | | I Am a Child of God |
| Through the Red Sea | Exodus 14 | | I Will Follow God's Plan |
| Ruth Gathers Grain | Ruth 2 | 5 grain | Love One Another |
| Queen Esther | Esther 4–5 | | Choose the Right |
| Jonah Goes to Nineveh | Jonah 3 | | Keep the Commandments |

Stories live in `stories.py`; add or reorder them there. Every maze is generated fresh, so **R** gives
a new one.

## Setup

You need a projector, a webcam that sees the whole projected picture, and a flashlight. The room
should be dim: the activity keeps its picture dark so that the flashlight is the brightest thing the camera
sees.

```
pip install -r requirements.txt
python fetch_art.py            # download the story pictures, scripture passages and songs (once)
python activity.py --camera 1  # pick your camera; it opens on the last display (the projector)
```

On the first run (and whenever you press **C**) the activity calibrates itself: it shows a black screen and
then four white squares, and finds them in the camera image (four squares rather than a white screen,
which lights up the ceiling and walls as much as the picture). Keep people and the flashlight out of the
picture for those few seconds. It waits for the projector to show the activity, starts only while the
activity's window is in front, and tries up to three times. The corners are saved in `calibration.yaml`. The balloon game's
`projector_calibration.yaml` from [sgbaird/balloon-pop-game](https://github.com/sgbaird/balloon-pop-game)
has the same format (`--calibration path/to/projector_calibration.yaml`) if the camera and projector
have not moved.

| Key | |
|---|---|
| **M** | Music off / on |
| **S** | Scripture passage on the story card, ending or story pages (again to close) |
| **T** | Story pages (again for the card) |
| **O** / Tab | Map |
| Left / right | Previous / next story page |
| **B** | Blank (black) screen and pause, to read from a book; **B** again to go on |
| **N** / **P** | Next / previous story |
| **R** | New maze |
| **C** | Recalibrate |
| **D** | Show the camera view (with the projection outline and the detected spot) |
| Arrow keys | Move the figure one square |
| Space / Enter | Same as holding the light on the button |
| **F11** | Fullscreen on / off |
| **Esc** | Quit |

Options: `--mouse` (no camera; the mouse is the flashlight), `--window`, `--display N`,
`--story <slug>`, `--size small|medium|large`, `--no-music` (start with the music off),
`--seed N`, `--record DIR` (save the projected picture, the camera video and a log of what was detected to
`DIR`, to look into a problem afterwards; the camera video shows the room, so keep it on your own computer).
The camera can also be set with `MAZE_CAMERA=1`. The mouse also works as the flashlight whenever it has
moved in the last two seconds.

### If the flashlight is not picked up

Press **D** to see what the camera sees. The thresholds are at the top of `flashlight.py`:
`MIN_LEVEL` (how bright the spot must be, 0–255), `DIFF` (how much brighter than the projected
picture) and `MIN_AREA` (how big the spot must be in the camera's view). Lower them for a weak or far
flashlight or a bright room; raise them if the figure wanders off or buttons press by themselves. A narrow, bright beam works best.

## Pictures and music

The pictures and story text are from *Old Testament Stories* (2022) and the songs are from the
*Children's Songbook*, both © Intellectual Reserve, Inc. Their
[terms of use](https://www.churchofjesuschrist.org/legal/terms-of-use?lang=eng) allow personal,
noncommercial use, so this repository does not contain them. `fetch_art.py` downloads the pictures,
the story's words panel by panel, the verses of each story's scripture reference and of every reference the
panels cite, and each song's instrumental accompaniment from its
song page, to `art/` on your own computer (git ignores that folder). Without the pictures the activity draws simple figures instead, and without the
music it is quiet.

The mazes are generated by the activity, in the spirit of the mazes in the *Friend* magazine; none are
copied from it.

## Development

`python -m pytest tests` checks the maze generator, the flashlight detector (on synthetic camera
frames) and the story list. The activity itself needs a projector, a camera and a display, so check
changes to `activity.py` by running it (`python activity.py --mouse --window` works without a camera).

`@codex` in an issue or comment starts a Codex session on GitHub Actions; see `AGENTS.md`.
