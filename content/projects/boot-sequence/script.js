// boot-sequence — types out a fake Y2K boot log, then idles at a prompt.
(function () {
  "use strict";

  var lines = [
    "BOTANICAL BIOS v2.0.0 ............... OK",
    "Detecting memory ........... 640K base, 64M extended",
    "Initializing display adapter ....... [aero/glossy]",
    "Mounting /garden ................... OK",
    "Loading skins: aero ................ done",
    "Spinning up flora daemon ........... running",
    "Checking sunlight levels ........... 87% nominal",
    "Watering schedule .................. armed",
    "",
    "SYSTEM READY.",
  ];

  var log = document.getElementById("log");
  var li = 0;
  var ci = 0;

  function typeChar() {
    if (li >= lines.length) {
      var cursor = document.createElement("span");
      cursor.className = "cursor";
      log.appendChild(cursor);
      return;
    }
    var line = lines[li];
    if (ci < line.length) {
      log.appendChild(document.createTextNode(line.charAt(ci)));
      ci++;
      setTimeout(typeChar, 14 + Math.random() * 22);
    } else {
      log.appendChild(document.createTextNode("\n"));
      li++;
      ci = 0;
      setTimeout(typeChar, line === "" ? 120 : 260);
    }
  }

  typeChar();
})();
