"""Set: a cut-away slice of skin, seen from the side, with tiny sensor workers.

The layered 'wall' (epidermis / dermis / fat) stands at y=2. Workers stand on a
ledge in front of it (floor z=0). The skin surface is the top of the wall
(z=7.5) with hairs and water drops on it. Sky behind.
Props: thermometer (left), graph screen (right), ice cubes (start hidden above).
"""
import math
import random
from toon import (toon, glassy, box, ellipsoid, cylinder, cone, tube, area_light, point_light,
                  text_obj, SetBuilder)

TOP = 7.5


def build(origin=(0, 0, 0)):
    rnd = random.Random(4)
    with SetBuilder('SkinLayer', origin) as root:
        epi = toon('Epidermis', '#F8CDAE')
        derm = toon('Dermis', '#F29C9C', tex=('brick', '#E48888', 1.4, 0.7, 'wall'))
        fat = toon('Fat', '#F7D77A', tex=('brick', '#E9C25F', 1.0, 0.8, 'wall'))
        ledge = toon('Ledge', '#E98A8A')
        hair = toon('HairStrand', '#4A3426')
        nerve = toon('Nerve', '#FFE58A', emit=True)
        sky = toon('SkinSky', '#BFE6FF', emit=True)
        drop = glassy('Drop', '#9ED8FF', alpha=0.75, emit_strength=0.2)
        ice = glassy('Ice', '#D9F4FF', alpha=0.8, emit_strength=0.25)
        glass = glassy('ThermoGlass', '#FFFFFF', alpha=0.35)
        red = toon('ThermoRed', '#E8393C')
        white = toon('Board', '#FAFAFA')
        dark = toon('GraphBg', '#1D2A44', emit=True)
        graph = toon('GraphLine', '#FF4D4D', emit=True)
        grid = toon('GraphGrid', '#35507A', emit=True)
        lbl = toon('LabelTxt', '#2A2230')

        # sky backdrop far behind
        box('Sky', (60, 0.2, 40), (0, 30, 12), sky)
        # the skin slice: layers stacked, front face at y=1.5
        box('Fat', (26, 2.0, 2.4), (0, 2.5, 1.2), fat)
        box('Dermis', (26, 2.0, 3.9), (0, 2.5, 4.35), derm)
        box('Epidermis', (26, 2.0, 1.2), (0, 2.5, 6.9), epi)
        box('Ledge', (26, 4.0, 0.3), (0, -0.5, -0.15), ledge)
        # glowing nerve lines running through the dermis
        for i in range(4):
            x0 = -9 + i * 5.5
            pts = [(x0 + 0.6 * math.sin(k), 1.45, 2.6 + 0.7 * k) for k in range(6)]
            tube(f'Nerve{i}', pts, 0.07, nerve)
        # hairs + water drops on the surface
        for i in range(9):
            x = -11 + i * 2.7 + rnd.uniform(-0.4, 0.4)
            tube(f'Hair{i}', [(x, 2.3, TOP - 0.8), (x + 0.15, 2.2, TOP + 0.6), (x + 0.6, 2.0, TOP + 1.8)], 0.07, hair)
        for i in range(10):
            x = -11 + i * 2.4 + rnd.uniform(-0.5, 0.5)
            r = rnd.uniform(0.3, 0.5)
            ellipsoid(f'Drop{i}', (r, r, r * 0.7), (x, 2.0, TOP + r * 0.5), drop, outline=0.02)

        # thermometer (left)
        cylinder('ThermoTube', 0.32, 4.0, (-6.5, 0.6, 2.6), glass, outline=0.03)
        ellipsoid('ThermoBulb', (0.55, 0.55, 0.55), (-6.5, 0.6, 0.55), red, outline=0.03)
        cylinder('ThermoLiquid', 0.16, 0.8, (-6.5, 0.6, 1.2), red)
        for k in range(7):
            box(f'ThermoTick{k}', (0.3, 0.04, 0.05), (-6.12, 0.45, 1.3 + 0.5 * k), lbl)
        ellipsoid('Snowflake', (0.35, 0.05, 0.35), (-5.6, 0.4, 4.6), toon('Snow', '#BEE7FF'), outline=0.02)

        # graph screen (right): temperature line plunging
        box('GraphFrame', (4.4, 0.25, 3.2), (6.2, 0.9, 3.6), white)
        box('GraphScreen', (4.0, 0.1, 2.8), (6.2, 0.75, 3.6), dark)
        for k in range(5):
            box(f'GridH{k}', (3.8, 0.04, 0.03), (6.2, 0.68, 2.5 + 0.55 * k), grid)
        pts = [(4.4, 0.62, 4.6), (5.1, 0.62, 4.55), (5.8, 0.62, 4.45), (6.3, 0.62, 3.2), (6.8, 0.62, 2.45), (7.9, 0.62, 2.35)]
        tube('GraphLine', pts, 0.06, graph)
        arrow = cone('GraphArrow', 0.35, 0.0, 0.6, (6.55, 0.55, 2.0), graph, rot=(180, 0, 0))
        text_obj('GraphLbl', 'TEMP', 0.35, (6.2, 0.6, 4.75), toon('GraphTxt', '#9FC4FF', emit=True))

        # ice cubes (start high above, dropped later)
        cubes = []
        for i in range(4):
            c = box(f'IceCube{i}', (1.1, 1.1, 1.1), (-1.5 + 1.3 * i, 2.0, TOP + 14), ice)
            c.rotation_euler = (rnd.uniform(0, 1), rnd.uniform(0, 1), rnd.uniform(0, 1))
            cubes.append(c)

        area_light((0, -9, 7), (70, 0, 0), 10.0, 1400, '#FFF5EE', 'SkinFront')
        area_light((0, -1, 13), (0, 0, 0), 10.0, 900, '#FFFFFF', 'SkinTop')
        point_light((0, 0.5, 3.5), 300, '#FFD0C0', 3.0, 'SkinWarm')
    return {'root': root, 'cubes': cubes, 'arrow': arrow, 'origin': origin, 'top': TOP}
