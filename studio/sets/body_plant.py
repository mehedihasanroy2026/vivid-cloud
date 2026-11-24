"""Sets: the 'inside your body' factory halls (EP06), real-light look.

Every hall shares one shell (shell()): pink painted block walls, concrete floor with yellow safety lines,
steel roof trusses + fluorescent strips, a row of high windows on the left wall that throw sun shafts
across the room, pipes along the back wall, and a big painted sign. Then each zone adds its machine.

Local layout of a hall: x -12..12, y -12..10, floor z=0, ceiling z=16. Cameras look toward +Y.
Characters are ~6 units tall.
"""
import math
import real
from toon import box, cylinder, ellipsoid, tube, cone, text_obj, SetBuilder, water_mat

W, D0, D1, H = 12.0, -12.0, 10.0, 16.0


def _mats():
    return {
        'wall': real.mat('BPWall', '#E7A3B4', 'brick', mode='wall', size=(1.2, 0.6), grime=0.22),
        'wallx': real.mat('BPWallX', '#E7A3B4', 'brick', mode='wallx', size=(1.2, 0.6), grime=0.22),
        'lower': real.mat('BPLower', '#7E93A6', 'paint', mode='wall', grime=0.3),
        'floor': real.mat('BPFloor', '#A9B1B8', 'concrete', mode='floor', scale=0.4, grime=0.35),
        'ceil': real.mat('BPCeil', '#5F7183', 'paint', grime=0.2),
        'steel': real.mat('BPSteel', '#8EA0B0', 'metal', grime=0.25),
        'dark': real.mat('BPDark', '#3D4855', 'metal', grime=0.2),
        'yellow': real.mat('BPYellow', '#F2C230', 'paint', grime=0.25),
        'sign': real.mat('BPSign', '#F4F1EA', 'paint', grime=0.15),
        'ink': real.mat('BPInk', '#25303D', 'paint', grime=0.0),
        'lamp': real.mat('BPLamp', '#FFF8EE', 'glow', emit=10.0),
        'sky': real.mat('BPSky', '#F4F8FF', 'glow', emit=4.0),
        'red': real.mat('BPRed', '#D23A3A', 'paint', grime=0.15),
        'rubber': real.mat('BPRubber', '#2B2F36', 'plastic', grime=0.1, rough=0.8),
        'pink': real.mat('BPFlesh', '#E87D93', 'flesh', grime=0.1),
    }


def shell(name, sign, sun_rot=(50, 0, -110), sun_power=11.0, haze=0.01, sign_x=0.0, sign_size=1.2, sign_w=11.0,
          mats=None):
    """The shared hall. Call inside a SetBuilder."""
    m = _mats()
    m.update(mats or {})
    box(f'{name}Floor', (2 * W + 0.4, D1 - D0 + 0.4, 0.2), (0, (D0 + D1) / 2, -0.1), m['floor'])
    box(f'{name}Ceil', (2 * W + 0.4, D1 - D0 + 0.4, 0.2), (0, (D0 + D1) / 2, H + 0.1), m['ceil'])
    box(f'{name}Back', (2 * W + 0.4, 0.4, H), (0, D1 + 0.2, H / 2), m['wall'])
    box(f'{name}BackLow', (2 * W, 0.1, 2.6), (0, D1 - 0.03, 1.3), m['lower'])
    box(f'{name}Right', (0.4, D1 - D0, H), (W + 0.2, (D0 + D1) / 2, H / 2), m['wallx'])
    box(f'{name}RightLow', (0.1, D1 - D0, 2.6), (W - 0.03, (D0 + D1) / 2, 1.3), m['lower'])
    # left wall with a row of tall high windows (z 9..14)
    box(f'{name}LeftLow', (0.4, D1 - D0, 9.0), (-W - 0.2, (D0 + D1) / 2, 4.5), m['wallx'])
    box(f'{name}LeftTop', (0.4, D1 - D0, 2.0), (-W - 0.2, (D0 + D1) / 2, 15.0), m['wallx'])
    box(f'{name}LeftLowB', (0.1, D1 - D0, 2.6), (-W + 0.03, (D0 + D1) / 2, 1.3), m['lower'])
    ys = [D0 + 1.0 + i * 3.0 for i in range(8)]
    for y in ys:
        box(f'{name}Pier', (0.5, 1.0, 5.0), (-W - 0.2, y, 11.5), m['wallx'])
    for y in ys[:-1]:
        box(f'{name}Mull', (0.12, 0.1, 5.0), (-W - 0.1, y + 1.5, 11.5), m['dark'])
        box(f'{name}MullH', (0.12, 2.0, 0.1), (-W - 0.1, y + 1.5, 11.5), m['dark'])
    sky = box(f'{name}SkyCard', (0.2, 60, 30), (-W - 12, 0, 10), m['sky'])
    sky.visible_shadow = False
    # floor safety lines
    for x in (-7.5, 7.5):
        box(f'{name}Line', (0.25, D1 - D0 - 1, 0.02), (x, (D0 + D1) / 2, 0.01), m['yellow'])
    box(f'{name}LineB', (15.2, 0.25, 0.02), (0, 6.5, 0.01), m['yellow'])
    # roof trusses + fluorescent strips
    for y in (-8.0, -2.0, 4.0):
        box(f'{name}Truss', (2 * W, 0.35, 0.7), (0, y, H - 0.6), m['steel'])
        box(f'{name}TrussLow', (2 * W, 0.25, 0.25), (0, y, H - 2.6), m['steel'])
        for i in range(9):
            x = -W + 1.4 + i * 2.65
            r = box(f'{name}Strut', (0.16, 0.16, 2.6), (x, y, H - 1.6), m['steel'])
            r.rotation_euler[1] = math.radians(35 if i % 2 else -35)
        for x in (-5.0, 5.0):
            box(f'{name}LampBox', (3.4, 0.6, 0.25), (x, y, H - 3.0), m['dark'])
            box(f'{name}LampTube', (3.2, 0.45, 0.06), (x, y, H - 3.14), m['lamp'])
    # pipes along the back wall
    for z, r, c in ((12.6, 0.35, 'steel'), (13.5, 0.25, 'red'), (11.8, 0.2, 'yellow')):
        cylinder(f'{name}Pipe', r, 2 * W, (0, D1 - 0.6, z), m[c], rot=(0, 90, 0))
        for x in (-8, 0, 8):
            box(f'{name}Bracket', (0.15, 0.7, 0.15), (x, D1 - 0.3, z + r + 0.05), m['dark'])
    # big painted sign on the back wall
    box(f'{name}SignBoard', (sign_w, 0.15, 2.2), (sign_x, D1 - 0.12, 8.6), m['sign'])
    box(f'{name}SignTrim', (sign_w + 0.3, 0.1, 2.5), (sign_x, D1 - 0.05, 8.6), m['dark'])
    t = text_obj(f'{name}SignText', sign, sign_size, (sign_x, D1 - 0.22, 8.6 - sign_size * 0.42), m['ink'], extrude=0.02)
    t.data.align_x = 'CENTER'
    # light
    real.sun(sun_rot, strength=sun_power, hexc='#FFE9C8', angle=1.0, name=f'{name}Sun')
    real.area((0, -16, 8), (78, 0, 0), 20, 1200, '#D8E4F2', shadow=False, name=f'{name}Front', volume=0.0)
    real.area((0, 0, H - 3.3), (0, 0, 0), 14, 700, '#FFF4E6', shadow=False, name=f'{name}Ceil', volume=0.0)
    real.shafts((0, (D0 + D1) / 2, H / 2), (2 * W, D1 - D0, H), density=haze, name=f'{name}Haze')
    return m


def sign(name, text, loc, size=0.6, w=None, rot=0, m=None, col='sign', parent=None):
    """A small painted sign board with text (faces -Y unless rot)."""
    m = m or _mats()
    w = w or (len(text) * size * 0.62 + 0.6)
    b = box(f'{name}Board', (w, 0.1, size * 1.8), loc, m[col], parent=parent)
    b.rotation_euler[2] = math.radians(rot)
    t = text_obj(f'{name}Text', text, size, (0, -0.07, -size * 0.38), m['ink'], extrude=0.01, parent=b)
    t.data.align_x = 'CENTER'
    return b


def catwalk(name, x0, x1, y, z, m):
    box(f'{name}Deck', (x1 - x0, 2.0, 0.15), ((x0 + x1) / 2, y, z), m['steel'])
    for s in (-1, 1):
        box(f'{name}Rail', (x1 - x0, 0.08, 0.08), ((x0 + x1) / 2, y + s * 0.95, z + 2.0), m['yellow'])
        box(f'{name}RailMid', (x1 - x0, 0.06, 0.06), ((x0 + x1) / 2, y + s * 0.95, z + 1.1), m['yellow'])
        n = int((x1 - x0) / 1.5) + 1
        for i in range(n):
            box(f'{name}Post', (0.08, 0.08, 2.0), (x0 + i * (x1 - x0) / (n - 1), y + s * 0.95, z + 1.0), m['yellow'])
    for x in (x0 + 0.5, x1 - 0.5):
        for s in (-1, 1):
            box(f'{name}Leg', (0.2, 0.2, z), (x, y + s * 0.85, z / 2), m['dark'])


# ================================================================ zones
def stomach(origin):
    """Stomach: a round pool filling with cola from a big pipe (FROM MOUTH)."""
    with SetBuilder('Stomach', origin) as root:
        m = shell('ST', 'STOMACH  -  TANK 1')
        brown = real.mat('ColaLiquid', '#4A2412', 'plastic', grime=0.0, rough=0.08)
        foam = real.mat('ColaFoam', '#D9B48A', 'fabric', grime=0.1)
        # tank: fleshy round wall with a steel lip
        cylinder('STTank', 6.5, 3.0, (0, 2.0, 1.5), m['pink'], verts=64)
        cylinder('STLip', 6.7, 0.35, (0, 2.0, 3.1), m['steel'], verts=64)
        pool = cylinder('STPool', 6.3, 0.1, (0, 2.0, 2.75), brown, verts=64)
        # foam ring + bubbles on the surface
        for i in range(26):
            a = i / 26 * 2 * math.pi
            r = 5.6 + 0.4 * math.sin(i * 1.7)
            ellipsoid('STFoam', (0.6, 0.6, 0.18), (r * math.cos(a), 2.0 + r * math.sin(a), 2.86), foam)
        # feed pipe from the top-back, pouring cola
        cylinder('STFeed', 1.0, 8.0, (0, 6.0, 12.5), m['steel'], rot=(90, 0, 0))
        tube('STFeedBend', [(0, 2.0, 12.5), (0, 2.0, 11.0), (0, 2.0, 10.0)], 1.0, m['steel'])
        cylinder('STNozzle', 1.2, 0.6, (0, 2.0, 9.8), m['dark'])
        fall = water_mat('ColaFall', '#5A2C14', speed=0.6)
        cylinder('STFall', 0.75, 7.2, (0, 2.0, 6.2), fall, verts=24)
        sign('STFromMouth', 'FROM MOUTH', (2.6, 4.0, 11.5), 0.5, m=m)
        catwalk('STWalk', -9.0, -3.5, -4.0, 3.0, m)
        cylinder('STGauge', 0.6, 0.15, (7.5, 8.0, 5.0), m['sign'], rot=(90, 0, 0))
        box('STControl', (2.2, 1.2, 3.2), (8.5, 7.0, 1.6), m['dark'])
        for i, c in enumerate(('red', 'yellow', 'lamp')):
            cylinder('STBtn', 0.18, 0.1, (8.0 + i * 0.5, 6.35, 2.6), m[c], rot=(90, 0, 0))
    return {'root': root, 'pool': pool}


def gut(origin):
    """Gut: a long conveyor; workers pull out water (blue drops) and sugar (cubes) into the BLOOD tank."""
    with SetBuilder('Gut', origin) as root:
        m = shell('GT', 'GUT  -  SORTING LINE', sun_rot=(48, 0, -115), sign_x=-5.0)
        # conveyor along x at y=1, top at z=2.6
        box('GTBelt', (22.0, 2.4, 0.3), (0, 1.0, 2.5), m['rubber'])
        box('GTFrame', (22.4, 2.8, 0.5), (0, 1.0, 2.15), m['steel'])
        for x in range(-10, 11, 2):
            cylinder('GTRoller', 0.3, 2.6, (x, 1.0, 2.2), m['dark'], rot=(90, 0, 0))
            box('GTLeg', (0.25, 0.25, 2.0), (x, 1.0, 1.0), m['dark'])
        # BLOOD tank behind the belt (glass with red liquid)
        cylinder('GTBloodTank', 2.4, 6.0, (2.5, 6.0, 3.0), real.glass('GTGlass', '#DDEBF3', 0.2), verts=48)
        blood = real.mat('BloodLiquid', '#B3122A', 'plastic', grime=0.0, rough=0.15)
        cylinder('GTBlood', 2.25, 3.4, (2.5, 6.0, 1.75), blood, verts=48)
        cylinder('GTTankLip', 2.5, 0.3, (2.5, 6.0, 6.1), m['steel'], verts=48)
        sign('GTBloodSign', 'BLOOD', (2.5, 3.5, 6.9), 0.7, m=m, col='red')
        # TO LIVER chute at the right end
        ch = box('GTChute', (3.0, 2.4, 0.2), (12.0, 1.0, 1.8), m['steel'])
        ch.rotation_euler[1] = math.radians(25)
        sign('GTLiverSign', 'TO LIVER  >', (9.5, 3.4, 5.6), 0.5, m=m)
        box('GTBin', (2.0, 2.0, 1.4), (-6.5, 4.0, 0.7), m['yellow'])
    return {'root': root}


def liver(origin):
    """Liver: a big hydraulic press that crushes brown dye blobs; an EXIT chute (to the poop) on the right."""
    with SetBuilder('Liver', origin) as root:
        m = shell('LV', 'LIVER  -  BREAKDOWN', sun_rot=(52, 0, -105), sign_x=5.5)
        # press frame
        for x in (-2.6, 2.6):
            box('LVColumn', (0.8, 0.8, 9.0), (x - 3.0, 3.0, 4.5), m['yellow'])
        box('LVTop', (6.8, 1.4, 1.2), (-3.0, 3.0, 9.4), m['yellow'])
        box('LVBed', (5.4, 3.0, 1.6), (-3.0, 3.0, 0.8), m['dark'])
        piston = cylinder('LVPiston', 0.5, 4.0, (-3.0, 3.0, 7.0), m['steel'])
        head = box('LVPressHead', (4.4, 2.4, 0.8), (-3.0, 3.0, 4.6), m['steel'])
        for i in range(6):
            box('LVStripe', (0.35, 0.05, 0.75), (-5.0 + i * 0.8, 1.78, 4.6), m['ink' if i % 2 else 'yellow'])
        sign('LVWarn', 'DANGER: CRUSHING', (-3.0, 2.2, 10.6), 0.42, m=m, col='yellow')
        # EXIT chute (down to the poop)
        box('LVHole', (3.4, 3.4, 0.05), (7.0, 2.0, 0.02), m['rubber'])
        for s in (-1, 1):
            box('LVHoleRim', (3.8, 0.3, 0.3), (7.0, 2.0 + s * 1.85, 0.15), m['yellow'])
            box('LVHoleRim2', (0.3, 3.8, 0.3), (7.0 + s * 1.85, 2.0, 0.15), m['yellow'])
        sl = box('LVSlide', (5.0, 3.0, 0.2), (7.0, 5.6, 2.0), m['steel'])
        sl.rotation_euler[0] = math.radians(-30)
        sign('LVExit', 'EXIT  (POOP)', (7.0, 9.6, 5.6), 0.6, m=m, col='red')
        box('LVDrums', (1.4, 1.4, 2.0), (10.0, 7.5, 1.0), m['red'])
        box('LVDrums2', (1.4, 1.4, 2.0), (-10.0, 7.5, 1.0), m['steel'])
    return {'root': root, 'piston': piston, 'head': head}


def kidney(origin):
    """Kidney: the filter factory. Blood cells walk over a mesh walkway; water + waste drip through
    into a funnel and the TO BLADDER pipe. Also a NO DRINKS sign and the boss's desk."""
    with SetBuilder('Kidney', origin) as root:
        m = shell('KD', 'KIDNEY FILTER CO.', sun_rot=(50, 0, -112), sign_x=4.5)
        yel = real.mat('PeeLiquid', '#F3D34A', 'plastic', grime=0.0, rough=0.1, emit=0.4)
        mesh = real.mat('KDMesh', '#55697C', 'metal', grime=0.1)
        # raised filter walkway with a grid deck (x -10..6, y 1, z 3)
        box('KDDeckFrame', (16.0, 3.0, 0.3), (-2.0, 1.0, 3.0), m['steel'])
        for i in range(30):
            box('KDGrid', (0.06, 2.6, 0.32), (-9.8 + i * 0.53, 1.0, 3.0), mesh)
        for x in (-9.5, -2.0, 5.5):
            for s in (-1, 1):
                box('KDLeg', (0.25, 0.25, 3.0), (x, 1.0 + s * 1.3, 1.5), m['dark'])
        # filter arch the cells walk through
        for x in (-5.4, -2.6):
            box('KDArchPost', (0.5, 0.5, 6.0), (x, -0.4, 6.0), m['steel'])
            box('KDArchPost', (0.5, 0.5, 6.0), (x, 2.4, 6.0), m['steel'])
        box('KDArchTop', (3.3, 3.3, 0.6), (-4.0, 1.0, 9.1), m['yellow'])
        sign('KDFilter', 'FILTER', (-4.0, -0.75, 9.1), 0.45, m=m, col='yellow')
        # funnel + bladder pipe under the deck
        cone('KDFunnel', 0.4, 2.6, 1.6, (-4.0, 1.0, 1.9), m['steel'])
        tube('KDBladderPipe', [(-4.0, 1.0, 1.1), (-4.0, 1.0, 0.6), (-1.0, 4.0, 0.6), (4.0, 7.0, 0.6),
                               (8.0, 7.0, 0.6)], 0.35, m['steel'])
        sign('KDBladderSign', 'TO BLADDER', (7.0, 9.3, 3.0), 0.5, m=m)
        cylinder('KDTank', 1.6, 4.0, (9.0, 7.0, 2.0), real.glass('KDGlass', '#E5F0F5', 0.2), verts=48)
        cylinder('KDTankFill', 1.5, 2.6, (9.0, 7.0, 1.35), yel, verts=48)
        # NO DRINKS sign on the right wall area + boss desk
        sign('KDNoDrinks', 'NO DRINKS ALLOWED', (5.0, 9.6, 5.4), 0.5, m=m, col='red')
        box('KDDesk', (4.0, 2.0, 0.2), (6.0, -2.0, 2.8), real.mat('KDDeskTop', '#9C7A58', 'wood'))
        for sx in (-1.8, 1.8):
            for sy in (-0.8, 0.8):
                box('KDDeskLeg', (0.15, 0.15, 2.8), (6.0 + sx, -2.0 + sy, 1.4), m['dark'])
        cylinder('KDFlaskBase', 0.4, 0.6, (7.2, -2.0, 3.2), real.glass('KDFlaskGlass', '#FFFFFF', 0.25))
    return {'root': root}


def recycle(origin):
    """Recycling: old blood cells walk into a RECYCLING door under a 2,000,000 / SEC display;
    yellow pigment drips from an outlet pipe into a jar."""
    with SetBuilder('Recycle', origin) as root:
        m = shell('RC', 'SPLEEN  -  RECYCLING', sun_rot=(50, 0, -108))
        yel = real.mat('PigmentGlow', '#FFD43A', 'glow', emit=3.0)
        # door frame on the back wall (x 4, y 9.8)
        box('RCDoorDark', (4.0, 0.1, 6.0), (4.0, 9.85, 3.0), real.mat('RCVoid', '#120E14', 'paint', grime=0))
        for x in (1.85, 6.15):
            box('RCJamb', (0.3, 0.6, 6.3), (x, 9.6, 3.15), m['yellow'])
        box('RCHead', (4.6, 0.6, 0.4), (4.0, 9.6, 6.35), m['yellow'])
        sign('RCDoorSign', 'RECYCLING', (4.0, 9.4, 7.3), 0.55, m=m, col='yellow')
        real.spot((4.0, 6.0, 9.5), (20, 0, 0), 1500, angle=50, hexc='#FFD9A0', radius=0.2)
        # big counter display (left wall side)
        box('RCDisp', (7.0, 0.3, 2.6), (-5.5, 9.5, 11.6), m['dark'])
        cnt = text_obj('RCCount', '2,000,000 / SEC', 0.9, (-5.5, 9.3, 11.25),
                       real.mat('RCLed', '#FF4A3A', 'glow', emit=6.0), extrude=0.02)
        cnt.data.align_x = 'CENTER'
        # outlet pipe + jar (right)
        tube('RCOutPipe', [(12.0, 6.0, 6.0), (9.5, 6.0, 6.0), (9.0, 6.0, 5.5)], 0.4, m['steel'])
        cylinder('RCJar', 1.3, 2.6, (9.0, 6.0, 1.3), real.glass('RCJarGlass', '#F4F8FA', 0.22), verts=48)
        jarfill = cylinder('RCJarFill', 1.2, 0.4, (9.0, 6.0, 0.25), real.mat('RCPee', '#F3D34A', 'plastic',
                                                                             grime=0, rough=0.1, emit=0.6), verts=48)
        sign('RCJarSign', 'PEE COLOR', (9.0, 4.6, 0.9), 0.32, m=m)
        catwalk('RCWalk', -10.0, -4.0, 5.0, 2.5, m)
    return {'root': root, 'jarfill': jarfill, 'pig': yel}
