# -*- coding: utf-8 -*-
"""
Build dist/favicon.svg from one or more Hollywood-sign glyphs
(dist/letters/<CH>.svg). Each glyph's internal ids are namespaced so inlined
glyphs don't collide on url(#id). The viewBox is trimmed to the actual ink
(letter face + 3-D extrusion + support posts, not the glyphs' built-in padding)
and preserveAspectRatio="none" stretches that to a square icon, so the word
fills the whole favicon horizontally AND vertically.

USAGE
  python tools/make_favicon.py [LETTERS]      # default: LA
"""
import re, sys

WORD = (sys.argv[1] if len(sys.argv) > 1 else "LA").upper()
GAP  = -3.0                 # horizontal kerning between glyphs, in glyph units
EXT_DX, EXT_DY = -9.0, 4.5  # 3-D extrusion direction (from gen_hollywood_glyphs.py)
POLE_TOP, POLE_BOT = 3.8, 94.7  # support-post vertical extent (constant per glyph)
STROKE = 0.85              # half the face edge stroke, so the outline isn't clipped

def face_bbox(d):
    """Min/max x,y of the letter-face path (handles M/L/H/V/C/S/Q/T absolute)."""
    xs, ys, x, y = [], [], 0.0, 0.0
    for cmd, args in re.findall(r"([MLHVCSQTZ])([^MLHVCSQTZ]*)", d):
        nums = [float(n) for n in re.findall(r"-?\d*\.?\d+", args)]
        if cmd == "H":
            for n in nums: x = n; xs.append(x); ys.append(y)
        elif cmd == "V":
            for n in nums: y = n; xs.append(x); ys.append(y)
        elif cmd != "Z":
            for i in range(0, len(nums) - 1, 2):
                x, y = nums[i], nums[i + 1]; xs.append(x); ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)

def load(ch):
    s = open("dist/letters/%s.svg" % ch, encoding="utf-8").read()
    inner = re.sub(r"^<svg[^>]*>", "", s).replace("</svg>", "").strip()
    W = float(re.search(r'viewBox="0 0 ([\d.]+)', s).group(1))
    gd = re.search(r'<path id="g" d="([^"]+)"', s).group(1)
    return inner, W, gd

def namespace(inner, suf):
    for i in ("g", "clip", "sil", "face"):
        inner = (inner.replace('id="%s"' % i, 'id="%s-%s"' % (i, suf))
                      .replace('href="#%s"' % i, 'href="#%s-%s"' % (i, suf))
                      .replace('url(#%s)' % i, 'url(#%s-%s)' % (i, suf)))
    return inner

glyphs, x = [], 0.0
minx, miny, maxx, maxy = 1e9, 1e9, -1e9, -1e9
for idx, ch in enumerate(WORD):
    inner, W, gd = load(ch)
    fx0, fy0, fx1, fy1 = face_bbox(gd)
    minx = min(minx, x + fx0 + EXT_DX - STROKE)
    maxx = max(maxx, x + fx1 + STROKE)
    miny = min(miny, min(fy0, POLE_TOP) - STROKE)
    maxy = max(maxy, max(fy1 + EXT_DY, POLE_BOT) + STROKE)
    glyphs.append((namespace(inner, str(idx)), x))
    x += W + GAP

vb_w, vb_h = maxx - minx, maxy - miny
side = round(max(vb_w, vb_h))
body = "".join('<g transform="translate(%.2f,0)">%s</g>' % (gx, g) for g, gx in glyphs)
svg = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="%.2f %.2f %.2f %.2f" '
    'width="%d" height="%d" preserveAspectRatio="none" role="img" aria-label="%s">'
    '%s</svg>'
) % (minx, miny, vb_w, vb_h, side, side, WORD, body)

open("dist/favicon.svg", "w", encoding="utf-8").write(svg)
print('wrote "%s"  viewBox %.2f %.2f %.2f %.2f  (stretch x%.2f vertically)'
      % (WORD, minx, miny, vb_w, vb_h, (max(vb_w, vb_h) / vb_h)))
