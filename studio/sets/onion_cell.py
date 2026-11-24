"""Set: inside an onion (EP08), real-light look.

Local layout: x -9..9, y -8..8, floor z=0. Cameras look toward +Y.
Two 'rooms' side by side (a cutaway, open toward the camera): LEFT room x -6.5..-0.3 (warm butter flesh), RIGHT room
x 0.3..6.5 (lilac flesh), depth y 0..5, height 5. The separating wall (returned as 'wall') sits at x -0.3..0.3; build.py
hides it when the knife breaks it. Behind and around: curved onion layers (cream -> pink -> purple skin), soft light
coming through the translucent layers from the upper left, plus haze.
"""
import math
import real
from toon import box, cylinder, SetBuilder

ROOM_H = 5.0


def build(origin=(0, 0, 0)):
    with SetBuilder('OnionCell', origin) as root:
        floor = real.mat('OCFloor', '#E9BFA6', 'flesh', grime=0.15)
        butter = real.mat('OCButter', '#F2C95E', 'flesh', grime=0.12)
        lilac = real.mat('OCLilac', '#B79AE0', 'flesh', grime=0.12)
        mid = real.mat('OCMid', '#E8C2A8', 'flesh', grime=0.18)
        box('OCFloorOb', (40, 40, 0.2), (0, 0, -0.1), floor)
        for x0, x1, m in ((-6.5, -0.3, butter), (0.3, 6.5, lilac)):
            cx, w = (x0 + x1) / 2, x1 - x0
            box('OCRoomFloor', (w, 5.2, 0.15), (cx, 2.5, 0.075), m)
            box('OCRoomBack', (w + 0.6, 0.4, ROOM_H), (cx, 5.2, ROOM_H / 2), m)
            box('OCRoomTop', (w + 0.6, 5.6, 0.35), (cx, 2.5, ROOM_H + 0.17), m)
            ox = x0 - 0.2 if x0 < 0 else x1 + 0.2
            box('OCRoomSide', (0.4, 5.6, ROOM_H), (ox, 2.5, ROOM_H / 2), m)
        wall = box('OCWall', (0.6, 5.2, ROOM_H), (0, 2.5, ROOM_H / 2), mid)
        # curved onion layers around everything (open toward the camera)
        for i, c in enumerate(('#F7E6EC', '#EDC3D6', '#D998BC', '#B4527C')):
            r = 11 + i * 2.2
            cyl = cylinder(f'OCLayer{i}', r, 30, (0, -2, 8), real.mat(f'OCLayer{i}M', c, 'flesh', grime=0.1), verts=96)
            # keep only the back half: scale the front away by flattening it behind the camera (cheap: rotate a half)
            cyl.scale = (1, 1, 1)
            cyl.visible_shadow = False
        # light through the layers
        real.sun((52, 0, -125), strength=9.0, hexc='#FFE6C8', angle=1.5, name='OCSun')
        real.area((0, -14, 7), (75, 0, 0), 18, 500, '#FFE8F0', shadow=False, name='OCFront', volume=0.0)
        real.area((0, 2.5, ROOM_H - 0.4), (0, 0, 0), 10, 180, '#FFF2E0', shadow=False, name='OCRoomLight', volume=0.0)
        real.shafts((0, 0, 6), (30, 30, 14), density=0.004, hexc='#FFE7F0', name='OCHaze')
    return {'root': root, 'wall': wall}
