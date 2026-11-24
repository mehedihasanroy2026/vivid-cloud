"""Set: apartment block at night, seen from across the street. 3 x 2 windows, each a tiny
lit bedroom where somebody jerks awake.

Local layout: facade in the plane y=0 (faces -Y), x -9..9, ground z=0.
WINDOWS: list of window centres (x, z). Sleeper for window i stands at (x, ROOM_Y, z - 3.6).
Returns per-window lights (key energy 0 -> on) and glass panes.
"""
import math
import random
from toon import toon, glassy, box, ellipsoid, cylinder, tube, point_light, area_light, SetBuilder, text_obj

COLS = (-6.0, 0.0, 6.0)
ROWS = (5.0, 12.0)
WINDOWS = [(x, z) for z in ROWS for x in COLS]
WIN_W, WIN_H = 4.2, 4.6
ROOM_Y = 2.6


def build(origin=(0, 0, 0)):
    rnd = random.Random(5)
    with SetBuilder('Apartment', origin) as root:
        brick = toon('AptBrick', '#8C4F55', tex=('brick', '#4A2A33', 0.9, 0.4, 'wall'))
        trim = toon('AptTrim', '#D8CDBB')
        dark = toon('AptDark', '#2C2440')
        side = toon('AptSide', '#5B4A6E', tex=('brick', '#3A2E4A', 0.9, 0.4, 'wall'))
        walk = toon('AptWalk', '#6E6A86', tex=('tiles', '#4D4966', 1.6))
        road = toon('AptRoad', '#34304A')
        sky = toon('AptSky', '#262055', emit=True)
        star = toon('AptStar', '#FFF6D8', emit=True)
        moon = toon('AptMoon', '#FFF1B8', emit=True)

        # sky card behind everything + moon + stars
        box('AptSkyCard', (90, 0.2, 60), (0, 30, 20), sky)
        cylinder('AptMoonDisc', 2.4, 0.1, (10, 29, 22), moon, rot=(90, 0, 0))
        for i in range(60):
            ellipsoid('AptStarDot', (0.09, 0.09, 0.09), (rnd.uniform(-40, 40), 29.5, rnd.uniform(8, 45)), star, segs=6, rings=3)

        # facade built from strips around the window holes
        W, H = 19.0, 17.0
        xs = sorted({-W / 2, W / 2} | {x - WIN_W / 2 for x in COLS} | {x + WIN_W / 2 for x in COLS})
        zs = sorted({0.0, H} | {z - WIN_H / 2 for z in ROWS} | {z + WIN_H / 2 for z in ROWS})
        for i in range(len(xs) - 1):
            for j in range(len(zs) - 1):
                cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
                if any(abs(cx - x) < 0.01 and abs(cz - z) < 0.01 for x, z in WINDOWS):
                    continue
                box('AptWall', (xs[i + 1] - xs[i], 0.6, zs[j + 1] - zs[j]), (cx, 0, cz), brick)
        box('AptRoof', (W + 0.8, 1.4, 0.7), (0, 0, H + 0.35), trim)
        box('AptBase', (W + 0.4, 1.0, 1.2), (0, -0.2, 0.6), trim)
        for sx in (-1, 1):       # neighbouring buildings peeking in at the sides
            box('AptNeighbour', (8, 6, 13 + 4 * (sx > 0)), (sx * 14.5, 2, 6.5 + 2 * (sx > 0)), side)
            for k in range(3):
                box('AptNWin', (1.4, 0.1, 1.8), (sx * (11.5 + 2.6 * k), -1.05, 9.5), toon('AptNWinGlow', '#F6C76A', emit=True))
        box('AptSidewalk', (60, 6, 0.3), (0, -3.5, 0.15), walk)
        box('AptRoad', (60, 14, 0.2), (0, -13, 0.0), road)

        # windows: frame, sill, cross bars, little room behind with headboard + lamp
        glass = glassy('AptGlass', '#BFD8FF', alpha=0.12)
        lights, rooms = [], []
        wallcols = ['#E9B872', '#9CC8E8', '#E8A0B4', '#A8D8A0', '#C9B0E8', '#F2D16B']
        for k, (x, z) in enumerate(WINDOWS):
            box('AptSill', (WIN_W + 0.6, 0.9, 0.25), (x, -0.4, z - WIN_H / 2 - 0.1), trim)
            box('AptLintel', (WIN_W + 0.4, 0.8, 0.3), (x, -0.3, z + WIN_H / 2 + 0.15), trim)
            for dx in (-WIN_W / 2, WIN_W / 2):
                box('AptJamb', (0.2, 0.7, WIN_H), (x + dx, -0.1, z), trim)
            box('AptBarV', (0.12, 0.12, WIN_H), (x, -0.2, z), trim)
            box('AptBarH', (WIN_W, 0.12, 0.12), (x, -0.2, z + 0.6), trim)
            box('AptPane', (WIN_W, 0.04, WIN_H), (x, -0.15, z), glass)
            wc = toon(f'AptRoomWall{k}', wallcols[k], tex=('stripes', wallcols[k], 0.4, 'x'))
            fl = toon('AptRoomFloor', '#7A5A44')
            box('AptRoomBack', (WIN_W + 2, 0.2, WIN_H + 2), (x, 5.0, z), wc)
            box('AptRoomFloorOb', (WIN_W + 2, 5.2, 0.2), (x, 2.5, z - WIN_H / 2 - 0.2), fl)
            box('AptRoomCeil', (WIN_W + 2, 5.2, 0.2), (x, 2.5, z + WIN_H / 2 + 0.6), dark)
            for dx in (-(WIN_W / 2 + 1), WIN_W / 2 + 1):
                box('AptRoomSide', (0.2, 5.2, WIN_H + 2), (x + dx, 2.5, z), wc)
            box('AptHeadboard', (2.6, 0.2, 2.2), (x, 4.7, z - WIN_H / 2 + 0.9), toon('AptHB', '#6B4A33'))
            box('AptQuilt', (2.8, 3.0, 0.5), (x, 3.3, z - WIN_H / 2 + 0.1), toon(f'AptQuilt{k}', rnd.choice(
                ('#C94F4F', '#4F8FC9', '#6DB36B', '#E8A33D', '#8E5BB5'))))
            li = point_light((x - 1.2, 2.4, z + 1.0), 0, '#FFC27A', 0.4, f'AptLamp{k}')
            lights.append(li)
        # street: lamp + warm pools, front fill
        metal = toon('AptMetal', '#2E2A40')
        cylinder('AptStreetPost', 0.16, 9, (-9.5, -4.8, 4.5), metal, outline=0.02)
        ellipsoid('AptStreetBulb', (0.6, 0.6, 0.35), (-8.6, -4.8, 9.0), toon('AptBulb', '#FFE6A0', emit=True), outline=0.02)
        tube('AptStreetArm', [(-9.5, -4.8, 9.0), (-8.6, -4.8, 9.3)], 0.09, metal)
        point_light((-8.6, -5.2, 8.3), 1200, '#FFC27A', 0.5, 'AptStreetLight')
        area_light((0, -30, 10), (78, 0, 0), 16, 2600, '#8C86D8', 'AptFront')
    return {'root': root, 'lights': lights, 'origin': origin}
