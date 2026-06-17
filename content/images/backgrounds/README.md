# Page backgrounds

Drop static images / GIFs here. They're copied verbatim to the build
(`content/images/` is a `STATIC_PATH`) and served at `/images/backgrounds/<file>`.

Each background fully covers the viewport as a **fixed** backdrop, layered over
the skin gradient. If the file is missing or partly transparent, the gradient
shows through — so a missing image degrades gracefully, it never breaks a page.

## How a page picks its background

- **Blog posts** (`content/blog/*.md`): add a front-matter line
  `Background: my-post.gif`. Per-post, optional.
- **Pages** (`content/pages/*.md`): same — `Background: about.gif`.
- **Blog index** (`/blog/`): looks for `blog.gif` (edit the `bg_image` block in
  `themes/mytheme/templates/blog.html` to rename or disable).
- **Gallery**: front-matter `Background:` on the gallery page, else `gallery.gif`.
- **Home**: no background by default — set one in the `bg_image` block in
  `templates/index.html` (e.g. `home.gif`).

Any image extension works (`.png`, `.jpg`, `.gif`, `.webp`, `.svg`) — just match
the filename you reference. Filenames are case-sensitive on the server.
