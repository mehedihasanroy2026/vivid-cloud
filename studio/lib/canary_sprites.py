"""Flat hand-drawn canary sprites (PNG with alpha) for the flat+real look.

    python lib/canary_sprites.py <outdir>     -> canary_*.png, fx_*.png and _canary_sheet.png

Side view, facing right, feet at the bottom edge of a 512 px canvas. Same ink style as flat_sprites.py.
States: perch, dizzy, faint (on its back), happy, whistle.
"""
import math
import os
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flat_sprites import Canvas, INK, SS, _hex, _shade

YEL = _hex('#FFD21F')
YEL_D = _hex('#F2A80C')
BEAK = _hex('#F47A1E')
W = 512
LW = 13


def _ell(cx, cy, rx, ry, rot=0.0, n=64, wob=0.012):
    pts = []
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    for i in range(n):
        a = 2 * math.pi * i / n
        k = 1 + wob * math.sin(3 * a + 0.6) + wob * 0.7 * math.sin(5 * a + 2.0)   # uneven hand-drawn line
        x, y = rx * math.cos(a) * k, ry * math.sin(a) * k
        pts.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return pts


def canary(path, eye='dot', beak=0.0, head_tilt=0.0, flip=False, sweat=False):
    """eye: dot | spiral | x | happy.  beak: 0 shut .. 1 wide open."""
    c = Canvas(W, W)
    # tail feathers
    tail = [(150, 300), (38, 372), (30, 408), (74, 404), (62, 432), (112, 420), (190, 356)]
    c.poly(tail, fill=YEL_D, outline=INK, width=LW)
    c.line([(60, 398), (128, 352)], width=5)
    # legs + toes (drawn first so the body overlaps their tops)
    for x in (232, 286):
        c.line([(x, 380), (x + 4, 478)], width=8)
        c.line([(x - 18, 488), (x + 4, 478), (x + 30, 488)], width=8)
    # body
    body = _ell(246, 296, 156, 118, rot=-18)
    c.poly(body, fill=YEL, outline=INK, width=LW)
    # belly shade
    sh = Canvas(W, W)
    sh.poly(_ell(262, 350, 120, 60, rot=-12), fill=_shade(YEL, 0.9))
    mask = Image.new('L', c.im.size, 0)
    ImageDraw.Draw(mask).polygon([(x * SS, y * SS) for x, y in _ell(246, 296, 144, 106, rot=-18)], fill=255)
    c.im.paste(sh.im, (0, 0), Image.composite(sh.im.split()[3], Image.new('L', c.im.size, 0), mask))
    c.d = ImageDraw.Draw(c.im)
    # wing
    wing = _ell(212, 300, 92, 58, rot=-28)
    c.poly(wing, fill=YEL_D, outline=INK, width=10)
    c.line([(160, 318), (236, 296)], width=5)
    c.line([(176, 340), (250, 314)], width=5)
    # head (can tilt around the neck)
    hx, hy = 352 + head_tilt * 0.6, 178 + abs(head_tilt) * 0.25
    c.poly(_ell(hx, hy, 92, 88), fill=YEL, outline=INK, width=LW)
    # crest: three little feathers
    for i, (dx, dy) in enumerate(((-26, -100), (0, -112), (26, -98))):
        c.line([(hx + dx * 0.5, hy - 78), (hx + dx - 6, hy + dy)], width=7)
    # beak
    bx, by = hx + 78, hy + 10
    op = 26 * beak
    c.poly([(bx, by - 22), (bx + 64, by - 4 - op * 0.5), (bx, by + 2)], fill=BEAK, outline=INK, width=8)
    c.poly([(bx, by + 4), (bx + 50, by + 8 + op), (bx, by + 24)], fill=_shade(BEAK, 0.85), outline=INK, width=8)
    # cheek
    c.ellipse((hx + 18, hy + 22, hx + 58, hy + 50), fill=(255, 150, 90, 150))
    # eye
    ex, ey = hx + 26, hy - 14
    if eye == 'dot':
        c.ellipse((ex - 17, ey - 20, ex + 17, ey + 20), fill=INK)
        c.ellipse((ex + 2, ey - 14, ex + 12, ey - 3), fill=(255, 255, 255, 255))
    elif eye == 'happy':
        c.arc(ex, ey + 10, 20, 20, 200, 340, width=9)
    elif eye == 'x':
        c.line([(ex - 17, ey - 17), (ex + 17, ey + 17)], width=9)
        c.line([(ex - 17, ey + 17), (ex + 17, ey - 17)], width=9)
    elif eye == 'spiral':
        c.ellipse((ex - 26, ey - 26, ex + 26, ey + 26), fill=(255, 255, 255, 255), outline=INK, width=6)
        pts = [(ex + (2 + 19 * t) * math.cos(t * 4.2 * math.pi), ey + (2 + 19 * t) * math.sin(t * 4.2 * math.pi))
               for t in [i / 40 for i in range(41)]]
        c.line(pts, width=5)
    if sweat:
        for dx, dy in ((-70, -96), (-104, -52)):
            x, y = hx + dx, hy + dy
            c.poly([(x, y - 22), (x + 13, y + 6), (x, y + 16), (x - 13, y + 6)], fill=(150, 215, 255, 255), outline=INK, width=5)
    if flip:
        c.im = ImageOps.flip(c.im)
    c.save(path)


def note(path):
    c = Canvas(256, 256)
    for col, w, g in ((INK, 30, 9), (_hex('#FFE23A'), 13, 0)):          # yellow note with an ink edge: reads on dark walls
        c.line([(96, 190), (96, 52), (188, 34), (188, 168)], fill=col, width=w)
        c.line([(96, 76), (188, 58)], fill=col, width=w)
        for x, y in ((66, 194), (158, 172)):
            c.poly(_ell(x, y, 36 + g, 27 + g, rot=-20, n=32), fill=col)
    c.save(path)


def heart(path):
    c = Canvas(256, 256)
    pts = []
    for i in range(80):
        t = 2 * math.pi * i / 80
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((128 + x * 6.2, 122 - y * 6.2))
    c.poly(pts, fill=_hex('#F2364A'), outline=INK, width=12)
    c.ellipse((82, 66, 108, 92), fill=(255, 255, 255, 200))
    c.save(path)


def question(path):
    c = Canvas(256, 256)
    arc = [(128 + 52 * math.cos(math.radians(a)), 92 + 52 * math.sin(math.radians(a))) for a in range(-180, 91, 9)]
    for col, w in ((INK, 44), (_hex('#FFE23A'), 24)):
        c.line(arc + [(128, 176)], fill=col, width=w)
        c.ellipse((128 - w / 2 - 3, 222 - w / 2 - 3, 128 + w / 2 + 3, 222 + w / 2 + 3), fill=col)
    c.save(path)


def gas(path):
    """Pale drifting gas wisp: soft translucent green cloud with a few drawn swirl lines."""
    c = Canvas(512, 256)
    lay = Image.new('L', c.im.size, 0)
    d = ImageDraw.Draw(lay)
    for cx, cy, rx, ry in ((130, 150, 110, 60), (260, 120, 130, 75), (390, 150, 105, 58), (200, 175, 120, 50), (330, 180, 120, 48)):
        d.ellipse(c.s(cx - rx, cy - ry, cx + rx, cy + ry), fill=95)
    lay = lay.filter(ImageFilter.GaussianBlur(14 * SS))
    c.im = Image.merge('RGBA', (*Image.new('RGB', c.im.size, (196, 232, 150)).split(), lay))
    c.d = ImageDraw.Draw(c.im)
    for x0, y0, k in ((90, 150, 1), (230, 110, -1), (350, 160, 1)):
        pts = [(x0 + t * 110, y0 + k * 16 * math.sin(t * 2 * math.pi)) for t in [i / 24 for i in range(25)]]
        c.line(pts, fill=(120, 170, 90, 150), width=5)
    c.save(path)


def puff(path):
    """Oxygen puff: white cartoon cloud with a blue ink edge."""
    c = Canvas(256, 256)
    blobs = ((92, 140, 52), (150, 150, 56), (128, 100, 50), (182, 118, 40), (70, 108, 36))
    for col, g in (((70, 150, 220, 255), 8), ((250, 253, 255, 255), 0)):
        for x, y, r in blobs:
            c.ellipse((x - r - g, y - r - g, x + r + g, y + r + g), fill=col)
    c.save(path)


STATES = {
    'canary_perch': dict(),
    'canary_chirp': dict(beak=1.0),
    'canary_dizzy': dict(eye='spiral', beak=0.6, head_tilt=-26, sweat=True),
    'canary_faint': dict(eye='x', beak=0.9, flip=True),
    'canary_happy': dict(eye='happy', beak=0.3),
    'canary_whistle': dict(eye='happy', beak=1.0),
}


def build_set(outdir):
    os.makedirs(outdir, exist_ok=True)
    for name, kw in STATES.items():
        canary(os.path.join(outdir, name + '.png'), **kw)
    note(os.path.join(outdir, 'fx_note.png'))
    heart(os.path.join(outdir, 'fx_heart.png'))
    question(os.path.join(outdir, 'fx_question.png'))
    gas(os.path.join(outdir, 'fx_gas.png'))
    puff(os.path.join(outdir, 'fx_puff.png'))


if __name__ == '__main__':
    out = sys.argv[1]
    build_set(out)
    names = list(STATES) + ['fx_note', 'fx_heart', 'fx_question', 'fx_gas', 'fx_puff']
    sheet = Image.new('RGBA', (len(names) * 260, 280), (120, 110, 100, 255))
    for i, n in enumerate(names):
        im = Image.open(os.path.join(out, n + '.png'))
        im.thumbnail((250, 250))
        sheet.alpha_composite(im, (i * 260 + 5, 15))
    sheet.save(os.path.join(out, '_canary_sheet.png'))
