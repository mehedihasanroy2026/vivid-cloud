"""Flat hand-drawn emu sprites (PNG with alpha) for the flat+real look (EP31 Emu War).

    python lib/emu_sprites.py <outdir>     -> emu_*.png + _emu_sheet.png

Side view, facing RIGHT. Three layers so the bird can run and bob:
  emu_body.png          512x384  shaggy body + drooping tail (no legs, no neck)
  emu_neck_<e>.png      256x512  neck + head; the neck base sits at the bottom centre
  emu_legs_<pose>.png   512x512  both legs; the hips sit at the top centre, feet at the bottom edge
Same uneven ink line as flat_sprites.py / canary_sprites.py.
"""
import math
import os
import random
import sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flat_sprites import Canvas, INK, _hex, _shade

FEATHER = _hex('#5A3F2A')
FEATHER_D = _hex('#3B281B')
FEATHER_L = _hex('#8A6A48')
NECK = _hex('#8FA2B4')        # blue-grey bare neck
NECK_D = _hex('#6C7F92')
BEAK = _hex('#3A3430')
EYE = _hex('#F08A1C')         # orange iris
LEG = _hex('#9A8C78')
LEG_D = _hex('#6E6252')
LW = 12


def _wob(pts, amt, seed):
    rnd = random.Random(seed)
    return [(x + rnd.uniform(-amt, amt), y + rnd.uniform(-amt, amt)) for x, y in pts]


def body(path):
    c = Canvas(512, 384)
    rnd = random.Random(4)
    # shaggy outline: an egg with ragged feather tips along the bottom and the tail (left)
    pts = []
    n = 90
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = math.cos(a), math.sin(a)
        rx, ry = 210, 128
        if x < -0.3:                        # tail end droops
            ry *= 1.0 + 0.25 * (-x - 0.3)
        r = 1.0
        if y > 0.15 or x < -0.6:            # ragged feather tips
            r += (0.09 if i % 2 else -0.02) + rnd.uniform(-0.02, 0.03)
        pts.append((262 + rx * x * r, 176 + ry * y * r + (28 if x < -0.5 and y > 0 else 0)))
    c.poly(pts, fill=FEATHER, outline=INK, width=LW)
    # feather strokes: darker hatch + a few light flecks
    for _ in range(70):
        x, y = rnd.uniform(90, 430), rnd.uniform(90, 290)
        if ((x - 262) / 200) ** 2 + ((y - 180) / 120) ** 2 > 0.8:
            continue
        L = rnd.uniform(22, 44)
        c.line([(x, y), (x - L * 0.55, y + L)], fill=FEATHER_D, width=5)
    for _ in range(26):
        x, y = rnd.uniform(130, 400), rnd.uniform(90, 200)
        if ((x - 262) / 190) ** 2 + ((y - 170) / 110) ** 2 > 0.7:
            continue
        c.line([(x, y), (x - 10, y + 18)], fill=FEATHER_L, width=4)
    # wing hint
    c.arc(300, 170, 90, 60, 150, 300, width=6, fill=INK)
    c.save(path)


def neck(path, kind='neutral'):
    """kind: neutral | smug | shocked | squawk."""
    c = Canvas(256, 512)
    # neck: a curved tube from the bottom centre up to the head (head toward +x)
    spine = [(128, 512), (122, 430), (112, 340), (116, 250), (132, 170), (150, 118)]
    left = [(x - w, y) for (x, y), w in zip(spine, (34, 30, 26, 23, 22, 22))]
    right = [(x + w, y) for (x, y), w in zip(spine, (34, 30, 26, 23, 22, 22))]
    c.poly(left + right[::-1], fill=NECK, outline=INK, width=LW)
    # a fluff of feathers where the neck meets the body
    for i in range(7):
        x = 90 + i * 12
        c.line([(x, 470), (x - 8, 506)], fill=FEATHER_D, width=7)
    c.line([(104, 300), (108, 220)], fill=NECK_D, width=5)
    # head
    hx, hy = 150, 92
    head = _wob([(hx + 64 * math.cos(a) * (1.12 if math.cos(a) > 0 else 1), hy + 56 * math.sin(a))
                 for a in [2 * math.pi * i / 48 for i in range(48)]], 1.5, 9)
    c.poly(head, fill=NECK, outline=INK, width=LW)
    # dark head fuzz on the crown
    for i in range(6):
        x = hx - 40 + i * 13
        c.line([(x, hy - 50), (x + 4, hy - 68)], fill=FEATHER_D, width=6)
    # beak: short, wide, slightly hooked
    bx, by = hx + 66, hy + 10
    op = 18 if kind == 'squawk' else 0
    c.poly([(bx - 6, by - 14), (bx + 44, by - 2), (bx + 46, by + 4), (bx - 6, by + 6)], fill=BEAK, outline=INK, width=7)
    c.poly([(bx - 6, by + 8), (bx + 38, by + 8 + op), (bx - 6, by + 20 + op * 0.6)], fill=_shade(BEAK, 1.3), outline=INK, width=7)
    # eye: big orange iris, black pupil, highlight; lids by expression
    ex, ey = hx + 18, hy - 8
    if kind == 'shocked':
        c.ellipse((ex - 30, ey - 32, ex + 30, ey + 32), fill=(255, 255, 255, 255), outline=INK, width=6)
        c.ellipse((ex - 6, ey - 6, ex + 6, ey + 6), fill=INK)
    else:
        c.ellipse((ex - 26, ey - 26, ex + 26, ey + 26), fill=EYE, outline=INK, width=6)
        c.ellipse((ex - 10, ey - 10, ex + 13, ey + 13), fill=INK)
        c.ellipse((ex + 2, ey - 12, ex + 11, ey - 3), fill=(255, 255, 255, 255))
        if kind == 'smug':                    # heavy half lid + a raised brow: the "you missed" look
            c.poly([(ex - 30, ey - 30), (ex + 30, ey - 30), (ex + 30, ey + 1), (ex - 30, ey - 2)], fill=NECK_D, outline=None)
            c.line([(ex - 28, ey - 2), (ex + 28, ey + 1)], width=8)
            c.line([(ex - 24, ey - 42), (ex + 26, ey - 52)], width=8)
        elif kind == 'squawk':
            c.line([(ex - 20, ey - 34), (ex + 22, ey - 28)], width=7)
    c.save(path)


# leg poses: (hip angle, knee bend, foot lift) per leg, front leg first. Angles in degrees from straight down, + = forward
POSES = {
    'stand': ((4, 10, 0), (-4, 10, 0)),
    'run0': ((34, 24, 0), (-28, 20, 30)),      # front foot reaching, back leg kicking up
    'run1': ((22, 80, 50), (-8, 14, 0)),       # passing: front leg tucked high
    'run2': ((-28, 20, 30), (34, 24, 0)),
    'run3': ((-8, 14, 0), (22, 80, 50)),
    'peck': ((10, 26, 0), (-12, 22, 0)),
}


def legs(path, pose):
    c = Canvas(512, 512)
    hip = (256, 40)
    thigh, shin = 135, 215
    for k, (ha, kb, lift) in enumerate(POSES[pose]):
        dx = -10 if k else 10
        hx, hy = hip[0] + dx, hip[1]
        a1 = math.radians(ha)
        kx, ky = hx + thigh * math.sin(a1), hy + thigh * math.cos(a1)
        a2 = math.radians(ha - kb - 8)                     # ostrich-style knee: the shin swings back
        fx, fy = kx + shin * math.sin(a2), ky + shin * math.cos(a2)
        fy = min(fy, 490 - lift)
        col, cold = (LEG, LEG_D) if k == 0 else (_shade(LEG, 0.8), _shade(LEG_D, 0.8))
        c.line([(hx, hy), (kx, ky)], fill=INK, width=54)
        c.line([(hx, hy), (kx, ky)], fill=cold, width=38)
        c.line([(kx, ky), (fx, fy)], fill=INK, width=32)
        c.line([(kx, ky), (fx, fy)], fill=col, width=19)
        # three toes
        for t in (-22, 6, 30):
            tx, ty = fx + 52 * math.cos(math.radians(t)), fy + 14 * math.sin(math.radians(t + 30)) + (4 if lift else 8)
            c.line([(fx, fy), (tx, ty)], fill=INK, width=14)
            c.line([(fx, fy), (tx, ty)], fill=col, width=6)
    c.save(path)


def build_set(outdir):
    os.makedirs(outdir, exist_ok=True)
    body(os.path.join(outdir, 'emu_body.png'))
    for k in ('neutral', 'smug', 'shocked', 'squawk'):
        neck(os.path.join(outdir, f'emu_neck_{k}.png'), k)
    for p in POSES:
        legs(os.path.join(outdir, f'emu_legs_{p}.png'), p)


if __name__ == '__main__':
    out = sys.argv[1]
    build_set(out)
    # preview sheet: the assembled bird in every leg pose + every neck
    sheet = Image.new('RGBA', (len(POSES) * 300, 760), (150, 130, 100, 255))
    b = Image.open(os.path.join(out, 'emu_body.png')).resize((256, 192))
    for i, p in enumerate(POSES):
        lg = Image.open(os.path.join(out, f'emu_legs_{p}.png')).resize((256, 256))
        nk = Image.open(os.path.join(out, f'emu_neck_{list(("neutral", "smug", "shocked", "squawk", "neutral", "smug"))[i]}.png')).resize((128, 256))
        x0 = i * 300 + 20
        sheet.alpha_composite(lg, (x0, 440))
        sheet.alpha_composite(b, (x0, 300))
        sheet.alpha_composite(nk, (x0 + 150, 110))
    sheet.save(os.path.join(out, '_emu_sheet.png'))
