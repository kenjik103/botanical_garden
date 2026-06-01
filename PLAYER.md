# Homepage Audio Player — Spec

A small, directory-driven audio player that lives on the home page. Point it at a folder of
songs; it cycles through and plays them, using the Winamp sprite chrome for its controls.

## Scope & the persistence model

- **Homepage only.** The player exists on the home page and nowhere else.
- **Music persists across the site via new tabs, not via JS.** All navigation links to other
  sections use `target="_blank" rel="noopener"`, so opening Blog/Projects/etc. spawns a new
  tab and leaves the homepage tab — and its audio — alive. The music stops only if the user
  closes the homepage tab. This is why there's no SPA / page-swap layer: we don't need one.
- **No attempt to keep `<audio>` alive across navigation, and no autoplay-with-sound on load.**
  Browsers block audio from starting until a user gesture, so the player loads **paused** and
  first playback requires a click. This is a hard browser rule, not a choice.

This scope is consistent with CLAUDE.md and PLAN.md (homepage-only audio is in scope;
site-wide/persistent audio and SPA layers are not).

## Songs as a directory (source of truth)

- Audio files live in `content/music/`, listed in Pelican's `STATIC_PATHS` so they copy
  verbatim to `output/music/`.
- A **build-time manifest step** (a small Python script, or a Pelican hook) scans
  `content/music/` and writes `music.json` — an ordered list of `{ file, title }`. Pull the
  title from the filename, or from ID3/Vorbis tags if you want (e.g. `mutagen`), but tags are
  optional; filename is fine to start.
- The directory is the source of truth: drop in an mp3, rebuild, it appears in the player.
  No editing JS to add a song.

Example `music.json`:
```json
[
  { "file": "music/track-01.mp3", "title": "Track One" },
  { "file": "music/track-02.mp3", "title": "Track Two" }
]
```

## Player logic (vanilla JS, no framework)

A single `player.js` in the theme's static JS:

1. `fetch('/music.json')` → the track list. Hold a current-track index.
2. One `<audio>` element (not shown to the user; the sprite UI drives it).
3. Wire the sprite transport buttons (from `skin-sprites.css`) to real controls:
   - play / pause → `audio.play()` / `audio.pause()`
   - stop → pause + reset to start
   - prev / next → change index, load, play
4. **Cycling:** `audio.addEventListener('ended', nextTrack)` advances automatically; wrap
   from last back to first.
5. Optional **shuffle / repeat** mapped onto the `shufrep.bmp` sprites (toggle state → swap to
   the "on" sprite offset; shuffle randomizes next index, repeat re-plays current).

## Sprite / chrome integration

These all reuse assets already produced by the skin-import tool (SKIN_IMPORT.md):

- **Transport buttons** = the `cbuttons.bmp` sprites, now functional, with `:active` showing
  the pressed sub-sprite so they physically depress on click.
- **Time readout** = the `numbers.bmp` bitmap digits, updated from `audio.currentTime`.
- **Track title** = a marquee rendered with the `text.bmp` bitmap font (the `skintext`
  Jinja2 filter / `chars.json` map), scrolling if it overflows.
- **Spectrum analyzer** (optional, very on-theme) = Web Audio `AnalyserNode` → `<canvas>`,
  colored from the `viscolor.txt` palette already extracted. Pure vanilla JS.

## Constraints to respect

- **First play needs a click.** Player loads paused; no autoplay-with-sound. Don't try to
  defeat this.
- **File size.** Cloudflare Pages caps a single asset at 25 MiB; larger files are meant to
  go to R2, not Pages. Keep tracks as compressed mp3/ogg/m4a and curate a handful — a FLAC
  album would blow the per-file cap and the free-plan file budget. (Free plan: 20,000 files
  total — irrelevant for a few songs, just don't dump a library.)
- **Copyright.** A public site publicly serves these files. Hosting commercial tracks you
  don't hold rights to is infringement. Prefer your own music, Creative Commons, or licensed
  tracks. Owner's call, but the exposure is real.

## Build order — one piece per Claude Code session

1. **Manifest step.** The Python script that scans `content/music/` → `music.json`, wired
   into the build. Verify the JSON is correct before any UI.
2. **Minimal player.** `<audio>` + a working play/pause bound to one sprite button, playing
   the first track. Prove the audio plumbing end-to-end.
3. **Prev / next + auto-cycle.** Index navigation and the `ended` → next handler.
4. **Bitmap readouts.** `numbers.bmp` time display and the `text.bmp` title marquee.
5. **Shuffle / repeat** via the `shufrep.bmp` sprites.
6. **(Optional) visualizer.** The `AnalyserNode` → canvas spectrum analyzer.

## How to direct Claude Code

- Each session: "Read CLAUDE.md, PLAYER.md, and `skin-sprites.css`. We're doing step N."
- **One piece per session**, and **you verify by actually listening** — Claude Code can't
  hear the audio or see the page. Confirm playback, cycling, and button states in the browser
  before moving on.
- Keep it **vanilla JS, no framework, no build step beyond the Python manifest script.**
- Reinforce the persistence model: section nav links use `target="_blank" rel="noopener"`;
  there is no SPA layer and no attempt to persist `<audio>` across page loads.

## Related docs

- Sprite assets (`skin-sprites.css`, `numbers`/`text` handling, `viscolor` palette):
  SKIN_IMPORT.md
- Where the transport buttons live and how nav moved to the playlist panel: REFACTOR.md
- Scope rules and `content/music/` / `STATIC_PATHS`: PLAN.md, CLAUDE.md
