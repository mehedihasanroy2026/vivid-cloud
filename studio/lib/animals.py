"""Cartoon animals in the doodle style.

    rig = dog('Rex', loc, col='#C98E5A')
    rig['mover'] position/turn, rig['root'] bounce, rig['head'] pivot, rig['jaw'] (rotate X to open: yawn/bark),
    rig['tail'] (wag: rotate Z), rig['eyes'] (scale Z to blink/squeeze).
Faces -Y like the characters. About 2.6 units tall at the head.
"""
import math
from toon import toon, ellipsoid, tube, empty, LINE_HEX


def dog(name, loc=(0, 0, 0), col='#C98E5A', col2='#F2DCC0', collar='#E8393C'):
    fur, light = toon(f'{name}_fur', col), toon(f'{name}_fur2', col2)
    ink = toon('Ink', LINE_HEX)
    white = toon('FaceWhite', '#FFFFFF')
    mouth_in = toon(f'{name}_mouthIn', '#7A2A3C')
    tongue = toon(f'{name}_tongue', '#F07890')
    mover = empty(name, loc)
    root = empty(f'{name}_body', (0, 0, 0), mover)
    ellipsoid(f'{name}_torso', (0.75, 1.15, 0.7), (0, 0.4, 1.35), fur, root, outline=0.04)
    ellipsoid(f'{name}_belly', (0.5, 0.8, 0.45), (0, 0.3, 1.05), light, root, outline=0.03)
    for sx in (-0.45, 0.45):
        for sy in (-0.35, 1.15):
            tube(f'{name}_leg', [(sx, sy, 1.0), (sx, sy, 0.15)], 0.13, fur, root, outline=0.025)
            ellipsoid(f'{name}_paw', (0.2, 0.26, 0.12), (sx, sy - 0.08, 0.1), light, root, outline=0.02)
    tail = empty(f'{name}_tailPivot', (0, 1.45, 1.6), root)
    tube(f'{name}_tail', [(0, 0, 0), (0, 0.4, 0.35), (0, 0.45, 0.85)], 0.09, fur, tail, outline=0.02)
    tube(f'{name}_collar', [(0.55 * math.cos(a), -0.45 + 0.4 * math.sin(a), 1.95) for a in
                             [math.pi * 2 * i / 16 for i in range(17)]], 0.07, toon(f'{name}_collarM', collar), root)
    head = empty(f'{name}_head', (0, -0.55, 2.05), root)
    ellipsoid(f'{name}_skull', (0.62, 0.58, 0.58), (0, 0, 0.3), fur, head, outline=0.04)
    ellipsoid(f'{name}_muzzle', (0.36, 0.42, 0.24), (0, -0.55, 0.12), light, head, outline=0.03)
    ellipsoid(f'{name}_nose', (0.13, 0.1, 0.09), (0, -0.95, 0.24), ink, head)
    jaw = empty(f'{name}_jaw', (0, -0.2, 0.02), head)
    ellipsoid(f'{name}_jawOb', (0.3, 0.42, 0.13), (0, -0.33, -0.08), light, jaw, outline=0.025)
    ellipsoid(f'{name}_mouthIn', (0.26, 0.36, 0.1), (0, -0.3, 0.02), mouth_in, jaw)
    ellipsoid(f'{name}_tongueOb', (0.15, 0.25, 0.06), (0, -0.4, 0.06), tongue, jaw)
    eyes = []
    for s in (1, -1):
        e = ellipsoid(f'{name}_eye{s}', (0.13, 0.08, 0.15), (s * 0.25, -0.48, 0.5), white, head, outline=0.025)
        ellipsoid(f'{name}_pupil{s}', (0.06, 0.05, 0.07), (0, -0.06, -0.01), ink, e)
        eyes.append(e)
        ear = empty(f'{name}_ear{s}', (s * 0.5, 0.0, 0.7), head)
        ellipsoid(f'{name}_earOb{s}', (0.18, 0.12, 0.5), (s * 0.12, 0, -0.4), toon(f'{name}_earM', '#6B4430'), ear,
                  outline=0.025).rotation_euler = (0, s * 0.35, 0)
    return {'mover': mover, 'root': root, 'head': head, 'jaw': jaw, 'tail': tail, 'eyes': eyes}
