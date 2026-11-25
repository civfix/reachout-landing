# -*- coding: utf-8 -*-
"""
Preview the live site (dist/) on your Mac, behaving like Cloudflare:
  - clean addresses: /team serves team.html, /updates/civfix-launch serves updates/civfix-launch.html
  - redirects from dist/_redirects (e.g. /mission -> /about)
  - missing pages get the site's 404 page with a 404 status

    python3 tools/serve.py          then open http://localhost:8790
    python3 tools/serve.py 9000     to use another port

Press Control + C to stop it.
"""
import http.server
import os
import socketserver
import sys
import urllib.parse

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8790


def load_redirects():
    rules = {}
    path = os.path.join(ROOT, "_redirects")
    if os.path.exists(path):
        for line in open(path):
            parts = line.split()
            if len(parts) >= 2 and not line.startswith("#"):
                rules[parts[0]] = (parts[1], int(parts[2]) if len(parts) > 2 else 302)
    return rules


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")   # always show the newest files while previewing
        super().end_headers()

    def do_GET(self):
        url = urllib.parse.urlsplit(self.path)
        path = url.path
        redirects = load_redirects()
        for key in (path, path.rstrip("/")):
            if key in redirects:
                target, code = redirects[key]
                self.send_response(code)
                self.send_header("Location", target)
                self.end_headers()
                return
        if path in ("/_redirects",):
            return self.not_found()
        local = os.path.join(ROOT, path.lstrip("/"))
        if path.endswith("/") and os.path.isfile(os.path.join(local, "index.html")):
            return super().do_GET()
        if os.path.isfile(local):
            return super().do_GET()
        if os.path.isfile(local.rstrip("/") + ".html"):
            self.path = path.rstrip("/") + ".html" + (("?" + url.query) if url.query else "")
            return super().do_GET()
        return self.not_found()

    def not_found(self):
        body = open(os.path.join(ROOT, "404.html"), "rb").read()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass   # keep the terminal quiet


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("Previewing dist/ at http://localhost:%d  (Control + C to stop)" % PORT)
    httpd.serve_forever()
