/* Homepage audio player (see PLAYER.md).
 *
 * Directory-driven: fetches music.json (emitted at build time from
 * content/music/) and cycles through the tracks. The Winamp sprite transport
 * buttons in the main window drive a single hidden <audio> element.
 *
 * Scope: homepage only. There's no autoplay-with-sound — browsers require a
 * user gesture, so the first play happens on a button click. Music persists
 * across the site only because section links open new tabs (leaving this tab
 * playing); we never try to keep <audio> alive across navigation.
 *
 * This piece wires play/pause/stop/prev/next + auto-cycle and the display
 * readouts (bitmap time + scrolling title). Shuffle/repeat and the visualizer
 * come in later steps.
 */
(function () {
  var root = document.querySelector(".winamp-main");
  var audio = document.getElementById("wa-audio");
  if (!root || !audio) return;

  var tracks = [];
  var index = 0;
  var loaded = false; // is tracks[index] loaded into <audio> yet?

  function resolve(path) {
    // resolve relative to the page (homepage at the site root)
    return new URL(path, document.baseURI).href;
  }

  /* ---- bitmap time display (numbers.bmp digits) ---- */
  var digitEls = root.querySelectorAll(".wa-time .wa-d");
  function renderTime(sec) {
    sec = Math.max(0, Math.floor(sec || 0));
    var mm = Math.min(99, Math.floor(sec / 60)), ss = sec % 60;
    var d = [Math.floor(mm / 10), mm % 10, Math.floor(ss / 10), ss % 10];
    for (var i = 0; i < digitEls.length; i++) {
      digitEls[i].className = digitEls[i].className.replace(/spr-digit-\d/, "spr-digit-" + d[i]);
    }
  }
  renderTime(0);
  audio.addEventListener("timeupdate", function () { renderTime(audio.currentTime); });

  /* ---- scrolling title marquee (text.bmp font via chars.json) ---- */
  var marquee = root.querySelector(".wa-marquee");
  var chars = null;
  var SEP = "   ***   ";

  function glyphs(text, into) {
    var up = text.toUpperCase();
    for (var i = 0; i < up.length; i++) {
      var pos = chars[up[i]] || chars[" "];
      if (!pos) continue;
      var s = document.createElement("span");
      s.className = "skinchar";
      s.style.backgroundPosition =
        (pos[0] ? -pos[0] + "px" : "0") + " " + (pos[1] ? -pos[1] + "px" : "0");
      into.appendChild(s);
    }
  }

  // Webamp marquee format: "N. Artist - Title (m:ss)" (artist/length optional)
  function trackText(i) {
    var t = tracks[i];
    if (!t) return "";
    var name = (t.artist ? t.artist + " - " : "") + (t.title || "");
    return (i + 1) + ". " + name + (t.length ? " (" + t.length + ")" : "");
  }

  function setTitle(text) {
    if (!marquee || !chars) return;
    marquee.textContent = "";
    var strip = document.createElement("div");
    strip.className = "wa-marquee-strip";
    // continuous ticker: always scrolls. Render "title + SEP" twice so the
    // animation loops seamlessly (translate by exactly one copy's width).
    glyphs(text + SEP, strip);
    marquee.appendChild(strip);
    requestAnimationFrame(function () {
      var oneW = strip.scrollWidth;            // width of one (title + SEP)
      glyphs(text + SEP, strip);               // second copy
      strip.style.setProperty("--wa-scroll-w", oneW + "px");
      strip.style.animationDuration = Math.max(4, (text.length + SEP.length) * 0.32) + "s";
      strip.classList.add("wa-scrolling");
    });
  }

  function loadTrack(i, andPlay) {
    if (!tracks.length) return;
    var n = tracks.length;
    index = ((i % n) + n) % n; // wrap both directions
    audio.src = resolve(tracks[index].file);
    loaded = true;
    setTitle(trackText(index));
    if (andPlay) audio.play().catch(function () {});
  }

  var actions = {
    play: function () {
      if (!tracks.length) return;
      if (!loaded) loadTrack(index, false);
      audio.play().catch(function () {});
    },
    pause: function () {
      // toggle, like Winamp's pause button
      if (audio.paused) {
        if (loaded) audio.play().catch(function () {});
      } else {
        audio.pause();
      }
    },
    stop: function () {
      audio.pause();
      audio.currentTime = 0;
    },
    prev: function () { loadTrack(index - 1, true); },
    next: function () { loadTrack(index + 1, true); },
  };

  root.querySelectorAll("[data-action]").forEach(function (btn) {
    var fn = actions[btn.getAttribute("data-action")];
    if (fn) btn.addEventListener("click", fn);
  });

  // auto-advance to the next track (wrapping last -> first)
  audio.addEventListener("ended", function () { loadTrack(index + 1, true); });

  // reflect play state on the root for styling / future indicators
  audio.addEventListener("play", function () { root.classList.add("is-playing"); });
  audio.addEventListener("pause", function () { root.classList.remove("is-playing"); });

  // show the first track's title once both the manifest and font map are in
  // (display is populated before the first play; audio still loads on click)
  function showFirst() {
    if (chars && tracks.length && !loaded) setTitle(trackText(0));
  }

  fetch(resolve("music.json"))
    .then(function (r) { return r.ok ? r.json() : []; })
    .then(function (list) { tracks = Array.isArray(list) ? list : []; showFirst(); })
    .catch(function () { tracks = []; });

  if (marquee && marquee.dataset.chars) {
    fetch(marquee.dataset.chars)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (m) { chars = m; showFirst(); })
      .catch(function () { chars = null; });
  }
})();
