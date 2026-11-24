"""Set: the tickle-robot science lab (EP07), real-light look.

Local layout: room x -10..10, y -10..7, floor z=0, ceiling z=11. Cameras look toward +Y.
Big window on the left wall (sun shafts across the room). Lab benches with glassware on the right.
The robot arm stands at ROBOT on a base: joints are empties (yaw about Z, shoulder/elbow/wrist about X);
the feather sits at the tip. A wall screen shows the delay: build.py toggles the 'values' text objects.
"""
import math
import assets
import real
from toon import box, cylinder, ellipsoid, tube, cone, text_obj, empty, SetBuilder

M = 7.5 / 3.5
ROBOT = (-2.4, 1.6)
SCREEN = (4.2, 6.85, 7.0)
DELAYS = ['0.0', '0.1', '0.2']


def build(origin=(0, 0, 0)):
    with SetBuilder('Lab', origin) as root:
        tile = real.mat('LBTile', '#EEF2F4', 'tile', mode='wall', size=(0.7, 0.7), line='#B6C2C9', grime=0.1)
        tilex = real.mat('LBTileX', '#EEF2F4', 'tile', mode='wallx', size=(0.7, 0.7), line='#B6C2C9', grime=0.1)
        upper = real.mat('LBUpper', '#9FC3C9', 'paint', mode='wall', grime=0.12)
        upperx = real.mat('LBUpperX', '#9FC3C9', 'paint', mode='wallx', grime=0.12)
        floor = real.mat('LBFloor', '#7C8C99', 'tile', mode='floor', size=(1.4, 1.4), line='#5D6B76', grime=0.25)
        ceil = real.mat('LBCeil', '#F1F4F4', 'paint', grime=0.08)
        trim = real.mat('LBTrim', '#FAFAF7', 'paint', grime=0.05)
        bench = real.mat('LBBench', '#3D4855', 'metal', grime=0.2)
        top = real.mat('LBTop', '#1F2A33', 'plastic', grime=0.1, rough=0.35)
        sky = real.mat('LBSky', '#F2F8FF', 'glow', emit=4.0)
        lampm = real.mat('LBLamp', '#FFFFFF', 'glow', emit=8.0)
        orange = real.mat('LBRobot', '#F28C28', 'plastic', grime=0.12, rough=0.35)
        dark = real.mat('LBRobotJ', '#2B2F36', 'metal', grime=0.15)
        ink = real.mat('LBInk', '#25303D', 'paint', grime=0)
        board = real.mat('LBBoard', '#FCFCFA', 'paint', grime=0.08)
        scr = real.mat('LBScreen', '#0E1A22', 'plastic', grime=0, rough=0.15)
        digit = real.mat('LBDigit', '#53FF8A', 'glow', emit=5.0)
        feather_m = real.mat('LBFeather', '#FF8FC0', 'fabric', grime=0)

        box('LBFloorOb', (20.4, 17.4, 0.2), (0, -1.5, -0.1), floor)
        box('LBCeilOb', (20.4, 17.4, 0.2), (0, -1.5, 11.1), ceil)
        box('LBBack', (20.4, 0.4, 4.0), (0, 7.2, 2.0), tile)
        box('LBBackUp', (20.4, 0.4, 7.4), (0, 7.2, 7.7), upper)
        box('LBRight', (0.4, 17.4, 4.0), (10.2, -1.5, 2.0), tilex)
        box('LBRightUp', (0.4, 17.4, 7.4), (10.2, -1.5, 7.7), upperx)
        # left wall with a big window (y -4..4, z 3.5..9.5)
        box('LBLeftLow', (0.4, 17.4, 3.5), (-10.2, -1.5, 1.75), tilex)
        box('LBLeftTop', (0.4, 17.4, 1.7), (-10.2, -1.5, 10.35), upperx)
        box('LBLeftA', (0.4, 5.7, 6.0), (-10.2, -7.15, 6.5), upperx)
        box('LBLeftB', (0.4, 3.0, 6.0), (-10.2, 5.5, 6.5), upperx)
        for y in (-4.0, 0.0, 4.0):
            box('LBWinV', (0.5, 0.18, 6.2), (-10.0, y, 6.5), trim)
        for z in (3.5, 6.5, 9.5):
            box('LBWinH', (0.5, 8.2, 0.18), (-10.0, 0.0, z), trim)
        sk = box('LBSkyCard', (0.2, 60, 40), (-30, 0, 10), sky)
        sk.visible_shadow = False
        box('LBTileCap', (20.0, 0.25, 0.2), (0, 6.95, 4.0), trim)
        # ceiling light panels
        for x, y in ((-4, -2), (4, -2), (-4, 4), (4, 4)):
            box('LBPanel', (3.0, 1.2, 0.1), (x, y, 10.95), lampm)
        # benches with glassware on the right
        g = real.glass('LBGlass', '#E3F3FA', 0.25)
        liquids = [real.mat(f'LBLiq{i}', c, 'glow', emit=1.5) for i, c in enumerate(('#53C7FF', '#FF6FB5', '#8BE34A'))]
        for y in (-3.5, 1.5):
            box('LBBenchOb', (2.6, 4.6, 3.0), (8.6, y, 1.5), bench)
            box('LBBenchTop', (2.8, 4.8, 0.15), (8.6, y, 3.07), top)
            for k in range(4):
                x, yy = 8.2 + (k % 2) * 0.8, y - 1.5 + k * 1.0
                cylinder('LBBeaker', 0.3, 0.9, (x, yy, 3.6), g)
                cylinder('LBLiquid', 0.26, 0.5, (x, yy, 3.4), liquids[k % 3])
        cone('LBFlask', 0.55, 0.15, 1.0, (8.0, 3.6, 3.65), g)
        # whiteboard on the back wall
        box('LBWB', (6.0, 0.1, 3.4), (-5.0, 6.95, 6.8), board)
        box('LBWBFrame', (6.2, 0.08, 3.6), (-5.0, 7.0, 6.8), real.mat('LBAlu', '#B9BEC4', 'metal', grime=0.1))
        t = text_obj('LBWBText', 'TICKLE STUDY', 0.5, (-5.0, 6.88, 7.7), ink, extrude=0.01)
        t.data.align_x = 'CENTER'
        tube('LBWBDoodle', [(-7.0, 6.88, 6.0), (-6.0, 6.88, 6.8), (-5.0, 6.88, 5.8), (-4.0, 6.88, 6.6),
                            (-3.0, 6.88, 6.1)], 0.04, real.mat('LBMarker', '#2F7DD1', 'paint', grime=0))
        t = text_obj('LBWBText2', 'DELAY = ?', 0.4, (-5.0, 6.88, 5.3), real.mat('LBRedInk', '#E53935', 'paint',
                                                                               grime=0), extrude=0.01)
        t.data.align_x = 'CENTER'
        # the delay screen
        sx, sy, sz = SCREEN
        box('LBScreenFrame', (5.0, 0.3, 3.0), (sx, sy + 0.1, sz), dark)
        box('LBScreenOb', (4.6, 0.1, 2.6), (sx, sy - 0.05, sz), scr)
        t = text_obj('LBScreenLbl', 'DELAY', 0.45, (sx, sy - 0.12, sz + 0.7), digit, extrude=0.005)
        t.data.align_x = 'CENTER'
        values = []
        for v in DELAYS:
            tv = text_obj(f'LBDelay{v}', f'{v} SEC', 1.0, (sx, sy - 0.12, sz - 0.75), digit, extrude=0.005)
            tv.data.align_x = 'CENTER'
            values.append(tv)
        real.point((sx, sy - 1.0, sz), 120, '#53FF8A', radius=1.0, name='LBScreenGlow', volume=0.1)

        # the robot arm
        rx, ry = ROBOT
        cylinder('LBRobotBase', 1.1, 0.6, (rx, ry, 0.3), dark, verts=48)
        yaw = empty('LBRobotYaw', (rx, ry, 0.6))
        cylinder('LBRobotTurret', 0.8, 0.8, (0, 0, 0.4), orange, parent=yaw, verts=48)
        sh = empty('LBRobotShoulder', (0, 0, 1.0), yaw)
        cylinder('LBRobotJ1', 0.5, 1.4, (0, 0, 0), dark, parent=sh, rot=(0, 90, 0))
        box('LBRobotArm1', (0.7, 0.7, 3.6), (0, 0, 1.8), orange, parent=sh, bevel=0.15)
        el = empty('LBRobotElbow', (0, 0, 3.6), sh)
        cylinder('LBRobotJ2', 0.42, 1.1, (0, 0, 0), dark, parent=el, rot=(0, 90, 0))
        box('LBRobotArm2', (0.55, 0.55, 3.0), (0, 0, 1.5), orange, parent=el, bevel=0.12)
        wr = empty('LBRobotWrist', (0, 0, 3.0), el)
        cylinder('LBRobotJ3', 0.3, 0.5, (0, 0, 0.1), dark, parent=wr)
        for s in (-1, 1):
            box('LBRobotClaw', (0.12, 0.2, 0.5), (s * 0.16, 0, 0.55), dark, parent=wr)
        # feather held in the claw (points along +Z of the wrist)
        fe = empty('LBFeatherRoot', (0, 0, 0.6), wr)
        tube('LBQuill', [(0, 0, -0.1), (0, 0, 1.0), (0, 0.05, 2.0)], 0.035, trim, fe)
        vane = ellipsoid('LBVane', (0.34, 0.05, 0.85), (0, 0.02, 1.35), feather_m, fe, outline=0.02)
        vane.rotation_euler[0] = math.radians(4)
        for k in range(5):
            b = ellipsoid('LBBarb', (0.38, 0.04, 0.08), (0, 0.03, 0.75 + k * 0.28), feather_m, fe)
            b.rotation_euler[1] = math.radians(20 if k % 2 else -20)
        # cables + a warning stripe on the floor
        tube('LBCable', [(rx + 0.8, ry, 0.15), (rx + 2.0, ry + 2.0, 0.08), (rx + 2.5, 5.5, 0.08)], 0.09, dark)
        for i in range(8):
            a = i / 8 * 2 * math.pi
            st = box('LBStripe', (0.5, 0.25, 0.02), (rx + 1.7 * math.cos(a), ry + 1.7 * math.sin(a), 0.011),
                     real.mat('LBYellow', '#F2C230', 'paint', grime=0.2))
            st.rotation_euler[2] = a + math.pi / 2
        assets.load('furniture-kit', 'chairDesk', loc=(1.4, 4.5, 0), scale=M, rot=(0, 0, 200), center=True)
        assets.load('furniture-kit', 'pottedPlant', loc=(-8.6, 5.6, 0), scale=M, center=True)

        # light: sun through the window, cool fill
        real.sun((55, 0, -95), strength=11.0, hexc='#FFEACC', angle=1.2, name='LBSun')
        real.area((0, -12, 8), (75, 0, 0), 16, 700, '#DCE8F6', shadow=False, name='LBFront', volume=0.0)
        real.area((0, 1, 10.8), (0, 0, 0), 10, 500, '#F4F8FF', shadow=False, name='LBCeilFill', volume=0.0)
        real.shafts((0, -1.5, 5.5), (20, 17, 11), density=0.009, name='LBHaze')
    return {'root': root, 'yaw': yaw, 'shoulder': sh, 'elbow': el, 'wrist': wr, 'feather': fe, 'values': values}
