"""Generate the Crustates brand kit (SVG + PNG + ICO).

Text is converted to outlines so every SVG renders identically without fonts.
Usage: python3 build_brand.py <fonts_dir> <out_dir>
"""
import io
import math
import os
import sys

import cairosvg
import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONTS, OUT = sys.argv[1], sys.argv[2]

INK = "#111111"
CREAM = "#FFF6E5"
RUST = "#E8552D"
BLUE = "#1F3FD1"
YELLOW = "#FFD23F"
GREEN = "#3DDC84"
TEAL = "#0B7A70"
VIOLET = "#A77BFF"
BROWN = "#8B5E3C"
PINK = "#FF7AA8"
WHITE = "#FFFFFF"


# ---------------------------------------------------------------- text → paths
class Font:
    def __init__(self, path):
        tt = TTFont(path)
        tt.flavor = None
        buf = io.BytesIO()
        tt.save(buf)
        data = buf.getvalue()
        self.tt = TTFont(io.BytesIO(data))
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upem = self.tt["head"].unitsPerEm
        self.hbfont = hb.Font(hb.Face(hb.Blob(data)))
        os2 = self.tt["OS/2"]
        self.xh = os2.sxHeight / self.upem
        self.cap = os2.sCapHeight / self.upem

    def shape(self, text):
        b = hb.Buffer()
        b.add_str(text)
        b.guess_segment_properties()
        hb.shape(self.hbfont, b, {})
        for info in b.glyph_infos:
            if info.codepoint == 0:
                raise ValueError(f"missing glyph in {text!r}")
        return b.glyph_infos, b.glyph_positions

    def width(self, text, size, tracking=0.0):
        _, pos = self.shape(text)
        s = size / self.upem
        adv = sum(p.x_advance for p in pos) * s
        return adv + tracking * size * (len(pos) - 1)

    def path(self, text, size, x, y, tracking=0.0):
        """Path data for text with its baseline starting at (x, y)."""
        infos, pos = self.shape(text)
        s = size / self.upem
        cx = x
        out = []
        for info, p in zip(infos, pos):
            pen = SVGPathPen(self.gs)
            t = TransformPen(pen, (s, 0, 0, -s, cx + p.x_offset * s, y - p.y_offset * s))
            self.gs[self.order[info.codepoint]].draw(t)
            out.append(pen.getCommands())
            cx += p.x_advance * s + tracking * size
        return " ".join(out)

    def circle_path(self, text, size, cx, cy, r):
        """Glyphs around a circle, clockwise from the top, spread to fill it."""
        infos, pos = self.shape(text)
        s = size / self.upem
        advs = [p.x_advance * s for p in pos]
        extra = (2 * math.pi * r - sum(advs)) / len(advs)
        theta = 0.0
        out = []
        for info, adv in zip(infos, advs):
            mid = theta + (adv / 2) / r
            h = adv / 2
            c, sn = math.cos(mid), math.sin(mid)
            px, py = cx + r * sn, cy - r * c
            pen = SVGPathPen(self.gs)
            t = TransformPen(pen, (s * c, s * sn, s * sn, -s * c, px - h * c, py - h * sn))
            self.gs[self.order[info.codepoint]].draw(t)
            out.append(pen.getCommands())
            theta += (adv + extra) / r
        return " ".join(out)


GROTESK = Font(os.path.join(FONTS, "space-grotesk-latin-700-normal.woff"))
GROTESK_MED = Font(os.path.join(FONTS, "space-grotesk-latin-500-normal.woff"))
MONO = Font(os.path.join(FONTS, "jetbrains-mono-latin-700-normal.woff"))


# ---------------------------------------------------------------- the mark
# 80-unit grid. Crab-crate: square body, raised pincer claws, square eyes,
# and a terminal-cursor mouth. Content spans x -2..82, y 10..66 (+ shadow).
SW = 3.5        # stroke width
SHADOW = 5      # hard shadow offset

CLAW_L = "M0 12 H5 V21 H11 V12 H16 V32 H0 Z"
CLAW_R = "M80 12 H75 V21 H69 V12 H64 V32 H80 Z"
MARK_BOX = (-2, 10, 82 + SHADOW, 66 + SHADOW)   # x0, y0, x1, y1


def mark_shapes(body, stroke, eye, pupil, mouth):
    st = f'stroke="{stroke}" stroke-width="{SW}" stroke-linejoin="miter"'
    return "".join([
        f'<rect x="5" y="30" width="12" height="12" fill="{body}" {st}/>',
        f'<rect x="63" y="30" width="12" height="12" fill="{body}" {st}/>',
        f'<path d="{CLAW_L}" fill="{body}" {st}/>',
        f'<path d="{CLAW_R}" fill="{body}" {st}/>',
        f'<rect x="16" y="34" width="48" height="30" fill="{body}" {st}/>',
        f'<rect x="23" y="19" width="13" height="13" fill="{eye}" {st}/>',
        f'<rect x="44" y="19" width="13" height="13" fill="{eye}" {st}/>',
        f'<rect x="29" y="22" width="5" height="5" fill="{pupil}"/>',
        f'<rect x="46" y="22" width="5" height="5" fill="{pupil}"/>',
        f'<rect x="34" y="49" width="12" height="4" fill="{mouth}"/>',
    ])


def mark_silhouette(color):
    """Union of the mark's outer shapes, used as the hard shadow."""
    st = f'stroke="{color}" stroke-width="{SW}" stroke-linejoin="miter"'
    return "".join([
        f'<rect x="5" y="30" width="12" height="12" fill="{color}" {st}/>',
        f'<rect x="63" y="30" width="12" height="12" fill="{color}" {st}/>',
        f'<path d="{CLAW_L}" fill="{color}" {st}/>',
        f'<path d="{CLAW_R}" fill="{color}" {st}/>',
        f'<rect x="16" y="34" width="48" height="30" fill="{color}" {st}/>',
        f'<rect x="23" y="19" width="13" height="13" fill="{color}" {st}/>',
        f'<rect x="44" y="19" width="13" height="13" fill="{color}" {st}/>',
    ])


THEMES = {
    "light": dict(body=RUST, stroke=INK, eye=CREAM, pupil=INK, mouth=INK, shadow=INK, text=INK),
    "dark": dict(body=RUST, stroke=CREAM, eye=CREAM, pupil=INK, mouth=INK, shadow=YELLOW, text=CREAM),
    "mono-black": dict(body=INK, stroke=INK, eye=WHITE, pupil=INK, mouth=WHITE, shadow=None, text=INK),
    "mono-white": dict(body=WHITE, stroke=WHITE, eye=INK, pupil=WHITE, mouth=INK, shadow=None, text=WHITE),
}


def mark_group(theme="light", shadow=True):
    t = THEMES[theme]
    parts = []
    if shadow and t["shadow"]:
        parts.append(f'<g transform="translate({SHADOW} {SHADOW})">{mark_silhouette(t["shadow"])}</g>')
    parts.append(mark_shapes(t["body"], t["stroke"], t["eye"], t["pupil"], t["mouth"]))
    return "".join(parts)


def svg(w, h, body, vb=None, title="Crustates"):
    vb = vb or f"0 0 {w} {h}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{vb}" '
            f'role="img" aria-label="{title}"><title>{title}</title>{body}</svg>\n')


def square_vb(box, pad):
    x0, y0, x1, y1 = box
    side = max(x1 - x0, y1 - y0) + 2 * pad
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return f"{cx - side / 2:g} {cy - side / 2:g} {side:g} {side:g}", side


# ---------------------------------------------------------------- outputs
FILES = {}


def put(name, content):
    FILES[name] = content


def mark_files():
    for theme in THEMES:
        sh = theme in ("light", "dark")
        vb, _ = square_vb(MARK_BOX, 4)
        put(f"svg/mark-{theme}.svg", svg(256, 256, mark_group(theme, sh), vb, "Crustates mark"))
    vb, _ = square_vb((-2, 10, 82, 66), 3)
    put("svg/mark-flat.svg", svg(256, 256, mark_group("light", False), vb, "Crustates mark"))
    put("svg/favicon.svg", favicon_pixel())


PIXELS = [
    ".R.R........R.R.",
    ".RRR.CC..CC.RRR.",
    ".RRR.CK..KC.RRR.",
    "..R.RRRRRRRR.R..",
    "..RRRRRRRRRRRR..",
    "....RRRRRRRR....",
    "....RRRKKRRR....",
    "....RRRRRRRR....",
]


def favicon_pixel():
    """16x16 pixel-art version of the mark with a 1px ink outline."""
    top = (16 - len(PIXELS)) // 2
    grid = {}
    for y, row in enumerate(PIXELS):
        for x, ch in enumerate(row):
            if ch != ".":
                grid[(x, y + top)] = ch
    colours = {"R": RUST, "C": CREAM, "K": INK}
    outline = set()
    for (x, y) in grid:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (x + dx, y + dy)
                if n not in grid and 0 <= n[0] < 16 and 0 <= n[1] < 16:
                    outline.add(n)
    rects = [f'<rect x="{x}" y="{y}" width="1" height="1" fill="{INK}"/>' for x, y in sorted(outline)]
    rects += [f'<rect x="{x}" y="{y}" width="1" height="1" fill="{colours[c]}"/>' for (x, y), c in sorted(grid.items())]
    return svg(32, 32, f'<g shape-rendering="crispEdges">{"".join(rects)}</g>', "0 0 16 16", "Crustates")


WORD = "crustates"
WORD_TRACK = -0.02


def word_size():
    # x-height of the wordmark is 80% of the mark's body height (30 units).
    return 24 / GROTESK.xh


def wordmark_files():
    size = word_size()
    w = GROTESK.width(WORD, size, WORD_TRACK)
    asc = 0.75 * size
    for theme in ("light", "dark", "mono-black", "mono-white"):
        color = THEMES[theme]["text"]
        d = GROTESK.path(WORD, size, 0, asc, WORD_TRACK)
        put(f"svg/wordmark-{theme}.svg",
            svg(round(w), round(asc + 0.25 * size), f'<path d="{d}" fill="{color}"/>', None, "crustates"))


def lockup_horizontal(theme):
    t = THEMES[theme]
    size = word_size()
    gap = 22
    wx = 82 + SHADOW + gap
    d = GROTESK.path(WORD, size, wx, 64, WORD_TRACK)       # baseline = body bottom
    ww = GROTESK.width(WORD, size, WORD_TRACK)
    x0, y0, x1, y1 = -6, 2, wx + ww + 6, 66 + SHADOW + 6
    bg = "" if theme != "dark" else f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="{INK}"/>'
    body = bg + mark_group(theme, theme in ("light", "dark")) + f'<path d="{d}" fill="{t["text"]}"/>'
    scale = 2
    return svg(round((x1 - x0) * scale), round((y1 - y0) * scale), body,
               f"{x0:g} {y0:g} {x1 - x0:g} {y1 - y0:g}", "Crustates")


def lockup_stacked(theme):
    t = THEMES[theme]
    size = word_size() * 0.72
    ww = GROTESK.width(WORD, size, WORD_TRACK)
    mark_w = 84 + SHADOW
    width = max(ww, mark_w) + 24
    mx = (width - mark_w) / 2 + 2
    wx = (width - ww) / 2
    baseline = 66 + SHADOW + 24 + 0.75 * size
    d = GROTESK.path(WORD, size, wx, baseline, WORD_TRACK)
    height = baseline + 0.25 * size + 8
    bg = "" if theme != "dark" else f'<rect x="0" y="0" width="{width}" height="{height}" fill="{INK}"/>'
    body = (bg + f'<g transform="translate({mx:g} -4)">{mark_group(theme, theme in ("light", "dark"))}</g>'
            + f'<path d="{d}" fill="{t["text"]}"/>')
    return svg(round(width * 2), round(height * 2), body, f"0 0 {width:g} {height:g}", "Crustates")


def lockup_files():
    for theme in THEMES:
        put(f"svg/logo-horizontal-{theme}.svg", lockup_horizontal(theme))
        put(f"svg/logo-stacked-{theme}.svg", lockup_stacked(theme))


# ---------------------------------------------------------------- product icons
def tile(fill, inner, shadow=INK):
    st = f'stroke="{INK}" stroke-width="4" stroke-linejoin="miter"'
    return (f'<rect x="9" y="9" width="52" height="52" fill="{shadow}" {st}/>'
            f'<rect x="4" y="4" width="52" height="52" fill="{fill}" {st}/>' + inner)


def tide_inner():
    st = f'fill="none" stroke="{CREAM}" stroke-width="5" stroke-linecap="square" stroke-linejoin="miter"'
    return (f'<path d="M12 25 H19 V17 H27 V25 H35 V17 H43 V25 H48" {st}/>'
            f'<path d="M12 42 H19 V34 H27 V42 H35 V34 H43 V42 H48" {st}/>')


def reef_inner():
    st = f'stroke="{INK}" stroke-width="3.5" stroke-linejoin="miter"'
    return (f'<circle cx="21" cy="15" r="5" fill="{CREAM}" {st}/>'
            f'<circle cx="34" cy="10" r="3" fill="{CREAM}" {st}/>'
            f'<rect x="12" y="24" width="36" height="8" fill="{CREAM}" {st}/>'
            f'<rect x="16" y="32" width="34" height="8" fill="{CREAM}" {st}/>'
            f'<rect x="10" y="40" width="36" height="8" fill="{CREAM}" {st}/>')


def current_inner():
    st = f'fill="none" stroke="{CREAM}" stroke-width="5" stroke-linecap="square" stroke-linejoin="miter"'
    return (f'<path d="M12 21 H42" {st}/><path d="M36 14 L43 21 L36 28" {st}/>'
            f'<path d="M48 39 H18" {st}/><path d="M24 32 L17 39 L24 46" {st}/>')


def molt_inner():
    st = f'stroke="{INK}" stroke-width="3.5" stroke-linejoin="miter"'
    ar = f'fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="square" stroke-linejoin="miter"'
    return (f'<rect x="15" y="30" width="30" height="18" fill="{CREAM}" {st}/>'
            f'<path d="M15 39 H45" {st}/>'
            f'<path d="M30 24 V11" {ar}/><path d="M23 17 L30 10 L37 17" {ar}/>')


def cast_inner():
    st = f'stroke="{INK}" stroke-width="3.5" stroke-linejoin="miter"'
    ls = f'stroke="{CREAM}" stroke-width="3.5" stroke-linejoin="miter"'
    return (f'<path d="M30 17 L16 41 M30 17 L44 41 M16 41 H44" fill="none" {ls}/>'
            f'<rect x="24" y="11" width="12" height="12" fill="{CREAM}" {st}/>'
            f'<rect x="10" y="35" width="12" height="12" fill="{CREAM}" {st}/>'
            f'<rect x="38" y="35" width="12" height="12" fill="{CREAM}" {st}/>')


def barnacle_inner():
    st = f'stroke="{INK}" stroke-width="3.5" stroke-linejoin="miter"'
    return (f'<path d="M9 48 L15 30 L23 26 H37 L45 30 L51 48 Z" fill="{CREAM}" {st}/>'
            f'<path d="M23 26 L26 34 H34 L37 26" fill="{INK}" {st}/>'
            f'<path d="M15 30 L18 48 M45 30 L42 48" fill="none" {st}/>'
            f'<rect x="24" y="10" width="4.5" height="12" fill="{INK}"/>'
            f'<rect x="31.5" y="10" width="4.5" height="12" fill="{INK}"/>')


def spawn_inner():
    # A git graph: main line, a branch that merges back, commits as cream dots.
    st = f'stroke="{INK}" stroke-width="3.5" stroke-linejoin="miter"'
    ln = f'fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="square" stroke-linejoin="miter"'
    return (f'<path d="M20 12 V48" {ln}/>'
            f'<path d="M20 22 H40 V38 H20" {ln}/>'
            f'<circle cx="20" cy="14" r="5" fill="{CREAM}" {st}/>'
            f'<circle cx="40" cy="30" r="5" fill="{CREAM}" {st}/>'
            f'<circle cx="20" cy="46" r="5" fill="{CREAM}" {st}/>')


PRODUCTS = {"tide": (BLUE, "tide_inner", "Tide"), "reef": (RUST, "reef_inner", "Reef"),
            "current": (TEAL, "current_inner", "Current"), "molt": (YELLOW, "molt_inner", "Molt"),
            "cast": (BROWN, "cast_inner", "Cast"),
            "barnacle": (VIOLET, "barnacle_inner", "Barnacle"),
            "spawn": (PINK, "spawn_inner", "Spawn")}


def product_files():
    for k, (fill, fn, name) in PRODUCTS.items():
        inner = globals()[fn]()
        put(f"svg/icon-{k}.svg", svg(256, 256, tile(fill, inner), "0 0 66 66", f"Crustates {name}"))
        put(f"svg/icon-{k}-flat.svg", svg(64, 64, f'<rect x="4" y="4" width="52" height="52" fill="{fill}" stroke="{INK}" stroke-width="4"/>' + inner, "1 1 58 58", f"Crustates {name}"))
    return
    # Flat versions for small sizes (no shadow)
    flat = lambda fill, inner: (f'<rect x="4" y="4" width="52" height="52" fill="{fill}" stroke="{INK}" '
                                f'stroke-width="4"/>' + inner)
    put("svg/icon-tide-flat.svg", svg(64, 64, flat(BLUE, tide_inner()), "1 1 58 58", "Crustates Tide"))
    put("svg/icon-reef-flat.svg", svg(64, 64, flat(RUST, reef_inner()), "1 1 58 58", "Crustates Reef"))


# ---------------------------------------------------------------- badges
def badge(parts, with_mark=False, title="badge"):
    size = 12
    pad = 10
    h = 28
    x = 2
    out = []
    segs = []
    if with_mark:
        segs.append(("mark", 34))
    for bg, fg, text in parts:
        segs.append(((bg, fg, text), MONO.width(text, size, 0.02) + 2 * pad))
    total = sum(w for _, w in segs)
    out.append(f'<rect x="{x + 3}" y="5" width="{total}" height="{h}" fill="{INK}"/>')
    cx = x
    for seg, w in segs:
        if seg == "mark":
            out.append(f'<rect x="{cx}" y="2" width="{w}" height="{h}" fill="{CREAM}"/>')
            out.append(f'<g transform="translate({cx + 4} 4) scale(0.32)">{mark_group("light", False)}</g>')
        else:
            bg, fg, text = seg
            out.append(f'<rect x="{cx}" y="2" width="{w}" height="{h}" fill="{bg}"/>')
            d = MONO.path(text, size, cx + pad, 2 + h / 2 + MONO.cap * size / 2, 0.02)
            out.append(f'<path d="{d}" fill="{fg}"/>')
        cx += w
    # dividers and frame on top
    cx = x
    for _, w in segs[:-1]:
        cx += w
        out.append(f'<line x1="{cx}" y1="2" x2="{cx}" y2="{2 + h}" stroke="{INK}" stroke-width="2.5"/>')
    out.append(f'<rect x="{x}" y="2" width="{total}" height="{h}" fill="none" stroke="{INK}" stroke-width="2.5"/>')
    W, H = total + 7, h + 6
    return svg(round(W * 2), round(H * 2), "".join(out), f"0 0 {W:g} {H:g}", title)


BADGES = {
    "badge-powered-by": ([(INK, CREAM, "POWERED BY"), (RUST, INK, "CRUSTATES")], True),
    "badge-runs-on": ([(INK, CREAM, "RUNS ON"), (RUST, INK, "CRUSTATES")], True),
    "badge-open-source": ([(INK, CREAM, "OPEN SOURCE"), (YELLOW, INK, "AGPL-3.0")], False),
    "badge-self-hosted": ([(INK, CREAM, "SELF-HOSTED"), (RUST, INK, "YOUR OWN CLOUD")], False),
    "badge-built-in-rust": ([(INK, CREAM, "BUILT IN"), (RUST, INK, "RUST")], False),
    "badge-compute-tide": ([(INK, CREAM, "COMPUTE"), (BLUE, CREAM, "TIDE")], False),
    "badge-storage-reef": ([(INK, CREAM, "STORAGE"), (RUST, INK, "REEF")], False),
    "badge-network-current": ([(INK, CREAM, "NETWORK"), (TEAL, CREAM, "CURRENT")], False),
    "badge-os-molt": ([(INK, CREAM, "UPGRADES"), (YELLOW, INK, "MOLT")], False),
    "badge-cluster-cast": ([(INK, CREAM, "CLUSTER"), (BROWN, CREAM, "CAST")], False),
    "badge-plugins-barnacle": ([(INK, CREAM, "PLUGINS"), (VIOLET, INK, "BARNACLE")], False),
    "badge-gitops-spawn": ([(INK, CREAM, "GITOPS"), (PINK, INK, "SPAWN")], False),
    "badge-made-in-nl": ([(INK, CREAM, "MADE IN"), (CREAM, INK, "THE NETHERLANDS")], False),
}


def badge_files():
    for name, (parts, m) in BADGES.items():
        title = " ".join(p[2] for p in parts).title()
        put(f"svg/{name}.svg", badge(parts, m, title))


# ---------------------------------------------------------------- emblem (seal)
def emblem(fill=CREAM, ring_text="CRUSTATES • OPEN SOURCE • YOUR OWN CLOUD • "):
    c = 120
    out = [
        f'<circle cx="{c + 7}" cy="{c + 7}" r="108" fill="{INK}"/>',
        f'<circle cx="{c}" cy="{c}" r="108" fill="{fill}" stroke="{INK}" stroke-width="5"/>',
        f'<circle cx="{c}" cy="{c}" r="74" fill="{YELLOW}" stroke="{INK}" stroke-width="3.5"/>',
    ]
    d = MONO.circle_path(ring_text, 15, c, c, 84)
    out.append(f'<path d="{d}" fill="{INK}"/>')
    # mark centred in the inner disc
    s = 1.18
    mx, my = c - 40 * s, c - 38 * s - 2
    out.append(f'<g transform="translate({mx:g} {my:g}) scale({s})">{mark_group("light", True)}</g>')
    return svg(500, 500, "".join(out), "4 4 238 238", "Crustates emblem: " + ring_text.replace(" • ", ", ").strip(" ,").lower())


def emblem_files():
    put("svg/emblem-seal.svg", emblem())
    put("svg/emblem-seal-hardware.svg",
        emblem(CREAM, "YOUR OWN CLOUD • ON YOUR OWN HARDWARE • "))


# ---------------------------------------------------------------- app & social
def centered_mark(canvas, frac, bg, border=0, theme="light"):
    x0, y0, x1, y1 = MARK_BOX
    mw, mh = x1 - x0, y1 - y0
    s = canvas * frac / max(mw, mh)
    tx = (canvas - mw * s) / 2 - x0 * s
    ty = (canvas - mh * s) / 2 - y0 * s
    frame = f'<rect width="{canvas}" height="{canvas}" fill="{bg}"/>'
    if border:
        frame += (f'<rect x="{border / 2}" y="{border / 2}" width="{canvas - border}" height="{canvas - border}" '
                  f'fill="none" stroke="{INK}" stroke-width="{border}"/>')
    return frame + f'<g transform="translate({tx:g} {ty:g}) scale({s:g})">{mark_group(theme, True)}</g>'


def app_files():
    put("svg/app-icon.svg", svg(1024, 1024, centered_mark(1024, 0.62, YELLOW, 40), None, "Crustates app icon"))
    put("svg/avatar.svg", svg(500, 500, centered_mark(500, 0.7, CREAM), None, "Crustates"))
    put("svg/avatar-dark.svg", svg(500, 500, centered_mark(500, 0.7, INK, 0, "dark"), None, "Crustates"))
    put("svg/apple-touch-icon.svg", svg(180, 180, centered_mark(180, 0.72, CREAM), None, "Crustates"))


def banner(W, H, mark_s=2.6, word_k=2.5):
    out = [f'<rect width="{W}" height="{H}" fill="{CREAM}"/>',
           f'<rect x="10" y="10" width="{W - 20}" height="{H - 20}" fill="none" stroke="{INK}" stroke-width="20"/>']
    top = (H - 630) / 2 + 70
    out.append(f'<g transform="translate(90 {top:g}) scale({mark_s})">{mark_group("light", True)}</g>')
    size = word_size() * word_k
    out.append(f'<path d="{GROTESK.path(WORD, size, 350, top + 162, WORD_TRACK)}" fill="{INK}"/>')
    for i, line in enumerate(["Your own cloud,", "on your own hardware."]):
        out.append(f'<path d="{GROTESK_MED.path(line, 46, 90, top + 280 + i * 58)}" fill="{INK}"/>')
    x = 90
    for bg, fg, text in [(BLUE, CREAM, "TIDE · COMPUTE"), (RUST, INK, "REEF · STORAGE"), (TEAL, CREAM, "CURRENT · NETWORK")]:
        w = MONO.width(text, 24, 0.02) + 40
        out.append(f'<rect x="{x + 7}" y="{top + 407:g}" width="{w}" height="58" fill="{INK}"/>')
        out.append(f'<rect x="{x}" y="{top + 400:g}" width="{w}" height="58" fill="{bg}" stroke="{INK}" stroke-width="5"/>')
        out.append(f'<path d="{MONO.path(text, 24, x + 20, top + 437, 0.02)}" fill="{fg}"/>')
        x += w + 26
    url = "crustates.eu"
    uw = MONO.width(url, 26)
    out.append(f'<path d="{MONO.path(url, 26, W - 90 - uw, top + 80)}" fill="{INK}"/>')
    return svg(W, H, "".join(out), None, "Crustates: your own cloud, on your own hardware")


def og_image():
    return banner(1200, 630)


def readme_header():
    W, H = 1600, 400
    out = [f'<rect width="{W}" height="{H}" fill="{RUST}"/>',
           f'<rect x="10" y="10" width="{W - 20}" height="{H - 20}" fill="none" stroke="{INK}" stroke-width="20"/>',
           f'<rect x="87" y="87" width="900" height="240" fill="{INK}"/>',
           f'<rect x="80" y="80" width="900" height="240" fill="{CREAM}" stroke="{INK}" stroke-width="6"/>',
           f'<g transform="translate(110 110) scale(1.9)">{mark_group("light", True)}</g>']
    size = word_size() * 1.9
    out.append(f'<path d="{GROTESK.path(WORD, size, 300, 222, WORD_TRACK)}" fill="{INK}"/>')
    out.append(f'<path d="{GROTESK_MED.path("Your own cloud, on your own hardware.", 30, 304, 282)}" fill="{INK}"/>')
    for i, k in enumerate(("tide", "reef", "current")):
        fill, fn, _ = PRODUCTS[k]
        out.append(f'<g transform="translate({1060 + i * 160} 130) scale(2.2)">{tile(fill, globals()[fn]())}</g>')
    return svg(W, H, "".join(out), None, "Crustates README header")


def social_files():
    put("svg/og-image.svg", og_image())
    put("svg/banner-social-1280x640.svg", banner(1280, 640))
    put("svg/banner-readme-1600x400.svg", readme_header())


# ---------------------------------------------------------------- write + render
def main():
    mark_files()
    wordmark_files()
    lockup_files()
    product_files()
    badge_files()
    emblem_files()
    app_files()
    social_files()

    for name, content in FILES.items():
        path = os.path.join(OUT, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)

    png = lambda src, dst, w: cairosvg.svg2png(bytestring=FILES[src].encode(), write_to=os.path.join(OUT, dst),
                                               output_width=w, output_height=w)
    os.makedirs(os.path.join(OUT, "png"), exist_ok=True)
    for size in (16, 32, 48, 64):
        png("svg/favicon.svg", f"png/favicon-{size}.png", size)
    png("svg/apple-touch-icon.svg", "png/apple-touch-icon.png", 180)
    for size in (192, 512):
        png("svg/apple-touch-icon.svg", f"png/icon-{size}.png", size)
    png("svg/app-icon.svg", "png/app-icon-1024.png", 1024)
    png("svg/avatar.svg", "png/avatar-500.png", 500)
    png("svg/avatar-dark.svg", "png/avatar-dark-500.png", 500)
    png("svg/mark-light.svg", "png/mark-light-512.png", 512)
    png("svg/icon-tide.svg", "png/icon-tide-512.png", 512)
    png("svg/icon-reef.svg", "png/icon-reef-512.png", 512)
    png("svg/emblem-seal.svg", "png/emblem-seal-1000.png", 1000)
    cairosvg.svg2png(bytestring=FILES["svg/og-image.svg"].encode(),
                     write_to=os.path.join(OUT, "png/og-image.png"), output_width=1200, output_height=630)
    for name in FILES:
        if name.startswith("svg/logo-") or name.startswith("svg/badge-"):
            base = os.path.basename(name)[:-4]
            cairosvg.svg2png(bytestring=FILES[name].encode(), write_to=os.path.join(OUT, f"png/{base}.png"),
                             scale=2)
    print(f"{len(FILES)} SVG files written to {OUT}")


if __name__ == "__main__":
    main()
