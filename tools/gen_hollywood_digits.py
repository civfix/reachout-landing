# -*- coding: utf-8 -*-
"""
Generate Hollywood-sign digit glyphs (dist/letters/4.svg, dist/letters/0.svg)
matching the letter glyphs from gen_hollywood_glyphs.py. The "SF Hollywood Hills"
font isn't available to re-run that script, so this authors blocky digit face
outlines and applies the SAME treatment (3-D extrusion, white gradient face, edge
contour, panel grid, support posts) using the exact constants observed in the
generated letters.

The "0" is a real digit: narrower than the round letter O and built as a ring
(outer + inner octagon), so the support posts show through the hole.

USAGE
  python tools/gen_hollywood_digits.py
"""
# --- constants (identical to the generated letters) ---
EXT_DX, EXT_DY = -9.0, 4.5
STEPS = 22
baselineY = 82.0
H = 97.7
GV = 9.0
poleTop, poleBot = 3.8, 92.8
POLE_W = 2.8
BACK_X, BACK_Y = EXT_DX * 0.62, EXT_DY * 0.62
PDX, PDY = EXT_DX * 0.42, EXT_DY * 0.42
braceTop, braceBot = poleTop + 4.0, poleBot - 2.0

FACE_TOP, FACE_BOT = "#FFFFFF", "#ECE9E2"
SIDE, CONTOUR = "#8E8A82", "#585550"
EDGE_CLR, STROKE_W = "#5E5A52", 1.7
GRID_CLR, GRID_W = "#CFC8BA", 0.7
POLE_FACE, POLE_SIDE = "#A7A299", "#6C685F"
BRACE, BRACE_W = "#6A665E", 1.5

# Each digit = (list of contours, viewBox width). Contours straight-line, cap 7..79.
# "4": one contour. "0": outer ring (CW) + inner hole (CCW) so nonzero fill cuts the hole.
DIGITS = {
    "4": ([[(12, 7), (29, 7), (29, 47), (42, 47), (42, 7),
            (59, 7), (59, 79), (42, 79), (42, 64), (12, 64)]], 62.5),
    "0": ([[(12, 19), (24, 7), (40, 7), (52, 19), (52, 67), (40, 79), (24, 79), (12, 67)],
           [(26, 61), (30, 65), (34, 65), (38, 61), (38, 25), (34, 21), (30, 21), (26, 25)]], 55.5),
}

def path_d(contours):
    out = []
    for pts in contours:
        out.append("M%.1f %.1f" % pts[0] + "".join("L%.1f %.1f" % p for p in pts[1:]) + "Z")
    return "".join(out)

def _edges(contours, kind):
    """kind='v' -> non-horizontal edges (for x extent by y); 'h' -> non-vertical."""
    e = []
    for pts in contours:
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            if (kind == "v" and a[1] != b[1]) or (kind == "h" and a[0] != b[0]):
                e.append((a[0], a[1], b[0], b[1]))
    return e

def extent_clip(contours, W):
    edges = _edges(contours, "v")
    ys = [p[1] for pts in contours for p in pts]
    base = "M0 %.1fL%.1f %.1fL%.1f %.1fL0 %.1fZ" % (baselineY, W, baselineY, W, H, H)
    if not edges:
        return base
    def span_at(y):
        xs = [x1 + (x2 - x1) * (y - y1) / (y2 - y1)
              for x1, y1, x2, y2 in edges if y1 <= y <= y2 or y2 <= y <= y1]
        return (min(xs), max(xs)) if xs else None
    rows = []; y = min(ys)
    while y < baselineY:
        s = span_at(y)
        if s: rows.append((y, s[0], s[1]))
        y += 1.0
    s = span_at(baselineY)
    if s: rows.append((baselineY, s[0], s[1]))
    if not rows:
        return base
    d = "M%.1f %.1f" % (rows[0][1], rows[0][0])
    d += "".join("L%.1f %.1f" % (r[1], r[0]) for r in rows[1:])
    d += "L0.0 %.1fL0.0 %.1fL%.1f %.1fL%.1f %.1f" % (rows[-1][0], H, W, H, W, rows[-1][0])
    d += "".join("L%.1f %.1f" % (r[2], r[0]) for r in reversed(rows))
    return d + "Z"

def footprint_xs(contours, W):
    edges = _edges(contours, "h")
    gly_bottom = max(p[1] for pts in contours for p in pts); foot = gly_bottom - 6.0
    samp = []; x = 0.0
    while x <= W:
        samp.append(x); x += 0.5
    flags = []
    for xv in samp:
        bottom = -1e9
        for x1, y1, x2, y2 in edges:
            if x1 <= xv <= x2 or x2 <= xv <= x1:
                bottom = max(bottom, y1 + (y2 - y1) * (xv - x1) / (x2 - x1))
        flags.append(bottom >= foot)
    intervals = []; start = None
    for i, f in enumerate(flags):
        if f and start is None:
            start = samp[i]
        elif not f and start is not None:
            intervals.append((start, samp[i - 1])); start = None
    if start is not None:
        intervals.append((start, samp[-1]))
    if not intervals:
        center, span = W / 2, 0.0
    else:
        center = (intervals[0][0] + intervals[-1][1]) / 2
        span = intervals[-1][1] - intervals[0][0]
    half = max(6.0, span * 0.42)
    return [center - half, center + half]

def leg(cx):
    bx = cx + BACK_X
    x0, x1 = bx - POLE_W / 2, bx + POLE_W / 2
    side = "%.1f,%.1f %.1f,%.1f %.1f,%.1f %.1f,%.1f" % (
        x0, poleTop, x0 + PDX, poleTop + PDY, x0 + PDX, poleBot + PDY, x0, poleBot)
    bot = "%.1f,%.1f %.1f,%.1f %.1f,%.1f %.1f,%.1f" % (
        x0, poleBot, x0 + PDX, poleBot + PDY, x1 + PDX, poleBot + PDY, x1, poleBot)
    return ('<polygon points="%s" fill="%s"/><polygon points="%s" fill="%s"/>'
            '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="%s" stroke="%s" stroke-width="0.6"/>'
            % (side, POLE_SIDE, bot, POLE_SIDE, x0, poleTop, POLE_W, poleBot - poleTop, POLE_FACE, CONTOUR))

def stilts(contours, W):
    xs = footprint_xs(contours, W)
    bl = []
    for i in range(len(xs) - 1):
        a, c = xs[i] + BACK_X, xs[i + 1] + BACK_X
        bl.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (a, braceTop, c, braceBot))
        bl.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (a, braceBot, c, braceTop))
    braces = ('<g stroke="%s" stroke-width="%s" stroke-linecap="round" fill="none">%s</g>'
              % (BRACE, BRACE_W, "".join(bl))) if bl else ""
    return braces + "".join(leg(cx) for cx in xs)

def build(ch, contours, W):
    d = path_d(contours)
    poles = stilts(contours, W)
    sil = extent_clip(contours, W)
    uses = []
    for i in range(STEPS, 0, -1):
        fr = i / STEPS; dx, dy = EXT_DX * fr, EXT_DY * fr
        if i == STEPS:
            uses.append('<use href="#g" transform="translate(%.1f,%.1f)" fill="%s" stroke="%s" stroke-width="1.3" stroke-linejoin="round"/>' % (dx, dy, SIDE, CONTOUR))
        else:
            uses.append('<use href="#g" transform="translate(%.1f,%.1f)" fill="%s"/>' % (dx, dy, SIDE))
    lines = []
    x = GV
    while x < W:
        lines.append('<line x1="%.1f" y1="0" x2="%.1f" y2="%.1f"/>' % (x, x, baselineY)); x += GV
    y = GV
    while y < baselineY:
        lines.append('<line x1="0" y1="%.1f" x2="%.1f" y2="%.1f"/>' % (y, W, y)); y += GV
    grid = '<g clip-path="url(#clip)" stroke="%s" stroke-width="%s" opacity="0.55">%s</g>' % (GRID_CLR, GRID_W, "".join(lines))
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.1f %.1f" width="%.1f" height="%.1f" role="img" aria-label="%s">'
        '<defs><path id="g" d="%s"/><clipPath id="clip"><use href="#g"/></clipPath>'
        '<clipPath id="sil"><path d="%s"/></clipPath>'
        '<linearGradient id="face" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient></defs>'
        '<g clip-path="url(#sil)">%s</g><g>%s</g>'
        '<use href="#g" fill="url(#face)" stroke="%s" stroke-width="%s" stroke-linejoin="round"/>%s</svg>'
        % (W, H, W, H, ch, d, sil, FACE_TOP, FACE_BOT, poles, "".join(uses), EDGE_CLR, STROKE_W, grid)
    )

for ch, (contours, W) in DIGITS.items():
    open("dist/letters/%s.svg" % ch, "w", encoding="utf-8").write(build(ch, contours, W))
    print("wrote dist/letters/%s.svg  (viewBox 0 0 %.1f %.1f)" % (ch, W, H))
