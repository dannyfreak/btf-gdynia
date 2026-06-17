/* BTF cookie/third-party consent.
   The site sets NO cookies of its own. Third-party content that may set cookies
   or transmit data (Google Maps embed, Google Fonts) is loaded ONLY after the
   user accepts. Choice is stored in localStorage (strictly necessary, no consent
   required for that). "Ustawienia cookies" in the footer reopens the banner. */
(function () {
  "use strict";
  var KEY = "btf-consent";
  var FONTS_HREF =
    "https://fonts.googleapis.com/css2?family=Archivo:wght@600;700;800;900" +
    "&family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap";

  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function set(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }

  function loadFonts() {
    if (document.getElementById("btf-fonts")) return;
    var pre = document.createElement("link");
    pre.rel = "preconnect"; pre.href = "https://fonts.gstatic.com"; pre.crossOrigin = "";
    document.head.appendChild(pre);
    var l = document.createElement("link");
    l.id = "btf-fonts"; l.rel = "stylesheet"; l.href = FONTS_HREF;
    document.head.appendChild(l);
  }

  function loadMaps() {
    var tpls = document.querySelectorAll("template[data-map-embed]");
    for (var i = 0; i < tpls.length; i++) {
      var tpl = tpls[i];
      var slot = tpl.closest("[data-map-slot]") || tpl.parentNode;
      if (!slot || slot.querySelector("iframe")) continue;
      if (tpl.content) slot.appendChild(tpl.content.cloneNode(true));
      var ph = slot.querySelector("[data-map-placeholder]");
      if (ph) ph.hidden = true;
    }
  }

  function grant() { loadFonts(); loadMaps(); }

  function banner() {
    var b = document.getElementById("btf-consent-banner");
    if (b) return b;
    b = document.createElement("div");
    b.id = "btf-consent-banner";
    b.className = "consent";
    b.setAttribute("role", "dialog");
    b.setAttribute("aria-label", "Zgoda na pliki cookies");
    b.hidden = true;
    b.innerHTML =
      '<div class="consent__inner">' +
        '<p class="consent__text">Ta strona <strong>nie zbiera danych</strong> ani nie używa analityki. ' +
        'Po Twojej zgodzie ładujemy treści zewnętrzne (mapa Google, Google Fonts), ' +
        'które mogą zapisać pliki cookies. Szczegóły w ' +
        '<a href="polityka-prywatnosci.html">Polityce prywatności</a>.</p>' +
        '<div class="consent__actions">' +
          '<button type="button" class="btn btn--ghost" data-consent="deny">Tylko niezbędne</button>' +
          '<button type="button" class="btn btn--primary" data-consent="accept">Akceptuję</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(b);
    b.querySelector('[data-consent="accept"]').addEventListener("click", function () {
      set("granted"); grant(); b.hidden = true;
    });
    b.querySelector('[data-consent="deny"]').addEventListener("click", function () {
      set("denied"); b.hidden = true;
    });
    return b;
  }

  function init() {
    var b = banner();
    var c = get();
    if (c === "granted") grant();
    else if (c !== "denied") b.hidden = false;

    var settings = document.querySelectorAll("[data-cookie-settings]");
    for (var i = 0; i < settings.length; i++) {
      settings[i].addEventListener("click", function (e) {
        e.preventDefault(); banner().hidden = false;
      });
    }
    var loaders = document.querySelectorAll("[data-load-map]");
    for (var j = 0; j < loaders.length; j++) {
      loaders[j].addEventListener("click", function () { set("granted"); grant(); });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else { init(); }
})();
