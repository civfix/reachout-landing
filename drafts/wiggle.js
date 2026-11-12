/* ==========================================================
   Wiggle: when the pointer sweeps past, things on the board get
   nudged in the direction it moved and spring back, like the
   current live homepage (dist/app.js).

   Two groups, with the live site's two sets of tuning numbers:
   - the REACH OUT LA letters: lively
   - pinned items (photos, notes, cards, flyers): gentler, like
     the live site's photo cards
   The header and footer stay still so navigation never moves
   under your cursor.

   How it works, once per screen refresh ("frame"):
   1. Work out how far the pointer moved since the last frame
      (its velocity).
   2. For each item, the closer the pointer is, the harder the
      item is pushed along that velocity.
   3. A spring pulls every item back toward its resting spot,
      and friction calms the wobble down.
   The loop stops itself once everything is still, so it doesn't
   use battery when nobody is moving the mouse.

   Items keep their CSS tilt: this script sets the separate
   "translate" and "rotate" properties, which stack on top of the
   tilt in "transform" instead of replacing it.
   ========================================================== */
(function () {
  'use strict';

  // Respect people who have asked their device for less motion.
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var GROUPS = [
    { // the sign letters (live site: amp 10, reach 0.1)
      selector: '.lettering img',
      amp: 10, reach: 0.1, rotK: 0.0025, rotCap: 270, maxRange: Infinity
    },
    { // example pins on the Civfix map: tiny, so they get a minimum reach
      selector: '.mpin',
      amp: 7, reach: 0.1, rotK: 0.0025, rotCap: 270, maxRange: Infinity, minRange: 70
    },
    { // little volunteer cut-outs on the team page: lively, like the letters
      selector: '.vol',
      amp: 9, reach: 0.1, rotK: 0.0025, rotCap: 270, maxRange: Infinity
    },
    { // pinned items (live site's photo cards: amp 3.4, reach 0.05)
      selector: '.hero-note, .hero-photos .photo, .scrap, .letter, .label, .card, .needs-info, .flyer, .member, .you-note',
      amp: 3.4, reach: 0.05, rotK: 0.0016, rotCap: 80,
      maxRange: 600   // tall cards would otherwise react to the pointer from very far away
    }
  ];
  var SPRING = 0.1;      // how hard an item is pulled back home
  var FRICTION = 0.7;    // how quickly the wobble dies down (lower = calmer)

  var items = [];
  function collect() {
    items = [];
    GROUPS.forEach(function (g) {
      document.querySelectorAll(g.selector).forEach(function (el) {
        items.push({ el: el, g: g, x: 0, y: 0, vx: 0, vy: 0, cx: 0, cy: 0, range: 0 });
      });
    });
    if (!running) measure();
  }
  // Other scripts (like team.js) announce when they add or rebuild things to wiggle
  window.addEventListener('wiggle:refresh', function () { collect(); });

  var pointer = { x: 0, y: 0, lastX: 0, lastY: 0, seen: false };

  // Where each item rests, in page coordinates (so scrolling doesn't confuse it).
  function measure() {
    items.forEach(function (d) {
      var b = d.el.getBoundingClientRect();
      d.cx = b.left + window.scrollX + b.width / 2 - d.x;
      d.cy = b.top + window.scrollY + b.height / 2 - d.y;
      d.range = Math.max(Math.min(b.width + b.height, d.g.maxRange), d.g.minRange || 1);
    });
  }

  // 0 when far away, rising smoothly to 1 right on top of the item
  function smoothstep(min, max, v) {
    var t = Math.max(0, Math.min(1, (v - min) / (max - min)));
    return t * t * (3 - 2 * t);
  }

  var running = false;
  var stillFrames = 0;

  function step() {
    var velX = pointer.x - pointer.lastX;
    var velY = pointer.y - pointer.lastY;
    pointer.lastX = pointer.x;
    pointer.lastY = pointer.y;

    var px = pointer.x + window.scrollX;
    var py = pointer.y + window.scrollY;
    var anythingMoving = velX !== 0 || velY !== 0;

    items.forEach(function (d) {
      var g = d.g;
      var distance = Math.hypot(px - d.cx, py - d.cy);
      var push = smoothstep(d.range, 0, distance) * g.reach;

      d.vx += velX * g.amp * push - d.x * SPRING;
      d.vy += velY * g.amp * push - d.y * SPRING;
      d.vx *= FRICTION;
      d.vy *= FRICTION;
      d.x += d.vx;
      d.y += d.vy;

      var r = Math.max(Math.min(g.rotK * (d.x + d.y), g.rotCap), -g.rotCap);
      d.el.style.translate = d.x.toFixed(2) + 'px ' + d.y.toFixed(2) + 'px';
      d.el.style.rotate = r.toFixed(3) + 'deg';

      if (Math.abs(d.x) + Math.abs(d.y) + Math.abs(d.vx) + Math.abs(d.vy) > 0.03) anythingMoving = true;
    });

    stillFrames = anythingMoving ? 0 : stillFrames + 1;
    if (stillFrames > 20) {
      // Everything has settled: snap to rest and stop the loop.
      items.forEach(function (d) {
        d.x = d.y = d.vx = d.vy = 0;
        d.el.style.translate = '';
        d.el.style.rotate = '';
      });
      running = false;
      return;
    }
    requestAnimationFrame(step);
  }

  function start() {
    if (running) return;
    measure();               // everything is at rest here, so this is accurate
    running = true;
    stillFrames = 0;
    requestAnimationFrame(step);
  }

  collect();   // find everything to wiggle on this page

  // "pointermove" covers a mouse, a pen, and a finger dragging on a touchscreen.
  window.addEventListener('pointermove', function (e) {
    if (!pointer.seen) {     // first event: no jump from a made-up starting point
      pointer.lastX = e.clientX;
      pointer.lastY = e.clientY;
      pointer.seen = true;
    }
    pointer.x = e.clientX;
    pointer.y = e.clientY;
    start();
  }, { passive: true });
})();
