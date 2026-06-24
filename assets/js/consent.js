/* BTF Carbon — cookie/third-party consent.
   The site sets NO cookies of its own. Third-party content that may set cookies
   or transmit data (Google Maps embed, Google Fonts) is loaded ONLY after the
   user accepts. Choice is stored in localStorage. "Ustawienia cookies" in the
   footer reopens the banner. */
(function () {
  "use strict";
  var KEY = "btf-consent";
  var FONTS_HREF =
    "https://fonts.googleapis.com/css2?family=Oswald:wght@300;400;500;600;700" +
    "&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500&display=swap";

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

  function loadMap() {
    var slot = document.querySelector("[data-map-slot]");
    var tpl = document.querySelector("template[data-map-embed]");
    if (!slot || !tpl || slot.querySelector("iframe")) return;
    slot.classList.add("loaded");
    slot.innerHTML = "";
    slot.appendChild(tpl.content.cloneNode(true));
  }

  function grant() { loadFonts(); loadMap(); }

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
        '<p class="consent__text">Ta strona <b>nie zbiera danych</b> ani nie używa analityki. ' +
        'Po Twojej zgodzie ładujemy treści zewnętrzne (mapa Google, Google Fonts), ' +
        'które mogą zapisać pliki cookies. Szczegóły w ' +
        '<a href="polityka-prywatnosci.html">Polityce prywatności</a>.</p>' +
        '<div class="consent__actions">' +
          '<button type="button" class="btn btn--ghost btn--sm" data-consent="deny">Tylko niezbędne</button>' +
          '<button type="button" class="btn btn--sm" data-consent="accept">Akceptuję</button>' +
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

    document.querySelectorAll("[data-cookie-settings]").forEach(function (el) {
      el.addEventListener("click", function (e) { e.preventDefault(); banner().hidden = false; });
    });
    // explicit per-map load button also grants (map only)
    document.querySelectorAll("[data-load-map]").forEach(function (btn) {
      btn.addEventListener("click", function () { set("granted"); grant(); });
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
