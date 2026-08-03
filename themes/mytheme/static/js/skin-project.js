/* Skin-switcher bootstrap for content/projects/ pages.
 *
 * Projects are raw, verbatim HTML (see CLAUDE.md) — no Jinja, so they can't
 * call available_skins()/ACTIVE_SKIN like base.html does. A project that
 * wants to follow the site-wide skin choice (see the homepage +FILE/-FILE
 * buttons) just adds one script tag, non-deferred, right after its
 * skin-vars.css <link id="skin-vars-link">:
 *
 *   <script src="../../theme/js/skin-project.js"></script>
 *
 * No per-project config: the site root is derived from this script's own
 * src (same relative depth already used for its other theme links), and the
 * skin list comes from output/skins.json (see _write_skins_manifest in
 * pelicanconf.py) — regenerated every build from themes/mytheme/static/
 * skins/, so a new skin (dropped as a .wsz into skins/, see _sync_skins)
 * reaches every project page automatically, no edits here.
 *
 * Runs synchronously (not deferred) so it swaps the stylesheet href before
 * the browser paints, same as base.html's bootstrap; the skins.json fetch is
 * a blocking XHR for the same reason (it's a few dozen bytes). Sets the same
 * window.__SKINS__/__SERVER_SKIN__/__ACTIVE_SKIN__/__SITEURL__ globals, so
 * the shared skin-fixup.js (which patches inline sprite urls) works
 * unmodified here too.
 */
(function () {
  var script = document.currentScript;
  var varsLink = document.getElementById("skin-vars-link");
  if (!varsLink) return;

  var scriptSrc = script.getAttribute("src") || "";
  var siteRoot = scriptSrc.replace(/\/?theme\/js\/skin-project\.js.*$/, "") || ".";

  var skins = [];
  try {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", siteRoot + "/skins.json", false); // sync: tiny file, must resolve before paint
    xhr.send(null);
    if (xhr.status === 200) skins = JSON.parse(xhr.responseText);
  } catch (e) {}
  if (!skins.length) return;

  var m = varsLink.getAttribute("href").match(/\/theme\/skins\/([^\/]+)\/skin-vars\.css/);
  var serverSkin = m ? m[1] : skins[0];

  var stored = null;
  try { stored = localStorage.getItem("wa-skin"); } catch (e) {}
  var active = (stored && skins.indexOf(stored) !== -1) ? stored : serverSkin;

  window.__SKINS__ = skins;
  window.__SERVER_SKIN__ = serverSkin;
  window.__ACTIVE_SKIN__ = active;
  window.__SITEURL__ = siteRoot;

  if (active !== serverSkin) {
    var newBase = siteRoot + "/theme/skins/" + active;
    varsLink.href = newBase + "/skin-vars.css";
    var spritesLink = document.getElementById("skin-sprites-link");
    if (spritesLink) spritesLink.href = newBase + "/skin-sprites.css";
  }
})();
