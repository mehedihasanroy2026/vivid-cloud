"""Set: bathroom with a walk-in shower, sink, mirror, towel rail.

Local layout: room x -5..5, y -9..4, floor z=0, ceiling z=9.
Shower spot (water hits here): SHOWER = (-2.2, 2.4).  Knob on back wall at KNOB.
Returns handles to animate: water stream object, knob lever, lights.
"""
import math
from toon import (toon, glassy, water_mat, box, ellipsoid, cylinder, cone, tube, area_light,
                  point_light, SetBuilder)

SHOWER = (-2.2, 2.4)
HEAD_Z = 7.3
KNOB = (-0.6, 3.82, 3.7)


def build(origin=(0, 0, 0)):
    with SetBuilder('Bathroom', origin) as root:
        wall = toon('BathTiles', '#9FD8EA', tex=('tiles', '#E6F6FB', 0.75, 'wall'))
        wall_low = toon('BathTilesLow', '#5FB3D1', tex=('tiles', '#D6EEF6', 0.75, 'wall'))
        floor = toon('BathFloor', '#E7ECF1', tex=('tiles', '#B4C0CB', 0.9))
        ceil = toon('BathCeil', '#F4F6F8')
        white = toon('Porcelain', '#F7F9FB', rough=0.35)
        chrome = toon('Chrome', '#C3CCD6', rough=0.25)
        ink = toon('Ink', '#2A2230')
        curtain = toon('Curtain', '#F5C342')
        mat = toon('BathMat', '#5EC4A6')
        towel = toon('TowelPink', '#F28CA6')
        mirror = glassy('Mirror', '#D8F1FF', alpha=1.0, emit_strength=0.25)
        red = toon('HotRed', '#E5483B')
        blue = toon('ColdBlue', '#3C8DEB')
        duck = toon('Duck', '#FFD43B')
        orange = toon('Beak', '#FF8A1F')
        bottle_cols = [toon('Shampoo', '#7C5CE0'), toon('Soap', '#3CC4B4'), toon('Gel', '#FF7A59')]

        # shell: tiled walls with a darker band at the bottom
        box('Floor', (10.4, 13.4, 0.2), (0, -2.5, -0.1), floor)
        box('Ceil', (10.4, 13.4, 0.2), (0, -2.5, 9.1), ceil)
        box('BackWall', (10.4, 0.3, 9.4), (0, 4.15, 4.6), wall)
        box('LeftWall', (0.3, 13.4, 9.4), (-5.15, -2.5, 4.6), wall)
        box('RightWall', (0.3, 13.4, 9.4), (5.15, -2.5, 4.6), wall)
        box('BackBand', (10.4, 0.05, 2.2), (0, 3.98, 1.1), wall_low)
        box('LeftBand', (0.05, 13.4, 2.2), (-4.98, -2.5, 1.1), wall_low)
        box('RightBand', (0.05, 13.4, 2.2), (4.98, -2.5, 1.1), wall_low)

        # shower: tray, pipe, head, knob
        sx, sy = SHOWER
        box('Tray', (3.4, 2.8, 0.22), (sx, sy + 0.2, 0.11), white)
        cylinder('Drain', 0.18, 0.04, (sx, sy, 0.23), chrome)
        tube('Pipe', [(sx, 3.95, 5.2), (sx, 3.95, 7.6), (sx, 3.6, 7.85), (sx, 3.0, 7.75)], 0.07, chrome)
        head = cone('ShowerHead', 0.5, 0.18, 0.35, (sx, sy + 0.25, HEAD_Z + 0.2), chrome, outline=0.025)
        head.rotation_euler = (math.radians(-15), 0, 0)
        kx, ky, kz = KNOB
        cylinder('KnobBase', 0.32, 0.1, (kx, ky, kz), chrome, rot=(90, 0, 0), outline=0.02)
        lever = box('KnobLever', (0.12, 0.1, 0.6), (kx, ky - 0.12, kz), chrome)
        ellipsoid('HotDot', (0.07, 0.03, 0.07), (kx - 0.45, ky - 0.02, kz + 0.2), red)
        ellipsoid('ColdDot', (0.07, 0.03, 0.07), (kx + 0.45, ky - 0.02, kz + 0.2), blue)
        # shampoo shelf
        box('Shelf', (1.4, 0.4, 0.08), (sx - 0.9, 3.8, 4.4), white)
        for i, c in enumerate(bottle_cols):
            cylinder(f'Bottle{i}', 0.13, 0.55 - 0.1 * i, (sx - 1.35 + 0.42 * i, 3.75, 4.72 - 0.05 * i), c, outline=0.015)

        # curtain bunched open on the left, rod across the front of the shower
        tube('Rod', [(-5.0, 1.0, 8.3), (0.2, 1.0, 8.3)], 0.05, chrome)
        for i in range(6):
            ellipsoid(f'Pleat{i}', (0.22, 0.14, 4.0), (-4.75 + 0.3 * i, 1.0 + 0.06 * (i % 2), 4.2), curtain, outline=0.025)

        # falling water (hidden until the knob turns)
        wm = water_mat()
        water = cone('Water', 1.05, 0.3, HEAD_Z - 0.25, (sx, sy, (HEAD_Z - 0.25) / 2 + 0.22), wm, caps=False, verts=32)
        water2 = cone('Water2', 0.75, 0.2, HEAD_Z - 0.25, (sx, sy, (HEAD_Z - 0.25) / 2 + 0.22), wm, caps=False, verts=32)
        water2.rotation_euler = (0, 0, 1.3)

        # sink, mirror, towel rail
        cylinder('SinkStand', 0.25, 2.4, (2.9, 3.4, 1.2), white, outline=0.025)
        ellipsoid('Sink', (0.9, 0.6, 0.35), (2.9, 3.3, 2.55), white, outline=0.03)
        tube('Tap', [(2.9, 3.85, 2.8), (2.9, 3.85, 3.2), (2.9, 3.45, 3.25)], 0.05, chrome)
        box('MirrorFrame', (1.9, 0.12, 2.4), (2.9, 3.95, 5.1), white)
        box('MirrorGlass', (1.6, 0.06, 2.1), (2.9, 3.88, 5.1), mirror)
        tube('TowelRail', [(4.95, 0.2, 4.8), (4.7, 0.2, 4.8), (4.7, 2.2, 4.8), (4.95, 2.2, 4.8)], 0.04, chrome)
        box('TowelHung', (0.12, 1.6, 1.8), (4.72, 1.2, 3.95), towel)
        # bath mat + rubber duck on the shelf
        box('BathMat', (2.4, 1.6, 0.05), (sx, 0.3, 0.03), mat)
        ellipsoid('DuckBody', (0.22, 0.28, 0.17), (sx + 0.7, 3.8, 4.62), duck, outline=0.015)
        ellipsoid('DuckHead', (0.13, 0.13, 0.13), (sx + 0.7, 3.65, 4.86), duck, outline=0.015)
        cone('DuckBeak', 0.06, 0.0, 0.14, (sx + 0.7, 3.5, 4.84), orange, rot=(90, 0, 0))

        # light
        area_light((0, -1.5, 8.9), (0, 0, 0), 5.5, 850, '#FFF6EA', 'BathCeiling')
        area_light((0.5, -9.5, 5.5), (78, 0, 0), 6.0, 600, '#FFFFFF', 'BathFront')
        point_light((sx, sy, 6.4), 120, '#D8F0FF', 0.6, 'ShowerGlow')
    return {'root': root, 'water': [water, water2], 'lever': lever, 'origin': origin}
