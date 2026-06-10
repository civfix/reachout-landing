// Cloudflare Pages "Advanced mode" worker.
//
// Why this file exists:
// This project ships a top-level 404.html (reachable at /404), but in PRODUCTION
// Cloudflare does NOT run its automatic custom-404 fallback for this project — an
// unmatched route comes back as "HTTP 404" with an *empty body* instead of our page.
// (Verified against the live site: /404 serves the full page, but /akdslfj returned a
// zero-length 404. A redeploy did not change it, and we are not in SPA mode — SPA mode
// would serve the homepage with a 200, not an empty 404.)
//
// A `_worker.js` in the output directory puts Pages in "Advanced mode": every request
// is served through the normal static-asset infrastructure (env.ASSETS.fetch, so clean
// URLs like /about -> about.html, redirects and headers all behave exactly as before),
// and ONLY when no asset matches do we serve 404.html ourselves with a real 404 status.
// It ships inside dist/, so it applies to both drag-&-drop and `wrangler pages deploy`.
//
// Failure is contained: if anything in the 404 branch throws, we fall back to the
// original response, so this can never make a working route worse.
export default {
  async fetch(request, env) {
    let assetResponse;
    try {
      assetResponse = await env.ASSETS.fetch(request);
    } catch (err) {
      return new Response('Unexpected error serving this page.', {
        status: 500,
        headers: { 'content-type': 'text/plain; charset=utf-8' },
      });
    }

    // Anything that matched an asset (or a redirect) is returned untouched.
    if (assetResponse.status !== 404) return assetResponse;

    // No asset matched -> serve the real 404 page, keeping a 404 status.
    try {
      const page = await env.ASSETS.fetch(new URL('/404', request.url));
      if (page.ok) {
        return new Response(page.body, {
          status: 404,
          statusText: 'Not Found',
          headers: {
            'content-type': 'text/html; charset=utf-8',
            'cache-control': 'no-store',
          },
        });
      }
    } catch (err) {
      // fall through to the original (empty) 404 below — no worse than before
    }

    return assetResponse;
  },
};
