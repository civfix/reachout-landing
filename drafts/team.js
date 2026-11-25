/* ==========================================================
   Team page: pin lots of little faceless paper people (with arms
   and legs) all over the board, around AND between the team.

   1. Measure the scene, plus the things they must not cover:
      the heading, each team print, and the "It's you" note.
   2. Try lots of random spots (from a fixed "seed", so the layout
      looks hand-placed but is the same every visit).
   3. Keep a spot only if it's clear of those things and not crowding
      another figure. Each figure gets a random pose, color, tilt,
      and sometimes a mirror flip so they face different ways.
   4. Re-place everything when the window width changes.
   Decoration only: the whole crowd is hidden from screen readers.
   ========================================================== */
(function () {
  'use strict';

  var scene = document.getElementById('team-scene');
  var crowd = document.getElementById('crowd');
  if (!scene || !crowd) return;

  // Paper colors that show up well on cork
  var COLORS = ['#E8735F', '#F2A541', '#F6D35B', '#6DBE7B', '#6FB7E0', '#B48DD8', '#FFF4DE', '#3E8E7E'];
  // Poses (see the <symbol>s in team.html); repeated names make that pose more common
  var POSES = ['p-stand', 'p-stand', 'p-walk', 'p-walk', 'p-wave', 'p-cheer'];

  // Small predictable random-number generator (same "seed" -> same layout)
  function rng(seed) {
    return function () {
      seed = (seed * 1664525 + 1013904223) % 4294967296;
      return seed / 4294967296;
    };
  }

  function keepOutAreas(s, pad) {
    var els = scene.querySelectorAll('.team-title, .member, .you-note, .scrap-you');
    return Array.prototype.map.call(els, function (el) {
      var r = el.getBoundingClientRect();
      return { left: r.left - s.left - pad, right: r.right - s.left + pad,
               top: r.top - s.top - pad, bottom: r.bottom - s.top + pad };
    }).filter(function (a) { return a.right > a.left; });   // skip hidden ones
  }

  function place() {
    var rand = rng(20261112);
    var s = scene.getBoundingClientRect();
    var W = s.width, H = s.height;
    var phone = W < 600;

    var areas = keepOutAreas(s, phone ? 6 : 12);
    var blocked = areas.reduce(function (sum, a) { return sum + (a.right - a.left) * (a.bottom - a.top); }, 0);

    // --s is the figure's width; it's 1.5x as tall
    var minSize = phone ? 18 : 22, maxSize = phone ? 26 : 34;
    var edge = 6;
    var placed = [];
    var target = Math.round((W * H - blocked) / (phone ? 1700 : 3000));
    target = Math.max(12, Math.min(target, phone ? 80 : 180));

    for (var tries = 0; tries < 12000 && placed.length < target; tries++) {
      var size = minSize + rand() * (maxSize - minSize);
      var half = size / 2, tall = size * 0.75;
      var x = edge + half + rand() * (W - 2 * (edge + half));
      var y = edge + tall + rand() * (H - 2 * (edge + tall));

      var hit = false;
      for (var a = 0; a < areas.length; a++) {
        var k = areas[a];
        if (x + half > k.left && x - half < k.right && y + tall > k.top && y - tall < k.bottom) { hit = true; break; }
      }
      if (hit) continue;

      var ok = true;
      for (var i = 0; i < placed.length; i++) {
        var p = placed[i];
        if (Math.abs(p.x - x) < (p.size + size) * 0.55 && Math.abs(p.y - y) < (p.size + size) * 0.7) { ok = false; break; }
      }
      if (!ok) continue;
      placed.push({ x: x, y: y, size: size });
    }

    // Draw top-to-bottom so figures lower on the board overlap the ones above, like a crowd
    placed.sort(function (a, b) { return a.y - b.y; });

    var html = '';
    placed.forEach(function (p, i) {
      var color = COLORS[Math.floor(rand() * COLORS.length)];
      var pose = POSES[Math.floor(rand() * POSES.length)];
      var tilt = (rand() * 14 - 7).toFixed(1);
      var flip = rand() < 0.5 ? -1 : 1;
      html += '<span class="vol" style="left:' + p.x.toFixed(0) + 'px;top:' + p.y.toFixed(0) +
        'px;--s:' + p.size.toFixed(0) + 'px;--c:' + color + ';--tilt:' + tilt + 'deg;--flip:' + flip +
        ';--d:' + (0.05 + i * 0.008).toFixed(2) + 's"><svg viewBox="0 0 40 60"><use href="#' + pose + '"/></svg></span>';
    });
    crowd.innerHTML = html;

    // Tell wiggle.js there are new things to wiggle
    window.dispatchEvent(new Event('wiggle:refresh'));
  }

  var lastWidth = 0, timer = null;
  function onResize() {
    var w = scene.getBoundingClientRect().width;
    if (Math.abs(w - lastWidth) < 2) return;   // ignore height-only changes (phone toolbars)
    lastWidth = w;
    clearTimeout(timer);
    timer = setTimeout(place, 120);
  }

  lastWidth = scene.getBoundingClientRect().width;
  place();
  window.addEventListener('resize', onResize);
  // Fonts and photos change sizes a little once they load; re-place once they're ready.
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(place);
  window.addEventListener('load', place);
})();
