"""Pelican configuration. Keep this minimal — see PLAN.md."""

import os
from glob import glob as _glob


def _gallery_images():
    """List image filenames in content/images/gallery/, sorted.

    Exposed to templates via JINJA_GLOBALS so gallery.html can glob the
    folder at build time without a plugin (see PLAN.md "Gallery").
    """
    base = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "content", "images", "gallery",
    )
    exts = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
    names = (os.path.basename(p) for p in _glob(os.path.join(base, "*")))
    return sorted(n for n in names if n.lower().endswith(exts))


AUTHOR = "Kenjiro"
SITENAME = "botanical garden"
SITEURL = ""  # empty for local dev; set per-environment at publish time

# --- Paths -------------------------------------------------------------------
PATH = "content"            # where the source content lives
OUTPUT_PATH = "output"      # generated build artifact (gitignored)
THEME = "themes/mytheme"

ARTICLE_PATHS = ["blog"]            # Markdown posts → article.html
PAGE_PATHS = ["pages"]              # Markdown pages → page.html
STATIC_PATHS = ["images", "projects"]  # copied VERBATIM, no templating

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

# Don't generate author/category/tag listing pages we aren't linking to.
DIRECT_TEMPLATES = ["index"]
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
JINJA_GLOBALS = {"gallery_images": _gallery_images}
