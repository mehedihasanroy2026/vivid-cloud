"""Episode 30 - Why You See Stars When You Rub Your Eyes. VIVID look, EP22 kit, 7 places, 25 shots.
BED night bedroom (Mia rubbing her eyes, loop) | VIS behind the eyelids: dark void with glowing swirls, sparkles and a
glowing checkerboard | EYE inside the eye: rows of little light-cell guys on the retina, a light beam, a giant finger squeezes |
BRN brain HQ: Zed reads the LIGHT signal, a giant finger presses the LIGHT button, low-blood alarm, IN HERE |
THT brain theater: fireworks on the screen, PHOSPHENES | KIT kitchen: Mia stands up too fast, stars | TWR colourful rooftop
"""
import sys
import os
import math
import random
import bpy

_a = sys.argv[sys.argv.index('--') + 1:]
ROOT = _a[_a.index('--root') + 1]
for sub in ('lib', 'sets'):
    sys.path.insert(0, os.path.join(ROOT, sub))
import toon as _toon
_toon.PAINT = 0.0
import assets
assets.ROOT = os.path.join(ROOT, 'assets')
from toon import clear_scene, ellipsoid, cone, tube, box, cylinder, empty, text_obj, SetBuilder
from acting import F, deg, W, A, shake, bob, nod, head_shake, _linear
import real
import vivid as V
import vsets as VS
import doodle_char as dc
import ep_common as E
import ep_kit as K
from ep_common import at, face, person, arms, legs, place, neck, lean, hold, sit, stand, show
from ep_kit import pop_in, word_pop, sign_pop, cs

args = E.std_args()
HERE = os.path.join(ROOT, 'episodes', '30_eye_stars')
clear_scene()
E.init(HERE, args)
V.setup(args.pct, args.samples)
SETS = ['bed', 'vis', 'eye', 'brn', 'tht', 'kit', 'twr']
BED, VIS, EYE, BRN, THT, KIT, TWR = [(300.0 * i, 0, 0) for i in range(len(SETS))]
random.seed(30)
SKIN = V.paint('FingerSkin', '#F2C7A5', rough=0.5, grime=0)
NAIL = V.paint('FingerNail', '#FFE4E8', rough=0.2, grime=0)
GLOWC = ('#FF4FD8', '#3FE0F8', '#FFD23F', '#7CF05A', '#FF7A3A', '#B48AFF')


def ring(nm, center, r, col, parent=None, n=24, th=0.12, k=6.0):
    """glowing swirl: an open spiral (1.6 turns) in the XZ plane around a pivot empty (rotate Y to spin)"""
    piv = empty(nm, center, parent)
    pts = []
    for i in range(n * 2):
        a = 2 * math.pi * 1.6 * i / (n * 2)
        rr = r * (0.25 + 0.75 * i / (n * 2))
        pts.append((rr * math.cos(a), 0, rr * math.sin(a)))
    tube(nm + 'Ob', pts, th, VS.glow(nm + 'M', col, k), piv)
    return piv


# ---------------------------------------------------------------- new set: behind the eyelids
def lid_void(nm, origin):
    """dark violet void (the inside of your closed eyelids): glowing checkerboard on the back wall, spirals, sparkles.
    returns 'show' = every glowing object (hidden at 'nowhere'), 'spins' = spiral pivots. SKY night"""
    glowing = []
    with SetBuilder(nm, origin) as root:
        dark = V.pat(nm + 'Wall', '#140E33', '#1B1442', 'dots', scale=0.6, mode='wall', grime=0)
        darkx = V.pat(nm + 'WallX', '#140E33', '#1B1442', 'dots', scale=0.6, mode='wallx', grime=0)
        VS.room(nm, 12, 9, -12, 13, dark, V.paint(nm + 'Floor', '#120C2C'), wallx=darkx, trim='#2B1A5A', ceil='#120C2C')
        for i in range(8):
            for j in range(5):
                c = ('#FF4FD8', '#3FE0F8') if (i + j) % 2 else ('#2A1A66', '#2A1A66')
                ob = box(f'{nm}Chk{i}{j}', (1.9, 0.1, 1.9), (-7.0 + i * 2.0, 8.7, 2.2 + j * 2.0),
                         VS.glow(f'{nm}Chk{c[0]}', c[0], 3.0 if c[0] != '#2A1A66' else 0.4))
                if (i + j) % 2:
                    glowing.append(ob)
    spins = []
    for k, (x, y, z, r, c) in enumerate(((-5.0, 3.0, 6.5, 2.4, '#FFD23F'), (4.6, 1.5, 7.2, 2.0, '#7CF05A'),
                                          (0.5, 5.5, 4.0, 2.8, '#FF7A3A'), (-1.5, -1.0, 9.0, 1.4, '#B48AFF'))):
        p = ring(f'{nm}Swirl{k}', W(origin, (x, y, z)), r, c)
        spins.append(p)
        glowing += list(p.children)
    for k in range(40):
        p = W(origin, (random.uniform(-10, 10), random.uniform(-4, 7), random.uniform(1.5, 11.5)))
        s = ellipsoid(f'{nm}Spk{k}', (0.12, 0.12, 0.12), p, VS.glow(f'{nm}SpkM{k % 6}', GLOWC[k % 6], 8), segs=8, rings=6)
        glowing.append(s)
    real.area(W(origin, (0, -8, 12)), (30, 0, 0), 14, 120, '#B48AFF', shadow=False, name=nm + 'Fill', volume=0.0)
    return {'root': root, 'show': glowing, 'spins': spins}


# ---------------------------------------------------------------- new set: inside the eye (retina)
def cell_guy(nm, loc, col):
    """little retina cell: tall body, round head with two eyes (faces -y). 'lit' = bright glowing head shown when firing"""
    r = empty(nm, loc)
    body = V.paint('CellBody' + col, col, rough=0.4, grime=0)
    cylinder(nm + 'B', 0.38, 2.4, (0, 0, 1.2), body, r, outline=0.03)
    ellipsoid(nm + 'H', (0.6, 0.55, 0.6), (0, 0, 2.95), V.paint('CellHead', '#E8D8F0', rough=0.3, grime=0), r, outline=0.04, segs=16, rings=10)
    lit = ellipsoid(nm + 'L', (0.66, 0.6, 0.66), (0, 0, 2.95), VS.glow('CellLit', '#FFF07A', 6.0), r, segs=16, rings=10)
    for sx in (-1, 1):
        ellipsoid(f'{nm}E{sx}', (0.09, 0.05, 0.13), (sx * 0.2, -0.6, 3.05), VS.ink(), r, segs=8, rings=4)
    return r, lit


def eye_room(nm, origin):
    """inside the eyeball: curved pink retina wall with red veins at the back, rows of cell guys on the floor (y 3..7),
    the round lens/pupil window high on the front-left. SKY indoor"""
    with SetBuilder(nm, origin) as root:
        wall = V.pat(nm + 'Wall', '#FF8A9A', '#F2707F', 'wallpaper', scale=0.5, mode='wall', c3='#D8344A')
        wallx = V.pat(nm + 'WallX', '#FF8A9A', '#F2707F', 'wallpaper', scale=0.5, mode='wallx', c3='#D8344A')
        VS.room(nm, 12, 9, -12, 12, wall, V.pat(nm + 'Floor', '#E8586A', '#FF8A9A', 'dots', scale=0.8, mode='floor'),
                wallx=wallx, trim='#B8233A', ceil='#E8586A')
        for k in range(5):
            a = -0.6 + k * 0.3
            tube(f'{nm}Vein{k}', [(0, 8.8, 6), (6 * math.sin(a), 8.8, 6 + 5 * math.cos(a)), (11 * math.sin(a), 8.8, 6 + 8 * math.cos(a))],
                 0.16, V.paint('Vein', '#B8233A', grime=0), outline=0.0)
        cylinder(nm + 'Optic', 1.4, 0.2, (0, 8.8, 6), V.paint('OpticM', '#FFE4C8', grime=0), rot=(90, 0, 0), outline=0.04)
        VS.sign(nm + 'Lbl', 'BACK OF YOUR EYE', (0, 8.6, 10.4), 0.45, board='#2B2A72', inkc='#FFE07A', k=1.0)
        VS.lamp(nm + 'Lamp', (-4, 1, 11.4), shade='#FFD23F', power=700, cord=1.2)
        VS.lamp(nm + 'Lamp2', (4, 1, 11.4), shade='#FFD23F', power=700, cord=1.2)
        real.area((0, -8, 11.6), (30, 0, 0), 16, 650, '#FFE6C8', shadow=False, name=nm + 'Fill', volume=0.0)
    cells = []
    for row, y in enumerate((3.0, 5.0, 7.0)):
        for i in range(7):
            x = -6.0 + i * 2.0 + (1.0 if row % 2 else 0.0)
            c = ('#8A6AE8', '#3FB8E8', '#FF7AB6')[(i + row) % 3]
            cells.append((x, y) + cell_guy(f'{nm}Cell{row}{i}', W(origin, (x, y, 0)), c))
    return {'root': root, 'cells': cells}


def finger(nm, loc, rot=(0, 0, 0)):
    """giant fingertip pointing along -x from its root (root at the knuckle end)"""
    r = empty(nm, loc)
    r.rotation_euler = deg(*rot)
    ellipsoid(nm + 'F', (3.6, 1.0, 1.0), (-3.6, 0, 0), SKIN, r, outline=0.06, segs=24, rings=12)
    ellipsoid(nm + 'N', (0.9, 0.75, 0.25), (-6.2, 0, 0.75), NAIL, r, outline=0.03, segs=16, rings=8)
    for k in (-1.8, -3.0):
        tube(f'{nm}Crease{k}', [(k, -0.9, 0.5), (k, -0.98, 0), (k, -0.9, -0.5)], 0.03, VS.ink(), r)
    return r


def burst(nm, center, t, col, n=16, r=1.8, life=0.8):
    """firework burst: n glowing balls flying out from center (in the XZ plane, slightly toward -y)"""
    m = VS.glow(nm + 'M', col, 10.0)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        b = ellipsoid(f'{nm}{i}', (0.22, 0.22, 0.22), center, m, segs=8, rings=6)
        A.set(b, 'location', 0, center)
        A.set(b, 'location', t, center)
        A.set(b, 'location', t + life, (center[0] + r * math.cos(a), center[1] - 0.3, center[2] + r * math.sin(a) - 0.3))
        A.set(b, 'scale', t, (1, 1, 1))
        A.set(b, 'scale', t + life * 0.7, (1.3, 1.3, 1.3))
        A.set(b, 'scale', t + life, (0.001,) * 3)
        out.append(b)
    show(out, [(t, t + life)])
    return out


# ---------------------------------------------------------------- sets
bed = VS.bedroom('Bed', BED)
vis = lid_void('Vis', VIS)
eye = eye_room('Eye', EYE)
brn = VS.brain_room('Brn', BRN, lever_txt='LIGHT')
tht = VS.theater('Tht', THT, screen='#4A3AA8')
kit = VS.kitchen('Kit', KIT)
twr = VS.rooftop('Twr', TWR)

E.HOOKS.update({
    'bed': lambda: V.sky('night', ambient=0.65), 'vis': lambda: V.sky('night', ambient=0.5), 'eye': lambda: V.sky('indoor', ambient=0.7),
    'brn': lambda: V.sky('indoor', ambient=0.7), 'tht': lambda: V.sky('night', ambient=0.7), 'kit': lambda: V.sky('indoor', ambient=0.8),
    'twr': lambda: V.sky('golden', ambient=0.85),
})
E.HANDLE = 8

E.make_S([('rub', None), ('show', 'a light show'), ('swirls', 'swirls'), ('checker', 'glowing'), ('shut', 'but your eyes'),
          ('where', 'so where is'), ('nowhere', 'nowhere'), ('nolight', 'there is no'), ('back', 'the back of'),
          ('cells', 'covered in cells'), ('fire', 'that fire a'), ('reads', 'and your brain reads'), ('dumb', 'but those cells'),
          ('squeeze', 'squeeze them'), ('push', 'so when you'), ('button', 'youre pressing'), ('fireworks', 'and your brain just'),
          ('phos', 'scientists call'), ('stand', 'stand up too'), ('blood', 'your brain gets'), ('misfire', 'and the same cells'),
          ('stars', 'stars'), ('colour', 'which means every'), ('outthere', 'was never out'), ('inhere', 'it was always'),
          ('end', 'now')])
S, END_T = E.S, E.END_T

# ---------------------------------------------------------------- cast
MIA = {'hair': 'bun', 'hair_col': '#5A2E1A', 'outfit': 'pajamas', 'cloth': '#8FB8FF', 'cloth2': '#FFFFFF', 'shoes': '#FF7AB6'}
ZED = {'hair': 'side', 'hair_col': '#1C1B4A', 'hat': 'headphones', 'hat_col': '#2B2A72', 'hat_col2': '#FFD23F', 'outfit': 'jacket',
       'cloth': '#FFD23F', 'cloth2': '#2B2A72', 'shoes': '#2B2A72', 'glasses': True}
MIA_AT = (1.0, 1.0, 0)
mia = person('Mia', W(BED, MIA_AT), MIA, 0)
mia2 = person('Mia2', W(KIT, (0, 2.6, 0)), MIA, 0)
zed = person('Zed', W(BRN, (2.6, 4.0, 0)), ZED, -20)
K.reset_cast()
DOWN = ((-20, 0, 15), (-20, 0, -15))
RUB_A = ((-140, 0, -24), (-140, 0, 24))
RUB_B = ((-128, 0, -36), (-128, 0, 36))


def rub(rig, t0, t1, every=0.16):
    """hands at the eyes, small circles"""
    arms(rig, t0 - 0.12, *RUB_A)
    t, k = t0, 0
    while t < t1:
        arms(rig, t, *(RUB_A if k % 2 else RUB_B))
        t += every
        k += 1


# ---------------------------------------------------------------- MIA in the bedroom
face(mia, 0, 'sleep')
arms(mia, 0, *RUB_A, jump=True)
neck(mia, 0, -8, 0, 0, jump=True)
rub(mia, 0.0, S['show'][0])
tsh0, tsh1 = S['shut']
arms(mia, tsh0 - 0.3, *DOWN)
face(mia, tsh0, 'sleep')
tw0, tw1 = S['where']
face(mia, tw0, 'worried')
neck(mia, tw0, 10, 0, 15, jump=True)
arms(mia, tw0, (-20, 0, 15), (-110, 0, -40), jump=True)
word_pop('BedQ', '?', W(BED, (2.4, 0.4, 7.6)), 1.0, '#FFE14A', at('light', tw0) - 0.05, tw1)
tp0, tp1 = S['push']
face(mia, tp0, 'wince')
neck(mia, tp0, -8, 0, 0, jump=True)
rub(mia, at('push', tp0), tp1, every=0.2)
word_pop('BedPush', 'PUSH', W(BED, (-0.4, 0.4, 7.4)), 0.6, '#FF7AB6', at('push', tp0) - 0.05, at('pressing', tp0))
te0, te1 = S['end']
face(mia, te0, 'smug')
neck(mia, te0, 0, 0, 0, jump=True)
arms(mia, te0, *DOWN, jump=True)
face(mia, at('rub', te0) - 0.1, 'sleep')
neck(mia, at('rub', te0), -8, 0, 0)
rub(mia, at('rub', te0), END_T)

# ---------------------------------------------------------------- VIS light show
t_off = at('nowhere') - 0.03
show(vis['show'], [(0, t_off)])
for k, p in enumerate(vis['spins']):
    A.set(p, 'rotation_euler', 0, (0, 0, 0))
    A.set(p, 'rotation_euler', t_off, (0, math.radians((360 if k % 2 else -360) * t_off / 2.0), 0))
    _linear(p, 'rotation_euler')
for k, ob in enumerate(vis['show']):
    if ob.name.startswith('VisSpk'):
        t = 0.05 * (k % 10)
        while t < t_off:
            A.set(ob, 'scale', t, (0.3,) * 3)
            A.set(ob, 'scale', t + 0.2, (1.8,) * 3)
            t += 0.45
sign_pop('VisNo', 'NO LIGHT', W(VIS, (0, 2.0, 6.4)), 0.8, at('no', S['nolight'][0]) - 0.05, S['nolight'][1], board='#1C1B4A', inkc='#FFFFFF')
word_pop('VisNowhere', 'NOWHERE.', W(VIS, (0, 2.0, 6.6)), 0.8, '#FFFFFF', at('nowhere') + 0.05, S['nolight'][0])

# ---------------------------------------------------------------- EYE cells
tf0, tf1 = S['fire']
t_hit = at('hits', tf0)
beam = tube('EyeBeam', [(-9.0, -10.0, 10.0), (0.0, 5.0, 3.0)], 0.5, VS.glow('BeamM', '#FFF6B0', 3.0))
beam.location = W(EYE, (0, 0, 0))
beam.visible_shadow = False
show([beam], [(at('when', tf0) - 0.05, S['reads'][0])])
A.set(beam, 'scale', 0, (1, 1, 1))
tq0, tq1 = S['squeeze']
t_press = at('squeeze', tq0) + 0.35
fing = finger('EyeFinger', W(EYE, (20.0, 4.6, 3.4)), rot=(0, 0, -8))
A.set(fing, 'location', 0, W(EYE, (22.0, 4.6, 3.4)))
A.set(fing, 'location', tq0, W(EYE, (22.0, 4.6, 3.4)))
A.set(fing, 'location', t_press, W(EYE, (13.5, 4.6, 3.0)))
A.set(fing, 'location', tq1 - 0.2, W(EYE, (13.8, 4.6, 3.0)))
A.set(fing, 'location', tq1 + 0.3, W(EYE, (22.0, 4.6, 3.4)))
tm0, tm1 = S['misfire']
tdm0, tdm1 = S['dumb']
for i, (x, y, root, lit) in enumerate(eye['cells']):
    ranges = [(t_hit + 0.03 * (i % 7), S['dumb'][0]), (t_press + 0.04 * (i % 5), tq1)]
    t = tm0 + random.uniform(0, 0.4)
    while t < tm1:
        d = random.uniform(0.08, 0.22)
        ranges.append((t, t + d))
        t += d + random.uniform(0.15, 0.5)
    show([lit], ranges)
    sq = 0.55 if x > 1.0 else 0.8
    A.set(root, 'scale', 0, (1, 1, 1))
    A.set(root, 'scale', t_press - 0.05, (1, 1, 1))
    A.set(root, 'scale', t_press + 0.1, (1.25, 1.25, sq))
    A.set(root, 'scale', tq1 - 0.1, (1.2, 1.2, sq + 0.05))
    A.set(root, 'scale', tq1 + 0.2, (1, 1, 1))
    A.set(root, 'rotation_euler', 0, (0, 0, 0))
    k, t = 0, tdm0
    while t < tdm1:
        A.set(root, 'rotation_euler', t, (0, math.radians(10 if (k + i) % 2 else -10), 0))
        t += 0.25
        k += 1
    A.set(root, 'rotation_euler', tdm1 + 0.05, (0, 0, 0))
sign_pop('EyeDumb', 'DUMB', W(EYE, (0.5, 1.0, 6.6)), 0.8, at('dumb') - 0.05, tdm1, board='#FFD23F', inkc='#2B2A72')
word_pop('EyeZap', 'ZAP!', W(EYE, (0, 1.5, 6.6)), 0.8, '#FFF07A', t_hit, tf1)
word_pop('EyeSqz', 'SQUISH!', W(EYE, (1.5, 1.5, 6.6)), 0.7, '#FFF07A', t_press, tq1)
word_pop('EyeOops', 'OOPS', W(EYE, (0, 1.5, 6.6)), 0.7, '#FFF07A', at('misfire', tm0), tm1)

# ---------------------------------------------------------------- BRN brain HQ
tr0, tr1 = S['reads']
face(zed, 0, 'neutral')
arms(zed, 0, *DOWN, jump=True)
face(zed, tr0, 'excited')
arms(zed, at('signal', tr0), (-140, 0, 40), (-140, 0, -40))
word_pop('BrnLight', 'LIGHT!', W(BRN, (0, 9.2, 6.8)), 0.9, '#FFE14A', at('signal', tr0), tr1)
tb0, tb1 = S['button']
t_btn = at('pressing', tb0) + 0.3
btn_base = box('BrnBtnBase', (2.4, 2.4, 2.0), W(BRN, (-3.0, 2.0, 1.0)), V.paint('BtnBase', '#2B2A72', kind='metal'), outline=0.04, bevel=0.1)
btn = cylinder('BrnBtn', 0.95, 0.6, W(BRN, (-3.0, 2.0, 2.3)), V.paint('BtnRed', '#FF2E3A', rough=0.3), outline=0.04)
VS.sign('BrnBtnLbl', 'LIGHT', W(BRN, (-3.0, 0.75, 1.2)), 0.4, board='#FFD23F', inkc='#2B2A72', k=0.6)
A.set(btn, 'location', 0, W(BRN, (-3.0, 2.0, 2.3)))
A.set(btn, 'location', t_btn - 0.05, W(BRN, (-3.0, 2.0, 2.3)))
A.set(btn, 'location', t_btn + 0.05, W(BRN, (-3.0, 2.0, 2.05)))
A.set(btn, 'location', tb1, W(BRN, (-3.0, 2.0, 2.05)))
bf = finger('BrnFinger', W(BRN, (-3.0, 2.0, 14.0)), rot=(0, -90, 0))
A.set(bf, 'location', 0, W(BRN, (-3.0, 2.0, 16.0)))
A.set(bf, 'location', tb0, W(BRN, (-3.0, 2.0, 16.0)))
A.set(bf, 'location', t_btn, W(BRN, (-3.0, 2.0, 9.8)))
A.set(bf, 'location', tb1, W(BRN, (-3.0, 2.0, 9.9)))
A.set(bf, 'location', tb1 + 0.4, W(BRN, (-3.0, 2.0, 16.0)))
word_pop('BrnHand', 'BY HAND!', W(BRN, (0.5, 1.0, 7.0)), 0.6, '#FFE14A', at('hand', tb0), tb1)
face(zed, tb0, 'shocked')
tbl0, tbl1 = S['blood']
face(zed, tbl0, 'dizzy')
shake(zed['root'], at('less', tbl0), tbl1, 0.05, seed=3)
sign_pop('BrnBlood', 'LOW BLOOD', W(BRN, (0, 4.5, 7.2)), 0.6, at('less', tbl0) - 0.05, tbl1, board='#E53945')
al = brn['alarm_light']
E.light_key(al, [(0, 0), (at('less', tbl0) - 0.05, 0)] + [(at('less', tbl0) + k * 0.15, 2500 if k % 2 == 0 else 0) for k in range(14)])
ti0, ti1 = S['inhere']
face(zed, ti0, 'proud')
arms(zed, ti0, (-20, 0, 15), (-150, 0, -30), jump=True)
sign_pop('BrnIn', 'IN HERE', W(BRN, (0, 4.5, 7.2)), 0.7, at('in here', ti0) - 0.05, ti1, board='#3FE0C8', inkc='#2B2A72')

# ---------------------------------------------------------------- THT fireworks on the brain screen
tfw0 = at('fireworks')
E.hide_named(['ThtScrTower', 'ThtScrCren'])
t, k = S['fireworks'][0] + 0.1, 0
while t < S['phos'][1] - 0.3:
    c = (random.uniform(-5.5, 5.5), 8.75, random.uniform(3.4, 7.0))
    burst(f'ThtFw{k}', W(THT, c), t, GLOWC[k % 6], n=12, r=random.uniform(1.4, 2.2))
    t += 0.22
    k += 1
word_pop('ThtBoom', 'BOOM!', W(THT, (3.6, 6.0, 7.6)), 0.6, '#FFE14A', S['fireworks'][0] + 0.2, S['phos'][0])
sign_pop('ThtPhos', 'PHOSPHENES', W(THT, (0, 6.0, 7.0)), 0.8, at('phosphenes') - 0.05, S['phos'][1], board='#FFD23F', inkc='#2B2A72', k=4)

# ---------------------------------------------------------------- KIT stand up too fast
ts0, ts1 = S['stand']
t_up = at('up', ts0)
sit(mia2, 0, W(KIT, (0, 2.6, 1.7)), 0)
lean(mia2, 0, 0, 0, jump=True)
neck(mia2, 0, 0, 0, 0, jump=True)
neck(zed, 0, 0, 0, 0, jump=True)
lean(zed, 0, 0, 0, jump=True)
face(mia2, 0, 'happy')
arms(mia2, 0, *DOWN, jump=True)
stand(mia2, t_up - 0.05, W(KIT, (0, 3.3, 0)), 0)
face(mia2, t_up, 'shocked')
arms(mia2, t_up, (-60, 0, 70), (-60, 0, -70))
tst0, tst1 = S['stars']
face(mia2, at('blood', ts0), 'dizzy')
lean(mia2, at('blood', ts0), 0, 8)
lean(mia2, tst0, 0, -10)
lean(mia2, tst1, 0, 6)
for k in range(5):
    VS_star = E.sparkles(f'KitStar{k}', W(KIT, (0, 3.0, 7.0)), at('misfire') - 0.2, tst1, n=1, r=0.0, hexc='#FFE14A', size=0.18)
    st = VS_star[0]
    for j in range(12):
        tt = at('blood', ts0) + j * 0.25
        a = 2 * math.pi * (j / 6.0 + k / 5.0)
        A.set(st, 'location', tt, W(KIT, (1.3 * math.cos(a), 3.0 + 1.3 * math.sin(a), 7.0)))
word_pop('KitStars', 'STARS!', W(KIT, (0, 2.0, 7.7)), 0.7, '#FFE14A', at('stars'), tst1)

# ---------------------------------------------------------------- TWR colour world
tc0, tc1 = S['colour']
sign_pop('TwrCol', 'EVERY COLOUR', W(TWR, (0, 6.0, 7.8)), 0.55, at('every', tc0) - 0.05, tc1, board='#FF7AB6')
to0, to1 = S['outthere']
sign_pop('TwrNot', 'NOT OUT THERE', W(TWR, (1.5, 7.0, 7.8)), 0.5, at('never', to0) - 0.05, to1, board='#2B2A72', inkc='#FFE07A')
for k in range(4):
    burst(f'TwrFw{k}', W(TWR, (-6 + k * 4.0, 18.0, 12 + (k % 2) * 2)), tc0 + 0.2 + k * 0.35, GLOWC[k], n=14, r=2.6, life=0.8)

# ---------------------------------------------------------------- cameras
HEAD = (1.0, 1.0, 5.6)
cs('rub', BED, (2.6, -5.0, 4.8), HEAD, 28, push=0.2, roll=-4, roll_to=3, min_d=3.0)
cs('show', VIS, (0.0, -10.0, 5.5), (0.0, 5.0, 6.0), 20, push=0.3, roll=4)
cs('swirls', VIS, (-1.0, -4.5, 6.0), (-5.0, 3.0, 6.5), 28, punch=[(at('swirls'), 40)], roll=8, min_d=4.0)
cs('checker', VIS, (4.0, -6.0, 4.0), (0.0, 8.7, 6.0), 24, orbit=-8, min_d=5.0)
cs('shut', BED, (1.3, -2.4, 5.4), HEAD, 34, punch=[(at('shut', S['shut'][0]), 48)], min_d=2.5)
cs('where', BED, (-3.0, -7.0, 6.0), (0.5, 2.0, 4.6), 22, orbit=8, min_d=4.0)
cs('nowhere', VIS, (0.0, -8.0, 6.0), (0.0, 2.0, 6.5), 26, push=0.2, min_d=4.0)
cs('nolight', VIS, (0.0, -5.0, 6.2), (0.0, 2.0, 6.5), 30, push=0.15, roll=-4, min_d=3.0)
cs('back', EYE, (0.0, -10.5, 7.0), (0.0, 5.0, 3.5), 20, push=0.35, min_d=5.0)
cs('cells', EYE, (-3.0, -1.2, 3.6), (0.0, 5.0, 3.0), 26, orbit=10, min_d=3.0)
cs('fire', EYE, (5.0, -5.0, 6.0), (0.0, 5.0, 3.0), 24, shakes=[(t_hit, 0.06)], min_d=4.0)
cs('reads', BRN, (5.0, -4.0, 5.0), (1.5, 6.0, 5.5), 24, push=0.2, min_d=4.0)
cs('dumb', EYE, (1.0, -0.4, 3.4), (0.5, 5.0, 3.2), 30, punch=[(at('dumb'), 42)], min_d=2.5)
cs('squeeze', EYE, (-4.0, -6.0, 5.0), (3.0, 5.0, 3.5), 24, shakes=[(t_press, 0.1)], min_d=4.0)
cs('push', BED, (0.6, -2.8, 5.0), HEAD, 30, punch=[(at('push', S['push'][0]), 44)], shakes=[(at('eyeball'), 0.06)], min_d=2.5)
cs('button', BRN, (-0.5, -5.0, 5.5), (-3.0, 2.0, 3.5), 26, punch=[(t_btn, 38)], shakes=[(t_btn, 0.1)], min_d=4.0)
cs('fireworks', THT, (0.0, -3.0, 4.2), (0.0, 8.9, 5.4), 24, push=0.2, min_d=6.0)
cs('phos', THT, (-4.0, -4.0, 3.5), (0.0, 8.9, 5.8), 26, punch=[(at('phosphenes'), 34)], min_d=6.0)
cs('stand', KIT, (3.0, -6.0, 4.5), (0.0, 2.8, 4.8), 24, shakes=[(t_up, 0.08)], min_d=4.0)
cs('blood', BRN, (0.0, -7.0, 6.0), (0.0, 5.0, 5.5), 22, shakes=[(at('less', S['blood'][0]), 0.08)], min_d=5.0)
cs('misfire', EYE, (2.0, -4.0, 4.0), (0.0, 5.0, 3.0), 24, orbit=-10, min_d=4.0)
cs('stars', KIT, (1.2, -4.0, 6.2), (0.0, 3.3, 6.0), 26, punch=[(at('stars'), 42)], min_d=2.5, roll=6)
cs('colour', TWR, (0.0, -8.0, 4.0), (0.0, 10.0, 6.5), 18, orbit=10, min_d=6.0)
cs('outthere', TWR, (-3.0, -5.0, 3.0), (2.0, 12.0, 7.0), 22, push=0.2, min_d=6.0)
cs('inhere', BRN, (0.0, -9.0, 5.0), (0.0, 5.0, 5.0), 20, push=0.3, roll=-4, min_d=5.0)
cs('end', BED, (2.6, -5.0, 4.8), HEAD, 28, push=0.2, roll=-4, roll_to=3, min_d=3.0)
E.flashes([t_hit, t_btn, at('stars')])

BOUNDS = {
    'bed': (-10.6, 10.6, -10.6, 8.6, 0.4, 9.1), 'vis': (-11.6, 11.6, -11.6, 8.6, 0.4, 12.6), 'eye': (-11.6, 11.6, -11.6, 8.6, 0.4, 11.6),
    'brn': (-12.6, 12.6, -11.6, 9.6, 0.4, 10.6), 'tht': (-10.6, 10.6, -9.6, 8.8, 0.4, 9.6), 'kit': (-11.6, 11.6, -10.6, 8.6, 0.4, 9.1),
}
K.run(args, SETS, BOUNDS)
