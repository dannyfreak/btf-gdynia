// BTF Carbon — shared interactions: sticky header, mobile menu, reveal, map.
(function () {
  var hd = document.querySelector('header.site');
  if (hd && !hd.classList.contains('always')) {
    var onScroll = function () { hd.classList.toggle('solid', window.scrollY > 40); };
    onScroll();
    addEventListener('scroll', onScroll, { passive: true });
  }

  var toggle = document.querySelector('.navtoggle');
  var menu = document.querySelector('.mobile-nav');
  if (toggle && menu) {
    toggle.addEventListener('click', function () {
      var open = menu.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    menu.addEventListener('click', function (e) { if (e.target.tagName === 'A') menu.classList.remove('open'); });
  }

  // Reveal on scroll
  var els = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && els.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    els.forEach(function (el) { io.observe(el); });
  } else {
    els.forEach(function (el) { el.classList.add('in'); });
  }

  // (Map loading + consent live in consent.js)
})();
