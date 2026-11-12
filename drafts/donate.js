/* ==========================================================
   Donate page DRAFT: amount picker + Stripe Embedded Checkout

   Flow:
   1. Donor picks how often and how much, then presses Continue.
   2. We load Stripe's script (only now, not on every page view),
      ask our server (/api/donate) for the public "publishable" key,
      and have Stripe draw its secure payment form inside #checkout.
   3. Stripe asks our server for a one-time "client secret" for this
      exact donation (fetchClientSecret below).
   4. After paying, Stripe sends the donor back to this page with
      ?session_id=... and we show a thank-you note.
   Card details go straight from the donor to Stripe; they never
   touch our page's code or our server.
   ========================================================== */
(function () {
  'use strict';

  var STRIPE_JS = 'https://js.stripe.com/dahlia/stripe.js';
  var MIN = 5, MAX = 25000;
  var CONTACT = 'roman@reachoutla.org';

  var params = new URLSearchParams(location.search);
  var campaign = params.get('campaign') === 'holiday' ? 'holiday' : 'general';

  var form = document.getElementById('donate-form');
  var errorBox = document.getElementById('form-error');
  var otherWrap = document.getElementById('other-wrap');
  var otherInput = document.getElementById('other-input');
  var continueBtn = document.getElementById('continue-btn');
  var checkoutStep = document.getElementById('checkout-step');
  var checkoutTitle = document.getElementById('checkout-title');
  var summary = document.getElementById('checkout-summary');
  var changeBtn = document.getElementById('change-btn');
  var thanks = document.getElementById('thanks');
  var needsInfo = document.querySelector('.donate-needs');

  var checkout = null;      // Stripe's embedded payment form, once created
  var stripePromise = null;

  /* ---------- 1. Campaign: show the right words and theme ---------- */
  document.querySelectorAll('[data-campaign]').forEach(function (el) {
    el.hidden = el.getAttribute('data-campaign') !== campaign;
  });
  if (campaign === 'holiday') {
    document.body.classList.add('theme-holiday');
    document.title = 'Support Civfix this holiday season — Reach Out LA';
  }

  /* ---------- 2. Amount picker ---------- */
  function chosen(name) {
    var el = form.querySelector('input[name="' + name + '"]:checked');
    return el ? el.value : null;
  }

  form.addEventListener('change', function (e) {
    if (e.target.name === 'amount') {
      var other = e.target.value === 'other';
      otherWrap.hidden = !other;
      if (other) otherInput.focus();
    }
    showError('');
  });

  function readAmount() {
    var v = chosen('amount');
    if (v !== 'other') return Number(v);
    var raw = otherInput.value.trim();
    if (!/^\d+$/.test(raw)) return NaN;
    return Number(raw);
  }

  function showError(msg) {
    errorBox.textContent = msg;
    if (msg) otherInput.setAttribute('aria-invalid', String(chosen('amount') === 'other'));
    else otherInput.removeAttribute('aria-invalid');
  }

  function describe(dollars, frequency) {
    var amount = '$' + dollars.toLocaleString('en-US');
    return frequency === 'monthly' ? amount + ' every month' : amount + ' one-time gift';
  }

  /* ---------- 3. Talking to our server and to Stripe ---------- */
  function apiGet(url) {
    return fetch(url, { headers: { accept: 'application/json' } }).then(function (res) {
      return res.json().catch(function () { throw new Error('no-server'); }).then(function (data) {
        if (!res.ok || data.error) throw new Error(data.error || 'server');
        return data;
      });
    });
  }

  function loadStripe() {
    if (stripePromise) return stripePromise;
    stripePromise = new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = STRIPE_JS;
      s.onload = function () { resolve(); };
      s.onerror = function () { reject(new Error('stripe-js')); };
      document.head.appendChild(s);
    }).then(function () {
      return apiGet('/api/donate');
    }).then(function (cfg) {
      return window.Stripe(cfg.publishableKey);
    });
    stripePromise.catch(function () { stripePromise = null; });  // allow a retry later
    return stripePromise;
  }

  function friendly(err) {
    if (err && err.message === 'no-server') {
      return 'The payment server isn’t running on this preview, so the payment form can’t load here. ' +
             '(Expected when previewing with the simple Python server.)';
    }
    if (err && err.message && err.message.length < 200 && !/^(server|stripe-js)$/.test(err.message)) {
      return err.message;
    }
    return 'The payment form couldn’t load. Please try again in a moment, or email ' + CONTACT + '.';
  }

  /* ---------- 4. Continue: show Stripe's form on this page ---------- */
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var dollars = readAmount();
    var frequency = chosen('frequency');

    if (!Number.isInteger(dollars) || dollars < MIN || dollars > MAX) {
      showError('Please enter a whole-dollar amount from $' + MIN + ' to $' + MAX.toLocaleString('en-US') + '.');
      if (chosen('amount') === 'other') otherInput.focus();
      return;
    }

    showError('');
    continueBtn.disabled = true;
    continueBtn.textContent = 'Loading secure payment…';

    loadStripe().then(function (stripe) {
      return stripe.createEmbeddedCheckoutPage({
        fetchClientSecret: function () {
          return fetch('/api/donate', {
            method: 'POST',
            headers: { 'content-type': 'application/json' },
            body: JSON.stringify({ amount: dollars, frequency: frequency, campaign: campaign, page: location.pathname }),
          })
            .then(function (res) { return res.json(); })
            .then(function (data) {
              if (data.error) throw new Error(data.error);
              return data.clientSecret;
            });
        },
      });
    }).then(function (c) {
      checkout = c;
      summary.textContent = describe(dollars, frequency);
      form.hidden = true;
      checkoutStep.hidden = false;
      checkout.mount('#checkout');
      checkoutTitle.focus();
    }).catch(function (err) {
      showError(friendly(err));
    }).then(function () {
      continueBtn.disabled = false;
      continueBtn.textContent = 'Continue to secure payment';
    });
  });

  changeBtn.addEventListener('click', function () {
    if (checkout) { checkout.destroy(); checkout = null; }
    checkoutStep.hidden = true;
    form.hidden = false;
    document.getElementById('form-title').setAttribute('tabindex', '-1');
    document.getElementById('form-title').focus();
  });

  /* ---------- 5. Coming back from Stripe: thank-you note ---------- */
  var sessionId = params.get('session_id');
  if (sessionId) {
    form.hidden = true;
    apiGet('/api/donate?session_id=' + encodeURIComponent(sessionId)).then(function (s) {
      if (s.status === 'complete') {
        var dollars = Math.round((s.amountTotal || 0) / 100);
        var amount = '$' + dollars.toLocaleString('en-US');
        document.getElementById('thanks-text').textContent = s.mode === 'subscription'
          ? 'Your ' + amount + ' monthly gift to Reach Out Los Angeles is set up.'
          : 'Your ' + amount + ' gift to Reach Out Los Angeles went through.';
        thanks.hidden = false;
        if (needsInfo) needsInfo.hidden = true;
        document.getElementById('thanks-title').focus();
      } else {
        form.hidden = false;
        showError('Your payment didn’t go through, so you haven’t been charged. You can try again below.');
      }
    }).catch(function (err) {
      form.hidden = false;
      showError(friendly(err));
    });
  }
})();
