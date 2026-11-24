"""Flat emu for the flat+real look (EP31). Sprites from lib/emu_sprites.py (assets/flat/emu_*.png).

    e = Emu('E1', loc=(0, 0, 0), facing=1)       # facing +1 = beak to camera-right, -1 = camera-left
    e.run(f0, f1); e.move(f0, f1, loc0, loc1); e.peck(f); e.expr(f, 'smug'); e.look(f, deg)
Layers: legs (flip-book of leg poses), body, neck pivot (expressions swap, neck can bend for pecks/looks).
Registers in flat_char.CHARS so flat_char.finish(cam) bakes it with the people.
"""
import math
import random
import bpy
import flat_char as F

POSES = ['stand', 'run0', 'run1', 'run2', 'run3', 'peck']
EXPRS = ['neutral', 'smug', 'shocked', 'squawk']


class Emu:
    def __init__(self, name, loc=(0, 0, 0), scale=0.72, facing=1, seed=0):
        self.name = name
        self.rnd = random.Random(seed or hash(name) & 0xffff)
        self.root = bpy.data.objects.new(name, None)
        bpy.context.collection.objects.link(self.root)
        self.root.location = loc
        self.root.scale = (scale,) * 3
        self.card = bpy.data.objects.new(name + '_card', None)
        bpy.context.collection.objects.link(self.card)
        self.card.parent = self.root
        self.flip = bpy.data.objects.new(name + '_flip', None)
        bpy.context.collection.objects.link(self.flip)
        self.flip.parent = self.card
        self.flip.scale = (facing, 1, 1)
        self.facing = facing
        self.bob = bpy.data.objects.new(name + '_bob', None)
        bpy.context.collection.objects.link(self.bob)
        self.bob.parent = self.flip
        self.legs = {p: F._plane(f'{name}_legs_{p}', f'emu_legs_{p}', 1.0, 1.0, (0.0, 0.5), -0.01, self.flip) for p in POSES}
        self.body = F._plane(name + '_body', 'emu_body', 1.15, 0.8625, (0.0, 1.17), 0.0, self.bob)
        self.neckp = bpy.data.objects.new(name + '_neck', None)
        bpy.context.collection.objects.link(self.neckp)
        self.neckp.parent = self.bob
        self.neckp.location = (0.36, 0, 1.30)
        self.necks = {e: F._plane(f'{name}_neck_{e}', f'emu_neck_{e}', 0.55, 1.1, (0.0, 0.5), 0.012, self.neckp) for e in EXPRS}
        self.pose_tl = {0: 'stand'}
        self.expr_tl = {0: 'neutral'}
        F.CHARS.append(self)

    # ------------------------------------------------------------------ acting
    def expr(self, f, kind):
        self.expr_tl[int(f)] = kind

    def pose(self, f, p):
        self.pose_tl[int(f)] = p

    def run(self, f0, f1, period=8, bounce=0.07):
        """Flip-book run cycle + body bob. period = frames per full stride (4 poses)."""
        f0, f1 = int(f0), int(f1)
        step = max(1, period // 4)
        ph = self.rnd.randint(0, 3)
        f, i = f0, ph
        while f < f1:
            self.pose_tl[f] = f'run{i % 4}'
            self.bob.location.z = bounce if i % 2 else 0.0
            self.bob.keyframe_insert('location', index=2, frame=f)
            f += step
            i += 1
        self.pose_tl[f1] = 'stand'
        self.bob.location.z = 0.0
        self.bob.keyframe_insert('location', index=2, frame=f1)
        # neck pumps forward while running
        self._neck_rot(f0, 0)
        self._neck_rot(f0 + 4, -14)
        self._neck_rot(f1 - 2, -14)
        self._neck_rot(f1 + 4, 0)

    def _neck_rot(self, f, deg):
        self.neckp.rotation_euler.y = math.radians(deg)     # card space: +y rotation tips the head toward +x (beak side)
        self.neckp.keyframe_insert('rotation_euler', index=1, frame=int(f))

    def peck(self, f, n=1):
        for k in range(n):
            g = int(f) + k * 12
            self._neck_rot(g, 0)
            self._neck_rot(g + 5, 95)
            self.pose_tl[g + 2] = 'peck'
            self._neck_rot(g + 10, 0)
            self.pose_tl[g + 11] = 'stand'

    def look(self, f, deg, dur=5):
        """Lean the head (deg > 0 toward the beak side, < 0 back)."""
        self.neckp.keyframe_insert('rotation_euler', index=1, frame=int(f) - dur)
        self._neck_rot(f, deg)

    def tilt(self, f, deg, dur=5):
        """Cock the head: a small roll of the whole neck around the view axis."""
        self.neckp.keyframe_insert('rotation_euler', index=1, frame=int(f) - dur)
        self._neck_rot(f, deg)

    def hop(self, f, h=0.2):
        for t, z in ((f, 0), (f + 4, h), (f + 9, 0)):
            self.bob.location.z = z
            self.bob.keyframe_insert('location', index=2, frame=int(t))

    def move(self, f0, f1, loc0, loc1, run=True, period=8):
        self.root.location = loc0
        self.root.keyframe_insert('location', frame=int(f0))
        self.root.location = loc1
        self.root.keyframe_insert('location', frame=int(f1))
        for fc in F_fcurves(self.root):
            for kp in fc.keyframe_points:
                if int(round(kp.co.x)) in (int(f0), int(f1)):
                    kp.interpolation = 'LINEAR'
        if run:
            self.run(f0, f1, period)

    def breathe(self, f0, f1):
        pass

    # ------------------------------------------------------------------ bake
    def bake(self, cam, frame_end):
        lt = self.card.constraints.new('LOCKED_TRACK')
        lt.target = cam
        lt.track_axis = 'TRACK_NEGATIVE_Y'
        lt.lock_axis = 'LOCK_Z'
        for tl, obs in ((self.pose_tl, self.legs), (self.expr_tl, self.necks)):
            keys = sorted(tl.items())
            for k, ob in obs.items():
                last = None
                ob.hide_render = k != keys[0][1]
                ob.keyframe_insert('hide_render', frame=0)
                last = not ob.hide_render
                for t, v in keys:
                    vis = (v == k)
                    if vis != last:
                        ob.hide_render = not vis
                        ob.keyframe_insert('hide_render', frame=t)
                        last = vis
                for fc in F_fcurves(ob):
                    for kp in fc.keyframe_points:
                        kp.interpolation = 'CONSTANT'
        for fc in F_fcurves(self.bob):
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'


def F_fcurves(ob):
    ad = ob.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    try:
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        return list(action_get_channelbag_for_slot(act, ad.action_slot).fcurves)
    except Exception:
        return list(getattr(act, 'fcurves', []))
