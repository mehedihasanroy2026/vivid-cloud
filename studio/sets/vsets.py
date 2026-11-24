"""Reusable VIVID sets (Ricks-style colour pairs, patterns, props). Each builder places a set around `origin`
(our convention: camera at -Y looking +Y, characters face -Y, floor z = 0, characters ~6 units tall, seat surface z ~1.6)
and returns a dict of useful local points / objects. Pair each set with a sky in E.HOOKS (see SKY in each docstring).

    import vsets as VS
    d = VS.diner('Din', (300, 0, 0))
"""
import math
import bpy
import real
import vivid as V
import assets
from toon import ellipsoid, cone, tube, box, cylinder, empty, text_obj, SetBuilder
from acting import deg, A

INKM = None


def ink():
    global INKM
    INKM = INKM or real.mat('VInk', '#24203A', 'paint', grime=0)
    return INKM


def glow(name, hexc, k=4.0):
    return real.mat(name, hexc, 'glow', emit=k)


def sign(name, txt, loc, size, board='#2B2E6E', inkc='#FFE07A', k=2.5, w=None, rot=0):
    w = w or (len(txt) * size * 0.78 + size)
    root = empty(name, loc)
    box(name + 'Board', (w, 0.18, size * 1.7), (0, 0, 0), V.paint(name + 'B', board, grime=0.03), root, outline=0.04)
    t = text_obj(name + 'Txt', txt, size, (0, -0.11, -size * 0.36), glow(name + 'T', inkc, k), extrude=0.02, parent=root)
    t.data.align_x = 'CENTER'
    root.rotation_euler = deg(0, 0, rot)
    return root


def room(nm, xw, yb, yf, h, wall, floor, ceil='#F6EEDF', wallx=None, trim='#FFFFFF', front=True, beams=None):
    """closed room: x in [-xw, xw], y from yf (front, behind camera) to yb (back wall)"""
    d = yb - yf
    yc = (yb + yf) / 2
    box(nm + 'Floor', (2 * xw, d, 0.2), (0, yc, -0.1), floor)
    box(nm + 'Back', (2 * xw, 0.4, h), (0, yb + 0.2, h / 2), wall)
    if front:
        box(nm + 'Front', (2 * xw, 0.4, h), (0, yf - 0.2, h / 2), wall)
    for s in (-1, 1):
        box(nm + 'Side', (0.4, d, h), (s * (xw + 0.2), yc, h / 2), wallx or wall)
        box(nm + 'BaseS', (0.15, d, 0.5), (s * (xw - 0.05), yc, 0.25), V.paint(nm + 'Trim', trim, grime=0.05))
    box(nm + 'Base', (2 * xw, 0.15, 0.5), (0, yb - 0.05, 0.25), V.paint(nm + 'Trim', trim, grime=0.05))
    box(nm + 'Crown', (2 * xw, 0.25, 0.3), (0, yb - 0.1, h - 0.15), V.paint(nm + 'Trim', trim, grime=0.05))
    if ceil:
        box(nm + 'Ceil', (2 * xw, d, 0.3), (0, yc, h + 0.15), V.paint(nm + 'CeilM', ceil, grime=0.04))
    if beams:
        for x in range(-int(xw) + 2, int(xw) - 1, 4):
            box(nm + 'Beam', (0.5, d, 0.6), (x, yc, h - 0.3), V.paint(nm + 'BeamM', beams, kind='wood', grime=0.1), outline=0.03)


def window(nm, loc, w, h, sky_top='#5EA0F0', sky_bot='#FFE3B0', frame='#FFFFFF', rot=0):
    """a glowing window on a wall (painted outside), with frame + cross bars; loc = centre on the wall face"""
    root = empty(nm, loc)
    pane = box(nm + 'Pane', (w, 0.05, h), (0, 0.02, 0), V.pat(nm + 'Sky' + sky_top, sky_bot, sky_top, 'stripes', scale=0.01, mode='wall', grime=0), root)
    m = real.mat(nm + 'Glow' + sky_top, sky_top, 'glow', emit=2.2)
    pane.data.materials[0] = m
    fm = V.paint(nm + 'Frame' + frame, frame, grime=0.05)
    for z in (-h / 2, h / 2):
        box(nm + 'FrH', (w + 0.3, 0.25, 0.18), (0, -0.05, z), fm, root, outline=0.02)
    for x in (-w / 2, w / 2):
        box(nm + 'FrV', (0.18, 0.25, h + 0.3), (x, -0.05, 0), fm, root, outline=0.02)
    box(nm + 'BarV', (0.1, 0.2, h), (0, -0.04, 0), fm, root)
    box(nm + 'BarH', (w, 0.2, 0.1), (0, -0.04, 0), fm, root)
    root.rotation_euler = deg(0, 0, rot)
    return root


def lamp(nm, loc, shade='#FF5A6E', power=700, col='#FFD7A0', cord=2.0):
    x, y, z = loc
    tube(nm + 'Cord', [(x, y, z + cord), (x, y, z)], 0.03, ink())
    cone(nm + 'Shade', 0.8, 0.18, 0.7, (x, y, z - 0.2), V.paint(nm + 'ShadeM' + shade, shade, grime=0.05), outline=0.03)
    ellipsoid(nm + 'Bulb', (0.22, 0.22, 0.22), (x, y, z - 0.55), glow('LampBulbG', '#FFE2A0', 10), segs=12, rings=8)
    return real.point((x, y, z - 1.0), power, col, radius=0.5, name=nm + 'L', volume=0.0)


def puff_palm(nm, loc, h=9.0, seed=0):
    r = empty(nm, loc)
    tube(nm + 'Trunk', [(0, 0, 0), (0.5, 0, h * 0.5), (1.1, 0, h)], 0.28, real.mat('PalmTrunk', '#B9864E', 'wood', grime=0.1), r, outline=0.04)
    lm = V._leaf('#3FAF4A')
    for i in range(6):
        a = i * math.pi / 3 + seed
        l = ellipsoid(f'{nm}Frond{i}', (2.4, 0.55, 0.12), (1.1 + 1.9 * math.cos(a), 1.9 * math.sin(a), h - 0.5), lm, r, outline=0.03, segs=16, rings=8)
        l.rotation_euler = (0, math.radians(22), a)
    return r


def booth_table(nm, loc, top='#FFF4DC', seat='#E53945'):
    x, y, z = loc
    box(nm + 'Top', (4.2, 2.6, 0.18), (x, y, 2.9), V.paint(nm + 'TopM', top, grime=0.03, rough=0.3), outline=0.03, bevel=0.05)
    box(nm + 'Edge', (4.3, 2.7, 0.1), (x, y, 2.78), V.paint('Chrome', '#D8E2EE', kind='metal', grime=0.02, rough=0.2))
    cylinder(nm + 'Leg', 0.15, 2.8, (x, y, 1.4), V.paint('Chrome', '#D8E2EE', kind='metal'))
    sm = V.pat(nm + 'Vinyl', seat, seat, 'stripes', scale=3, mode='box', rough=0.35)
    for s in (1, -1):
        box(nm + 'Seat', (4.2, 1.6, 0.6), (x, y + s * 2.4, 1.3), sm, outline=0.03, bevel=0.15)
        box(nm + 'SeatBack', (4.2, 0.6, 2.8), (x, y + s * 3.1, 2.6), sm, outline=0.03, bevel=0.2)


# ================================================================== EP12 sets
def diner(nm, origin):
    """retro diner: mint walls, red booths, red/cream checker floor, neon. SKY indoor"""
    with SetBuilder(nm, origin) as root:
        room(nm, 12, 9, -12, 9, V.pat(nm + 'Wall', '#7FD8C8', '#6CCAB9', 'stripes', scale=1.4, mode='wall'),
             V.pat(nm + 'Floor', '#E53945', '#FFF4DC', 'checker', scale=0.5, mode='floor', rough=0.3),
             wallx=V.pat(nm + 'WallX', '#7FD8C8', '#6CCAB9', 'stripes', scale=1.4, mode='wallx'), trim='#E53945')
        box(nm + 'Stripe', (24, 0.1, 0.5), (0, 8.9, 3.6), V.paint('Chrome', '#D8E2EE', kind='metal', rough=0.2))
        booth_table(nm + 'Booth', (0, 1.0, 0))
        for x in (-6, 6):
            window(nm + 'Win', (x, 8.85, 5.4), 4.2, 3.0, '#4F95EE', '#FFD9A0')
        s = sign(nm + 'Neon', 'DINER', (0, 8.75, 7.0), 0.9, board='#2B2A72', inkc='#FF5FA2', k=6)
        for x in (-9.5, 9.5):    # counter + stools at the sides
            box(nm + 'Counter', (3.0, 6.0, 2.8), (x, 2, 1.4), V.paint(nm + 'CounterM', '#E53945', grime=0.05), outline=0.03, bevel=0.08)
            box(nm + 'CounterTop', (3.2, 6.2, 0.2), (x, 2, 2.9), V.paint(nm + 'TopM', '#FFF4DC', rough=0.3), outline=0.03)
        box(nm + 'Juke', (2.0, 1.4, 3.6), (-10.2, 7.6, 1.8), V.paint('JukeM', '#FFB830', grime=0.05), outline=0.04, bevel=0.3)
        box(nm + 'JukeGlow', (1.4, 0.1, 1.6), (-10.2, 6.85, 2.4), glow('JukeG', '#FF5FA2', 3.0))
        for x in (-4, 4):
            lamp(nm + 'Lamp', (x, 1.0, 7.4), shade='#E53945', power=500)
        for x, y in ((11, 8), (-11, -10), (11, -10)):
            assets.load('furniture-kit', 'pottedPlant', loc=(x, y, 0), scale=2.4 * 2.1, center=True)
        real.area((0, -8, 8.6), (30, 0, 0), 14, 600, '#FFE6C8', shadow=False, name=nm + 'Fill', volume=0.0)
        real.area((0, 6, 8.6), (0, 0, 0), 8, 400, '#FFD7A8', shadow=True, name=nm + 'Key', volume=0.0)
    return {'root': root, 'leo_seat': (0, 3.4, 1.6), 'mia_seat': (0, -1.4, 1.6), 'table': (0, 1.0, 3.0)}


def swamp(nm, origin):
    """prehistoric swamp at sunset: purple water, giant ferns, volcano. SKY sunset"""
    with SetBuilder(nm, origin) as root:
        box(nm + 'Water', (200, 200, 0.2), (0, 60, -0.35), V.pat(nm + 'WaterM', '#4B3C9E', '#E0688A', 'wavy', scale=0.08, mode='floor', rough=0.05, bump=0.05))
        bank = V.pat(nm + 'Mud', '#6C8E3A', '#8FAE45', 'grass', scale=0.4, mode='floor', c3='#A88A4A', bump=0.3)
        for x, y, rx, ry in ((-6, -4, 9, 6), (10, 8, 6, 5), (-14, 14, 7, 6), (2, -12, 14, 5)):
            ellipsoid(nm + 'Bank', (rx, ry, 1.2), (x, y, -0.6), bank, segs=24, rings=12)
        for i, (x, y) in enumerate(((-3, 3), (2, 6), (5, 1), (-1, 9), (7, 5))):
            ellipsoid(nm + 'Pad', (0.9, 0.9, 0.05), (x, y, -0.2), V.paint('LilyPad', '#4FBF5A', grime=0.05), outline=0.02, segs=16, rings=4)
        fern = V._leaf('#3E9E46')
        for i, (x, y, h) in enumerate(((-11, 6, 7), (12, 12, 8), (-15, 18, 9), (16, 2, 6), (-17, -3, 5))):
            r = empty(f'{nm}Fern{i}', (x, y, 0))
            for k in range(7):
                a = k * 0.9 + i
                f = ellipsoid(f'{nm}Fr{i}{k}', (h * 0.38, 0.5, 0.1), (math.cos(a) * h * 0.3, math.sin(a) * h * 0.3, h * 0.4), fern, r, outline=0.03, segs=16, rings=6)
                f.rotation_euler = (0, math.radians(-35), a)
        for i, (x, y, h) in enumerate(((-24, 30, 12), (22, 34, 13), (-36, 50, 15))):
            V.puff_tree(f'{nm}Tree{i}', (x, y, 0), h=h, col='#2F8F5A', trunk='#6B4A3A', seed=i + 4)
        cone(nm + 'Volcano', 40, 6, 34, (25, 150, 15), V.paint('VolcanoM', '#6A4A8A', grime=0.15), outline=0.08)
        ellipsoid(nm + 'Lava', (6, 6, 1.5), (25, 150, 32.5), glow('LavaG', '#FF7A30', 6), segs=16, rings=8)
        real.sun(V.sun_rot(8, 15), strength=4.0, hexc='#FFB060', angle=2.0, name=nm + 'Sun')
        real.sun(V.sun_rot(35, 200), strength=2.6, hexc='#FFD8C8', angle=4.0, name=nm + 'Front')
        real.shafts((0, 30, 6), (90, 80, 14), density=0.006, hexc='#FFB8A0', name=nm + 'Haze')
    return {'root': root, 'pond': (0, 4, -0.25), 'shore': (-6, -4, 0.55)}


def underwater(nm, origin):
    """deep-time ocean: teal water, light rays, seaweed, sand. SKY indoor (blue ambient); hook sets the world."""
    with SetBuilder(nm, origin) as root:
        box(nm + 'Sand', (120, 120, 0.2), (0, 30, -0.1), V.pat(nm + 'SandM', '#F2D49A', '#E6BE7A', 'gravel', scale=0.8, mode='floor', c3='#F7E2B8', bump=0.2))
        box(nm + 'Surface', (120, 120, 0.1), (0, 30, 22), glow(nm + 'SurfG', '#9FE8FF', 1.6)).visible_shadow = False
        for i in range(14):
            x, y = -16 + (i * 7.3) % 32, 2 + (i * 5.7) % 26
            h = 4 + (i % 4) * 2
            tube(f'{nm}Weed{i}', [(x, y, 0), (x + 0.6, y, h * 0.4), (x - 0.5, y, h * 0.75), (x + 0.3, y, h)], 0.18,
                 V.paint('Weed' + str(i % 3), ('#2FBF6A', '#7FD84A', '#1FA58C')[i % 3], grime=0.05), outline=0.03)
        for i, (x, y, r) in enumerate(((-9, 10, 2.2), (8, 14, 3.0), (14, 4, 1.8), (-14, 20, 3.4))):
            ellipsoid(f'{nm}Rock{i}', (r, r * 0.8, r * 0.6), (x, y, 0.3), V.paint('SeaRock', '#7A6AC8', grime=0.2), outline=0.04, segs=16, rings=8)
        for i, (x, y) in enumerate(((-6, 8), (5, 9), (11, 16))):
            for k in range(5):
                c = ('#FF6F91', '#FFB830', '#C77BFF')[i]
                ellipsoid(f'{nm}Coral{i}{k}', (0.5, 0.5, 1.2), (x + 0.5 * math.cos(k * 1.3), y + 0.5 * math.sin(k * 1.3), 1.0), V.paint('Coral' + c, c, grime=0.05), outline=0.03, segs=12, rings=8)
        real.sun(V.sun_rot(70, 180), strength=3.0, hexc='#CFF6FF', angle=3.0, name=nm + 'Sun')
        real.shafts((0, 14, 10), (60, 50, 22), density=0.007, hexc='#7FD8F0', anisotropy=0.75, name=nm + 'Water')
    return {'root': root}


def chest(nm, origin):
    """inside the chest: pink flesh walls, rib arches, two lung balloons, diaphragm dome trampoline. SKY indoor"""
    with SetBuilder(nm, origin) as root:
        flesh = real.mat(nm + 'Flesh', '#F27A8A', 'flesh', grime=0.15)
        room(nm, 14, 10, -12, 16, flesh, real.mat(nm + 'FleshF', '#D9506A', 'flesh', grime=0.2), ceil='#E86A82')
        bone = V.paint('Bone', '#FFF2DC', grime=0.1)
        for y in (-4, 0, 4, 8):
            pts = [(14 * math.cos(a), y, 2 + 13 * math.sin(a)) for a in [math.pi * k / 14 for k in range(15)]]
            tube(f'{nm}Rib{y}', pts, 0.55, bone, None, outline=0.05)
        lungs = []
        for s in (-1, 1):
            l = ellipsoid(f'{nm}Lung{s}', (3.6, 3.0, 5.0), (s * 5.0, 4, 9.0), V.pat('LungM', '#FF9EB5', '#F27A9A', 'dots', scale=1.2, mode='box', grime=0.05), outline=0.06)
            lungs.append(l)
        tube(nm + 'Windpipe', [(-5, 4, 13), (-2, 4, 14.5), (0, 4, 16)], 0.8, V.paint('Pipe', '#FFB8C8'), None, outline=0.05)
        tube(nm + 'Windpipe2', [(5, 4, 13), (2, 4, 14.5), (0, 4, 16)], 0.8, V.paint('Pipe', '#FFB8C8'), None, outline=0.05)
        dia = ellipsoid(nm + 'Diaphragm', (11, 8, 2.2), (0, 3, 1.4), V.pat('DiaM', '#C2185B', '#E04A86', 'stripes', scale=1.5, mode='box', grime=0.05), outline=0.07)
        stom = ellipsoid(nm + 'Stomach', (3.0, 2.4, 2.0), (3.5, -1, 0.8), V.paint('StomM', '#FFB25C', grime=0.1), outline=0.05)
        sign(nm + 'DiaSign', 'DIAPHRAGM', (-6, 9.7, 5), 0.6, board='#FFF2DC', inkc='#C2185B', k=0.5)
        real.point((0, -4, 10), 3000, '#FFD8E0', radius=2.0, name=nm + 'Glow', volume=0.0)
        real.area((0, -8, 14), (35, 0, 0), 16, 900, '#FFE6EE', shadow=False, name=nm + 'Fill', volume=0.0)
        real.shafts((0, 0, 8), (26, 20, 15), density=0.01, hexc='#FFC0D0', name=nm + 'Haze')
    return {'root': root, 'lungs': lungs, 'dia': dia, 'stomach': stom}


def brain_room(nm, origin, lever_txt='TADPOLE MODE', wall=('#6E4FD0', '#5E41BC'), floor=('#22B5A6', '#F4EEDC')):
    """brain control room: wallpaper, checker floor, consoles, monitor wall, a dusty old lever with a sign, alarm lamp. SKY indoor"""
    with SetBuilder(nm, origin) as root:
        room(nm, 13, 10, -12, 11, V.pat(nm + 'Wall', wall[0], wall[1], 'wallpaper', scale=0.5, mode='wall', c3='#F7C64A'),
             V.pat(nm + 'Floor', floor[0], floor[1], 'checker', scale=0.45, mode='floor', rough=0.35),
             wallx=V.pat(nm + 'WallX', wall[0], wall[1], 'wallpaper', scale=0.5, mode='wallx', c3='#F7C64A'), trim='#2B2A72', beams='#C8743A')
        sign(nm + 'Title', 'BRAIN HQ', (0, 9.75, 8.6), 0.75, board='#FF5A6E', inkc='#FFF4D0')
        for i, (x, c) in enumerate(((-9, '#FF7AB6'), (-5.5, '#3FE0C8'), (5.5, '#FFD23F'), (9, '#8FB8FF'))):
            box(f'{nm}Mon{i}', (3.0, 0.3, 2.0), (x, 9.8, 5.0), V.paint('MonFrame', '#1C1B4A'), outline=0.03)
            box(f'{nm}MonS{i}', (2.6, 0.1, 1.6), (x, 9.6, 5.0), glow(f'MonG{c}', c, 2.5))
        for x in (-7, 7):
            box(nm + 'Console', (5.0, 2.0, 2.6), (x, 6.5, 1.3), V.paint(nm + 'ConsM', '#1FA58C', kind='metal', rough=0.4), outline=0.04, bevel=0.1)
            for k in range(5):
                c = ('#FF2E3A', '#FFD23F', '#3FE0C8', '#FF7AB6', '#8FB8FF')[k]
                cylinder(f'{nm}Btn', 0.2, 0.15, (x - 1.8 + k * 0.9, 6.0, 2.65), glow('Btn' + c, c, 2.0))
        # the old lever: base, stick on a pivot (rotate X), dusty sign
        box(nm + 'LeverBase', (2.4, 2.0, 2.2), (0, 6.6, 1.1), V.paint(nm + 'LevBase', '#8A6A4A', kind='metal', grime=0.4), outline=0.04, bevel=0.1)
        piv = empty(nm + 'LeverPivot', (0, 6.6, 2.3))
        tube(nm + 'LeverStick', [(0, 0, 0), (0, 0, 2.2)], 0.12, V.paint('LeverStickM', '#C9C9D6', kind='metal'), piv, outline=0.03)
        ellipsoid(nm + 'LeverKnob', (0.35, 0.35, 0.35), (0, 0, 2.3), V.paint('KnobRed', '#FF2E3A', rough=0.3), piv, outline=0.03, segs=16, rings=8)
        piv.rotation_euler = deg(-35, 0, 0)
        lev_sign = sign(nm + 'LeverSign', lever_txt, (0, 5.5, 3.7), 0.32, board='#FFD23F', inkc='#2B2A72', k=0.3)
        alarm = ellipsoid(nm + 'Alarm', (0.5, 0.5, 0.5), (0, 9.6, 7.0), glow(nm + 'AlarmM', '#FF3B3B', 0.6), segs=16, rings=8)
        for x, y in ((-12, 8), (12, 8)):
            assets.load('furniture-kit', 'pottedPlant', loc=(x, y, 0), scale=2.4 * 2.1, center=True)
        for x in (-5, 5):
            lamp(nm + 'Lamp', (x, 1, 9.4), shade='#FF5A6E', power=700)
        real.area((0, -6, 10.5), (30, 0, 0), 16, 800, '#FFE6C8', shadow=False, name=nm + 'Fill', volume=0.0)
    light = real.point((origin[0], origin[1] + 8.0, 7.5), 0, '#FF3030', radius=1.0, name=nm + 'AlarmL', volume=0.2)
    return {'root': root, 'lever': piv, 'alarm': alarm, 'alarm_light': light, 'worker': (2.6, 5.0, 0)}


def throat(nm, origin):
    """throat tunnel with the two vocal-cord doors (rotate pivots Z to slam shut). SKY indoor"""
    with SetBuilder(nm, origin) as root:
        cylinder(nm + 'Tunnel', 6.8, 34, (0, 5, 6), real.mat(nm + 'In', '#F58AA0', 'flesh', grime=0.2), rot=(90, 0, 0))
        for i in range(8):     # soft ridges along the tunnel
            pts = [(6.6 * math.cos(a), -8 + i * 4, 6 + 6.6 * math.sin(a)) for a in [2 * math.pi * k / 24 for k in range(25)]]
            tube(f'{nm}Ridge{i}', pts, 0.25, real.mat(nm + 'Ridge', '#D9506A', 'flesh', grime=0.1))
        box(nm + 'Floor', (14, 32, 0.2), (0, 5, 0.6), real.mat(nm + 'Fl', '#D9506A', 'flesh', grime=0.2))
        doors = []
        cm = V.pat('CordM', '#FFF2E8', '#F7D8D0', 'stripes', scale=2.5, mode='box', grime=0.05)
        for s in (-1, 1):
            piv = empty(f'{nm}Cord{s}', (s * 5.6, 6, 6))
            ellipsoid(f'{nm}CordOb{s}', (2.9, 0.6, 5.0), (-s * 2.8, 0, 0), cm, piv, outline=0.06, segs=24, rings=12)
            piv.rotation_euler = deg(0, 0, s * -55)      # open
            doors.append(piv)
        sign(nm + 'Sign', 'VOCAL CORDS', (0, 13, 10.5), 0.6, board='#FFF2E8', inkc='#C2185B', k=0.5)
        real.point((0, -2, 9), 2500, '#FFD0DA', radius=1.5, name=nm + 'Glow', volume=0.0)
        real.point((0, 14, 6), 1500, '#FFB0C0', radius=2.0, name=nm + 'Back', volume=0.0)
        real.shafts((0, 5, 6), (12, 30, 12), density=0.01, hexc='#FFC0D0', name=nm + 'Haze')
    return {'root': root, 'doors': doors}


def rooftop(nm, origin):
    """city rooftop at golden hour: tiles, railing, water tower, string lights, skyline. SKY golden"""
    with SetBuilder(nm, origin) as root:
        box(nm + 'Roof', (26, 22, 0.4), (0, 2, -0.2), V.pat(nm + 'Tiles', '#E8915A', '#D87A48', 'checker', scale=0.6, mode='floor', rough=0.6))
        rm = V.paint('Rail', '#2B2A72', kind='metal')
        for s in (-1, 1):
            box(nm + 'RailS', (0.15, 22, 0.15), (s * 13, 2, 2.4), rm)
        box(nm + 'RailB', (26, 0.15, 0.15), (0, 13, 2.4), rm)
        for x in range(-13, 14, 2):
            box(nm + 'Post', (0.12, 0.12, 2.4), (x, 13, 1.2), rm)
        r = empty(nm + 'Tower', (9, 9, 0))
        for x, y in ((-1.2, -1.2), (1.2, -1.2), (-1.2, 1.2), (1.2, 1.2)):
            box(nm + 'TLeg', (0.3, 0.3, 5), (x, y, 2.5), V.paint('TowerLeg', '#6B4A3A', kind='wood'), r)
        cylinder(nm + 'Tank', 2.2, 4, (0, 0, 7), V.pat('TankM', '#C8743A', '#A85E2E', 'planks', scale=2.0, mode='box'), r, outline=0.05)
        cone(nm + 'TankTop', 2.5, 0.2, 1.6, (0, 0, 9.8), V.paint('TankTopM', '#2B2A72'), r, outline=0.04)
        cols = ('#FF5A6E', '#FFD23F', '#3FE0C8', '#C77BFF')
        for i in range(16):
            x = -11 + i * 1.47
            ellipsoid(nm + 'StrL', (0.15, 0.15, 0.2), (x, 9, 6.2 - 0.6 * math.sin(math.pi * i / 15)), glow('StrG' + cols[i % 4], cols[i % 4], 8), segs=10, rings=6)
        for x, y in ((-10, 10), (-11, -4), (11, 0)):
            assets.load('furniture-kit', 'pottedPlant', loc=(x, y, 0), scale=2.4 * 2.1, center=True)
        box(nm + 'Mat', (4, 3, 0.05), (0, 1.5, 0.02), V.pat('YogaMat', '#3FE0C8', '#2FC0A8', 'stripes', scale=3, mode='floor'))
        for i, (x, y, n, c) in enumerate(((-70, 150, 'building-skyscraper-a', '#C9B8F0'), (-25, 190, 'building-skyscraper-b', '#F8C8D8'),
                                          (30, 170, 'building-skyscraper-c', '#A8D0F8'), (80, 200, 'building-skyscraper-d', '#FFD8A8'),
                                          (-120, 210, 'building-skyscraper-e', '#B8E0F0'))):
            V.load('city-kit-commercial', n, (x, y, -85), size=45, tint=c, amt=0.75)
        real.sun(V.sun_rot(12, 20), strength=5.0, hexc='#FFC27A', angle=2.0, name=nm + 'Sun')
        real.sun(V.sun_rot(40, 200), strength=1.5, hexc='#FFE6C8', angle=3.0, name=nm + 'Front')
        real.shafts((0, 40, 6), (120, 100, 30), density=0.004, hexc='#FFD8A8', name=nm + 'Haze')
    return {'root': root, 'mat': (0, 1.5, 0)}


# ================================================================== EP13 sets
FURN = 7.35          # Kenney furniture-kit units -> our units


def furn(name, loc, rot=0, tint=None, amt=0.8, size=FURN):
    return V.load('furniture-kit', name, loc, size=size, rot=(0, 0, rot), tint=tint, amt=amt)


def umbrella(nm, loc, c1='#FF5A6E', c2='#FFFFFF'):
    x, y, z = loc
    tube(nm + 'Pole', [(x, y, 0), (x, y, 6.5)], 0.08, V.paint('Pole', '#F4EEDC'))
    cone(nm + 'Top', 3.2, 0.1, 1.4, (x, y, 6.6), V.pat(nm + 'TopM' + c1, c1, c2, 'stripes', scale=2.2, mode='box'), outline=0.04, verts=16)


def beach(nm, origin):
    """sunny beach: sand, turquoise sea, striped umbrellas, palms, sandcastle. SKY day"""
    with SetBuilder(nm, origin) as root:
        box(nm + 'Sand', (200, 60, 0.2), (0, -10, -0.1), V.pat(nm + 'SandM', '#F7D79A', '#F2C77E', 'grass', scale=0.3, mode='floor', c3='#FFE6B8', bump=0.15))
        box(nm + 'Sea', (300, 200, 0.2), (0, 120, -0.3), V.pat(nm + 'SeaM', '#1FB5C8', '#3FD8E0', 'wavy', scale=0.06, mode='floor', rough=0.08, bump=0.1))
        for i in range(3):
            ellipsoid(f'{nm}Foam{i}', (60, 0.6, 0.12), (0, 19.8 + i * 3, -0.15), V.paint('Foam', '#FFFFFF', grime=0), segs=24, rings=6)
        umbrella(nm + 'U1', (-9, 6, 0), '#FF5A6E')
        umbrella(nm + 'U2', (11, 9, 0), '#2F6FD8', '#FFD23F')
        umbrella(nm + 'U3', (-22, 12, 0), '#FFB830')
        for x, y, c in ((-8, 4.5, '#3FE0C8'), (12, 7, '#FF7AB6')):
            box(nm + 'Towel', (2.6, 4.6, 0.05), (x, y, 0.03), V.pat(nm + 'Towel' + c, c, '#FFFFFF', 'stripes', scale=2.0, mode='floor'))
        castle = empty(nm + 'Castle', (3.2, 2.0, 0))
        sm = V.paint('SandCastle', '#E8B86A', grime=0.15)
        cylinder(nm + 'CBase', 1.3, 1.0, (0, 0, 0.5), sm, castle, outline=0.03)
        for a in range(4):
            cylinder(nm + 'CTow', 0.38, 1.6, (1.1 * math.cos(a * 1.57), 1.1 * math.sin(a * 1.57), 0.8), sm, castle, outline=0.03)
            cone(nm + 'CTop', 0.45, 0.0, 0.6, (1.1 * math.cos(a * 1.57), 1.1 * math.sin(a * 1.57), 1.9), sm, castle, outline=0.02, verts=12)
        tube(nm + 'Flag', [(0, 0, 1.0), (0, 0, 2.8)], 0.03, ink(), castle)
        box(nm + 'FlagC', (0.6, 0.04, 0.4), (0.3, 0, 2.6), V.paint('FlagRed', '#FF5A6E'), castle)
        ball = ellipsoid(nm + 'Ball', (0.6, 0.6, 0.6), (-4, -1, 0.6), V.pat('BallM', '#FF5A6E', '#FFFFFF', 'stripes', scale=1.6, mode='box'), outline=0.03, segs=24, rings=12)
        for i, (x, y) in enumerate(((-16, 2), (17, 3), (-28, 8), (26, 10), (-6, 14))):
            puff_palm(f'{nm}Palm{i}', (x, y, 0), h=10 + (i % 3) * 1.5, seed=i)
        t = empty(nm + 'Guard', (20, 14, 0))
        for x, y in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            tube(nm + 'GLeg', [(x, y, 0), (x * 0.7, y * 0.7, 5)], 0.12, V.paint('GuardW', '#FFFFFF'), t)
        box(nm + 'GHut', (2.4, 2.4, 2.0), (0, 0, 6), V.paint('GuardR', '#FF5A6E'), t, outline=0.03)
        cone(nm + 'GRoof', 2.2, 0.2, 1.0, (0, 0, 7.5), V.paint('GuardRoof', '#FFFFFF'), t, outline=0.03, verts=4)
        real.sun(V.sun_rot(50, 200), strength=6.0, hexc='#FFF1D6', angle=1.2, name=nm + 'Sun')
        real.shafts((0, 40, 8), (160, 120, 20), density=0.0015, hexc='#CFE8FF', name=nm + 'Haze')
    return {'root': root, 'ball': ball, 'castle': castle}


def suburb(nm, origin):
    """sunny suburban street: houses, lawns, picket fences, puffy trees, bus stop. SKY day"""
    with SetBuilder(nm, origin) as root:
        box(nm + 'Road', (200, 10, 0.2), (0, -8, -0.2), V.pat(nm + 'Asph', '#3C4560', '#475173', 'gravel', scale=0.6, mode='floor', c3='#353D57', bump=0.08))
        for i in range(12):
            box(nm + 'Dash', (3.0, 0.3, 0.02), (-44 + i * 8, -8, -0.09), V.paint('RoadLine', '#FFD23F', grime=0.05))
        box(nm + 'Walk', (200, 3, 0.3), (0, -1.6, -0.15), V.pat(nm + 'WalkM', '#E8DCC8', '#DCCFB8', 'bricks', scale=0.9, mode='floor'))
        lawn = V.pat(nm + 'LawnM', '#5DBA3F', '#7ED34E', 'grass', scale=0.5, mode='floor', c3='#9AD84A', bump=0.2)
        box(nm + 'Lawn', (200, 30, 0.2), (0, 14, -0.1), lawn)
        box(nm + 'LawnF', (200, 20, 0.2), (0, -24, -0.1), lawn)
        cols = ('#FFB3C7', '#8FC8FF', '#FFD05A', '#B6E07A', '#C9A8F0', '#FF9C7A')
        for i, x in enumerate((-36, -18, 0, 18, 36)):
            V.load('city-kit-suburban', 'building-type-' + 'abcdefg'[i], (x, 14, 0), size=13, tint=cols[i], amt=0.6)
        for i, x in enumerate((-27, -9, 9, 27)):
            V.puff_tree(f'{nm}Tree{i}', (x, 6, 0), h=9 + (i % 2), col=('#5DBB4A', '#7CC84A')[i % 2], seed=i)
        fm = V.paint('Picket', '#FFFFFF', grime=0.05)
        for x in range(-40, 41, 1):
            box(nm + 'Pick', (0.25, 0.15, 1.6), (x, 1.2, 0.8), fm)
        box(nm + 'Rail', (82, 0.12, 0.2), (0, 1.15, 1.1), fm)
        V.load('retro-urban-kit', 'detail-bench', (7, -1.0, 0), size=10)
        box(nm + 'BusPole', (0.15, 0.15, 6), (4.5, -2.6, 3), V.paint('Pole', '#F4EEDC'))
        sign(nm + 'BusSign', 'BUS', (4.5, -2.7, 5.6), 0.5, board='#2F6FD8', inkc='#FFFFFF', k=1.0)
        box(nm + 'Mailbox', (0.7, 1.0, 0.8), (-6, 0.2, 2.2), V.paint('MailBlue', '#2F6FD8'), outline=0.03, bevel=0.2)
        tube(nm + 'MailPost', [(-6, 0.2, 0), (-6, 0.2, 1.8)], 0.08, V.paint('Pole', '#F4EEDC'))
        real.sun(V.sun_rot(48, 215), strength=6.0, hexc='#FFF1D6', angle=1.2, name=nm + 'Sun')
        real.shafts((0, 20, 8), (160, 100, 20), density=0.0015, hexc='#CFE8FF', name=nm + 'Haze')
    return {'root': root, 'bus_stop': (6.5, -1.0, 0)}


def coaster_path(u):
    """u 0..1 along the coaster: x from -40 to 40, a big hill at x=-12 and a drop to x=6"""
    x = -40 + 80 * u
    z = 2.5 + 13 * math.exp(-((x + 12) / 9) ** 2) + 5 * math.exp(-((x - 22) / 7) ** 2)
    return (x, 6.0, z)


def coaster(nm, origin):
    """theme park: roller coaster with a big drop, ferris wheel, striped tent, pennants. SKY day.
    returns 'car' (an empty; animate it with ride())"""
    with SetBuilder(nm, origin) as root:
        box(nm + 'Grass', (200, 120, 0.2), (0, 30, -0.1), V.pat(nm + 'GrassM', '#5DBA3F', '#7ED34E', 'grass', scale=0.5, mode='floor', c3='#9AD84A', bump=0.2))
        box(nm + 'Path', (200, 6, 0.1), (0, -4, 0.0), V.pat(nm + 'PathM', '#F2B48C', '#E89C7A', 'bricks', scale=0.9, mode='floor'))
        pts = [coaster_path(k / 80) for k in range(81)]
        rm = V.paint('RailRed', '#FF2E3A', kind='metal', rough=0.3)
        for dy in (-0.6, 0.6):
            tube(nm + 'Rail', [(x, y + dy, z) for x, y, z in pts], 0.12, rm, outline=0.02)
        sm = V.paint('Support', '#FFFFFF', kind='metal')
        for k in range(0, 81, 3):
            x, y, z = pts[k]
            tube(nm + 'Sup', [(x, y, 0), (x, y, z - 0.1)], 0.12, sm)
            box(nm + 'Tie', (0.2, 1.6, 0.12), (x, y, z - 0.12), V.paint('Tie', '#2B2A72'))
        car = empty(nm + 'Car', pts[0])
        box(nm + 'CarBody', (2.6, 1.8, 1.0), (0, 0, 0.7), V.paint('CarYel', '#FFD23F', rough=0.3), car, outline=0.04, bevel=0.2)
        box(nm + 'CarFront', (0.4, 1.8, 1.2), (1.4, 0, 0.9), V.paint('CarRed', '#FF5A6E', rough=0.3), car, outline=0.03, bevel=0.15)
        wheel = empty(nm + 'Wheel', (14, 40, 16))
        wm = V.paint('WheelW', '#FFFFFF', kind='metal')
        circ = [(13 * math.cos(a), 0, 13 * math.sin(a)) for a in [2 * math.pi * k / 48 for k in range(49)]]
        tube(nm + 'Rim', circ, 0.3, wm, wheel, outline=0.03)
        cc = ('#FF5A6E', '#FFD23F', '#3FE0C8', '#C77BFF', '#2F6FD8', '#FF9C3A')
        for k in range(12):
            a = 2 * math.pi * k / 12
            tube(nm + 'Spoke', [(0, 0, 0), (13 * math.cos(a), 0, 13 * math.sin(a))], 0.12, wm, wheel)
            box(nm + 'Cab', (1.6, 1.6, 1.6), (13 * math.cos(a), 0, 13 * math.sin(a) - 1.2), V.paint('Cab' + cc[k % 6], cc[k % 6]), wheel, outline=0.03, bevel=0.2)
        for s in (-1, 1):
            tube(nm + 'WLeg', [(14 + s * 7, 40, 0), (14, 40, 16)], 0.4, wm, outline=0.03)
        cone(nm + 'Tent', 9, 0.3, 7, (-26, 30, 7.5), V.pat('TentM', '#FF5A6E', '#FFFFFF', 'stripes', scale=1.2, mode='box'), outline=0.05, verts=24)
        cylinder(nm + 'TentBase', 8.5, 4, (-26, 30, 2), V.pat('TentM2', '#FFD23F', '#FF5A6E', 'stripes', scale=1.2, mode='box'), outline=0.04)
        fc = ('#FF5A6E', '#FFD23F', '#3FE0C8', '#2F6FD8')
        for i in range(24):
            x = -30 + i * 2.5
            cone(nm + 'Pennant', 0.5, 0.0, 0.9, (x, -6, 7 - 0.8 * math.sin(math.pi * (i % 12) / 11)), V.paint('Pen' + fc[i % 4], fc[i % 4]), verts=3, rot=(180, 0, 0))
        for x in (-30, 30):
            tube(nm + 'FlagPole', [(x, -6, 0), (x, -6, 7.5)], 0.1, V.paint('Pole', '#F4EEDC'))
        for i, x in enumerate((-36, 34, 44)):
            V.puff_tree(f'{nm}Tree{i}', (x, 14, 0), h=9, col='#5DBB4A', seed=i)
        real.sun(V.sun_rot(45, 210), strength=6.0, hexc='#FFF1D6', angle=1.2, name=nm + 'Sun')
        real.shafts((0, 30, 10), (160, 100, 26), density=0.0015, hexc='#CFE8FF', name=nm + 'Haze')
    return {'root': root, 'car': car}


def ride(car, origin, t0, t1, u0=0.0, u1=1.0, steps=24):
    """move the coaster car along coaster_path between t0 and t1, pitched with the slope"""
    for k in range(steps + 1):
        u = u0 + (u1 - u0) * k / steps
        x, y, z = coaster_path(u)
        x2, _, z2 = coaster_path(min(1, u + 0.005))
        pitch = math.atan2(z2 - z, x2 - x)
        A.set(car, 'location', t0 + (t1 - t0) * k / steps, (origin[0] + x, origin[1] + y, origin[2] + z))
        A.set(car, 'rotation_euler', t0 + (t1 - t0) * k / steps, (0, -pitch, 0))


def library(nm, origin, title='MEMORY ARCHIVE'):
    """brain memory archive: tall colourful bookshelves, giant scrapbook on a desk, sign. SKY indoor.
    returns 'pages' (the scrapbook page stack: animate scale Z = how full the year is)"""
    with SetBuilder(nm, origin) as root:
        room(nm, 13, 10, -12, 12, V.pat(nm + 'Wall', '#1FA58C', '#1A9480', 'wallpaper', scale=0.5, mode='wall', c3='#FFD23F'),
             V.pat(nm + 'Floor', '#B9733A', '#A8652E', 'planks', scale=0.5, mode='floor'),
             wallx=V.pat(nm + 'WallX', '#1FA58C', '#1A9480', 'wallpaper', scale=0.5, mode='wallx', c3='#FFD23F'), trim='#6B3A22', beams='#8A4A2A')
        wood = V.pat('ShelfWood', '#8A4A2A', '#7A3E22', 'planks', scale=1.0, mode='box')
        bc = ('#FF5A6E', '#FFD23F', '#3FE0C8', '#2F6FD8', '#C77BFF', '#FF9C3A', '#7CC84A', '#FFFFFF')
        k = 0
        for sx in (-12.2, 12.2):
            for y0 in (-6, 0, 6):
                box(nm + 'Shelf', (0.8, 5.0, 10), (sx, y0, 5), wood, outline=0.03)
                for row in range(5):
                    z = 0.9 + row * 1.9
                    box(nm + 'Board', (1.0, 5.0, 0.15), (sx, y0, z - 0.1), wood)
                    yy = y0 - 2.2
                    while yy < y0 + 2.2:
                        w = 0.3 + 0.15 * ((k * 7) % 3)
                        box(nm + 'Book', (0.7, w, 1.2 + 0.2 * (k % 3)), (sx - math.copysign(0.6, sx), yy + w / 2, z + 0.6 + 0.1 * (k % 3)),
                            V.paint('Book' + bc[k % 8], bc[k % 8], grime=0.05))
                        yy += w + 0.05
                        k += 1
        box(nm + 'Desk', (8, 4, 2.6), (0, 4.5, 1.3), wood, outline=0.04, bevel=0.1)
        box(nm + 'Cover', (6.4, 3.6, 0.25), (0, 4.5, 2.75), V.paint('BookCover', '#E53945', grime=0.05), outline=0.04, bevel=0.05)
        pages = empty(nm + 'PagesP', (0, 4.5, 2.88))
        box(nm + 'Pages', (6.0, 3.3, 0.6), (0, 0, 0.3), V.pat('PageStack', '#FFF6E4', '#EDE2CC', 'stripes', scale=12, mode='box', rough=0.9), pages, outline=0.03)
        photos = []
        for i, (x, c) in enumerate(((-1.6, '#3FE0C8'), (1.4, '#FFB830'), (-0.2, '#FF7AB6'))):
            ph = box(f'{nm}Photo{i}', (1.4, 1.1, 0.05), (x, 0.3 * (i % 2) - 0.1, 0.63), V.paint('Photo' + c, c, grime=0), pages, outline=0.02)
            ph.rotation_euler = (0, 0, 0.15 * (i - 1))
            photos.append(ph)
        sign(nm + 'Title', title, (0, 9.75, 9.0), 0.7, board='#E53945', inkc='#FFF4D0')
        for x in (-5, 5):
            lamp(nm + 'Lamp', (x, 2, 10.2), shade='#FFD23F', power=800)
        real.area((0, -6, 11.5), (30, 0, 0), 16, 700, '#FFE6C8', shadow=False, name=nm + 'Fill', volume=0.0)
        real.shafts((0, 0, 6), (24, 20, 12), density=0.006, hexc='#FFE0B0', name=nm + 'Haze')
    return {'root': root, 'pages': pages, 'photos': photos, 'book': (0, 4.5, 3.5)}


PAGE_COLS = ('#3FE0C8', '#FFB830', '#FF7AB6', '#8FB8FF', '#B6E07A', '#FF5A6E')


def flying_pages(nm, origin, t0, t1, src, dst, n=10, cols=PAGE_COLS, every=0.18):
    """bright photo pages flying from src to dst (local points of the set at origin) between t0 and t1"""
    from ep_common import show as _show
    out = []
    for i in range(n):
        t = t0 + i * every
        if t > t1 - 0.3:
            break
        p = box(f'{nm}{i}', (1.2, 0.9, 0.04), (0, 0, 0), V.paint('Fly' + cols[i % len(cols)], cols[i % len(cols)], grime=0), outline=0.02)
        A.set(p, 'location', t, (origin[0] + src[0] + 0.6 * ((i % 3) - 1), origin[1] + src[1], origin[2] + src[2] + 0.4 * (i % 2)))
        A.set(p, 'location', t + 0.6, (origin[0] + dst[0], origin[1] + dst[1], origin[2] + dst[2]))
        A.set(p, 'rotation_euler', t, (0.4 * i, 0.3, 0.7 * i))
        A.set(p, 'rotation_euler', t + 0.6, (0, 0, 0.2 * (i % 3)))
        _show([p], [(t, t + 0.62)])
        out.append(p)
    return out


def bedroom(nm, origin, neon=False):
    """bedroom: wallpaper, bed, nightstand + alarm clock, window, posters, rug. neon=True: purple walls, LED strips, speakers.
    SKY indoor (neon: 'neon'). returns 'bed' (mattress top, centre), 'clock'"""
    with SetBuilder(nm, origin) as root:
        if neon:
            wall = V.pat(nm + 'Wall', '#4A2A9E', '#3E2288', 'stripes', scale=1.2, mode='wall')
            wallx = V.pat(nm + 'WallX', '#4A2A9E', '#3E2288', 'stripes', scale=1.2, mode='wallx')
            floor = V.pat(nm + 'Floor', '#2B2A72', '#FF7AB6', 'dots', scale=1.0, mode='floor', c3='#2B2A72')
        else:
            wall = V.pat(nm + 'Wall', '#8FC8FF', '#7FB8F0', 'wallpaper', scale=0.6, mode='wall', c3='#FFFFFF')
            wallx = V.pat(nm + 'WallX', '#8FC8FF', '#7FB8F0', 'wallpaper', scale=0.6, mode='wallx', c3='#FFFFFF')
            floor = V.pat(nm + 'Floor', '#C88A54', '#B67A46', 'planks', scale=0.5, mode='floor')
        room(nm, 11, 9, -11, 9.5, wall, floor, wallx=wallx, trim='#FFFFFF' if not neon else '#2B2A72', ceil='#F6EEDF' if not neon else '#2B1A5A')
        bed = empty(nm + 'Bed', (-3.5, 5.0, 0))
        wood = V.paint('BedWood', '#8A4A2A', kind='wood')
        box(nm + 'BedFrame', (6.0, 8.0, 1.6), (0, 0, 0.8), wood, bed, outline=0.04, bevel=0.1)
        box(nm + 'Headboard', (6.2, 0.5, 4.2), (0, 3.9, 2.1), wood, bed, outline=0.04, bevel=0.15)
        box(nm + 'Mattress', (5.7, 7.6, 0.8), (0, 0, 1.9), V.paint('Mattress', '#FFFFFF'), bed, outline=0.03, bevel=0.25)
        box(nm + 'Blanket', (5.9, 4.6, 0.5), (0, -1.6, 2.3), V.pat(nm + 'BlanketM', '#FF7AB6' if neon else '#FFD23F', '#FFFFFF', 'checker', scale=1.2, mode='box'), bed, outline=0.03, bevel=0.2)
        box(nm + 'Pillow', (3.6, 1.6, 0.7), (0, 2.8, 2.5), V.paint('PillowW', '#FFFFFF'), bed, outline=0.03, bevel=0.3)
        box(nm + 'Stand', (2.0, 2.0, 2.4), (1.6, 7.6, 1.2), V.paint('StandM' + str(neon), '#FF5A6E' if not neon else '#3FE0C8'), outline=0.03, bevel=0.08)
        clock = box(nm + 'Clock', (1.0, 0.6, 0.7), (1.6, 7.4, 2.75), V.paint('ClockM', '#2B2A72'), outline=0.03, bevel=0.1)
        box(nm + 'ClockFace', (0.8, 0.05, 0.45), (1.6, 7.08, 2.75), glow('ClockG', '#FF3B3B', 4))
        window(nm + 'Win', (5.0, 8.85, 5.2), 4.4, 3.4, '#4F95EE' if not neon else '#1A1A5A', '#FFE3B0' if not neon else '#7A3AB8')
        for i, (x, c, c2) in enumerate(((-8.5, '#FFB830', '#FF5A6E'), (9.6, '#3FE0C8', '#2F6FD8'))):
            box(nm + 'Poster', (2.2, 0.1, 3.0), (x, 8.85, 5.4), V.pat(nm + f'Poster{i}', c, c2, 'dots', scale=2.0, mode='wall', grime=0), outline=0.03)
        box(nm + 'Rug', (7, 5, 0.04), (3.5, 0, 0.02), V.pat(nm + 'RugM', '#FF7AB6' if neon else '#E53945', '#FFD23F', 'rug', scale=0.4, mode='floor', c3='#FF9C3A'))
        if neon:
            box(nm + 'LedB', (22, 0.15, 0.15), (0, 8.8, 9.2), glow('LedPink', '#FF4FD8', 10))
            for s, c in ((-1, '#3FE0F8'), (1, '#FF4FD8')):
                box(nm + 'LedS', (0.15, 20, 0.15), (s * 10.8, -1, 9.2), glow('Led' + c, c, 10))
                real.point((s * 8, 2, 8), 900, c, radius=1.0, name=nm + 'LedL', volume=0.0)
            for x in (8.5, -9.6):
                box(nm + 'Speaker', (1.6, 1.4, 3.0), (x, 7.6, 1.5), V.paint('SpeakerM', '#1C1B4A'), outline=0.03, bevel=0.1)
                cylinder(nm + 'Cone', 0.55, 0.1, (x, 6.85, 1.9), V.paint('ConeM', '#3FE0F8', kind='metal'), rot=(90, 0, 0))
        else:
            lamp(nm + 'Lamp', (2, 0, 9.0), shade='#FF5A6E', power=600)
        real.area((0, -7, 9.2), (30, 0, 0), 14, 600 if not neon else 300, '#FFE6C8' if not neon else '#B48AFF', shadow=False, name=nm + 'Fill', volume=0.0)
        real.area((5, 8, 5), (-90, 0, 0), 4, 500 if not neon else 150, '#FFF0D0', shadow=True, name=nm + 'WinL', volume=0.0)
    return {'root': root, 'bed': (-3.5, 5.0, 2.3), 'clock': clock}


def office(nm, origin):
    """office: mustard wallpaper, teal cubicle walls, desk + monitor, big wall calendar, city window. SKY indoor"""
    with SetBuilder(nm, origin) as root:
        room(nm, 12, 9, -11, 9.5, V.pat(nm + 'Wall', '#FFC93C', '#F2B830', 'wallpaper', scale=0.55, mode='wall', c3='#FFFFFF'),
             V.pat(nm + 'Floor', '#2F6FD8', '#3A7AE0', 'rug', scale=0.4, mode='floor', c3='#2A62C8'),
             wallx=V.pat(nm + 'WallX', '#FFC93C', '#F2B830', 'wallpaper', scale=0.55, mode='wallx', c3='#FFFFFF'), trim='#2B2A72')
        cub = V.pat(nm + 'Cub', '#1FA58C', '#1A9480', 'rug', scale=0.6, mode='box', c3='#22B5A0')
        box(nm + 'CubL', (0.3, 7, 4.4), (-5, 3, 2.2), cub, outline=0.03)
        box(nm + 'CubR', (0.3, 7, 4.4), (5, 3, 2.2), cub, outline=0.03)
        box(nm + 'Desk', (9.6, 3.6, 0.25), (0, 4.6, 2.9), V.paint('DeskTop', '#F4EEDC', rough=0.4), outline=0.03)
        for x in (-4.4, 4.4):
            box(nm + 'DeskLeg', (0.3, 3.2, 2.8), (x, 4.6, 1.4), V.paint('DeskLegM', '#2B2A72'))
        box(nm + 'Monitor', (3.2, 0.25, 2.0), (0, 5.8, 4.4), V.paint('MonFrame', '#1C1B4A'), outline=0.03)
        box(nm + 'Screen', (2.8, 0.1, 1.6), (0, 5.65, 4.4), glow('OffScreen', '#8FD8FF', 2.2))
        box(nm + 'MonStand', (0.4, 0.4, 0.9), (0, 5.9, 3.4), V.paint('MonFrame', '#1C1B4A'))
        box(nm + 'Keyb', (2.4, 0.8, 0.12), (0, 4.0, 3.07), V.paint('KeybM', '#FFFFFF'), outline=0.02)
        cylinder(nm + 'Mug', 0.3, 0.6, (2.6, 4.0, 3.3), V.paint('MugRed', '#FF5A6E'), outline=0.02)
        cal = empty(nm + 'Cal', (-7.5, 8.75, 5.5))
        box(nm + 'CalBack', (2.6, 0.12, 3.2), (0, 0, 0), V.paint('CalRed', '#E53945'), cal, outline=0.03)
        box(nm + 'CalPage', (2.3, 0.1, 2.3), (0, -0.08, -0.3), V.paint('CalPageM', '#FFFFFF'), cal, outline=0.02)
        t = text_obj(nm + 'CalTxt', 'MON', 0.5, (0, -0.15, -0.5), V.paint('CalInk', '#2B2A72'), extrude=0.01, parent=cal)
        t.data.align_x = 'CENTER'
        window(nm + 'Win', (6.5, 8.85, 5.4), 4.0, 3.6, '#4F95EE', '#FFE3B0')
        for x, y in ((-10.5, 7.5), (10.5, 7.5)):
            furn('pottedPlant', (x, y, 0), size=FURN * 1.1)
        lamp(nm + 'Lamp', (0, 3, 9.0), shade='#2F6FD8', power=600)
        real.area((0, -7, 9.2), (30, 0, 0), 14, 600, '#FFE6C8', shadow=False, name=nm + 'Fill', volume=0.0)
    return {'root': root, 'seat': (0, 2.4, 1.7), 'cal': (-7.5, 8.6, 5.2)}


def kitchen(nm, origin):
    """home kitchen: coral tile walls, mint cabinets, fridge, yellow table, coffee machine, window. SKY indoor"""
    with SetBuilder(nm, origin) as root:
        room(nm, 12, 9, -11, 9.5, V.pat(nm + 'Wall', '#FFB3A0', '#FF9C88', 'checker', scale=1.4, mode='wall'),
             V.pat(nm + 'Floor', '#2B2A72', '#FFF4DC', 'checker', scale=0.45, mode='floor', rough=0.35),
             wallx=V.pat(nm + 'WallX', '#FFB3A0', '#FF9C88', 'checker', scale=1.4, mode='wallx'), trim='#FFFFFF')
        for x in (-8, -4, 0):
            furn('kitchenCabinet', (x, 7.4, 0), tint='#7FD8C8', amt=0.9)
            furn('kitchenCabinetUpper', (x, 8.2, 5.8), tint='#7FD8C8', amt=0.9)
        furn('kitchenFridgeLarge', (5, 7.6, 0))
        furn('kitchenCoffeeMachine', (-4, 7.6, 2.9), size=FURN * 1.2)
        window(nm + 'Win', (-4, 8.85, 5.6), 4.2, 2.6, '#4F95EE', '#FFE3B0')
        box(nm + 'Table', (5, 3.4, 0.25), (0, 0.5, 2.9), V.paint('TableTop', '#FFD23F', rough=0.4), outline=0.03, bevel=0.05)
        for x, y in ((-2.2, -1), (2.2, -1), (-2.2, 2), (2.2, 2)):
            box(nm + 'TLeg', (0.25, 0.25, 2.8), (x, 0.5 + y * 0.6, 1.4), V.paint('TLegM', '#2B2A72'))
        cylinder(nm + 'Plate', 0.8, 0.08, (0, -0.2, 3.07), V.paint('PlateW', '#FFFFFF'), outline=0.02)
        ellipsoid(nm + 'Food', (0.5, 0.5, 0.18), (0, -0.2, 3.2), V.paint('FoodM', '#C88A44'), outline=0.02, segs=16, rings=8)
        cylinder(nm + 'Mug', 0.3, 0.6, (1.4, 0.0, 3.3), V.paint('MugBlue', '#2F6FD8'), outline=0.02)
        lamp(nm + 'Lamp', (0, 0.5, 8.8), shade='#E53945', power=700)
        real.area((0, -7, 9.2), (30, 0, 0), 14, 600, '#FFE6C8', shadow=False, name=nm + 'Fill', volume=0.0)
        real.area((-4, 8, 5.6), (-90, 0, 0), 4, 500, '#FFF0D0', shadow=True, name=nm + 'WinL', volume=0.0)
    return {'root': root, 'seat': (0, 2.6, 1.7), 'counter': (-4, 6.4, 0)}


def market(nm, origin):
    """night food market: stalls with striped awnings, lantern strings, glowing signs. SKY night"""
    with SetBuilder(nm, origin) as root:
        box(nm + 'Ground', (200, 120, 0.2), (0, 20, -0.1), V.pat(nm + 'Pave', '#4A3A7A', '#3E2E6A', 'bricks', scale=0.9, mode='floor', rough=0.5))
        stalls = (('NOODLES', '#FF5A6E', '#FFFFFF', -9), ('TACOS', '#FFD23F', '#FF5A6E', 0), ('BBQ', '#3FE0C8', '#2B2A72', 9))
        for i, (txt, c1, c2, x) in enumerate(stalls):
            s = empty(f'{nm}Stall{i}', (x, 7, 0))
            box(nm + 'Counter', (7, 2.4, 2.8), (0, 0, 1.4), V.pat(nm + f'Cnt{i}', c2, c1, 'stripes', scale=1.5, mode='box'), s, outline=0.04, bevel=0.06)
            box(nm + 'CTop', (7.3, 2.7, 0.2), (0, 0, 2.9), V.paint('StallTop', '#F4EEDC'), s, outline=0.03)
            for px in (-3.4, 3.4):
                box(nm + 'SPost', (0.2, 0.2, 7), (px, -1.0, 3.5), V.paint('StallPost', '#6B4A3A', kind='wood'), s)
            aw = box(nm + 'Awn', (7.6, 3.2, 0.3), (0, -0.8, 6.6), V.pat(nm + f'Awn{i}', c1, '#FFFFFF', 'stripes', scale=1.6, mode='box'), s, outline=0.04)
            aw.rotation_euler = deg(-15, 0, 0)
            sign(f'{nm}Sign{i}', txt, (x, 5.6, 7.9), 0.6, board='#1C1B4A', inkc=c1, k=6)
            for k in range(4):
                c = ('#C88A44', '#FFB830', '#E53945', '#7CC84A')[k]
                ellipsoid(f'{nm}Food{i}{k}', (0.4, 0.4, 0.3), (-2 + k * 1.3, -0.3, 3.2), V.paint('Food' + c, c), s, outline=0.02, segs=12, rings=6)
            real.point((x, 4.5, 5.5), 900, '#FFC88A', radius=1.0, name=nm + 'StallL', volume=0.3)
        lc = ('#FF5A6E', '#FFD23F', '#3FE0C8', '#C77BFF', '#FF9C3A')
        for row, y in enumerate((1.0, -4.0)):
            for i in range(20):
                x = -16 + i * 1.7
                z = 9 - 1.2 * math.sin(math.pi * i / 19)
                ellipsoid(f'{nm}Lant{row}{i}', (0.35, 0.35, 0.45), (x, y, z), glow('Lant' + lc[i % 5], lc[i % 5], 7), segs=12, rings=8)
            tube(f'{nm}Wire{row}', [(-16 + i * 1.7, y, 9.3 - 1.2 * math.sin(math.pi * i / 19)) for i in range(20)], 0.03, ink())
        for x in (-18, 18):
            tube(nm + 'LPole', [(x, 1, 0), (x, 1, 9.6)], 0.12, ink())
            tube(nm + 'LPole', [(x, -4, 0), (x, -4, 9.6)], 0.12, ink())
        for i, (x, y, n, c) in enumerate(((-40, 60, 'building-e', '#7A5AD0'), (-20, 55, 'building-c', '#C2185B'), (20, 58, 'building-b', '#2F6FD8'), (40, 62, 'building-f', '#7A5AD0'))):
            V.load('city-kit-commercial', n, (x, y, 0), size=18, tint=c, amt=0.7)
        real.area((0, -10, 12), (40, 0, 0), 20, 500, '#B48AFF', shadow=False, name=nm + 'Fill', volume=0.0)
        real.shafts((0, 10, 6), (60, 40, 14), density=0.006, hexc='#FFB8E0', name=nm + 'Haze')
    return {'root': root}


# ================================================================== EP14 sets
def skin(nm, origin, n=6, gap=4.2):
    """macro skin landscape: peach skin ground, a grid of hairs (pivots: rotate X 0 = standing, 70 = lying flat)
    and goosebump mounds (scale Z: 0.15 flat -> 1 raised), each with a little pink muscle rope. SKY body"""
    with SetBuilder(nm, origin) as root:
        sk = real.mat(nm + 'Skin', '#FFC8A8', 'flesh', grime=0.08)
        box(nm + 'Ground', (200, 200, 0.2), (0, 40, -0.1), sk)
        for i in range(10):     # skin creases
            tube(f'{nm}Crease{i}', [(-40, -6 + i * 7, 0.02), (0, -5 + i * 7 + 1.5 * (i % 2), 0.02), (40, -6 + i * 7, 0.02)], 0.08,
                 V.paint('Crease', '#E8A088', grime=0))
        hm = V.paint('HairM', '#5E3F2B', rough=0.4)
        bm = real.mat(nm + 'Bump', '#FFC0A0', 'flesh', grime=0.05)
        mm = V.paint('MuscleRope', '#FF6F91', grime=0)
        hairs, bumps, ropes = [], [], []
        for i in range(n):
            for j in range(n):
                x, y = (i - (n - 1) / 2) * gap + (j % 2) * 1.2, j * gap - 2
                b = ellipsoid(f'{nm}Bump{i}{j}', (1.3, 1.3, 1.0), (x, y, 0), bm, outline=0.04, segs=24, rings=12)
                b.scale = (1, 1, 0.15)
                bumps.append(b)
                p = empty(f'{nm}HairP{i}{j}', (x, y, 0.1))
                tube(f'{nm}Hair{i}{j}', [(0, 0, 0), (0.1, 0, 2.5), (0.3, 0, 5.0)], 0.13, hm, p, outline=0.02, radii=[0.16, 0.12, 0.06])
                p.rotation_euler = deg(70, 0, 20 * ((i + j) % 3 - 1))
                hairs.append(p)
                r = tube(f'{nm}Rope{i}{j}', [(x + 0.2, y + 0.3, 0.6), (x + 1.4, y + 1.6, 0.15)], 0.12, mm, outline=0.02)
                ropes.append(r)
        real.sun(V.sun_rot(45, 200), strength=4.0, hexc='#FFF0E0', angle=3.0, name=nm + 'Sun')
        real.shafts((0, 20, 6), (80, 60, 14), density=0.006, hexc='#FFD0C0', name=nm + 'Haze')
    return {'root': root, 'hairs': hairs, 'bumps': bumps, 'ropes': ropes}


def snow_pine(nm, loc, h=8.0, parent=None):
    r = empty(nm, loc, parent)
    tube(nm + 'Trunk', [(0, 0, 0), (0, 0, h * 0.3)], h * 0.05, real.mat('PineTrunk', '#6B4A3A', 'wood', grime=0.1), r)
    gm, sm = V._leaf('#2F8F6A'), V.paint('SnowCap', '#F4FAFF', grime=0)
    for k in range(3):
        z = h * (0.25 + 0.22 * k)
        rad = h * (0.34 - 0.08 * k)
        cone(f'{nm}Tier{k}', rad, 0.0, h * 0.38, (0, 0, z + h * 0.19), gm, r, outline=0.04, verts=16)
        cone(f'{nm}Snow{k}', rad * 0.7, 0.0, h * 0.2, (0, 0, z + h * 0.3), sm, r, verts=16)
    return r


def ice_age(nm, origin):
    """ice-age valley at golden hour: snow, snowy pines, icy rocks, a far mammoth. SKY golden"""
    with SetBuilder(nm, origin) as root:
        snow = V.pat(nm + 'Snow', '#F4FAFF', '#DCEBFA', 'grass', scale=0.2, mode='floor', c3='#E8F0FF', bump=0.15)
        box(nm + 'Ground', (300, 300, 0.2), (0, 80, -0.1), snow)
        for x, y, rx, rz in ((-50, 90, 45, 14), (40, 110, 60, 20), (110, 80, 40, 12), (-10, 170, 100, 30)):
            ellipsoid(nm + 'Hill', (rx, 30, rz), (x, y, -rz * 0.3), snow, segs=32, rings=12)
        for i, (x, y, h) in enumerate(((-12, 8, 9), (13, 12, 10), (-20, 20, 12), (22, 26, 11), (-6, 30, 9), (6, 40, 12), (-30, 34, 13))):
            snow_pine(f'{nm}Pine{i}', (x, y, 0), h=h)
        ice = V.paint('IceRock', '#8FD0F8', rough=0.2)
        for i, (x, y, r) in enumerate(((-7, 3, 1.4), (8, 5, 2.0), (16, 2, 1.2))):
            ellipsoid(f'{nm}Ice{i}', (r, r * 0.8, r * 0.9), (x, y, r * 0.5), ice, outline=0.04, segs=16, rings=8)
        m = empty(nm + 'Mammoth', (34, 70, 0))
        fur = V.paint('MammFur', '#7A4A3A', kind='fabric')
        ellipsoid(nm + 'MBody', (6, 3.6, 4), (0, 0, 7), fur, m, outline=0.08)
        ellipsoid(nm + 'MHead', (2.6, 2.4, 2.6), (-6, 0, 8.5), fur, m, outline=0.07)
        tube(nm + 'MTrunk', [(-8, 0, 8), (-9.5, 0, 5), (-9, 0, 2.5)], 0.7, fur, m, outline=0.05)
        tube(nm + 'MTusk', [(-7.5, -1, 7), (-10, -1.2, 5.5), (-11, -1.3, 7)], 0.3, V.paint('Tusk', '#FFF6E4'), m, outline=0.04)
        for x in (-3.5, 3.5):
            for y in (-2, 2):
                tube(nm + 'MLeg', [(x, y, 4), (x, y, 0)], 1.1, fur, m, outline=0.05)
        real.sun(V.sun_rot(12, 25), strength=4.5, hexc='#FFB070', angle=2.0, name=nm + 'Sun')
        real.sun(V.sun_rot(40, 200), strength=2.2, hexc='#E8F0FF', angle=3.0, name=nm + 'Front')
        real.shafts((0, 40, 8), (160, 120, 20), density=0.004, hexc='#FFE0C8', name=nm + 'Haze')
    return {'root': root}


def snowfall(nm, origin, t0, t1, area=(-12, 12, -6, 10), n=40, top=14.0, speed=3.0):
    """falling snowflakes (world objects) between t0 and t1"""
    from ep_common import show as _show
    m = V.paint('Flake', '#FFFFFF', grime=0)
    out = []
    for i in range(n):
        x = origin[0] + area[0] + (area[1] - area[0]) * ((i * 0.618) % 1)
        y = origin[1] + area[2] + (area[3] - area[2]) * ((i * 0.381) % 1)
        f = ellipsoid(f'{nm}{i}', (0.1, 0.1, 0.1), (x, y, top), m, segs=8, rings=6)
        z0 = top * ((i * 0.737) % 1)
        dur = (t1 - t0)
        A.set(f, 'location', t0, (x, y, origin[2] + z0 + top * 0.6))
        A.set(f, 'location', t1, (x + 1.0, y, origin[2] + z0 + top * 0.6 - speed * dur))
        _show([f], [(t0, t1)])
        out.append(f)
    from acting import _linear
    for f in out:
        _linear(f, 'location')
    return out


def cave(nm, origin):
    """night: rocky ground, big cave mouth (dark inside), campfire (light 'CampL'), moon. SKY night.
    returns 'mouth' (local point at the cave's dark centre), 'fire_light'"""
    with SetBuilder(nm, origin) as root:
        rock = V.pat(nm + 'Rock', '#5A4A8A', '#4A3A7A', 'gravel', scale=0.25, mode='box', c3='#6A5A9A', bump=0.3)
        box(nm + 'Ground', (200, 200, 0.2), (0, 60, -0.1), V.pat(nm + 'Dirt', '#4A3A6A', '#3E2E5A', 'gravel', scale=0.5, mode='floor', c3='#5A4A7A', bump=0.2))
        for i, (x, y, z, rx, ry, rz) in enumerate(((-9, 12, 5, 6, 5, 8), (9, 12, 5, 6, 5, 8), (0, 13, 12, 12, 6, 5), (-16, 16, 4, 6, 6, 6), (16, 16, 4, 6, 6, 6))):
            ellipsoid(f'{nm}Boulder{i}', (rx, ry, rz), (x, y, z), rock, outline=0.08, segs=24, rings=12)
        box(nm + 'Dark', (12, 1.0, 12), (0, 15.5, 5), V.paint('CaveDark', '#0A0614', grime=0, rough=1.0))
        logs = V.paint('Log', '#6B4A3A', kind='wood')
        for a in (0, 60, 120):
            l = cylinder(f'{nm}Log{a}', 0.3, 2.6, (0, 1, 0.3), logs, rot=(0, 90, a), outline=0.03)
        for k, (s, c) in enumerate(((1.0, '#FF7A30'), (0.65, '#FFC83A'), (0.35, '#FFF2A0'))):
            cone(f'{nm}Flame{k}', 0.9 * s, 0.0, 2.6 * s, (0, 1, 0.5 + 1.3 * s), glow(f'Flame{k}', c, 8), verts=12)
        for i in range(8):
            a = i * 0.785
            ellipsoid(f'{nm}Stone{i}', (0.45, 0.45, 0.3), (1.5 * math.cos(a), 1 + 1.5 * math.sin(a), 0.2), V.paint('FireStone', '#8A8AA8'), outline=0.02, segs=12, rings=6)
        ellipsoid(nm + 'Moon', (5, 5, 5), (-40, 160, 60), glow('MoonG', '#FFF6D8', 4), segs=32, rings=16)
        for i, (x, y) in enumerate(((-24, 30), (26, 34), (-34, 50))):
            snow_pine(f'{nm}Pine{i}', (x, y, 0), h=13)
        real.shafts((0, 10, 6), (60, 40, 14), density=0.008, hexc='#C8B0FF', name=nm + 'Haze')
        real.area((0, -14, 12), (40, 0, 0), 20, 250, '#7A8AFF', shadow=False, name=nm + 'MoonFill', volume=0.0)
    fire = real.point((origin[0], origin[1] + 1, origin[2] + 2.5), 2500, '#FF9A40', radius=0.8, name=nm + 'CampL', volume=0.4)
    return {'root': root, 'mouth': (0, 14.5, 4.5), 'fire_light': fire}


def living(nm, origin):
    """living room: yellow wallpaper, red sofa, rug, lamp, TV, plant, frames, window. SKY indoor"""
    with SetBuilder(nm, origin) as root:
        room(nm, 12, 9, -11, 9.5, V.pat(nm + 'Wall', '#FFD05A', '#F2C24A', 'wallpaper', scale=0.6, mode='wall', c3='#FFFFFF'),
             V.pat(nm + 'Floor', '#C88A54', '#B67A46', 'planks', scale=0.5, mode='floor'),
             wallx=V.pat(nm + 'WallX', '#FFD05A', '#F2C24A', 'wallpaper', scale=0.6, mode='wallx', c3='#FFFFFF'), trim='#FFFFFF')
        furn('loungeSofa', (-1.5, 7.0, 0), rot=180, tint='#E53945', amt=0.9, size=FURN * 1.1)
        box(nm + 'Rug', (9, 6, 0.04), (0, 1.5, 0.02), V.pat(nm + 'RugM', '#1FA58C', '#FFF4DC', 'rug', scale=0.4, mode='floor', c3='#2BB5A0'))
        furn('lampRoundFloor', (-8.5, 7.5, 0), size=FURN * 1.1)
        furn('cabinetTelevision', (8.0, 1.0, 0), rot=-90, tint='#2B2A72', amt=0.8)
        furn('televisionModern', (8.4, 1.0, 2.6), rot=-90)
        furn('pottedPlant', (10.5, 7.8, 0), size=FURN * 1.2)
        for i, (x, c) in enumerate(((-4, '#2F6FD8'), (0, '#FF5A6E'), (4, '#3FE0C8'))):
            box(f'{nm}Frame{i}', (1.8, 0.12, 1.4), (x, 8.85, 6.5), V.paint('FrameGold', '#F2B53A', kind='metal'), outline=0.03)
            box(f'{nm}Pic{i}', (1.5, 0.1, 1.1), (x, 8.8, 6.5), V.pat(f'Pic{c}', c, '#FFFFFF', 'dots', scale=2.0, mode='wall', grime=0))
        window(nm + 'Win', (-10.85, 1.0, 5.4), 4.0, 3.4, '#4F95EE', '#FFE3B0', rot=90)
        lamp(nm + 'Lamp', (0, 2, 9.0), shade='#1FA58C', power=700)
        real.area((0, -7, 9.2), (30, 0, 0), 14, 600, '#FFE6C8', shadow=False, name=nm + 'Fill', volume=0.0)
        real.area((-10, 1, 5.4), (0, 90, 0), 4, 500, '#FFF0D0', shadow=True, name=nm + 'WinL', volume=0.0)
    return {'root': root, 'rug': (0, 1.5, 0)}


def concert(nm, origin):
    """concert crowd at night: stage BEHIND the camera (-Y), coloured beams sweeping over a cheering crowd, neon back wall.
    SKY neon. returns 'crowd' (list of (rig_like dict with 'root')) and 'spots'"""
    with SetBuilder(nm, origin) as root:
        box(nm + 'Floor', (80, 80, 0.2), (0, 20, -0.1), V.paint('ConFloor', '#1C1B4A', rough=0.4))
        box(nm + 'BackWall', (80, 0.5, 30), (0, 36, 15), V.pat(nm + 'BackW', '#2B1A5A', '#3A2280', 'stripes', scale=0.8, mode='wall'))
        for i, (x, c) in enumerate(((-14, '#FF4FD8'), (0, '#3FE0F8'), (14, '#FFD23F'))):
            sign(f'{nm}Neon{i}', ('LOUD', 'LIVE', 'WOW')[i], (x, 35.6, 14 + 2 * (i % 2)), 1.6, board='#1C1B4A', inkc=c, k=8)
        box(nm + 'Stage', (40, 8, 2.5), (0, -14, 1.25), V.paint('StageM', '#2B2A72'), outline=0.04)
        for x in (-16, 16):
            box(nm + 'Stack', (4, 3, 8), (x, -12, 4), V.paint('SpeakerM', '#1C1B4A'), outline=0.04)
        tm = V.paint('Truss', '#C9C9D6', kind='metal')
        tube(nm + 'Truss', [(-24, -11, 16), (24, -11, 16)], 0.35, tm, outline=0.03)
        tube(nm + 'Truss2', [(-24, -11, 17), (24, -11, 17)], 0.2, tm)
        crowd = []
        cc = ('#FF5A6E', '#3FE0C8', '#FFD23F', '#C77BFF', '#2F6FD8', '#FF9C3A', '#7CC84A')
        for i in range(36):
            x, y = -14 + (i % 9) * 3.5 + (i // 9 % 2) * 1.7, 4 + (i // 9) * 3.6
            if abs(x) < 2.6 and y < 6:
                continue
            p = empty(f'{nm}Fan{i}', (x, y, 0))
            r = empty(f'{nm}FanR{i}', (0, 0, 0), p)
            ellipsoid(f'{nm}FanBody{i}', (0.62, 0.5, 1.1), (0, 0, 3.3), V.paint('Fan' + cc[i % 7], cc[i % 7]), r, outline=0.05, segs=16, rings=8)
            ellipsoid(f'{nm}FanHead{i}', (1.0, 0.9, 0.92), (0, 0, 5.0), V.paint('FanSkin', '#F7F2EC', grime=0), r, outline=0.06, segs=24, rings=12)
            for s in (1, -1):
                tube(f'{nm}FanArm{i}{s}', [(s * 0.5, 0, 3.85), (s * 0.9, 0, 5.2), (s * 1.0, 0, 6.3)], 0.05, ink(), r)
            for s in (1, -1):
                tube(f'{nm}FanLeg{i}{s}', [(s * 0.22, 0, 2.5), (s * 0.24, 0, 0.1)], 0.055, ink(), r)
            crowd.append({'root': r})
        real.area((0, -6, 20), (20, 0, 0), 30, 1400, '#9A7AFF', shadow=False, name=nm + 'Fill', volume=0.0)
        real.shafts((0, 10, 10), (60, 50, 22), density=0.012, hexc='#FFFFFF', anisotropy=0.7, name=nm + 'Haze')
    spots = []
    for i, (x, c) in enumerate(((-15, '#FF4FD8'), (-5, '#3FE0F8'), (5, '#FFD23F'), (15, '#7A5AFF'))):
        sp = real.spot((origin[0] + x, origin[1] - 11, origin[2] + 15.5), (-60, 0, 0), 30000, angle=14, hexc=c, blend=0.3, name=nm + 'Spot', volume=1.5)
        spots.append(sp)
    return {'root': root, 'crowd': crowd, 'spots': spots}


# ================================================================== EP15 / EP16 sets
def cloud(nm, loc, s=1.0, col='#FFFFFF', parent=None):
    r = empty(nm, loc, parent)
    m = V.paint('Cloud' + col, col, grime=0, rough=0.9)
    for i, (x, y, z, k) in enumerate(((0, 0, 0, 1.0), (1.3, 0.2, -0.2, 0.75), (-1.3, -0.1, -0.25, 0.8), (0.5, 0.6, 0.5, 0.7), (-0.6, 0.4, 0.4, 0.65))):
        ellipsoid(f'{nm}P{i}', (k * s * 1.4, k * s * 1.1, k * s), (x * s, y * s, z * s), m, r, outline=0.04, segs=20, rings=10)
    return r


def dream_sky(nm, origin):
    """pastel dream sky: a castle on a floating island far below, puffy clouds (returned for drifting), a rainbow, other islands.
    SKY sunset. The hero flies around (0, 0, 0)."""
    with SetBuilder(nm, origin) as root:
        isl = empty(nm + 'Island', (0, 55, -38))
        ellipsoid(nm + 'IslTop', (24, 20, 3.0), (0, 0, 0), V.pat(nm + 'IslGrass', '#7ED34E', '#5DBA3F', 'grass', scale=0.3, mode='floor', c3='#C8E86A'), isl, outline=0.08)
        cone(nm + 'IslRock', 22, 2, 26, (0, 0, -14), V.pat(nm + 'IslRockM', '#A88AD8', '#8A6AC8', 'gravel', scale=0.2, mode='box', c3='#C8A8F0'), isl, outline=0.08, rot=(180, 0, 0))
        for x, y, h in ((0, 0, 3), (-9, -7, 2), (9, -7, 2), (-9, 7, 2), (9, 7, 2)):
            big = x == 0 and y == 0
            base = 'tower-square' if big else 'tower-hexagon'
            sz = 7.0 if big else 6.5
            z = 2.5
            V.load('castle-kit', base + '-base', (x, y, z), size=sz, parent=isl)
            z += sz * (1.0 if big else 1.31)
            for k in range(h - 1):
                V.load('castle-kit', 'tower-square-mid-windows' if big else 'tower-hexagon-mid', (x, y, z), size=sz, parent=isl)
                z += sz * (1.0 if big else 0.46)
            V.load('castle-kit', 'tower-square-top-roof-high' if big else 'tower-hexagon-roof', (x, y, z), size=sz, parent=isl,
                   tint='#FF7AB6' if big else '#8FB8FF', amt=0.7)
        for a in range(4):
            ang = a * math.pi / 2
            for k in (-1, 0, 1):
                V.load('castle-kit', 'wall', (9 * math.cos(ang) + k * 4.5 * math.sin(ang), 7 * math.sin(ang) - k * 4.5 * math.cos(ang) * 0.8, 2.5),
                       size=4.5, rot=(0, 0, math.degrees(ang) + 90), parent=isl)
        clouds = []
        for i, (x, y, z, s) in enumerate(((-14, 10, -6, 2.6), (13, 16, -9, 3.0), (-8, 30, -14, 3.4), (18, 40, -4, 2.4), (-22, 46, -2, 3.0),
                                          (6, -4, -9, 2.2), (-30, 20, 4, 2.8), (28, 24, 3, 2.6), (0, 70, -20, 4.0))):
            clouds.append(cloud(f'{nm}Cloud{i}', (x, y, z), s, '#FFFFFF' if i % 3 else '#FFE8F4'))
        for i, (x, y, z, r) in enumerate(((-40, 90, -20, 8), (45, 100, -10, 9), (-70, 130, 5, 12))):
            e = ellipsoid(f'{nm}MiniIsl{i}', (r, r * 0.9, r * 0.3), (x, y, z), V.paint('MiniIslG', '#7ED34E', grime=0.05), outline=0.06, segs=24, rings=10)
            cone(f'{nm}MiniRock{i}', r * 0.9, 0.3, r * 1.4, (x, y, z - r * 0.7), V.paint('MiniRock', '#A88AD8'), outline=0.06, rot=(180, 0, 0))
        rc = ('#FF5A6E', '#FF9C3A', '#FFD23F', '#7CC84A', '#3FA0FF', '#7A5AD0')
        for k, c in enumerate(rc):
            R = 60 - k * 2.0
            tube(f'{nm}Rainbow{k}', [(R * math.cos(a), 140, -30 + R * math.sin(a)) for a in [math.pi * j / 30 for j in range(31)]], 1.0,
                 real.mat('Rainbow' + c, c, 'glow', emit=1.6))
        real.sun(V.sun_rot(10, 15), strength=4.0, hexc='#FFC08A', angle=2.0, name=nm + 'Sun')
        real.sun(V.sun_rot(40, 200), strength=2.4, hexc='#FFE6F0', angle=3.0, name=nm + 'Front')
        real.shafts((0, 50, -10), (160, 140, 60), density=0.003, hexc='#FFD0E8', name=nm + 'Haze')
    return {'root': root, 'clouds': clouds}


def theater(nm, origin, screen='#FFB8E8'):
    """brain movie theater: purple velvet, gold, red seats, a glowing screen, a LIVE sign. SKY night"""
    with SetBuilder(nm, origin) as root:
        gold = V.paint('Gold', '#F2B53A', rough=0.3, kind='metal', grime=0.05)
        velvet = V.pat(nm + 'Velvet', '#7A1F3D', '#651733', 'stripes', scale=1.2, mode='wall', rough=0.9)
        velvetx = V.pat(nm + 'VelvetX', '#7A1F3D', '#651733', 'stripes', scale=1.2, mode='wallx', rough=0.9)
        carpet = V.pat(nm + 'Carpet', '#1F2E6B', '#F2B53A', 'dots', scale=1.6, mode='floor', rough=0.95, c3='#26357A')
        room(nm, 11, 9.2, -10, 10, velvet, carpet, wallx=velvetx, ceil='#1A1745', trim='#F2B53A')
        for s in (-1, 1):
            for y in (-6, -1, 4):
                box(nm + 'SconceB', (0.12, 0.7, 1.0), (s * 10.85, y, 5.4), gold)
                ellipsoid(nm + 'Sconce', (0.35, 0.35, 0.5), (s * 10.6, y, 5.7), glow('SconceGlow', '#FFB25C', 7.0), segs=12, rings=8)
        screen_ob = box(nm + 'Screen', (14, 0.1, 5.6), (0, 8.95, 5.2), glow(nm + 'ScreenM', screen, 2.6))
        box(nm + 'ScreenFrame', (14.6, 0.14, 6.2), (0, 9.0, 5.2), gold)
        for i, (x, z, r) in enumerate(((-3.0, 4.2, 1.2), (-1.4, 4.6, 0.9), (2.5, 3.8, 1.5))):     # dream castle silhouette on screen
            box(f'{nm}ScrTower{i}', (r * 1.6, 0.05, r * 2.2), (x, 8.88, z), V.paint('ScrInk', '#7A3A9A', grime=0))
            box(f'{nm}ScrCren{i}', (r * 1.9, 0.05, r * 0.35), (x, 8.88, z + r * 1.2), V.paint('ScrInk', '#7A3A9A', grime=0))
        sign(nm + 'Live', 'LIVE', (5.4, 8.7, 8.7), 0.6, board='#E53945', inkc='#FFFFFF', k=4)
        for ry, rz in ((-1.5, 0.0), (1.3, 0.35)):
            box(nm + 'Riser', (18, 2.8, rz + 0.01), (0, ry, rz / 2), carpet)
            for i in range(7):
                x = -6 + i * 2.0
                seat = V.paint('ThSeat', '#D7263D', rough=0.8, kind='fabric')
                box(nm + 'SeatPan', (1.6, 1.4, 0.4), (x, ry, rz + 1.2), seat, bevel=0.12)
                box(nm + 'SeatBack', (1.6, 0.35, 1.8), (x, ry - 0.7, rz + 2.1), seat, bevel=0.14)
        pod = box(nm + 'Podium', (2.0, 1.6, 2.6), (-7.5, 5.0, 1.3), V.paint('PodM', '#2B2A72'), outline=0.04, bevel=0.1)
        rec = cylinder(nm + 'RecBtn', 0.6, 0.35, (-7.5, 5.0, 2.75), V.paint('RecRed', '#C8323C', rough=0.4), outline=0.03)
        sign(nm + 'RecSign', 'RECORD', (-7.5, 4.15, 2.0), 0.3, board='#FFD23F', inkc='#2B2A72', k=0.3)
        real.area((0, 7.6, 5.2), (-80, 0, 0), 12, 1800, screen, shadow=True, name=nm + 'ScreenL', volume=0.0)
        real.area((0, -9, 9), (70, 0, 0), 14, 700, '#B27AFF', shadow=False, name=nm + 'Fill', volume=0.0)
        real.shafts((0, 4, 5), (18, 12, 9), density=0.008, hexc='#FFD0F0', name=nm + 'Haze')
    return {'root': root, 'rec': rec, 'seats': [(-6 + i * 2.0, 1.3, 1.95) for i in range(7)]}


def tank_room(nm, origin, label='MEMORY JUICE'):
    """brain chemical room: orange brick walls, a big glass tank of glowing liquid (scale the 'liquid' pivot Z to drain),
    pipes, a gauge (rotate 'needle' Y). SKY indoor"""
    with SetBuilder(nm, origin) as root:
        room(nm, 12, 9, -11, 11, V.pat(nm + 'Wall', '#E8743A', '#D8652E', 'bricks', scale=1.2, mode='wall'),
             V.pat(nm + 'Floor', '#2B2A72', '#3A3A8A', 'checker', scale=0.5, mode='floor', rough=0.35),
             wallx=V.pat(nm + 'WallX', '#E8743A', '#D8652E', 'bricks', scale=1.2, mode='wallx'), trim='#2B2A72', beams='#2B2A72')
        cylinder(nm + 'TankBase', 3.6, 1.0, (0, 4, 0.5), V.paint('TankBaseM', '#2B2A72', kind='metal'), outline=0.04)
        cylinder(nm + 'TankTop', 3.6, 0.6, (0, 4, 9.3), V.paint('TankBaseM', '#2B2A72', kind='metal'), outline=0.04)
        liquid = empty(nm + 'Liquid', (0, 4, 1.0))
        cylinder(nm + 'Juice', 3.1, 8.0, (0, 0, 4.0), real.mat('Juice', '#3FE0C8', 'glow', emit=1.8), liquid)
        cylinder(nm + 'Glass', 3.4, 8.0, (0, 4, 5.0), real.glass('TankGlass', '#E8FBFF', 0.15))
        sign(nm + 'Label', label, (0, 0.2, 10.4), 0.55, board='#FFD23F', inkc='#2B2A72', k=0.3)
        pm = V.paint('PipeY', '#FFD23F', kind='metal', rough=0.3)
        for s in (-1, 1):
            tube(nm + 'Pipe', [(s * 3.4, 4, 8.5), (s * 7, 4, 8.5), (s * 7, 8.6, 8.5)], 0.45, pm, outline=0.04)
            tube(nm + 'Pipe2', [(s * 3.4, 4, 2.0), (s * 9, 4, 2.0), (s * 9, 8.6, 2.0)], 0.45, V.paint('PipeB', '#3FA0FF', kind='metal'), outline=0.04)
        g = empty(nm + 'Gauge', (6.5, 8.75, 5.5))
        cylinder(nm + 'GaugeFace', 1.4, 0.2, (0, 0, 0), V.paint('GaugeW', '#FFFFFF'), g, rot=(90, 0, 0), outline=0.04)
        for k, c in enumerate(('#FF2E3A', '#FFD23F', '#7CC84A')):
            a = math.radians(150 - k * 60)
            box(f'{nm}Mark{k}', (0.5, 0.05, 0.2), (1.0 * math.cos(a), -0.12, 1.0 * math.sin(a)), V.paint('Mark' + c, c), g).rotation_euler = (0, -a, 0)
        needle = empty(nm + 'Needle', (0, -0.15, 0), g)
        box(nm + 'NeedleOb', (1.1, 0.05, 0.1), (0.55, 0, 0), V.paint('NeedleRed', '#2B2A72'), needle)
        needle.rotation_euler = (0, math.radians(-30), 0)
        lamp(nm + 'Lamp', (-5, 0, 10.4), shade='#3FE0C8', power=700)
        lamp(nm + 'Lamp2', (5, 0, 10.4), shade='#3FE0C8', power=700)
        real.area((0, -7, 10.6), (30, 0, 0), 14, 600, '#FFE6C8', shadow=False, name=nm + 'Fill', volume=0.0)
    return {'root': root, 'liquid': liquid, 'needle': needle}


def exam_hall(nm, origin):
    """exam hall: mint wallpaper, chalkboard 'FINAL EXAM', big wall clock (hour/min pivots, rotate Y), 3x3 desks.
    Students sit at seats[i] facing +Y (rot 180). SKY indoor"""
    with SetBuilder(nm, origin) as root:
        room(nm, 12, 9, -13, 10, V.pat(nm + 'Wall', '#9FE0C8', '#8CD0B8', 'wallpaper', scale=0.6, mode='wall', c3='#FFFFFF'),
             V.pat(nm + 'Floor', '#C88A54', '#B67A46', 'planks', scale=0.5, mode='floor'),
             wallx=V.pat(nm + 'WallX', '#9FE0C8', '#8CD0B8', 'wallpaper', scale=0.6, mode='wallx', c3='#FFFFFF'), trim='#2B2A72')
        box(nm + 'Board', (12, 0.2, 4.6), (0, 8.85, 5.4), V.paint('Chalk', '#2E6B4A', rough=0.9), outline=0.04)
        box(nm + 'BoardFrame', (12.5, 0.25, 5.1), (0, 8.9, 5.4), V.paint('BoardWood', '#8A4A2A', kind='wood'))
        t = text_obj(nm + 'BoardTxt', 'FINAL EXAM', 0.9, (0, 8.7, 5.6), V.paint('ChalkW', '#F4FFF4', grime=0), extrude=0.01)
        t.data.align_x = 'CENTER'
        t2 = text_obj(nm + 'BoardTxt2', 'SILENCE PLEASE', 0.45, (0, 8.7, 4.3), V.paint('ChalkY', '#FFE07A', grime=0), extrude=0.01)
        t2.data.align_x = 'CENTER'
        ck = empty(nm + 'Clock', (8.5, 8.75, 7.8))
        cylinder(nm + 'ClockFace', 1.3, 0.2, (0, 0, 0), V.paint('ClockW', '#FFFFFF'), ck, rot=(90, 0, 0), outline=0.05)
        cylinder(nm + 'ClockRim', 1.45, 0.15, (0, 0.08, 0), V.paint('ClockRimM', '#E53945'), ck, rot=(90, 0, 0), outline=0.03)
        hands = []
        for k, (L, w) in enumerate(((0.75, 0.12), (1.05, 0.08))):
            h = empty(f'{nm}Hand{k}', (0, -0.15, 0), ck)
            box(f'{nm}HandOb{k}', (w, 0.05, L), (0, 0, L / 2), V.paint('HandInk', '#2B2A72'), h)
            hands.append(h)
        hands[0].rotation_euler = (0, math.radians(60), 0)
        for i, x in enumerate((-9.5, 9.5)):
            window(nm + f'Win{i}', (x, 8.85, 7.4), 2.2, 2.0, '#4F95EE', '#FFE3B0')
        seats = []
        dm = V.paint('DeskTop', '#F2B53A', rough=0.4)
        cm = V.paint('ChairBlue', '#2F6FD8')
        for yd in (3.0, -2.5, -8.0):
            for x in (-6.0, 0.0, 6.0):
                box(nm + 'Desk', (3.2, 2.0, 0.2), (x, yd, 2.8), dm, outline=0.03, bevel=0.04)
                for sx in (-1.4, 1.4):
                    box(nm + 'DeskLeg', (0.15, 1.8, 2.7), (x + sx, yd, 1.35), V.paint('DeskLegM', '#2B2A72'))
                box(nm + 'Paper', (1.2, 1.5, 0.03), (x, yd + 0.1, 2.92), V.paint('PaperW', '#FFFFFF', grime=0))
                box(nm + 'ChairSeat', (1.8, 1.6, 0.25), (x, yd - 1.9, 1.45), cm, outline=0.03, bevel=0.05)
                box(nm + 'ChairBack', (1.8, 0.2, 2.0), (x, yd - 2.75, 2.5), cm, outline=0.03, bevel=0.05)
                seats.append((x, yd - 1.9, 1.6))
        box(nm + 'TeacherDesk', (5.0, 2.4, 2.8), (-6.5, 6.6, 1.4), V.paint('TDesk', '#8A4A2A', kind='wood'), outline=0.04, bevel=0.06)
        lamp(nm + 'Lamp', (-4, -3, 9.4), shade='#FFD23F', power=600)
        lamp(nm + 'Lamp2', (4, -3, 9.4), shade='#FFD23F', power=600)
        real.area((0, -11, 9.6), (35, 0, 0), 16, 700, '#FFE6C8', shadow=False, name=nm + 'Fill', volume=0.0)
        real.area((0, 8, 8), (-110, 0, 0), 10, 500, '#FFF0D0', shadow=True, name=nm + 'WinL', volume=0.0)
    return {'root': root, 'seats': seats, 'hands': hands}


def gut_tube(nm, origin):
    """inside the intestine: a long pink tunnel along Y with soft folds; 'ring' = muscle ring empty (animate location Y and
    scale XZ to squeeze). Floor at z ~0.6. SKY body"""
    with SetBuilder(nm, origin) as root:
        cylinder(nm + 'Tunnel', 7.0, 80, (0, 20, 6), real.mat(nm + 'In', '#FF8FA0', 'flesh', grime=0.2), rot=(90, 0, 0))
        for i in range(18):
            pts = [(6.8 * math.cos(a), -18 + i * 4.5, 6 + 6.8 * math.sin(a)) for a in [2 * math.pi * k / 28 for k in range(29)]]
            tube(f'{nm}Fold{i}', pts, 0.35, real.mat(nm + 'Fold', '#E8607A', 'flesh', grime=0.1))
        box(nm + 'Floor', (16, 80, 0.2), (0, 20, 0.5), real.mat(nm + 'Fl', '#E86A82', 'flesh', grime=0.2))
        for i in range(30):      # villi bumps on the floor
            ellipsoid(f'{nm}Villus{i}', (0.35, 0.35, 0.6), (-3.5 + (i * 2.3) % 7, -10 + i * 2.0, 0.8), V.paint('Villus', '#FFB0C0', grime=0), segs=10, rings=6)
        ring = empty(nm + 'Ring', (0, 30, 6))
        pts = [(6.4 * math.cos(a), 0, 6.4 * math.sin(a)) for a in [2 * math.pi * k / 32 for k in range(33)]]
        tube(nm + 'RingOb', pts, 1.0, V.pat('MuscleM', '#C2185B', '#E04A86', 'stripes', scale=4, mode='box'), ring, outline=0.05)
        real.point((0, -6, 9), 3000, '#FFD0DA', radius=1.5, name=nm + 'Glow', volume=0.0)
        real.point((0, 20, 8), 3000, '#FFB0C8', radius=2.0, name=nm + 'Glow2', volume=0.0)
        real.shafts((0, 15, 6), (14, 60, 12), density=0.008, hexc='#FFC0D0', name=nm + 'Haze')
    return {'root': root, 'ring': ring}


def stomach_room(nm, origin):
    """inside the stomach: a big round pink chamber with folds, a shiny acid pool, the food pipe coming in from the top.
    SKY body"""
    with SetBuilder(nm, origin) as root:
        shell = ellipsoid(nm + 'Shell', (18, 16, 12), (0, 4, 8), real.mat(nm + 'Wall', '#F27A8A', 'flesh', grime=0.15), segs=48, rings=24)
        for i in range(9):
            a = -0.9 + i * 0.22
            pts = [(17.5 * math.sin(a), 4 + 15.5 * math.cos(a) * math.cos(b), 8 + 11.5 * math.sin(b)) for b in [-1.2 + 2.4 * k / 16 for k in range(17)]]
            tube(f'{nm}Ruga{i}', pts, 0.45, real.mat(nm + 'Ruga', '#D9506A', 'flesh', grime=0.1))
        box(nm + 'Floor', (30, 30, 0.2), (0, 4, 0.3), real.mat(nm + 'Fl', '#E86A82', 'flesh', grime=0.2))
        ellipsoid(nm + 'Acid', (9, 7, 0.4), (0, 6, 0.45), real.mat('Acid', '#C8F04A', 'plastic', grime=0, rough=0.05, emit=0.5), segs=32, rings=8)
        tube(nm + 'Esoph', [(-6, 6, 22), (-5, 6, 17), (-4, 6, 15)], 2.2, V.paint('EsophM', '#FFB0C0'), outline=0.06)
        real.point((0, -4, 12), 3500, '#FFD8E0', radius=2.0, name=nm + 'Glow', volume=0.0)
        real.area((0, -8, 14), (35, 0, 0), 16, 700, '#FFE6EE', shadow=False, name=nm + 'Fill', volume=0.0)
        real.shafts((0, 4, 8), (30, 26, 16), density=0.008, hexc='#FFC0D0', name=nm + 'Haze')
    return {'root': root}


def sound_rings(nm, loc, t0, n=4, every=0.18, grow=6.0, col='#FFE14A', life=0.6, axis='y'):
    """expanding glowing rings (sound waves / echoes) at a world point"""
    from ep_common import show as _show
    out = []
    m = real.mat('Ring' + col, col, 'glow', emit=4.0)
    for i in range(n):
        pts = [(math.cos(a), 0, math.sin(a)) if axis == 'y' else (math.cos(a), math.sin(a), 0) for a in [2 * math.pi * k / 32 for k in range(33)]]
        r = tube(f'{nm}{i}', pts, 0.06, m)
        r.location = loc
        t = t0 + i * every
        A.set(r, 'scale', t, (0.3, 0.3, 0.3))
        A.set(r, 'scale', t + life, (grow, grow, grow))
        _show([r], [(t, t + life)])
        out.append(r)
    return out
