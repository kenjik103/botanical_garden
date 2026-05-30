# Winamp-Layout Refactor — Spec & Claude Code Workflow

Refactor the site so it reads as a Winamp player: title-bar chrome, sprite buttons, and a
"playlist" panel whose rows are site links instead of tracks.

## What this doc assumes

The **Winamp-inspired, build-from-sprite-CSS** path: your own page layout, rendered with the
sprite classes from `skin-sprites.css`, no JS framework, full creative control. NOT a
pixel-exact clone of Winamp's 275px window, and NOT embedding Webamp. If you change your
mind toward either of those, this plan does not apply.

## Terminology (read this first)

A **"window"** here means a reusable Winamp-style visual *panel* — title-bar sprite chrome
across the top, sprite buttons, content region below. It is NOT a browser window and NOT a
draggable desktop window. It's a CSS/HTML component you build once and reuse.

The site stays **multi-page**: Blog, Projects, Gallery, etc. are each their own page with
their own URL (`/blog/`, `/projects/`, …), exactly as in PLAN.md. We are not putting every
section on one mega-page. A page is built out of one or more of these panel components.

## How the shared chrome works (Jinja2 inheritance)

The **main player window is shared chrome**: written once in `themes/mytheme/templates/
base.html`, and every page reuses it via Jinja2 template inheritance.

`base.html` holds the main window markup and leaves a named hole:

```html
<!-- base.html -->
<div class="winamp-main-window">
  <div class="titlebar"><!-- sprite chrome --></div>
  <nav><!-- transport-button links to section pages --></nav>
</div>
<main>
  {% block content %}{% endblock %}   <!-- the hole -->
</main>
```

Each section page extends it and fills only the hole:

```html
<!-- a section page template -->
{% extends "base.html" %}
{% block content %}
  <!-- this page's panel(s) -->
{% endblock %}
```

At build time Pelican stitches these together and writes one self-contained static HTML
file per page, each physically containing the main window chrome plus that page's content.
"Inherited" describes how it's *authored* (defined once, reused) — there is no runtime
sharing. The payoff: the main window lives in exactly ONE file; change a sprite or nav link
there and it updates across every page on the next build.

**Hard rule for Claude Code:** the main window chrome lives only in `base.html` and is
pulled in via `{% extends %}`. It must never be pasted into individual page templates.
Section pages own only their `content` block.

## Prerequisite (do this FIRST)

The sprite stylesheet must exist. You can't place sprites that aren't sliced yet. Before any
layout work:
1. Finish Module 2 of `SKIN_IMPORT.md` — lift the Webamp coordinate map, generate
   `skin-sprites.css` and the PNG sheets.
2. Render a couple of sprites in a throwaway page and confirm they look right (the
   `cbuttons.bmp` 23×18 buttons are the test case).
Only then start the refactor below.

## Semantic mapping (Winamp control → site function)

This is the part Claude Code cannot guess — it's your information architecture. Decide it
explicitly and hand it over. A starting proposal:

- **Main window** (shared chrome in `base.html`) → site identity + primary nav. The transport
  buttons are links to your section pages: e.g. play → Blog, next/prev → cycle sections,
  eject → external links, stop → Home.
- **Playlist panel** → a link list. Rows are pages/posts (the literal "playlists swapped for
  site links" idea). Used most obviously on the Blog index, where each row links to a post.
- **Equalizer panel** → a fun secondary component: skin switcher, theme toggles, or an
  "about/now-playing" blurb styled as EQ sliders.
- **Section pages** → Projects, Gallery, About — each its own page, each dropping an
  appropriate panel into its content block.

Adjust to taste, but pin it down before building. The buttons must *do* something coherent.

## Layout model

- **Main window** = shared chrome in `base.html` (see above), present on every page.
- **Panels** (playlist, EQ, etc.) = reusable component templates. Build a panel once and
  reuse it across whichever pages need that look. In Jinja2, factor a panel into a partial
  template and `{% include %}` it, or a macro, so it isn't restated per page.
- **Each section is a page** that `{% extends "base.html" %}` and fills its `content` block
  with the relevant panel(s).

Decisions to make up front:
- **Fixed-width vs responsive.** A fixed-width, desktop-only layout is period-accurate and
  far simpler to make pixel-tidy. Choose deliberately (see PLAN.md note on this).
- **Static panels vs draggable windows.** Static is simple and fine. Draggable/resizable
  windows look great but require real vanilla JS and are where scope explodes — treat as
  optional later polish, not part of the core refactor.

## Build order — ONE unit per Claude Code session

A "unit" is the shared chrome, a reusable panel, or a single page — not the whole player.

1. **Main window chrome in `base.html`** — frame + title-bar sprites + transport-button
   links to the section pages. Get this pixel-tidy first; every page inherits it and it sets
   the visual language.
2. **Playlist panel** as a reusable partial, wired up on the Blog index page. This is the
   heart of the concept.
3. **Remaining section pages** — Projects, Gallery, About — one page per session, each
   extending `base.html` and dropping in its panel.
4. **Skin switcher wiring** — point the active-skin variable at different generated folders.
5. **(Optional) window dragging** — small vanilla JS, only if you want it. Adds JS; keep it
   isolated and optional.

Each step is a separate session. Do not ask for the whole player in one prompt.

## How to direct Claude Code

- **Point it at docs, not chat fragments.** Each session: "Read CLAUDE.md, this file, and
  `skin-sprites.css`. We're doing step N: <the one unit>." Let the spec carry the context.
- **One unit per session.** Finish and verify before starting the next. A fresh session per
  unit keeps its context focused.
- **Give it the reference for that unit.** Drop the relevant Winamp screenshot / skin region
  so it knows the target.
- **Hand over the semantic mapping.** It can't invent your IA; tell it which control is which
  link.
- **Enforce the shared-chrome rule.** Main window in `base.html` only, pulled in via
  `{% extends %}`; never duplicated into page templates. Reusable panels go in partials/macros.
- **You are the visual verifier.** Claude Code cannot see the rendered page. The loop is:
  CC implements → you open it in the browser + DevTools → you give specific corrections
  ("the play button is 3px too low; the title bar sprite is the wrong offset"). Iterate in
  DevTools (instant) and have CC commit the values that work.
- **Keep the constraints loud.** Restate: no JS framework, no CSS framework, use the existing
  sprite classes, plain multi-page navigation. CC will otherwise reach for React or a UI lib
  when layout gets fiddly.

## Caveats

- **Fake transparency.** Sprites drawn to sit on `main.bmp` may fringe on a mismatched
  background. Build each panel's background to match the skin's chrome color (you have it
  from the palette extractor) so the sprites blend.
- **Fidelity bar.** Decide how close to "exact" you actually need. Inspired-but-clean beats a
  half-finished pixel-perfect clone. Don't chase the last pixel on every sprite.
- **Scope discipline.** Window dragging, animated transitions, multi-window focus management —
  all tempting, all JS, all optional. Ship the static version first.
