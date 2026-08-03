/* Shared bitmap-font glyph builder: turns TEXT into a run of .skinchar spans
 * positioned into the active skin's text.png via CHARS (chars.json offsets).
 * Mirrors the `skintext` Jinja filter in pelicanconf.py, which renders the
 * server-side default; this is the client-side equivalent used wherever a
 * skin switch needs to re-render bitmap text after the page has loaded —
 * the homepage marquee (player.js) and the section headers (skin-fixup.js).
 */
window.SkinGlyphs = function (text, chars) {
  var frag = document.createDocumentFragment();
  var up = String(text).toUpperCase();
  for (var i = 0; i < up.length; i++) {
    var pos = chars[up[i]] || chars[" "];
    if (!pos) continue;
    var s = document.createElement("span");
    s.className = "skinchar";
    s.style.backgroundPosition =
      (pos[0] ? -pos[0] + "px" : "0") + " " + (pos[1] ? -pos[1] + "px" : "0");
    frag.appendChild(s);
  }
  return frag;
};
