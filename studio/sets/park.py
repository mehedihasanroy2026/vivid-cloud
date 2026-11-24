"""Set: sunny summer park with an ice cream cart. Pro-look standard: dense props, bright day.

Local layout: ground z=0. Path runs along X at y -1..1. Hero spot HERO = (0, -1.0).
Ice cream cart behind-left at (-5, 3). Bench right at (5, 2.5). Sky card far back (y=40).
"""
import math
import random
from toon import toon, glassy, box, ellipsoid, cylinder, cone, tube, point_light, area_light, SetBuilder, text_obj, empty

HERO = (0.0, -1.0)


def tree(name, x, y, h, rnd, mats, bark):
    cylinder(f'{name}Trunk', 0.35, h, (x, y, h / 2), bark, outline=0.03)
    for i in range(6):
        ellipsoid(f'{name}Leaf', (rnd.uniform(1.4, 2.1),) * 2 + (rnd.uniform(1.2, 1.6),),
                  (x + rnd.uniform(-1.3, 1.3), y + rnd.uniform(-1.0, 1.0), h + rnd.uniform(-0.3, 1.6)),
                  rnd.choice(mats), outline=0.04, segs=20, rings=10)


def build(origin=(0, 0, 0), kit=False):
    """kit=True: use the downloaded Kenney models for houses, fences, bench, bin, cart treats."""
    rnd = random.Random(21)
    with SetBuilder('Park', origin) as root:
        grass = toon('PkGrass', '#7CC46A', tex=('stripes', '#72B860', 1.6, 'x'))
        path = toon('PkPath', '#E8D7B0', tex=('tiles', '#C9B48A', 1.2))
        sky = toon('PkSky', '#8FD0F2', emit=True)
        cloud = toon('PkCloud', '#FFFFFF', emit=True)
        bark = toon('PkBark', '#8A5A3C', tex=('planks', '#5A3826', 0.25, 'wall'))
        leaves = [toon('PkLeaf1', '#5DB35A'), toon('PkLeaf2', '#4A9E50'), toon('PkLeaf3', '#7CC46A')]
        white = toon('PkWhite', '#F7F4EC')
        wood = toon('PkWood', '#C58A55', tex=('planks', '#7A4E2D', 0.25, 'floor'))
        metal = toon('PkMetal', '#3E4A5C')
        cart_c = toon('PkCart', '#F6A6C1', tex=('stripes', '#FFFFFF', 0.45, 'x'))
        umb = toon('PkUmbrella', '#FF7A8A', tex=('stripes', '#FFF3D6', 0.6, 'x'))
        flower_cols = [toon(f'PkFlower{i}', c) for i, c in enumerate(('#FF6B8B', '#FFD23F', '#B07CF0', '#FF9F43'))]
        house_cols = [toon(f'PkHouse{i}', c) for i, c in enumerate(('#F2C6A0', '#B8D8F0', '#F7E3A1', '#D7C2EE'))]
        roof = toon('PkRoof', '#C0504D')
        scoop_cols = [toon('PkScoopPink', '#FFB3C7'), toon('PkScoopMint', '#A8E6CF'), toon('PkScoopVan', '#FFF1C9'),
                      toon('PkScoopChoc', '#8B5A3C')]
        cone_m = toon('PkCone', '#E0A458', tex=('tiles', '#B97A35', 0.12, 'wall'))

        # sky, sun disc, clouds
        box('PkSkyCard', (160, 0.2, 70), (0, 45, 25), sky)
        cylinder('PkSunDisc', 4, 0.1, (-22, 44.5, 38), toon('PkSunM', '#FFF4B0', emit=True), rot=(90, 0, 0))
        for i in range(7):
            cx, cz = rnd.uniform(-45, 45), rnd.uniform(18, 34)
            for k in range(4):
                ellipsoid('PkCloudPuff', (rnd.uniform(2.5, 4),) * 2 + (2,), (cx + k * 2.6 - 4, 44, cz + rnd.uniform(-0.6, 0.8)),
                          cloud, segs=16, rings=8)

        # ground + path + far hills + houses
        box('PkGround', (120, 90, 0.4), (0, 15, -0.2), grass)
        box('PkPathOb', (120, 2.6, 0.06), (0, -1.0, 0.03), path)
        for i in range(5):
            ellipsoid('PkHill', (18, 8, 6), (-40 + i * 20, 36, 0), toon('PkHillM', '#8FD07A'), segs=24, rings=12)
        if kit:
            import assets
            for i, t in enumerate('abcdefgh'):
                assets.load('city-kit-suburban', f'building-type-{t}', loc=(-30 + i * 8.5, 24 + (i % 2) * 2.5, 0),
                            scale=1.25, rot=(0, 0, 180 + (i % 3 - 1) * 8))
            for i in range(9):
                assets.load('city-kit-suburban', 'fence-1x4', loc=(-26 + i * 6.6, 9.0, 0), scale=1.0, rot=(0, 0, 90))
            assets.load('furniture-kit', 'bench', loc=(5.0, 2.6, 0), scale=1.9, rot=(0, 0, 180))
            assets.load('furniture-kit', 'trashcan', loc=(7.6, 2.4, 0), scale=1.6)
            assets.load('city-kit-suburban', 'planter', loc=(-9.5, 1.6, 0), scale=1.0)
            assets.load('city-kit-suburban', 'planter', loc=(9.5, 1.2, 0), scale=1.0)
            for x in (-2.6, -1.8, -1.0):
                assets.load('food-kit', 'ice-cream', loc=(-5.0 + x + 1.8, 3.0, 2.8), scale=0.55)
        for i in range(0 if kit else 6):
            hx = -25 + i * 10 + rnd.uniform(-1, 1)
            hm = rnd.choice(house_cols)
            box('PkHouseBody', (5, 4, 4.5), (hx, 26, 2.25), hm)
            r = cone('PkHouseRoof', 3.9, 0.0, 2.6, (hx, 26, 5.8), roof, verts=4, rot=(0, 0, 45))
            r.scale = (1.0, 0.75, 1)
            for dx in (-1.2, 1.2):
                box('PkHouseWin', (1.0, 0.1, 1.0), (hx + dx, 23.95, 2.8), toon('PkWinBlue', '#8FC7EE'))
            box('PkHouseDoor', (1.0, 0.1, 2.0), (hx, 23.95, 1.0), toon('PkDoor', '#7A4E2D'))

        # picket fence along the back
        for i in range(0 if kit else 60):
            x = -30 + i * 1.0
            box('PkPicket', (0.3, 0.12, 1.8), (x, 9.0, 0.9), white)
        for z in ((0.6, 1.4) if not kit else ()):
            box('PkRail', (60, 0.1, 0.15), (0, 9.08, z), white)

        # trees
        for i, (x, y, h) in enumerate(((-9, 6, 5.5), (8.5, 6.5, 6.0), (-16, 12, 6.5), (15, 13, 6.0), (2, 14, 7.0),
                                       (-4, 18, 7.0), (22, 18, 6.5), (-24, 17, 6.0))):
            tree(f'PkTree{i}', x, y, h, rnd, leaves, bark)

        # ice cream cart: body, wheels, umbrella, menu, cone rack
        cx, cy = -5.0, 3.0
        box('PkCartBody', (3.6, 1.8, 2.0), (cx, cy, 1.6), cart_c, bevel=0.08)
        box('PkCartTop', (3.8, 2.0, 0.2), (cx, cy, 2.7), white, bevel=0.05)
        for dx in (-1.3, 1.3):
            w = cylinder('PkWheel', 0.55, 0.2, (cx + dx, cy - 0.95, 0.55), metal, rot=(90, 0, 0), outline=0.02)
            cylinder('PkHub', 0.18, 0.24, (cx + dx, cy - 0.95, 0.55), white, rot=(90, 0, 0))
        cylinder('PkUmbPole', 0.06, 3.8, (cx, cy, 4.5), metal)
        cone('PkUmbTop', 2.6, 0.1, 0.9, (cx, cy, 6.3), umb, outline=0.03, verts=12)
        box('PkMenu', (1.6, 0.1, 1.0), (cx + 0.6, cy - 0.95, 1.7), toon('PkMenuBoard', '#3E2C4A'))
        text_obj('PkMenuTxt', 'ICE\nCREAM', 0.28, (cx + 0.6, cy - 1.02, 1.72), toon('PkMenuTxtM', '#FFD23F', emit=True),
                 extrude=0.01)
        for i in range(0 if kit else 4):     # display scoops on top
            ellipsoid('PkDisplayScoop', (0.32, 0.32, 0.28), (cx - 1.2 + i * 0.8, cy, 3.05), scoop_cols[i], outline=0.02)
        text_obj('PkCartSign', 'SCOOPS', 0.4, (cx, cy - 0.92, 2.15), toon('PkCartSignM', '#FFFFFF'), extrude=0.02)

        # bench + bin + lamppost + flowers + balloons on the cart
        bx, by = 5.0, 2.5
        if not kit:           # with kit=True the bench and bin come from the downloaded models
            box('PkBenchSeat', (3.4, 1.0, 0.16), (bx, by, 1.3), wood)
            box('PkBenchBack', (3.4, 0.16, 1.0), (bx, by + 0.5, 2.0), wood)
            for dx in (-1.5, 1.5):
                box('PkBenchLeg', (0.14, 0.9, 1.3), (bx + dx, by, 0.65), metal)
            cylinder('PkBin', 0.45, 1.3, (bx + 2.6, by, 0.65), toon('PkBinM', '#4A8C5C'), outline=0.02)
        cylinder('PkLampPost', 0.12, 6.0, (-1.8, 4.5, 3.0), metal, outline=0.02)
        ellipsoid('PkLampTop', (0.45, 0.45, 0.35), (-1.8, 4.5, 6.2), white, outline=0.02)
        for i in range(40):
            fx, fy = rnd.uniform(-14, 14), rnd.uniform(3.5, 8.5)
            if abs(fx - cx) < 2.4 and abs(fy - cy) < 1.6:
                continue
            cylinder('PkStem', 0.03, 0.5, (fx, fy, 0.25), leaves[1])
            ellipsoid('PkBloom', (0.16, 0.16, 0.12), (fx, fy, 0.55), rnd.choice(flower_cols), outline=0.012,
                      segs=10, rings=5)
        for i, c in enumerate(('#FF6B8B', '#4FB0F0', '#FFD23F')):
            tube('PkString', [(cx + 1.7, cy, 2.8), (cx + 1.9 + 0.3 * i, cy - 0.2, 4.6 + 0.3 * i)], 0.015, metal)
            ellipsoid('PkBalloon', (0.38, 0.38, 0.48), (cx + 1.9 + 0.3 * i, cy - 0.2, 5.0 + 0.3 * i), toon(f'PkBal{i}', c),
                      outline=0.02)

        # lights: shadowless sky fill + front fill (the sun is added per-set in the episode)
        area_light((0, -2, 18), (0, 0, 0), 30, 2500, '#CFE8FF', 'PkSkyFill')
        area_light((0, -22, 8), (75, 0, 0), 16, 1800, '#FFF4E0', 'PkFront')
    return {'root': root, 'origin': origin, 'scoops': scoop_cols, 'cone': cone_m}
