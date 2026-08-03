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
 * readouts (bitmap time + scrolling title). Playback order is shuffled (see
 * shuffle() below), not the manifest's filename order — drop a new file into
 * content/music/ and it just joins the rotation, no renaming/numbering needed.
 * Repeat and the visualizer come in later steps.
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

  // Fisher-Yates, in place. Called once on load and again whenever playback
  // wraps around, so the rotation keeps re-randomizing instead of repeating
  // the same lap in the same order.
  function shuffle(arr) {
    for (var i = arr.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = arr[i]; arr[i] = arr[j]; arr[j] = tmp;
    }
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
    into.appendChild(window.SkinGlyphs(text, chars));
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
    prev: function () { advance(-1); },
    next: function () { advance(1); },
  };

  // Move one step through the shuffled order; reshuffle on wrap so each lap
  // through the rotation lands in a fresh random order.
  function advance(delta) {
    var n = tracks.length;
    if (!n) return;
    var i = index + delta;
    if (i < 0 || i >= n) {
      shuffle(tracks);
      i = delta > 0 ? 0 : n - 1;
    }
    loadTrack(i, true);
  }

  root.querySelectorAll("[data-action]").forEach(function (btn) {
    var fn = actions[btn.getAttribute("data-action")];
    if (fn) btn.addEventListener("click", fn);
  });

  // auto-advance to the next track (wrapping last -> first, reshuffled)
  audio.addEventListener("ended", function () { advance(1); });

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
    .then(function (list) {
      tracks = Array.isArray(list) ? list : [];
      shuffle(tracks);
      showFirst();
    })
    .catch(function () { tracks = []; });

  if (marquee && marquee.dataset.chars) {
    fetch(marquee.dataset.chars)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (m) { chars = m; showFirst(); })
      .catch(function () { chars = null; });
  }
})();
