/* Winamp-style playlist scrollbar.
 *
 * The row list (.pl-body) scrolls natively (overflow-y) with its native
 * scrollbar hidden; this script drives the skin's scroll-handle sprite in the
 * right-edge groove so it reflects the scroll position and can be dragged.
 *
 * Note on coordinates: the whole player sits inside a `zoom`ed ancestor, so
 * layout metrics (scrollTop, clientHeight, offsetHeight) are in unzoomed CSS
 * px while pointer events (clientY) and getBoundingClientRect() are in painted
 * screen px. We position the handle in layout px (it lives in the same zoomed
 * space) and do drag math in painted px — never mixing the two.
 */
(function () {
  function setup(pl) {
    var body = pl.querySelector(".pl-body");
    var track = pl.querySelector(".pl-scrolltrack");
    var handle = pl.querySelector(".pl-handle");
    if (!body || !track || !handle) return;

    function syncHandle() {
      var range = body.scrollHeight - body.clientHeight; // hidden, layout px
      var travel = track.clientHeight - handle.offsetHeight; // layout px
      if (range <= 0 || travel <= 0) {
        handle.style.top = "0px";
        handle.style.display = range <= 0 ? "none" : ""; // hide when nothing to scroll
        return;
      }
      handle.style.display = "";
      handle.style.top = Math.round((body.scrollTop / range) * travel) + "px";
    }

    body.addEventListener("scroll", syncHandle);
    window.addEventListener("resize", syncHandle);

    // drag the handle -> set scrollTop from the pointer's position over the
    // track (painted px); the resulting scroll event repositions the handle.
    var dragging = false;
    handle.addEventListener("pointerdown", function (e) {
      dragging = true;
      handle.setPointerCapture(e.pointerId);
      e.preventDefault();
    });
    handle.addEventListener("pointermove", function (e) {
      if (!dragging) return;
      var range = body.scrollHeight - body.clientHeight;
      if (range <= 0) return;
      var tRect = track.getBoundingClientRect();
      var hRect = handle.getBoundingClientRect();
      var travel = tRect.height - hRect.height; // painted px
      if (travel <= 0) return;
      var ratio = (e.clientY - tRect.top - hRect.height / 2) / travel;
      ratio = Math.max(0, Math.min(1, ratio));
      body.scrollTop = ratio * range;
    });
    function endDrag(e) {
      if (!dragging) return;
      dragging = false;
      if (handle.hasPointerCapture && handle.hasPointerCapture(e.pointerId)) {
        handle.releasePointerCapture(e.pointerId);
      }
    }
    handle.addEventListener("pointerup", endDrag);
    handle.addEventListener("pointercancel", endDrag);

    syncHandle();
  }

  document.querySelectorAll(".winamp-playlist").forEach(setup);
})();
