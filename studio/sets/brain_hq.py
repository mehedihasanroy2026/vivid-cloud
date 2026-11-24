"""Sets: inside the brain (EP07), real-light look. Built on body_plant.shell (same hall: x -12..12,
y -12..10, ceiling 16, cameras look toward +Y).

motor()   MOTOR DEPT.: control desk with a big MOVE lever + screens, a photocopier that makes the
          'copy of the plan', and a glass pneumatic tube that rises from the copier and shoots off
          through the right wall (TUBE_PATH, local points).
predict() PREDICTION DEPT. (the cerebellum, 'back of the head'): a cosy lilac back office. The tube comes
          in through the left wall and drops into an in-tray on the desk. A big TICKLE dial on the back
          wall (needle pivot spins about local Y), alarm beacons on the walls, filing cabinets.
"""
import math
import real
from toon import box, cylinder, ellipsoid, tube, text_obj, empty, SetBuilder
import body_plant as bp

TUBE_PATH = [(-6.0, 3.0, 3.6), (-6.0, 3.0, 11.0), (-5.0, 3.0, 12.0), (12.5, 3.0, 12.0)]
PD_TUBE = [(-12.5, 1.0, 10.5), (-2.6, 1.0, 10.5), (-1.6, 1.0, 9.5), (-1.6, 1.0, 3.8)]
DIAL = (6.0, 9.75, 7.0)
DESK_TOP = 2.95


def _glass_tube(name, pts, r, m):
    g = real.glass(f'{name}Glass', '#DDF1FA', 0.22)
    tube(f'{name}Tube', pts, r, g)
    for p in (pts[0], pts[-1]):
        cylinder(f'{name}Collar', r + 0.12, 0.35, p, m['steel'],
                 rot=(0, 90, 0) if abs(pts[-1][0] - pts[-2][0]) > 0.1 and p is pts[-1] else None)


def motor(origin):
    with SetBuilder('Motor', origin) as root:
        m = bp.shell('MT', 'MOTOR DEPT.', sun_rot=(50, 0, -112), sign_x=3.0)
        screen = real.mat('MTScreen', '#2C7BC4', 'glow', emit=2.2)
        white = real.mat('MTWhite', '#F4F7FA', 'glow', emit=3.0)
        cream = real.mat('MTCream', '#E9E4D8', 'plastic', grime=0.1, rough=0.4)
        # control desk (front face toward -Y) with a sloped panel
        box('MTDesk', (7.0, 2.4, 2.8), (2.5, 2.0, 1.4), m['dark'])
        p = box('MTPanel', (7.0, 1.8, 0.25), (2.5, 1.7, 3.0), m['steel'])
        p.rotation_euler[0] = math.radians(-18)
        for i, c in enumerate(('red', 'yellow', 'lamp', 'red', 'yellow')):
            cylinder('MTBtn', 0.2, 0.15, (0.0 + i * 0.7, 1.3, 3.2), m[c])
        # the big lever: pivot empty, rotates about X (0 = up/back, +50 = pulled toward camera)
        lev = empty('MTLeverPivot', (4.6, 1.8, 3.2))
        cylinder('MTLeverBase', 0.45, 0.3, (0, 0, 0), m['dark'], parent=lev)
        cylinder('MTLeverStick', 0.09, 2.2, (0, 0, 1.1), m['steel'], parent=lev)
        ellipsoid('MTLeverKnob', (0.32, 0.32, 0.32), (0, 0, 2.3), m['red'], parent=lev)
        lev.rotation_euler[0] = math.radians(-25)
        bp.sign('MTLeverSign', 'MOVE', (4.6, 0.75, 2.3), 0.35, m=m, col='yellow')
        # screens on a stand behind the desk
        for i, x in enumerate((0.0, 2.5, 5.0)):
            box('MTScreenFrame', (2.3, 0.3, 1.6), (x, 3.6, 5.4), m['dark'])
            box('MTScreenOb', (2.0, 0.1, 1.3), (x, 3.42, 5.4), screen)
            # a little stick-arm diagram on each screen
            tube('MTArmIcon', [(x - 0.6, 3.36, 5.0), (x, 3.36, 5.5), (x + 0.6, 3.36, 5.3)], 0.06, white)
            cylinder('MTPole', 0.1, 1.8, (x, 3.6, 3.7), m['dark'])
        # photocopier (paper slides out of the front slot toward -Y)
        box('MTCopier', (3.0, 2.4, 3.0), (-6.0, 3.0, 1.5), cream)
        box('MTCopierLid', (3.1, 2.5, 0.25), (-6.0, 3.0, 3.1), m['dark'])
        box('MTCopierTray', (1.6, 1.0, 0.1), (-6.0, 1.4, 2.0), cream)
        box('MTCopierSlot', (1.7, 0.1, 0.2), (-6.0, 1.78, 2.2), m['dark'])
        box('MTCopierLight', (1.8, 0.05, 0.15), (-6.0, 1.77, 2.6), real.mat('MTGreen', '#5BE37A', 'glow', emit=3.0))
        bp.sign('MTCopySign', 'COPY', (-6.0, 1.75, 5.3), 0.5, m=m)
        # the pneumatic tube from the copier, up and out through the right wall
        _glass_tube('MT', TUBE_PATH, 0.55, m)
        bp.sign('MTTubeSign', 'TO: BACK OF HEAD  >>', (4.0, 2.2, 13.6), 0.42, m=m, col='yellow')
        # extra dressing: lockers + a water cooler
        for i in range(4):
            box('MTLocker', (1.2, 1.0, 4.5), (8.0 + i * 1.25, 8.9, 2.25), real.mat('MTLock', '#5C7FA3', 'metal',
                                                                               grime=0.25))
        cylinder('MTCooler', 0.6, 2.6, (-10.0, 7.0, 1.3), cream)
        cylinder('MTCoolerBottle', 0.55, 1.4, (-10.0, 7.0, 3.3), real.glass('MTWater', '#7EC8F2', 0.5))
    return {'root': root, 'lever': lev, 'path': TUBE_PATH}


def predict(origin):
    with SetBuilder('Predict', origin) as root:
        lilac = {'wall': real.mat('PDWall', '#B7A4D8', 'brick', mode='wall', size=(1.2, 0.6), grime=0.2),
                 'wallx': real.mat('PDWallX', '#B7A4D8', 'brick', mode='wallx', size=(1.2, 0.6), grime=0.2),
                 'lower': real.mat('PDLower', '#5E5577', 'paint', mode='wall', grime=0.25)}
        m = bp.shell('PD', 'PREDICTION DEPT.', sun_rot=(52, 0, -108), sun_power=10.0, sign_x=-3.5,
                     sign_size=1.0, sign_w=12.0, mats=lilac)
        wood = real.mat('PDWood', '#8A5E3C', 'wood', grime=0.15)
        paper = real.mat('PDPaper', '#F7F5EE', 'paint', grime=0.05)
        face = real.mat('PDDialFace', '#F6F1E4', 'paint', grime=0.08)
        green = real.mat('PDGreen', '#3FAF5B', 'paint', grime=0)
        orange = real.mat('PDOrange', '#F2A33A', 'paint', grime=0)
        red = real.mat('PDRed', '#E53935', 'paint', grime=0)
        # desk with in-tray, stamp pad, mug, desk lamp
        box('PDDesk', (6.0, 2.6, 0.2), (0.5, 1.0, DESK_TOP - 0.1), wood)
        for x in (-2.3, 3.3):
            box('PDDeskLeg', (0.25, 2.2, DESK_TOP - 0.2), (x, 1.0, (DESK_TOP - 0.2) / 2), m['dark'])
        box('PDDeskFront', (5.8, 0.1, 1.6), (0.5, -0.25, DESK_TOP - 1.0), wood)
        box('PDTray', (1.6, 1.2, 0.3), (-1.6, 1.0, DESK_TOP + 0.15), m['steel'])
        box('PDTrayIn', (1.4, 1.0, 0.1), (-1.6, 1.0, DESK_TOP + 0.12), paper)
        bp.sign('PDTraySign', 'IN', (-1.6, 0.35, DESK_TOP + 0.35), 0.22, m=m, col='yellow')
        box('PDInkPad', (0.9, 0.6, 0.1), (2.6, 0.8, DESK_TOP + 0.05), real.mat('PDInk', '#B71C1C', 'fabric'))
        cylinder('PDMug', 0.25, 0.5, (1.6, 1.6, DESK_TOP + 0.25), real.mat('PDMugM', '#2F7DD1', 'plastic', grime=0))
        cylinder('PDLampBase', 0.35, 0.1, (3.0, 1.8, DESK_TOP + 0.05), m['dark'])
        tube('PDLampArm', [(3.0, 1.8, DESK_TOP), (3.0, 1.9, DESK_TOP + 1.4), (2.3, 1.5, DESK_TOP + 1.8)], 0.06, m['dark'])
        cylinder('PDLampHead', 0.4, 0.4, (2.2, 1.45, DESK_TOP + 1.65), m['dark'])
        real.spot((2.2, 1.4, DESK_TOP + 1.5), (0, 0, 0), 300, angle=80, hexc='#FFD9A0', blend=0.7, radius=0.2,
                  volume=0.3, name='PDDeskLamp')
        # pneumatic tube from the left wall into the in-tray
        _glass_tube('PD', PD_TUBE, 0.55, m)
        # big TICKLE dial on the back wall: face plate, coloured arc (green -> red), ticks, labels, needle
        dx, dy, dz = DIAL
        cylinder('PDDialRim', 2.7, 0.3, (dx, dy, dz), m['dark'], rot=(90, 0, 0), verts=64)
        cylinder('PDDialFaceOb', 2.45, 0.32, (dx, dy - 0.02, dz), face, rot=(90, 0, 0), verts=64)
        for i in range(11):
            a = math.radians(-120 + i * 24)          # -120 (0) ... +120 (MAX), 0 = straight up
            col = green if i < 4 else (orange if i < 8 else red)
            t = box('PDTick', (0.5, 0.06, 0.18), (dx + 1.85 * math.sin(a), dy - 0.2, dz + 1.85 * math.cos(a)), col)
            t.rotation_euler[1] = -a + math.pi / 2
        for txt, a in (('0', -120), ('MAX', 120)):
            r = math.radians(a)
            lb = text_obj('PDDialLbl', txt, 0.45, (dx + 1.3 * math.sin(r), dy - 0.22, dz + 1.3 * math.cos(r) - 0.2),
                          m['ink'], extrude=0.01)
            lb.data.align_x = 'CENTER'
        lb = text_obj('PDDialTitle', 'TICKLE', 0.55, (dx, dy - 0.22, dz - 1.4), m['ink'], extrude=0.01)
        lb.data.align_x = 'CENTER'
        needle = empty('PDNeedlePivot', (dx, dy - 0.3, dz))
        box('PDNeedle', (0.14, 0.06, 2.0), (0, 0, 0.9), red, parent=needle)
        cylinder('PDNeedleHub', 0.25, 0.12, (0, 0, 0), m['dark'], parent=needle, rot=(90, 0, 0))
        needle.rotation_euler[1] = math.radians(100)        # starts near MAX (local Y spins in the dial plane)
        # crank wheel under the dial (the worker turns it)
        crank = empty('PDCrank', (dx, dy - 0.4, 3.4))
        cylinder('PDCrankWheel', 0.9, 0.2, (0, 0, 0), m['red'], parent=crank, rot=(90, 0, 0), verts=32)
        for k in range(3):
            sp = box('PDCrankSpoke', (1.7, 0.1, 0.12), (0, -0.1, 0), m['dark'], parent=crank)
            sp.rotation_euler[1] = math.radians(k * 60)
        box('PDCrankPost', (0.3, 0.3, 2.0), (dx, dy - 0.1, 2.4), m['dark'])
        # alarm beacons (dark until build.py lights them)
        beacons = []
        for i, (x, y, z) in enumerate(((-10.0, 9.4, 12.0), (-1.0, 9.4, 13.0), (10.0, 9.4, 12.0), (11.4, -4.0, 11.0))):
            box('PDBeaconBase', (0.8, 0.5, 0.3), (x, y + 0.3, z - 0.5), m['dark'])
            beacons.append(ellipsoid(f'PDBeacon{i}', (0.5, 0.5, 0.6), (x, y, z), real.mat('PDBeaconOff', '#7A2020',
                                                                                          'plastic', grime=0, rough=0.2)))
        # filing cabinets on the right wall + shelf of binders
        for i in range(4):
            y = -6.0 + i * 1.9
            box('PDCab', (1.6, 1.7, 4.2), (11.0, y, 2.1), real.mat('PDCabM', '#7D8A99', 'metal', grime=0.2))
            for z in (0.9, 2.1, 3.3):
                box('PDCabHandle', (0.1, 0.6, 0.12), (10.15, y, z), m['steel'])
        bp.sign('PDCabSign', 'EXPECTED', (10.1, -3.0, 5.0), 0.45, rot=90, m=m, col='yellow')
        box('PDShelf', (6.0, 1.0, 0.2), (-7.5, 9.4, 5.5), wood)
        for i in range(14):
            c = ('#3F6E9A', '#C8102E', '#F2C230', '#4E9A3A')[i % 4]
            box('PDBinder', (0.32, 0.8, 1.3), (-10.0 + i * 0.4, 9.4, 6.25), real.mat(f'PDBind{c}', c, 'plastic',
                                                                                     grime=0.1))
        bp.sign('PDShelfSign', 'PREDICTIONS', (-7.5, 8.85, 7.6), 0.35, m=m)
        bp.sign('PDBack', 'BACK OF THE HEAD', (-6.5, 9.6, 3.4), 0.32, m=m, col='yellow')
    return {'root': root, 'needle': needle, 'crank': crank, 'beacons': beacons, 'path': PD_TUBE}
