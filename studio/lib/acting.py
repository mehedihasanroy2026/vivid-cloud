"""Reusable animation helpers for episodes (timeline in seconds, 30 fps).

    from acting import F, deg, W, A, shake, bob, walk, pop, ranges_visible, expr, Shots
"""
import math
import random
import bpy
import doodle_char as dc

FPS = 30


def F(t):
    return int(round(t * FPS)) + 1


def deg(*a):
    return tuple(math.radians(x) for x in a)


def W(o, p):
    return (o[0] + p[0], o[1] + p[1], o[2] + (p[2] if len(p) > 2 else 0))


class Anim:
    """Keyframes with memory, so a value can 'jump' cleanly on a cut."""
    def __init__(self):
        self.last = {}

    def set(self, ob, path, t, val, frame=None):
        f = frame if frame is not None else F(t)
        setattr(ob, path, val)
        ob.keyframe_insert(path, frame=f)
        self.last[(ob.name, path)] = tuple(val) if hasattr(val, '__len__') else val

    def jump(self, ob, path, t, val):
        k = (ob.name, path)
        if k in self.last:
            setattr(ob, path, self.last[k])
            ob.keyframe_insert(path, frame=F(t) - 1)
        self.set(ob, path, t, val)


A = Anim()


def shake(ob, t0, t1, amp, seed=0, every=1):
    rnd = random.Random(seed)
    f0, f1 = F(t0), F(t1)
    ob.location = (0, 0, 0)
    ob.keyframe_insert('location', frame=f0 - 1)
    for f in range(f0, f1, every):
        ob.location = (rnd.uniform(-amp, amp), rnd.uniform(-amp * 0.3, amp * 0.3), rnd.uniform(-amp * 0.4, amp * 0.4))
        ob.keyframe_insert('location', frame=f)
    ob.location = (0, 0, 0)
    ob.keyframe_insert('location', frame=f1)
    A.last[(ob.name, 'location')] = (0, 0, 0)


def bob(ob, t0, t1, amp=0.06, period=0.5):
    """Bounce a character's body (root) up and down."""
    t, up = t0, False
    while t < t1:
        ob.location = (0, 0, amp if up else 0)
        ob.keyframe_insert('location', frame=F(t))
        t += period / 2
        up = not up
    ob.location = (0, 0, 0)
    ob.keyframe_insert('location', frame=F(t1))
    A.last[(ob.name, 'location')] = (0, 0, 0)


def walk(rig, t0, t1, p0, p1, step=0.27, swing=24):
    """Walk the mover from p0 to p1 (world coords) with leg/arm swing and bounce."""
    m, r = rig['mover'], rig['root']
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    face = math.degrees(math.atan2(dx, -dy))        # character faces -Y at 0
    A.jump(m, 'location', t0, p0)
    A.jump(m, 'rotation_euler', t0, deg(0, 0, face))
    A.set(m, 'location', t1, p1)
    t, k = t0, 0
    while t < t1:
        a = swing if k % 2 else -swing
        A.set(rig['hipL'], 'rotation_euler', t, deg(a, 0, 0))
        A.set(rig['hipR'], 'rotation_euler', t, deg(-a, 0, 0))
        A.set(rig['shoulderL'], 'rotation_euler', t, deg(-a * 0.8, 0, 0))
        A.set(rig['shoulderR'], 'rotation_euler', t, deg(a * 0.8, 0, 0))
        A.set(r, 'location', t, (0, 0, 0))
        A.set(r, 'location', t + step / 2, (0, 0, 0.12))
        t += step
        k += 1
    for side in ('hipL', 'hipR', 'shoulderL', 'shoulderR'):
        A.set(rig[side], 'rotation_euler', t1 + 0.1, deg(0, 0, 0))
    A.set(r, 'location', t1, (0, 0, 0))
    # make the walk itself linear (constant speed)
    _linear(m, 'location')


def _fcurves(ob):
    ad = ob.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, 'fcurves') and len(getattr(act, 'fcurves', [])):
        return list(act.fcurves)
    out = []
    for layer in getattr(act, 'layers', []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                out.extend(cb.fcurves)
    return out


def _linear(ob, path):
    for fc in _fcurves(ob):
        if fc.data_path == path:
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'


def pop(ob, t, size=1.0, hide_before=True):
    """Pop an object in with a little overshoot."""
    if hide_before:
        A.set(ob, 'scale', 0, (0.001,) * 3)
    A.set(ob, 'scale', t, (0.001,) * 3)
    A.set(ob, 'scale', t + 0.12, (size * 1.25,) * 3)
    A.set(ob, 'scale', t + 0.24, (size,) * 3)


def unpop(ob, t):
    A.set(ob, 'scale', t, A.last.get((ob.name, 'scale'), (1, 1, 1)))
    A.set(ob, 'scale', t + 0.12, (0.001,) * 3)


def ranges_visible(objs, ranges, flicker=0):
    """Show objects only inside the given (t0, t1) ranges. flicker = toggle every n frames."""
    for o in objs:
        targets = [o] + list(o.children_recursive)
        for ob in targets:
            ob.hide_render = True
            ob.keyframe_insert('hide_render', frame=1)
            for t0, t1 in ranges:
                f = F(t0)
                on = True
                while f < F(t1):
                    ob.hide_render = not on
                    ob.keyframe_insert('hide_render', frame=f)
                    if not flicker:
                        break
                    f += flicker
                    on = not on
                ob.hide_render = True
                ob.keyframe_insert('hide_render', frame=F(t1))


def expr(rig, t, which):
    dc.set_expression(rig, which, frame=F(t))


def nod(neck, t0, t1, amp=10, period=0.35):
    t, k = t0, 0
    while t < t1:
        A.set(neck, 'rotation_euler', t, deg(amp if k % 2 else -amp * 0.4, 0, 0))
        t += period
        k += 1
    A.set(neck, 'rotation_euler', t1, deg(0, 0, 0))


def head_shake(neck, t0, t1, amp=20, period=0.12):
    t, k = t0, 0
    while t < t1:
        A.set(neck, 'rotation_euler', t, deg(0, 0, amp if k % 2 else -amp))
        t += period
        k += 1
    A.set(neck, 'rotation_euler', t1, deg(0, 0, 0))
