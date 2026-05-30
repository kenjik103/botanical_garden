# Personal Site — Build Plan

A stylized personal website: blog, projects, gallery. A creative playground, not a
corporate portfolio. Visual inspiration is Y2K / Frutiger Aero / Winamp — skinnable
window chrome, bevels, gradients, glossy media-player aesthetics. **"Winamp" refers to
visual style only — there is no audio player.**

The owner is an experienced C++/Python developer comfortable with files and directory
structures, but inexperienced with servers, web frameworks, and JS tooling. The
architecture below deliberately minimizes server/tooling exposure and maximizes the
file-based mental model.

---

## Tech stack

- **Pelican** — Python static site generator. Markdown content, Jinja2 templates,
  Python config. Output is plain static files.
- **Hand-written CSS** — no component library, no CSS framework, no Tailwind. All styling
  is bespoke.
- **Vanilla JS** — only for small visual flourishes (hover FX, optional skin switcher).
  No framework.
- **Cloudflare Pages** — free static hosting, rebuilds and deploys on `git push`.

## Non-goals (do NOT build these)

- No audio player.
- No client-side page-swap / SPA layer (Swup, barba, View Transitions). Standard
  multi-page navigation with full page loads is fine and intended.
- No backend, database, comments, guestbook, or hit counter. The site is 100% static.
- No JS framework (React/Vue/Svelte/etc.) and no Node build pipeline beyond what Pelican
  needs (which is none — Pelican is Python).
- No pre-built theme. Build the theme from scratch.

---

## Directory structure

```
mysite/
├── content/
│   ├── blog/                     # Markdown posts → rendered via article template
│   │   └── 2026-05-30-hello.md
│   ├── pages/                    # Markdown static pages (about, etc.)
│   │   └── about.md
│   ├── projects/                 # Raw HTML, copied VERBATIM (see "Projects" below)
│   │   └── boot-sequence/
│   │       ├── index.html
│   │       ├── style.css
│   │       └── script.js
│   └── images/
│       └── gallery/
├── themes/mytheme/
│   ├── templates/                # Jinja2 (same templating as Flask)
│   │   ├── base.html             # shared chrome: window frame, nav
│   │   ├── index.html
│   │   ├── article.html
│   │   ├── page.html
│   │   └── gallery.html
│   └── static/
│       ├── css/
│       ├── js/
│       ├── fonts/
│       └── img/                  # theme assets: icons, textures, chrome
├── pelicanconf.py                # config
└── output/                       # generated build artifact; gitignore this
```

## How content works

- **Blog**: Markdown files in `content/blog/`. Pelican renders each into the `article.html`
  template and builds an index. Standard, uniform, consistent.
- **Pages**: Markdown in `content/pages/` for things like About, rendered via `page.html`.
- **Projects (passthrough)**: each project is a self-contained folder of raw HTML/CSS/JS
  under `content/projects/`. These are **copied verbatim to the output and bypass
  templating entirely.** Mechanism: list `projects` in Pelican's `STATIC_PATHS` so Pelican
  copies it untouched rather than processing it. Each project is its own isolated world
  and shares nothing with the core site, so it cannot break it.
- **Gallery**: a template that globs `content/images/gallery/` and lays the images out.
  Start with plain `<img>` tags; thumbnail generation can be added later if needed. No
  gallery plugin.

## Theme / styling

- All styling is hand-written CSS in the theme.
- **Drive all colors, gradients, and bevels through CSS custom properties** (`--accent`,
  `--bevel-light`, `--window-bg`, etc.). This is mandatory because it enables the next
  point cheaply.
- **Optional skin switcher**: a small vanilla-JS dropdown that swaps the CSS-variable set,
  i.e. Winamp-style skins. Trivial once the CSS is variable-driven. Nice-to-have, build
  after the core site works.
- `base.html` holds the shared chrome (window frame + nav); every other template
  `{% extends "base.html" %}` and fills in blocks.

## Pelican config levers (pelicanconf.py)

Key settings Claude Code will need to set: `PATH` (content dir), `OUTPUT_PATH`, `THEME`,
`ARTICLE_PATHS = ['blog']`, `PAGE_PATHS = ['pages']`, `STATIC_PATHS = ['images', 'projects']`.
Disable any default pagination/feeds/categories that aren't wanted. Keep the config minimal.

---

## Extensibility model (important)

Future "flare" pages and experiments are added as **new self-contained folders under
`content/projects/`** — each with its own HTML/CSS/JS, fully isolated. To add one: drop the
folder in, link to it from the nav or a project index, done. These never touch the core
theme or each other. Treat the core site (blog/pages/gallery + theme) as stable, and
projects as an open-ended collection of independent experiments.

---

## Build order (milestones)

1. **Scaffold + loop working.** Install Pelican, create a minimal theme (`base.html`,
   `index.html`, `article.html` only), one test post. Confirm `pelican --listen` serves a
   working local preview. Get the build loop working before any styling.
2. **Deploy FIRST, while nearly empty.** Push the repo to GitHub, connect Cloudflare Pages,
   confirm a near-empty site is live on every push. Solve the unfamiliar systems/deploy
   step while the stakes are zero — do not leave this for the end.
3. **Core shell + theme.** Build the persistent chrome (window frame, nav), the Y2K /
   Frutiger / Winamp CSS, and CSS custom properties for theming.
4. **Content sections.** Blog (Markdown), gallery template, and the `projects/` passthrough
   mechanism (verify a raw HTML project folder copies through untouched).
5. **Polish.** Fonts, hover FX, favicons, About page, and the optional skin switcher.

## Local workflow

- Edit content as files; run `pelican --listen` for live local preview.
- Commit and push; Cloudflare Pages rebuilds and publishes automatically.
- Never SSH into anything. There is no server to manage.
