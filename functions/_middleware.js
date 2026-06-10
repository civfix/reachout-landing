// Cloudflare Pages Function middleware — runs on every request.
//
// Why this exists:
// In production this project's Pages deployment does NOT run Cloudflare's built-in
// 404.html fallback. An unmatched route comes back as "HTTP 404" with an *empty body*
// instead of our page. (Verified against the live site: /404 serves the full page, but
// /asdfklja returned a zero-length 404. We are not in SPA mode — that would serve the
// homepage with a 200, not an empty 404 — and a redeploy did not change it.)
//
// This middleware passes every request through to the normal static-asset server via
// context.next() (so clean URLs like /about -> about.html, redirects and headers behave
// exactly as before) and ONLY when that yields a 404 does it return our real 404.html
// with a 404 status. Every non-404 response is returned untouched, so it cannot change
// how a working route is served. If anything in the override throws, we fall back to the
// original response — never worse than today.
//
// This lives in /functions (NOT in the asset directory), so `wrangler pages deploy dist`
// bundles it as a Pages Function and it never gets uploaded as a public asset.
export async function onRequest(context) {
  const response = await context.next();

  if (!response || response.status !== 404) return response;

  try {
    const page = await context.env.ASSETS.fetch(new URL('/404', context.request.url));
    if (page.ok) {
      return new Response(page.body, {
        status: 404,
        statusText: 'Not Found',
        headers: {
          'content-type': 'text/html; charset=utf-8',
          'cache-control': 'no-store',
          'x-reachout-404': 'middleware',
        },
      });
    }
  } catch (err) {
    // env.ASSETS unavailable or fetch failed -> fall through to the original 404.
  }

  return response;
}
