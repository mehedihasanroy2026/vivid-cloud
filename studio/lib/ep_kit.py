"""Shared episode kit (from EP22): the helpers every build used to copy, plus the EP22 "more cuts" upgrade.

    import ep_kit as K
    K.pop_in(objs, t_in, t_out); K.word_pop(...); K.cs(name, origin, loc, target, lens, ...)
    K.reset_cast()                    # key every rig at t=0 (rig rule from the EP12-14 bugs)
    K.run(args, SETS, BOUNDS)         # drop_frame0 + PROBE/CAMCHECK + ink + render

Upgrade (EP22-26, user: "not engaging enough, make more cuts"):
  - ~20 shots per minute instead of ~12, with HARD cuts between shots in the same place (K.HARD_INSIDE),
    fly-through dissolves between places (6 frames).
  - punch= crash zooms on key words inside a shot: cs(..., punch=[(t, lens)]) snaps the lens in 3 frames.
"""
import os
import math
import bpy

from toon import ellipsoid, cone, tube, box, cylinder, empty, text_obj
from acting import F, deg, W, A
import real
import vivid as V
import vsets as VS
import ep_common as E
from ep_common import place, arms, legs, neck, lean, face, show, shot

HARD_INSIDE = True
CROSS_T = 6


def reset_cast():
    for rg in E.RIGS:
        place(rg, 0, tuple(rg['mover'].location), math.degrees(rg['mover'].rotation_euler.z))
        lean(rg, 0, 0, 0, jump=True)
        neck(rg, 0, 0, 0, 0, jump=True)
        arms(rg, 0, (-20, 0, 15), (-20, 0, -15), jump=True)
        legs(rg, 0, (0, 0, 0), (0, 0, 0), jump=True)
        face(rg, 0, 'neutral')


def pop_in(objs, t_in, t_out, size=1.0):
    """scale-pop roots between t_in and t_out (+ a show range so they are really gone outside it)"""
    for o in objs:
        A.set(o, 'scale', 0, (0.001,) * 3)
        A.set(o, 'scale', t_in, (0.001,) * 3)
        A.set(o, 'scale', t_in + 0.12, (size * 1.2,) * 3)
        A.set(o, 'scale', t_in + 0.22, (size,) * 3)
        A.set(o, 'scale', t_out - 0.1, (size,) * 3)
        A.set(o, 'scale', t_out, (0.001,) * 3)
    show(objs, [(t_in, t_out)])


def word_pop(nm, txt, loc, size, col, t_in, t_out, rot=(90, 0, 0)):
    o = text_obj(nm, txt, size, loc, VS.glow(nm + 'M', col, 3.5), rot=rot, extrude=0.06)
    o.data.align_x = 'CENTER'
    o.data.align_y = 'CENTER'
    o.visible_shadow = False
    pop_in([o], t_in, t_out)
    return o


def sign_pop(nm, txt, loc, size, t_in, t_out, board='#E53945', inkc='#FFFFFF', rot=0, k=1.5):
    s = VS.sign(nm, txt, loc, size, board=board, inkc=inkc, k=k, rot=rot)
    pop_in([s], t_in, t_out)
    return s


def cs(name, origin, loc, target, lens, punch=(), **kw):
    """shot() with handheld on, plus punch=[(t, lens)] crash zooms (lens snaps in 0.1 s and holds)"""
    kw.setdefault('hand', 0.06)
    if punch:
        z = list(kw.pop('zoom', ()))
        cur = lens
        for t, l in punch:
            z += [(t - 0.02, cur), (t + 0.1, l)]
            cur = l
        kw['zoom'] = sorted(z)
    return shot(name, origin, loc, target, lens, **kw)


def kids(rig):
    return [rig['mover']] + list(rig['mover'].children_recursive)


def offstage(rig, t, far=(0, 0, -60)):
    """hide a rig for the coming shots by moving it far below its set (EP17 rule: never show() a rig)"""
    loc = rig['mover'].location
    A.jump(rig['mover'], 'location', t, (round(loc.x / 300.0) * 300.0 + far[0], far[1], far[2]))


# ---------------------------------------------------------------- shared props
def toilet(nm, loc, rot=0, parent=None, lid_open=True):
    """white toilet from primitives, facing -y (rot turns it). Returns {'root','lid','bowl','hole'}; bowl rim top z ~2.15.
    The water surface is dark teal so a snake can rise out of it."""
    r = empty(nm, loc, parent)
    r.rotation_euler = deg(0, 0, rot)
    white = V.paint('LooW', '#FAFAFF', rough=0.18, grime=0.02)
    cylinder(nm + 'Foot', 0.75, 1.2, (0, 0.2, 0.6), white, r, outline=0.04)
    bowl = ellipsoid(nm + 'Bowl', (1.25, 1.6, 0.75), (0, -0.2, 1.55), white, r, outline=0.05, segs=32, rings=16)
    ring = [(1.12 * math.cos(2 * math.pi * k / 32), -0.2 + 1.45 * math.sin(2 * math.pi * k / 32), 2.32) for k in range(33)]
    tube(nm + 'Seat', ring, 0.17, V.paint('LooSeat', '#FFFFFF', rough=0.3, grime=0), r, outline=0.03)
    hole = ellipsoid(nm + 'Hole', (1.0, 1.32, 0.03), (0, -0.2, 2.31), V.paint('LooWater', '#13343E', rough=0.05, grime=0), r, segs=32, rings=8)
    box(nm + 'Tank', (2.4, 0.9, 1.9), (0, 1.55, 2.9), white, r, outline=0.05, bevel=0.15)
    box(nm + 'TankLid', (2.6, 1.05, 0.2), (0, 1.55, 3.9), white, r, outline=0.04, bevel=0.06)
    cylinder(nm + 'Flush', 0.14, 0.12, (0.9, 1.0, 3.5), V.paint('Chrome', '#D8D8E8', kind='metal'), r, rot=(90, 0, 0))
    lid = empty(nm + 'LidPiv', (0, 1.0, 2.25), r)
    ellipsoid(nm + 'Lid', (1.25, 0.12, 1.6), (0, 0.05, 1.5), white, lid, outline=0.04, segs=32, rings=8)
    if not lid_open:
        lid.rotation_euler = deg(-90, 0, 0)
    return {'root': r, 'lid': lid, 'bowl': bowl, 'hole': hole}


def snake(nm, n=14, col='#C9A23A', col2='#6B4A1E', r=0.22, seg=0.38):
    """snake as a chain of beads under a root empty; 'body' = list of beads (animate bead locations with slither()),
    head with eyes + forked red tongue. All local to root."""
    root = empty(nm)
    m1 = V.pat(nm + 'Skin', col, col2, 'dots', scale=3.0, mode='box')
    beads = []
    for i in range(n):
        rr = r * (0.55 + 0.45 * min(1, (n - i) / (n * 0.6)))
        b = ellipsoid(f'{nm}B{i}', (rr, rr, rr * 0.9), (0, i * seg, 0), m1, root, outline=0.02, segs=14, rings=8)
        beads.append(b)
    head = beads[0]
    head.scale = (1.35, 1.6, 1.0)
    for s in (-1, 1):
        ellipsoid(f'{nm}Eye{s}', (0.07, 0.07, 0.07), (s * 0.13, -0.08, 0.15), V.paint('SnakeEye', '#FFE14A', grime=0), head, segs=10, rings=6)
        ellipsoid(f'{nm}Pup{s}', (0.03, 0.03, 0.045), (s * 0.13, -0.13, 0.17), VS.ink(), head, segs=8, rings=4)
    tongue = tube(nm + 'Tongue', [(0, -0.2, 0), (0, -0.45, 0), (0.07, -0.55, 0)], 0.018, V.paint('SnakeTongue', '#E8303A', grime=0), head)
    tube(nm + 'Tongue2', [(0, -0.45, 0), (-0.07, -0.55, 0)], 0.018, V.paint('SnakeTongue', '#E8303A', grime=0), head)
    return {'root': root, 'beads': beads, 'head': head, 'tongue': tongue}


def slither(sn, t0, t1, path, every=1 / 30, wig=0.25, period=0.6):
    """move the snake beads along a polyline path (local coords of sn['root']) from t0 to t1. The head leads; each
    bead trails along the same path with a side wiggle."""
    import mathutils
    pts = [mathutils.Vector(p) for p in path]
    segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    L = sum((b - a).length for a, b in segs)

    def at_len(s):
        s = max(0.0, min(L, s))
        for a, b in segs:
            d = (b - a).length
            if s <= d:
                return a + (b - a) * (s / d if d else 0), (b - a).normalized()
            s -= d
        return pts[-1], (pts[-1] - pts[-2]).normalized()
    seg = (sn['beads'][1].location - sn['beads'][0].location).length if len(sn['beads']) > 1 else 0.38
    t = t0
    while t <= t1 + 1e-6:
        u = (t - t0) / max(1e-6, (t1 - t0))
        head_s = L * u
        for i, b in enumerate(sn['beads']):
            s = head_s - i * seg
            p, d = at_len(s)
            side = mathutils.Vector((-d.y, d.x, 0))
            if side.length < 1e-4:
                side = mathutils.Vector((1, 0, 0))
            side.normalize()
            p = p + side * (wig * math.sin((t * 2 * math.pi / period) - i * 0.7) * min(1.0, i / 3))
            A.set(b, 'location', t, tuple(p))
        t += every * 3


def clock(nm, loc, r=1.6, face_col='#FFFFFF', rim='#E53945', parent=None, rot=0):
    """wall clock facing -y: returns {'root','hour','min'} (rotate the hands about Y)"""
    root = empty(nm, loc, parent)
    root.rotation_euler = deg(0, 0, rot)
    cylinder(nm + 'Rim', r * 1.12, 0.3, (0, 0.05, 0), V.paint(nm + 'RimM', rim), root, rot=(90, 0, 0), outline=0.04)
    cylinder(nm + 'Face', r, 0.32, (0, 0, 0), V.paint(nm + 'FaceM', face_col, grime=0.02), root, rot=(90, 0, 0))
    for k in range(12):
        a = 2 * math.pi * k / 12
        box(f'{nm}Tick{k}', (0.08, 0.05, 0.28), (r * 0.82 * math.sin(a), -0.18, r * 0.82 * math.cos(a)), VS.ink(), root).rotation_euler = (0, a, 0)
    hp = empty(nm + 'Hour', (0, -0.2, 0), root)
    box(nm + 'HourOb', (0.12, 0.05, r * 0.5), (0, 0, r * 0.25), VS.ink(), hp)
    mp = empty(nm + 'Min', (0, -0.24, 0), root)
    box(nm + 'MinOb', (0.08, 0.05, r * 0.78), (0, 0, r * 0.39), V.paint(nm + 'MinM', rim), mp)
    cylinder(nm + 'Hub', 0.12, 0.1, (0, -0.28, 0), VS.ink(), root, rot=(90, 0, 0))
    return {'root': root, 'hour': hp, 'min': mp}


def spin_clock(ck, t0, t1, turns_min=6.0, turns_hour=0.5):
    A.set(ck['min'], 'rotation_euler', t0, (0, 0, 0))
    A.set(ck['min'], 'rotation_euler', t1, (0, 2 * math.pi * turns_min, 0))
    A.set(ck['hour'], 'rotation_euler', t0, (0, 0, 0))
    A.set(ck['hour'], 'rotation_euler', t1, (0, 2 * math.pi * turns_hour, 0))
    from acting import _linear
    _linear(ck['min'], 'rotation_euler')
    _linear(ck['hour'], 'rotation_euler')


def speed_lines(nm, center, t0, t1, n=10, length=6.0, rad=3.5, col='#FFFFFF', axis='y'):
    """streaks rushing past the camera (anime speed lines) around a world point, moving along -axis"""
    m = VS.glow(nm + 'M', col, 3.0)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n + 0.3 * (i % 3)
        r = rad * (0.8 + 0.4 * ((i * 37) % 10) / 10)
        x, z = center[0] + r * math.cos(a), center[2] + r * math.sin(a)
        ob = box(f'{nm}{i}', (0.06, length, 0.06), (x, center[1], z), m)
        ob.visible_shadow = False
        ph = (i * 0.13) % 0.4
        t = t0 - ph
        while t < t1:
            A.set(ob, 'location', max(t0, t), (x, center[1] + 14, z))
            A.set(ob, 'location', max(t0, t) + 0.4, (x, center[1] - 14, z))
            t += 0.4
        out.append(ob)
    show(out, [(t0, t1)])
    return out


# ---------------------------------------------------------------- QA + render
def drop_frame0():
    """A.jump at t=0 keys the old pose on frame 0; motion blur on frame 1 then smears that jump. Remove those keys."""
    from acting import _fcurves
    for ob in bpy.data.objects:
        for fc in _fcurves(ob):
            for kp in [k for k in fc.keyframe_points if k.co.x < 0.5]:
                fc.keyframe_points.remove(kp)


def cam_check(SETS, BOUNDS):
    sc = bpy.context.scene
    for n, _ in E.T:
        t0, t1 = E.S[n]
        cam = E.cams[n]
        si = int(round(E.RIG[n].location.x / 300.0))
        b = BOUNDS.get(SETS[si])
        for f in range(F(t0), F(t1), 2):
            sc.frame_set(f)
            p = cam.matrix_world.translation
            lx, ly, lz = p.x - 300.0 * si, p.y, p.z
            bad = lz < 0.4 if b is None else not (b[0] <= lx <= b[1] and b[2] <= ly <= b[3] and b[4] <= lz <= b[5])
            if bad:
                print(f'CAMWARN {n} f{f} local=({lx:.1f},{ly:.1f},{lz:.1f})')
                break


def run(args, SETS, BOUNDS):
    set_of = {n: SETS[int(round(E.RIG[n].location.x / 300.0))] for n, _ in E.T}
    names = [n for n, _ in E.T]
    for i, n in enumerate(names[1:], 1):
        if n in E.TRANS:
            continue
        same = set_of[names[i - 1]] == set_of[n]
        E.TRANS[n] = (0 if HARD_INSIDE else 4) if same else CROSS_T
    print('CUTS hard:', sum(1 for n in names[1:] if E.TRANS[n] == 0), 'dissolves:', sum(1 for n in names[1:] if E.TRANS[n] > 0),
          'shots:', len(names), 'avg %.2fs' % (E.END_T / len(names)))
    drop_frame0()
    if os.environ.get('PROBE'):
        exec(open(os.environ['PROBE']).read())
        raise SystemExit(0)
    if os.environ.get('CAMCHECK'):
        E.fly_throughs(set_of)
        cam_check(SETS, BOUNDS)
        raise SystemExit(0)
    for rg in E.RIGS:
        V.ink_chars(rg, 0.075, 0.4)
    E.render(args, SETS, finish=V.grade, glow=0.4)
