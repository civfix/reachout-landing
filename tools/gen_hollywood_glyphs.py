# -*- coding: utf-8 -*-
"""
Generate the Hollywood-Sign 3-D letter SVGs used for the site logo and the
subpage titles (dist/letters/*.svg).

Each letter is rendered from a real font outline as:
  - support poles (stilts) beneath the letter   -> the scaffolding it stands on
  - a stacked extrusion to the lower-left        -> the 3-D "depth" / side faces
  - a crisp contour on the deepest copy          -> defines the silhouette
  - a white front face with a thin edge          -> the letter itself
  - an optional clipped panel grid               -> the metal-sheet texture

All glyphs share one vertical frame (same baseline + scale), so rendering every
<img> at the same CSS height keeps the baselines aligned automatically; only the
width varies per letter. The script prints the CSS height factor (GH) to use for
`.char .glyph { height: calc(var(--base) * GH) }` so the cap height stays put as
the stilts extend the frame downward.

FONT
  Built with "SF Hollywood Hills" (Bold) by ShyFonts / ShyFoundry — a replica of
  the actual Hollywood Sign lettering (tall chamfered/octagonal block caps).
  NOTE: ShyFoundry freeware is licensed for personal use; business / for-profit
  use "requires an additional license that may be purchased from ShyFoundry.com".
  For a public org site, buy that license or swap in a differently-licensed
  look-alike (the script works with any TTF/OTF; e.g. a chamfered OFL face).

USAGE
  pip install fonttools
  python tools/gen_hollywood_glyphs.py <font.ttf> dist/letters ABCEFHILMNOPRSTUVX grid
  # drop the trailing "grid" arg for plain faces (no panel texture)
"""
import os, sys, re
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

FONT   = sys.argv[1]
OUT    = sys.argv[2]
GLYPHS = sys.argv[3] if len(sys.argv) > 3 else "ABCEFHILMNOPRSTUVX"
GRID   = (len(sys.argv) > 4 and sys.argv[4] == "grid")

f = TTFont(FONT)
if "fvar" in f:
    axes = {a.axisTag: a.maxValue for a in f["fvar"].axes}
    instantiateVariableFont(f, {"wght": axes.get("wght", 700)}, inplace=True)
upm  = f["head"].unitsPerEm
gs   = f.getGlyphSet()
cmap = f.getBestCmap()
def gly(ch): return gs[cmap[ord(ch)]]

def bounds(ch):
    bp = BoundsPen(gs); gly(ch).draw(bp); return bp.bounds  # (xMin,yMin,xMax,yMax)

tops, bots = [], []
for ch in GLYPHS:
    b = bounds(ch)
    if b: tops.append(b[3]); bots.append(b[1])
TOP, BOT = max(tops), min(bots)

# --- geometry (px; the em renders at 100px regardless of font upm) ---
S        = 100.0 / upm
EXT_DX   = -9.0      # depth direction: left  (slight side angle)
EXT_DY   =  4.5      # depth direction: down
STEPS    = 22
EDGE     = 3.5
TOPPAD   = 4.0
BOTPAD   = 3.0
# stilts
STILT_LEN = 8.0      # short legs below the baseline (the scaffold sits BEHIND, not below)
POLE_W    = 2.8      # post width
OVERHANG  = 3.0      # posts reach the cap; a per-letter top-profile clip trims them
POLE_GAP  = 16.0     # target spacing between posts -> post count per letter
BACK_X    = EXT_DX * 0.62   # push the scaffold to the letter's BACK plane (3-D depth)
BACK_Y    = EXT_DY * 0.62
PDX       = EXT_DX * 0.42    # each support's own small depth
PDY       = EXT_DY * 0.42

LEFTPAD   = EDGE + abs(EXT_DX)
baselineY = TOPPAD + S * TOP
# posts run the FULL letter height at the BACK plane: from above the cap
# (poking up behind the letter) down to a short length below the baseline.
poleTop   = baselineY - S * TOP - OVERHANG + BACK_Y
poleBot   = baselineY + STILT_LEN + BACK_Y
H = poleBot + PDY + BOTPAD

CAP_PX = S * TOP                       # cap height in viewBox px
GH = round(0.752 * H / CAP_PX, 3)      # CSS height factor that preserves cap size

# colors
FACE_TOP = "#FFFFFF"; FACE_BOT = "#ECE9E2"
SIDE     = "#8E8A82"; CONTOUR  = "#585550"
EDGE_CLR = "#5E5A52"; STROKE_W = 1.7
GRID_CLR = "#CFC8BA"; GRID_W   = 0.7; GV = 9.0; GH_CELL = 9.0
POLE_FACE = "#A7A299"; POLE_SIDE = "#6C685F"
BRACE     = "#6A665E"; BRACE_W   = 1.5

def rnd(d):
    return re.sub(r"-?\d+\.\d+", lambda m: f"{float(m.group()):.1f}", d)

def path_d(g, tx, ty):
    out = SVGPathPen(gs)
    g.draw(TransformPen(out, (S, 0, 0, -S, tx, ty)))   # scale + flip Y to SVG space
    return rnd(out.getCommands())

class FlattenPen:
    """Collects a glyph's outline as flat polygons (curves sampled to line segments)."""
    def __init__(self, steps=6):
        self.contours = []; self.cur = None; self.last = None; self.steps = steps
    def moveTo(self, p): self.cur = [p]; self.last = p
    def lineTo(self, p): self.cur.append(p); self.last = p
    def _quad(self, p0, c, p2):
        for s in range(1, self.steps + 1):
            t = s / self.steps; mt = 1 - t
            self.cur.append((mt*mt*p0[0] + 2*mt*t*c[0] + t*t*p2[0],
                             mt*mt*p0[1] + 2*mt*t*c[1] + t*t*p2[1]))
    def qCurveTo(self, *pts):
        if pts[-1] is None:
            offs = list(pts[:-1])
            on_last = ((offs[0][0]+offs[-1][0])/2, (offs[0][1]+offs[-1][1])/2)
        else:
            offs = list(pts[:-1]); on_last = pts[-1]
        if not offs:
            self.lineTo(on_last); return
        on = [((offs[i][0]+offs[i+1][0])/2, (offs[i][1]+offs[i+1][1])/2) for i in range(len(offs)-1)]
        on.append(on_last)
        p0 = self.last
        for i, c in enumerate(offs):
            self._quad(p0, c, on[i]); p0 = on[i]
        self.last = on_last
    def curveTo(self, *pts):
        c1, c2, end = pts[-3], pts[-2], pts[-1]; p0 = self.last
        for s in range(1, self.steps + 1):
            t = s / self.steps; mt = 1 - t
            self.cur.append((mt**3*p0[0] + 3*mt*mt*t*c1[0] + 3*mt*t*t*c2[0] + t**3*end[0],
                             mt**3*p0[1] + 3*mt*mt*t*c1[1] + 3*mt*t*t*c2[1] + t**3*end[1]))
        self.last = end
    def closePath(self):
        if self.cur and len(self.cur) >= 2: self.contours.append(self.cur)
        self.cur = None
    def endPath(self): self.closePath()
    def addComponent(self, *a, **k): pass

def signed_area(pts):
    a = 0.0; n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % n]
        a += x0*y1 - x1*y0
    return a * 0.5

def extent_clip(g, tx, ty, W):
    """Clip-path: at every height, the region from the letter's LEFTMOST ink to its
    RIGHTMOST ink (full width below the baseline for the base). Clipping the scaffold to
    this shows posts through interior openings/counters and gaps -- E's notches, the U/V
    opening, the A/O counters -- and below the letter, but never beyond the letter's sides
    (so the L's empty top-right stays clear) and never above it."""
    fp = FlattenPen()
    g.draw(TransformPen(fp, (S, 0, 0, -S, tx, ty)))
    edges = []; ys = []
    for c in fp.contours:
        m = len(c)
        for i in range(m):
            a = c[i]; b = c[(i + 1) % m]
            if a[1] != b[1]:                      # non-horizontal edge -> defines side extent
                edges.append((a[0], a[1], b[0], b[1]))
            ys.append(a[1])
    base = f"M0 {baselineY:.1f}L{W:.1f} {baselineY:.1f}L{W:.1f} {H:.1f}L0 {H:.1f}Z"
    if not edges or not ys:
        return base
    def span_at(y):
        xs = []
        for x1, y1, x2, y2 in edges:
            if y1 <= y <= y2 or y2 <= y <= y1:
                xs.append(x1 + (x2 - x1) * (y - y1) / (y2 - y1))
        return (min(xs), max(xs)) if xs else None
    rows = []
    y = min(ys)
    while y < baselineY:
        s = span_at(y)
        if s: rows.append((y, s[0], s[1]))
        y += 1.0
    s = span_at(baselineY)
    if s: rows.append((baselineY, s[0], s[1]))
    if not rows:
        return base
    d = "M%.1f %.1f" % (rows[0][1], rows[0][0])
    d += "".join("L%.1f %.1f" % (r[1], r[0]) for r in rows[1:])               # down the left edge
    d += "L0.0 %.1fL0.0 %.1fL%.1f %.1fL%.1f %.1f" % (rows[-1][0], H, W, H, W, rows[-1][0])  # base
    d += "".join("L%.1f %.1f" % (r[2], r[0]) for r in reversed(rows))         # up the right edge
    return d + "Z"

def leg(cx):
    """One support post sitting at the letter's BACK plane (shifted by BACK_X/Y and
    drawn behind the letter, so the letter body occludes its top -> reads as 'behind')."""
    bx = cx + BACK_X
    x0 = bx - POLE_W / 2; x1 = bx + POLE_W / 2
    side = f"{x0:.1f},{poleTop:.1f} {x0+PDX:.1f},{poleTop+PDY:.1f} {x0+PDX:.1f},{poleBot+PDY:.1f} {x0:.1f},{poleBot:.1f}"
    bot  = f"{x0:.1f},{poleBot:.1f} {x0+PDX:.1f},{poleBot+PDY:.1f} {x1+PDX:.1f},{poleBot+PDY:.1f} {x1:.1f},{poleBot:.1f}"
    return (f'<polygon points="{side}" fill="{POLE_SIDE}"/>'
            f'<polygon points="{bot}" fill="{POLE_SIDE}"/>'
            f'<rect x="{x0:.1f}" y="{poleTop:.1f}" width="{POLE_W:.1f}" height="{(poleBot-poleTop):.1f}" fill="{POLE_FACE}" stroke="{CONTOUR}" stroke-width="0.6"/>')

def footprint_xs(g, tx, ty, W):
    """x positions where the letter meets the baseline (where it 'stands'). Posts placed
    here read as real supports instead of random sticks under curved/sloped/open parts."""
    fp = FlattenPen()
    g.draw(TransformPen(fp, (S, 0, 0, -S, tx, ty)))
    edges = []
    for c in fp.contours:
        m = len(c)
        for i in range(m):
            a = c[i]; b = c[(i + 1) % m]
            if a[0] != b[0]:
                edges.append((a[0], a[1], b[0], b[1]))
    gly_bottom = max((p[1] for c in fp.contours for p in c), default=baselineY)
    foot = gly_bottom - 6.0                   # 'stands' if a column's ink reaches the glyph's own bottom
    samp = []
    x = 0.0
    while x <= W:
        samp.append(x); x += 0.5
    flags = []
    for xv in samp:
        bottom = -1e9
        for x1, y1, x2, y2 in edges:
            if x1 <= xv <= x2 or x2 <= xv <= x1:
                yv = y1 + (y2 - y1) * (xv - x1) / (x2 - x1)
                if yv > bottom:
                    bottom = yv              # bottommost ink (largest y) at this column
        flags.append(bottom >= foot)         # reaches near the baseline -> a footing here
    intervals = []; start = None
    for i, f in enumerate(flags):
        if f and start is None:
            start = samp[i]
        elif not f and start is not None:
            intervals.append((start, samp[i - 1])); start = None
    if start is not None:
        intervals.append((start, samp[-1]))
    if not intervals:
        all_x = [e[0] for e in edges] + [e[2] for e in edges]
        center = (min(all_x) + max(all_x)) / 2 if all_x else W / 2
        span = 0.0
    else:
        center = (intervals[0][0] + intervals[-1][1]) / 2
        span = intervals[-1][1] - intervals[0][0]
    half = max(6.0, span * 0.42)          # exactly TWO posts, wider apart for wider letters
    return [center - half, center + half]

def stilts(g, tx, ty, W):
    """Support posts at the letter's footprint with a braced base. Posts run up behind the
    letter (trimmed by the top-profile clip); the X-bracing + tie sit below as the base."""
    xs = footprint_xs(g, tx, ty, W)
    braceTop = poleTop + 4.0                              # the X runs the FULL height behind the
    braceBot = poleBot - 2                                # letter, so it shows through every gap
    bl = []
    for i in range(len(xs) - 1):
        a = xs[i] + BACK_X; c = xs[i + 1] + BACK_X
        bl.append(f'<line x1="{a:.1f}" y1="{braceTop:.1f}" x2="{c:.1f}" y2="{braceBot:.1f}"/>')
        bl.append(f'<line x1="{a:.1f}" y1="{braceBot:.1f}" x2="{c:.1f}" y2="{braceTop:.1f}"/>')
    braces = f'<g stroke="{BRACE}" stroke-width="{BRACE_W}" stroke-linecap="round" fill="none">{"".join(bl)}</g>' if bl else ""
    return braces + "".join(leg(cx) for cx in xs)

def build(ch):
    g = gly(ch); adv = g.width
    tx, ty = LEFTPAD, baselineY
    W = S * adv + tx + EDGE
    d = path_d(g, tx, ty)
    poles = stilts(g, tx, ty, W)
    sil = extent_clip(g, tx, ty, W)
    uses = []
    for i in range(STEPS, 0, -1):
        fr = i / STEPS; dx = EXT_DX * fr; dy = EXT_DY * fr
        if i == STEPS:
            uses.append(f'<use href="#g" transform="translate({dx:.1f},{dy:.1f})" fill="{SIDE}" stroke="{CONTOUR}" stroke-width="1.3" stroke-linejoin="round"/>')
        else:
            uses.append(f'<use href="#g" transform="translate({dx:.1f},{dy:.1f})" fill="{SIDE}"/>')
    side = "".join(uses)
    grid = clip = ""
    if GRID:
        lines = []
        x = GV
        while x < W: lines.append(f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{baselineY:.1f}"/>'); x += GV
        y = GH_CELL
        while y < baselineY: lines.append(f'<line x1="0" y1="{y:.1f}" x2="{W:.1f}" y2="{y:.1f}"/>'); y += GH_CELL
        grid = f'<g clip-path="url(#clip)" stroke="{GRID_CLR}" stroke-width="{GRID_W}" opacity="0.55">{"".join(lines)}</g>'
        clip = '<clipPath id="clip"><use href="#g"/></clipPath>'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.1f} {H:.1f}" width="{W:.1f}" height="{H:.1f}" role="img" aria-label="{ch}">'
        f'<defs><path id="g" d="{d}"/>{clip}'
        f'<clipPath id="sil"><path d="{sil}"/></clipPath>'
        f'<linearGradient id="face" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{FACE_TOP}"/><stop offset="1" stop-color="{FACE_BOT}"/></linearGradient></defs>'
        f'<g clip-path="url(#sil)">{poles}</g>'
        f'<g>{side}</g>'
        f'<use href="#g" fill="url(#face)" stroke="{EDGE_CLR}" stroke-width="{STROKE_W}" stroke-linejoin="round"/>'
        f'{grid}</svg>'
    )

os.makedirs(OUT, exist_ok=True)
for ch in GLYPHS:
    open(os.path.join(OUT, ch + ".svg"), "w", encoding="utf-8").write(build(ch))
print(f"wrote {len(GLYPHS)} glyphs to {OUT} (grid={GRID}, frame H={H:.1f})")
print(f"CSS:  .char .glyph {{ height: calc(var(--base) * {GH}); }}")
