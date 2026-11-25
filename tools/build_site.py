# -*- coding: utf-8 -*-
"""
Build the live website (dist/) from the editable drafts (drafts/).

    python3 tools/build_site.py

What it does:
  1. Turns each draft page into a live page with a clean address
     (drafts/team.html -> dist/team.html, served at reachoutla.org/team).
  2. Removes draft-only things: the yellow "Draft" banner, the
     "don't index me" tag, and "(draft)" in titles.
  3. Adds search and social-sharing info to every page: description,
     canonical address, Open Graph / Twitter preview tags, and on the
     homepage the organization details Google reads.
  4. Rewrites every link and file path so pages work from any address.
  5. Copies styles, scripts, images and the press kit into dist/.
  6. Writes sitemap.xml, robots.txt and _redirects (old /mission and /help).
  7. Removes old-site files the new pages don't use.

Edit the drafts, run this again, and dist/ is rebuilt from scratch.
Nothing here deploys anything: Cloudflare publishes dist/ only when
changes are merged into the main branch.
"""
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRAFTS = os.path.join(ROOT, "drafts")
DIST = os.path.join(ROOT, "dist")
SITE = "https://www.reachoutla.org"
DEFAULT_OG = "/assets/img/og-image.jpg"
OG_ALT = "The Reach Out LA bulletin board, with the REACH OUT LA sign standing on hills above Los Angeles."

# draft file -> (output file in dist, address, title, description, type, publish date, og image)
PAGES = {
    "home.html": ("index.html", "/", "Reach Out LA",
        "Reach Out LA is a Los Angeles 501(c)(3) nonprofit that uses software and research to connect residents with each other and their local governments.",
        "website", None, None),
    "about.html": ("about.html", "/about", "About | Reach Out LA",
        "Who we are: a nonprofit that started with high school students on Skid Row and now runs civfix and an unhoused research program.",
        "website", None, None),
    "team.html": ("team.html", "/team", "Team | Reach Out LA",
        "Meet the team behind Reach Out LA and civfix, and the volunteers who make the work possible.",
        "website", None, None),
    "civfix.html": ("civfix.html", "/civfix", "civfix | Reach Out LA",
        "civfix is our resident reporting and volunteer hub: report a problem in under a minute, see what neighbors are flagging, and join or host a cleanup.",
        "website", None, "/images/updates/civfix-logo.png"),
    "updates.html": ("updates.html", "/updates", "Updates | Reach Out LA",
        "News, research and announcements from Reach Out LA.",
        "website", None, None),
    "press.html": ("press.html", "/press", "Press | Reach Out LA",
        "Press kit for Reach Out LA: media contact, descriptions, fast facts, the civfix logo, photos with credits, and headshots.",
        "website", None, None),
    "update-311-app.html": ("updates/better-311-app.html", "/updates/better-311-app",
        "Reach Out LA receives $10,000 to build a better 311 app | Reach Out LA",
        "A one-time donation will fund civfix, a third-party 311 app that is easier to use in any city and shows how long reports take to get fixed in richer and poorer neighborhoods.",
        "article", "2026-05-19", None),
    "update-charter-assembly.html": ("updates/charter-assembly.html", "/updates/charter-assembly",
        "Unhoused Angelenos get a seat at the table in LA’s charter rewrite | Reach Out LA",
        "Reach Out LA partnered with Rewrite LA to bring unhoused representation to the 2026 Los Angeles City Charter Civic Assembly.",
        "article", "2026-03-09", "/images/updates/charter-outreach-volunteer.jpg"),
    "update-civfix-launch.html": ("updates/civfix-launch.html", "/updates/civfix-launch",
        "Reach Out launches civfix: the global volunteer hub | Reach Out LA",
        "Report a problem in under a minute, see what your neighbors are flagging, and join or host a cleanup, all in one app on iPhone, Android and the web.",
        "article", "2026-09-25", "/images/updates/civfix-logo.png"),
    "404.html": ("404.html", None, "Page not found | Reach Out LA",
        "This page isn’t on the board.", "website", None, None),
}

# How draft page links become live addresses
LINKS = {draft: info[1] for draft, info in PAGES.items() if info[1]}

CSS = ["home.css", "article.css", "team.css", "civfix.css", "press.css"]
JS = ["menu.js", "wordmark.js", "wiggle.js", "team.js", "team-bios.js", "civfix.js", "civfix-pins.js", "press.js"]
IMG = ["hills.svg", "la-map.svg"]

REDIRECTS = [
    ("/mission", "/about", 301),     # old founder's message page
    ("/help", "/#get-involved", 301),  # old "Help Us" page
]

# Old-site files the new site doesn't use
OLD_FILES = ["app.js", "content.js", "router.js", "image-slot.js", "styles.css", "vendor",
             "mission.html", "help.html", "images/__wtest.txt"]


def fail(msg):
    sys.exit("BUILD FAILED: " + msg)


def map_ref(value, draft):
    """Turn a link or file path used in a draft into its live-site address."""
    # external links, in-page links, and addresses that are already live-site paths
    if re.match(r'^(https?:|mailto:|tel:|data:|#|/)', value):
        return value
    # split "page.html?v=3#section" into its path, query (?v=3) and section (#section)
    m = re.match(r'^([^?#]*)(\?[^#]*)?(#.*)?$', value)
    path, query, fragment = m.group(1), m.group(2) or '', m.group(3) or ''

    if path in LINKS:
        target = LINKS[path]
        if target == "/" and fragment:
            return "/" + fragment
        return target + fragment
    if path.startswith("../dist/"):
        return "/" + path[len("../dist/"):] + query
    if path.startswith("images/") or path.startswith("press/"):
        return "/" + path + query
    if path in CSS:
        return "/assets/css/" + path + query
    if path in JS:
        return "/assets/js/" + path + query
    if path in IMG:
        return "/assets/img/" + path + query
    fail("%s links to %r, which the build doesn't know how to publish" % (draft, value))


def seo_block(draft, out, url, title, desc, kind, date, og):
    image = SITE + (og or DEFAULT_OG)
    lines = ['  <meta name="description" content="%s">' % desc]
    if url:
        lines.append('  <link rel="canonical" href="%s%s">' % (SITE, url))
    lines += [
        '  <meta name="theme-color" content="#F3EBDD">',
        '  <link rel="icon" href="/favicon.svg" type="image/svg+xml">',
        '  <meta property="og:type" content="%s">' % kind,
        '  <meta property="og:site_name" content="Reach Out LA">',
        '  <meta property="og:title" content="%s">' % title.replace(" | Reach Out LA", ""),
        '  <meta property="og:description" content="%s">' % desc,
        '  <meta property="og:image" content="%s">' % image,
        '  <meta property="og:image:alt" content="%s">' % (OG_ALT if not og else title.replace(" | Reach Out LA", "")),
        '  <meta property="og:locale" content="en_US">',
        '  <meta name="twitter:card" content="summary_large_image">',
    ]
    if url:
        lines.insert(lines.index('  <meta property="og:site_name" content="Reach Out LA">'),
                     '  <meta property="og:url" content="%s%s">' % (SITE, url))
    if date:
        lines.append('  <meta property="article:published_time" content="%s">' % date)
    if draft == "home.html":
        lines.append('''  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": ["NGO", "Organization"],
    "@id": "https://www.reachoutla.org/#organization",
    "name": "Reach Out LA",
    "legalName": "Reach Out Los Angeles INC",
    "alternateName": "Reach Out Los Angeles",
    "url": "https://www.reachoutla.org/",
    "logo": "https://www.reachoutla.org/favicon.svg",
    "image": "https://www.reachoutla.org/assets/img/og-image.jpg",
    "email": "roman@reachoutla.org",
    "description": "%s",
    "foundingDate": "2024-12",
    "foundingLocation": "Los Angeles, California",
    "address": { "@type": "PostalAddress", "streetAddress": "3214 Veteran Ave", "addressLocality": "Los Angeles", "addressRegion": "CA", "postalCode": "90034", "addressCountry": "US" },
    "nonprofitStatus": "Nonprofit501c3",
    "taxID": "41-2454206"
  }
  </script>''' % desc)
    return "\n".join(lines)


def build_page(draft, info):
    out, url, title, desc, kind, date, og = info
    src = os.path.join(DRAFTS, draft)
    s = open(src, encoding="utf-8").read()

    # 1. draft-only bits
    s = re.sub(r'\s*<!-- DRAFT:.*?-->', '', s, flags=re.S)
    if draft != "404.html":   # a 404 page should stay out of search results
        s = re.sub(r'\s*<meta name="robots" content="noindex, nofollow">', '', s)
    s = re.sub(r'\s*<p class="draft-banner".*?</p>', '', s, flags=re.S)
    s = re.sub(r'\s*<!-- Add \?campaign=holiday.*?-->', '', s, flags=re.S)
    s = re.sub(r'<title>.*?</title>', '<title>%s</title>' % title, s, flags=re.S)

    # 2. search + social info, right after the viewport tag
    m = re.search(r'<meta name="viewport"[^>]*>\n', s)
    if not m:
        fail(draft + " has no viewport tag")
    s = s[:m.end()] + seo_block(draft, out, url, title, desc, kind, date, og) + "\n" + s[m.end():]

    # 3. links and file paths
    s = re.sub(r'(href|src)="([^"]+)"', lambda mm: '%s="%s"' % (mm.group(1), map_ref(mm.group(2), draft)), s)

    if "draft" in re.sub(r'<!--.*?-->', '', s, flags=re.S).lower().split("</head>")[0] and draft != "404.html":
        fail(draft + " still mentions 'draft' in its <head>")
    dest = os.path.join(DIST, out)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8").write(s)
    return out


def copy(src, dest):
    if os.path.isdir(src):
        shutil.copytree(src, dest)
    else:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)


def main():
    # fresh copies of everything the build owns
    for d in ["assets", "updates", "press", "images/team", "images/updates"]:
        shutil.rmtree(os.path.join(DIST, d), ignore_errors=True)
    for f in OLD_FILES:
        p = os.path.join(DIST, f)
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.exists(p):
            os.remove(p)

    for name in CSS:
        copy(os.path.join(DRAFTS, name), os.path.join(DIST, "assets/css", name))
    for name in JS:
        copy(os.path.join(DRAFTS, name), os.path.join(DIST, "assets/js", name))
    for name in IMG:
        copy(os.path.join(DRAFTS, name), os.path.join(DIST, "assets/img", name))
    og_src = os.path.join(ROOT, "tools", "og-image.jpg")
    if os.path.exists(og_src):
        copy(og_src, os.path.join(DIST, "assets/img/og-image.jpg"))
    else:
        print("note: tools/og-image.jpg not found; social preview image missing")
    copy(os.path.join(DRAFTS, "images/team"), os.path.join(DIST, "images/team"))
    copy(os.path.join(DRAFTS, "images/updates"), os.path.join(DIST, "images/updates"))
    copy(os.path.join(DRAFTS, "press"), os.path.join(DIST, "press"))

    built = [build_page(d, info) for d, info in PAGES.items()]

    # sitemap: every public page, articles with their publish dates
    urls = []
    for d, (out, url, title, desc, kind, date, og) in PAGES.items():
        if url:
            urls.append("  <url>\n    <loc>%s%s</loc>\n    <lastmod>%s</lastmod>\n  </url>" % (SITE, url, date or "2026-11-14"))
    open(os.path.join(DIST, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + "\n</urlset>\n")

    open(os.path.join(DIST, "robots.txt"), "w").write(
        "User-agent: *\nAllow: /\n\nSitemap: %s/sitemap.xml\n" % SITE)

    open(os.path.join(DIST, "_redirects"), "w").write(
        "# Old addresses from the previous site. Format: from  to  status\n"
        + "".join("%s %s %d\n" % r for r in REDIRECTS))

    # report images in dist/images that no page uses (old-site leftovers)
    html = "".join(open(os.path.join(DIST, b), encoding="utf-8").read() for b in built)
    unused = [f for f in sorted(os.listdir(os.path.join(DIST, "images")))
              if os.path.isfile(os.path.join(DIST, "images", f)) and ("/images/" + f) not in html]
    for f in unused:
        os.remove(os.path.join(DIST, "images", f))

    print("built %d pages: %s" % (len(built), ", ".join(built)))
    print("removed unused old images: %s" % (", ".join(unused) or "none"))
    print("wrote sitemap.xml (%d addresses), robots.txt, _redirects (%d)" % (len(urls), len(REDIRECTS)))


if __name__ == "__main__":
    main()
