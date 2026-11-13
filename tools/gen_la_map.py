# -*- coding: utf-8 -*-
"""
Draw a Los Angeles street map for the Civfix page draft from OpenStreetMap data,
plus a set of EXAMPLE pin positions (illustration only, not real reports).

Two modes:

  python3 tools/gen_la_map.py <data folder> --area
      A square box of the LA basin (the default the page uses). No city boundary:
      Civfix works anywhere, so the map just fades out at the edges (done in CSS).
      Reads area-major.json and area-minor.json.

  python3 tools/gen_la_map.py <data folder>
      The City of Los Angeles only, clipped to its boundary with a dashed outline.
      Reads boundary.json, major.json and minor.json.

Output:
  drafts/la-map.svg     the map drawing
  drafts/civfix-pins.js example pin positions (window.CIVFIX_PINS), as % of the map

Map data (c) OpenStreetMap contributors, available under the Open Database
License (ODbL). The page must show that credit wherever the map appears.

Download queries (Overpass API, https://overpass-api.de/api/interpreter):
  area-major.json: way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"](33.94,-118.44,34.16,-118.18);out skel geom qt;
  area-minor.json: way["highway"~"^(residential|unclassified|living_street)$"](33.94,-118.44,34.16,-118.18);out skel geom qt;
  boundary.json:   rel(207359);out geom;
  major.json / minor.json: same filters inside area(3600207359) (the City of LA)
"""
import json
import math
import os
import random
import sys

args = [a for a in sys.argv[1:] if not a.startswith('--')]
AREA_MODE = '--area' in sys.argv
SRC = args[0] if args else '.'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_SVG = os.path.join(ROOT, 'drafts', 'la-map.svg')
OUT_PINS = os.path.join(ROOT, 'drafts', 'civfix-pins.js')

AREA_BOX = (33.94, -118.44, 34.16, -118.18)   # south, west, north, east

W = 1000            # drawing width in SVG units; height follows the shape
PAD = 0 if AREA_MODE else 12
SIMPLIFY = 0.55     # how much to straighten wiggly lines (SVG units); bigger = smaller file
MIN_LEN = 1.2       # drop residential pieces shorter than this (SVG units)


def load(name):
    p = os.path.join(SRC, name)
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


# ---------- the area being drawn ----------
if AREA_MODE:
    s, w, n, e = AREA_BOX
    bounds = {'minlat': s, 'minlon': w, 'maxlat': n, 'maxlon': e}
    rel = None
else:
    rel = load('boundary.json')['elements'][0]
    bounds = rel['bounds']

# ---------- projection: simple equirectangular, fine for one city ----------
LAT0 = (bounds['minlat'] + bounds['maxlat']) / 2
KX = math.cos(math.radians(LAT0))
x_min, x_max = bounds['minlon'] * KX, bounds['maxlon'] * KX
y_min, y_max = -bounds['maxlat'], -bounds['minlat']
SCALE = (W - 2 * PAD) / (x_max - x_min)
H = round((y_max - y_min) * SCALE + 2 * PAD)


def proj(lat, lon):
    return ((lon * KX - x_min) * SCALE + PAD, (-lat - y_min) * SCALE + PAD)


# ---------- line simplification (Douglas-Peucker) ----------
def simplify(pts, tol):
    if len(pts) < 3:
        return pts
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, z = stack.pop()
        ax, ay = pts[a]
        zx, zy = pts[z]
        dx, dy = zx - ax, zy - ay
        seg = math.hypot(dx, dy)
        best, idx = 0, -1
        for i in range(a + 1, z):
            px, py = pts[i]
            if seg < 1e-9:   # closed loop (start == end): measure distance from that point
                d = math.hypot(px - ax, py - ay)
            else:
                d = abs(dy * (px - ax) - dx * (py - ay)) / seg
            if d > best:
                best, idx = d, i
        if best > tol and idx > 0:
            keep[idx] = True
            stack += [(a, idx), (idx, z)]
    return [p for p, k in zip(pts, keep) if k]


def length(pts):
    return sum(math.hypot(x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in zip(pts, pts[1:]))


def path_d(lines, decimals=1):
    """Compact SVG path: absolute move, then relative line steps."""
    f = '%.' + str(decimals) + 'f'
    out = []
    for pts in lines:
        x0, y0 = pts[0]
        px, py = round(x0, decimals), round(y0, decimals)
        steps = []
        for x, y in pts[1:]:
            rx, ry = round(x, decimals), round(y, decimals)
            steps.append((f % (rx - px)) + ',' + (f % (ry - py)))
            px, py = rx, ry
        out.append('M' + (f % x0) + ',' + (f % y0) + 'l' + ' '.join(steps))
    return ''.join(out).replace('.0,', ',').replace('.0 ', ' ').replace('-0,', '0,')


def join_pieces(lines):
    """OpenStreetMap splits streets at intersections. Join pieces that meet end-to-start
    into longer lines: fewer separate pieces = smaller file and no hairline gaps."""
    key = lambda p: (round(p[0], 2), round(p[1], 2))
    starts = {}
    for i, ln in enumerate(lines):
        starts.setdefault(key(ln[0]), []).append(i)
    used = [False] * len(lines)
    out = []
    for i, ln in enumerate(lines):
        if used[i]:
            continue
        used[i] = True
        chain = list(ln)
        while True:
            nxt = None
            for j in starts.get(key(chain[-1]), []):
                if not used[j]:
                    nxt = j
                    break
            if nxt is None:
                break
            used[nxt] = True
            chain += lines[nxt][1:]
        out.append(chain)
    return out


def street_lines(data, min_len=0.0):
    raw = []
    if not data:
        return raw
    for el in data['elements']:
        geom = el.get('geometry')
        if not geom or len(geom) < 2:
            continue
        raw.append([proj(g['lat'], g['lon']) for g in geom if g])
    lines = []
    for pts in join_pieces(raw):
        pts = simplify(pts, SIMPLIFY)
        if length(pts) >= min_len:
            lines.append(pts)
    return lines


# ---------- City of LA boundary (city mode only) ----------
def stitch(ways):
    ways = [list(w) for w in ways if len(w) > 1]
    rings = []
    while ways:
        ring = ways.pop()
        changed = True
        while changed and ring[0] != ring[-1]:
            changed = False
            for i, w in enumerate(ways):
                if w[0] == ring[-1]:
                    ring += w[1:]
                elif w[-1] == ring[-1]:
                    ring += w[-2::-1]
                elif w[-1] == ring[0]:
                    ring = w[:-1] + ring
                elif w[0] == ring[0]:
                    ring = w[:0:-1] + ring
                else:
                    continue
                ways.pop(i)
                changed = True
                break
        rings.append(ring)
    return rings


def ring_pieces(role):
    ways = []
    for m in rel['members']:
        if m['type'] == 'way' and m.get('role') == role and m.get('geometry'):
            ways.append([(g['lat'], g['lon']) for g in m['geometry']])
    return [[proj(lat, lon) for lat, lon in r] for r in stitch(ways)]


def ring_d(rings):
    return ''.join(path_d([simplify(r, SIMPLIFY * 0.5)]) + 'z' for r in rings if len(r) > 2)


def inside(x, y, ring):
    c = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            c = not c
        j = i
    return c


# ---------- streets ----------
prefix = 'area-' if AREA_MODE else ''
minor = street_lines(load(prefix + 'minor.json'), MIN_LEN)   # only tiny residential bits get dropped
major = street_lines(load(prefix + 'major.json'))

svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (W, H, W, H)]
if AREA_MODE:
    svg.append('<!-- Los Angeles area streets. Map data (c) OpenStreetMap contributors, ODbL. -->')
    svg.append('<g fill="none" stroke-linecap="round" stroke-linejoin="round">')
else:
    outer, inner = ring_pieces('outer'), ring_pieces('inner')
    city_d = ring_d(outer) + ring_d(inner)
    svg.append('<!-- City of Los Angeles. Map data (c) OpenStreetMap contributors, ODbL. -->')
    svg.append('<defs><clipPath id="city"><path clip-rule="evenodd" d="%s"/></clipPath></defs>' % city_d)
    svg.append('<path d="%s" fill="#F1E6CF" fill-rule="evenodd"/>' % city_d)
    svg.append('<g clip-path="url(#city)" fill="none" stroke-linecap="round" stroke-linejoin="round">')
if minor:
    svg.append('<path d="%s" stroke="#B8AB96" stroke-width=".55"/>' % path_d(minor))
if major:
    svg.append('<path d="%s" stroke="#7E7262" stroke-width="1.3"/>' % path_d(major))
svg.append('</g>')
if not AREA_MODE:
    svg.append('<path d="%s" fill="none" stroke="#A8322B" stroke-width="1.6" stroke-dasharray="6 4" fill-rule="evenodd"/>' % city_d)
svg.append('</svg>')

with open(OUT_SVG, 'w') as f:
    f.write(''.join(svg))

# ---------- EXAMPLE pins (illustration only, not real reports) ----------
rnd = random.Random(90012)
CATS = ['Illegal dumping', 'Graffiti', 'Pothole', 'Broken streetlight', 'Overgrown brush', 'Broken sidewalk']

if AREA_MODE:
    # Pins sit on real streets, away from the faded edges of the map
    spots = [p for ln in (minor + major) for p in ln
             if W * 0.08 < p[0] < W * 0.92 and H * 0.08 < p[1] < H * 0.92]

    def candidate():
        return rnd.choice(spots)
else:
    outer = outer if not AREA_MODE else []

    def candidate():
        while True:
            x, y = rnd.uniform(PAD, W - PAD), rnd.uniform(PAD, H - PAD)
            if any(inside(x, y, r) for r in outer) and not any(inside(x, y, r) for r in inner):
                return x, y

pins = []
want = {'report': 44, 'cleanup': 16}
for kind, count in want.items():
    tries = 0
    while sum(1 for p in pins if p['type'] == kind) < count and tries < 20000:
        tries += 1
        x, y = candidate()
        if any(math.hypot(x - p['_x'], y - p['_y']) < 30 for p in pins):
            continue
        pin = {'type': kind, '_x': x, '_y': y}
        if kind == 'report':
            pin['cat'] = rnd.choice(CATS)
        pins.append(pin)

# Label a few pins with a little paper tag. A tag sticks out to the right of its pin,
# so only use pins with clear space there (no other pin, no other tag).
TAG_W, TAG_H = W * 0.23, H * 0.06   # generous: tags look bigger on small screens


def tag_box(p):
    return (p['_x'] + 4, p['_y'] - TAG_H - 6, p['_x'] + 4 + TAG_W, p['_y'] + 2)


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def room_for_tag(p, taken):
    box = tag_box(p)
    if box[2] > W * 0.95:
        return False
    for q in pins:
        if q is not p and box[0] - 8 < q['_x'] < box[2] + 8 and box[1] - 18 < q['_y'] < box[3] + 8:
            return False
    return not any(overlaps(box, t) for t in taken)


taken = []
for kind, count in (('cleanup', 3), ('report', 6)):   # cleanups pick first so both kinds get labels
    group = [p for p in pins if p['type'] == kind]
    rnd.shuffle(group)
    for p in group:
        if sum(1 for q in pins if q['type'] == kind and 'tag' in q) >= count:
            break
        if room_for_tag(p, taken):
            p['tag'] = p['cat'] if kind == 'report' else 'Cleanup'
            taken.append(tag_box(p))

out = []
for p in pins:
    item = {'type': p['type'], 'x': round(p['_x'] / W * 100, 2), 'y': round(p['_y'] / H * 100, 2)}
    if 'cat' in p:
        item['cat'] = p['cat']
    if 'tag' in p:
        item['tag'] = p['tag']
    out.append(item)

with open(OUT_PINS, 'w') as f:
    f.write('// EXAMPLE pins for the Civfix page map (illustration only, not real reports).\n')
    f.write('// Made by tools/gen_la_map.py. x/y are percentages of the map image.\n')
    f.write('window.CIVFIX_PINS = ' + json.dumps(out) + ';\n')

print('%s map: %dx%d, minor %d, major %d lines, %d KB; pins: %d' % (
    'area' if AREA_MODE else 'city', W, H, len(minor), len(major),
    os.path.getsize(OUT_SVG) // 1024, len(out)))
