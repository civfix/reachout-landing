# -*- coding: utf-8 -*-
"""
Draw the City of Los Angeles street map for the Civfix page draft, from
OpenStreetMap data, plus a set of EXAMPLE pin positions inside the city.

  python3 tools/gen_la_map.py <folder with the .json files>

Input files (downloaded from the Overpass API, see the notes at the bottom):
  boundary.json  the City of Los Angeles boundary (relation 207359)
  major.json     motorway / trunk / primary / secondary / tertiary roads
  minor.json     residential / unclassified / living_street roads   (optional)
  freeway.json   motorway / trunk roads with tags                   (optional)

Output:
  drafts/la-map.svg     the map drawing
  drafts/civfix-pins.js example pin positions (window.CIVFIX_PINS), as % of the map

Map data (c) OpenStreetMap contributors, available under the Open Database
License (ODbL). The page must show that credit wherever the map appears.
"""
import json
import math
import os
import random
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else '.'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_SVG = os.path.join(ROOT, 'drafts', 'la-map.svg')
OUT_PINS = os.path.join(ROOT, 'drafts', 'civfix-pins.js')

W = 1000            # drawing width in SVG units; height follows the city's shape
PAD = 12
SIMPLIFY = 0.55     # how much to straighten wiggly lines (SVG units); bigger = smaller file
MIN_LEN = 1.2       # drop street pieces shorter than this (SVG units)


def load(name):
    p = os.path.join(SRC, name)
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


# ---------- projection: simple equirectangular, good enough for one city ----------
boundary = load('boundary.json')
rel = boundary['elements'][0]
b = rel['bounds']
LAT0 = (b['minlat'] + b['maxlat']) / 2
KX = math.cos(math.radians(LAT0))
x_min, x_max = b['minlon'] * KX, b['maxlon'] * KX
y_min, y_max = -b['maxlat'], -b['minlat']
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
        seg = ['M' + (f % x0) + ',' + (f % y0)]
        px, py = round(x0, decimals), round(y0, decimals)
        steps = []
        for x, y in pts[1:]:
            rx, ry = round(x, decimals), round(y, decimals)
            steps.append((f % (rx - px)) + ',' + (f % (ry - py)))
            px, py = rx, ry
        out.append(seg[0] + 'l' + ' '.join(steps))
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


# ---------- boundary: stitch the outer and inner pieces into closed rings ----------
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


outer = ring_pieces('outer')
inner = ring_pieces('inner')


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


def in_city(x, y):
    return any(inside(x, y, r) for r in outer) and not any(inside(x, y, r) for r in inner)


# ---------- streets ----------
minor = street_lines(load('minor.json'), MIN_LEN)   # only tiny residential bits get dropped
major = street_lines(load('major.json'))
freeway = street_lines(load('freeway.json'))

city_d = ring_d(outer) + ring_d(inner)

svg = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (W, H, W, H),
    '<!-- City of Los Angeles. Map data (c) OpenStreetMap contributors, ODbL. -->',
    '<defs><clipPath id="city"><path clip-rule="evenodd" d="%s"/></clipPath></defs>' % city_d,
    '<path d="%s" fill="#F1E6CF" fill-rule="evenodd"/>' % city_d,
    '<g clip-path="url(#city)" fill="none" stroke-linecap="round" stroke-linejoin="round">',
]
if minor:
    svg.append('<path d="%s" stroke="#B8AB96" stroke-width=".45"/>' % path_d(minor))
if major:
    svg.append('<path d="%s" stroke="#7E7262" stroke-width="1.1"/>' % path_d(major))
if freeway:
    svg.append('<path d="%s" stroke="#E8735F" stroke-width="2.2"/>' % path_d(freeway))
svg.append('</g>')
svg.append('<path d="%s" fill="none" stroke="#A8322B" stroke-width="1.6" stroke-dasharray="6 4" fill-rule="evenodd"/>' % city_d)
svg.append('</svg>')

with open(OUT_SVG, 'w') as f:
    f.write(''.join(svg))

# ---------- EXAMPLE pins (illustration only, not real reports) ----------
rnd = random.Random(90012)
CATS = ['Illegal dumping', 'Graffiti', 'Pothole', 'Broken streetlight', 'Overgrown brush', 'Broken sidewalk']
pins = []
want = {'report': 44, 'cleanup': 16}
for kind, n in want.items():
    tries = 0
    while sum(1 for p in pins if p['type'] == kind) < n and tries < 20000:
        tries += 1
        x, y = rnd.uniform(PAD, W - PAD), rnd.uniform(PAD, H - PAD)
        if not in_city(x, y):
            continue
        if any(math.hypot(x - p['_x'], y - p['_y']) < 26 for p in pins):
            continue
        pin = {'type': kind, '_x': x, '_y': y}
        if kind == 'report':
            pin['cat'] = rnd.choice(CATS)
        pins.append(pin)

# Label a few pins with a little paper tag
for p in rnd.sample([p for p in pins if p['type'] == 'report'], 6):
    p['tag'] = p['cat']
for p in rnd.sample([p for p in pins if p['type'] == 'cleanup'], 3):
    p['tag'] = 'Cleanup'

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

print('map: %dx%d, minor %d, major %d, freeway %d lines, %d KB' % (
    W, H, len(minor), len(major), len(freeway), os.path.getsize(OUT_SVG) // 1024))
print('pins:', len(out))

# Data download notes (Overpass API, https://overpass-api.de/api/interpreter):
#   boundary.json: rel(207359);out geom;
#   major.json:    area(3600207359)->.la;way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"](area.la);out skel geom qt;
#   minor.json:    area(3600207359)->.la;way["highway"~"^(residential|unclassified|living_street)$"](area.la);out skel geom qt;
#   freeway.json:  area(3600207359)->.la;way["highway"~"^(motorway|trunk)$"](area.la);out skel geom qt;
