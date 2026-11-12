# -*- coding: utf-8 -*-
"""
Generate the layered "cut-paper" LA hills that sit behind the REACH OUT LA sign
on the homepage draft.

Run (from the project folder):  python3 tools/gen_hills.py > drafts/hills.svg
Same SEED -> same drawing every time. Change SEED for a different variation.

Layers, back to front (each one casts a soft shadow, like paper on cork):
  haze       - pale, far-off ridgeline
  far range  - dusty blue-lavender hills
  mid ridge  - sage-green hills with chaparral clumps along the gullies
  near hill  - golden dry-grass hill that the letters stand on, with fire roads
Canvas is 1200 x 400. The near hill's crest is flat-ish from x=140 to x=1060
at y~300, so the letters (spanning ~x 170-1030) look planted on it.
"""
import math
import random

SEED = 11
W, H = 1200, 400
rnd = random.Random(SEED)


def ridge(base, bumps, noise=2.0, step=6):
    """A rolling ridgeline: a base height minus a few smooth bumps, plus a little wiggle."""
    pts = []
    phase = [rnd.uniform(0, 6.28) for _ in range(3)]
    for x in range(-6, W + 7, step):
        y = base
        for (cx, height, width) in bumps:
            y -= height * math.exp(-((x - cx) / width) ** 2)
        y += noise * (math.sin(x * 0.045 + phase[0]) + 0.6 * math.sin(x * 0.11 + phase[1])
                      + 0.3 * math.sin(x * 0.23 + phase[2]))
        pts.append((x, y))
    return pts


def y_at(r, x):
    for (x1, y1), (x2, y2) in zip(r, r[1:]):
        if x1 <= x <= x2:
            return y1 + (x - x1) / (x2 - x1) * (y2 - y1)
    return r[-1][1]


def area(r):
    return "M-6,406 L" + " L".join("%.0f,%.1f" % p for p in r) + " L%d,406 Z" % (W + 6)


def crest(r, dy=1.5):
    return "M" + " L".join("%.0f,%.1f" % (x, y + dy) for x, y in r)


def peaks(r):
    out = []
    for i in range(2, len(r) - 2):
        if r[i][1] <= min(r[i - 2][1], r[i - 1][1], r[i + 1][1], r[i + 2][1]):
            if not out or r[i][0] - out[-1][0] > 50:
                out.append(r[i])
    return out


svg = []
add = svg.append

haze = ridge(200, [(80, 70, 120), (330, 105, 140), (610, 85, 130), (880, 115, 150), (1150, 80, 120)], 3)
far = ridge(250, [(170, 95, 110), (430, 120, 130), (700, 90, 110), (960, 130, 140), (1200, 70, 90)], 3.5)
mid = ridge(292, [(40, 90, 90), (260, 80, 110), (520, 100, 120), (790, 85, 110), (1040, 105, 120), (1210, 70, 80)], 3)


def near_y(x):
    # flat crest from 140 to 1060, easing down to the edges
    if 140 <= x <= 1060:
        y = 300
    elif x < 140:
        t = (140 - x) / 146
        y = 300 + 52 * (1 - math.cos(min(t, 1) * math.pi)) / 2
    else:
        t = (x - 1060) / 146
        y = 300 + 48 * (1 - math.cos(min(t, 1) * math.pi)) / 2
    return y + 1.6 * math.sin(x * 0.05) + 0.8 * math.sin(x * 0.13 + 1)


near = [(x, near_y(x)) for x in range(-6, W + 7, 6)]

add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (W, H, W, H))
add('<defs>')
add('<filter id="lift" x="-5%" y="-20%" width="110%" height="140%">'
    '<feDropShadow dx="0" dy="2.5" stdDeviation="3" flood-color="#2d1908" flood-opacity=".32"/></filter>')
for name, top, bottom in [("g-haze", "#D7D6D6", "#C6C7CC"), ("g-far", "#AEB2C2", "#9299AB"),
                          ("g-mid", "#9AA77C", "#76845C"), ("g-near", "#E2C284", "#C79F5E")]:
    add('<linearGradient id="%s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s"/>'
        '<stop offset="1" stop-color="%s"/></linearGradient>' % (name, top, bottom))
for name, r in [("c-far", far), ("c-mid", mid), ("c-near", near)]:
    add('<clipPath id="%s"><path d="%s"/></clipPath>' % (name, area(r)))
add('</defs>')

# sun peeking over the haze
add('<circle cx="250" cy="92" r="36" fill="#F5E3B6" filter="url(#lift)"/>')

# haze
add('<path d="%s" fill="url(#g-haze)" filter="url(#lift)"/>' % area(haze))

# far range: soft shadow on the east (right) side of each hill, plus a few gullies
add('<g filter="url(#lift)"><path d="%s" fill="url(#g-far)"/><g clip-path="url(#c-far)">' % area(far))
for px, py in peaks(far):
    add('<path d="M%.0f,%.0f C%.0f,%.0f %.0f,%.0f %.0f,300 L%.0f,300 C%.0f,%.0f %.0f,%.0f %.0f,%.0f Z" fill="#7F879B" opacity=".28"/>'
        % (px, py, px + 10, py + 50, px - 5, py + 100, px + 15, px + 120, px + 110, py + 80, px + 60, py + 20, px, py))
    for k in (-1, 1):
        sx = px + k * rnd.uniform(25, 55)
        sy = y_at(far, sx) + 4
        add('<path d="M%.0f,%.0f q%.0f,30 %.0f,70" fill="none" stroke="#7F879B" stroke-width="1.3" opacity=".45"/>'
            % (sx, sy, k * 6, k * 2))
add('<path d="%s" fill="none" stroke="#CDD0DB" stroke-width="2"/>' % crest(far))
add('</g></g>')


def clump(x, y, s, dark, mid_c, light):
    """A bush: a few overlapping blobs with a highlight on the upper left."""
    parts = []
    for _ in range(rnd.randint(3, 5)):
        parts.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>'
                     % (x + rnd.uniform(-1.2, 1.2) * s, y + rnd.uniform(-0.6, 0.6) * s, s * rnd.uniform(0.7, 1.05), dark))
    parts.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (x - 0.2 * s, y - 0.3 * s, s * 0.7, mid_c))
    parts.append('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s"/>' % (x - 0.45 * s, y - 0.55 * s, s * 0.3, light))
    return "".join(parts)


# mid ridge: gullies with chaparral clumps following them
add('<g filter="url(#lift)"><path d="%s" fill="url(#g-mid)"/><g clip-path="url(#c-mid)">' % area(mid))
mid_peaks = peaks(mid)
for px, py in mid_peaks:
    add('<path d="M%.0f,%.0f C%.0f,%.0f %.0f,%.0f %.0f,330 L%.0f,330 C%.0f,%.0f %.0f,%.0f %.0f,%.0f Z" fill="#5F6D46" opacity=".22"/>'
        % (px, py, px + 8, py + 40, px - 4, py + 80, px + 10, px + 100, px + 90, py + 60, px + 50, py + 15, px, py))
# gullies start beside the peaks (not right on them) and fan out as they run downhill
gully_starts = sorted([p[0] + rnd.choice((-1, 1)) * rnd.uniform(25, 55) for p in mid_peaks]
                      + [rnd.uniform(0, W) for _ in range(6)])
for gx in gully_starts:
    top = y_at(mid, gx)
    drift = rnd.uniform(-45, 45)
    add('<path d="M%.0f,%.0f q%.0f,40 %.0f,110" fill="none" stroke="#66744C" stroke-width="1.4" opacity=".45"/>'
        % (gx, top + 6, drift * 0.3, drift))
    for i in range(rnd.randint(3, 5)):
        t = (i + rnd.uniform(0.3, 1.0)) / 5
        cx = gx + drift * t + rnd.uniform(-14, 14) * (0.6 + t)
        cy = top + 14 + 100 * t + rnd.uniform(-6, 6)
        add(clump(cx, cy, rnd.uniform(3.2, 5.2) * (0.9 + t * 0.5), "#5E6C45", "#6E7D52", "#8E9C6E"))
# scattered bushes on open slopes, thicker toward the bottom of the slope
for _ in range(80):
    x = rnd.uniform(0, W)
    top = y_at(mid, x)
    y = top + 12 + 100 * math.sqrt(rnd.random())
    add(clump(x, y, rnd.uniform(2.2, 4), "#66744C", "#74835A", "#93A174"))
add('<path d="%s" fill="none" stroke="#B9C499" stroke-width="2"/>' % crest(mid))
add('</g></g>')

# near hill: dry grass, a fire road on each shoulder, a few shrubs
add('<g filter="url(#lift)"><path d="%s" fill="url(#g-near)"/><g clip-path="url(#c-near)">' % area(near))
add('<path d="M-6,372 C200,360 420,380 640,366 S1000,374 1206,360 L1206,406 L-6,406 Z" fill="#BF9655" opacity=".35"/>')
add('<path d="M-10,388 C40,372 90,356 150,346 S250,334 205,322 S120,312 60,322" fill="none" stroke="#F1DEAF" stroke-width="4.5" stroke-linecap="round"/>')
add('<path d="M1210,384 C1160,370 1110,356 1050,346 S950,334 995,322 S1080,312 1140,320" fill="none" stroke="#F1DEAF" stroke-width="4.5" stroke-linecap="round"/>')
for _ in range(170):
    x = rnd.uniform(0, W)
    top = y_at(near, x)
    y = rnd.uniform(top + 8, H)
    add('<path d="M%.0f,%.0f l%.1f,-%.1f" stroke="#B08A4C" stroke-width="1.2" stroke-linecap="round" opacity=".6"/>'
        % (x, y, rnd.uniform(-2, 2), rnd.uniform(3, 7)))
for _ in range(28):
    x = rnd.uniform(0, W)
    top = y_at(near, x)
    y = rnd.uniform(top + 14, H - 6)
    add(clump(x, y, rnd.uniform(3.5, 6), "#7E7A47", "#8F8B55", "#ADA874"))
add('<path d="%s" fill="none" stroke="#F0DCA8" stroke-width="2"/>' % crest(near))
add('</g></g>')

add('</svg>')
print("".join(svg))
