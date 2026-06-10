(function () {
  'use strict';

  var ROUTES = { about: 'about', mission: 'mission', civfix: 'civfix', help: 'help' };

  var SITE_TITLE = 'Reach Out LA';
  // Full <title> strings, kept in sync with each page's static <title> so the
  // title Google renders (JS runs) matches the server-sent HTML — no SEO mismatch.
  var HOME_TITLE = 'Reach Out LA';
  var TITLES = {
    about:   'About | ' + SITE_TITLE,
    mission: 'Mission| ' + SITE_TITLE,
    civfix:  'Civfix | ' + SITE_TITLE,
    help:    'Help Us | ' + SITE_TITLE
  };
  function setTitle(key) {
    document.title = (key && TITLES[key]) ? TITLES[key] : HOME_TITLE;
  }

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
    setTitle(key);
  }
  function showHome() {
    backFallOut();
    drive(function () { if (backBtn) backBtn.click(); });
    current = null;
    setTitle(null);
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
        setTitle(key);
      }
      return;
    }
    if (t.closest('#pageBack') && current !== null) {
      current = null;
      history.pushState({ key: null }, '', '/');
      setTitle(null);
      backFallOut();
    }
  }, true);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !driving && current !== null) {
      current = null;
      history.pushState({ key: null }, '', '/');
      setTitle(null);
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
  setTitle(initialKey);

  if (initialKey) {
    var stageEl = document.getElementById('stage');
    if (stageEl) stageEl.style.display = 'none';

    var pageEl = document.getElementById('page');
    var c = cardFor(initialKey);
    if (c) {
      driving = true;
      try {
        c.click();
        if (window.gsap) {
          var deckEls = Array.from(document.querySelectorAll('#logo .char'))
                          .concat(Array.from(document.querySelectorAll('.deck-card')));
          gsap.getTweensOf(deckEls).forEach(function (t) { try { t.progress(1); } catch (e) {} });
        }
        document.body.classList.add('viewing');
        if (stageEl) stageEl.style.display = 'none';
      } finally { driving = false; }
      current = initialKey;

      setTimeout(function () {
        if (!window.gsap || !pageEl) return;
        var sample = pageEl.querySelector('.page-title .char');
        if (sample && parseFloat(getComputedStyle(sample).opacity) < 0.05) {
          gsap.set(Array.from(pageEl.querySelectorAll('.page-title .char, .page-eyebrow, .block')),
            { opacity: 1, x: 0, y: 0, rotation: 0, scale: 1 });
        }
      }, 900);
    }
  }
})();
