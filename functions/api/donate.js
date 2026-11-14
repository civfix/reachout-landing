// Cloudflare Pages Function: /api/donate
//
// This is server code. It runs on Cloudflare, never in the visitor's browser,
// which is why it is allowed to use the Stripe SECRET key.
//
//   GET  /api/donate                    -> { publishableKey }  (public by design)
//   GET  /api/donate?session_id=cs_...  -> { status, amountTotal, currency, mode }
//   POST /api/donate  { amount, frequency, campaign, page }
//                                      -> { clientSecret }    (starts a Stripe Checkout Session)
//
// Keys come from Cloudflare "environment variables", never from files in this repo
// (the repo is public):
//   STRIPE_SECRET_KEY       sk_test_... while testing, sk_live_... only when launching
//   STRIPE_PUBLISHABLE_KEY  pk_test_... / pk_live_...
// Locally they live in a .dev.vars file, which .gitignore keeps out of git.

// Pin the Stripe API version so a change to the account's default can't break this.
// "embedded_page" (the on-site payment form) needs 2026-03-25.dahlia or later.
const STRIPE_VERSION = '2026-03-25.dahlia';

const MIN_DOLLARS = 5;
const MAX_DOLLARS = 25000;

// Campaigns this page can run. Anything else is rejected, so nobody can make up
// their own product name or description by editing the request.
const CAMPAIGNS = {
  general: {
    productName: 'Donation to Reach Out Los Angeles',
    designation: 'General support',
  },
  holiday: {
    productName: 'Holiday gift for civfix, a program of Reach Out Los Angeles',
    designation: 'civfix program',
  },
};

// Pages allowed to receive donors back after paying.
const RETURN_PAGES = ['/donate', '/drafts/donate.html'];

const TAX_NOTE =
  'Reach Out Los Angeles INC is a 501(c)(3) nonprofit organization, EIN 41-2454206. ' +
  'Your gift is tax-deductible to the extent allowed by law.';

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
  });
}

function keysProblem(env, request) {
  const key = env.STRIPE_SECRET_KEY || '';
  if (!key) return 'Donations are not set up yet (missing STRIPE_SECRET_KEY).';
  // Safety net: never let a laptop preview charge real cards.
  const host = new URL(request.url).hostname;
  const isLocal = host === 'localhost' || host === '127.0.0.1' || host.endsWith('.localhost');
  if (isLocal && key.startsWith('sk_live_')) {
    return 'A live Stripe key is being used on a local preview. Use your sk_test_ key locally.';
  }
  return null;
}

async function stripe(env, method, path, params) {
  const res = await fetch('https://api.stripe.com/v1/' + path, {
    method,
    headers: {
      authorization: 'Bearer ' + env.STRIPE_SECRET_KEY,
      'stripe-version': STRIPE_VERSION,
      ...(params ? { 'content-type': 'application/x-www-form-urlencoded' } : {}),
    },
    body: params ? params.toString() : undefined,
  });
  const data = await res.json();
  if (!res.ok) {
    // Details go to Cloudflare's logs for us; the donor sees a friendly message.
    console.error('Stripe error', res.status, data && data.error && data.error.message);
    throw new Error('stripe');
  }
  return data;
}

// GET: publishable key, or the result of a finished donation
export async function onRequestGet({ request, env }) {
  const problem = keysProblem(env, request);
  if (problem) return json({ error: problem }, 503);

  const sessionId = new URL(request.url).searchParams.get('session_id');
  if (!sessionId) {
    if (!env.STRIPE_PUBLISHABLE_KEY) return json({ error: 'Missing STRIPE_PUBLISHABLE_KEY.' }, 503);
    return json({ publishableKey: env.STRIPE_PUBLISHABLE_KEY });
  }

  if (!/^cs_(test|live)_[A-Za-z0-9]+$/.test(sessionId)) return json({ error: 'Invalid session.' }, 400);
  try {
    const s = await stripe(env, 'GET', 'checkout/sessions/' + encodeURIComponent(sessionId));
    // Only what the thank-you note needs. No names, emails or card details.
    return json({ status: s.status, amountTotal: s.amount_total, currency: s.currency, mode: s.mode });
  } catch {
    return json({ error: 'We could not look up that donation.' }, 502);
  }
}

// POST: start a Checkout Session for the chosen amount
export async function onRequestPost({ request, env }) {
  const problem = keysProblem(env, request);
  if (problem) return json({ error: problem }, 503);

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'Bad request.' }, 400);
  }

  // Never trust numbers from the browser: check everything again here.
  const dollars = Number(body.amount);
  if (!Number.isInteger(dollars) || dollars < MIN_DOLLARS || dollars > MAX_DOLLARS) {
    return json({ error: `Please choose a whole-dollar amount from $${MIN_DOLLARS} to $${MAX_DOLLARS.toLocaleString('en-US')}.` }, 400);
  }
  const monthly = body.frequency === 'monthly';
  const campaignKey = Object.hasOwn(CAMPAIGNS, body.campaign) ? body.campaign : 'general';
  const campaign = CAMPAIGNS[campaignKey];
  const page = RETURN_PAGES.includes(body.page) ? body.page : RETURN_PAGES[0];

  const origin = new URL(request.url).origin;
  const returnUrl =
    origin + page + '?session_id={CHECKOUT_SESSION_ID}' + (campaignKey !== 'general' ? '&campaign=' + campaignKey : '');

  const p = new URLSearchParams();
  p.set('ui_mode', 'embedded_page');
  p.set('mode', monthly ? 'subscription' : 'payment');
  p.set('return_url', returnUrl);
  p.set('line_items[0][quantity]', '1');
  p.set('line_items[0][price_data][currency]', 'usd');
  p.set('line_items[0][price_data][unit_amount]', String(dollars * 100));
  p.set('line_items[0][price_data][product_data][name]', campaign.productName + (monthly ? ' (monthly)' : ''));
  if (monthly) p.set('line_items[0][price_data][recurring][interval]', 'month');
  if (!monthly) p.set('submit_type', 'donate'); // the button says "Donate" instead of "Pay"
  p.set('custom_text[submit][message]', TAX_NOTE);
  // Labels for our own bookkeeping, visible in the Stripe Dashboard
  p.set('metadata[campaign]', campaignKey);
  p.set('metadata[designation]', campaign.designation);
  if (monthly) {
    p.set('subscription_data[metadata][campaign]', campaignKey);
    p.set('subscription_data[metadata][designation]', campaign.designation);
  } else {
    p.set('payment_intent_data[metadata][campaign]', campaignKey);
    p.set('payment_intent_data[metadata][designation]', campaign.designation);
  }

  try {
    const session = await stripe(env, 'POST', 'checkout/sessions', p);
    return json({ clientSecret: session.client_secret });
  } catch {
    return json({ error: 'The payment form could not be started. Please try again in a moment.' }, 502);
  }
}
