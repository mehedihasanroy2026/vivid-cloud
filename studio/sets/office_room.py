"""Set: small office with brick walls, tiled floor, desk, chair, clock, cabinet, plant.

Room interior: x -6..6, y -9..6, floor z=0, ceiling z=10.
A window in the right wall lets warm sun fall across the back wall.
"""
import math
from mathutils import Vector
from toon import toon, box, ellipsoid, cylinder, tube, empty, sun, area_light, hexcol

OUT = 0.03          # outline thickness for props


def build():
    wall = toon('Brick', '#86C98F', tex=('brick', '#6DAF78', 0.9, 0.34, 'wall'))
    floor = toon('Tiles', '#93A8CC', tex=('tiles', '#7286AA', 1.3))
    ceil = toon('Ceiling', '#EEF0F2')
    trim = toon('Trim', '#5E9F6A')
    desk = toon('Desk', '#C9D0DB')
    desk_dark = toon('DeskSide', '#A7B0BE')
    ink = toon('Ink', '#2A2230')
    chair = toon('Chair', '#4F7FC2')
    white = toon('White', '#FAFAFA')
    red = toon('ClockRed', '#D8433A')
    cab = toon('Cabinet', '#8E9AAB')
    pot = toon('Pot', '#C9693C')
    leaf = toon('Leaf', '#4FAE5A')
    paper = toon('Paper', '#FFF8E6')
    cork = toon('Cork', '#C79A5B')
    glass = toon('WinGlass', '#DDF3FF', emit=True)
    note_cols = [toon(f'Note{i}', c) for i, c in enumerate(('#FFD84D', '#FF8FA3', '#7FD3FF', '#9BE58C'))]

    # shell
    box('Floor', (12.4, 15.4, 0.2), (0, -1.5, -0.1), floor)
    box('BackWall', (12.4, 0.3, 10.4), (0, 6.15, 5), wall)
    box('LeftWall', (0.3, 15.4, 10.4), (-6.15, -1.5, 5), wall)
    box('Ceiling', (12.4, 15.4, 0.2), (0, -1.5, 10.1), ceil)
    # right wall with a window hole (y 0.5..3.5, z 3.5..7.5)
    box('RW_a', (0.3, 9.5, 10.4), (6.15, -4.25, 5), wall)
    box('RW_b', (0.3, 2.5, 10.4), (6.15, 4.75, 5), wall)
    box('RW_c', (0.3, 3.0, 3.5), (6.15, 2.0, 1.75), wall)
    box('RW_d', (0.3, 3.0, 2.5), (6.15, 2.0, 8.75), wall)
    box('WinBar', (0.2, 0.15, 4.0), (6.1, 2.0, 5.5), white)
    box('WinBarH', (0.2, 3.0, 0.15), (6.1, 2.0, 5.5), white)
    # baseboards
    box('Base_back', (12.4, 0.12, 0.35), (0, 5.95, 0.17), trim)
    box('Base_left', (0.12, 15.4, 0.35), (-5.95, -1.5, 0.17), trim)

    # desk (right of the character) with a drawer pedestal
    DX, DY = 2.6, 0.9
    box('DeskTop', (3.6, 1.8, 0.16), (DX, DY, 2.62), desk)
    box('DeskPed', (1.2, 1.7, 2.54), (DX - 1.15, DY, 1.27), desk_dark)
    for i, z in enumerate((2.05, 1.3, 0.55)):
        box(f'Drawer{i}', (1.08, 0.06, 0.62), (DX - 1.15, DY - 0.87, z), desk)
        box(f'Handle{i}', (0.5, 0.06, 0.07), (DX - 1.15, DY - 0.92, z + 0.12), ink)
    for x in (DX + 1.65,):
        for y in (DY - 0.75, DY + 0.75):
            box('DeskLeg', (0.14, 0.14, 2.54), (x, y, 1.27), desk_dark)
    # things on the desk
    box('Laptop', (1.0, 0.7, 0.06), (DX + 0.6, DY + 0.1, 2.74), cab)
    box('LaptopScreen', (1.0, 0.06, 0.68), (DX + 0.6, DY + 0.45, 3.08), ink)
    cylinder('Mug', 0.17, 0.36, (DX - 0.6, DY - 0.3, 2.88), white, outline=0.02)
    box('Papers', (0.7, 0.9, 0.08), (DX - 0.2, DY + 0.3, 2.74), paper)

    # chair behind the desk
    box('ChairSeat', (1.1, 1.0, 0.18), (DX + 0.6, DY + 1.6, 1.6), chair)
    box('ChairBack', (1.1, 0.16, 1.3), (DX + 0.6, DY + 2.1, 2.4), chair)
    cylinder('ChairPole', 0.07, 1.4, (DX + 0.6, DY + 1.6, 0.8), ink)

    # wall clock
    clock = cylinder('Clock', 0.75, 0.16, (-0.3, 5.92, 7.6), white, rot=(90, 0, 0))
    cylinder('ClockRim', 0.85, 0.12, (-0.3, 5.98, 7.6), red, rot=(90, 0, 0))
    box('HandH', (0.08, 0.04, 0.42), (-0.3, 5.82, 7.75), ink).rotation_euler = (0, math.radians(-60), 0)
    box('HandM', (0.06, 0.04, 0.6), (-0.3, 5.81, 7.85), ink)
    for k in range(12):
        a = k * math.pi / 6
        box(f'Tick{k}', (0.05, 0.03, 0.12), (-0.3 + 0.6 * math.sin(a), 5.83, 7.6 + 0.6 * math.cos(a)), ink).rotation_euler = (0, a, 0)

    # cork board with notes
    box('Cork', (2.4, 0.1, 1.6), (3.0, 5.95, 6.2), cork)
    for i, (x, z) in enumerate(((2.3, 6.5), (3.0, 6.0), (3.7, 6.45), (2.6, 5.8), (3.6, 5.75))):
        box(f'Note{i}', (0.5, 0.04, 0.5), (x, 5.88, z), note_cols[i % 4])

    # filing cabinet, left back
    box('Cabinet', (1.5, 1.4, 3.6), (-4.8, 4.9, 1.8), cab)
    for i, z in enumerate((3.0, 1.8, 0.6)):
        box(f'CabDrawer{i}', (1.36, 0.06, 1.0), (-4.8, 4.18, z), toon('CabFront', '#A3AEBD'))
        box(f'CabHandle{i}', (0.5, 0.06, 0.08), (-4.8, 4.13, z + 0.2), ink)

    # plant
    cylinder('PlantPot', 0.45, 0.9, (-4.8, 1.5, 0.45), pot, outline=OUT)
    for i, (x, y, z, r) in enumerate([(-4.8, 1.5, 1.5, 0.6), (-5.15, 1.4, 2.1, 0.45), (-4.45, 1.6, 2.2, 0.45), (-4.8, 1.5, 2.6, 0.4)]):
        ellipsoid(f'Leaf{i}', (r, r, r * 1.15), (x, y, z), leaf, outline=OUT)

    # light: warm sun through the window, cool sky fill, soft ceiling panel
    d = Vector((-0.62, 0.62, -0.48)).normalized()
    s = sun(strength=5.5, hexc='#FFD873', angle=1.5)
    s.rotation_euler = (-d).to_track_quat('Z', 'Y').to_euler()
    area_light((0, -1, 9.8), (0, 0, 0), 6.0, 700, '#FFF8EE', 'CeilingPanel')
    area_light((1, -9, 6), (75, 0, 0), 5.0, 500, '#FFFFFF', 'FrontFill')
    return {'desk': (DX, DY, 2.7)}
