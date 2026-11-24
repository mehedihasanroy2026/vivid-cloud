"""Small cartoon creatures for vivid episodes (outlined, bright, face -Y like the people).

    t = tadpole('Tad', loc, col)      -> {'mover', 'tail'(wiggle Z), 'mouth'(scale to gulp), 'gill'}
    f = frog('Frog', loc)             -> {'mover', 'root'}
    c = cat('Cat', loc)               -> {'mover', 'root', 'fur'(scale up = puffed), 'tail', 'head'}
    e = eyes_in_dark('Eyes', loc)     -> empty; glowing eye pair (scale Z to blink)
    coat = fur_coat(rig, col)         -> fur shell around a doodle character's torso + head (scale 'coat' to puff / vanish)
"""
import math
from toon import ellipsoid, tube, cone, empty
import real
import vivid as V
from acting import A, deg


def _eye(name, loc, parent, r=0.18, look=(0, -0.05, 0)):
    e = ellipsoid(name, (r, r * 0.7, r * 1.15), loc, V.paint('CrWhite', '#FFFFFF', grime=0), parent, outline=0.025, segs=16, rings=8)
    ellipsoid(name + 'P', (r * 0.45, r * 0.4, r * 0.5), (look[0], -r * 0.55, look[2]), V.paint('CrInk', '#1E1A2E', grime=0), e, segs=12, rings=6)
    return e


def tadpole(name, loc=(0, 0, 0), col='#4E7A3A', scale=1.0):
    mover = empty(name, loc)
    mover.scale = (scale,) * 3
    body = V.paint(f'Tad{col}', col, grime=0.05, rough=0.3)
    belly = V.paint('TadBelly', '#D8E8A8', grime=0)
    ellipsoid(name + 'Body', (0.9, 1.0, 0.8), (0, 0, 0), body, mover, outline=0.05, segs=24, rings=12)
    ellipsoid(name + 'Belly', (0.6, 0.6, 0.45), (0, -0.25, -0.3), belly, mover, outline=0.03, segs=16, rings=8)
    tail = empty(name + 'TailP', (0, 0.8, 0), mover)
    tube(name + 'Tail', [(0, 0, 0), (0, 0.9, 0.05), (0, 1.8, 0.1), (0, 2.5, 0.12)], 0.25, body, tail, outline=0.04, radii=[0.4, 0.3, 0.18, 0.05])
    for s in (1, -1):
        _eye(f'{name}Eye{s}', (s * 0.38, -0.7, 0.45), mover)
    mouth = ellipsoid(name + 'Mouth', (0.22, 0.08, 0.1), (0, -0.95, -0.05), V.paint('TadMouth', '#5A1E2E', grime=0), mover, segs=12, rings=6)
    gill = []
    for s in (1, -1):
        for k in range(3):
            g = ellipsoid(f'{name}Gill{s}{k}', (0.08, 0.25, 0.08), (s * 0.85, -0.1 + k * 0.18, 0.1 - k * 0.12), V.paint('Gill', '#FF6F91', grime=0), mover, outline=0.015, segs=8, rings=6)
            gill.append(g)
    return {'mover': mover, 'tail': tail, 'mouth': mouth, 'gill': gill}


def wiggle(tail, t0, t1, amp=25, period=0.3):
    t, k = t0, 0
    while t < t1:
        A.set(tail, 'rotation_euler', t, deg(0, 0, amp if k % 2 else -amp))
        t += period / 2
        k += 1


def frog(name, loc=(0, 0, 0), col='#5DBB4A', scale=1.0):
    mover = empty(name, loc)
    mover.scale = (scale,) * 3
    root = empty(name + 'Body', (0, 0, 0), mover)
    m = V.paint(f'Frog{col}', col, grime=0.05, rough=0.35)
    ellipsoid(name + 'Torso', (1.0, 1.1, 0.75), (0, 0, 0.8), m, root, outline=0.05, segs=24, rings=12)
    ellipsoid(name + 'Belly', (0.7, 0.5, 0.5), (0, -0.55, 0.65), V.paint('FrogBelly', '#E8F0A8', grime=0), root, outline=0.03, segs=16, rings=8)
    for s in (1, -1):
        ellipsoid(f'{name}Leg{s}', (0.45, 0.8, 0.35), (s * 0.9, 0.3, 0.35), m, root, outline=0.04, segs=16, rings=8)
        ellipsoid(f'{name}EyeBump{s}', (0.38, 0.36, 0.38), (s * 0.45, -0.4, 1.45), m, root, outline=0.04, segs=16, rings=8)
        _eye(f'{name}Eye{s}', (s * 0.45, -0.62, 1.5), root, r=0.2)
    tube(name + 'Smile', [(-0.45, -0.95, 0.85), (0, -1.02, 0.75), (0.45, -0.95, 0.85)], 0.04, V.paint('CrInk', '#1E1A2E'), root)
    return {'mover': mover, 'root': root}


def cat(name, loc=(0, 0, 0), col='#FF9E4A', col2='#FFF2DC', scale=1.0):
    mover = empty(name, loc)
    mover.scale = (scale,) * 3
    root = empty(name + 'Body', (0, 0, 0), mover)
    m, m2 = V.paint(f'Cat{col}', col, grime=0.05, kind='fabric'), V.paint(f'Cat2{col2}', col2, grime=0, kind='fabric')
    fur = empty(name + 'Fur', (0, 0.3, 1.2), root)
    ellipsoid(name + 'Torso', (0.65, 1.2, 0.65), (0, 0, 0), m, fur, outline=0.05, segs=24, rings=12)
    for i in range(10):      # spiky fur tufts (stand up when puffed)
        a = i * 0.63
        t = cone(f'{name}Spike{i}', 0.18, 0.0, 0.5, (0.5 * math.cos(a) * 0.6, -0.9 + i * 0.2, 0.55), m, fur, outline=0.02, verts=8)
    for sx in (-0.35, 0.35):
        for sy in (-0.55, 1.05):
            tube(f'{name}Leg', [(sx, sy, 1.0), (sx, sy, 0.1)], 0.13, m, root, outline=0.025)
            ellipsoid(f'{name}Paw', (0.17, 0.2, 0.1), (sx, sy - 0.05, 0.08), m2, root, outline=0.02, segs=12, rings=6)
    tail = empty(name + 'TailP', (0, 1.4, 1.5), root)
    tube(name + 'Tail', [(0, 0, 0), (0, 0.3, 0.6), (0, 0.1, 1.3)], 0.13, m, tail, outline=0.025)
    ellipsoid(name + 'Neck', (0.5, 0.7, 0.55), (0, -0.85, 1.75), m, root, outline=0.04, segs=20, rings=10)
    head = empty(name + 'Head', (0, -1.25, 2.35), root)
    ellipsoid(name + 'Skull', (0.78, 0.68, 0.68), (0, 0, 0), m, head, outline=0.045, segs=24, rings=12)
    ellipsoid(name + 'Muzzle', (0.32, 0.2, 0.2), (0, -0.5, -0.15), m2, head, outline=0.025, segs=16, rings=8)
    ellipsoid(name + 'Nose', (0.08, 0.06, 0.06), (0, -0.68, -0.05), V.paint('CatNose', '#FF6F91', grime=0), head, segs=8, rings=6)
    for s in (1, -1):
        cone(f'{name}Ear{s}', 0.26, 0.0, 0.5, (s * 0.38, -0.05, 0.6), m, head, outline=0.025, verts=12).rotation_euler = deg(0, s * 18, 0)
        _eye(f'{name}Eye{s}', (s * 0.25, -0.45, 0.15), head, r=0.15)
    return {'mover': mover, 'root': root, 'fur': fur, 'tail': tail, 'head': head}


def eyes_in_dark(name, loc, col='#FFE14A', size=0.35, gap=1.2):
    r = empty(name, loc)
    m = real.mat('DarkEyes' + col, col, 'glow', emit=12.0)
    for s in (1, -1):
        e = ellipsoid(f'{name}{s}', (size, size * 0.4, size * 0.7), (s * gap / 2, 0, 0), m, r, segs=16, rings=8)
        e.rotation_euler = deg(0, s * -15, 0)
        ellipsoid(f'{name}Slit{s}', (size * 0.18, size * 0.2, size * 0.6), (0, -size * 0.35, 0), V.paint('CrInk', '#1E1A2E'), e, segs=8, rings=6)
    return r


def fur_coat(rig, col='#8A5A3C', name=None):
    """shaggy fur shell on a doodle character: returns the coat empty (animate its scale: 1 = normal, 1.25 = puffed, ~0 = gone)"""
    name = name or rig['mover'].name + 'Coat'
    m = V.paint(name + 'M', col, kind='fabric', grime=0.1)
    coat = empty(name, (0, 0, 3.05), rig['root'])
    ellipsoid(name + 'Body', (0.72, 0.6, 1.0), (0, 0, 0), m, coat, outline=0.05, segs=24, rings=12)
    for i in range(18):
        a, z = i * 1.1, -0.75 + (i % 6) * 0.28
        cone(f'{name}Tuft{i}', 0.18, 0.0, 0.4, (0.72 * math.cos(a), 0.6 * math.sin(a), z), m, coat, outline=0.02, verts=8).rotation_euler = (
            math.cos(a) * 0.0 + math.radians(90) * math.sin(a) * -1, math.radians(90) * math.cos(a), 0)
    return coat
