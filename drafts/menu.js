/* Turns the nav into a "Menu" button on phones.
   Without JavaScript the links simply stay visible, so nothing breaks. */
(function () {
  var btn = document.querySelector('.menu-toggle');
  var nav = document.getElementById('main-nav');
  if (!btn || !nav) return;
  var phone = window.matchMedia('(max-width: 760px)');

  function setOpen(open) {
    btn.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
  }
  function sync() {
    btn.hidden = !phone.matches;
    setOpen(!phone.matches);
  }
  btn.addEventListener('click', function () {
    setOpen(btn.getAttribute('aria-expanded') !== 'true');
  });
  nav.addEventListener('click', function (e) {
    if (phone.matches && e.target.closest('a')) setOpen(false);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && phone.matches && nav.classList.contains('is-open')) {
      setOpen(false);
      btn.focus();
    }
  });
  phone.addEventListener('change', sync);
  sync();
})();
