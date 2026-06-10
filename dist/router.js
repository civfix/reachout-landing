(function () {
  'use strict';

  var ROUTES = { about: 'about', mission: 'mission', civfix: 'civfix', help: 'help' };

  function keyFromPath(path) {
    var seg = (path || '/').replace(/^\/+|\/+$/g, '').split('/')[0].toLowerCase();
    return ROUTES[seg] || null;
  }
  function pathFromKey(key) { return key ? '/' + key : '/'; }

  function cardFor(key) {
    return document.querySelector('.deck-card[data-key="' + key + '"]');
  }
  var backBtn = document.getElementById('pageBack');

  var canAnimateBack = !!(window.gsap && backBtn && window.MutationObserver);
  function backFallIn() {
    if (!canAnimateBack) return;
    gsap.killTweensOf(backBtn);
    gsap.fromTo(backBtn,
      { y: -110, opacity: 0, rotation: -8, scale: 0.7 },
      { y: 0, opacity: 1, rotation: 0, scale: 1, duration: 0.9, delay: 0.1,
        ease: 'elastic.out(1, 0.6)',

        onComplete: function () { gsap.set(backBtn, { clearProps: 'transform' }); } });
  }
  function backFallOut() {
    if (!canAnimateBack) return;
    gsap.killTweensOf(backBtn);
    gsap.to(backBtn, { y: 130, opacity: 0, rotation: 8, scale: 0.85,
      duration: 0.42, ease: 'back.in(1.5)' });
  }
  if (canAnimateBack) {

    gsap.set(backBtn, { opacity: 0 });

    var backWasViewing = document.body.classList.contains('viewing');
    new MutationObserver(function () {
      var v = document.body.classList.contains('viewing');
      if (v && !backWasViewing) backFallIn();
      backWasViewing = v;
    }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
  }

  var current = null;

  var driving = false;

  function drive(fn) { driving = true; try { fn(); } finally { driving = false; } }

  function showKey(key) {
    var c = key && cardFor(key);
    if (!c) return;
    drive(function () { c.click(); });
    current = key;
  }
  function showHome() {
    backFallOut();
    drive(function () { if (backBtn) backBtn.click(); });
    current = null;
  }

  document.addEventListener('click', function (e) {
    if (driving) return;
    var t = e.target;
    if (!t || !t.closest) return;

    var card = t.closest('.deck-card');
    if (card) {
      var key = card.getAttribute('data-key');
      if (ROUTES[key] && current !== key) {
        current = key;
        history.pushState({ key: key }, '', pathFromKey(key));
      }
      return;
    }
    if (t.closest('#pageBack') && current !== null) {
      current = null;
      history.pushState({ key: null }, '', '/');
      backFallOut();
    }
  }, true);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !driving && current !== null) {
      current = null;
      history.pushState({ key: null }, '', '/');
      backFallOut();
    }
  });

  window.addEventListener('popstate', function () {
    var key = keyFromPath(location.pathname);
    if (key === current) return;
    if (key && current === null) {
      showKey(key);
    } else if (!key && current !== null) {
      showHome();
    } else {
      showHome();
      setTimeout(function () { showKey(key); }, 700);
    }
  });

  var initialKey = keyFromPath(location.pathname);

  history.replaceState({ key: initialKey }, '', pathFromKey(initialKey));
  current = initialKey;

  if (initialKey) {

    var stageEl = document.getElementById('stage');
    if (stageEl) stageEl.style.display = 'none';

    var realMatchMedia = window.matchMedia;
    var reducedStub = {
      matches: true, media: '(prefers-reduced-motion: reduce)', onchange: null,
      addEventListener: function () {}, removeEventListener: function () {},
      addListener: function () {}, removeListener: function () {},
      dispatchEvent: function () { return false; }
    };
    try {
      window.matchMedia = function (q) {
        if (/prefers-reduced-motion/.test(String(q))) return reducedStub;
        return realMatchMedia.call(window, q);
      };
    } catch (err) {  }

    var opened = false;
    var openOnce = function () {
      if (opened) return;
      opened = true;

      try { window.matchMedia = realMatchMedia; } catch (e) {}

      setTimeout(function () {
        var c = cardFor(initialKey);
        if (!c) return;
        driving = true;
        try {
          c.click();

          if (window.gsap) {
            var deckEls = Array.from(document.querySelectorAll('#logo .char'))
                            .concat(Array.from(document.querySelectorAll('.deck-card')));
            gsap.getTweensOf(deckEls).forEach(function (t) { try { t.progress(1); } catch (e) {} });
          }
        } finally { driving = false; }
        current = initialKey;
      }, 0);
    };

    if (document.fonts && document.fonts.ready) {
      Promise.race([
        document.fonts.ready,
        new Promise(function (r) { setTimeout(r, 950); })
      ]).then(openOnce);
    } else {

      setTimeout(openOnce, 60);
    }
  }
})();
