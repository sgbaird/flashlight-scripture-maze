# Flashlight Scripture Mazes

Sterling's (`sgbaird`) projector game for Sunday family play: a maze is projected on a wall, a camera watches
it, and children guide a scripture-story figure through the maze with a flashlight. `README.md` covers play and
setup.

- Python with OpenCV, NumPy, pygame and PyYAML (`requirements.txt`).
- `game.py` is the entry point (pygame, screens, walker, dwell buttons). `maze.py` (generation, paths, item
  placement) and `flashlight.py` (calibration geometry, spot detection, camera thread) have no pygame, so they
  are unit-tested. `art.py` turns the downloaded pictures into cards and circular portraits. `stories.py` lists
  the stories, their picture crops and songs. `fetch_art.py` downloads the pictures.
- Check changes with `python -m pytest tests` and `python -m py_compile *.py`. The game needs a projector,
  camera and display, so a CI runner cannot play it; `python game.py --mouse --window` runs without a camera.
  Say what was not run.
- Keep the projected picture dim: dark sky, muted walls (`WALL`), portraits dimmed (`art.portrait`). The
  detector finds the flashlight as the patch that is both much brighter than the learned background and bright
  in absolute terms (`DIFF`, `MIN_LEVEL` in `flashlight.py`). Anything bright and moving that the game draws can
  be mistaken for the flashlight; never draw a marker at the detected spot (it would detect itself).
- Content must suit Sunday: scripture stories told as in *Old Testament Stories*, gentle sounds, nothing scary
  or violent (the lions are quiet; David's maze is about gathering stones, not the fight).

## Church media: never commit it

The *Old Testament Stories* pictures and text and *Children's Songbook* music are © Intellectual Reserve, Inc.,
licensed for personal, noncommercial use. This repository is public, so:

- Never commit pictures, story text, audio or sheet music from churchofjesuschrist.org (or the *Friend*
  magazine). `art/` is git-ignored; `fetch_art.py` fills it on the player's computer.
- Links are fine: story pages, song pages (`https://www.churchofjesuschrist.org/media/music/songs/<slug>`), and
  the image IDs the content API returns. Before adding a song, check that its page title is the song's name; an
  unknown slug still returns HTTP 200 with the title "Music Library".
- Mazes are generated, never traced or copied from the *Friend*.
- A Codex session on GitHub cannot see `art/`, so the game must work without it (drawn figures).

## @codex on GitHub

`@codex` (`.github/workflows/codex.yml`) in an issue (title or body) or an issue or PR conversation comment starts
a Codex session, for anyone with write access. Model and effort tags: `@codex+gpt-6-luna:high`, `@codex:low`; a bare
tag uses the plan's defaults. On an issue, a session that changes files opens a pull request from its branch. The pull
request description holds the full write-up and key images; the reply on the issue is one sentence linking it. (If
it cannot open one, the write-up goes in the reply with a compare link.) Efforts: `none`, `minimal`, `low`, `medium`,
`high`, `xhigh`, `max`, `ultra` (each model accepts a subset). The first tag with a `+model` or `:effort` wins,
wherever it is in the title or body. On an issue the session works on a new `codex/issue-<n>-<run>` branch; on a PR it
pushes to the PR's branch. Every `@codex` starts at once, so other sessions may be working on the same issue or PR:
check with `gh run list -w codex.yml --status in_progress` and the thread's "working on this" comments, and on a
shared PR branch `git pull --rebase` before each push rather than force-pushing. Cancel a run from the Actions tab.
While it runs, its "working on this" comment shows the plan, the latest interim message and the recent commands
(never their output), updated about once a minute, so anything a session writes in an interim message or a command
line is public on this repository.

## The shared Codex login (for Sterling and for sessions)

Every run uses one ChatGPT-managed login (`auth.json`), following
https://learn.chatgpt.com/docs/auth/ci-cd-auth for ephemeral runners. Same design as `sgbaird/balloon-pop-game`
and `ME-EN-250/me-en-250-private`, each with its own separate login.

- `.github/actions/codex-run` restores the newest encrypted copy from the Actions cache (key prefix `codex-auth-`),
  falling back to the `CODEX_AUTH_JSON` secret, and saves a new encrypted copy whenever Codex rewrote the file.
  `CODEX_AUTH_KEY` is the encryption passphrase. No token with secret-write access is involved.
- `codex-keepalive.yml` forces a refresh on Mondays and Thursdays. Codex itself refreshes only within 5 minutes of
  the 10-day access token's expiry (or on a 401), so ordinary runs never refresh and can run in parallel.
- This repository is public: GitHub turns off scheduled workflows after 60 days with no repository activity. If the
  keep-alive stops, re-enable it under Actions and reseed.
- Sessions: never read, print or copy anything under `$CODEX_HOME`.
- **Reseed** if a run fails with "Reseed CODEX_AUTH_JSON", or the keep-alive fails twice in a row. On Sterling's
  PC, in PowerShell: `$env:CODEX_HOME="$env:USERPROFILE\.codex-ci-maze"; npx -y @openai/codex@0.165.0 login`,
  then `gh secret set CODEX_AUTH_JSON -R sgbaird/flashlight-scripture-maze < $env:USERPROFILE\.codex-ci-maze\auth.json`,
  delete the cache entries (`gh cache delete --all -R sgbaird/flashlight-scripture-maze`), run the keep-alive by
  hand (`gh workflow run codex-keepalive.yml -R sgbaird/flashlight-scripture-maze`), and then delete the local
  `auth.json`. Never use that CODEX_HOME for local work, and never reuse another repository's CI login: the CI
  copy rotates its tokens, and two holders of one login log each other out.
