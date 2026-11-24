"""Generic flat animal (pig, chicken) for the flat+real look, generalised from emu.py.

    p = Beast('Pig', 'pig', loc=(0, 0, 0), facing=1)
    p.run(f0, f1); p.peck(f); p.expr(f, 'shocked'); p.hop(f)
Layers: legs flip-book, body, head pivot (expression swaps). Registers in flat_char.CHARS (baked by F.finish).
"""
import math
import random
import bpy
import flat_char as F

SPECS = {
    # legs (w, h, centre), body (w, h, centre), head pivot (x, z), head (w, h, centre rel. pivot), poses, exprs, run cycle
    'pig': dict(legs=(1.0, 0.5, (0.0, 0.25)), body=(1.0, 0.75, (0.0, 0.78)), pivot=(0.42, 0.86),
                head=(0.58, 0.58, (0.12, 0.0)), poses=['stand', 'walk0', 'walk1', 'walk2', 'walk3'],
                exprs=['neutral', 'happy', 'shocked', 'munch'], cycle=['walk0', 'walk1', 'walk2', 'walk3'], peck_pose='stand'),
    'chick': dict(legs=(0.42, 0.42, (0.0, 0.21)), body=(0.62, 0.465, (0.0, 0.58)), pivot=(0.17, 0.62),
                  head=(0.3, 0.45, (0.0, 0.2)), poses=['stand', 'run0', 'run1', 'run2', 'run3', 'peck'],
                  exprs=['neutral', 'shocked', 'squawk', 'headless'], cycle=['run0', 'run1', 'run2', 'run3'], peck_pose='peck'),
}


class Beast:
    def __init__(self, name, kind, loc=(0, 0, 0), scale=1.0, facing=1, seed=0):
        sp = SPECS[kind]
        self.sp, self.kind, self.name = sp, kind, name
        self.rnd = random.Random(seed or hash(name) & 0xffff)
        mk = lambda n, par: _empty(n, par)
        self.root = mk(name, None)
        self.root.location = loc
        self.root.scale = (scale,) * 3
        self.card = mk(name + '_card', self.root)
        self.flip = mk(name + '_flip', self.card)
        self.flip.scale = (facing, 1, 1)
        self.bob = mk(name + '_bob', self.flip)
        lw, lh, lc = sp['legs']
        self.legs = {p: F._plane(f'{name}_legs_{p}', f'{kind}_legs_{p}', lw, lh, lc, -0.01, self.flip) for p in sp['poses']}
        bw, bh, bc = sp['body']
        self.body = F._plane(name + '_body', f'{kind}_body', bw, bh, bc, 0.0, self.bob)
        self.headp = mk(name + '_head', self.bob)
        self.headp.location = (sp['pivot'][0], 0, sp['pivot'][1])
        hw, hh, hc = sp['head']
        self.heads = {e: F._plane(f'{name}_h_{e}', f'{kind}_head_{e}', hw, hh, hc, 0.012, self.headp) for e in sp['exprs']}
        self.pose_tl = {0: 'stand'}
        self.expr_tl = {0: 'neutral'}
        F.CHARS.append(self)

    def expr(self, f, kind):
        self.expr_tl[int(f)] = kind

    def pose(self, f, p):
        self.pose_tl[int(f)] = p

    def run(self, f0, f1, period=8, bounce=0.05):
        f0, f1 = int(f0), int(f1)
        cyc = self.sp['cycle']
        step = max(1, period // len(cyc))
        f, i = f0, self.rnd.randint(0, 3)
        while f < f1:
            self.pose_tl[f] = cyc[i % len(cyc)]
            self.bob.location.z = bounce if i % 2 else 0.0
            self.bob.keyframe_insert('location', index=2, frame=f)
            f += step
            i += 1
        self.pose_tl[f1] = 'stand'
        self.bob.location.z = 0.0
        self.bob.keyframe_insert('location', index=2, frame=f1)

    def _rot(self, f, deg):
        self.headp.rotation_euler.y = math.radians(deg)
        self.headp.keyframe_insert('rotation_euler', index=1, frame=int(f))

    def peck(self, f, n=1, deg=60):
        for k in range(n):
            g = int(f) + k * 12
            self._rot(g, 0)
            self._rot(g + 5, deg)
            self.pose_tl[g + 2] = self.sp['peck_pose']
            self._rot(g + 10, 0)
            self.pose_tl[g + 11] = 'stand'

    def tilt(self, f, deg, dur=5):
        self.headp.keyframe_insert('rotation_euler', index=1, frame=int(f) - dur)
        self._rot(f, deg)

    def hop(self, f, h=0.2):
        for t, z in ((f, 0), (f + 4, h), (f + 9, 0)):
            self.bob.location.z = z
            self.bob.keyframe_insert('location', index=2, frame=int(t))

    def flap(self, f0, f1, amp=6):
        """Jittery whole-body shake (wing-flap panic)."""
        f = int(f0)
        i = 0
        while f < f1:
            self.bob.rotation_euler.y = math.radians(amp if i % 2 else -amp)
            self.bob.keyframe_insert('rotation_euler', index=1, frame=f)
            f += 2
            i += 1
        self.bob.rotation_euler.y = 0
        self.bob.keyframe_insert('rotation_euler', index=1, frame=int(f1))

    def breathe(self, f0, f1):
        pass

    def bake(self, cam, frame_end):
        lt = self.card.constraints.new('LOCKED_TRACK')
        lt.target = cam
        lt.track_axis = 'TRACK_NEGATIVE_Y'
        lt.lock_axis = 'LOCK_Z'
        for tl, obs in ((self.pose_tl, self.legs), (self.expr_tl, self.heads)):
            keys = sorted(tl.items())
            for k, ob in obs.items():
                ob.hide_render = k != keys[0][1]
                ob.keyframe_insert('hide_render', frame=0)
                last = not ob.hide_render
                for t, v in keys:
                    vis = (v == k)
                    if vis != last:
                        ob.hide_render = not vis
                        ob.keyframe_insert('hide_render', frame=t)
                        last = vis
                for fc in _fc(ob):
                    for kp in fc.keyframe_points:
                        kp.interpolation = 'CONSTANT'
        for fc in _fc(self.bob):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'


def _empty(n, par):
    e = bpy.data.objects.new(n, None)
    bpy.context.collection.objects.link(e)
    e.parent = par
    return e


def _fc(ob):
    ad = ob.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    try:
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        return list(action_get_channelbag_for_slot(act, ad.action_slot).fcurves)
    except Exception:
        return list(getattr(act, 'fcurves', []))
