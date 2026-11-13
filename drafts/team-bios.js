/* ==========================================================
   Team page bios: clicking a team print (or its "Read bio"
   button) opens that person's bio as a pinned paper note.
   Uses the browser's built-in <dialog>, which already handles
   the keyboard: Escape closes it, and focus goes back to the
   button that opened it.
   ========================================================== */
(function () {
  'use strict';

  function open(id) {
    var d = document.getElementById(id);
    if (d && typeof d.showModal === 'function' && !d.open) d.showModal();
  }

  // "Read bio" buttons
  document.querySelectorAll('.bio-btn').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      open(btn.getAttribute('data-bio'));
    });
  });

  // Clicking anywhere on a print with a bio does the same (mouse/touch convenience;
  // keyboard users use the button, which is already focusable)
  document.querySelectorAll('.member.has-bio').forEach(function (card) {
    card.addEventListener('click', function () {
      var btn = card.querySelector('.bio-btn');
      if (btn) btn.click();
    });
  });

  // A link like team.html#bio-roman opens that bio straight away (handy for sharing)
  if (/^#bio-[a-z]+$/.test(location.hash)) open(location.hash.slice(1));

  document.querySelectorAll('.bio-dialog').forEach(function (d) {
    d.querySelector('.bio-close').addEventListener('click', function () { d.close(); });
    // a click on the dimmed area outside the note closes it
    d.addEventListener('click', function (e) {
      if (e.target !== d) return;
      var r = d.getBoundingClientRect();
      var inside = e.clientX >= r.left && e.clientX <= r.right && e.clientY >= r.top && e.clientY <= r.bottom;
      if (!inside) d.close();
    });
  });
})();
