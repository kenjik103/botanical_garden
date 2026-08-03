"""Pelican configuration. Keep this minimal — see PLAN.md."""

import os
import time
from glob import glob as _glob

# Changes every build; appended as ?v=… to CSS links so browsers never serve
# a stale stylesheet against freshly-changed markup (see base.html).
CACHE_BUST = int(time.time())


def _gallery_images():
    """Images in content/images/gallery/, sorted, as {name, width, height}.

    Exposed to templates via JINJA_GLOBALS so gallery.html can glob the
    folder at build time without a plugin (see PLAN.md "Gallery").

    Pixel dimensions come from the file header (Pillow, already required by
    import_skin.py). The gallery collage lazy-loads below-the-fold photos, and
    a lazy <img> with no known size is 0px tall until it loads — in a
    multi-column masonry that makes the whole layout reshuffle as you scroll.
    Emitting width/height lets the browser reserve the right box up front.
    width/height are None for formats Pillow can't read (e.g. .svg); the
    template just omits the attributes then.
    """
    base = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "content", "images", "gallery",
    )
    exts = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
    paths = sorted(
        p for p in _glob(os.path.join(base, "*"))
        if p.lower().endswith(exts)
    )

    try:
        from PIL import Image
    except ImportError:
        Image = None

    out = []
    for p in paths:
        w = h = None
        if Image is not None:
            try:
                with Image.open(p) as im:
                    w, h = im.size
            except Exception:
                pass
        out.append({"name": os.path.basename(p), "width": w, "height": h})
    return out


def _available_skins():
    """Folder names under themes/mytheme/static/skins/, sorted.

    Exposed to templates via JINJA_GLOBALS so base.html can hand the full
    list to the client-side skin switcher (the homepage +FILE/-FILE buttons
    cycle through it) without hand-maintaining a separate list here.
    """
    base = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "themes", "mytheme", "static", "skins",
    )
    names = (
        n for n in os.listdir(base)
        if os.path.isfile(os.path.join(base, n, "skin-vars.css"))
    ) if os.path.isdir(base) else ()
    return sorted(names)


def _bg_for(stem):
    """Resolve a page background by filename STEM, returning the actual file
    (with extension) in content/images/backgrounds/, or "" if none exists.

    Lets a template say bg_for('home') and pick up home.gif / home.jpg / home.png
    interchangeably — drop in whatever extension you like, no template edit. If
    several extensions match, the first by _BG_EXTS order wins. Used for the
    named-default pages (home/blog/gallery); per-post/page `Background:` metadata
    stays an explicit filename.
    """
    base = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "content", "images", "backgrounds",
    )
    for ext in _BG_EXTS:
        if os.path.isfile(os.path.join(base, stem + ext)):
            return stem + ext
    return ""


_BG_EXTS = (".gif", ".png", ".jpg", ".jpeg", ".webp", ".svg")


def _asset_version(relpath):
    """Cache-bust token for a static asset, from its mtime under content/.

    The global CACHE_BUST is one timestamp fixed per build process, so a file
    swapped in under the SAME name (e.g. replacing a page background) produces
    an identical URL and the browser keeps its cached copy. Keying off the
    file's mtime means a swap changes the ?v= token on the next build, forcing
    a refetch. Falls back to CACHE_BUST when the file is missing so the URL is
    always valid (templates never break).
    """
    p = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "content", relpath.lstrip("/"),
    )
    try:
        return int(os.path.getmtime(p))
    except OSError:
        return CACHE_BUST


AUTHOR = "Kenjiro"
SITENAME = "kenjiro's botanical garden"
SITEURL = ""  # empty for local dev; set per-environment at publish time

# --- Paths -------------------------------------------------------------------
PATH = "content"            # where the source content lives
OUTPUT_PATH = "output"      # generated build artifact (gitignored)
THEME = "themes/mytheme"

ARTICLE_PATHS = ["blog"]            # Markdown posts → article.html
PAGE_PATHS = ["pages"]              # Markdown pages → page.html
STATIC_PATHS = ["images", "projects", "music"]  # copied VERBATIM, no templating

TIMEZONE = "America/New_York"
DEFAULT_LANG = "en"
DEFAULT_DATE_FORMAT = "%Y-%m-%d"

# --- Turn off machinery we don't want ---------------------------------------
# No feeds during local development.
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# No pagination yet — one flat index.
DEFAULT_PAGINATION = False

# "index" → the home page (the Winamp clone). "blog" → the post-listing
# page at /blog/ (its template gets the global `articles` context).
DIRECT_TEMPLATES = ["index", "blog"]
BLOG_SAVE_AS = "blog/index.html"
BLOG_URL = "blog/"
AUTHOR_SAVE_AS = ""
AUTHORS_SAVE_AS = ""
CATEGORY_SAVE_AS = ""
CATEGORIES_SAVE_AS = ""
TAG_SAVE_AS = ""
TAGS_SAVE_AS = ""
ARCHIVES_SAVE_AS = ""

# Clean-ish URLs for articles: /blog/<slug>/
ARTICLE_URL = "blog/{slug}/"
ARTICLE_SAVE_AS = "blog/{slug}/index.html"
PAGE_URL = "{slug}/"
PAGE_SAVE_AS = "{slug}/index.html"

# Relative URLs make the local --listen preview work without SITEURL.
RELATIVE_URLS = True

# Expose the gallery glob to templates (see gallery.html).
JINJA_GLOBALS = {
    "gallery_images": _gallery_images,
    "cache_bust": CACHE_BUST,
    "asset_version": _asset_version,
    "bg_for": _bg_for,
    "available_skins": _available_skins,
}

# --- Skins (see SKIN_IMPORT.md) ---------------------------------------------
# Skins are generated by import_skin.py into themes/mytheme/static/skins/<name>/.
# Set ACTIVE_SKIN to a folder name to re-skin the whole site; leave it "" to use
# the theme's built-in "aero" palette. base.html links the skin's CSS when set,
# and the `skintext` filter renders headings in the skin's bitmap font.
ACTIVE_SKIN = "blame-wired"  # e.g. "necromech" or "blame-wired"; "" = built-in aero


def _skintext_filter():
    """Build the `skintext` Jinja filter: turn a string into a row of bitmap-
    font glyph spans, using the active skin's chars.json offsets into text.png.

    Falls back to returning the plain string unchanged when no skin is active
    or the skin has no bitmap font, so templates never break.
    """
    import json
    from markupsafe import Markup, escape

    chars = None
    if ACTIVE_SKIN:
        cj = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "themes", "mytheme", "static", "skins", ACTIVE_SKIN, "chars.json",
        )
        if os.path.isfile(cj):
            with open(cj, encoding="utf-8") as fh:
                chars = json.load(fh)

    def skintext(text):
        text = "" if text is None else str(text)
        if not chars:
            return escape(text)  # no bitmap font available; render as plain text
        spans = []
        for ch in text.upper():
            pos = chars.get(ch) or chars.get(" ")
            if pos is None:
                continue
            x = "0" if pos[0] == 0 else "-%dpx" % pos[0]
            y = "0" if pos[1] == 0 else "-%dpx" % pos[1]
            spans.append(
                "<span class=\"skinchar\" style=\"background-position:%s %s\"></span>" % (x, y)
            )
        return Markup("<span class=\"skintext\" role=\"img\" aria-label=\"%s\">%s</span>"
                      % (escape(text), "".join(spans)))

    return skintext


JINJA_FILTERS = {"skintext": _skintext_filter()}


# --- Homepage audio player: music manifest (see PLAYER.md) -------------------
# content/music/ is copied verbatim (STATIC_PATHS). After each build we scan it
# and write output/music.json — the ordered track list the player fetches. The
# directory is the source of truth: drop in an audio file, rebuild, it appears.
_AUDIO_EXTS = (".mp3", ".ogg", ".oga", ".m4a", ".opus", ".aac", ".flac", ".wav")


def _title_from_filename(name):
    """Readable title from a filename stem: drop a leading "NN " or "NN_" track
    number, swap _/- for spaces, collapse whitespace."""
    import re
    stem = os.path.splitext(name)[0]
    stem = re.sub(r"^\s*\d+\s*[-_.]\s*", "", stem)  # strip leading "01 - "
    stem = re.sub(r"[_-]+", " ", stem).strip()
    return re.sub(r"\s+", " ", stem) or os.path.splitext(name)[0]


def _fmt_len(seconds):
    """Seconds -> "m:ss" (Webamp-style); "" if unknown."""
    if not seconds or seconds <= 0:
        return ""
    s = int(round(seconds))
    return "%d:%02d" % (s // 60, s % 60)


def _track_meta(path, name):
    """(title, artist, length) for one audio file. Pulls title/artist/length
    from ID3/Vorbis tags via mutagen when available; falls back to the filename
    for the title (artist/length stay empty). Tags are optional (PLAYER.md)."""
    title = artist = None
    length = None
    try:
        import mutagen
        mf = mutagen.File(path, easy=True)
        if mf is not None:
            if mf.tags:
                title = (mf.tags.get("title") or [None])[0]
                artist = (mf.tags.get("artist") or [None])[0]
            if mf.info:
                length = mf.info.length
    except Exception:
        pass  # no mutagen, or unreadable tags — fall back to the filename
    return (title or _title_from_filename(name)), (artist or ""), _fmt_len(length)


def _write_music_manifest(pelican):
    """`finalized` signal handler: scan content/music/ and emit music.json.
    The directory is the source of truth (drop a file in, rebuild, it appears);
    metadata comes from the file's tags — do NOT hand-edit music.json."""
    import json
    src = os.path.join(pelican.settings["PATH"], "music")
    out = pelican.settings["OUTPUT_PATH"]
    tracks = []
    if os.path.isdir(src):
        for name in sorted(os.listdir(src)):
            if name.lower().endswith(_AUDIO_EXTS):
                title, artist, length = _track_meta(os.path.join(src, name), name)
                tracks.append({"file": "music/" + name, "title": title,
                               "artist": artist, "length": length})
    with open(os.path.join(out, "music.json"), "w", encoding="utf-8") as fh:
        json.dump(tracks, fh, ensure_ascii=False, indent=2)
    print("  [music] %d track(s) -> music.json" % len(tracks))


# --- Skin auto-import (see SKIN_IMPORT.md) -----------------------------------
# Drop a .wsz into skins/ (repo root) and the next build imports it: no manual
# `python import_skin.py ...` invocation needed. Mirrors the music.json
# pattern above — the folder is the source of truth.
_SKINS_SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skins")
_SKINS_OUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "themes", "mytheme", "static", "skins",
)


def _skin_slug(wsz_filename):
    """".wsz filename -> URL-safe folder slug, e.g. "Blame - Wired.wsz" ->
    "blame-wired", "Persona.wsz" -> "persona"."""
    import re
    stem = os.path.splitext(wsz_filename)[0]
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-") or "skin"


def _relocate_stray_wsz():
    """.wsz files sometimes get dropped directly into themes/mytheme/static/
    skins/ (the generated-output folder) instead of skins/ (the source
    folder) — an easy mix-up since both live under a folder someone might
    call "the theme folder". Move any found there into skins/ before the
    import scan below, so they get picked up the same as a properly-placed
    one, and the output folder goes back to holding only generated
    subfolders. Skips (and warns about) a name collision rather than
    overwriting an existing source file."""
    import shutil
    if not os.path.isdir(_SKINS_OUT_DIR):
        return
    os.makedirs(_SKINS_SRC_DIR, exist_ok=True)
    for name in sorted(os.listdir(_SKINS_OUT_DIR)):
        src = os.path.join(_SKINS_OUT_DIR, name)
        if not (name.lower().endswith(".wsz") and os.path.isfile(src)):
            continue
        dest = os.path.join(_SKINS_SRC_DIR, name)
        if os.path.exists(dest):
            print("  [skins] %s already exists in skins/, leaving the copy in "
                  "themes/mytheme/static/skins/ alone" % name)
            continue
        shutil.move(src, dest)
        print("  [skins] moved %s -> skins/ (that's the source folder; "
              "themes/mytheme/static/skins/ only holds generated output)" % name)


def _sync_skins(pelican=None):
    """`initialized` signal handler: for every skins/*.wsz, (re)generate its
    theme assets via import_skin.py's pipeline if missing or stale (the .wsz
    is newer than its generated skin-vars.css). Runs before generation, so
    available_skins() and ACTIVE_SKIN both see freshly-imported folders.
    A skin that fails to import is skipped (and its partial output removed)
    rather than aborting the whole build — one bad .wsz shouldn't block it."""
    import shutil
    import sys

    _relocate_stray_wsz()
    if not os.path.isdir(_SKINS_SRC_DIR):
        return
    root = os.path.dirname(os.path.abspath(__file__))
    if root not in sys.path:
        sys.path.insert(0, root)
    import import_skin

    for name in sorted(os.listdir(_SKINS_SRC_DIR)):
        if not name.lower().endswith(".wsz"):
            continue
        wsz_path = os.path.join(_SKINS_SRC_DIR, name)
        out_dir = os.path.join(_SKINS_OUT_DIR, _skin_slug(name))
        marker = os.path.join(out_dir, "skin-vars.css")
        if os.path.isfile(marker) and os.path.getmtime(marker) >= os.path.getmtime(wsz_path):
            continue  # already up to date
        try:
            import_skin.main([wsz_path, "--out", out_dir])
        except SystemExit:
            pass  # import_skin already printed why
        except Exception as e:
            print("  [skins] failed to import %s: %s" % (name, e))
            shutil.rmtree(out_dir, ignore_errors=True)  # don't leave a half-built skin


def _write_skins_manifest(pelican):
    """`finalized` signal handler: emit output/skins.json — the raw
    content/projects/ pages aren't templated (see CLAUDE.md) so they can't
    call available_skins() directly; skin-project.js fetches this instead."""
    import json
    out = pelican.settings["OUTPUT_PATH"]
    with open(os.path.join(out, "skins.json"), "w", encoding="utf-8") as fh:
        json.dump(_available_skins(), fh)
    print("  [skins] %d skin(s) -> skins.json" % len(_available_skins()))


# Wire the hooks at config-load time (Pelican executes this file at startup).
from pelican import signals as _signals  # noqa: E402
_signals.initialized.connect(_sync_skins)
_signals.finalized.connect(_write_music_manifest)
_signals.finalized.connect(_write_skins_manifest)
