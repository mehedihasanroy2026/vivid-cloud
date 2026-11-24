"""Set: the brain's control room ("Brain HQ").

Local layout: room x -7..7, y -9..5, floor z=0, ceiling z=9.
Big screen on the back wall shows messages (swap by visibility).
A red siren on the ceiling spins two red spotlights for the alarm.
"""
import math
from toon import (toon, glassy, box, ellipsoid, cylinder, cone, tube, area_light, point_light,
                  text_obj, SetBuilder, hexcol)
import bpy

SCREEN_C = (0, 4.75, 6.5)


def _spot(name, loc, rot_deg, power, hexc, angle=35):
    ld = bpy.data.lights.new(name, 'SPOT')
    ld.energy = power
    ld.color = hexcol(hexc)[:3]
    ld.spot_size = math.radians(angle)
    ld.spot_blend = 0.4
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot_deg]
    return ob


def build(origin=(0, 0, 0)):
    with SetBuilder('ControlRoom', origin) as root:
        wall = toon('HQWall', '#3D4E8C', tex=('tiles', '#33437A', 1.6, 'wall'))
        floor = toon('HQFloor', '#2C355E', tex=('tiles', '#232B4D', 1.5))
        ceil = toon('HQCeil', '#28305A')
        console = toon('Console', '#C9D2E3')
        console_top = toon('ConsoleTop', '#7E8BA8')
        frame = toon('ScreenFrame', '#1E2340')
        screen = toon('ScreenGlow', '#0E2A47', emit=True)
        pink = toon('BrainPink', '#F49AC1')
        ink = toon('Ink', '#2A2230')
        btn_cols = [toon(f'Btn{i}', c, emit=True) for i, c in enumerate(('#FF4D4D', '#FFD23F', '#3DDC97', '#4DA6FF'))]
        red_txt = toon('TxtRed', '#FF3B3B', emit=True)
        yel_txt = toon('TxtYellow', '#FFD23F', emit=True)
        blu_txt = toon('TxtBlue', '#6FD3FF', emit=True)
        grn_txt = toon('TxtGreen', '#4BEA8B', emit=True)
        siren_mat = glassy('SirenGlass', '#FF2A2A', alpha=0.9, emit_strength=3.0)
        white = toon('ClockFace', '#FAFAFA')

        box('Floor', (14.4, 14.4, 0.2), (0, -2, -0.1), floor)
        box('Ceil', (14.4, 14.4, 0.2), (0, -2, 9.1), ceil)
        box('BackWall', (14.4, 0.3, 9.4), (0, 5.15, 4.6), wall)
        box('LeftWall', (0.3, 14.4, 9.4), (-7.15, -2, 4.6), wall)
        box('RightWall', (0.3, 14.4, 9.4), (7.15, -2, 4.6), wall)

        # big screen + messages
        box('ScreenFrame', (7.6, 0.25, 3.6), (0, 4.95, 6.6), frame)
        box('Screen', (7.2, 0.1, 3.2), (0, 4.8, 6.6), screen)
        msgs = {
            'shock': text_obj('MsgShock', 'COLD SHOCK!', 0.95, (0, 4.7, 6.6), red_txt),
            'warn': text_obj('MsgWarn', 'WARNING!', 1.1, (0, 4.7, 6.6), yel_txt),
            'incoming': text_obj('MsgIncoming', 'COLD INCOMING\nSTAY CALM', 0.7, (0, 4.7, 6.6), blu_txt),
            'clear': text_obj('MsgClear', 'ALL CLEAR', 1.0, (0, 4.7, 6.6), grn_txt),
        }
        # "BRAIN HQ" sign with a little brain
        text_obj('SignHQ', 'BRAIN HQ', 0.55, (-5.2, 4.95, 7.0), toon('SignTxt', '#F7F3E8'))
        for i, (x, z) in enumerate(((-5.5, 7.75), (-5.2, 8.0), (-5.8, 7.95))):
            ellipsoid(f'BrainLobe{i}', (0.32, 0.18, 0.24), (x, 4.95, z), pink, outline=0.02)

        # wall clock (right)
        cylinder('Clock', 0.75, 0.15, (5.2, 4.92, 6.6), white, rot=(90, 0, 0), outline=0.03)
        hour = box('ClockHour', (0.08, 0.04, 0.4), (5.2, 4.8, 6.6), ink)
        minute_pivot = bpy.data.objects.new('MinutePivot', None)
        bpy.context.scene.collection.objects.link(minute_pivot)
        minute_pivot.location = (5.2, 4.78, 6.6)
        box('ClockMin', (0.06, 0.04, 0.6), (0, 0, 0.28), ink, parent=minute_pivot)
        for k in range(12):
            a = k * math.pi / 6
            box(f'HQTick{k}', (0.05, 0.03, 0.1), (5.2 + 0.6 * math.sin(a), 4.82, 6.6 + 0.6 * math.cos(a)), ink).rotation_euler = (0, a, 0)

        # consoles: two curved rows of desks with sloped panels and glowing buttons
        for row, (y, n, z0) in enumerate(((1.8, 3, 1.6), (-1.2, 2, 1.6))):
            for i in range(n):
                x = (i - (n - 1) / 2) * 3.6
                box(f'Desk{row}{i}', (3.2, 1.3, z0), (x, y, z0 / 2), console)
                top = box(f'Panel{row}{i}', (3.2, 1.0, 0.12), (x, y - 0.05, z0 + 0.22), console_top)
                top.rotation_euler = (math.radians(-22), 0, 0)
                for b in range(5):
                    cylinder(f'Btn{row}{i}{b}', 0.1, 0.08, (x - 1.1 + 0.55 * b, y - 0.2, z0 + 0.36),
                             btn_cols[(b + i + row) % 4], rot=(-22, 0, 0))
                box(f'Monitor{row}{i}', (1.1, 0.1, 0.8), (x + 0.6, y + 0.4, z0 + 0.85), frame)
                box(f'MonitorGlow{row}{i}', (0.95, 0.04, 0.65), (x + 0.6, y + 0.33, z0 + 0.85), btn_cols[(i + 2) % 4])

        # siren: red dome on the ceiling + two spinning red spotlights
        cylinder('SirenBase', 0.45, 0.2, (0, 0.5, 8.9), console_top)
        ellipsoid('SirenDome', (0.38, 0.38, 0.45), (0, 0.5, 8.6), siren_mat)
        spinner = bpy.data.objects.new('SirenSpin', None)
        bpy.context.scene.collection.objects.link(spinner)
        spinner.location = (0, 0.5, 8.5)
        s1 = _spot('SirenA', (0, 0, 0), (80, 0, 0), 9000, '#FF2020', 45)
        s2 = _spot('SirenB', (0, 0, 0), (-80, 0, 0), 9000, '#FF2020', 45)
        s1.parent = s2.parent = spinner
        siren_glow = point_light((0, 0.5, 8.2), 600, '#FF3030', 0.5, 'SirenGlow')

        # normal room light (dimmed during the alarm)
        room = area_light((0, -1, 8.9), (0, 0, 0), 9.0, 900, '#E8F0FF', 'HQCeiling')
        front = area_light((0, -10, 5), (78, 0, 0), 7.0, 500, '#FFFFFF', 'HQFront')
        point_light(SCREEN_C[:1] + (3.6, 5.4), 150, '#6FD3FF', 1.0, 'ScreenSpill')
    return {'root': root, 'msgs': msgs, 'spinner': spinner, 'sirens': [s1, s2, siren_glow],
            'room': room, 'front': front, 'minute': minute_pivot, 'origin': origin}
