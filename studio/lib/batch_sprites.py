"""Flat sprites for the EP32-41 batch: new costumes + hats, a standing bear (flat_char parts), a pig and a chicken (beast.py).

    python lib/batch_sprites.py assets/flat      -> writes the PNGs + _batch_sheet.png
Same uneven ink line and egg-head conventions as flat_sprites.py.
"""
import math
import os
import random
import sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flat_sprites as FS
from flat_sprites import Canvas, INK, _hex, _shade, HEAD
import emu_sprites as ES

LW = 12


def _wob(pts, amt, seed):
    rnd = random.Random(seed)
    return [(x + rnd.uniform(-amt, amt), y + rnd.uniform(-amt, amt)) for x, y in pts]


def _oval(cx, cy, rx, ry, n=64, seed=1, wob=1.5, fn=None):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = math.cos(a), math.sin(a)
        r = fn(x, y, i) if fn else 1.0
        pts.append((cx + rx * x * r, cy + ry * y * r))
    return _wob(pts, wob, seed)


def _hat_done(c, path):
    k = 0.84                                   # same squeeze as flat_sprites.hat (egg crown)
    small = c.im.resize((int(c.im.width * k), c.im.height), Image.LANCZOS)
    c.im = Image.new('RGBA', c.im.size, (0, 0, 0, 0))
    c.im.alpha_composite(small, ((c.im.width - small.width) // 2, 0))
    c.save(path)


# ------------------------------------------------------------------ hats (512 x 300, brim around y 200-216)
def hat(path, kind, col):
    c = Canvas(HEAD, 300)
    hc = _hex(col)
    if kind == 'bowler':
        dome = [(256 + 150 * math.cos(math.radians(a)), 190 + 150 * math.sin(math.radians(a))) for a in range(180, 361, 6)]
        c.poly(dome, fill=hc, outline=INK, width=13)
        c.d.rectangle(c.s(108, 166, 404, 192), fill=_shade(hc, 0.6))
        brim = [(256 + 236 * math.cos(math.radians(a)), 204 + 26 * math.sin(math.radians(a))) for a in range(0, 360, 6)]
        c.poly(brim, fill=_shade(hc, 0.85), outline=INK, width=11)
        c.arc(210, 110, 50, 40, 200, 260, width=8, fill=(255, 255, 255, 90))
    elif kind == 'tricorn':
        c.poly([(20, 210), (110, 70), (256, 120), (402, 70), (492, 210), (256, 250)], fill=hc, outline=INK, width=13)
        c.line([(60, 196), (256, 236), (452, 196)], fill=(214, 180, 90, 255), width=10)
        c.ellipse((236, 150, 276, 190), fill=(230, 220, 200, 255), outline=INK, width=5)
    elif kind == 'wig':                         # powdered 1700s wig: rolled curls over the ears
        top = [(256 + 214 * math.cos(math.radians(a)), 230 + 190 * math.sin(math.radians(a))) for a in range(180, 361, 6)]
        c.poly(top, fill=hc, outline=INK, width=12)
        for x in (60, 452):
            for k, y in enumerate((150, 205, 258)):
                c.ellipse((x - 46, y - 30, x + 46, y + 30), fill=_shade(hc, 0.95 - k * 0.04), outline=INK, width=9)
        for i in range(-4, 5):
            c.arc(256 + i * 40, 80 + abs(i) * 10, 24, 14, 190, 350, width=5, fill=_shade(hc, 0.7))
    elif kind == 'bonnet':                      # cloth coif / kerchief tied at the back
        dome = [(256 + 236 * math.cos(math.radians(a)), 240 + 220 * math.sin(math.radians(a))) for a in range(180, 361, 6)]
        c.poly(dome + [(492, 290), (20, 290)], fill=hc, outline=INK, width=12)
        c.line([(30, 244), (482, 244)], fill=_shade(hc, 0.7), width=10)
        for i in range(-5, 6):
            c.line([(256 + i * 36, 70 + abs(i) * abs(i) * 3), (256 + i * 40, 236)], fill=_shade(hc, 0.85), width=4)
    elif kind == 'ushanka':                     # Soviet fur hat with the ear flaps tied up and a red star
        c.d.rounded_rectangle(c.s(60, 60, 452, 220), radius=60 * SS_(), fill=_shade(hc, 0.9), outline=INK, width=12 * SS_())
        fur = (205, 196, 180, 255)
        c.d.rounded_rectangle(c.s(36, 170, 476, 246), radius=36 * SS_(), fill=fur, outline=INK, width=11 * SS_())
        rnd = random.Random(3)
        for _ in range(60):
            x, y = rnd.uniform(50, 462), rnd.uniform(180, 236)
            c.line([(x, y), (x + rnd.uniform(-6, 6), y + 10)], fill=(150, 140, 126, 255), width=3)
        star = [(256 + (34 if i % 2 == 0 else 14) * math.cos(math.radians(-90 + 36 * i)),
                 206 + (34 if i % 2 == 0 else 14) * math.sin(math.radians(-90 + 36 * i))) for i in range(10)]
        c.poly(star, fill=(210, 40, 40, 255), outline=INK, width=4)
    elif kind == 'kepi':                        # 1850s US forage cap: tilted crown, short visor
        c.poly([(110, 212), (130, 40), (400, 70), (402, 212)], fill=hc, outline=INK, width=13)
        c.d.rectangle(c.s(110, 176, 402, 212), fill=_shade(hc, 0.6), outline=INK, width=8 * SS_())
        visor = [(256 + 180 * math.cos(math.radians(a)), 216 + 40 * math.sin(math.radians(a))) for a in range(0, 181, 6)]
        c.poly([(80, 216)] + visor + [(436, 216)], fill=(26, 24, 26, 255), outline=INK, width=10)
        c.ellipse((238, 120, 274, 156), fill=(214, 180, 70, 255), outline=INK, width=5)
    elif kind == 'shako':                       # British shako: tall cylinder, plume, peak
        c.poly([(120, 214), (140, 30), (372, 30), (392, 214)], fill=hc, outline=INK, width=13)
        c.d.rectangle(c.s(122, 40, 390, 64), fill=(214, 180, 70, 255))
        c.ellipse((226, 100, 286, 160), fill=(214, 180, 70, 255), outline=INK, width=6)
        c.ellipse((236, 0, 276, 40), fill=(240, 240, 236, 255), outline=INK, width=6)
        visor = [(256 + 170 * math.cos(math.radians(a)), 216 + 36 * math.sin(math.radians(a))) for a in range(0, 181, 6)]
        c.poly([(90, 216)] + visor + [(422, 216)], fill=(26, 24, 26, 255), outline=INK, width=10)
    elif kind == 'boater':                      # flat straw boater (1900s)
        c.d.rectangle(c.s(120, 110, 392, 196), fill=hc, outline=INK, width=12 * SS_())
        c.d.rectangle(c.s(120, 160, 392, 196), fill=_hex('#2A3E7A'))
        brim = [(256 + 240 * math.cos(math.radians(a)), 204 + 28 * math.sin(math.radians(a))) for a in range(0, 360, 6)]
        c.poly(brim, fill=_shade(hc, 0.92), outline=INK, width=11)
    elif kind == 'sidecap':                     # WWII side cap (folded garrison cap) with a badge
        c.poly([(70, 214), (120, 120), (300, 80), (450, 150), (450, 214)], fill=hc, outline=INK, width=13)
        c.line([(90, 196), (446, 196)], fill=_shade(hc, 0.6), width=10)
        c.ellipse((150, 140, 190, 180), fill=(220, 200, 120, 255), outline=INK, width=5)
    _hat_done(c, path)


def SS_():
    return FS.SS


# ------------------------------------------------------------------ accessories (face frame 512)
def acc(path, kind):
    c = Canvas(HEAD, HEAD)
    if kind == 'whiskers':                      # huge Victorian moustache + mutton chops (Bazalgette)
        hair = (52, 38, 32, 255)
        for sg in (-1, 1):
            c.poly([(256 + sg * 10, 318), (256 + sg * 120, 300), (256 + sg * 175, 270), (256 + sg * 160, 330),
                    (256 + sg * 70, 352), (256 + sg * 10, 340)], fill=hair, outline=INK, width=5)
            c.poly([(256 + sg * 190, 150), (256 + sg * 214, 250), (256 + sg * 180, 360), (256 + sg * 150, 300),
                    (256 + sg * 168, 200)], fill=hair, outline=INK, width=5)
    elif kind == 'beard':
        hair = (60, 44, 34, 255)
        pts = [(256 + 200 * math.cos(math.radians(a)), 300 + 150 * math.sin(math.radians(a))) for a in range(0, 181, 6)]
        c.poly(pts, fill=hair, outline=INK, width=6)
        c.poly([(200, 330), (312, 330), (290, 360), (222, 360)], fill=(120, 40, 44, 255))
    elif kind == 'cheeks':                      # rosy cheeks (kid / dancer)
        for x in (150, 362):
            c.ellipse((x - 34, 300, x + 34, 336), fill=(240, 140, 150, 110))
    c.save(path)


# ------------------------------------------------------------------ bear (flat_char head + body)
BEAR = _hex('#6A4428')
BEAR_D = _hex('#4A2E1A')
BEAR_L = _hex('#B8895A')


def bear_head(path):
    c = Canvas(HEAD, HEAD)
    for sg in (-1, 1):                         # round ears
        ex, ey = 256 + sg * 168, 92
        c.ellipse((ex - 62, ey - 62, ex + 62, ey + 62), fill=BEAR, outline=INK, width=LW)
        c.ellipse((ex - 32, ey - 30, ex + 32, ey + 34), fill=BEAR_L)
    pts = _oval(256, 270, 214, 210, 80, 5, 2.0, lambda x, y, i: 1.0 + (0.03 if i % 3 == 0 and y < 0.2 else 0))
    c.poly(pts, fill=BEAR, outline=INK, width=LW + 2)
    rnd = random.Random(8)
    for _ in range(40):                        # fur strokes
        x, y = rnd.uniform(90, 420), rnd.uniform(110, 430)
        if ((x - 256) / 200) ** 2 + ((y - 270) / 196) ** 2 > 0.85:
            continue
        c.line([(x, y), (x + rnd.uniform(-8, 8), y + 18)], fill=BEAR_D, width=5)
    c.ellipse((166, 300, 346, 440), fill=BEAR_L, outline=INK, width=8)      # muzzle (the mouth from the face sprite lands here)
    c.poly(_oval(256, 322, 34, 22, 24, 2, 0.8), fill=INK)                  # nose
    c.ellipse((242, 312, 256, 320), fill=(255, 255, 255, 160))
    c.save(path)


def bear_body(path):
    c = Canvas(FS.BODY_W, FS.BODY_H)
    cx = FS.BODY_W / 2
    pts = []
    for i in range(80):
        a = 2 * math.pi * i / 80
        x, y = math.cos(a), math.sin(a)
        w = 0.78 + 0.26 * ((y + 1) / 2) ** 0.7
        r = 1.0 + (0.035 if i % 2 else -0.01)
        pts.append((cx + 205 * w * x * r, 262 + (226 if y < 0 else 214) * y * r))
    c.poly(pts, fill=BEAR, outline=INK, width=LW)
    c.poly(_oval(cx, 300, 120, 150, 48, 4, 2.0), fill=BEAR_L)
    rnd = random.Random(2)
    for _ in range(70):
        x, y = rnd.uniform(60, FS.BODY_W - 60), rnd.uniform(60, 470)
        c.line([(x, y), (x + rnd.uniform(-8, 8), y + 20)], fill=BEAR_D if rnd.random() < 0.7 else _shade(BEAR_L, 0.85), width=5)
    c.save(path)


# ------------------------------------------------------------------ pig (beast.py: body / head / legs, faces RIGHT)
PINK = _hex('#F2A8A8')
PINK_D = _hex('#D07E84')
PINK_L = _hex('#FFD2D0')


def pig_body(path):
    c = Canvas(512, 384)
    c.poly(_oval(250, 200, 210, 140, 80, 3, 2.0), fill=PINK, outline=INK, width=LW)
    c.arc(250, 260, 150, 60, 20, 160, width=6, fill=PINK_D)
    for x, y, r in ((180, 160, 26), (300, 130, 18), (340, 230, 22)):     # mud spots
        c.poly(_oval(x, y, r * 1.4, r, 20, x, 2.0), fill=(140, 100, 70, 200))
    pts = [(46, 170), (20, 150), (18, 120), (44, 112), (52, 138), (34, 148)]
    c.line(pts, fill=INK, width=16)
    c.line(pts, fill=PINK_D, width=8)
    c.save(path)


def pig_head(path, kind='neutral'):
    c = Canvas(320, 320)
    c.poly([(90, 70), (120, 10), (160, 80)], fill=PINK_D, outline=INK, width=9)          # ear
    c.poly(_oval(150, 170, 120, 112, 64, 7, 1.6), fill=PINK, outline=INK, width=LW)
    c.poly(_oval(262, 196, 46, 56, 40, 9, 1.0), fill=PINK_L, outline=INK, width=9)        # snout
    for y in (176, 212):
        c.ellipse((262, y - 10, 280, y + 12), fill=(110, 50, 60, 255))
    ex, ey = 176, 136
    if kind == 'shocked':
        c.ellipse((ex - 26, ey - 30, ex + 26, ey + 30), fill=(255, 255, 255, 255), outline=INK, width=6)
        c.ellipse((ex - 6, ey - 6, ex + 6, ey + 6), fill=INK)
        c.ellipse((176, 236, 206, 270), fill=(90, 30, 40, 255), outline=INK, width=5)
    elif kind == 'happy':
        c.arc(ex, ey + 8, 22, 16, 200, 340, width=8)
        c.arc(200, 236, 40, 22, 20, 150, width=7)
    elif kind == 'munch':
        c.arc(ex, ey + 8, 22, 16, 200, 340, width=8)
        c.poly(_oval(212, 250, 34, 18, 20, 3, 1.0), fill=(90, 30, 40, 255), outline=INK, width=5)
        c.poly(_oval(236, 262, 22, 16, 16, 4, 1.0), fill=(196, 160, 96, 255), outline=INK, width=4)   # a potato
    else:
        c.ellipse((ex - 20, ey - 22, ex + 20, ey + 22), fill=(255, 255, 255, 255), outline=INK, width=6)
        c.ellipse((ex - 4, ey - 8, ex + 12, ey + 10), fill=INK)
        c.line([(192, 248), (222, 252)], width=6)
    c.save(path)


PIG_POSES = {'stand': (0, 0), 'walk0': (18, -18), 'walk1': (6, -6), 'walk2': (-18, 18), 'walk3': (-6, 6)}


def pig_legs(path, pose):
    c = Canvas(512, 256)
    fa, ba = PIG_POSES[pose]
    for k, (x, ang) in enumerate(((140, ba), (175, -ba), (330, fa), (365, -fa))):
        col = PINK_D if k % 2 else PINK
        a = math.radians(ang)
        fx, fy = x + 150 * math.sin(a), 30 + 150 * math.cos(a)
        c.line([(x, 30), (fx, fy)], fill=INK, width=56)
        c.line([(x, 30), (fx, fy)], fill=col, width=40)
        c.ellipse((fx - 26, fy - 12, fx + 26, fy + 18), fill=(70, 50, 46, 255), outline=INK, width=6)     # trotter
    c.save(path)


# ------------------------------------------------------------------ chicken (beast.py, faces RIGHT)
WHITE = _hex('#F6F2EA')
WHITE_D = _hex('#D8D0C2')
COMB = _hex('#D83A2E')
BEAK = _hex('#F0B030')


def chick_body(path):
    c = Canvas(512, 384)
    pts = _oval(270, 210, 180, 140, 80, 5, 2.0, lambda x, y, i: 1.0 + (0.06 if (x < -0.5 and i % 2) else 0))
    c.poly(pts, fill=WHITE, outline=INK, width=LW)
    for k in range(5):                         # tail feathers fanning up-left
        a = math.radians(200 + k * 14)
        c.poly([(120, 200), (120 + 150 * math.cos(a) - 18, 200 + 150 * math.sin(a)),
                (120 + 160 * math.cos(a) + 18, 200 + 160 * math.sin(a))], fill=_shade(WHITE, 0.95 - k * 0.02), outline=INK, width=8)
    c.poly(_oval(280, 220, 100, 62, 40, 2, 1.5), fill=WHITE_D, outline=INK, width=7)    # wing
    for k in range(4):
        c.arc(250 + k * 22, 236, 30, 20, 20, 120, width=4, fill=_shade(WHITE_D, 0.8))
    c.save(path)


def chick_head(path, kind='neutral'):
    """Neck + head in a 256x384 card; the neck base sits at the bottom centre. 'headless' = neck stump only."""
    c = Canvas(256, 384)
    if kind == 'headless':
        c.poly([(84, 384), (88, 300), (172, 300), (176, 384)], fill=WHITE, outline=INK, width=LW)
        c.poly(_oval(130, 300, 46, 16, 24, 3, 1.0), fill=(190, 60, 60, 255), outline=INK, width=6)
        c.save(path)
        return
    c.poly([(80, 384), (96, 220), (170, 220), (180, 384)], fill=WHITE, outline=INK, width=LW)
    hx, hy = 140, 160
    for k, (x, r) in enumerate(((112, 22), (140, 28), (168, 22))):     # comb
        c.ellipse((x - r, hy - 92 - r * 0.6, x + r, hy - 92 + r * 1.2), fill=COMB, outline=INK, width=6)
    c.poly(_oval(hx, hy, 70, 68, 48, 4, 1.2), fill=WHITE, outline=INK, width=LW)
    op = 22 if kind == 'squawk' else 0
    c.poly([(hx + 60, hy - 4), (hx + 112, hy + 10), (hx + 60, hy + 20)], fill=BEAK, outline=INK, width=6)
    if op:
        c.poly([(hx + 60, hy + 22), (hx + 100, hy + 26 + op), (hx + 60, hy + 34)], fill=_shade(BEAK, 0.85), outline=INK, width=6)
    c.poly(_oval(hx + 56, hy + 50, 16, 24, 20, 2, 1.0), fill=COMB, outline=INK, width=5)     # wattle
    ex, ey = hx + 22, hy - 12
    if kind == 'shocked':
        c.ellipse((ex - 22, ey - 24, ex + 22, ey + 24), fill=(255, 255, 255, 255), outline=INK, width=6)
        c.ellipse((ex - 5, ey - 5, ex + 5, ey + 5), fill=INK)
    else:
        c.ellipse((ex - 16, ey - 16, ex + 16, ey + 16), fill=(240, 160, 40, 255), outline=INK, width=5)
        c.ellipse((ex - 7, ey - 7, ex + 8, ey + 8), fill=INK)
    c.save(path)


def chick_legs(path, pose):
    old = (ES.LEG, ES.LEG_D)
    ES.LEG, ES.LEG_D = _hex('#F0B030'), _hex('#C88A20')
    ES.legs(path, pose)
    ES.LEG, ES.LEG_D = old


# ------------------------------------------------------------------ build
def build(out):
    os.makedirs(out, exist_ok=True)
    j = lambda n: os.path.join(out, n + '.png')
    # heads
    FS.head(j('head_side_black'), 'side', '#141012')
    FS.head(j('head_side_white'), 'side', '#E6E2DA')
    FS.head(j('head_messy_brown'), 'messy', '#6A4426')
    FS.head(j('head_messy_blond'), 'messy', '#C89A48')
    # bodies (style from flat_sprites.body)
    FS.body(j('body_polish'), '#7E7A52', '#5A5638', 'uniform')
    FS.body(j('body_bluecoat'), '#2E4A7A', '#3A3A44', 'officer')
    FS.body(j('body_redcoat'), '#B42E2A', '#2A2A30', 'officer')
    FS.body(j('body_soviet'), '#5E6A4A', '#3A3E30', 'officer')
    FS.body(j('body_suit_dark'), '#2A2C34', '#22242A', 'suit')
    FS.body(j('body_suit_grey'), '#6A6E74', '#4A4C50', 'suit')
    FS.body(j('body_suit_brown'), '#6A4A34', '#4A3424', 'suit')
    FS.body(j('body_dress_red'), '#B8443A', '#5A3028', 'apron')
    FS.body(j('body_dress_blue'), '#3E6AA8', '#3A3040', 'apron')
    FS.body(j('body_dress_green'), '#5E8A4A', '#3A3028', 'apron')
    FS.body(j('body_tunic_brown'), '#8A6A44', '#5A4430', 'vest', 'plaid')
    FS.body(j('body_kid'), '#E0A030', '#4A5A7A', 'sweater')
    FS.body(j('body_waist_green'), '#3E7A5A', '#3A3530', 'waistcoat', detail='#D23A3A')
    FS.body(j('body_waist_plum'), '#6A2E5A', '#2E2228', 'suit_rose', detail='#E0B020')
    # hats
    hat(j('hat_bowler'), 'bowler', '#2A2628')
    hat(j('hat_bowler_brown'), 'bowler', '#6A4A30')
    hat(j('hat_tricorn'), 'tricorn', '#2A2430')
    hat(j('hat_wig'), 'wig', '#ECE6DA')
    hat(j('hat_bonnet'), 'bonnet', '#F0EADC')
    hat(j('hat_bonnet_red'), 'bonnet', '#C84A3A')
    hat(j('hat_ushanka'), 'ushanka', '#4A4E3A')
    hat(j('hat_kepi'), 'kepi', '#2E4A7A')
    hat(j('hat_kepi_fr'), 'kepi', '#2A3050')
    hat(j('hat_shako'), 'shako', '#1E1E24')
    hat(j('hat_boater'), 'boater', '#E8CC88')
    hat(j('hat_sidecap'), 'sidecap', '#6E6A46')
    FS.hat(j('hat_beret_khaki'), 'beret', '#6E6A46')
    acc(j('acc_whiskers'), 'whiskers')
    acc(j('acc_beard'), 'beard')
    acc(j('acc_cheeks'), 'cheeks')
    # animals
    bear_head(j('head_bear'))
    bear_body(j('body_bear'))
    pig_body(j('pig_body'))
    for k in ('neutral', 'happy', 'shocked', 'munch'):
        pig_head(j(f'pig_head_{k}'), k)
    for p in PIG_POSES:
        pig_legs(j(f'pig_legs_{p}'), p)
    chick_body(j('chick_body'))
    for k in ('neutral', 'shocked', 'squawk', 'headless'):
        chick_head(j(f'chick_head_{k}'), k)
    for p in ES.POSES:
        chick_legs(j(f'chick_legs_{p}'), p)


NEW = None


if __name__ == '__main__':
    out = sys.argv[1]
    before = set(os.listdir(out)) if os.path.isdir(out) else set()
    build(out)
    names = sorted(f for f in os.listdir(out) if f.endswith('.png') and f not in before and not f.startswith('_'))
    names = names or sorted(f for f in os.listdir(out) if f.endswith('.png') and not f.startswith('_'))
    sheet = Image.new('RGBA', (8 * 200, ((len(names) + 7) // 8) * 230), (150, 140, 120, 255))
    for i, n in enumerate(names):
        im = Image.open(os.path.join(out, n))
        im.thumbnail((190, 190))
        sheet.alpha_composite(im, ((i % 8) * 200 + 5, (i // 8) * 230 + 5))
        ImageDraw.Draw(sheet).text(((i % 8) * 200 + 5, (i // 8) * 230 + 205), n[:-4], fill=(255, 255, 255, 255))
    sheet.save(os.path.join(out, '_batch_sheet.png'))
    print(len(names), 'sprites')
