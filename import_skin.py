#!/usr/bin/env python3
"""Import a classic Winamp skin (.wsz) and emit everything the site needs to
wear it: a CSS custom-property palette, a sprite stylesheet, the bitmap-font
assets, and a preview page.

This is a STANDALONE build tool, separate from the Pelican build. It writes
into the theme's static dir; Pelican then serves the output like any other
asset. See SKIN_IMPORT.md for the full spec.

    python import_skin.py path/to/skin.wsz --out themes/mytheme/static/skins/<name>/

Then open the generated preview.html to review before committing. Re-running
against a different .wsz (and pointing pelicanconf's ACTIVE_SKIN at the new
folder) re-skins the whole site.

Dependencies: standard library + Pillow. No others.
"""

import argparse
import configparser
import html
import io
import json
import os
import sys
import zipfile

try:
    from PIL import Image
except ImportError:
    sys.exit("This tool needs Pillow:  pip install Pillow")

import webamp_sprites as wa


# =====================================================================
#  Module 1 config — palette mapping  (EDIT HERE to hand-tune a skin)
# =====================================================================
# A skin has dozens of colors; the site has ~6-10 CSS variables. The mapping
# is interpretive, not 1:1. build_vars() below assembles a `src` dict of named
# source colors pulled from the skin, then maps them onto the site's real
# custom-property names (the ones in themes/mytheme/static/css/style.css).
#
# To re-tune a skin by hand, tweak build_vars() — it's deliberately explicit
# rather than a clever table, so every choice is visible and editable.

# Sprites whose CSS class should be skipped entirely (see "fake transparency"
# caveat in SKIN_IMPORT.md — background-dependent accents transfer poorly).
SKIP_SPRITES = set()

# Friendly short aliases for the most-used controls, so templates can write
# <button class="spr-play"> instead of the full Webamp name. Maps the Webamp
# base sprite name -> short class suffix.
SPRITE_ALIASES = {
    "MAIN_PREVIOUS_BUTTON": "prev",
    "MAIN_PLAY_BUTTON": "play",
    "MAIN_PAUSE_BUTTON": "pause",
    "MAIN_STOP_BUTTON": "stop",
    "MAIN_NEXT_BUTTON": "next",
    "MAIN_EJECT_BUTTON": "eject",
}

# Playlist frame pieces cropped into standalone PNGs. Two reasons: (1) you
# can't background-repeat a sub-region of the combined sheet, so tileable
# edges need their own image; (2) the sheet has 1px separator rows/cols
# between cells — at fractional display scales a background-position sprite
# samples across that boundary and bleeds the separator in as a thin line, so
# even the (non-tiled) corner is cropped to isolate it. Maps output filename
# -> the Webamp sprite to crop from the PLEDIT sheet.
EDGE_TILES = {
    "pledit-top-tile.png":    "PLAYLIST_TOP_TILE_SELECTED",
    "pledit-bottom-tile.png": "PLAYLIST_BOTTOM_TILE",
    "pledit-left-tile.png":   "PLAYLIST_LEFT_TILE",
    "pledit-right-tile.png":  "PLAYLIST_RIGHT_TILE",
    "pledit-corner.png":      "PLAYLIST_TOP_LEFT_CORNER",
}


# =====================================================================
#  .wsz plumbing
# =====================================================================
class Skin:
    """A loaded .wsz (a renamed ZIP). Files are matched case-insensitively by
    basename, since skin authors are inconsistent about casing and folders."""

    def __init__(self, path):
        self.path = path
        self.zip = zipfile.ZipFile(path)
        # lowercased basename -> archive member name
        self._index = {}
        for name in self.zip.namelist():
            if name.endswith("/"):
                continue
            self._index[os.path.basename(name).lower()] = name

    def has(self, filename):
        return filename.lower() in self._index

    def read_bytes(self, filename):
        member = self._index[filename.lower()]
        return self.zip.read(member)

    def read_text(self, filename):
        raw = self.read_bytes(filename)
        # Skin text files are typically Windows-1252 / latin-1; decode loosely.
        for enc in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("latin-1", errors="replace")

    def open_image(self, filename):
        """Open a BMP sheet as an RGB Pillow image."""
        return Image.open(io.BytesIO(self.read_bytes(filename))).convert("RGB")


# =====================================================================
#  small color helpers
# =====================================================================
def _clamp(v):
    return max(0, min(255, int(round(v))))


def hexc(rgb):
    return "#%02x%02x%02x" % (_clamp(rgb[0]), _clamp(rgb[1]), _clamp(rgb[2]))


def rgba(rgb, a):
    return "rgba(%d, %d, %d, %s)" % (_clamp(rgb[0]), _clamp(rgb[1]), _clamp(rgb[2]), a)


def mix(a, b, t):
    """Linear blend a->b by t in [0,1]."""
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def lighten(rgb, t):
    return mix(rgb, (255, 255, 255), t)


def darken(rgb, t):
    return mix(rgb, (0, 0, 0), t)


def luma(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.4152 * rgb[2]


def parse_hex(s):
    """'#FF8924' or 'FF8924' -> (r,g,b). Returns None if unparseable."""
    if not s:
        return None
    s = s.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        return None
    try:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return None


def dominant_colors(img, n=3, sample_box=None):
    """Return the n most common colors in (a region of) an image, ignoring
    near-black/near-white noise where possible. Used to recover chrome colors
    from main.bmp / titlebar.bmp, which store no named palette."""
    if sample_box:
        img = img.crop(sample_box)
    # Quantize to a small adaptive palette, then rank colors by pixel count.
    q = img.convert("P", palette=Image.ADAPTIVE, colors=16).convert("RGB")
    colors = q.getcolors(maxcolors=4096) or []  # [(count, rgb), ...]
    ranked = [rgb for _, rgb in sorted(colors, key=lambda c: c[0], reverse=True)]
    return ranked[:n] if ranked else [(128, 128, 128)]


# =====================================================================
#  Module 1 — palette extraction -> skin-vars.css
# =====================================================================
def parse_pledit(skin):
    """Parse pledit.txt's [Text] section. Returns a dict of named colors
    (as rgb tuples) plus 'font' (str), with any subset possibly missing."""
    out = {}
    if not skin.has("pledit.txt"):
        return out
    cp = configparser.ConfigParser(strict=False, interpolation=None)
    try:
        cp.read_string(skin.read_text("pledit.txt"))
    except configparser.Error:
        return out
    if not cp.has_section("Text"):
        # Some skins lowercase the section name.
        for sect in cp.sections():
            if sect.lower() == "text":
                cp._sections["Text"] = cp._sections[sect]
                break
        else:
            return out
    sect = cp["Text"]
    for key in ("Normal", "Current", "NormalBG", "SelectedBG", "MbFG", "MbBG"):
        val = None
        for k in sect:
            if k.lower() == key.lower():
                val = sect[k]
                break
        rgb = parse_hex(val)
        if rgb:
            out[key] = rgb
    for k in sect:
        if k.lower() == "font":
            out["font"] = sect[k].strip()
            break
    return out


def parse_viscolor(skin):
    """Parse viscolor.txt -> list of (r,g,b). 24 rows:
    0=vis bg, 1=dots, 2-17=spectrum analyzer (16-step, row2=peak),
    18-22=oscilloscope, 23=peak dots."""
    rows = []
    if not skin.has("viscolor.txt"):
        return rows
    for line in skin.read_text("viscolor.txt").splitlines():
        # Lines look like:  255,255,255 // comment
        head = line.split("//")[0].split(";")[0].strip()
        if not head:
            continue
        parts = [p for p in head.replace("\t", " ").replace(" ", ",").split(",") if p != ""]
        try:
            r, g, b = (int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            continue
        rows.append((r, g, b))
    return rows


def build_vars(skin):
    """Assemble the site's CSS custom properties from the skin.

    Returns (vars_dict, notes_list). `vars_dict` keys are the real variable
    names used in themes/mytheme/static/css/style.css, so emitting them as a
    :root block recolors the whole site.
    """
    notes = []
    pledit = parse_pledit(skin)
    vis = parse_viscolor(skin)

    # --- gather named source colors, with graceful fallbacks --------------
    text = pledit.get("Normal", (16, 38, 58))
    text_active = pledit.get("Current", (54, 163, 224))
    bg = pledit.get("NormalBG", (255, 255, 255))
    bg_selected = pledit.get("SelectedBG", (90, 131, 176))
    mb_fg = pledit.get("MbFG", text_active)

    # Analyzer gradient (16 steps) -> accent. Row 2 is the peak/brightest.
    analyzer = vis[2:18] if len(vis) >= 18 else []
    if analyzer:
        accent = analyzer[len(analyzer) // 2]   # midpoint of the gradient
        accent_hot = analyzer[0]                # peak
    else:
        accent = text_active
        accent_hot = text_active
        if not vis:
            notes.append("viscolor.txt missing — accent derived from pledit Current.")

    # Chrome colors live in the title bar / main window pixels, not text files.
    if skin.has("titlebar.bmp"):
        chrome_ranked = dominant_colors(skin.open_image("titlebar.bmp"), n=4)
    elif skin.has("main.bmp"):
        chrome_ranked = dominant_colors(skin.open_image("main.bmp"), n=4)
    else:
        chrome_ranked = [(47, 127, 214)]
        notes.append("No titlebar.bmp/main.bmp — chrome colors are a fallback.")
    # Pick a mid chrome tone, then derive a top (lighter) and bottom (darker).
    chrome_mid = chrome_ranked[0]
    chrome_top = lighten(chrome_mid, 0.28)
    chrome_bot = darken(chrome_mid, 0.28)

    if skin.has("main.bmp"):
        window_bg = dominant_colors(skin.open_image("main.bmp"), n=1)[0]
    else:
        window_bg = lighten(bg, 0.1)

    # Chrome text must read against chrome_mid; pick white or near-black.
    chrome_ink = (255, 255, 255) if luma(chrome_mid) < 150 else (20, 30, 45)

    font = pledit.get("font")

    # --- map onto the site's real custom-property names -------------------
    v = {}
    # page backdrop (the big gradient behind the window): Winamp skins are
    # dark, so pull a dark gradient from the skin's own window/playlist colors
    # rather than lightening the chrome into a pale page (the bitmap display
    # text is light and must read against it).
    v["--page-bg-top"] = hexc(window_bg)
    v["--page-bg-mid"] = hexc(mix(window_bg, bg_selected, 0.5))
    v["--page-bg-bot"] = hexc(bg_selected)

    # the application window
    v["--window-bg"] = hexc(window_bg)
    v["--window-border"] = hexc(chrome_bot)
    v["--content-bg"] = hexc(bg)              # pledit NormalBG (playlist bg)
    v["--content-ink"] = hexc(text)           # pledit Normal (track text)
    v["--selected-bg"] = hexc(bg_selected)    # pledit SelectedBG (selected row)
    v["--muted-ink"] = hexc(mix(text, bg, 0.4))

    # glossy chrome (title bar / nav / buttons)
    v["--chrome-top"] = hexc(chrome_top)
    v["--chrome-mid"] = hexc(chrome_mid)
    v["--chrome-bot"] = hexc(chrome_bot)
    v["--chrome-ink"] = hexc(chrome_ink)

    # bevels — keep the structural light/demphasis but tint toward the skin
    v["--bevel-light"] = rgba(lighten(chrome_top, 0.5), "0.85")
    v["--bevel-dark"] = rgba(darken(chrome_bot, 0.4), "0.45")

    # accents
    v["--accent"] = hexc(accent)
    v["--accent-glow"] = rgba(lighten(accent_hot, 0.1), "0.55")
    v["--link"] = hexc(text_active)
    v["--link-hover"] = hexc(darken(text_active, 0.25))

    # type — only override font if the skin named one
    if font:
        v["--font-ui"] = '"%s", "Segoe UI", Tahoma, sans-serif' % font
        v["--font-body"] = '"%s", "Segoe UI", Tahoma, sans-serif' % font
    # skin font hook (per spec) — bitmap font name, monospace fallback
    v["--skin-font"] = '"%s", monospace' % (font or "monospace")

    return v, notes


def write_vars_css(vars_dict, notes, out_dir, skin_name):
    lines = [
        "/* skin-vars.css — generated by import_skin.py from %s */" % skin_name,
        "/* Loaded AFTER the theme's style.css, so :root here overrides the",
        "   default 'aero' palette and recolors the entire site. */",
    ]
    for note in notes:
        lines.append("/* NOTE: %s */" % note)
    lines.append(":root {")
    width = max(len(k) for k in vars_dict)
    for k, val in vars_dict.items():
        lines.append("  %-*s %s;" % (width + 1, k + ":", val))
    lines.append("}")
    path = os.path.join(out_dir, "skin-vars.css")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return path


# =====================================================================
#  Module 2 — sprite stylesheet -> skin-sprites.css
# =====================================================================
def _kebab(name):
    return name.lower().replace("_", "-")


def _pos(v):
    """Format one background-position axis: 0 stays '0', else '-Npx'."""
    return "0" if v == 0 else "-%dpx" % v


def _esc(s):
    return html.escape(str(s), quote=True)


def _base_and_state(name):
    """Split a Webamp sprite name into (base, state) where state is one of
    'normal', 'active' (pressed), or None for things we keep as-is.
    e.g. MAIN_PLAY_BUTTON_ACTIVE -> ('MAIN_PLAY_BUTTON', 'active')."""
    for suffix in ("_ACTIVE", "_DEPRESSED"):
        if name.endswith(suffix):
            return name[: -len(suffix)], "active"
    return name, "normal"


def class_for(name):
    """CSS class suffix for a sprite base name (alias if we defined one)."""
    return SPRITE_ALIASES.get(name, _kebab(name))


def convert_sheets(skin, out_dir):
    """Convert every present BMP sheet (that we have coordinates for) to PNG.
    Returns {sheet_key: png_filename}."""
    written = {}
    for sheet, sprites in wa.SPRITES.items():
        if sheet == "TEXT":
            continue  # handled by Module 3
        bmp = wa.SHEET_FILES[sheet]
        if not skin.has(bmp):
            continue
        png_name = os.path.splitext(bmp)[0] + ".png"
        img = skin.open_image(bmp)
        img.save(os.path.join(out_dir, png_name))
        written[sheet] = png_name
    return written


def write_edge_tiles(skin, out_dir):
    """Crop the playlist's tileable edge pieces (top/bottom/left/right) into
    standalone PNGs so the theme can tile them seamlessly with background-
    repeat — the combined sheet can't be repeated a sub-region at a time.
    Returns the list of filenames written (empty if the skin has no pledit)."""
    bmp = wa.SHEET_FILES["PLEDIT"]
    if not skin.has(bmp):
        return []
    sheet = skin.open_image(bmp)
    by_name = {s["name"]: s for s in wa.SPRITES["PLEDIT"]}
    written = []
    for fname, sprite_name in EDGE_TILES.items():
        s = by_name[sprite_name]
        box = (s["x"], s["y"], s["x"] + s["width"], s["y"] + s["height"])
        sheet.crop(box).save(os.path.join(out_dir, fname))
        written.append(fname)
    return written


def write_sprites_css(skin, out_dir, sheets):
    """Emit one class per sprite with :active variants wired to pressed slots."""
    out = [
        "/* skin-sprites.css — generated by import_skin.py */",
        "/* Each class is a fixed-size element showing one sprite via",
        "   background-position. Use like <button class=\"spr-play\"></button>.",
        "   Scale only by integer factors or the pixel art turns to mush. */",
        "",
        "[class^=\"spr-\"], [class*=\" spr-\"] {",
        "  display: inline-block;",
        "  image-rendering: pixelated;",
        "  background-repeat: no-repeat;",
        "  border: 0; padding: 0; background-color: transparent;",
        "}",
        "",
    ]
    flagged = []
    for sheet, png_name in sheets.items():
        # Group this sheet's sprites by base name so ACTIVE/DEPRESSED become
        # :active on the base class rather than separate classes.
        by_base = {}
        for spr in wa.SPRITES[sheet]:
            base, state = _base_and_state(spr["name"])
            by_base.setdefault(base, {})[state] = spr

        out.append("/* ---- %s (%s) ---- */" % (sheet.lower(), png_name))
        for base, states in by_base.items():
            normal = states.get("normal")
            if normal is None:
                # Pressed-only sprite with no normal slot; emit it standalone.
                normal = next(iter(states.values()))
            if normal["name"] in SKIP_SPRITES:
                flagged.append(normal["name"])
                continue
            cls = class_for(base)
            out.append(
                ".spr-%s { width:%dpx; height:%dpx;"
                " background-image:url(%s);"
                " background-position:%s %s; }"
                % (cls, normal["width"], normal["height"], png_name,
                   _pos(normal["x"]), _pos(normal["y"]))
            )
            active = states.get("active")
            if active is not None and active is not normal:
                out.append(
                    ".spr-%s:active { background-position:%s %s; }"
                    % (cls, _pos(active["x"]), _pos(active["y"]))
                )
        out.append("")

    path = os.path.join(out_dir, "skin-sprites.css")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")
    return path, flagged


# =====================================================================
#  Module 3 — bitmap text -> chars.json + .skinchar CSS + skintext filter
# =====================================================================
def _font_to_transparent(img, tol=20):
    """Key the font sheet's background to transparent so glyphs render on any
    surface. Winamp's text.bmp pads its cells with the display's background
    color (opaque); left as-is, every glyph shows that color as a box on a
    mismatched surface (e.g. the playlist rows). The background is taken from
    the top-left padding pixel (the glyph color may actually be the single
    most-common color, so don't key by frequency); the bg is often dithered,
    so pixels within `tol` of the corner color become transparent."""
    img = img.convert("RGBA")
    br, bgc, bb, _ = img.getpixel((0, 0))
    keyed = [
        (r, g, b, 0)
        if abs(r - br) <= tol and abs(g - bgc) <= tol and abs(b - bb) <= tol
        else (r, g, b, a)
        for r, g, b, a in img.getdata()
    ]
    img.putdata(keyed)
    return img


def write_font(skin, out_dir):
    """Convert text.bmp -> text.png, emit chars.json (char -> [x,y]) and the
    .skinchar CSS. Returns (chars_path, png_name) or (None, None) if no font."""
    if not skin.has("text.bmp"):
        return None, None
    png_name = "text.png"
    _font_to_transparent(skin.open_image("text.bmp")).save(os.path.join(out_dir, png_name))

    chars = {}
    for char, (row, col) in wa.FONT_LOOKUP.items():
        x = col * wa.CHAR_W
        y = row * wa.CHAR_H
        # Winamp's font glyphs are uppercase; store letters under upper key so
        # the skintext filter (which uppercases input) finds them.
        key = char.upper() if char.isalpha() else char
        chars[key] = [x, y]

    chars_path = os.path.join(out_dir, "chars.json")
    with open(chars_path, "w") as f:
        json.dump(chars, f, ensure_ascii=False, indent=0, sort_keys=True)

    # Append the .skinchar rule to skin-sprites.css (single stylesheet to link).
    with open(os.path.join(out_dir, "skin-sprites.css"), "a") as f:
        f.write(
            "\n/* ---- bitmap font (text.png), %dx%d cells ---- */\n"
            ".skinchar { display:inline-block; width:%dpx; height:%dpx;\n"
            "  background-image:url(%s); image-rendering:pixelated;\n"
            "  background-repeat:no-repeat; vertical-align:baseline; }\n"
            % (wa.CHAR_W, wa.CHAR_H, wa.CHAR_W, wa.CHAR_H, png_name)
        )
    return chars_path, png_name


# =====================================================================
#  preview.html
# =====================================================================
def write_preview(out_dir, skin_name, vars_dict, sheets, font_png, notes, flagged):
    swatches = []
    for k, val in vars_dict.items():
        if k.startswith("--font") or k == "--skin-font":
            continue
        swatches.append(
            "<div class='sw'><span class='chip' style='background:%s'></span>"
            "<code>%s</code><span class='val'>%s</span></div>" % (val, k, val)
        )

    # Sample buttons from whatever transport sprites exist.
    buttons = []
    if "CBUTTONS" in sheets:
        for base, alias in (("MAIN_PREVIOUS_BUTTON", "prev"),
                            ("MAIN_PLAY_BUTTON", "play"),
                            ("MAIN_PAUSE_BUTTON", "pause"),
                            ("MAIN_STOP_BUTTON", "stop"),
                            ("MAIN_NEXT_BUTTON", "next"),
                            ("MAIN_EJECT_BUTTON", "eject")):
            buttons.append("<button class='spr-%s' title='%s (click to see :active)'></button>" % (alias, alias))

    # --- bitmap font (text.png): raw sheet + parsed glyph grid + sample ----
    font_demo = ""
    if font_png:
        with open(os.path.join(out_dir, "chars.json")) as f:
            chars = json.load(f)

        # (a) the raw sheet, magnified and pixel-crisp
        raw_sheet = ("<div class='sheet'><div class='zoom5'>"
                     "<img src='%s' alt='%s'></div> <code>%s</code></div>"
                     % (font_png, font_png, font_png))

        # (b) every parsed glyph cut from the sheet, with its character label
        cells = []
        for ch in sorted(chars, key=lambda c: (chars[c][1], chars[c][0])):
            x, y = chars[ch]
            label = {" ": "spc"}.get(ch, ch)
            cells.append(
                "<figure class='cell'><span class='skinchar' "
                "style='background-position:%s %s'></span>"
                "<figcaption>%s</figcaption></figure>"
                % (_pos(x), _pos(y), _esc(label))
            )
        glyph_grid = "<div class='glyphgrid'>%s</div>" % "".join(cells)

        # (c) a rendered sample string (same offsets the skintext filter uses)
        spans = []
        for ch in "BOTANICAL GARDEN 2026":
            pos = chars.get(ch.upper()) or chars.get(" ")
            if pos:
                spans.append("<span class='skinchar' style='background-position:%s %s'></span>"
                             % (_pos(pos[0]), _pos(pos[1])))
        sample = "<div class='fontrow' style='zoom:3'>%s</div>" % "".join(spans)

        font_demo = (
            "<h2>bitmap font — text.png</h2>"
            "%s"
            "<h3>parsed glyphs (%d cells, %d×%d each)</h3>%s"
            "<h3>sample via the <code>skintext</code> filter</h3>%s"
            % (raw_sheet, len(chars), wa.CHAR_W, wa.CHAR_H, glyph_grid, sample)
        )

    # --- time digits (numbers.png / nums_ex.png): raw sheet + parsed 0-9 ----
    digits_demo = ""
    digit_sheet = "NUMBERS" if "NUMBERS" in sheets else ("NUMS_EX" if "NUMS_EX" in sheets else None)
    if digit_sheet:
        dpng = sheets[digit_sheet]
        suffix = "-ex" if digit_sheet == "NUMS_EX" else ""
        cells = "".join("<span class='spr-digit-%d%s'></span>" % (d, suffix) for d in range(10))
        digits_demo = (
            "<h2>time digits — %s</h2>"
            "<div class='sheet'><div class='zoom5'><img src='%s' alt='%s'></div> <code>%s</code></div>"
            "<h3>parsed DIGIT_0…9 (9×13 each), via <code>.spr-digit-N%s</code></h3>"
            "<div class='digits'>%s</div>"
            % (dpng, dpng, dpng, dpng, suffix, cells)
        )

    note_html = ""
    if notes or flagged:
        items = ["<li>%s</li>" % n for n in notes]
        if flagged:
            items.append("<li>skipped sprites: %s</li>" % ", ".join(flagged))
        note_html = "<h2>notes</h2><ul class='notes'>%s</ul>" % "".join(items)

    # Cache-bust the stylesheet link so re-running the tool against the same
    # --out dir during iteration always shows the freshly written CSS. Without
    # this, the browser reuses the cached skin-sprites.css and silently drops
    # any rules added since (the classic "glyphs are blank" footgun, when the
    # cached copy predates the appended .skinchar rule).
    css_v = int(os.path.getmtime(os.path.join(out_dir, "skin-sprites.css")))

    html = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>skin preview — {name}</title>
<link rel="stylesheet" href="skin-sprites.css?v={cssv}">
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family: system-ui, sans-serif; margin: 0; padding: 24px;
         background: {bg}; color: #111; }}
  h1 {{ margin: 0 0 4px; }} .sub {{ color:#555; margin:0 0 20px; }}
  h2 {{ margin: 28px 0 10px; font-size: 15px; text-transform: uppercase;
       letter-spacing: .08em; color:#444; }}
  h3 {{ margin: 16px 0 6px; font-size: 12px; font-weight: 600; color:#666; }}
  .swatches {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:6px; }}
  .sw {{ display:flex; align-items:center; gap:8px; font-size:13px; }}
  .chip {{ width:26px; height:26px; border:1px solid #0003; border-radius:4px; flex:none; }}
  .sw code {{ flex:none; width:130px; }} .val {{ color:#666; }}
  .buttons {{ display:flex; gap:10px; align-items:center; padding:14px;
             background:#cfd6df; border-radius:6px; width:max-content; zoom:2; }}
  .hint {{ color:#777; font-size:12px; }}
  .notes {{ color:#a23; font-size:13px; }}
  /* raw sprite sheets, magnified & pixel-crisp */
  .sheet {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
  .sheet code {{ font-size:11px; color:#555; }}
  .zoom5 {{ zoom:5; display:inline-block; line-height:0; outline:1px solid #0002; }}
  .zoom5 img {{ image-rendering:pixelated; display:block; }}
  /* parsed glyph grid */
  .glyphgrid {{ display:flex; flex-wrap:wrap; gap:12px 10px; padding:14px;
               background:#cfd6df; border-radius:6px; width:max-content; max-width:100%; }}
  .cell {{ margin:0; text-align:center; }}
  .cell .skinchar {{ zoom:4; outline:1px solid #0002; }}
  .cell figcaption {{ font-family:monospace; font-size:10px; color:#444; margin-top:5px; }}
  .fontrow {{ padding:14px; background:#cfd6df; border-radius:6px; width:max-content; }}
  .digits {{ display:flex; gap:5px; padding:14px; background:#cfd6df;
            border-radius:6px; width:max-content; zoom:3; }}
</style></head>
<body>
  <h1>{name}</h1>
  <p class="sub">generated by import_skin.py — eyeball this before committing</p>

  <h2>palette → CSS variables</h2>
  <div class="swatches">{swatches}</div>

  <h2>transport buttons{btnnote}</h2>
  <div class="buttons">{buttons}</div>
  <p class="hint">click and hold a button to see its pressed (:active) sprite</p>

  {font_demo}
  {digits_demo}
  {notes}
</body></html>
""".format(
        name=skin_name,
        cssv=css_v,
        bg=vars_dict.get("--page-bg-mid", "#ddd"),
        swatches="".join(swatches),
        buttons="".join(buttons) or "<em>no cbuttons.bmp in this skin</em>",
        btnnote="" if buttons else " (none)",
        font_demo=font_demo,
        digits_demo=digits_demo,
        notes=note_html,
    )
    path = os.path.join(out_dir, "preview.html")
    with open(path, "w") as f:
        f.write(html)
    return path


# =====================================================================
#  main
# =====================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(description="Import a Winamp .wsz skin into the theme.")
    ap.add_argument("wsz", help="path to the .wsz skin file")
    ap.add_argument("--out", required=True,
                    help="output dir, e.g. themes/mytheme/static/skins/<name>/")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.wsz):
        sys.exit("No such file: %s" % args.wsz)

    out_dir = args.out
    os.makedirs(out_dir, exist_ok=True)
    skin_name = os.path.basename(os.path.normpath(out_dir)) or "skin"

    skin = Skin(args.wsz)
    print("Importing %s -> %s" % (args.wsz, out_dir))

    # Module 1 — palette
    vars_dict, notes = build_vars(skin)
    p = write_vars_css(vars_dict, notes, out_dir, os.path.basename(args.wsz))
    print("  [1] palette      -> %s (%d vars)" % (p, len(vars_dict)))

    # Module 2 — sprites
    sheets = convert_sheets(skin, out_dir)
    p, flagged = write_sprites_css(skin, out_dir, sheets)
    print("  [2] sprites      -> %s (%d sheets: %s)"
          % (p, len(sheets), ", ".join(sorted(sheets)) or "none"))
    tiles = write_edge_tiles(skin, out_dir)
    if tiles:
        print("  [2b] edge tiles  -> %s" % ", ".join(tiles))

    # Module 3 — bitmap font
    chars_path, font_png = write_font(skin, out_dir)
    if chars_path:
        print("  [3] bitmap font  -> %s + text.png" % chars_path)
    else:
        print("  [3] bitmap font  -> (no text.bmp in skin)")

    # preview
    p = write_preview(out_dir, skin_name, vars_dict, sheets, font_png, notes, flagged)
    print("  [*] preview      -> %s" % p)
    for note in notes:
        print("      note: %s" % note)
    print("Done. Open %s to review." % p)


if __name__ == "__main__":
    main()
