(function () {
  const chars = Array.from(document.querySelectorAll('.char'));
  const cards = Array.from(document.querySelectorAll('.deck-card'));
  const stage = document.getElementById('stage');
  const page = document.getElementById('page');
  const pageBack = document.getElementById('pageBack');
  const C = window.ROLA_CONTENT;
  const durationScalar = 1.0;

  let entered = false;
  let pageActive = false;
  let openKey = null;
  let transId = 0;

  const input = {
    x: window.innerWidth / 2,
    y: window.innerHeight / 2,
    lastX: window.innerWidth / 2,
    lastY: window.innerHeight / 2
  };

  const charData = [];
  const cardData = [];
  let running = false;

  function recordFor(list, el, amp, baseRot) {
    const b = el.getBoundingClientRect();
    list.push({
      element: el, amp, baseRot: baseRot || 0,
      x: 0, y: 0, vx: 0, vy: 0, targetX: 0, targetY: 0,
      pageX: b.left + b.width / 2,
      pageY: b.top + b.height / 2,
      width: b.width, height: b.height
    });
  }

  function remeasure() {
    if (pageActive) return;
    [charData, cardData].forEach(list => list.forEach(d => {
      const b = d.element.getBoundingClientRect();
      d.pageX = b.left + b.width / 2 - d.x;
      d.pageY = b.top + b.height / 2 - d.y;
      d.width = b.width;
      d.height = b.height;
    }));
  }
  window.addEventListener('resize', remeasure);

  function recordAll() {
    chars.forEach(c => recordFor(charData, c, 10, 0));
    cards.forEach(c => recordFor(cardData, c, 3.4, parseFloat(c.dataset.rot) || 0));
  }

  function resetWiggle() {
    [charData, cardData].forEach(list => list.forEach(d => { d.x = 0; d.y = 0; d.vx = 0; d.vy = 0; }));
  }

  function finishEntrance() {
    if (entered) return;
    entered = true;
    gsap.killTweensOf(chars);
    gsap.killTweensOf(cards);
    gsap.set(chars, { y: 0, opacity: 1, scale: 1, rotation: 0 });
    gsap.set(cards, { y: 0, opacity: 1, scale: 1, rotation: (i, el) => parseFloat(el.dataset.rot) || 0 });
    recordAll();
    start();
  }

  function transitionIn() {
    let delay = 0;
    chars.forEach((char, i) => {
      const spin = Math.random() < 0.5 ? -1 : 1;
      const tl = gsap.timeline(i === chars.length - 1 ? { onComplete: finishEntrance } : {});
      tl.fromTo(char,
        { y: -window.innerHeight / 2, opacity: 0, scale: 0.5, rotation: 360 * spin },
        { y: window.innerHeight / 2, opacity: 1, scale: 1, rotation: 180 * spin,
          duration: 0.85 * durationScalar, ease: 'power3.in', delay: delay });
      tl.to(char, { y: 0, rotation: 0, duration: 1.5 * durationScalar, ease: 'elastic' });
      delay += 0.13;
    });
    gsap.fromTo(cards,
      { y: () => -window.innerHeight * 0.7, opacity: 0, scale: 0.7, rotation: () => (Math.random() < 0.5 ? -22 : 22) },
      { y: 0, opacity: 1, scale: 1, rotation: (i, el) => parseFloat(el.dataset.rot) || 0,
        duration: 1.4, ease: 'elastic.out(1, 0.55)', stagger: 0.1, delay: delay + 0.1 });
    setTimeout(finishEntrance, 4200);
  }

  const friction = 0.7;
  function dist(x1, x2, y1, y2) { const a = x1 - x2, b = y1 - y2; return Math.sqrt(a * a + b * b); }
  function smoothstep(min, max, v) { const x = Math.max(0, Math.min(1, (v - min) / (max - min))); return x * x * (3 - 2 * x); }

  function step() {
    requestAnimationFrame(step);
    if (pageActive) { input.lastX = input.x; input.lastY = input.y; return; }
    const velX = (input.x - input.lastX);
    const velY = (input.y - input.lastY);
    applyWiggle(charData, velX, velY, 0.1, 0.0025, 270);
    applyWiggle(cardData, velX, velY, 0.05, 0.0016, 80);
    input.lastX = input.x;
    input.lastY = input.y;
  }

  function applyWiggle(list, velX, velY, reach, rotK, rotCap) {
    list.forEach(d => {
      const dd = dist(input.x, d.pageX, input.y, d.pageY);
      const scalar = smoothstep(d.width + d.height, 0, dd) * reach;
      d.targetX = velX * d.amp * scalar;
      d.targetY = velY * d.amp * scalar;
      const dx = d.targetX - d.x * 0.1;
      const dy = d.targetY - d.y * 0.1;
      d.vx += dx; d.vy += dy;
      d.vx *= friction; d.vy *= friction;
      d.x += d.vx; d.y += d.vy;
      const r = Math.max(Math.min(rotK * (d.x + d.y), rotCap), -rotCap);
      d.element.style.transform = `translate(${d.x}px, ${d.y}px) rotate(${r + d.baseRot}deg)`;
    });
  }

  function start() { if (!running) { running = true; step(); } }

  // ---- Hollywood-sign glyphs with a continuous LA-map face -------------------
  // Each letter is rendered as an INLINE svg (not <img>) so every glyph can pull
  // from ONE shared map image. A letter's map crop is offset by its cumulative
  // position along the line, so adjacent letters line up into a single, zoomed-in
  // map that reads continuously across the whole word. Renders uppercase; the
  // letter is kept on the span (aria-label + data-ch) for a11y / re-runs.
  const GLYPH_SET = 'ABCEFHILMNOPRSTUVX';
  const glyphTpl = {};            // ch -> { raw, W }
  let glyphSeq = 0;

  const MAP_SRC = 'images/la-map.webp';
  const MAP_W = 816, MAP_H = 527; // intrinsic source size (for aspect only)
  const MAP_ZOOM = 1.35;          // 1 = whole map spread across a line; >1 zooms into its centre strip
  const MAP_CENTER_Y = 0.52;      // which horizontal band of the map shows through the faces (0 top .. 1 bottom)
  const MAP_OPACITY = 0.95;
  const SPACE_UNITS = 30;         // continuity width charged to a word space, in glyph units
  const FACE_CY = 42;             // approx vertical centre of a letter face, in viewBox units

  const templatesReady = Promise.all([...GLYPH_SET].map(ch =>
    fetch('letters/' + ch + '.svg').then(r => r.text()).then(t => {
      const m = t.match(/viewBox="0 0 ([\d.]+) ([\d.]+)"/);
      glyphTpl[ch] = { raw: t, W: m ? parseFloat(m[1]) : 60 };
    })
  ));

  function buildGlyphSVG(ch, leftUnits, bandUnits) {
    const tpl = glyphTpl[ch];
    if (!tpl) return null;
    const k = ++glyphSeq;
    let s = tpl.raw;
    ['g', 'clip', 'sil', 'face'].forEach(id => {       // namespace ids: inlined svgs must not share url(#id)
      s = s.split('id="' + id + '"').join('id="' + id + '-' + k + '"')
           .split('href="#' + id + '"').join('href="#' + id + '-' + k + '"')
           .split('url(#' + id + ')').join('url(#' + id + '-' + k + ')');
    });
    const spanPx = MAP_W / MAP_ZOOM;        // map px spread across the whole line
    const startPx = (MAP_W - spanPx) / 2;   // centre the used strip when zoomed in
    const mppu = spanPx / bandUnits;        // map px per glyph unit (identical for every letter)
    const imgW = MAP_W / mppu;              // the full map, expressed in this glyph's units
    const imgH = MAP_H / mppu;
    const x = -(startPx / mppu) - leftUnits;
    const y = FACE_CY - MAP_CENTER_Y * imgH;
    const img = '<image class="map" x="' + x.toFixed(2) + '" y="' + y.toFixed(2) +
                '" width="' + imgW.toFixed(2) + '" height="' + imgH.toFixed(2) +
                '" preserveAspectRatio="none" clip-path="url(#clip-' + k + ')" opacity="' +
                MAP_OPACITY + '" href="' + MAP_SRC + '"/>';
    const grid = '<g clip-path="url(#clip-' + k + ')" stroke="#CFC8BA"';   // map sits over the face, under the grid
    const i = s.indexOf(grid);
    s = i >= 0 ? s.slice(0, i) + img + s.slice(i) : s.replace('</svg>', img + '</svg>');
    return s.replace('<svg ', '<svg class="glyph" ').replace(/ width="[\d.]+" height="[\d.]+"/, '');
  }

  function glyphifyLine(container) {
    if (!container) return;
    let band = 0;                                       // cumulative width of the line, in glyph units
    const items = Array.from(container.children).map(el => {
      if (el.classList.contains('char')) {
        const ch = (el.dataset.ch || el.textContent || '').trim().toUpperCase();
        const left = band; band += (glyphTpl[ch] ? glyphTpl[ch].W : 60);
        return { el, ch, left };
      }
      band += SPACE_UNITS; return null;
    });
    items.forEach(it => {
      if (!it) return;
      const svg = buildGlyphSVG(it.ch, it.left, band);
      if (svg == null) return;
      it.el.dataset.ch = it.ch;
      it.el.innerHTML = svg;
      it.el.dataset.glyphed = '1';
    });
    if (entered && !pageActive) remeasure();
  }

  // Back-compat: glyphify(els) -> rebuild whichever line(s) those els belong to.
  function glyphify(els) {
    const lines = new Set();
    els.forEach(el => { if (el.parentElement) lines.add(el.parentElement); });
    lines.forEach(glyphifyLine);
  }

  window.addEventListener('mousemove', e => {
    if (pageActive) return;
    input.x = e.clientX; input.y = e.clientY;
  }, false);
  window.addEventListener('touchmove', e => {
    if (pageActive) return;
    const t = e.changedTouches[0]; input.x = t.clientX; input.y = t.clientY;
  }, false);

  function makeTitle(text) {
    let html = '';
    for (const ch of text) {
      html += ch === ' ' ? '<span class="space"></span>' : `<span class="char">${ch}</span>`;
    }
    return html;
  }

  function slot(id, opts) {
    opts = opts || {};
    const shape = opts.shape || 'rounded';
    const radius = opts.radius != null ? opts.radius : 18;
    const cls = opts.cls || '';
    const ph = opts.ph || 'Drop a photo';
    const fit = opts.fit || '';
    const src = opts.src ? ` src="${opts.src}"` : '';
    const fitAttr = fit ? ` fit="${fit}"` : '';
    return `<image-slot class="${cls}" id="${id}" shape="${shape}" radius="${radius}" placeholder="${ph}"${src}${fitAttr}></image-slot>`;
  }

  function paras(arr) { return (arr || []).map(p => `<p>${p}</p>`).join(''); }

  function ctaCard(b) {
    const btn = b.button;
    const action = btn.notice
      ? `<button type="button" class="cta-btn" data-notice="${btn.notice}">${btn.label}` +
          `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>` +
        `</button>` +
        `<p class="cta-notice" hidden></p>`
      : `<a class="cta-btn" href="${btn.href}"${/^https?:/.test(btn.href) ? ' target="_blank" rel="noopener"' : ''}>${btn.label}` +
          `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg>` +
        `</a>`;
    return `<div class="cta-card">` +
      `<h2 class="sec-head">${b.heading}</h2>` +
      paras(b.paras) +
      action +
      `</div>`;
  }

  const TILTS = [-2.4, 2.1, -1.6, 2.8, -2.2, 1.7];

  function buildBlock(b) {
    switch (b.t) {
      case 'heading':
        return `<div class="block block-heading">` +
          `<h2 class="sec-head">${b.text}</h2>` +
          (b.sub ? `<p class="sec-sub">${b.sub}</p>` : '') +
          `</div>`;

      case 'spread': {
        let side;
        if (b.bios) {
          side = `<div class="spread-bios">` +
            b.bios.map((m, i) =>
              (m.label ? `<div class="side-label">${m.label}</div>` : '') +
              `<div class="side-bio">` +
                `<div class="tilt-card shot-wrap" style="--tilt:${TILTS[i % TILTS.length]}deg">` +
                  slot(m.slot, { cls: 'shot', radius: 18, ph: 'Headshot', src: m.src }) +
                `</div>` +
                `<div class="bio-body">` +
                  `<div class="bio-head">` +
                    `<div class="bio-name">${m.name}</div>` +
                    (m.email ? `<a class="bio-email" href="mailto:${m.email}" aria-label="Email ${m.name}" title="${m.email}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg></a>` : '') +
                  `</div>` +
                  `<div class="bio-role">${m.role}</div>` +
                  paras(m.bio) +
                `</div>` +
              `</div>`
            ).join('') +
          `</div>`;
        } else {
          side = `<div class="spread-media${b.sidecap ? ' is-sidecap' : ''}">` +
            b.media.map((it, i) =>
              `<figure class="tilt-card${it.full ? ' is-full' : ''}" style="--tilt:${TILTS[i % TILTS.length]}deg">` +
              slot(it.slot, { cls: 'media', src: it.src, fit: it.fit || '' }) +
              (it.cap ? `<figcaption class="${it.long ? 'pg-cap' : 'fig-cap'}">${it.long ? `<p>${it.cap}</p>` : it.cap}</figcaption>` : '') +
              `</figure>`
            ).join('') +
          `</div>`;
        }
        return `<div class="block block-spread${b.flip ? ' is-flip' : ''}${b.together ? ' is-together' : ''}">` +
          `<div class="spread-text">` +
            paras(b.paras) +
            (b.signed ? `<p class="prose-sign">${b.signed}</p>` : '') +
          `</div>` +
          side +
          `</div>`;
      }

      case 'ctarow':
        return `<div class="block block-ctarow">` +
          b.items.map(ctaCard).join('') +
          `</div>`;

      default:
        return '';
    }
  }

  function buildPage(key) {
    const d = C[key];
    const blocks = d.blocks.map(buildBlock).join('');
    page.innerHTML =
      `<header class="page-head">` +
        `<div class="page-eyebrow">Reach Out Los Angeles</div>` +
        `<h1 class="page-title">${makeTitle(d.title)}</h1>` +
      `</header>` +
      `<div class="page-flow page-flow-${key}">${blocks}</div>`;
  }

  function openPage(key) {
    if (!entered) finishEntrance();
    const my = ++transId;
    pageActive = true;
    openKey = key;
    buildPage(key);

    const vh = window.innerHeight;
    gsap.killTweensOf(chars); gsap.killTweensOf(cards);
    gsap.to(chars, {
      y: () => vh * 1.15, opacity: 0, rotation: () => gsap.utils.random(-120, 120), scale: 0.8,
      duration: 0.48, ease: 'back.in(1.4)', stagger: { each: 0.016, from: 'random' }
    });
    gsap.to(cards, {
      y: () => vh * 1.15, opacity: 0, rotation: () => gsap.utils.random(-40, 40), scale: 0.8,
      duration: 0.5, ease: 'back.in(1.4)', stagger: 0.04,
      onComplete: () => {
        if (my !== transId) return;
        stage.style.display = 'none';
        document.body.classList.add('viewing');
        window.scrollTo(0, 0);
        revealPage(my);
      }
    });
  }

  function revealPage(my) {
    const titleChars = Array.from(page.querySelectorAll('.page-title .char'));
    glyphify(titleChars);
    const head = [page.querySelector('.page-eyebrow')];
    const blocks = Array.from(page.querySelectorAll('.block'));

    gsap.fromTo(titleChars,
      { y: () => -window.innerHeight * 0.5 - gsap.utils.random(40, 200), opacity: 0, rotation: () => gsap.utils.random(-45, 45), scale: 0.65 },
      { y: 0, opacity: 1, rotation: 0, scale: 1, duration: 1.05, ease: 'elastic.out(1, 0.6)', stagger: 0.045 });

    gsap.fromTo(head, { y: -26, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.5, ease: 'power3.out', stagger: 0.08, delay: 0.14 });

    gsap.fromTo(blocks,
      { y: () => -window.innerHeight * 0.42 - gsap.utils.random(20, 200), opacity: 0, rotation: () => gsap.utils.random(-7, 7), scale: 0.92 },
      { y: 0, opacity: 1, rotation: 0, scale: 1, duration: 0.9, ease: 'elastic.out(1, 0.72)',
        stagger: { each: 0.06, from: 'start' }, delay: 0.18 });

    setTimeout(() => {
      if (my !== transId) return;
      gsap.set([...titleChars, ...head, ...blocks], { opacity: 1, x: 0, y: 0, rotation: 0, scale: 1 });
    }, 2600);
  }

  function closePage() {
    if (!pageActive) return;
    const my = ++transId;
    const titleChars = Array.from(page.querySelectorAll('.page-title .char'));
    const head = [page.querySelector('.page-eyebrow')];
    const blocks = Array.from(page.querySelectorAll('.block'));
    const all = [...titleChars, ...head, ...blocks];

    gsap.killTweensOf(all);
    gsap.to(all, {
      y: () => window.innerHeight * 0.7 + gsap.utils.random(20, 420),
      opacity: 0, rotation: () => gsap.utils.random(-12, 12),
      duration: 0.42, ease: 'back.in(1.5)', stagger: { each: 0.014, from: 'end' },
      onComplete: () => {
        if (my !== transId) return;
        document.body.classList.remove('viewing');
        page.innerHTML = '';
        stage.style.display = '';
        window.scrollTo(0, 0);
        openKey = null;
        homeIn(my);
      }
    });
  }

  function homeIn(my) {
    gsap.killTweensOf(chars); gsap.killTweensOf(cards);
    gsap.fromTo(chars,
      { y: () => -window.innerHeight * 0.55 - gsap.utils.random(20, 180), opacity: 0, rotation: () => gsap.utils.random(-50, 50), scale: 0.65 },
      { y: 0, opacity: 1, rotation: 0, scale: 1, duration: 1.0, ease: 'elastic.out(1, 0.6)', stagger: 0.04 });
    gsap.fromTo(cards,
      { y: () => -window.innerHeight * 0.6, opacity: 0, scale: 0.7, rotation: () => (Math.random() < 0.5 ? -20 : 20) },
      { y: 0, opacity: 1, scale: 1, rotation: (i, el) => parseFloat(el.dataset.rot) || 0,
        duration: 1.15, ease: 'elastic.out(1, 0.6)', stagger: 0.08,
        onComplete: () => {
          if (my !== transId) return;
          pageActive = false;
          resetWiggle();
          remeasure();
        } });
  }

  cards.forEach(card => card.addEventListener('click', () => openPage(card.dataset.key)));
  pageBack.addEventListener('click', closePage);
  page.addEventListener('click', e => {
    const btn = e.target.closest('.cta-btn[data-notice]');
    if (!btn) return;
    const note = btn.parentElement.querySelector('.cta-notice');
    if (note) {
      note.textContent = btn.dataset.notice;
      note.hidden = false;
      setTimeout(() => note.classList.add('is-shown'), 16);
    }
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && pageActive) closePage();
  });

  // The browser freezes requestAnimationFrame (and therefore GSAP's ticker)
  // while the tab is in the background. Letters and cards default to opacity:0
  // in CSS and are only revealed by GSAP, so leaving the tab mid-reveal can
  // strand them invisible. On return, finish the entrance if it never ran and
  // fast-forward any in-flight reveal to its end so the visible state is
  // always restored (progress(1) also fires the callbacks that settle state).
  const settleVisible = () => {
    if (!window.gsap) return;
    if (!entered) finishEntrance();
    const els = chars.concat(cards,
      page ? Array.from(page.querySelectorAll('.page-title .char, .page-eyebrow, .block')) : []);
    gsap.getTweensOf(els).forEach(t => { try { t.progress(1); } catch (e) {} });
  };
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') settleVisible();
  });
  window.addEventListener('pageshow', e => { if (e.persisted) settleVisible(); });

  function boot() {
    glyphifyLine(document.getElementById('logo'));
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      gsap.set(chars, { y: 0, opacity: 1, rotation: 0, scale: 1 });
      gsap.set(cards, { y: 0, opacity: 1, rotation: 0, scale: 1 });
      entered = true;
      recordAll();
      start();
    } else {
      transitionIn();
    }
  }

  const fontsReady = (document.fonts && document.fonts.ready)
    ? Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 900))])
    : Promise.resolve();
  Promise.all([fontsReady, templatesReady]).then(boot);
})();
