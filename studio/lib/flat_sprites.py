"""Draw flat 2D character parts (PNG with alpha) for flat_char.py.

Plain Python + Pillow (no Blender), so the art can be checked on its own:
    python lib/flat_sprites.py <outdir>     -> writes a preview sheet too

Style: like hand-drawn cut-out characters. White egg-shaped head with an uneven ink outline,
white eyes with pupils, lids and brows, small mouths, bean body with clothes, details drawn on.
"""
import math
import os
import sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter

SS = 4                      # supersampling for smooth edges
INK = (16, 12, 14, 255)          # near-black ink like the reference
SKIN = (252, 251, 249, 255)        # clean paper white


def _hex(h, a=255):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def _shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (c[3],)


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def s(self, *v):
        return [x * SS for x in v]

    def ellipse(self, box, fill=None, outline=None, width=0):
        self.d.ellipse(self.s(*box), fill=fill, outline=outline, width=int(width * SS))

    def line(self, pts, fill=INK, width=6, joint='curve'):
        self.d.line([(x * SS, y * SS) for x, y in pts], fill=fill, width=int(width * SS), joint=joint)
        r = width * SS / 2
        for x, y in (pts[0], pts[-1]):
            self.d.ellipse((x * SS - r, y * SS - r, x * SS + r, y * SS + r), fill=fill)

    def poly(self, pts, fill=None, outline=None, width=0):
        P = [(x * SS, y * SS) for x, y in pts]
        if fill:
            self.d.polygon(P, fill=fill)
        if outline:
            self.line(list(pts) + [pts[0]], fill=outline, width=width)

    def arc(self, cx, cy, rx, ry, a0, a1, width=6, fill=INK, n=24):
        pts = [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                cy + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
        self.line(pts, fill=fill, width=width)

    def save(self, path):
        self.im.resize((self.w, self.h), Image.LANCZOS).save(path)


# ------------------------------------------------------------------ heads
# 2026-11-17: the perfect-circle head was judged ugly. Heads are now an EGG (full cheeks, smaller crown) with a slightly
# uneven hand-drawn outline whose ink swells toward the bottom right, and eyes are white with pupils, lids and brows.
# (The old circle version is kept in flat_sprites_circle_backup.py.)
FACE_SCALE = 1.2
HEAD = 512          # px canvas; the head sits around (HCX, HCY)
HCX, HCY = 256, 262
R = 232             # old circle radius: hats are still laid out against it
LW = 13             # ink width at head size
LID = (238, 234, 238, 255)      # eyelid: a touch darker than the skin so it reads
MOUTH = (70, 30, 36, 255)


def _egg(n=96, cx=HCX, cy=HCY, rx=212, ry=236, p=2.2, taper=0.11):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        c, s = math.cos(a), math.sin(a)
        x = abs(c) ** (2 / p) * (1 if c >= 0 else -1)
        y = abs(s) ** (2 / p) * (1 if s >= 0 else -1)
        wob = 1 + 0.013 * math.sin(3 * a + 0.7) + 0.009 * math.sin(5 * a + 2.1)     # hand-drawn unevenness
        pts.append((cx + rx * x * (1 + taper * y) * wob, cy + ry * y * wob))        # y > 0 is the chin side
    return pts


def _inner(pts, lw=LW):
    k = 1 - lw / 225
    return [(HCX - 3 + (x - HCX) * k, HCY - 4 + (y - HCY) * k) for x, y in pts]     # off-centre inset = varying line


def head(path, hair=None, hair_col='#2A201C'):
    """hair: None | 'messy' | 'side'"""
    c = Canvas(HEAD, HEAD)
    pts = _egg()
    inner = _inner(pts)
    c.poly(pts, fill=INK)
    c.poly(inner, fill=SKIN)
    mask = Image.new('L', c.im.size, 0)
    ImageDraw.Draw(mask).polygon([(x * SS, y * SS) for x, y in inner], fill=255)
    # soft shading on the lower right, like a painted highlight/shadow
    sh = Image.new('L', c.im.size, 0)
    ImageDraw.Draw(sh).ellipse(c.s(210, 230, 600, 610), fill=34)
    sh = sh.filter(ImageFilter.GaussianBlur(40 * SS))
    c.im.paste(Image.new('RGBA', c.im.size, (205, 200, 212, 255)), (0, 0), ImageChops.multiply(sh, mask))
    hc = _hex(hair_col)
    hl = Canvas(HEAD, HEAD)
    if hair == 'messy':
        jag = []
        for i in range(10):
            x = 20 + (HEAD - 40) * i / 9
            jag.append((x, 150 + (26 if i % 2 else 0) + 8 * math.sin(i * 1.7)))
        hl.poly([(0, 0), (HEAD, 0)] + jag[::-1], fill=hc)
        hl.line(jag, width=5)
    elif hair == 'side':
        edge = [(HEAD, 175), (330, 112), (180, 142), (0, 215)]
        hl.poly([(0, 0), (HEAD, 0)] + edge, fill=hc)
        hl.line(edge, width=5)
    if hair:
        him = hl.im
        him.putalpha(ImageChops.multiply(him.split()[3], mask))   # hair stays inside the ink outline
        c.im.alpha_composite(him)
    c.save(path)


# faces are drawn on their own transparent layer, same frame as the head
def face(path, kind='neutral', look=(0, 0)):
    c = Canvas(HEAD, HEAD)
    ex, ey, sp, my = 256, 252, 62, 360
    px, py = 5 + look[0] * 12, 2 + look[1] * 10

    def seg(cx, rx, ry, a0, a1, n=20):
        """Eyelid: the slice of the eye ellipse between two angles, closed by a straight lid line."""
        pts = [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                ey + ry * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
        c.poly(pts, fill=LID, outline=INK, width=6)

    def eye(s, lid=-1.0, rx=32, ry=39, pupil=11, dy=0, low=1.0):
        """lid: -1 open .. 0 half shut (upper lid).  low: 1 open .. 0.3 lower lid pushed up (squint)."""
        cx = ex + s * sp
        box = (cx - rx, ey - ry, cx + rx, ey + ry)
        c.ellipse(box, fill=(255, 255, 255, 255), outline=INK, width=6)
        c.ellipse((cx + px - pupil, ey + py + dy - pupil * 1.2, cx + px + pupil, ey + py + dy + pupil * 1.2), fill=INK)
        if lid > -0.98:
            a = math.degrees(math.asin(max(-0.98, min(0.98, lid))))
            seg(cx, rx, ry, 180 - a, 360 + a)
        if low < 0.98:
            a = math.degrees(math.asin(low))
            seg(cx, rx, ry, a, 180 - a)

    def brow(s, dy=-62, tilt=0, w=8, arch=0):
        cx = ex + s * sp
        if arch:
            c.arc(cx, ey + dy + arch, 30, arch, 200, 340, width=w)
        else:
            t = tilt * s
            c.line([(cx - 30, ey + dy + t), (cx + 30, ey + dy - t)], width=w)

    def both(f, **kw):
        for s in (-1, 1):
            f(s, **kw)

    if kind == 'neutral':           # relaxed, slightly lidded
        both(eye, lid=-0.55, dy=4); both(brow, dy=-60, tilt=-2)
        c.line([(238, my), (274, my + 3)], width=7)
    elif kind == 'talk':
        both(eye, lid=-0.7); both(brow, dy=-64, arch=10)
        c.ellipse((236, my - 17, 278, my + 19), fill=MOUTH, outline=INK, width=6)
    elif kind == 'talk2':
        both(eye, lid=-0.7); both(brow, dy=-64, arch=10)
        c.ellipse((241, my - 8, 273, my + 11), fill=MOUTH, outline=INK, width=6)
    elif kind == 'oh':
        both(eye); both(brow, dy=-68, arch=12)
        c.ellipse((246, my - 10, 268, my + 12), fill=MOUTH, outline=INK, width=6)
    elif kind == 'smug':            # half lids, one brow up, side smirk
        both(eye, lid=-0.05, dy=10)
        brow(-1, dy=-50, tilt=-3); brow(1, dy=-70, arch=12)
        c.arc(264, my - 20, 28, 18, 25, 125, width=7)
    elif kind == 'happy':           # ^ ^ eyes, smile
        for s in (-1, 1):
            c.arc(ex + s * sp, ey + 12, 26, 24, 200, 340, width=9)
        both(brow, dy=-58, arch=9)
        c.arc(256, my - 20, 32, 24, 20, 160, width=8)
    elif kind == 'grin':            # closed eyes, big open smile
        for s in (-1, 1):
            c.arc(ex + s * sp, ey + 12, 28, 26, 200, 340, width=9)
        both(brow, dy=-60, arch=10)
        c.poly([(218, my - 14), (294, my - 14), (256, my + 28)], fill=MOUTH, outline=INK, width=7)
    elif kind == 'grimace':         # the one toothy face
        both(eye, pupil=8); both(brow, dy=-62, tilt=-8)
        x0, x1, y0, y1 = 220, 292, my - 20, my + 18
        c.d.rounded_rectangle(c.s(x0, y0, x1, y1), radius=10 * SS, fill=(255, 255, 255, 255), outline=INK, width=6 * SS)
        for i in range(1, 4):
            x = x0 + (x1 - x0) * i / 4
            c.line([(x, y0 + 2), (x, y1 - 2)], width=4)
        c.line([(x0 + 2, (y0 + y1) / 2), (x1 - 2, (y0 + y1) / 2)], width=4)
    elif kind == 'shocked':
        both(eye, rx=36, ry=44, pupil=7); both(brow, dy=-76, arch=13)
        c.ellipse((241, my - 18, 271, my + 20), fill=MOUTH, outline=INK, width=6)
    elif kind == 'blink':
        for s in (-1, 1):
            c.arc(ex + s * sp, ey - 6, 30, 16, 20, 160, width=8)
        both(brow, dy=-56, tilt=-2)
        c.line([(238, my), (274, my + 3)], width=7)
    elif kind == 'worried':
        both(eye, lid=-0.75, pupil=9); both(brow, dy=-60, tilt=-11)
        c.arc(256, my + 16, 26, 15, 200, 340, width=7)
    elif kind == 'stern':
        both(eye, lid=-0.3, low=0.75, dy=4); both(brow, dy=-44, tilt=11, w=10)
        c.line([(236, my + 2), (276, my + 2)], width=8)
    # features a bit bigger so they read on a phone
    k, (fx, fy) = FACE_SCALE, (256, 300)
    big = c.im.resize((int(c.im.width * k), int(c.im.height * k)), Image.LANCZOS)
    ox, oy = int(fx * SS * k - fx * SS), int(fy * SS * k - fy * SS)
    c.im = big.crop((ox, oy, ox + c.im.width, oy + c.im.height))
    c.save(path)


# ------------------------------------------------------------------ bodies
BODY_W, BODY_H = 448, 512


def body(path, cloth='#2BA39A', pants='#7A5A2E', style='sweater', pattern=None, detail='#C23A2A'):
    """Bean torso. style: sweater | vest | suit. pattern: None | 'plaid' | 'dots'."""
    c = Canvas(BODY_W, BODY_H)
    cx = BODY_W / 2
    pts = []
    n = 72
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = math.cos(a), math.sin(a)
        w = 0.70 + 0.30 * ((y + 1) / 2) ** 0.75   # bean: narrow round shoulders, wide bottom
        pts.append((cx + 198 * w * x, 262 + (226 if y < 0 else 214) * y))
    cl = _hex(cloth)
    c.poly(pts, fill=cl)
    mask = Image.new('L', c.im.size, 0)
    ImageDraw.Draw(mask).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
    lay = Image.new('RGBA', c.im.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    S = SS
    if pattern == 'plaid':
        for i in range(-2, 14):
            x = i * 44 * S
            ld.line((x, 0, x, BODY_H * S), fill=_shade(cl, 0.62)[:3] + (200,), width=9 * S)
            ld.line((x + 14 * S, 0, x + 14 * S, BODY_H * S), fill=(255, 230, 200, 110), width=3 * S)
        for j in range(0, 14):
            y = j * 44 * S
            ld.line((0, y, BODY_W * S, y), fill=_shade(cl, 0.62)[:3] + (200,), width=9 * S)
            ld.line((0, y + 14 * S, BODY_W * S, y + 14 * S), fill=(255, 230, 200, 110), width=3 * S)
    elif pattern == 'dots':
        for j in range(12):
            for i in range(12):
                x, y = (i * 40 + (20 if j % 2 else 0)) * S, j * 40 * S
                ld.ellipse((x - 7 * S, y - 7 * S, x + 7 * S, y + 7 * S), fill=_hex(detail))
    elif pattern == 'camo':      # WWII-ish blotch camo: 3 tones of blobs
        rnd = __import__('random').Random(7)
        for tone in (0.62, 0.8, 1.25):
            for _ in range(26):
                x, y = rnd.uniform(0, BODY_W) * S, rnd.uniform(0, BODY_H) * S
                r = rnd.uniform(18, 40) * S
                blob = [(x + r * (1 + 0.35 * math.sin(3 * k + x)) * math.cos(k), y + r * 0.7 * (1 + 0.3 * math.cos(2 * k + y)) * math.sin(k))
                        for k in [i * 0.5 for i in range(13)]]
                col = _shade(cl, tone) if tone < 1 else tuple(min(255, int(v * 1.0)) for v in (176, 160, 112)) + (255,)
                ld.polygon(blob, fill=col[:3] + (235,))
    elif pattern == 'stripes':   # Breton stripes
        for j in range(0, 12):
            y = (60 + j * 34) * S
            ld.rectangle((0, y, BODY_W * S, y + 13 * S), fill=_hex(detail)[:3] + (240,))
    # pants band at the bottom
    ld.rectangle((0, 418 * S, BODY_W * S, BODY_H * S), fill=_hex(pants))
    ld.line((0, 418 * S, BODY_W * S, 418 * S), fill=INK, width=6 * S)
    # side shading + highlight (painted look)
    sh = Image.new('L', c.im.size, 0)
    ImageDraw.Draw(sh).ellipse((270 * S, 40 * S, 660 * S, 620 * S), fill=55)
    sh = sh.filter(ImageFilter.GaussianBlur(45 * S))
    lay.paste(Image.new('RGBA', c.im.size, (60, 30, 60, 255)), (0, 0), sh)
    hl = Image.new('L', c.im.size, 0)
    ImageDraw.Draw(hl).ellipse((70 * S, 70 * S, 170 * S, 300 * S), fill=70)
    hl = hl.filter(ImageFilter.GaussianBlur(30 * S))
    lay.paste(Image.new('RGBA', c.im.size, (255, 255, 255, 255)), (0, 0), hl)
    from PIL import ImageChops
    a = ImageChops.multiply(lay.split()[3], mask)
    lay.putalpha(a)
    c.im.alpha_composite(lay)
    if style == 'sweater':       # collar placket + 2 buttons
        c.line([(cx, 40), (cx, 120)], width=5)
        for y in (75, 108):
            c.ellipse((cx + 8, y - 7, cx + 22, y + 7), fill=(245, 240, 230, 255), outline=INK, width=3)
        c.poly([(cx - 30, 36), (cx, 62), (cx + 30, 36)], fill=_hex(detail), outline=INK, width=4)
    elif style == 'vest':        # suspenders over a plaid shirt
        for s in (-1, 1):
            xt, x = cx + s * 46, cx + s * 74          # straps follow the bean (narrow shoulders)
            c.poly([(xt - 12, 44), (xt + 12, 44), (x + 13, 418), (x - 13, 418)], fill=(225, 170, 60, 255), outline=INK, width=4)
            for y in range(66, 410, 22):
                xx = xt + (x - xt) * (y - 44) / 374
                c.line([(xx - 2, y), (xx - 2, y + 8)], fill=(120, 80, 30, 255), width=2)
            c.ellipse((x - 11, 392, x + 11, 414), fill=(240, 200, 80, 255), outline=INK, width=3)
        for y in (80, 140):
            c.ellipse((cx - 8, y - 8, cx + 8, y + 8), fill=(245, 240, 230, 255), outline=INK, width=3)
    elif style == 'suit':
        c.poly([(cx - 70, 30), (cx, 200), (cx + 70, 30)], fill=(250, 248, 244, 255), outline=INK, width=4)
        for y in (230, 290, 350):
            c.ellipse((cx - 9, y - 9, cx + 9, y + 9), fill=INK)
    elif style == 'suit_rose':    # rich man suit: lapels, shirt, tie, a rose on the lapel, gold watch chain
        c.poly([(cx - 74, 28), (cx, 210), (cx + 74, 28)], fill=(250, 248, 244, 255), outline=INK, width=4)
        c.poly([(cx - 10, 44), (cx + 10, 44), (cx + 14, 150), (cx, 175), (cx - 14, 150)], fill=_hex(detail), outline=INK, width=4)
        for sg in (-1, 1):
            c.poly([(cx + sg * 74, 28), (cx + sg * 26, 200), (cx + sg * 104, 120)], fill=_shade(cl, 0.85), outline=INK, width=4)
        rx, ry = cx - 92, 120
        for a in range(0, 360, 72):
            ox, oy = 13 * math.cos(math.radians(a)), 13 * math.sin(math.radians(a))
            c.ellipse((rx + ox - 15, ry + oy - 15, rx + ox + 15, ry + oy + 15), fill=(214, 30, 52, 255), outline=INK, width=3)
        c.ellipse((rx - 9, ry - 9, rx + 9, ry + 9), fill=(160, 16, 36, 255), outline=INK, width=3)
        c.poly([(rx, ry + 16), (rx - 26, ry + 40), (rx - 6, ry + 30)], fill=(60, 140, 50, 255), outline=INK, width=3)
        c.arc(cx + 70, 300, 50, 26, 10, 170, width=4, fill=(240, 196, 70, 255))
        for y in (250, 320):
            c.ellipse((cx - 9, y - 9, cx + 9, y + 9), fill=INK)
    elif style == 'waistcoat':    # white shirt, waistcoat, bow tie
        c.poly([(cx - 64, 32), (cx, 230), (cx + 64, 32)], fill=(250, 248, 244, 255), outline=INK, width=4)
        for y in (250, 300, 350):
            c.ellipse((cx - 9, y - 9, cx + 9, y + 9), fill=(240, 196, 70, 255), outline=INK, width=3)
        c.poly([(cx, 88), (cx - 40, 66), (cx - 40, 110)], fill=_hex(detail), outline=INK, width=4)
        c.poly([(cx, 88), (cx + 40, 66), (cx + 40, 110)], fill=_hex(detail), outline=INK, width=4)
        c.ellipse((cx - 11, 77, cx + 11, 99), fill=_shade(_hex(detail), 0.8), outline=INK, width=4)
        c.poly([(cx + 70, 180), (cx + 120, 180), (cx + 118, 196), (cx + 72, 196)], fill=_shade(cl, 0.7), outline=INK, width=3)
    elif style == 'shirt_tie':    # office shirt, tie, pencil in the pocket
        c.poly([(cx - 9, 40), (cx + 9, 40), (cx + 16, 230), (cx, 262), (cx - 16, 230)], fill=_hex(detail), outline=INK, width=4)
        c.poly([(cx - 40, 30), (cx - 4, 46), (cx - 30, 78)], fill=(250, 250, 250, 255), outline=INK, width=4)
        c.poly([(cx + 40, 30), (cx + 4, 46), (cx + 30, 78)], fill=(250, 250, 250, 255), outline=INK, width=4)
        c.d.rectangle(c.s(cx + 58, 150, cx + 118, 210), fill=_shade(cl, 0.9), outline=INK, width=4 * SS)
        c.poly([(cx + 70, 96), (cx + 82, 96), (cx + 82, 160), (cx + 76, 172), (cx + 70, 160)], fill=(250, 200, 40, 255), outline=INK, width=3)
    elif style == 'apron':        # shopkeeper: shirt + long apron with a pocket and neck straps
        c.line([(cx - 52, 40), (cx - 80, 150)], fill=(240, 236, 226, 255), width=10)
        c.line([(cx + 52, 40), (cx + 80, 150)], fill=(240, 236, 226, 255), width=10)
        c.d.rounded_rectangle(c.s(cx - 112, 150, cx + 112, 470), radius=18 * SS, fill=(244, 238, 222, 255), outline=INK, width=4 * SS)
        c.d.rectangle(c.s(cx - 50, 250, cx + 50, 320), fill=(232, 222, 200, 255), outline=INK, width=3 * SS)
        c.line([(cx - 130, 236), (cx + 130, 236)], fill=(200, 60, 50, 255), width=8)
    elif style == 'uniform':      # GI field jacket: collar, two chest pockets, web belt with buckle
        dk = _shade(cl, 0.7)
        for sg in (-1, 1):
            c.poly([(cx + sg * 6, 40), (cx + sg * 58, 28), (cx + sg * 40, 96)], fill=dk, outline=INK, width=4)
            px = cx + sg * 70
            c.d.rounded_rectangle(c.s(px - 34, 140, px + 34, 210), radius=6 * SS, fill=dk[:3] + (120,), outline=INK, width=3 * SS)
            c.line([(px - 34, 158), (px + 34, 158)], width=3)
            c.ellipse((px - 6, 160, px + 6, 172), fill=(60, 50, 30, 255))
        c.line([(cx, 46), (cx, 330)], width=4)
        c.d.rectangle(c.s(cx - 184, 338, cx + 184, 370), fill=(150, 136, 92, 255), outline=INK, width=4 * SS)
        c.d.rectangle(c.s(cx - 22, 334, cx + 22, 374), fill=(206, 176, 90, 255), outline=INK, width=4 * SS)
        for x in range(int(cx - 170), int(cx + 176), 36):
            if abs(x - cx) > 30:
                c.line([(x, 344), (x, 364)], fill=(110, 96, 60, 255), width=3)
    elif style == 'breton':       # striped shirt with a red neckerchief
        c.poly([(cx - 46, 34), (cx + 46, 34), (cx + 18, 100), (cx, 120), (cx - 18, 100)], fill=(206, 40, 44, 255), outline=INK, width=4)
        c.poly([(cx + 10, 100), (cx + 40, 160), (cx + 18, 166)], fill=(206, 40, 44, 255), outline=INK, width=4)
    elif style == 'officer':      # grey tunic: high collar, tabs, 4 buttons, belt + strap
        c.d.rectangle(c.s(cx - 52, 24, cx + 52, 62), fill=_shade(cl, 0.6), outline=INK, width=4 * SS)
        for sg in (-1, 1):
            c.d.rectangle(c.s(cx + sg * 40 - 12, 32, cx + sg * 40 + 12, 54), fill=(200, 200, 190, 255))
        for y in (100, 160, 220, 280):
            c.ellipse((cx - 9, y - 9, cx + 9, y + 9), fill=(170, 170, 160, 255), outline=INK, width=3)
        c.d.rectangle(c.s(cx - 186, 330, cx + 186, 360), fill=(40, 30, 26, 255))
        c.line([(cx - 120, 40), (cx + 90, 332)], fill=(40, 30, 26, 255), width=14)
        c.d.rectangle(c.s(cx - 20, 326, cx + 20, 364), fill=(170, 170, 160, 255), outline=INK, width=3 * SS)
    c.poly(pts, outline=INK, width=14)
    c.save(path)


# ------------------------------------------------------------------ hats
def hat(path, kind='beanie', col='#D9A23A'):
    c = Canvas(HEAD, 300)
    hc = _hex(col)
    if kind == 'beanie':
        dome = [(256 + 238 * math.cos(math.radians(a)), 250 + 230 * math.sin(math.radians(a))) for a in range(180, 361, 6)]
        c.poly(dome, fill=hc)
        for i in range(-10, 11):
            x = 256 + i * 22
            c.line([(x, 60 + abs(i) * abs(i) * 1.2), (x * 0.98 + 5, 238)], fill=_shade(hc, 0.75), width=4)
        c.d.rounded_rectangle(c.s(14, 205, 498, 270), radius=22 * SS, fill=_shade(hc, 0.9), outline=INK, width=13 * SS)
        c.poly(dome, outline=INK, width=14)
    elif kind == 'miner':        # wide brim hat with a brass lamp
        crown = [(256 + 170 * math.cos(math.radians(a)), 205 + 150 * math.sin(math.radians(a))) for a in range(180, 361, 6)]
        c.poly(crown, fill=hc, outline=INK, width=13)
        c.d.rectangle(c.s(90, 175, 422, 205), fill=_shade(hc, 0.6))
        brim = [(256 + 250 * math.cos(math.radians(a)), 215 + 42 * math.sin(math.radians(a))) for a in range(0, 360, 6)]
        c.poly(brim, fill=_shade(hc, 0.85), outline=INK, width=13)
        c.ellipse((215, 88, 297, 170), fill=(214, 168, 60, 255), outline=INK, width=8)
        c.ellipse((236, 109, 276, 149), fill=(255, 246, 210, 255), outline=INK, width=5)
    elif kind == 'top':          # tall top hat with a band
        c.d.rounded_rectangle(c.s(140, 6, 372, 206), radius=10 * SS, fill=hc, outline=INK, width=13 * SS)
        c.d.rectangle(c.s(146, 150, 366, 196), fill=(176, 30, 44, 255))
        c.line([(146, 150), (366, 150)], width=6)
        c.line([(170, 20), (176, 140)], fill=(255, 255, 255, 70), width=10)
        brim = [(256 + 236 * math.cos(math.radians(a)), 212 + 30 * math.sin(math.radians(a))) for a in range(0, 360, 6)]
        c.poly(brim, fill=_shade(hc, 0.8), outline=INK, width=13)
    elif kind == 'visor':        # green eyeshade
        c.d.rounded_rectangle(c.s(30, 180, 482, 226), radius=16 * SS, fill=_shade(hc, 0.75), outline=INK, width=10 * SS)
        brim = [(256 + 250 * math.cos(math.radians(a)), 228 + 62 * math.sin(math.radians(a))) for a in range(0, 181, 6)]
        c.poly([(6, 228)] + brim + [(506, 228)], fill=hc[:3] + (215,), outline=INK, width=10)
    elif kind == 'flatcap':      # tweed flat cap
        dome = [(256 + 236 * math.cos(math.radians(a)), 222 + 120 * math.sin(math.radians(a))) for a in range(180, 361, 6)]
        c.poly(dome, fill=hc)
        for i in range(-9, 10):
            x = 256 + i * 24
            for j in range(4):
                y = 120 + j * 26
                c.line([(x - 6, y), (x + 6, y + 12)], fill=_shade(hc, 0.72), width=4)
        c.poly(dome, outline=INK, width=13)
        brim = [(256 + 248 * math.cos(math.radians(a)), 226 + 40 * math.sin(math.radians(a))) for a in range(0, 181, 6)]
        c.poly([(8, 222)] + brim + [(504, 222)], fill=_shade(hc, 0.8), outline=INK, width=12)
        c.ellipse((236, 92, 276, 112), fill=_shade(hc, 0.6), outline=INK, width=5)
    elif kind == 'helmet':       # M1 steel pot with camouflage netting
        dome = [(256 + 250 * math.cos(math.radians(a)), 236 + 200 * math.sin(math.radians(a))) for a in range(180, 361, 5)]
        dome = [(dome[0][0] - 10, 252)] + dome + [(dome[-1][0] + 10, 252)]
        c.poly(dome, fill=hc)
        nd = _shade(hc, 0.55)
        net = Image.new('RGBA', c.im.size, (0, 0, 0, 0))
        nd_ = ImageDraw.Draw(net)
        for i in range(-12, 13):                 # net diamonds, clipped to the dome
            x = 256 + i * 30
            nd_.line(((x - 60) * SS, 248 * SS, (x + 60) * SS, 40 * SS), fill=nd, width=4 * SS)
            nd_.line(((x + 60) * SS, 248 * SS, (x - 60) * SS, 40 * SS), fill=nd, width=4 * SS)
        mk = Image.new('L', c.im.size, 0)
        ImageDraw.Draw(mk).polygon([(x * SS, y * SS) for x, y in dome], fill=255)
        from PIL import ImageChops
        net.putalpha(ImageChops.multiply(net.split()[3], mk))
        c.im.alpha_composite(net)
        for x, y in ((150, 120), (300, 90), (380, 170), (210, 190)):          # leaf scrim tufts
            c.poly([(x, y), (x + 26, y - 18), (x + 40, y + 6), (x + 16, y + 22)], fill=(110, 120, 60, 255), outline=INK, width=3)
        c.line([(150, 70), (210, 50)], fill=(255, 255, 255, 80), width=12)
        c.poly(dome, outline=INK, width=14)
        c.d.rounded_rectangle(c.s(0, 236, 512, 268), radius=14 * SS, fill=_shade(hc, 0.8), outline=INK, width=11 * SS)
    elif kind == 'beret':        # floppy beret tilted to one side, with a little stalk
        b = [(236 + 250 * math.cos(math.radians(a)), 214 + 92 * math.sin(math.radians(a))) for a in range(0, 360, 5)]
        b = [(x + (30 if y < 200 else 0), y) for x, y in b]
        c.poly(b, fill=hc, outline=INK, width=13)
        c.d.rounded_rectangle(c.s(60, 232, 452, 262), radius=12 * SS, fill=_shade(hc, 0.75), outline=INK, width=9 * SS)
        c.line([(256, 124), (262, 96)], width=10)
        c.line([(150, 170), (250, 150)], fill=(255, 255, 255, 60), width=10)
    elif kind == 'officer_cap':  # peaked cap: high front, band, black visor, badge
        c.poly([(40, 150), (80, 70), (432, 70), (472, 150), (440, 210), (72, 210)], fill=hc, outline=INK, width=13)
        c.d.rectangle(c.s(72, 176, 440, 214), fill=_shade(hc, 0.55), outline=INK, width=8 * SS)
        visor = [(256 + 210 * math.cos(math.radians(a)), 216 + 52 * math.sin(math.radians(a))) for a in range(0, 181, 6)]
        c.poly([(46, 216)] + visor + [(466, 216)], fill=(26, 24, 26, 255), outline=INK, width=10)
        c.ellipse((236, 120, 276, 160), fill=(200, 200, 190, 255), outline=INK, width=5)
    elif kind == 'slouch':       # Australian slouch hat: dented crown, band, wide brim pinned up on the left side
        crown = [(70, 200), (110, 70), (190, 46), (256, 72), (322, 46), (402, 70), (442, 200)]
        c.poly(crown, fill=hc, outline=INK, width=13)
        c.line([(256, 76), (256, 150)], fill=_shade(hc, 0.7), width=8)
        c.d.rectangle(c.s(82, 160, 430, 198), fill=_shade(hc, 0.55), outline=INK, width=8 * SS)
        brim = [(276 + 236 * math.cos(math.radians(a)), 206 + 34 * math.sin(math.radians(a))) for a in range(-60, 181, 6)]
        c.poly([(70, 200)] + brim + [(512, 200)], fill=_shade(hc, 0.85), outline=INK, width=12)
        up = [(70, 206), (14, 60), (40, 36), (96, 150)]                    # the pinned-up side
        c.poly(up, fill=_shade(hc, 0.75), outline=INK, width=11)
        c.ellipse((40, 120, 84, 164), fill=(214, 168, 60, 255), outline=INK, width=6)   # rising-sun badge
    elif kind == 'straw':        # farmer's straw hat
        crown = [(256 + 160 * math.cos(math.radians(a)), 200 + 140 * math.sin(math.radians(a))) for a in range(180, 361, 6)]
        c.poly(crown, fill=hc, outline=INK, width=13)
        for i in range(-6, 7):
            c.line([(256 + i * 24, 80), (256 + i * 26, 196)], fill=_shade(hc, 0.8), width=3)
        c.d.rectangle(c.s(98, 168, 414, 200), fill=(150, 50, 40, 255))
        brim = [(256 + 252 * math.cos(math.radians(a)), 210 + 44 * math.sin(math.radians(a))) for a in range(0, 360, 6)]
        c.poly(brim, fill=_shade(hc, 0.9), outline=INK, width=12)
    k = 0.84                                  # egg crown is narrower than the old circle head
    small = c.im.resize((int(c.im.width * k), c.im.height), Image.LANCZOS)
    c.im = Image.new('RGBA', c.im.size, (0, 0, 0, 0))
    c.im.alpha_composite(small, ((c.im.width - small.width) // 2, 0))
    c.save(path)


def acc(path, kind):
    """Face accessories in the face frame (after FACE_SCALE): eyes at x 182 / 330, y 242; mouth y 372."""
    c = Canvas(HEAD, HEAD)
    if kind == 'glasses':
        for x in (180, 332):
            c.ellipse((x - 50, 192, x + 50, 292), fill=(220, 236, 255, 40), outline=INK, width=9)
            c.arc(x - 8, 220, 26, 20, 200, 260, width=6, fill=(255, 255, 255, 200))
        c.arc(256, 238, 26, 14, 200, 340, width=8)
        c.line([(130, 236), (62, 222)], width=8)
        c.line([(382, 236), (450, 222)], width=8)
    elif kind == 'moustache':
        for sg in (-1, 1):
            pts = [(256, 318)]
            for i in range(13):
                t = i / 12
                pts.append((256 + sg * (12 + 88 * t), 316 + 26 * math.sin(t * math.pi) - 22 * t * t))
            for i in range(12, -1, -1):
                t = i / 12
                pts.append((256 + sg * (12 + 88 * t), 316 + 46 * math.sin(t * math.pi * 0.9) - 18 * t * t + 6))
            c.poly(pts, fill=(48, 34, 30, 255), outline=INK, width=5)
    c.save(path)


def build_ep28(outdir):
    """EP28 Agloe cast. Only adds files: the EP27 parts stay as they are."""
    head(os.path.join(outdir, 'head_side_grey.png'), 'side', '#9A9690')
    head(os.path.join(outdir, 'head_messy_red.png'), 'messy', '#8A3A1E')
    head(os.path.join(outdir, 'head_side_dark.png'), 'side', '#1E1612')
    body(os.path.join(outdir, 'body_waistcoat.png'), '#3A5BA8', '#3A3530', 'waistcoat', detail='#D23A3A')
    body(os.path.join(outdir, 'body_shirt_tie.png'), '#8EC7E8', '#4A4038', 'shirt_tie', detail='#2C4E9C')
    body(os.path.join(outdir, 'body_suit_rose.png'), '#6A2E4E', '#2E2228', 'suit_rose', detail='#E0B020')
    body(os.path.join(outdir, 'body_apron.png'), '#3E8C4A', '#5A4028', 'apron', pattern='plaid')
    hat(os.path.join(outdir, 'hat_top.png'), 'top', '#242026')
    hat(os.path.join(outdir, 'hat_visor.png'), 'visor', '#2FA35A')
    hat(os.path.join(outdir, 'hat_flatcap.png'), 'flatcap', '#8A6A4A')
    acc(os.path.join(outdir, 'acc_glasses.png'), 'glasses')
    acc(os.path.join(outdir, 'acc_moustache.png'), 'moustache')


def build_ep29(outdir):
    """EP29 Ghost Army cast: patterned costumes (camo, Breton stripes), helmets, berets, officer cap."""
    head(os.path.join(outdir, 'head_side_blond.png'), 'side', '#B8893E')
    body(os.path.join(outdir, 'body_gi_camo.png'), '#5E6B3A', '#4A4A2E', 'uniform', pattern='camo')
    body(os.path.join(outdir, 'body_gi_olive.png'), '#6A7040', '#4A4A2E', 'uniform')
    body(os.path.join(outdir, 'body_breton.png'), '#F2EEE4', '#2E3A5A', 'breton', pattern='stripes', detail='#2A3E8C')
    body(os.path.join(outdir, 'body_breton_red.png'), '#F2EEE4', '#5A4A38', 'breton', pattern='stripes', detail='#B83030')
    body(os.path.join(outdir, 'body_officer.png'), '#6E7470', '#3A3E3C', 'officer')
    hat(os.path.join(outdir, 'hat_helmet.png'), 'helmet', '#5E6838')
    hat(os.path.join(outdir, 'hat_beret.png'), 'beret', '#22262E')
    hat(os.path.join(outdir, 'hat_beret_red.png'), 'beret', '#9A2A30')
    hat(os.path.join(outdir, 'hat_officer.png'), 'officer_cap', '#6E7470')


def build_ep31(outdir):
    """EP31 Emu War cast: khaki Australian uniforms, slouch hats, the Major's peaked cap, a farmer in braces."""
    head(os.path.join(outdir, 'head_side_ginger.png'), 'side', '#A8542A')
    body(os.path.join(outdir, 'body_khaki.png'), '#B79E66', '#8C7548', 'uniform')
    body(os.path.join(outdir, 'body_khaki_dark.png'), '#9C8452', '#6E5C3A', 'uniform')
    body(os.path.join(outdir, 'body_major.png'), '#8E7A4E', '#5E4E34', 'officer')
    hat(os.path.join(outdir, 'hat_slouch.png'), 'slouch', '#8A7A52')
    hat(os.path.join(outdir, 'hat_major.png'), 'officer_cap', '#8E7A4E')
    hat(os.path.join(outdir, 'hat_straw.png'), 'straw', '#E2C27A')


EXPRESSIONS = ['neutral', 'talk', 'talk2', 'oh', 'smug', 'happy', 'grin', 'grimace', 'shocked', 'blink', 'worried', 'stern']


def build_set(outdir):
    os.makedirs(outdir, exist_ok=True)
    head(os.path.join(outdir, 'head_messy.png'), 'messy')
    head(os.path.join(outdir, 'head_side.png'), 'side', '#5A3A22')
    head(os.path.join(outdir, 'head_bald.png'), None)
    for k in EXPRESSIONS:
        face(os.path.join(outdir, f'face_{k}.png'), k)
    body(os.path.join(outdir, 'body_sweater.png'), '#13B3A6', '#7A5528', 'sweater')
    body(os.path.join(outdir, 'body_plaid.png'), '#E0402A', '#6E4622', 'vest', 'plaid')
    hat(os.path.join(outdir, 'hat_beanie.png'), 'beanie', '#F0B02C')
    hat(os.path.join(outdir, 'hat_miner.png'), 'miner', '#9A6A34')


if __name__ == '__main__':
    out = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == 'ep28':
        build_ep28(out)
        sys.exit()
    if len(sys.argv) > 2 and sys.argv[2] == 'ep31':
        build_ep31(out)
        sys.exit()
    if len(sys.argv) > 2 and sys.argv[2] == 'ep29':
        build_ep29(out)
        sys.exit()
    build_set(out)
    # preview sheet
    names = sorted(f for f in os.listdir(out) if f.endswith('.png') and not f.startswith('_'))
    sheet = Image.new('RGBA', (6 * 260, ((len(names) + 5) // 6) * 300), (120, 110, 100, 255))
    for i, n in enumerate(names):
        im = Image.open(os.path.join(out, n))
        im.thumbnail((250, 250))
        if n.startswith('face_'):
            base = Image.open(os.path.join(out, 'head_bald.png'))
            base.thumbnail((250, 250))
            base.alpha_composite(im)
            im = base
        sheet.alpha_composite(im, ((i % 6) * 260, (i // 6) * 300))
        ImageDraw.Draw(sheet).text(((i % 6) * 260 + 5, (i // 6) * 300 + 270), n, fill=(255, 255, 255, 255))
    sheet.save(os.path.join(out, '_sheet.png'))
