"""Set: cutaway house - living room (x<0) | wall with doorway | kitchen (x>0).

No front wall / ceiling (dollhouse view). Divider wall at x=0 runs along Y with a
door opening at y -2.0..0.0 (centre DOOR_Y=-1.0). The door has sneaky cartoon eyes.
Door hinge at (0, 0); closed = in the wall plane, open into the kitchen = +90 deg.
A "NEW SCENE!" sign hangs above the door on the living-room side (pop it in).
"""
import math
import bpy
from toon import (toon, glassy, box, ellipsoid, cylinder, cone, tube, area_light, point_light,
                  text_obj, SetBuilder, empty)

DOOR_Y = -1.0


def build(origin=(0, 0, 0)):
    with SetBuilder('House', origin) as root:
        lr_wall = toon('LRWall', '#F3D9A8', tex=('tiles', '#EBCB93', 1.4, 'wall'))
        k_wall = toon('KWall', '#BFE6D4')
        splash = toon('Backsplash', '#8FD3C1', tex=('tiles', '#E8F7F2', 0.55, 'wall'))
        divider = toon('Divider', '#EFD2A0')
        wood = toon('WoodFloor', '#C98B5A', tex=('brick', '#A9703F', 3.0, 0.6, 'floor'))
        ktile = toon('KitchenFloor', '#E9E2D0', tex=('tiles', '#B9AE96', 1.1))
        trim = toon('TrimWhite', '#FAF7F0')
        door_c = toon('DoorWood', '#B5784A')
        sofa = toon('Sofa', '#D9534F')
        cushion = toon('Cushion', '#F2C14E')
        rug = toon('LRRug', '#5DA9E9')
        shelf = toon('Shelf', '#8C5A3C')
        book_cols = [toon(f'Book{i}', c) for i, c in enumerate(('#E4572E', '#29A19C', '#F3A712', '#6C5CE7', '#2E86DE'))]
        lamp_shade = glassy('LampShade', '#FFE3A3', alpha=1.0, emit_strength=1.2)
        metal = toon('Metal', '#3A3F4B')
        cab = toon('KCabinet', '#F7F4EC')
        counter = toon('Counter', '#4A4E57')
        fridge = toon('Fridge', '#BFD7EA')
        steel = toon('Steel', '#C3CCD6', rough=0.3)
        ink = toon('Ink', '#2A2230')
        white = toon('FaceWhite', '#FFFFFF')
        fruit = [toon('Apple', '#E8393C'), toon('Banana', '#FFD43B'), toon('Orange', '#FF8A1F')]
        frame_c = toon('PicFrame', '#6B4A33')
        pic_cols = [toon('Pic0', '#7FC8F8', emit=True), toon('Pic1', '#FFB4A2', emit=True)]
        sign_bg = toon('SignBlack', '#1E1E24')
        sign_txt = toon('SignYellow', '#FFD23F', emit=True)

        # floors + back walls
        box('LRFloor', (10.2, 12, 0.2), (-5.1, -1, -0.1), wood)
        box('KFloor', (10.2, 12, 0.2), (5.1, -1, -0.1), ktile)
        box('LRBack', (10.2, 0.3, 9), (-5.1, 5.15, 4.5), lr_wall)
        box('KBack', (10.2, 0.3, 9), (5.1, 5.15, 4.5), k_wall)
        box('Splash', (8.2, 0.05, 2.6), (5.3, 4.98, 4.1), splash)
        # divider wall with door opening y -2..0, z 0..7
        box('DivFront', (0.35, 1.0, 9), (0, -2.5, 4.5), divider)
        box('DivBack', (0.35, 5.0, 9), (0, 2.5, 4.5), divider)
        box('DivTop', (0.35, 2.0, 2.0), (0, DOOR_Y, 8.0), divider)
        for y in (-2.05, 0.05):
            box('DoorTrim', (0.5, 0.18, 7.1), (0, y, 3.55), trim)
        box('DoorTrimTop', (0.5, 2.3, 0.18), (0, DOOR_Y, 7.05), trim)
        # the door (hinge at y=0), eyes on the living-room face
        hinge = empty('DoorHinge', (0, 0.0, 0))
        hinge.parent = None
        box('DoorLeaf', (0.14, 2.0, 6.9), (0, -1.0, 3.45), door_c, hinge)
        for k, z in enumerate((1.6, 5.0)):
            box(f'DoorPanel{k}', (0.03, 1.5, 2.4 if k else 2.2), (-0.085, -1.0, z), toon('DoorPanel', '#A06A40'), hinge)
        ellipsoid('Knob', (0.12, 0.12, 0.12), (-0.15, -1.75, 3.3), steel, hinge, outline=0.015)
        eyes = []
        for s, y in ((1, -0.6), (-1, -1.4)):
            e = ellipsoid(f'DoorEye{s}', (0.06, 0.32, 0.26), (-0.09, y, 5.3), white, hinge, outline=0.03)
            p = ellipsoid(f'DoorPupil{s}', (0.04, 0.12, 0.12), (-0.04, 0.0, -0.02), ink, e)
            eyes.append(p)
            brow = box(f'DoorBrow{s}', (0.05, 0.5, 0.09), (-0.1, y, 5.72), ink, hinge)
            brow.rotation_euler = (math.radians(22 * s), 0, 0)   # inner ends down = sneaky
        # "NEW SCENE!" sign above the door (living-room side), clapperboard style
        sign = empty('SceneSign', (-0.35, DOOR_Y, 8.4))
        sign.parent = None
        box('SignBoard', (0.12, 3.8, 1.25), (0, 0, 0), sign_bg, sign)
        for k in range(5):
            st = box(f'SignStripe{k}', (0.13, 0.28, 0.35), (0, -1.6 + 0.8 * k, 0.8), white if k % 2 else sign_bg, sign)
            st.rotation_euler = (math.radians(25), 0, 0)
        text_obj('SignText', 'NEW SCENE!', 0.62, (-0.1, 0, -0.05), sign_txt, rot=(90, 0, -90), parent=sign)

        # living room
        box('SofaBase', (3.8, 1.5, 1.2), (-5.6, 3.6, 0.6), sofa)
        box('SofaBack', (3.8, 0.45, 1.6), (-5.6, 4.35, 1.6), sofa)
        for s in (1, -1):
            box('SofaArm', (0.4, 1.5, 1.6), (-5.6 + s * 2.0, 3.6, 0.9), sofa)
        for k in range(2):
            ellipsoid(f'Cushion{k}', (0.55, 0.25, 0.5), (-6.4 + 1.6 * k, 4.0, 1.75), cushion, outline=0.02)
        cylinder('LRRug', 2.6, 0.04, (-5.0, 0.6, 0.02), rug)
        box('CoffeeTable', (2.2, 1.1, 0.12), (-5.4, 1.6, 1.0), shelf)
        for x in (-6.3, -4.5):
            box('CTLeg', (0.12, 0.12, 0.95), (x, 1.6, 0.48), shelf)
        box('Remote', (0.25, 0.6, 0.08), (-5.0, 1.5, 1.1), ink)
        box('Bookshelf', (1.8, 1.0, 5.2), (-8.8, 4.4, 2.6), shelf)
        for r_ in range(3):
            for b in range(5):
                box(f'Book{r_}{b}', (0.22, 0.7, 0.9 + 0.1 * (b % 3)), (-9.45 + 0.3 * b, 4.25, 1.15 + 1.6 * r_ + 0.05 * (b % 3)),
                    book_cols[(b + r_) % 5])
        cylinder('LampPole', 0.06, 5.0, (-2.4, 4.2, 2.5), metal)
        cone('LampShade', 0.75, 0.45, 0.9, (-2.4, 4.2, 5.3), lamp_shade, outline=0.02)
        for k, x in enumerate((-7.2, -4.0)):
            box(f'Pic{k}', (1.6, 0.1, 1.2), (x, 4.95, 6.0), frame_c)
            box(f'PicIn{k}', (1.3, 0.06, 0.9), (x, 4.9, 6.0), pic_cols[k])

        # kitchen
        box('Cabinets', (8.2, 1.6, 2.6), (5.3, 4.15, 1.3), cab)
        box('Countertop', (8.4, 1.8, 0.2), (5.3, 4.05, 2.7), counter)
        for k in range(5):
            box(f'CabDoor{k}', (1.45, 0.05, 2.1), (1.95 + 1.65 * k, 3.33, 1.25), toon('CabDoor', '#EDE8DC'))
            box(f'CabKnob{k}', (0.08, 0.06, 0.3), (2.5 + 1.65 * k, 3.29, 1.9), steel)
        box('UpperCab', (6.0, 1.0, 2.0), (4.2, 4.5, 6.6), cab)
        for k in range(3):
            box(f'UpDoor{k}', (1.85, 0.05, 1.7), (2.2 + 2.0 * k, 3.98, 6.6), toon('CabDoor', '#EDE8DC'))
        box('Fridge', (2.0, 1.8, 6.6), (9.0, 4.0, 3.3), fridge)
        box('FridgeHandle', (0.1, 0.12, 1.6), (8.2, 3.05, 4.4), steel)
        box('FridgeLine', (2.0, 0.04, 0.05), (9.0, 3.08, 4.9), ink)
        box('Stove', (1.8, 1.2, 0.08), (5.7, 4.0, 2.84), metal)
        for k in range(4):
            cylinder(f'Burner{k}', 0.25, 0.04, (5.25 + 0.9 * (k % 2), 3.75 + 0.55 * (k // 2), 2.9), ink)
        box('SinkHole', (1.6, 1.0, 0.06), (2.8, 4.0, 2.82), steel)
        tube('KTap', [(2.8, 4.7, 2.8), (2.8, 4.7, 3.5), (2.8, 4.25, 3.6)], 0.06, steel)
        # table with fruit
        box('KTable', (3.0, 1.8, 0.15), (5.0, -1.6, 2.4), shelf)
        for x in (3.7, 6.3):
            for y in (-2.3, -0.9):
                box('KTLeg', (0.14, 0.14, 2.35), (x, y, 1.18), shelf)
        ellipsoid('Bowl', (0.55, 0.55, 0.25), (5.0, -1.6, 2.6), white, outline=0.02)
        for k, (dx, dy) in enumerate(((-0.2, 0), (0.2, 0.1), (0, -0.2))):
            ellipsoid(f'Fruit{k}', (0.2, 0.2, 0.2), (5.0 + dx, -1.6 + dy, 2.85), fruit[k], outline=0.015)
        # hanging lamp
        tube('Cord', [(5.0, -1.6, 9.5), (5.0, -1.6, 7.6)], 0.03, ink)
        cone('HangLamp', 0.8, 0.15, 0.6, (5.0, -1.6, 7.4), toon('HangLampCol', '#2E9E6B'), outline=0.02)

        area_light((0, -2, 10), (0, 0, 0), 14, 1500, '#FFF6EA', 'HouseTop')
        area_light((0, -14, 6), (75, 0, 0), 12, 1300, '#FFFFFF', 'HouseFront')
        point_light((-2.4, 3.8, 5.0), 250, '#FFD9A0', 0.5, 'LampGlow')
        point_light((5.0, -1.6, 6.8), 250, '#FFF1D6', 0.4, 'HangGlow')
    return {'root': root, 'hinge': hinge, 'eyes': eyes, 'sign': sign, 'origin': origin}
