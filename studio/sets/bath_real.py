"""Set: small home bathroom, real-light look (EP06).

Local layout: x -8..8, y -9..6, floor z=0, ceiling z=12. Cameras look toward +Y.
Toilet against the back wall at TOILET (faces -Y). Sink + mirror on the right of the back wall.
A pee-colour chart poster on the left of the back wall: CHART centre, CHART_SWATCH x positions of the
6 swatches (light -> dark); arrow = returned 'arrow' object (move it along x).
High frosted window on the left wall throws a sun shaft.
"""
import math
import assets
import real
from toon import box, cylinder, text_obj, SetBuilder

M = 7.5 / 3.5
TOILET = (0.0, 4.6)
CHART = (-4.6, 5.9, 6.6)
SWATCH_HEX = ['#FBF6D2', '#F8EC9A', '#F3DB5E', '#E8C030', '#D9A21C', '#B97A12']
CHART_SWATCH = [CHART[0] - 2.0 + i * 0.8 for i in range(6)]


def build(origin=(0, 0, 0)):
    with SetBuilder('Bath', origin) as root:
        tile = real.mat('BTile', '#E4ECEF', 'tile', mode='wall', size=(0.8, 0.8), line='#AFBCC2', grime=0.12)
        tilex = real.mat('BTileX', '#E4ECEF', 'tile', mode='wallx', size=(0.8, 0.8), line='#AFBCC2', grime=0.12)
        upper = real.mat('BUpper', '#7FA2B5', 'paint', mode='wall', grime=0.15)
        upperx = real.mat('BUpperX', '#7FA2B5', 'paint', mode='wallx', grime=0.15)
        floor = real.mat('BFloor', '#5E6E7A', 'tile', mode='floor', size=(0.9, 0.9), line='#3E4A54', grime=0.3)
        ceil = real.mat('BCeil', '#EEF2F2', 'paint', grime=0.1)
        trim = real.mat('BTrim', '#FAFAF7', 'paint', grime=0.05)
        sky = real.mat('BSky', '#F2F8FF', 'glow', emit=4.0)
        frost = real.glass('BFrost', '#E9F2F8', 0.55)
        poster = real.mat('BPoster', '#FFFDF6', 'paint', grime=0.05)
        ink = real.mat('BInk', '#25303D', 'paint', grime=0.0)
        water = real.mat('BToiletWater', '#F6EFB0', 'plastic', grime=0.0, rough=0.05)

        box('BFloorOb', (16.4, 15.4, 0.2), (0, -1.5, -0.1), floor)
        box('BCeilOb', (16.4, 15.4, 0.2), (0, -1.5, 12.1), ceil)
        box('BBack', (16.4, 0.4, 5.0), (0, 6.2, 2.5), tile)
        box('BBackUp', (16.4, 0.4, 7.4), (0, 6.2, 8.7), upper)
        box('BRight', (0.4, 15.4, 5.0), (8.2, -1.5, 2.5), tilex)
        box('BRightUp', (0.4, 15.4, 7.4), (8.2, -1.5, 8.7), upperx)
        # left wall with a high window (y -1..3, z 8..11)
        box('BLeft', (0.4, 15.4, 8.0), (-8.2, -1.5, 4.0), tilex if False else upperx)
        box('BLeftTile', (0.1, 15.4, 5.0), (-7.97, -1.5, 2.5), tilex)
        box('BLeftTop', (0.4, 15.4, 1.0), (-8.2, -1.5, 11.5), upperx)
        box('BLeftA', (0.4, 7.0, 3.0), (-8.2, -5.5, 9.5), upperx)
        box('BLeftB', (0.4, 4.2, 3.0), (-8.2, 4.1, 9.5), upperx)
        box('BWinPane', (0.05, 4.0, 3.0), (-8.25, 1.0, 9.5), frost).visible_shadow = False
        box('BWinBar', (0.15, 0.15, 3.0), (-8.1, 1.0, 9.5), trim)
        sk = box('BSkyCard', (0.2, 40, 30), (-20, 0, 10), sky)
        sk.visible_shadow = False
        box('BTileCap', (16.0, 0.25, 0.2), (0, 5.95, 5.0), trim)
        # fixtures
        assets.load('furniture-kit', 'toilet', loc=(TOILET[0], TOILET[1], 0), scale=M, rot=(0, 0, 180), center=True)
        wt = cylinder('BWater', 0.62, 0.02, (TOILET[0], TOILET[1] - 0.1, 1.15), water, verts=32)
        wt.scale = (1.0, 1.25, 1.0)
        assets.load('furniture-kit', 'bathroomSink', loc=(5.0, 5.3, 0), scale=M, rot=(0, 0, 180), center=True)
        assets.load('furniture-kit', 'bathroomMirror', loc=(5.0, 5.9, 5.6), scale=M, rot=(0, 0, 180), center=True)
        assets.load('furniture-kit', 'bathroomCabinetDrawer', loc=(-7.0, -3.0, 0), scale=M, rot=(0, 0, -90),
                    center=True)
        cylinder('BRollHolder', 0.08, 0.6, (1.8, 5.8, 3.0), trim, rot=(0, 90, 0))
        cylinder('BRoll', 0.32, 0.45, (1.8, 5.65, 3.0), trim, rot=(0, 90, 0))
        # pee colour chart poster
        cx, cy, cz = CHART
        box('BPosterOb', (5.6, 0.08, 4.6), (cx, cy, cz), poster)
        box('BPosterFrame', (5.8, 0.06, 4.8), (cx, cy + 0.03, cz), ink)
        t = text_obj('BPosterTitle', 'PEE COLOR CHART', 0.42, (cx, cy - 0.06, cz + 1.4), ink, extrude=0.01)
        t.data.align_x = 'CENTER'
        for i, (x, h) in enumerate(zip(CHART_SWATCH, SWATCH_HEX)):
            box(f'BSwatch{i}', (0.7, 0.05, 1.8), (x, cy - 0.06, cz - 0.1), real.mat(f'BSw{i}', h, 'paint', grime=0))
        for txt, x in (('GOOD', cx - 1.6), ('DRINK WATER!', cx + 1.2)):
            tt = text_obj('BPosterLbl', txt, 0.28, (x, cy - 0.06, cz - 1.55), ink, extrude=0.01)
            tt.data.align_x = 'CENTER'
        arrow = box('BArrow', (0.25, 0.1, 0.55), (CHART_SWATCH[2], cy - 0.12, cz + 0.95),
                    real.mat('BArrowM', '#E53935', 'paint', grime=0))
        arrow.rotation_euler[1] = math.radians(45)
        # light
        real.sun((48, 0, -100), strength=10.0, hexc='#FFEACC', angle=1.2, name='BSun')
        real.area((0, -12, 8), (75, 0, 0), 14, 700, '#DCE8F6', shadow=False, name='BFront', volume=0.0)
        real.area((0, 0, 11.8), (0, 0, 0), 5, 350, '#FFF6EA', shadow=False, name='BCeilLamp', volume=0.0)
        box('BCeilLampOb', (2.5, 2.5, 0.12), (0, 0, 11.95), real.mat('BLampGlow', '#FFFFFF', 'glow', emit=6.0))
        real.shafts((0, -1.5, 6.0), (16, 15, 12), density=0.01, name='BHaze')
    return {'root': root, 'arrow': arrow, 'water': wt}
