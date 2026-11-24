"""Set: home living room, real-light look (EP07).

Local layout: room x -10..10, y -10..7, floor z=0, ceiling z=11. Cameras look toward +Y.
Sofa against the back wall (y ~4.6) facing -Y. Big window on the back-left: the afternoon sun pours in
across a soft rug in the middle (RUG centre, about 8 x 6), which is where Kai ends up rolling on the floor.
TV unit on the right wall, bookcase + plant on the left.
"""
import assets
import real
from toon import box, cylinder, SetBuilder

M = 7.5 / 3.5
RUG = (0.0, -0.5)


def build(origin=(0, 0, 0)):
    with SetBuilder('Living', origin) as root:
        wall = real.mat('LWall', '#E3C7A6', 'paint', mode='wall', scale=0.6, grime=0.15)
        wallx = real.mat('LWallX', '#E3C7A6', 'paint', mode='wallx', scale=0.6, grime=0.15)
        accent = real.mat('LAccent', '#4F7C8A', 'paint', mode='wall', scale=0.6, grime=0.12)
        floor = real.mat('LFloor', '#A8784F', 'wood', mode='floor', scale=0.5, grime=0.25)
        ceil = real.mat('LCeil', '#F1ECE4', 'paint', grime=0.08)
        trim = real.mat('LTrim', '#FBF8F2', 'paint', grime=0.05)
        rug = real.mat('LRug', '#C9584A', 'fabric', grime=0.05)
        rug2 = real.mat('LRug2', '#F1D9A8', 'fabric', grime=0.05)
        sky = real.mat('LSky', '#EAF4FF', 'glow', emit=3.2)
        trees = real.mat('LTrees', '#86B56D', 'glow', emit=1.3)
        frame = real.mat('LFrame', '#2E2A27', 'wood', grime=0.1)
        art = [real.mat(f'LArt{i}', c, 'paint', grime=0) for i, c in enumerate(('#E9B44C', '#5B8E7D', '#D8674A'))]
        lampm = real.mat('LLamp', '#FFF3DC', 'glow', emit=6.0)

        box('LFloorOb', (20.4, 17.4, 0.2), (0, -1.5, -0.1), floor)
        box('LCeilOb', (20.4, 17.4, 0.2), (0, -1.5, 11.1), ceil)
        # back wall with a window hole (x -9..-3, z 2.6..9)
        box('LBackL', (1.0, 0.4, 11.4), (-9.6, 7.2, 5.5), wall)
        box('LBackR', (13.0, 0.4, 11.4), (3.5, 7.2, 5.5), accent)
        box('LBackLow', (6.0, 0.4, 2.6), (-6.0, 7.2, 1.3), wall)
        box('LBackTop', (6.0, 0.4, 2.4), (-6.0, 7.2, 10.2), wall)
        box('LLeft', (0.4, 17.4, 11.4), (-10.2, -1.5, 5.5), wallx)
        box('LRight', (0.4, 17.4, 11.4), (10.2, -1.5, 5.5), wallx)
        for z in (2.6, 9.0):
            box('LWinH', (6.2, 0.5, 0.18), (-6.0, 7.0, z), trim)
        for x in (-9.0, -6.0, -3.0):
            box('LWinV', (0.18, 0.5, 6.6), (x, 7.0, 5.8), trim)
        box('LSill', (6.8, 1.0, 0.2), (-6.0, 6.7, 2.5), trim)
        outside = [box('LSkyCard', (60, 0.2, 40), (0, 30, 10), sky),
                   box('LTreeBand', (60, 0.2, 6.0), (0, 29.8, 3.0), trees)]
        for x in (-16, -11, -7.5, -3, 2):
            outside.append(cylinder('LTreeTop', 2.8, 0.3, (x, 29.6, 6.2), trees, rot=(90, 0, 0)))
        for o in outside:
            o.visible_shadow = False
        for nm, size, loc in (('LBase', (20.0, 0.2, 0.5), (0, 6.95, 0.25)),
                              ('LBaseL', (0.2, 17.0, 0.5), (-9.95, -1.5, 0.25)),
                              ('LBaseR', (0.2, 17.0, 0.5), (9.95, -1.5, 0.25))):
            box(nm, size, loc, trim)
        box('LCrown', (20.0, 0.3, 0.3), (0, 6.9, 10.85), trim)

        # rug: a big soft rectangle with a border
        box('LRugOb', (9.0, 6.6, 0.08), (RUG[0], RUG[1], 0.04), rug)
        box('LRugIn', (7.6, 5.2, 0.09), (RUG[0], RUG[1], 0.045), rug2)
        box('LRugCore', (6.4, 4.0, 0.1), (RUG[0], RUG[1], 0.05), rug)

        # furniture (Kenney)
        assets.load('furniture-kit', 'loungeSofaLong', loc=(1.5, 5.3, 0), scale=M, center=True, tint='#5D6F86')
        for x, c in ((-1.6, 'pillowBlue'), (4.6, 'pillow')):
            assets.load('furniture-kit', c, loc=(x, 6.0, 1.7), scale=M, center=True)
        assets.load('furniture-kit', 'cabinetTelevision', loc=(9.0, -1.5, 0), scale=M, rot=(0, 0, 90), center=True)
        assets.load('furniture-kit', 'televisionModern', loc=(9.0, -1.5, 2.3), scale=M, rot=(0, 0, 90), center=True)
        assets.load('furniture-kit', 'lampRoundFloor', loc=(7.6, 5.6, 0), scale=M, center=True)
        assets.load('furniture-kit', 'pottedPlant', loc=(-8.8, 5.4, 0), scale=M, center=True)
        assets.load('furniture-kit', 'bookcaseOpen', loc=(-9.2, -2.5, 0), scale=M, rot=(0, 0, -90), center=True)
        assets.load('furniture-kit', 'books', loc=(-9.2, -2.5, 3.0), scale=M, rot=(0, 0, -90), center=True)
        assets.load('furniture-kit', 'sideTable', loc=(-2.6, 5.6, 0), scale=M * 0.8, center=True)
        assets.load('furniture-kit', 'lampRoundTable', loc=(-2.6, 5.6, 1.75), scale=M, center=True)
        assets.load('furniture-kit', 'tableCoffee', loc=(6.0, -4.5, 0), scale=M * 0.6, rot=(0, 0, 20), center=True)
        assets.load('furniture-kit', 'plantSmall2', loc=(6.0, -4.5, 1.05), scale=M, center=True)
        # framed pictures above the sofa
        for i, (x, z, w, h) in enumerate(((-0.2, 7.2, 2.0, 1.5), (2.4, 7.5, 1.5, 2.1), (4.8, 7.1, 1.8, 1.3))):
            box('LPicFrame', (w, 0.1, h), (x, 6.95, z), frame)
            box('LPicArt', (w - 0.3, 0.06, h - 0.3), (x, 6.89, z), art[i])
        # ceiling lamp
        cylinder('LCeilLampOb', 1.1, 0.25, (0, -1.0, 10.85), lampm)

        # light: afternoon sun through the window onto the rug, warm fill, haze for shafts
        real.sun((58, 0, 200), strength=12.0, hexc='#FFE0B0', angle=1.2, name='LSun')
        real.area((-6.0, 6.0, 6.0), (90, 0, 0), 6, 450, '#CFE4FF', shadow=False, name='LWinFill', volume=0.0)
        real.area((0, -12, 8), (75, 0, 0), 16, 600, '#F2E6D8', shadow=False, name='LFront', volume=0.0)
        real.area((0, -1, 10.7), (0, 0, 0), 8, 300, '#FFE9CC', shadow=False, name='LCeilFill', volume=0.0)
        real.point((7.6, 5.6, 5.6), 200, '#FFC98A', radius=0.6, name='LLampGlow', volume=0.2)
        real.shafts((0, -1.5, 5.5), (20, 17, 11), density=0.008, name='LHaze')
    return {'root': root, 'origin': origin}
