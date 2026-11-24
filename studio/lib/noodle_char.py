"""'Noodle' - the Doodles Got Noodles mascot.

Round white head, noodle hair with chopsticks, small shirt body, stick limbs.
Faces -Y (toward the camera). Feet at the root's origin, ~4.4 units tall.
"""
import math
import random
from mathutils import Vector
from toon import toon, ellipsoid, tube, empty

HEAD_R = (1.0, 0.93, 0.88)       # head ellipsoid radii
HEAD_Z = 2.98                    # head centre height
FRONT = -math.pi / 2             # azimuth of the face

DEFAULT_LOOK = {
    'skin': '#F7F2E8',
    'hair': '#F2C14E',
    'shirt': '#E4572E',
    'shoes': '#4A2E1F',
    'chopsticks': '#B83227',
    'eyes': '#151515',
}


def surf(theta, phi, lift=0.0, r=HEAD_R):
    """Point + normal on the head. theta = angle from top, phi = azimuth."""
    d = Vector((math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta)))
    t = 1 / math.sqrt((d.x / r[0]) ** 2 + (d.y / r[1]) ** 2 + (d.z / r[2]) ** 2)
    p = d * t
    n = Vector((p.x / r[0] ** 2, p.y / r[1] ** 2, p.z / r[2] ** 2)).normalized()
    return p + n * lift, n


def build(name='Noodle', loc=(0, 0, 0), look=None, seed=3):
    look = dict(DEFAULT_LOOK, **(look or {}))
    rnd = random.Random(seed)
    M = {k: toon(f'{name}_{k}', v) for k, v in look.items()}
    M['eyes'] = toon(f'{name}_eyes', look['eyes'], emit=True)
    white = toon('EyeShine', '#FFFFFF', emit=True)

    root = empty(name, loc)
    rig = {'root': root}

    # ---- body -------------------------------------------------------------
    ellipsoid(f'{name}_torso', (0.44, 0.38, 0.56), (0, 0, 1.6), M['shirt'], root, outline=0.03)
    for s, side in ((1, 'L'), (-1, 'R')):
        tube(f'{name}_leg{side}', [(s * 0.17, 0, 1.2), (s * 0.18, 0, 0.6), (s * 0.19, 0, 0.14)],
             0.045, M['eyes'], root)
        ellipsoid(f'{name}_shoe{side}', (0.15, 0.25, 0.11), (s * 0.2, -0.09, 0.1), M['shoes'], root, outline=0.025)
        sh = empty(f'{name}_shoulder{side}', (s * 0.36, 0, 1.92), root)
        tube(f'{name}_arm{side}', [(0, 0, 0), (s * 0.13, 0, -0.38), (s * 0.2, -0.02, -0.74)],
             0.04, M['eyes'], sh)
        ellipsoid(f'{name}_hand{side}', (0.1, 0.1, 0.1), (s * 0.21, -0.02, -0.8), M['skin'], sh, outline=0.02)
        rig[f'shoulder{side}'] = sh

    # ---- head -------------------------------------------------------------
    neck = empty(f'{name}_neck', (0, 0, 2.1), root)
    head = ellipsoid(f'{name}_head', HEAD_R, (0, 0, HEAD_Z - 2.1), M['skin'], neck, outline=0.035, segs=64, rings=32)
    rig['neck'] = neck
    rig['head'] = head

    # eyes (with a small shine dot)
    rig['eyes'] = []
    for s in (1, -1):
        p, n = surf(1.47, FRONT + s * 0.31, 0.0)
        eye = ellipsoid(f'{name}_eye{s}', (0.075, 0.115, 0.035), p, M['eyes'], head, segs=24, rings=12)
        eye.rotation_euler = n.to_track_quat('Z', 'Y').to_euler()
        ellipsoid(f'{name}_shine{s}', (0.026, 0.03, 0.02), (0.024, 0.045, 0.02), white, eye, segs=12, rings=6)
        rig['eyes'].append(eye)

    # eyebrows
    for s in (1, -1):
        pts = []
        for k in range(5):
            u = (k / 4 - 0.5)
            pts.append(surf(1.2 - 0.03 * (1 - 4 * u * u), FRONT + s * 0.31 + u * 0.22, 0.012)[0])
        tube(f'{name}_brow{s}', pts, 0.018, M['eyes'], head)

    # smile
    pts = []
    for k in range(9):
        u = k / 8 * 2 - 1
        pts.append(surf(1.86 + 0.09 * (1 - u * u), FRONT + 0.27 * u, 0.012)[0])
    rig['mouth'] = tube(f'{name}_mouth', pts, 0.022, M['eyes'], head)

    # ---- noodle hair ------------------------------------------------------
    hair = empty(f'{name}_hair', (0, 0, 0), head)
    n_strands = 16
    for i in range(n_strands):
        phi0 = 2 * math.pi * i / n_strands + rnd.uniform(-0.1, 0.1)
        front = max(0.0, -math.sin(phi0))          # 1 = over the forehead
        th_end = 1.62 - 0.6 * front ** 1.5
        wav, ph = rnd.uniform(5, 8), rnd.uniform(0, 6)
        pts = []
        for k in range(26):
            t = k / 25
            th = 0.08 + (th_end - 0.08) * t
            phi = phi0 + 0.12 * math.sin(wav * t * math.pi + ph) * t
            pts.append(surf(th, phi, 0.05 + 0.02 * math.sin(t * 9 + ph))[0])
        tube(f'{name}_noodle{i}', pts, 0.055, M['hair'], hair, outline=0.014)
    # messy loops piled on top
    for i in range(6):
        a = rnd.uniform(0, math.pi)
        pts = []
        for k in range(22):
            t = k / 21
            th = -0.75 + 1.5 * t                   # crosses over the crown
            phi = a + (0 if th >= 0 else math.pi)
            p, n = surf(abs(th) + 0.02, phi + 0.15 * math.sin(t * 8 + i), 0.08 + 0.16 * math.sin(math.pi * t))
            pts.append(p)
        tube(f'{name}_loop{i}', pts, 0.055, M['hair'], hair, outline=0.014)

    # chopsticks stuck in the hair (the signature)
    for s in (1, -1):
        base, n = surf(0.55, math.pi / 2 + s * 0.35, -0.05)
        tip = base + Vector((s * 0.35, 0.55, 1.15))
        tube(f'{name}_chopstick{s}', [base, base.lerp(tip, 0.5), tip], 0.032, M['chopsticks'], hair, outline=0.012)

    return rig
