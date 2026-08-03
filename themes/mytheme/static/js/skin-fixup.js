/* Applies a stored skin override (chosen via the homepage +FILE/-FILE
 * buttons, see skin-buttons.js) to the handful of things the <head>
 * stylesheet swap in base.html can't reach, because they're absolute
 * urls baked into inline styles/attributes at build time rather than
 * CSS-class lookups: the window-frame tiles, the homepage's main.png and
 * playlist tiles, and the bitmap-font headers (whose glyph positions come
 * from the OLD skin's chars.json and would otherwise misread against the
 * new skin's text.png). No-op when the visitor hasn't picked an override —
 * the common case, and the only one when only one skin exists.
 */
(function () {
  var active = window.__ACTIVE_SKIN__;
  var server = window.__SERVER_SKIN__;
  if (!active || !server || active === server) return;

  var oldBase = window.__SITEURL__ + "/theme/skins/" + server;
  var newBase = window.__SITEURL__ + "/theme/skins/" + active;

  document.querySelectorAll('[style*="' + oldBase + '"]').forEach(function (el) {
    el.setAttribute("style", el.getAttribute("style").split(oldBase).join(newBase));
  });

  var marquee = document.querySelector(".wa-marquee[data-chars]");
  if (marquee) marquee.dataset.chars = marquee.dataset.chars.split(oldBase).join(newBase);

  var texts = document.querySelectorAll(".skintext[aria-label]");
  if (!texts.length) return;
  fetch(newBase + "/chars.json")
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (chars) {
      if (!chars) return;
      texts.forEach(function (el) {
        el.textContent = "";
        el.appendChild(window.SkinGlyphs(el.getAttribute("aria-label"), chars));
      });
    })
    .catch(function () {});
})();
