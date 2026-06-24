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

  // Theme toggle (dark <-> light), injected so page headers stay clean
  (function () {
    var root = document.documentElement;
    var MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg>';
    var SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'theme-toggle';
    function sync() {
      var light = root.dataset.theme === 'light';
      btn.innerHTML = light ? MOON : SUN;
      btn.setAttribute('aria-label', light ? 'Przełącz na tryb ciemny' : 'Przełącz na tryb jasny');
      btn.setAttribute('aria-pressed', light ? 'true' : 'false');
    }
    btn.addEventListener('click', function () {
      var light = root.dataset.theme === 'light';
      if (light) { delete root.dataset.theme; } else { root.dataset.theme = 'light'; }
      try { localStorage.setItem('btf-theme', root.dataset.theme || 'dark'); } catch (e) {}
      sync();
    });
    var navr = document.querySelector('.nav-r');
    if (navr) { navr.insertBefore(btn, navr.firstChild); sync(); }

    // Follow OS/browser theme changes live — but only until the user picks one.
    if (window.matchMedia) {
      var mq = matchMedia('(prefers-color-scheme: dark)');
      var onSys = function (e) {
        try { if (localStorage.getItem('btf-theme')) return; } catch (err) {}
        if (e.matches) { delete root.dataset.theme; } else { root.dataset.theme = 'light'; }
        sync();
      };
      if (mq.addEventListener) mq.addEventListener('change', onSys);
      else if (mq.addListener) mq.addListener(onSys);
    }
  })();
})();
