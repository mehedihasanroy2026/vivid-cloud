"""Set: bright home kitchen, real-light look (EP06).

Local layout: room x -10..10, y -10..7, floor z=0, ceiling z=12. Cameras look toward +Y.
Back wall y=7: big window on the left (x -8..-2, z 3.5..9.5), the sun pours in through it toward
the camera. Counters + cabinets + fridge along the back-right. Kitchen island in the middle-right.
COUNTER_TOP = height of the counter top (for props).
"""
import math
import assets
import real
from toon import box, cylinder, empty, SetBuilder

M = 7.5 / 3.5
COUNTER_TOP = 3.05
WIN = (-5.0, 6.5, 6.0)      # local window centre


def build(origin=(0, 0, 0), sun=True):
    with SetBuilder('Kitchen', origin) as root:
        wall = real.mat('KWall', '#B9CBD3', 'paint', mode='wall', scale=0.6, grime=0.18)
        tile = real.mat('KTile', '#F1F3EF', 'tile', mode='wall', size=(0.6, 0.3), line='#B9C1C2', grime=0.08)
        floor = real.mat('KFloor', '#D9D4CA', 'tile', mode='floor', size=(1.6, 1.6), line='#9C978E', grime=0.3)
        ceil = real.mat('KCeil', '#E8ECEC', 'paint', grime=0.1)
        trim = real.mat('KTrim', '#FAFAF6', 'paint', grime=0.05)
        frame = real.mat('KFrame', '#FFFFFF', 'paint', grime=0.0)
        beam = real.mat('KBeam', '#8B6A4E', 'wood', mode='box', scale=1.0, grime=0.2)
        steel = real.mat('KSteel', '#C9CED3', 'metal', grime=0.1)
        sky = real.mat('KSky', '#EAF4FF', 'glow', emit=3.0)
        trees = real.mat('KTrees', '#7FB069', 'glow', emit=1.4)
        lampm = real.mat('KLamp', '#FFF7E8', 'glow', emit=8.0)

        box('KFloorOb', (20.4, 17.4, 0.2), (0, -1.5, -0.1), floor)
        box('KCeilOb', (20.4, 17.4, 0.2), (0, -1.5, 12.1), ceil)
        # back wall with the window hole (x -8..-2, z 3.5..9.5)
        box('KBackL', (2.0, 0.4, 12.4), (-9.0, 7.2, 6.0), wall)
        box('KBackR', (12.0, 0.4, 12.4), (4.0, 7.2, 6.0), wall)
        box('KBackLow', (6.0, 0.4, 3.5), (-5.0, 7.2, 1.75), wall)
        box('KBackTop', (6.0, 0.4, 2.7), (-5.0, 7.2, 10.85), wall)
        box('KLeft', (0.4, 17.4, 12.4), (-10.2, -1.5, 6.0), wall)
        box('KRight', (0.4, 17.4, 12.4), (10.2, -1.5, 6.0), wall)
        # window frame + mullions + sill
        for z in (3.5, 6.5, 9.5):
            box('KWinH', (6.2, 0.5, 0.18), (-5.0, 7.0, z), frame)
        for x in (-8.0, -5.0, -2.0):
            box('KWinV', (0.18, 0.5, 6.2), (x, 7.0, 6.5), frame)
        box('KSill', (6.8, 1.0, 0.2), (-5.0, 6.7, 3.4), trim)
        # outside: soft bright sky + a band of distant trees
        outside = [box('KSkyCard', (60, 0.2, 40), (0, 30, 10), sky),
                   box('KTreeBand', (60, 0.2, 5.0), (0, 29.8, 3.0), trees)]
        for x in (-14, -9, -6.5, -1, 3):
            outside.append(cylinder('KTreeTop', 2.6, 0.3, (x, 29.6, 5.6), trees, rot=(90, 0, 0)))
        for o in outside:
            o.visible_shadow = False
        # tiled backsplash behind the counters
        box('KSplash', (11.5, 0.08, 3.6), (4.2, 6.96, COUNTER_TOP + 1.8), tile)
        # baseboards
        box('KBase', (20.0, 0.2, 0.5), (0, 6.95, 0.25), trim)
        box('KBaseL', (0.2, 17.0, 0.5), (-9.95, -1.5, 0.25), trim)
        box('KBaseR', (0.2, 17.0, 0.5), (9.95, -1.5, 0.25), trim)
        # ceiling beams + two pendant lamps
        for y in (-6.0, -1.0, 4.0):
            box('KBeamOb', (20.4, 0.7, 0.8), (0, y, 11.6), beam)
        for x, y in ((3.0, 1.0), (-3.0, 1.0)):
            cylinder('KCord', 0.03, 3.0, (x, y, 10.5), steel)
            cylinder('KShade', 0.9, 0.7, (x, y, 8.8), steel)
            cylinder('KBulb', 0.45, 0.2, (x, y, 8.4), lampm)
            real.spot((x, y, 8.3), (0, 0, 0), 900, angle=90, hexc='#FFE2B8', blend=0.8, radius=0.3, volume=0.4)

        # counters + cabinets along the back-right (Kenney furniture)
        for i, x in enumerate((0.0, 2.2, 4.4, 6.6)):
            nm = 'kitchenSink' if i == 1 else ('kitchenStove' if i == 3 else 'kitchenCabinetDrawer')
            assets.load('furniture-kit', nm, loc=(x, 6.0, 0), scale=M, rot=(0, 0, 180), center=True,
                        tint='#DCE3DF' if i != 3 else None)
            assets.load('furniture-kit', 'kitchenCabinetUpper', loc=(x, 6.5, 6.6), scale=M, rot=(0, 0, 180),
                        center=True, tint='#DCE3DF')
        # custom fridge (door opens): body x 7.4..10.0, front face y=4.2, hinge on the right edge
        fr = real.mat('KFridge', '#E9EDEF', 'metal', grime=0.06, rough=0.3, metal=0.2)
        inside = real.mat('KFridgeIn', '#F7FBFF', 'glow', emit=1.0)
        box('KFridgeBack', (2.6, 0.2, 8.0), (8.7, 6.6, 4.0), fr)
        box('KFridgeL', (0.2, 2.4, 8.0), (7.5, 5.4, 4.0), fr)
        box('KFridgeR', (0.2, 2.4, 8.0), (9.9, 5.4, 4.0), fr)
        box('KFridgeTop', (2.6, 2.4, 0.2), (8.7, 5.4, 7.9), fr)
        box('KFridgeBot', (2.6, 2.4, 0.4), (8.7, 5.4, 0.2), fr)
        box('KFridgeIn', (2.2, 0.05, 7.4), (8.7, 6.45, 4.0), inside)
        shelf = real.glass('KShelf', '#DDEFFF', 0.4)
        can_m = real.mat('ColaCan', '#C8102E', 'metal', grime=0.0, rough=0.25)
        fridge_cans = []
        for z in (2.2, 4.2, 6.2):
            box('KFShelf', (2.2, 2.2, 0.06), (8.7, 5.5, z), shelf)
        for i, x in enumerate((8.0, 8.55, 9.1, 9.6)):
            fridge_cans.append(cylinder('KFCan', 0.24, 0.8, (x, 4.9, 4.65), can_m))
        hinge = empty('KFridgeHinge', (9.95, 4.2, 0))
        door = box('KFridgeDoor', (2.6, 0.3, 8.0), (-1.25, -0.15, 4.0), fr, parent=hinge)
        box('KFridgeHandle', (0.15, 0.25, 2.4), (-2.3, -0.4, 4.6), steel, parent=hinge)
        real.point((8.7, 5.0, 7.0), 150, '#EAF4FF', name='KFridgeLight')
        assets.load('furniture-kit', 'kitchenMicrowave', loc=(4.4, 6.3, COUNTER_TOP), scale=M, rot=(0, 0, 180),
                    center=True)
        assets.load('furniture-kit', 'kitchenCoffeeMachine', loc=(-0.2, 6.3, COUNTER_TOP), scale=M,
                    rot=(0, 0, 180), center=True)
        assets.load('furniture-kit', 'pottedPlant', loc=(-8.6, 5.2, 0), scale=M, center=True)
        assets.load('furniture-kit', 'plantSmall1', loc=(-3.0, 6.75, 3.5), scale=M, center=True)
        assets.load('furniture-kit', 'plantSmall2', loc=(-6.8, 6.75, 3.5), scale=M, center=True)
        # island with stools on the right
        for x in (3.2, 5.4):
            assets.load('furniture-kit', 'kitchenBar', loc=(x, -0.5, 0), scale=M, center=True, tint='#6F8C84')
        for x in (3.2, 5.4):
            assets.load('furniture-kit', 'stoolBar', loc=(x, -2.6, 0), scale=M, center=True)
        assets.load('furniture-kit', 'kitchenBlender', loc=(5.8, -0.4, COUNTER_TOP), scale=M, center=True)

        # light: low sun through the window toward the camera, cool sky fill, haze for shafts
        if sun:
            real.sun((60, 0, 198), strength=14.0, hexc='#FFE4BC', angle=1.2, name='KSun')
        real.area((-5.0, 6.0, 6.5), (90, 0, 0), 6, 500, '#CFE4FF', shadow=False, name='KWinFill', volume=0.0)
        real.area((0, -12, 8), (75, 0, 0), 16, 500, '#DCE8F6', shadow=False, name='KFront', volume=0.0)
        real.shafts((0, -1.5, 6.0), (20, 17, 12), density=0.008, name='KHaze')
    return {'root': root, 'origin': origin, 'fridge_hinge': hinge, 'fridge_cans': fridge_cans}
