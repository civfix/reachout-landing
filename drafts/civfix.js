/* ==========================================================
   Civfix page:
   Put the EXAMPLE pins on the map. (The colorful civfix wordmark
   is drawn by wordmark.js, shared by every page.) Positions come from
      civfix-pins.js (made by tools/gen_la_map.py) as percentages
      of the map, so they stay in place at any size. When the map
      comes into view, the pins drop in one after another.
   ========================================================== */
(function () {
  'use strict';

  /* ---------- Example pins on the map ---------- */
  var holder = document.getElementById('map-pins');
  var pins = window.CIVFIX_PINS || [];
  if (!holder || !pins.length) return;

  pins = pins.slice().sort(function (a, b) { return a.y - b.y; });   // drop top to bottom, like rain

  var html = '';
  pins.forEach(function (p, i) {
    var tag = p.tag ? '<span class="mpin-tag">' + p.tag + '</span>' : '';
    html += '<span class="mpin mpin--' + p.type + '" style="--x:' + p.x + '%;--y:' + p.y +
      '%;--d:' + (i * 0.035).toFixed(2) + 's">' + tag + '</span>';
  });
  holder.innerHTML = html;
  window.dispatchEvent(new Event('wiggle:refresh'));

  if ('IntersectionObserver' in window) {
    holder.classList.add('waiting');
    var io = new IntersectionObserver(function (entries) {
      if (entries.some(function (e) { return e.isIntersecting; })) {
        holder.classList.remove('waiting');
        io.disconnect();
      }
    }, { threshold: 0.2 });
    io.observe(holder);
  }
})();
