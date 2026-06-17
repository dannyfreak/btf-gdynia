/* Accessible mobile menu toggle. Progressive enhancement: with JS disabled the
   nav remains in the DOM and is shown by CSS at wide viewports / falls back to a
   visible list. The toggle drives aria-expanded + an .is-open class on the nav. */
(function () {
  "use strict";
  var toggle = document.querySelector(".nav-toggle");
  if (!toggle) return;
  var navId = toggle.getAttribute("aria-controls");
  var nav = navId ? document.getElementById(navId) : null;
  if (!nav) return;

  function setOpen(open) {
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    nav.classList.toggle("is-open", open);
  }

  toggle.addEventListener("click", function () {
    var open = toggle.getAttribute("aria-expanded") === "true";
    setOpen(!open);
  });

  // Close the menu on Escape and when a nav link is followed.
  nav.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
      setOpen(false);
      toggle.focus();
    }
  });
  nav.addEventListener("click", function (e) {
    if (e.target.closest("a")) setOpen(false);
  });
})();
