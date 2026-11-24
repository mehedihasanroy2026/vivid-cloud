"""Set: inside the chest - a cartoon heart pounding between the ribs."""
import math
from toon import toon, box, ellipsoid, cone, tube, area_light, point_light, SetBuilder, empty


def build(origin=(0, 0, 0)):
    with SetBuilder('Chest', origin) as root:
        bg = toon('ChestBg', '#7A1E3A', tex=('brick', '#6A1A33', 2.2, 1.2, 'wall'))
        rib = toon('Rib', '#FFF3E6')
        red = toon('HeartRed', '#E8364E')
        shine = toon('HeartShine', '#FF8A9B')
        ink = toon('Ink', '#2A2230')
        white = toon('FaceWhite', '#FFFFFF')
        vein = toon('Vein', '#4A7BD8')

        box('ChestBack', (30, 0.3, 24), (0, 4, 4), bg)
        for i in range(5):        # ribs curving behind the heart
            z = -1.5 + 2.2 * i
            for s in (1, -1):
                tube(f'Rib{i}{s}', [(s * 0.6, 3.0, z), (s * 3.5, 2.4, z + 0.4), (s * 6.5, 1.8, z - 0.3), (s * 9, 1.5, z - 1.2)],
                     0.32, rib, outline=0.04)
        tube('Spine', [(0, 3.4, -4), (0, 3.4, 12)], 0.6, rib, outline=0.04)

        heart = empty('Heart', (0, 0, 4))
        heart.parent = None
        for s in (1, -1):
            ellipsoid(f'HeartLobe{s}', (1.35, 1.1, 1.35), (s * 0.95, 0, 0.7), red, heart, outline=0.07)
        c = cone('HeartTip', 1.9, 0.15, 2.6, (0, 0, -0.75), red, heart, outline=0.07)
        c.rotation_euler = (math.radians(180), 0, 0)
        c.scale = (1.0, 0.6, 1.0)
        ellipsoid('HeartShine', (0.35, 0.1, 0.22), (-1.2, -1.05, 1.3), shine, heart)
        tube('Aorta', [(0.3, 0.3, 1.6), (0.4, 0.4, 2.8), (1.4, 0.5, 3.4), (2.0, 0.6, 2.8)], 0.38, red, heart, outline=0.05)
        tube('VeinL', [(-0.6, 0.4, 1.7), (-0.9, 0.5, 3.0), (-0.7, 0.5, 3.6)], 0.3, vein, heart, outline=0.05)
        # panicked face
        for s in (1, -1):
            e = ellipsoid(f'HeartEye{s}', (0.36, 0.1, 0.42), (s * 0.7, -1.18, 0.55), white, heart, outline=0.04)
            ellipsoid(f'HeartPupil{s}', (0.12, 0.05, 0.14), (s * 0.05, -0.1, 0.0), ink, e)
        ellipsoid('HeartMouth', (0.32, 0.1, 0.4), (0, -1.12, -0.5), ink, heart)
        # "thump" lines either side
        lines = []
        for s in (1, -1):
            for k in range(3):
                a = (k - 1) * 0.45
                p0 = (s * (3.0 + 0.0), -0.4, 0.6 + 2.0 * a)
                p1 = (s * (4.0 + 0.2 * abs(k - 1)), -0.4, 0.6 + 2.6 * a)
                lines.append(tube(f'Thump{s}{k}', [p0, p1], 0.12, toon('ThumpTxt', '#FFF3E6'), heart))

        area_light((0, -12, 6), (75, 0, 0), 12, 1800, '#FFE8E8', 'ChestFront')
        point_light((0, -4, 8), 400, '#FFFFFF', 1.0, 'ChestKey')
    return {'root': root, 'heart': heart, 'lines': lines, 'origin': origin}
