"""Set: prehistoric jungle at night. One big tree with a thick sleeping branch, ferns,
vines, fireflies, background tree silhouettes, a huge moon.

Local layout: ground z=0. Trunk at (-3, 2). Sleeping branch runs along +X at z=BRANCH_Z,
from x=-3 to x=6, at y=BRANCH_Y. A sleeper lies on top (body along X).
"""
import math
import random
from toon import toon, box, ellipsoid, cylinder, cone, tube, point_light, area_light, SetBuilder

BRANCH_Z = 8.0
BRANCH_Y = 1.0


def build(origin=(0, 0, 0)):
    rnd = random.Random(8)
    with SetBuilder('Jungle', origin) as root:
        bark = toon('JBark', '#6B4A3A', tex=('planks', '#3E2A22', 0.35, 'wall'))
        leaf = toon('JLeaf', '#3E8A5A')
        leaf2 = toon('JLeaf2', '#2F6E52')
        leaf3 = toon('JLeaf3', '#5BA86A')
        grass = toon('JGround', '#3C6B4A', tex=('tiles', '#335C40', 2.5))
        far = toon('JFar', '#2C3B5E')
        far2 = toon('JFar2', '#3A4C70')
        sky = toon('JSky', '#2B3570', emit=True)
        moon = toon('JMoon', '#FFF1B8', emit=True)
        fly = toon('JFirefly', '#FFF27A', emit=True)
        vine = toon('JVine', '#4E7A3A')
        flower = toon('JFlower', '#E86A8A')

        box('JSkyCard', (140, 0.2, 80), (0, 45, 25), sky)
        cylinder('JMoonDisc', 7, 0.1, (8, 44, 24), moon, rot=(90, 0, 0))
        box('JGroundOb', (80, 60, 0.4), (0, 10, -0.2), grass)

        # hero tree: trunk, roots, sleeping branch, canopy
        tx, ty = -3.0, 2.0
        cone('JTrunk', 1.4, 0.9, 16, (tx, ty, 8), bark, outline=0.04, verts=24)
        for a in range(5):
            ang = a * 2 * math.pi / 5 + 0.3
            tube('JRoot', [(tx, ty, 1.2), (tx + 1.6 * math.cos(ang), ty + 1.6 * math.sin(ang), 0.4),
                           (tx + 2.4 * math.cos(ang), ty + 2.4 * math.sin(ang), 0.05)], 0.35, bark, outline=0.03)
        tube('JBranch', [(tx, BRANCH_Y, BRANCH_Z - 0.5), (1.0, BRANCH_Y, BRANCH_Z - 0.6), (4.5, BRANCH_Y, BRANCH_Z - 0.4),
                         (7.0, BRANCH_Y, BRANCH_Z + 0.2)], 0.55, bark, outline=0.04,
                         radii=[1.2, 1.0, 0.8, 0.5])
        tube('JTwig', [(5.5, BRANCH_Y, BRANCH_Z - 0.3), (6.5, BRANCH_Y - 0.6, BRANCH_Z + 1.4)], 0.15, bark, outline=0.02)
        for i in range(26):
            ellipsoid('JCanopy', (rnd.uniform(2.2, 3.4), rnd.uniform(1.8, 2.8), rnd.uniform(1.4, 2.2)),
                      (tx + rnd.uniform(-6, 9), ty + rnd.uniform(-1, 3), rnd.uniform(12.5, 17)),
                      rnd.choice((leaf, leaf2, leaf3)), outline=0.05, segs=20, rings=10)
        for i in range(6):           # leaf clumps on the branch tip
            ellipsoid('JTipLeaf', (0.9, 0.5, 0.25), (6.2 + rnd.uniform(-0.6, 0.8), BRANCH_Y + rnd.uniform(-0.6, 0.6),
                                                    BRANCH_Z + 1.2 + rnd.uniform(0, 0.9)), leaf3, outline=0.02).rotation_euler = (
                rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(0, 3))
        for i in range(7):           # hanging vines
            x = rnd.uniform(-8, 9)
            top = rnd.uniform(11.5, 13)
            tube('JVineOb', [(x, rnd.uniform(-1, 1), top), (x + 0.3, -0.5, top - 3), (x - 0.2, -0.3, top - 6.5)],
                 0.06, vine)

        # undergrowth: ferns, bushes, flowers, rocks
        for i in range(18):
            x, y = rnd.uniform(-14, 14), rnd.uniform(-6, 6)
            if -6 < x < 8 and y < 3:      # keep the fall area clear for the camera
                x += 14 if x > 1 else -14
            for k in range(5):
                a = k * 2 * math.pi / 5
                f = ellipsoid('JFern', (0.35, 1.5, 0.12), (x + 0.9 * math.sin(a), y + 0.9 * math.cos(a), 0.6),
                              rnd.choice((leaf, leaf3)), outline=0.02, segs=12, rings=6)
                f.rotation_euler = (0.6, 0, -a)
        for i in range(10):
            ellipsoid('JBush', (rnd.uniform(1.5, 2.6),) * 2 + (rnd.uniform(1.0, 1.6),),
                      (rnd.uniform(-16, 16), rnd.uniform(4, 12), 0.8), rnd.choice((leaf2, leaf)), outline=0.04,
                      segs=16, rings=8)
        for i in range(8):
            ellipsoid('JFlowerOb', (0.22, 0.22, 0.15), (rnd.uniform(-10, 10), rnd.uniform(-6, 2), 1.3), flower,
                      outline=0.015, segs=10, rings=5)
        rock = toon('JRock', '#6E6A86')
        for i in range(5):
            ellipsoid('JRockOb', (rnd.uniform(0.8, 1.5), 1.0, 0.6), (rnd.uniform(-10, 10), rnd.uniform(-5, 0), 0.3), rock,
                      outline=0.03, segs=12, rings=6)

        # background tree silhouettes (two depth layers)
        for layer, (mat, y0) in enumerate(((far2, 16), (far, 26))):
            for i in range(9):
                x = -36 + i * 9 + rnd.uniform(-2, 2)
                h = rnd.uniform(12, 20)
                cylinder('JFarTrunk', 0.7, h, (x, y0, h / 2), mat)
                for k in range(3):
                    ellipsoid('JFarLeaf', (rnd.uniform(3, 4.5),) * 2 + (2.4,), (x + rnd.uniform(-2, 2), y0, h + rnd.uniform(-1, 2)),
                              mat, segs=16, rings=8)

        # fireflies
        for i in range(24):
            ellipsoid('JFly', (0.07, 0.07, 0.07), (rnd.uniform(-12, 12), rnd.uniform(-4, 6), rnd.uniform(1, 10)), fly,
                      segs=6, rings=3)

        area_light((14, -8, 20), (40, 25, 0), 3.0, 9000, '#B8C8FF', 'JMoonKey')
        area_light((0, -26, 9), (78, 0, 0), 16, 1500, '#7E8AD8', 'JFront')
        point_light((2, -3, 5), 120, '#FFF27A', 2.0, 'JFlyGlow')
    return {'root': root, 'origin': origin}
