"""Set: cosy bedroom at night (EP03 hypnic jerk). Built to the 'pro look' standard:
closed room (no void in shot), every surface textured, lots of props, warm lamp vs cool moonlight.

Local layout: room x -6..6, y -11..4.5, floor z=0, ceiling z=9. Front (-Y) open for cameras.
Bed against the back wall, headboard at y=4, foot toward -Y. Sleeper sits/lies at BED_SPOT.
Returns handles: lamp light + shade (switch on/off), phone screen, clock text, moon light.
"""
import math
import random
from toon import (toon, glassy, box, ellipsoid, cylinder, cone, tube, area_light, point_light,
                  text_obj, SetBuilder, empty)

BED_X, BED_Y = 1.2, 0.6          # mattress centre
MATTRESS_TOP = 1.75
BED_SPOT = (BED_X, 2.6)           # where the sleeper's hips go (near the pillow)


def build(origin=(0, 0, 0)):
    rnd = random.Random(3)
    with SetBuilder('Bedroom', origin) as root:
        wallpaper = toon('BRWallpaper', '#7D78A8', tex=('stripes', '#716C9C', 0.5, 'x'))
        wainscot = toon('BRWainscot', '#5E5580', tex=('planks', '#3A3152', 0.55, 'wall'))
        floor = toon('BRFloor', '#9A6440', tex=('planks', '#4A2C1C', 0.7, 'floor'))
        ceil = toon('BRCeil', '#655E8C')
        trim = toon('BRTrim', '#E9E1CF')
        wood = toon('BRWood', '#8A5534', tex=('planks', '#4A2C1C', 0.5, 'wall'))
        wood_dk = toon('BRWoodDark', '#5E3A24')
        sheet = toon('BRSheet', '#EDEBE4')
        pillow = toon('BRPillow', '#F6F2E8')
        quilt = toon('BRQuilt', '#C94F4F', tex=('patch', ['#B85A4E', '#D9A050', '#5E86B0', '#78A06A',
                                                          '#8C6AA8', '#D08A8A', '#E6CB7A'], 0.6))
        rug = toon('BRRug', '#B8434F', tex=('stripes', '#E4B65C', 0.35, 'x'))
        shade = glassy('BRLampShade', '#FFD58A', alpha=1.0, emit_strength=2.5)
        brass = toon('BRBrass', '#C9A04A', rough=0.35)
        ink = toon('Ink', '#2A2230')
        white = toon('FaceWhite', '#FFFFFF')
        clock_body = toon('BRClockBody', '#2F3A5C')
        clock_face = toon('BRClockFace', '#101418', emit=False)
        red_led = toon('BRClockLED', '#FF4A3D', emit=True)
        phone_body = toon('BRPhone', '#1C1F2B')
        phone_glow = toon('BRPhoneScreen', '#9FD3FF', emit=True)
        glass = glassy('BRGlass', '#CFEFFF', alpha=0.35)
        night = toon('BRNightSky', '#1B2552', emit=True)
        moon = toon('BRMoon', '#FFF4C8', emit=True)
        star = toon('BRStar', '#FFFFFF', emit=True)
        curtain = toon('BRCurtain', '#2F7F7A', tex=('stripes', '#28706C', 0.25, 'x'))
        frame_c = toon('BRFrame', '#C9A04A')
        poster = toon('BRPoster', '#E8A33D', emit=False)
        book_cols = [toon(f'BRBook{i}', c) for i, c in enumerate(
            ('#C94F4F', '#4F8FC9', '#E8A33D', '#6DB36B', '#8E5BB5', '#E07A9B', '#3E9C9C'))]
        slipper = toon('BRSlipper', '#7A9BD8')
        plant = toon('BRPlant', '#4E9B5A')
        pot = toon('BRPot', '#C46A44')

        # ---- shell (closed room: back, left, right walls + ceiling) ----
        box('BRFloor', (12.4, 15.8, 0.2), (0, -3.3, -0.1), floor)
        box('BRCeiling', (12.4, 15.8, 0.2), (0, -3.3, 9.1), ceil)
        box('BRBack', (12.4, 0.3, 9.4), (0, 4.6, 4.6), wallpaper)
        box('BRLeft', (0.3, 15.8, 9.4), (-6.15, -3.3, 4.6), wallpaper)
        box('BRRight', (0.3, 15.8, 9.4), (6.15, -3.3, 4.6), wallpaper)
        for nm, size, loc in (('BRWainB', (12.0, 0.08, 2.4), (0, 4.42, 1.2)),
                              ('BRWainL', (0.08, 15.4, 2.4), (-5.97, -3.3, 1.2)),
                              ('BRWainR', (0.08, 15.4, 2.4), (5.97, -3.3, 1.2))):
            box(nm, size, loc, wainscot)
        box('BRRailB', (12.0, 0.16, 0.14), (0, 4.38, 2.42), trim)
        box('BRRailL', (0.16, 15.4, 0.14), (-5.93, -3.3, 2.42), trim)
        box('BRRailR', (0.16, 15.4, 0.14), (5.93, -3.3, 2.42), trim)
        box('BRSkirtB', (12.0, 0.14, 0.3), (0, 4.38, 0.15), trim)
        box('BRCrown', (12.0, 0.25, 0.25), (0, 4.35, 8.88), trim)

        # ---- window on the left wall: night sky, moon, stars, curtains ----
        wy, wz = -0.6, 5.4
        box('BRWinSky', (0.05, 3.6, 3.4), (-6.0, wy, wz), night)
        cylinder('BRMoonDisc', 0.55, 0.03, (-5.96, wy + 0.9, wz + 0.8), moon, rot=(0, 90, 0))
        for i in range(9):
            ellipsoid(f'BRStar{i}', (0.03, 0.05, 0.05),
                      (-5.96, wy - 1.5 + rnd.random() * 3.0, wz - 1.4 + rnd.random() * 2.8), star, segs=8, rings=4)
        for dy in (-1.85, 0.0, 1.85):
            box('BRWinV', (0.2, 0.14, 3.7), (-5.92, wy + dy, wz), trim)
        for dz in (-1.75, 0.0, 1.75):
            box('BRWinH', (0.2, 3.84, 0.14), (-5.92, wy, wz + dz), trim)
        box('BRSill', (0.6, 4.3, 0.16), (-5.75, wy, wz - 1.85), trim)
        tube('BRCurtainRod', [(-5.6, wy - 2.8, wz + 2.2), (-5.6, wy + 2.8, wz + 2.2)], 0.05, brass)
        for s in (-1, 1):
            for i in range(4):
                ellipsoid(f'BRPleat{s}{i}', (0.18, 0.2, 2.4),
                          (-5.62 + 0.04 * (i % 2), wy + s * (2.2 + 0.28 * i), wz - 0.1), curtain, outline=0.02)

        # ---- bed: frame, headboard, mattress, quilt, pillows ----
        bx, by = BED_X, BED_Y
        box('BRBedBase', (4.6, 7.2, 0.9), (bx, by, 0.75), wood, bevel=0.05)
        for dx in (-2.15, 2.15):
            box('BRBedLegF', (0.3, 0.3, 0.4), (bx + dx, by - 3.45, 0.2), wood_dk)
        box('BRHeadboard', (4.9, 0.35, 3.6), (bx, 4.15, 1.8), wood, bevel=0.06)
        for dx in (-2.45, 2.45):
            cylinder('BRPost', 0.2, 4.2, (bx + dx, 4.15, 2.1), wood_dk, outline=0.02)
            ellipsoid('BRPostKnob', (0.26, 0.26, 0.26), (bx + dx, 4.15, 4.35), wood_dk, outline=0.02)
        box('BRFootboard', (4.9, 0.3, 1.9), (bx, by - 3.65, 0.95), wood, bevel=0.05)
        box('BRMattress', (4.3, 7.0, 0.6), (bx, by, 1.45), sheet, bevel=0.12)
        for dx in (-1.05, 1.05):
            ellipsoid('BRPillow', (0.95, 0.55, 0.32), (bx + dx, 3.35, 2.05), pillow, outline=0.03)
        # quilt drapes over the lower two-thirds and down the sides
        box('BRQuiltTop', (4.5, 5.0, 0.22), (bx, by - 1.0, 1.86), quilt, bevel=0.08)
        box('BRQuiltSideL', (0.12, 5.0, 0.9), (bx - 2.25, by - 1.0, 1.4), quilt)
        box('BRQuiltSideR', (0.12, 5.0, 0.9), (bx + 2.25, by - 1.0, 1.4), quilt)
        box('BRQuiltFold', (4.5, 0.5, 0.3), (bx, by + 1.4, 1.95), sheet, bevel=0.1)

        # ---- nightstand left of the bed: lamp, alarm clock, phone, water glass ----
        nx, ny = -2.2, 3.4
        box('BRStand', (1.8, 1.5, 2.0), (nx, ny, 1.0), wood, bevel=0.05)
        box('BRDrawer', (1.5, 0.05, 0.6), (nx, ny - 0.76, 1.35), wood_dk)
        ellipsoid('BRKnob', (0.08, 0.06, 0.08), (nx, ny - 0.8, 1.35), brass)
        cylinder('BRLampBase', 0.32, 0.12, (nx - 0.35, ny + 0.2, 2.06), brass, outline=0.015)
        cylinder('BRLampStem', 0.05, 1.1, (nx - 0.35, ny + 0.2, 2.6), brass)
        lamp_shade = cone('BRLampShadeOb', 0.6, 0.35, 0.75, (nx - 0.35, ny + 0.2, 3.3), shade, outline=0.025)
        box('BRClock', (0.7, 0.35, 0.42), (nx + 0.35, ny - 0.25, 2.21), clock_body, bevel=0.06)
        box('BRClockFace', (0.58, 0.02, 0.3), (nx + 0.35, ny - 0.43, 2.22), clock_face)
        clock_txt = text_obj('BRClockTxt', '3:00', 0.22, (nx + 0.35, ny - 0.45, 2.22), red_led, extrude=0.005)
        phone = box('BRPhoneBody', (0.32, 0.6, 0.04), (nx + 0.45, ny + 0.35, 2.02), phone_body)
        phone.rotation_euler = (0, 0, math.radians(-20))
        scr = box('BRPhoneScr', (0.27, 0.52, 0.01), (0, 0, 0.025), phone_glow, parent=phone)
        cylinder('BRGlassOb', 0.13, 0.4, (nx - 0.7, ny - 0.4, 2.2), glass, outline=0.012)

        # ---- right side: bookshelf, poster, plant ----
        sx = 4.9
        box('BRShelfBack', (1.6, 0.2, 5.2), (sx, 4.3, 2.6), wood)
        for z in (0.2, 1.5, 2.8, 4.1, 5.2):
            box('BRShelfBoard', (1.6, 1.2, 0.12), (sx, 3.8, z), wood_dk)
        for side in (-0.8, 0.8):
            box('BRShelfSide', (0.12, 1.2, 5.2), (sx + side, 3.8, 2.6), wood_dk)
        for row, z in enumerate((0.26, 1.56, 2.86, 4.16)):
            x = sx - 0.68
            while x < sx + 0.6:
                w = rnd.uniform(0.12, 0.2)
                h = rnd.uniform(0.75, 1.1)
                tilt = math.radians(rnd.choice((0, 0, 0, 8)))
                b = box('BRBook', (w, 0.85, h), (x + w / 2, 3.85, z + h / 2), rnd.choice(book_cols))
                b.rotation_euler = (0, tilt, 0)
                x += w + 0.02
            if row == 1:
                break
        cylinder('BRPotOb', 0.35, 0.6, (sx, 3.8, 3.15), pot, outline=0.015)
        for i in range(6):
            a = i * math.pi / 3
            ellipsoid(f'BRLeaf{i}', (0.16, 0.16, 0.5), (sx + 0.25 * math.cos(a), 3.8 + 0.25 * math.sin(a), 3.75),
                      plant, outline=0.015).rotation_euler = (0.5 * math.sin(a), 0.5 * math.cos(a), 0)
        box('BRPosterFrame', (2.0, 0.08, 2.6), (-2.6, 4.42, 6.2), frame_c)
        box('BRPosterArt', (1.75, 0.04, 2.35), (-2.6, 4.37, 6.2), poster)
        ellipsoid('BRPosterSun', (0.45, 0.03, 0.45), (-2.6, 4.33, 6.6), toon('BRPosterSunM', '#C94F4F'))
        for i, z in enumerate((5.5, 5.8)):
            box('BRPosterHill', (1.6, 0.03, 0.25), (-2.6, 4.33, z - 0.3 * i), toon('BRPosterHillM', '#4F8FC9'))
        # little framed photo above the bed
        box('BRPhoto', (1.3, 0.08, 1.0), (bx, 4.42, 6.0), frame_c)
        box('BRPhotoArt', (1.1, 0.04, 0.8), (bx, 4.37, 6.0), toon('BRPhotoArtM', '#9AD1E8'))

        # ---- floor: rug, slippers, socks ----
        rugo = cylinder('BRRugOb', 2.6, 0.04, (bx - 0.4, -4.3, 0.02), rug, verts=64)
        rugo.scale = (1.3, 0.8, 1)
        for i, dx in enumerate((-0.3, 0.3)):
            ellipsoid(f'BRSlipper{i}', (0.22, 0.42, 0.12), (bx - 2.9 + dx, -1.6, 0.1), slipper, outline=0.02)

        # ---- lights: cool moonlight through the window, warm lamp pool, dim ceiling fill ----
        moon_l = area_light((-8.5, wy + 0.5, wz + 1.5), (0, -62, 0), 2.6, 3800, '#AFC4FF', 'BRMoonLight')
        moon_l.rotation_euler = (0, math.radians(-62), math.radians(-12))
        lamp = point_light((nx - 0.35, ny + 0.2, 3.25), 650, '#FFB766', 0.35, 'BRLamp')
        area_light((0, -4, 8.8), (0, 0, 0), 9, 700, '#A99ED8', 'BRFill')
        area_light((1, -16, 5.5), (80, 0, 0), 10, 900, '#C4B8E8', 'BRFront')
        # warm lamp key on the sleeper's face
        point_light((BED_X - 1.6, 0.4, 5.2), 260, '#FFC98A', 0.6, 'BRFaceKey')
        point_light((nx + 0.45, ny + 0.35, 2.4), 6, '#9FD3FF', 0.1, 'BRPhoneGlow')
    return {'root': root, 'lamp': lamp, 'lamp_shade': lamp_shade, 'phone_screen': scr,
            'clock_txt': clock_txt, 'moon': moon_l, 'origin': origin}
