"""PIL helpers for episode art (local only: Windows fonts). Cards are 1200 x 506 (aspect 2.37 = kit.card default).

    import art_kit as A
    A.word('art/word_bear.png', 'PRIVATE BEAR')            # big outlined word card (transparent)
    A.year('art/title_1942.png', '1942', 'IRAN')           # year slam card
    A.paper('art/letter.png', 'TITLE', ['line', ...])      # paper document
    A.sign('art/sign.png', 'TEXT', bg, fg, (w, h))         # painted shop/wood sign
"""
import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FD = 'C:/Windows/Fonts/'
INK = (22, 16, 14, 255)


def font(name, size):
    for n in (name, 'arialbd.ttf'):
        try:
            return ImageFont.truetype(FD + n, size)
        except OSError:
            pass


def _fit(d, text, fname, size, maxw):
    f = font(fname, size)
    while d.textlength(text, font=f) > maxw and size > 20:
        size -= 6
        f = font(fname, size)
    return f


def word(path, text, col=(255, 236, 160, 255), size=170, fname='segoeprb.ttf', w=1200, h=506, sub=None):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f = _fit(d, text, fname, size, w - 80)
    y = h / 2 if not sub else h * 0.42
    d.text((w / 2 + 8, y + 10), text, fill=(0, 0, 0, 120), font=f, anchor='mm', stroke_width=14, stroke_fill=(0, 0, 0, 120))
    d.text((w / 2, y), text, fill=col, font=f, anchor='mm', stroke_width=14, stroke_fill=INK)
    if sub:
        fs = _fit(d, sub, fname, 90, w - 120)
        d.text((w / 2, h * 0.8), sub, fill=(255, 255, 255, 255), font=fs, anchor='mm', stroke_width=9, stroke_fill=INK)
    im.save(path)


def year(path, text, sub=None, col=(255, 214, 90, 255)):
    """Torn-paper badge with a big year (like EP31's 1932 card)."""
    w, h = 1200, 506
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(len(text))
    pts = []
    for i in range(60):
        a = 2 * math.pi * i / 60
        r = 1 + rnd.uniform(-0.04, 0.04)
        pts.append((w / 2 + 420 * math.cos(a) * r, h / 2 + 200 * math.sin(a) * r))
    d.polygon([(x + 10, y + 12) for x, y in pts], fill=(0, 0, 0, 110))
    d.polygon(pts, fill=(246, 238, 220, 255), outline=INK)
    d.line(pts + [pts[0]], fill=INK, width=12)
    f = _fit(d, text, 'segoeprb.ttf', 230, 760)
    d.text((w / 2, h / 2 - (30 if sub else 0)), text, fill=col, font=f, anchor='mm', stroke_width=12, stroke_fill=INK)
    if sub:
        d.text((w / 2, h / 2 + 125), sub, fill=INK, font=_fit(d, sub, 'segoeprb.ttf', 70, 700), anchor='mm')
    im.save(path)


def paper(path, title, lines, w=900, h=1200, hand='segoesc.ttf', bg=(240, 232, 210), ink=(30, 34, 80, 255), stamp=None):
    im = Image.new('RGB', (w, h), bg)
    d = ImageDraw.Draw(im, 'RGBA')
    rnd = random.Random(len(title))
    for _ in range(400):
        d.point((rnd.randint(0, w), rnd.randint(0, h)), fill=(120, 90, 50, 50))
    d.text((w / 2, 90), title, fill=(30, 26, 22, 255), font=_fit(d, title, 'georgiab.ttf', 64, w - 100), anchor='mm')
    d.line((70, 140, w - 70, 140), fill=(30, 26, 22, 255), width=4)
    f = font(hand, 46)
    for i, t in enumerate(lines):
        d.text((80, 190 + i * 96), t, fill=ink, font=f)
    if stamp:
        sf = font('segoeprb.ttf', 90)
        lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        ld.text((w * 0.62, h * 0.82), stamp, fill=(196, 40, 40, 220), font=sf, anchor='mm')
        x0, y0, x1, y1 = ld.textbbox((w * 0.62, h * 0.82), stamp, font=sf, anchor='mm')
        ld.rectangle((x0 - 24, y0 - 18, x1 + 24, y1 + 18), outline=(196, 40, 40, 220), width=10)
        lay = lay.rotate(12, center=(w * 0.62, h * 0.82))
        im.paste(lay, (0, 0), lay)
    im.filter(ImageFilter.GaussianBlur(0.6)).save(path)


def sign(path, text, bg=(60, 40, 28), fg=(240, 220, 160, 255), size=(1200, 400), fname='georgiab.ttf', border=True, sub=None):
    w, h = size
    im = Image.new('RGB', (w, h), bg)
    d = ImageDraw.Draw(im, 'RGBA')
    rnd = random.Random(len(text) * 7)
    for _ in range(int(w * h / 900)):                       # wood / paint grain
        y = rnd.randint(0, h)
        d.line((0, y, w, y + rnd.randint(-3, 3)), fill=(0, 0, 0, 18), width=2)
    if border:
        d.rectangle((14, 14, w - 14, h - 14), outline=fg, width=8)
    y = h / 2 if not sub else h * 0.4
    f = _fit(d, text, fname, int(h * 0.42), w - 80)
    d.text((w / 2, y), text, fill=fg, font=f, anchor='mm')
    if sub:
        d.text((w / 2, h * 0.76), sub, fill=fg, font=_fit(d, sub, fname, int(h * 0.18), w - 100), anchor='mm')
    im.filter(ImageFilter.GaussianBlur(0.7)).save(path)


def poster(path, title, lines, w=800, h=1100, bg=(232, 220, 190), fg=(40, 26, 20, 255), accent=(170, 40, 34, 255)):
    """Old letterpress poster (circus / patent medicine)."""
    im = Image.new('RGB', (w, h), bg)
    d = ImageDraw.Draw(im, 'RGBA')
    rnd = random.Random(len(title) * 3)
    for _ in range(600):
        d.point((rnd.randint(0, w), rnd.randint(0, h)), fill=(110, 80, 40, 60))
    d.rectangle((20, 20, w - 20, h - 20), outline=fg, width=10)
    d.rectangle((40, 40, w - 40, h - 40), outline=fg, width=3)
    y = 130
    d.text((w / 2, y), title, fill=accent, font=_fit(d, title, 'georgiab.ttf', 120, w - 120), anchor='mm')
    y += 130
    for i, t in enumerate(lines):
        big = i == 0
        f = _fit(d, t, 'georgiab.ttf' if big else 'georgia.ttf', 80 if big else 56, w - 120)
        d.text((w / 2, y), t, fill=fg if i % 2 == 0 else accent, font=f, anchor='mm')
        y += 120 if big else 92
    im.filter(ImageFilter.GaussianBlur(0.6)).save(path)


def label(path, text, bg=(196, 40, 40), fg=(255, 255, 255, 255), size=(600, 300), fname='segoeprb.ttf', round_=True):
    w, h = size
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if round_:
        d.rounded_rectangle((6, 6, w - 6, h - 6), radius=h // 5, fill=bg + (255,), outline=INK, width=10)
    else:
        d.rectangle((6, 6, w - 6, h - 6), fill=bg + (255,), outline=INK, width=10)
    d.text((w / 2, h / 2), text, fill=fg, font=_fit(d, text, fname, int(h * 0.5), w - 60), anchor='mm')
    im.save(path)


def badge(path, top, bottom, draw_fn=None, col=(214, 180, 70)):
    """Round unit badge (Wojtek's 'bear with a shell'): draw_fn(d, cx, cy, r) adds the emblem."""
    s = 800
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s / 2
    d.ellipse((20, 20, s - 20, s - 20), fill=col + (255,), outline=INK, width=16)
    d.ellipse((90, 90, s - 90, s - 90), fill=(240, 232, 210, 255), outline=INK, width=10)
    if draw_fn:
        draw_fn(d, c, c, 250)
    f = font('segoeprb.ttf', 60)
    d.text((c, 58), top, fill=INK, font=f, anchor='mt')
    d.text((c, s - 58), bottom, fill=INK, font=f, anchor='mb')
    im.save(path)


def glow_dot(path, col=(255, 220, 140), size=256):
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    lay = Image.new('L', im.size, 0)
    ImageDraw.Draw(lay).ellipse((size * 0.2, size * 0.2, size * 0.8, size * 0.8), fill=255)
    lay = lay.filter(ImageFilter.GaussianBlur(size * 0.12))
    im = Image.merge('RGBA', (*Image.new('RGB', im.size, col).split(), lay))
    im.save(path)


def stink(path, col=(150, 170, 70)):
    """Wavy cartoon stink lines (green)."""
    w, h = 400, 700
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for k, x0 in enumerate((110, 200, 290)):
        pts = [(x0 + 34 * math.sin(i / 6 + k), h - 20 - i * 9) for i in range(70)]
        d.line(pts, fill=INK, width=30, joint='curve')
        d.line(pts, fill=col + (255,), width=16, joint='curve')
    im.save(path)


def coins(path, n=7):
    """Stack of banknotes + coins (cash), top-ish view, transparent."""
    w, h = 700, 500
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(n)
    for k in range(n):
        x, y = 120 + rnd.uniform(0, 300), 120 + rnd.uniform(0, 160)
        box = [(x, y), (x + 260, y + 20), (x + 250, y + 150), (x - 10, y + 130)]
        d.polygon(box, fill=(150, 196, 140, 255), outline=INK)
        d.line(box + [box[0]], fill=INK, width=7)
        d.ellipse((x + 90, y + 45, x + 160, y + 105), outline=(60, 100, 60, 255), width=6)
    im.save(path)
