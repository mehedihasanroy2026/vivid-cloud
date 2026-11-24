"""Set: cosy family living room in golden evening light (EP05), Kenney furniture.

Local layout: room x -8..8, y -9..6, floor z=0, ceiling z=9. Cameras look toward +Y.
Sofa against the back wall facing -Y; SOFA_SEATS are (x, y) mover spots, SOFA_Z the mover height
for a seated character. Rug + coffee table in front, TV unit on the right, window on the back-left.
"""
import math
import random
import assets
from toon import toon, glassy, box, ellipsoid, cylinder, cone, tube, area_light, point_light, SetBuilder, text_obj

M = 7.5 / 3.5
SOFA_SEATS = [(-2.0, 3.4), (0.0, 3.4), (2.0, 3.4)]
SOFA_Z = -0.6


def build(origin=(0, 0, 0)):
    rnd = random.Random(31)
    with SetBuilder('Living', origin) as root:
        wall = toon('LVWall', '#E9A97A', tex=('stripes', '#E19F70', 0.5, 'x'))
        wains = toon('LVWains', '#8E5B4A', tex=('planks', '#6B4236', 0.5, 'wall'))
        floor = toon('LVFloor', '#B07A4E', tex=('planks', '#6B4430', 0.65, 'floor'))
        ceil = toon('LVCeil', '#F2DCC0')
        trim = toon('LVTrim', '#FFF1DE')
        sky = toon('LVSky', '#FF9F5A', emit=True)
        frame = toon('LVFrame', '#C9A04A')
        art = [toon(f'LVArt{i}', c) for i, c in enumerate(('#4F8FC9', '#6DB36B', '#E8393C', '#F2C14E'))]

        box('LVFloorOb', (16.4, 15.4, 0.2), (0, -1.5, -0.1), floor)
        box('LVCeilOb', (16.4, 15.4, 0.2), (0, -1.5, 9.1), ceil)
        # back wall with a window hole at x -6..-2.4, z 3..7.4
        box('LVBackL', (2.0, 0.3, 9.4), (-7.2, 6.15, 4.6), wall)
        box('LVBackR', (10.4, 0.3, 9.4), (2.8, 6.15, 4.6), wall)
        box('LVBackLow', (3.6, 0.3, 3.0), (-4.2, 6.15, 1.5), wall)
        box('LVBackTop', (3.6, 0.3, 1.9), (-4.2, 6.15, 8.35), wall)
        box('LVSkyCard', (40, 0.2, 30), (0, 25, 8), sky)
        for dz in (3.0, 7.4):
            box('LVWinH', (3.8, 0.4, 0.2), (-4.2, 6.0, dz), trim)
        for dx in (-6.0, -4.2, -2.4):
            box('LVWinV', (0.2, 0.4, 4.6), (dx, 6.0, 5.2), trim)
        box('LVSill', (4.2, 0.9, 0.2), (-4.2, 5.7, 2.95), trim)
        curtain = toon('LVCurtain', '#7A3E5A', tex=('stripes', '#6C3550', 0.3, 'x'))
        for s in (-1, 1):
            for i in range(3):
                ellipsoid('LVPleat', (0.2, 0.18, 2.8), (-4.2 + s * (2.3 + 0.28 * i), 5.75, 5.2), curtain, outline=0.02)
        box('LVLeft', (0.3, 15.4, 9.4), (-8.15, -1.5, 4.6), wall)
        box('LVRight', (0.3, 15.4, 9.4), (8.15, -1.5, 4.6), wall)
        for nm, size, loc in (('LVWainB', (16.0, 0.08, 2.4), (2.8, 5.97, 1.2)),
                              ('LVWainL', (0.08, 15.0, 2.4), (-7.97, -1.5, 1.2)),
                              ('LVWainR', (0.08, 15.0, 2.4), (7.97, -1.5, 1.2))):
            box(nm, size, loc, wains)
        box('LVRail', (16.0, 0.18, 0.15), (0, 5.93, 2.42), trim)
        box('LVCrown', (16.0, 0.3, 0.3), (0, 5.9, 8.85), trim)

        # furniture (Kenney)
        assets.load('furniture-kit', 'rugRectangle', loc=(0, 0.2, 0.01), scale=M * 0.9, center=True)
        assets.load('furniture-kit', 'loungeSofa', loc=(0, 4.3, 0), scale=M, center=True, tint='#5E7FB8')
        for x, c in ((-2.6, 'pillowBlue'), (2.6, 'pillow')):
            assets.load('furniture-kit', c, loc=(x, 5.0, 1.7), scale=M, center=True)
        assets.load('furniture-kit', 'tableCoffee', loc=(0, -1.8, 0), scale=M * 0.6, center=True)
        assets.load('furniture-kit', 'cabinetTelevision', loc=(7.0, -1.5, 0), scale=M, rot=(0, 0, 90), center=True)
        assets.load('furniture-kit', 'televisionModern', loc=(7.0, -1.5, 2.3), scale=M, rot=(0, 0, 90), center=True)
        assets.load('furniture-kit', 'lampRoundFloor', loc=(5.6, 4.6, 0), scale=M, center=True)
        assets.load('furniture-kit', 'pottedPlant', loc=(-7.0, 4.5, 0), scale=M, center=True)
        assets.load('furniture-kit', 'bookcaseOpen', loc=(-7.2, -2.0, 0), scale=M, rot=(0, 0, -90), center=True)
        assets.load('furniture-kit', 'sideTable', loc=(4.6, 4.8, 0), scale=M * 0.8, rot=(0, 0, 180), center=True)
        assets.load('furniture-kit', 'books', loc=(-0.6, -1.8, 1.2), scale=M, center=True)
        assets.load('furniture-kit', 'radio', loc=(4.6, 4.8, 2.1), scale=M, rot=(0, 0, 180), center=True)
        # framed pictures above the sofa
        for i, (x, z, w, h) in enumerate(((-1.8, 6.6, 1.6, 1.2), (0.3, 6.9, 1.2, 1.6), (2.2, 6.5, 1.4, 1.0))):
            box('LVPicFrame', (w, 0.1, h), (x, 5.92, z), frame, outline=0.02)
            box('LVPicArt', (w - 0.25, 0.06, h - 0.25), (x, 5.87, z), art[i])
        # dog bed + bowl
        cylinder('LVDogBed', 1.3, 0.35, (-4.0, -1.5, 0.18), toon('LVDogBedM', '#C9A04A'), outline=0.03)
        cylinder('LVDogBowl', 0.35, 0.25, (-5.6, -3.0, 0.12), toon('LVBowl', '#E8393C'), outline=0.02)

        area_light((0, -14, 6), (80, 0, 0), 14, 1300, '#FFD9B0', 'LVFront')
        area_light((0, -1, 8.8), (0, 0, 0), 10, 450, '#FFE6C8', 'LVCeilFill')
        point_light((5.6, 4.6, 6.2), 350, '#FFC27A', 0.6, 'LVLampGlow')
        point_light((-4.2, 5.4, 5.2), 500, '#FF9F5A', 2.5, 'LVWinGlow')
    return {'root': root, 'origin': origin}
