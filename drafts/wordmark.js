/* ==========================================================
   civfix wordmark: draws every "civfix" in the page's main
   content in the colorful civfix logo style (lowercase, one
   color per letter). Links stay links: the word is restyled
   inside the link, not replaced.
   It still reads, and copies, as the plain word "civfix".
   Left alone: buttons (rainbow letters would clash with the
   button colors), the menu and footer, which stay plain
   so navigation looks the same on every page, and decoration
   hidden from screen readers (like the tear-off tabs), and
   anything inside .no-wordmark (e.g. copy-ready press text).
   Styles: .cf-word in home.css.
   ========================================================== */
(function () {
  'use strict';

  var main = document.getElementById('main');
  if (!main) return;

  // The six letters sit side by side with no spaces, so they still read
  // (and copy/paste) as the single word "civfix".
  function wordmark() {
    var outer = document.createElement('span');
    outer.className = 'cf-word';
    'civfix'.split('').forEach(function (ch, i) {
      var s = document.createElement('span');
      s.className = 's' + (i + 1);
      s.textContent = ch;
      outer.appendChild(s);
    });
    return outer;
  }

  var walker = document.createTreeWalker(main, NodeFilter.SHOW_TEXT, {
    acceptNode: function (node) {
      if (!/civfix/i.test(node.nodeValue)) return NodeFilter.FILTER_REJECT;
      // skip buttons, navigation, and decoration (e.g. the flyer's sideways tear-off tabs)
      if (node.parentElement.closest('.btn, .cf-word, .no-wordmark, nav, [aria-hidden="true"], script, style, textarea')) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    }
  });
  var found = [];
  while (walker.nextNode()) found.push(walker.currentNode);

  found.forEach(function (node) {
    var parts = node.nodeValue.split(/(civfix)/i);
    var frag = document.createDocumentFragment();
    parts.forEach(function (part) {
      if (/^civfix$/i.test(part)) frag.appendChild(wordmark());
      else if (part) frag.appendChild(document.createTextNode(part));
    });
    node.parentNode.replaceChild(frag, node);
  });
})();
