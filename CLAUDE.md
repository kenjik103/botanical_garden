# CLAUDE.md

Project memory for Claude Code. Read this first every session.

## What this is

A stylized personal website (blog, projects, gallery) built as a static site. Visual
inspiration: Y2K / Frutiger Aero / Winamp — skinnable window chrome, bevels, gradients,
glossy media-player look. It's a creative playground, not a corporate portfolio.

## Source of truth

**`PLAN.md` is the authoritative spec.** Read it before starting work. This file is a
quick-reference summary; when they disagree, PLAN.md wins. If something is ambiguous, ask
rather than guess.

## Stack

- **Pelican** (Python static site generator): Markdown content, Jinja2 templates, Python
  config (`pelicanconf.py`).
- **Hand-written CSS** in `themes/mytheme/`. No CSS framework, no component library.
- **Vanilla JS** only — for small visual flourishes and the homepage audio player. No
  framework, no Node build step.
- **Cloudflare Pages** for hosting; deploys on `git push`.

## Hard constraints — do NOT do these

- No site-wide / persistent audio, and no SPA / client-side page-swap layer (Swup, barba,
  View Transitions). Plain multi-page navigation with full page loads is intended. A
  **homepage-only** audio player IS in scope (see PLAYER.md). Music persists across the site
  only because subpages open in new tabs (leaving the homepage tab playing) — never via an
  SPA layer or by trying to keep `<audio>` alive across navigation.
- No backend, database, comments, guestbook, or hit counter. The site is 100% static.
- No JS framework (React/Vue/Svelte) and no Node build pipeline.
- No pre-built theme and no CSS framework. Build the theme from scratch.
- Do not over-engineer. Prefer the simplest thing that works. Do not add plugins,
  abstractions, or tooling that PLAN.md does not call for.

## Conventions

- Content is files: `content/blog/` (Markdown posts), `content/pages/` (Markdown pages),
  `content/projects/` (raw HTML folders copied **verbatim** via `STATIC_PATHS`),
  `content/images/`, and `content/music/` (audio files copied verbatim via `STATIC_PATHS`;
  a build step scans it and emits `music.json` for the player).
- Each item in `content/projects/` is a self-contained HTML/CSS/JS world that shares
  nothing with the core theme. Adding one must never require touching the core site.
- All theme colors/gradients/bevels go through **CSS custom properties** — this is required
  so a skin switcher can swap variable sets later.
- `themes/mytheme/templates/base.html` holds shared chrome; other templates extend it.
- `output/` is generated — keep it gitignored, never edit it by hand.

## Commands

- Local preview with live reload: `pelican --listen`
- One-off build: `pelican content`
- Deploy: commit and `git push`; Cloudflare Pages rebuilds automatically. There is no
  server to manage and nothing to SSH into.

## Current status

Core site is scaffolded, deployed to Cloudflare Pages, and the skin-import palette step
works (the site recolors from a `.wsz`). Current phase: the Winamp-layout refactor
(`REFACTOR.md`) and the homepage audio player (`PLAYER.md`). Prerequisite for the refactor's
sprite work: finish Module 2 of `SKIN_IMPORT.md` (generate `skin-sprites.css`) before
positioning any sprites — you cannot place sprites that aren't sliced yet.

## Owner context

Experienced C++/Python developer; very comfortable with files, directory structures, and
reading code. Inexperienced with servers, web frameworks, and JS tooling. When a step
touches deployment, hosting, or web/systems concepts, explain what's happening and why
rather than just running it. Default to file-based, transparent approaches over magic.
