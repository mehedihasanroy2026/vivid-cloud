"""Set: classroom in golden late-afternoon light (EP05). Pro-look standard + Kenney props.

Local layout: room x -9..9, y -11..6, floor z=0, ceiling z=10. Cameras look toward +Y.
Students sit facing -Y (toward the camera); the chalkboard wall is the open front (behind camera).
Left wall (-X) has three tall windows; the low sun pours in through them (golden hour).
DESKS: list of (x, y) desk centres; the student for a desk sits at (x, y + 1.5).
SEAT_Z: mover height for a seated character (hips on the chair).
"""
import math
import random
import assets
from toon import toon, glassy, box, ellipsoid, cylinder, cone, tube, area_light, point_light, SetBuilder, text_obj, empty

DESKS = [(x, y) for y in (-4.0, 0.0, 4.0) for x in (-5.0, 0.0, 5.0)]
SEAT_Z = -0.75
M = 7.0 / 3.5          # Kenney furniture multiplier on top of assets.SCALE (a chair ~3.3 units tall)


def build(origin=(0, 0, 0)):
    rnd = random.Random(12)
    with SetBuilder('Classroom', origin) as root:
        wall = toon('CLWall', '#F2D49B', tex=('stripes', '#EBCB8D', 0.6, 'x'))
        wains = toon('CLWains', '#7FA7C9', tex=('planks', '#5E84A8', 0.5, 'wall'))
        floor = toon('CLFloor', '#C98E5A', tex=('planks', '#7A4E2D', 0.6, 'floor'))
        ceil = toon('CLCeil', '#F6E8CC')
        trim = toon('CLTrim', '#FFF6E2')
        sky = toon('CLSky', '#FFB26B', emit=True)
        sun_disc = toon('CLSun', '#FFF0B8', emit=True)
        desk_top = toon('CLDeskTop', '#E8C08A', tex=('planks', '#B98A55', 0.35, 'floor'))
        metal = toon('CLMetal', '#5A6A8A')
        green = toon('CLBoard', '#2F5D4A')
        chalk = toon('CLChalk', '#F4F1E8', emit=True)
        cork = toon('CLCork', '#C9955E')
        poster_cols = [toon(f'CLPoster{i}', c) for i, c in enumerate(('#E8393C', '#4F8FC9', '#F2C14E', '#6DB36B', '#B07CF0'))]

        # shell: floor, ceiling, back wall, right wall, left wall with 3 window holes
        box('CLFloorOb', (18.4, 17.4, 0.2), (0, -2.5, -0.1), floor)
        box('CLCeilOb', (18.4, 17.4, 0.2), (0, -2.5, 10.1), ceil)
        box('CLBack', (18.4, 0.3, 10.4), (0, 6.15, 5), wall)
        box('CLRight', (0.3, 17.4, 10.4), (9.15, -2.5, 5), wall)
        wy = (-7.5, -2.0, 3.5)          # window centres along the left wall
        ys = sorted({-11.2, 6.0} | {y - 1.8 for y in wy} | {y + 1.8 for y in wy})
        for i in range(len(ys) - 1):
            cy, h = (ys[i] + ys[i + 1]) / 2, ys[i + 1] - ys[i]
            is_win = any(abs(cy - y) < 0.01 for y in wy)
            if is_win:
                box('CLWinLow', (0.3, h, 2.8), (-9.15, cy, 1.4), wall)
                box('CLWinTop', (0.3, h, 1.6), (-9.15, cy, 9.2), wall)
            else:
                box('CLWallSeg', (0.3, h, 10.4), (-9.15, cy, 5), wall)
        for y in wy:                    # frames, mullions, sills, sky behind
            for dz in (2.8, 8.4):
                box('CLWinH', (0.35, 3.8, 0.2), (-9.0, y, dz), trim)
            for dy in (-1.8, 0.0, 1.8):
                box('CLWinV', (0.35, 0.2, 5.8), (-9.0, y + dy, 5.6), trim)
            box('CLWinMid', (0.3, 3.6, 0.14), (-9.0, y, 5.6), trim)
            box('CLSill', (0.9, 4.0, 0.2), (-8.7, y, 2.75), trim)
        box('CLSkyCard', (0.2, 60, 30), (-30, -2.5, 8), sky)
        cylinder('CLSunDisc', 3.0, 0.1, (-29.5, 4.0, 6.5), sun_disc, rot=(0, 90, 0))
        # wainscot + trims
        for nm, size, loc in (('CLWainB', (18.0, 0.08, 2.6), (0, 5.97, 1.3)),
                              ('CLWainR', (0.08, 17.0, 2.6), (8.97, -2.5, 1.3))):
            box(nm, size, loc, wains)
        box('CLRailB', (18.0, 0.18, 0.16), (0, 5.93, 2.62), trim)
        box('CLRailR', (0.18, 17.0, 0.16), (8.93, -2.5, 2.62), trim)
        box('CLCrown', (18.0, 0.3, 0.3), (0, 5.9, 9.85), trim)

        # back wall: cork board + posters, clock, alphabet strip, bookcases, plants
        box('CLCork', (6.0, 0.12, 3.0), (-3.0, 5.92, 5.6), cork)
        for i in range(6):
            p = box('CLPin', (rnd.uniform(0.8, 1.3), 0.05, rnd.uniform(0.8, 1.2)),
                    (-5.2 + i * 0.9, 5.84, 5.2 + 0.6 * (i % 2)), poster_cols[i % 5])
            p.rotation_euler = (0, math.radians(rnd.uniform(-6, 6)), 0)
        text_obj('CLAlpha', 'A B C D E F G H I J', 0.42, (0.0, 5.86, 8.7), toon('CLAlphaM', '#3E4C82'), extrude=0.02)
        cylinder('CLClock', 0.7, 0.14, (4.6, 5.9, 6.4), toon('CLClockFace', '#FFFFFF'), rot=(90, 0, 0), outline=0.03)
        cylinder('CLClockRim', 0.8, 0.1, (4.6, 5.96, 6.4), toon('CLClockRimM', '#E8393C'), rot=(90, 0, 0))
        ink = toon('Ink', '#2A2230')
        box('CLHandH', (0.07, 0.04, 0.4), (4.6, 5.8, 6.55), ink).rotation_euler = (0, math.radians(-110), 0)
        box('CLHandM', (0.05, 0.04, 0.58), (4.6, 5.79, 6.65), ink).rotation_euler = (0, math.radians(20), 0)
        box('CLBoardSide', (0.12, 4.0, 2.8), (8.9, -4.0, 5.6), green)
        text_obj('CLBoardTxt', 'YAWN 101', 0.5, (8.82, -4.0, 6.0), chalk, rot=(90, 0, -90), extrude=0.01)
        tube('CLChalkLine', [(8.82, -5.5, 5.0), (8.82, -4.0, 4.7), (8.82, -2.5, 5.1)], 0.03, chalk)
        for i, x in enumerate((6.6, 8.0)):
            assets.load('furniture-kit', 'bookcaseOpen', loc=(x - 0.6, 5.0, 0), scale=M, rot=(0, 0, 180), center=True)
        assets.load('furniture-kit', 'pottedPlant', loc=(-7.8, 4.8, 0), scale=M, center=True)
        assets.load('furniture-kit', 'pottedPlant', loc=(8.0, -9.0, 0), scale=M, center=True)
        # cubbies with bags on the right wall
        for i in range(4):
            box('CLCubby', (1.4, 1.6, 1.4), (8.2, -0.5 + i * 1.65, 1.0), toon('CLCubbyM', '#E8D7B0'), outline=0.02)
            ellipsoid('CLBag', (0.45, 0.4, 0.4), (8.0, -0.5 + i * 1.65, 1.0), poster_cols[(i + 2) % 5], outline=0.02)

        # student desks (simple school desks) + Kenney chairs + things on desks
        for i, (x, y) in enumerate(DESKS):
            box('CLDeskTop', (3.0, 2.0, 0.16), (x, y, 2.7), desk_top, bevel=0.04)
            for dx in (-1.35, 1.35):
                for dy in (-0.85, 0.85):
                    box('CLDeskLeg', (0.12, 0.12, 2.6), (x + dx, y + dy, 1.3), metal)
            box('CLDeskShelf', (2.7, 1.7, 0.08), (x, y, 1.9), metal)
            assets.load('furniture-kit', 'chair', loc=(x, y + 1.9, 0), scale=M, rot=(0, 0, 180), center=True)
            if i % 3 == 0:
                assets.load('furniture-kit', 'books', loc=(x - 0.8, y - 0.2, 2.78), scale=M, rot=(0, 0, rnd.uniform(-30, 30)),
                            center=True)
            elif i % 3 == 1:
                box('CLPaper', (0.9, 1.2, 0.02), (x + 0.5, y, 2.79), toon('CLPaperM', '#FFFFFF'))
                cylinder('CLPencil', 0.04, 0.9, (x - 0.4, y + 0.1, 2.82), toon('CLPencilM', '#F2C14E'), rot=(0, 90, 20))
            else:
                cylinder('CLApple', 0.0001, 0.0001, (x, y, 2.8))
                ellipsoid('CLAppleOb', (0.26, 0.26, 0.24), (x + 0.9, y - 0.3, 3.02), toon('CLAppleM', '#E8393C'),
                          outline=0.02)

        # light: low golden sun comes from the windows (added per-set in the episode), warm fill
        area_light((0, -14, 6), (80, 0, 0), 14, 1200, '#FFD9B0', 'CLFront')
        area_light((0, -2, 9.8), (0, 0, 0), 12, 500, '#FFE8CC', 'CLCeilFill')
        point_light((-8.5, -2.0, 5.5), 600, '#FFB26B', 3.0, 'CLWinGlow')
    return {'root': root, 'origin': origin}
