"""Set: snowy prehistoric riverbank with a freezing river and pine trees.

Bank (walkable snow) on y < 0, river along x at y 0.5..5, far bank beyond.
Snowflakes drift down (cycled keyframes).
"""
import math
import random
import bpy
from toon import (toon, glassy, box, ellipsoid, cylinder, cone, tube, area_light, sun, SetBuilder, hexcol)


def _pine(name, x, y, h, M):
    cylinder(f'{name}_trunk', 0.22 * h / 5, h * 0.25, (x, y, h * 0.12), M['bark'], outline=0.03)
    for k in range(3):
        z = h * (0.3 + 0.22 * k)
        r = h * (0.32 - 0.08 * k)
        cone(f'{name}_tier{k}', r, 0.0, h * 0.38, (x, y, z), M['pine'], outline=0.035)
        cone(f'{name}_snow{k}', r * 0.55, 0.0, h * 0.18, (x, y, z + h * 0.12), M['snow'])


def build(origin=(0, 0, 0)):
    rnd = random.Random(11)
    with SetBuilder('SnowRiver', origin) as root:
        M = {
            'snow': toon('SnowGround', '#F3F8FF'),
            'pine': toon('Pine', '#2F8F6B'),
            'bark': toon('Bark', '#6B4A33'),
            'rock': toon('Rock', '#8C97A8'),
        }
        river = toon('River', '#2E73C9', rough=0.15)
        ice = glassy('RiverIce', '#DDF3FF', alpha=0.9)
        sky = toon('WinterSky', '#A9D2F2', emit=True)
        mountain = toon('Mountain', '#C7D6EC')
        flake = toon('Flake', '#FFFFFF', emit=True)

        box('Sky', (200, 0.5, 80), (0, 70, 20), sky)
        for i, (x, h) in enumerate(((-40, 22), (-15, 30), (12, 26), (38, 32))):
            cone(f'Mountain{i}', 22, 0, h, (x, 62, h / 2 - 2), mountain)
            cone(f'MountainCap{i}', 7, 0, h * 0.32, (x, 61.8, h - h * 0.16 - 2), M['snow'])

        box('NearBank', (90, 20, 1.0), (0, -10, -0.5), M['snow'])
        box('FarBank', (90, 50, 1.0), (0, 30, -0.5), M['snow'])
        box('RiverWater', (90, 4.6, 0.6), (0, 2.75, -1.2), river)
        box('RiverBedL', (90, 0.4, 1.4), (0, 0.4, -0.9), M['rock'])
        # floating ice chunks
        for i in range(10):
            x = rnd.uniform(-25, 25)
            c = box(f'IceChunk{i}', (rnd.uniform(0.8, 1.8), rnd.uniform(0.6, 1.3), 0.25), (x, rnd.uniform(1.2, 4.3), -0.85), ice)
            c.rotation_euler = (0, 0, rnd.uniform(0, 3))
        # snow mounds + rocks on the near bank
        for i in range(8):
            x = rnd.uniform(-20, 20)
            ellipsoid(f'Mound{i}', (rnd.uniform(1.2, 2.5), rnd.uniform(1.0, 2.0), rnd.uniform(0.3, 0.6)),
                      (x, rnd.uniform(-8, -2), 0.0), M['snow'], outline=0.03)
        for i in range(4):
            ellipsoid(f'Rock{i}', (0.7, 0.6, 0.45), (rnd.uniform(-14, 14), -0.6, 0.15), M['rock'], outline=0.03)
        # trees on both banks
        for i in range(9):
            _pine(f'PineFar{i}', -24 + 6 * i + rnd.uniform(-1.5, 1.5), rnd.uniform(9, 16), rnd.uniform(6, 9), M)
        for i, x in enumerate((-11, -6.5, 9, 13)):
            _pine(f'PineNear{i}', x, rnd.uniform(-5, -3.5), rnd.uniform(5, 7), M)

        # snowflakes: each falls 12 units over 90 frames, cycling forever
        flakes = []
        for i in range(70):
            x, y = rnd.uniform(-12, 12), rnd.uniform(-9, 6)
            z0 = rnd.uniform(0, 12)
            f = ellipsoid(f'Flake{i}', (0.06, 0.06, 0.06), (x, y, z0), flake, segs=8, rings=4)
            flakes.append((f, x, y, z0))

        s = sun((50, 0, 30), strength=3.2, hexc='#FFF4E0', angle=3)
        area_light((0, -18, 9), (70, 0, 0), 14, 2200, '#E8F2FF', 'SnowFill')
    return {'root': root, 'flakes': flakes, 'sun': s, 'origin': origin}


def animate_flakes(info, start, end):
    """Make snow fall between frames start..end (linear, cycling)."""
    for f, x, y, z0 in info['flakes']:
        period = 90
        phase = (z0 / 12.0) * period
        f.location = (x, y, 12)
        f.keyframe_insert('location', frame=start - phase)
        f.location = (x + 0.8, y, 0)
        f.keyframe_insert('location', frame=start - phase + period)
        fc = f.animation_data.action
        for curve in _fcurves(f):
            for kp in curve.keyframe_points:
                kp.interpolation = 'LINEAR'
            curve.modifiers.new('CYCLES')


def _fcurves(ob):
    ad = ob.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, 'fcurves') and len(getattr(act, 'fcurves', [])):
        return list(act.fcurves)
    # Blender 4.4+ layered actions
    out = []
    for layer in getattr(act, 'layers', []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                out.extend(cb.fcurves)
    return out
