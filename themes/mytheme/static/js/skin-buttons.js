/* Homepage-only: the playlist's "+FILE"/"-FILE" buttons (already painted
 * into the bottom-corner sprite art — see .pl-skin-btn in index.html) double
 * as a skin cycler. Clicking one stores the next/previous skin folder name
 * in localStorage and reloads: a normal full page load, same as any other
 * navigation on this site (see PLAYER.md/CLAUDE.md — no SPA layer). The
 * reload lets base.html's skin bootstrap + skin-fixup.js (which run on every
 * page) apply the choice consistently, instead of duplicating that logic
 * here for a live in-place swap.
 */
(function () {
  var skins = window.__SKINS__ || [];
  if (skins.length < 2) return; // nothing to cycle between

  function switchSkin(delta) {
    var i = skins.indexOf(window.__ACTIVE_SKIN__);
    if (i === -1) i = 0;
    var next = skins[(i + delta + skins.length) % skins.length];
    try { localStorage.setItem("wa-skin", next); } catch (e) {}
    location.reload();
  }

  var prev = document.querySelector('[data-skin-cycle="prev"]');
  var next = document.querySelector('[data-skin-cycle="next"]');
  if (prev) prev.addEventListener("click", function () { switchSkin(-1); });
  if (next) next.addEventListener("click", function () { switchSkin(1); });
})();
