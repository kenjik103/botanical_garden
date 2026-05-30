# Skin Import Tool — Spec

A Python tool that ingests a classic Winamp skin (`.wsz`) and emits everything the site
needs to wear that skin: a CSS custom-property palette, a sprite stylesheet for buttons and
accents, the bitmap-font assets, and a preview page. Run it against any `.wsz` and the
whole site re-skins.

This is a standalone build tool, separate from the Pelican build. It writes its output into
the theme's static assets; Pelican then serves them like any other CSS/image.

## Why this works (the core mechanism)

Classic Winamp skins do **not** store sprite coordinates. Winamp has the sprite layout
hardcoded internally — every skin's BMP sheets place each sprite at the same fixed
`(x, y, w, h)`. "Cutting" a sprite is just blitting a known rectangle. The exact web
equivalent is a CSS sprite: a fixed-size element with the sheet as `background-image` and
`background-position` set to the sprite's negative offset. So this tool's job is to pair
each skin's pixel sheets with the (universal, external) coordinate map and generate CSS.

## Inputs / outputs

**Input:** a `.wsz` file (a renamed ZIP — open with `zipfile`, no extraction needed) and a
coordinate map (see Module 2).

**Output**, written to `themes/mytheme/static/skins/<skin-name>/`:
- `*.png` — the sheets, converted from BMP.
- `skin-vars.css` — `:root { --… }` custom properties (the palette).
- `skin-sprites.css` — one class per sprite, with `:active` variants.
- `chars.json` (or similar) — the bitmap-font character→offset map, consumed by a Jinja2
  filter at Pelican build time.
- `preview.html` — swatches + rendered sample buttons/text to eyeball before committing.

## Module 1 — Palette extraction → `skin-vars.css`

Combine the readable text files with quantized chrome colors:

- **`pledit.txt`** (INI-style, `[Text]` section). Parse with `configparser`. Keys: `Normal`,
  `Current`, `NormalBG`, `SelectedBG`, `MbFG`, `MbBG` (hex like `#FF8924`), and `Font` (a
  typeface name). These are the deliberate, named colors — map them to semantic variables.
- **`viscolor.txt`** (24 lines, each `r,g,b` + comment). Split lines, take the first three
  ints. Layout: row 0 = vis background, row 1 = dots, rows 2–17 = spectrum analyzer
  (a 16-step gradient, row 2 = peak), rows 18–22 = oscilloscope (18 = trough → 22 = crest),
  row 23 = peak dots. The 16-step analyzer block is an excellent CSS accent gradient.
- **Chrome colors** are NOT in any text file — they're pixels in `main.bmp` and
  `titlebar.bmp`. Recover them with Pillow: `img.convert("P", palette=Image.ADAPTIVE,
  colors=N)` then read the palette, or histogram the most common colors. These give the
  dominant window/title-bar colors.

**Mapping is interpretive, not 1:1.** A skin has dozens of colors; the site has ~6–10
variables. Provide sensible defaults (e.g. `--text` ← `pledit.Normal`, `--text-active` ←
`pledit.Current`, `--bg` ← `pledit.NormalBG`, `--bg-selected` ← `pledit.SelectedBG`,
`--accent` ← a midpoint of the analyzer gradient, `--chrome` ← quantized `titlebar.bmp`),
but make the mapping a small editable dict at the top of the script so hand-tuning is easy.
Also emit `--skin-font: "<pledit Font>", monospace;`.

## Module 2 — Sprite stylesheet → `skin-sprites.css`

**Do not hand-author the coordinate map.** Lift it from **Webamp**, the JS Winamp
reimplementation, which renders classic skins pixel-for-pixel and therefore encodes every
sprite's `{name, x, y, width, height}` for every sheet in its source. Find the sprite
definition file in the Webamp repo (github.com/captbaritone/webamp) and convert that table
to a Python dict. This is the critical dependency — get this map and the rest is mechanical.

Known anchors for sanity-checking the map after import:
- `cbuttons.bmp`: transport buttons are 23×18; pressed states are stacked directly below
  the normal states.
- `numbers.bmp` / `nums_ex.bmp`: time digits, 9×13 each.
- `text.bmp`: font cells 5×6 (see Module 3).

For each sheet:
1. Convert BMP → PNG with Pillow (smaller, better-supported; transparency handling cleaner).
2. For each sprite in the map, emit a class:
   ```
   .spr-play { width:23px; height:18px;
     background-image:url(cbuttons.png); background-position:-Xpx -Ypx; }
   .spr-play:active { background-position:-Xpx -Y2px; }  /* pressed slot */
   ```
3. Where the map defines hover/pressed sub-sprites, emit `:hover` / `:active` variants.

Templates then use `<button class="spr-play">` etc. Slider thumbs (`posbar`, `volume`,
`balance`) can skin native `<input type=range>` thumbs if you want functional-looking
controls.

## Module 3 — Bitmap text → Jinja2 `skintext` filter

`text.bmp` is a bitmap font: a glyph atlas, fixed 5×6 cell per character, with a known
character ordering (also available in Webamp's source — lift the character→cell map rather
than guessing the layout).

- The tool emits `chars.json`: `{ "A": [x, y], "B": [x, y], … }` offsets into `text.png`.
- Register a Jinja2 filter in `pelicanconf.py` (via `JINJA_FILTERS`) named `skintext` that,
  given a string, emits a row of spans:
  ```
  <span class="skinchar" style="background-position:-Xpx -Ypx"></span>
  ```
  with `.skinchar { display:inline-block; width:5px; height:6px;
  background-image:url(.../text.png); image-rendering:pixelated; }`
- Usage in templates: `{{ "PROJECTS" | skintext }}` renders the heading in the skin's font.
  Uppercase only unless the skin's font defines lowercase; fall back to a space sprite for
  unmapped characters.

## Caveats (bake these into the tool / its docs)

- **Fake transparency.** Many accent sprites were drawn assuming they sit on `main.bmp`, so
  they may show a wrong-colored fringe on a different background. Self-contained sprites
  (transport/toggle buttons, font glyphs) transfer cleanly; background-dependent accents may
  need a matching backdrop or should be skipped. Have the tool flag/skip a configurable list.
- **Crispness.** Apply `image-rendering: pixelated` to every sprite/glyph element and scale
  only by integer factors (2×, 3×) or pixel art turns to mush.
- **States.** Remember to wire `:active` (and `:hover` where present) to the correct stacked
  sub-sprite offsets, or buttons won't visually depress.

## Build order

1. Module 1 (palette) first — smallest, proves the `.wsz`/`zipfile` plumbing and gives an
   immediate visible result (`skin-vars.css` + swatches in `preview.html`).
2. Module 2 starting with `cbuttons.bmp` only — the simplest sheet, dimensions already
   known, validates the Webamp coordinate map end-to-end.
3. Expand Module 2 to the remaining sheets once one works.
4. Module 3 (bitmap text) last — depends on the same slicing approach being proven.

## Tech

- Standard library: `zipfile`, `configparser`, `json`, `argparse`.
- `Pillow` for BMP→PNG conversion and chrome-color quantization. No other dependencies.
- CLI shape:
  `python import_skin.py path/to/skin.wsz --out themes/mytheme/static/skins/<name>/`
  then open the generated `preview.html` to review before committing.

## Integration with the site

The generated files live under the theme's static dir, so Pelican serves them automatically.
Switching skins = re-running the tool against a different `.wsz` (or pointing the site's
active-skin variable at a different generated folder). This is the data side of the
CSS-custom-property skin switcher already planned in PLAN.md.
