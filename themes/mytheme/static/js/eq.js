/* Winamp equalizer: 11 independent vertical slider thumbs (preamp + 10
 * bands) and the ON/AUTO toggle buttons. Visual/interactive only — nothing
 * here processes real audio; it's the classic skin's EQ chrome kept as a
 * fully-slideable toy, the same way the transport buttons are real controls
 * but the window-chrome buttons above them are just decorative.
 *
 * Coordinate note (mirrors playlist-scroll.js): the player sits inside a
 * `zoom`ed ancestor, so pointer positions (painted px) and the thumb's
 * `top` (layout px) live in different spaces and are never mixed directly.
 * TOP_MIN/TOP_MAX/WINDOW_H below match the constants documented in
 * style.css's .winamp-eq comment — change one, change the other. Drag math
 * converts the pointer position into layout px using the window's own
 * painted height as the zoom scale factor, so it works at any --wa-scale.
 */
(function () {
  var TOP_MIN = 38, TOP_MAX = 90, THUMB_H = 11, WINDOW_H = 116;

  function valueFor(ratio) {
    return Math.round((12 - ratio * 24) * 10) / 10; // +12dB..-12dB
  }

  function setRatio(thumb, ratio) {
    ratio = Math.max(0, Math.min(1, ratio));
    thumb.style.top = Math.round(TOP_MIN + ratio * (TOP_MAX - TOP_MIN)) + "px";
    thumb.setAttribute("aria-valuenow", String(valueFor(ratio)));
  }

  function ratioOf(thumb) {
    var top = parseFloat(thumb.style.top);
    if (isNaN(top)) top = (TOP_MIN + TOP_MAX) / 2; // matches the CSS default (0dB)
    return (top - TOP_MIN) / (TOP_MAX - TOP_MIN);
  }

  function setupPanel(panel) {
    panel.querySelectorAll(".wa-eq-thumb").forEach(function (thumb) {
      var dragging = false;

      function ratioFromPointer(e) {
        var panelRect = panel.getBoundingClientRect();
        var scale = panelRect.height / WINDOW_H; // painted px per layout px
        var layoutY = (e.clientY - panelRect.top) / scale; // pointer, in layout px
        var top = layoutY - THUMB_H / 2; // pointer marks the thumb's center
        return (top - TOP_MIN) / (TOP_MAX - TOP_MIN);
      }

      thumb.addEventListener("pointerdown", function (e) {
        dragging = true;
        thumb.setPointerCapture(e.pointerId);
        setRatio(thumb, ratioFromPointer(e));
        e.preventDefault();
      });
      thumb.addEventListener("pointermove", function (e) {
        if (!dragging) return;
        setRatio(thumb, ratioFromPointer(e));
      });
      function endDrag(e) {
        if (!dragging) return;
        dragging = false;
        if (thumb.hasPointerCapture && thumb.hasPointerCapture(e.pointerId)) {
          thumb.releasePointerCapture(e.pointerId);
        }
      }
      thumb.addEventListener("pointerup", endDrag);
      thumb.addEventListener("pointercancel", endDrag);

      // standard ARIA slider keyboard pattern: arrows step 1dB, Page steps
      // 3dB, Home/End jump to the extremes.
      thumb.addEventListener("keydown", function (e) {
        var ratio = ratioOf(thumb);
        var step = 1 / 24;
        if (e.key === "ArrowUp" || e.key === "ArrowRight") ratio -= step;
        else if (e.key === "ArrowDown" || e.key === "ArrowLeft") ratio += step;
        else if (e.key === "PageUp") ratio -= step * 3;
        else if (e.key === "PageDown") ratio += step * 3;
        else if (e.key === "Home") ratio = 0;
        else if (e.key === "End") ratio = 1;
        else return;
        e.preventDefault();
        setRatio(thumb, ratio);
      });

      setRatio(thumb, ratioOf(thumb)); // normalize aria-valuenow to the CSS default
    });
  }

  document.querySelectorAll(".winamp-eq").forEach(setupPanel);

  // ON/AUTO: real persistent toggle buttons — the skin ships a genuine
  // off/on sprite pair for each (see write_sprites_css's SELECTED handling
  // in import_skin.py), so clicking swaps between them and CSS's own
  // :active pseudo-class layers the momentary pressed look on top.
  document.querySelectorAll("[data-eq-toggle]").forEach(function (btn) {
    var base = null;
    btn.classList.forEach(function (c) {
      if (/^spr-eq-(on|auto)-button$/.test(c)) base = c;
    });
    if (!base) return;
    btn.addEventListener("click", function () {
      var on = btn.classList.toggle(base + "-selected");
      btn.setAttribute("aria-pressed", String(on));
    });
  });
})();
