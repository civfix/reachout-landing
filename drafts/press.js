/* ==========================================================
   Press page: "Copy" buttons for the ready-to-use descriptions.
   Copies the exact text and announces "Copied" for screen readers.
   ========================================================== */
(function () {
  'use strict';

  var status = document.querySelector('.copy-status');

  function say(msg) {
    if (!status) return;
    status.textContent = msg;
    clearTimeout(say.t);
    say.t = setTimeout(function () { status.textContent = ''; }, 4000);
  }

  // Fallback for browsers without the Clipboard API: select the text so it can be copied by hand
  function selectText(el) {
    var range = document.createRange();
    range.selectNodeContents(el);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  }

  document.querySelectorAll('.copy-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var el = document.getElementById(btn.getAttribute('data-copy'));
      if (!el) return;
      var text = el.textContent.replace(/\s+/g, ' ').trim();
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(
          function () { say('Copied to your clipboard.'); },
          function () { selectText(el); say('Text selected. Press Cmd+C (or Ctrl+C) to copy.'); }
        );
      } else {
        selectText(el);
        say('Text selected. Press Cmd+C (or Ctrl+C) to copy.');
      }
    });
  });
})();
