"""Flat cut-out characters inside 3D sets (the look of the reference channel's newer Shorts).

Every character is a 'card' of flat drawn parts (PNG sprites from flat_sprites.py) plus
black curve limbs. The card always turns to face the camera (Locked Track around Z), so
the character reads as a drawing while the world around it is fully 3D.

    import flat_char as F
    a = F.Char('Ned', head='head_messy', body='body_sweater', hat='hat_beanie', loc=(0, 0, 0), scale=0.55)
    a.say(10, 60)            # mouth flaps
    a.expr(70, 'grimace')
    a.nod(80)
    a.arm('R', 40, elbow=(0.55, 1.9), hand=(0.65, 2.4))
    F.finish(cam)            # bakes face switches, points every card at cam

Card space: X right, Z up, feet at z=0, about 3.4 units tall before scale.
"""
import math
import os
import random
import bpy
import bmesh
from mathutils import Vector

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'flat')
EXPRS = ['neutral', 'talk', 'talk2', 'oh', 'smug', 'happy', 'grin', 'grimace', 'shocked', 'blink', 'worried', 'stern']
INK = (0.006, 0.005, 0.005, 1)
CHARS = []
GLOW = float(os.environ.get("FGLOW", 1.0))         # self-lit brightness of the drawing (tuned for the Khronos PBR Neutral view)
WHITE_BOOST = float(os.environ.get("FBOOST", 0.5))  # extra glow for near-white parts
FLAT = 0.62         # 1 = pure flat drawing, 0 = fully lit by the scene
SAT = 1.0           # saturation lift for the sprite colours
LINE = 0.036        # limb bevel radius (card units)


def _mat_img(name, file):
    """Drawing material: mostly self-lit (FLAT) so colours stay clean and saturated like a drawing,
    plus a little real light (1-FLAT) so the scene's warm/cool light and shadows still touch it."""
    key = 'F_' + name
    if key in bpy.data.materials:
        return bpy.data.materials[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    out = N['Material Output']
    b = N['Principled BSDF']
    t = N.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(os.path.join(ART, file + '.png'), check_existing=True)
    t.interpolation = 'Cubic'
    # small saturation lift to survive AgX's highlight desaturation
    hs = N.new('ShaderNodeHueSaturation')
    hs.inputs['Saturation'].default_value = SAT
    L.new(t.outputs['Color'], hs.inputs['Color'])
    L.new(hs.outputs[0], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.8
    try:
        b.inputs['Specular IOR Level'].default_value = 0.1
    except Exception:
        pass
    em = N.new('ShaderNodeEmission')
    L.new(hs.outputs[0], em.inputs['Color'])
    em.inputs['Strength'].default_value = GLOW
    # near-white pixels (skin, paper, eye whites) glow extra so they read paper-white after AgX;
    # saturated colours keep plain GLOW so they stay rich instead of washing out
    sep = N.new('ShaderNodeSeparateColor')
    L.new(t.outputs['Color'], sep.inputs[0])
    m1 = N.new('ShaderNodeMath'); m1.operation = 'MINIMUM'
    L.new(sep.outputs[0], m1.inputs[0]); L.new(sep.outputs[1], m1.inputs[1])
    m2 = N.new('ShaderNodeMath'); m2.operation = 'MINIMUM'
    L.new(m1.outputs[0], m2.inputs[0]); L.new(sep.outputs[2], m2.inputs[1])
    mr = N.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.55
    mr.inputs['From Max'].default_value = 0.95
    mr.inputs['To Min'].default_value = GLOW
    mr.inputs['To Max'].default_value = GLOW + WHITE_BOOST
    L.new(m2.outputs[0], mr.inputs['Value'])
    L.new(mr.outputs[0], em.inputs['Strength'])
    mix = N.new('ShaderNodeMixShader')
    mix.inputs[0].default_value = FLAT
    L.new(b.outputs[0], mix.inputs[1])
    L.new(em.outputs[0], mix.inputs[2])
    tr = N.new('ShaderNodeBsdfTransparent')
    cut = N.new('ShaderNodeMixShader')
    L.new(t.outputs['Alpha'], cut.inputs[0])
    L.new(tr.outputs[0], cut.inputs[1])
    L.new(mix.outputs[0], cut.inputs[2])
    L.new(cut.outputs[0], out.inputs['Surface'])
    try:
        m.surface_render_method = 'DITHERED'
    except Exception:
        m.blend_method = 'HASHED'
    return m


def _mat_ink():
    if 'F_ink' in bpy.data.materials:
        return bpy.data.materials['F_ink']
    m = bpy.data.materials.new('F_ink')
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = INK
    b.inputs['Roughness'].default_value = 0.9
    return m


def _plane(name, file, w, h, center, depth, parent):
    """Image quad in the card's XZ plane; depth = offset toward the camera (-Y)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    vs = [bm.verts.new((center[0] + x * w / 2, -depth, center[1] + z * h / 2))
          for x, z in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    f = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new()
    for lp, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uv].uv = c
    bm.to_mesh(me)
    bm.free()
    me.materials.append(_mat_img(file, file))
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.parent = parent
    return ob


def _curve(name, pts, parent, depth):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = LINE
    cu.bevel_resolution = 3
    cu.use_fill_caps = True
    sp = cu.splines.new('NURBS')
    sp.points.add(len(pts) - 1)
    for p, (x, z) in zip(sp.points, pts):
        p.co = (x, -depth, z, 1)
    sp.order_u = 3
    sp.use_endpoint_u = True
    sp.resolution_u = 12
    cu.materials.append(_mat_ink())
    ob = bpy.data.objects.new(name, cu)
    bpy.context.collection.objects.link(ob)
    ob.parent = parent
    return ob


def _dot(name, loc, parent, r=0.075):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(_mat_ink())
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.parent = parent
    ob.location = loc
    ob.scale = (1.0, 0.5, 0.85)
    for p in me.polygons:
        p.use_smooth = True
    return ob


class Char:
    # layout (card units)
    HIP_Z, BODY_C, BODY_H = 1.12, 1.62, 1.18
    NECK_Z, HEAD_C, HEAD_D = 2.12, 2.6, 1.0
    SHOULDER = (0.4, 1.98)

    def __init__(self, name, head='head_bald', body='body_sweater', hat=None, loc=(0, 0, 0),
                 scale=0.55, facing=-1, hat_z=0.0, seed=0, acc=()):
        self.name = name
        self.facing = facing
        self.rnd = random.Random(seed or hash(name) & 0xffff)
        self.root = bpy.data.objects.new(name, None)       # world position (animate this)
        bpy.context.collection.objects.link(self.root)
        self.root.location = loc
        self.root.scale = (scale,) * 3
        self.card = bpy.data.objects.new(name + '_card', None)   # turns to the camera
        bpy.context.collection.objects.link(self.card)
        self.card.parent = self.root
        self.bob = bpy.data.objects.new(name + '_bob', None)     # breathing / hops
        bpy.context.collection.objects.link(self.bob)
        self.bob.parent = self.card
        self.body = _plane(name + '_body', body, 1.02, self.BODY_H, (0, self.BODY_C), 0.0, self.bob)
        self.headp = bpy.data.objects.new(name + '_neck', None)
        bpy.context.collection.objects.link(self.headp)
        self.headp.parent = self.bob
        self.headp.location = (0, 0, self.NECK_Z)
        hz = self.HEAD_C - self.NECK_Z
        self.head = _plane(name + '_head', head, 1.0, 1.0, (0, hz), 0.02, self.headp)
        self.faces = {}
        for e in EXPRS:
            self.faces[e] = _plane(f'{name}_f_{e}', f'face_{e}', 1.0, 1.0, (0, hz), 0.03, self.headp)
        self.accs = [_plane(f'{name}_acc{i}', f, 1.0, 1.0, (0, hz), 0.035, self.headp) for i, f in enumerate(acc)]
        self.hat = None
        if hat:
            self.hat = _plane(name + '_hat', hat, 1.04, 0.61, (0, hz + 0.42 + hat_z), 0.04, self.headp)
        sx, sz = self.SHOULDER
        f = facing
        self.legs = {}
        self.leg_x = {'L': -0.17, 'R': 0.17}
        for s, x in self.leg_x.items():
            self.legs[s] = _curve(f'{name}_leg{s}', self._leg_pts(x), self.bob, -0.01)
        self.arms, self.hands = {}, {}
        for s, sg in (('L', -1), ('R', 1)):
            pts = [(sg * sx, sz), (sg * (sx + 0.14), 1.6), (sg * (sx + 0.08), 1.25)]
            self.arms[s] = _curve(f'{name}_arm{s}', pts, self.bob, 0.05)
            self.hands[s] = _dot(f'{name}_hand{s}', (pts[-1][0], -0.05, pts[-1][1]), self.bob)
        self.timeline = {1: 'neutral'}
        self.base = 'neutral'
        CHARS.append(self)

    def _leg_pts(self, x, sw=0.0, lift=0.0):
        """sw: foot swing along the walk direction (card x), lift: foot off the ground."""
        f = self.facing
        return [(x, self.HIP_Z + 0.1), (x + 0.02 + f * sw * 0.45, 0.58 + lift * 0.6),
                (x + f * sw, 0.06 + lift), (x + f * (sw + 0.2), lift * 0.8)]

    def _key_leg(self, side, fr, sw=0.0, lift=0.0):
        sp = self.legs[side].data.splines[0]
        for p, (x, z) in zip(sp.points, self._leg_pts(self.leg_x[side], sw, lift)):
            p.co = (x, 0.01, z, 1)
            p.keyframe_insert('co', frame=fr)

    def walk(self, f0, f1, step=6, stride=0.17, lift=0.09, arms=False):
        """Stepping legs (and optional arm swing) between f0 and f1; one step = `step` frames."""
        f0, f1 = int(f0), int(f1)
        for s in ('L', 'R'):
            self._key_leg(s, f0 - 1)
        i, fr = 0, f0
        while fr < f1:
            a, b = ('L', 'R') if i % 2 == 0 else ('R', 'L')
            self._key_leg(a, fr, stride, 0.0)              # front foot planted
            self._key_leg(b, fr, -stride, 0.0)             # back foot pushing off
            mid = fr + step // 2
            if mid < f1:
                self._key_leg(b, mid, 0.0, lift)           # back foot swings through, lifted
                self._key_leg(a, mid, 0.0, 0.0)
            if arms:
                sg = 1 if a == 'L' else -1
                for side, k in (('L', 1), ('R', -1)):
                    d = sg * k * self.facing
                    self.arm(side, fr, elbow=(k * -0.54 + 0.08 * d, 1.62), hand=(k * -0.48 + 0.2 * d, 1.27), dur=0)
            fr += step
            i += 1
        for s in ('L', 'R'):
            self._key_leg(s, f1 + 2)

    # ------------------------------------------------------------- acting
    def expr(self, f, kind):
        self.base = kind
        self.timeline[int(f)] = kind

    def say(self, f0, f1, rate=4):
        """Mouth flaps between f0 and f1, returns to the base face after."""
        base = self.base
        f = int(f0)
        i = 0
        while f < f1:
            self.timeline[f] = ('talk', 'talk2', 'neutral' if base in ('neutral', 'talk') else base, 'talk')[i % 4]
            f += rate + self.rnd.choice((0, 0, 1))
            i += 1
        self.timeline[int(f1)] = base

    def blink(self, f):
        prev = self._face_at(f)
        if prev in ('neutral', 'talk', 'talk2', 'oh', 'worried', 'stern'):
            self.timeline[int(f)] = 'blink'
            self.timeline[int(f) + 3] = prev

    def _face_at(self, f):
        k = max([t for t in self.timeline if t <= f], default=1)
        return self.timeline[k]

    def nod(self, f, depth=0.07, n=1):
        for i in range(n):
            g = f + i * 9
            for t, z, r in ((g, 0, 0), (g + 4, -depth, 4), (g + 9, 0, 0)):
                self.headp.location.z = self.NECK_Z + z
                self.headp.keyframe_insert('location', index=2, frame=t)
                self.headp.rotation_euler.y = math.radians(-r * self.facing * 0.3)
                self.headp.keyframe_insert('rotation_euler', index=1, frame=t)

    def tilt(self, f, deg, dur=6):
        k = self.headp
        k.keyframe_insert('rotation_euler', index=1, frame=f)
        k.rotation_euler.y = math.radians(deg)
        k.keyframe_insert('rotation_euler', index=1, frame=f + dur)

    def arm(self, side, f, elbow, hand, dur=6):
        """Move one arm (card coords) so it arrives at frame f; keys the previous pose at f-dur."""
        cu = self.arms[side].data.splines[0]
        h = self.hands[side]
        for p in cu.points:
            p.keyframe_insert('co', frame=f - dur)
        h.keyframe_insert('location', frame=f - dur)
        cu.points[1].co = (elbow[0], -0.05, elbow[1], 1)
        cu.points[2].co = (hand[0], -0.05, hand[1], 1)
        h.location = (hand[0], -0.05, hand[1])
        for p in cu.points:
            p.keyframe_insert('co', frame=f)
        h.keyframe_insert('location', frame=f)

    def breathe(self, f0, f1, amp=0.012, period=48):
        ph = self.rnd.random() * period
        for f in range(int(f0), int(f1) + 1, 6):
            s = math.sin((f + ph) / period * 2 * math.pi)
            self.bob.scale = (1 - amp * 0.5 * s, 1, 1 + amp * s)
            self.bob.keyframe_insert('scale', frame=f)

    def hop(self, f, h=0.25):
        for t, z in ((f, 0), (f + 4, h), (f + 9, 0), (f + 11, -0.03), (f + 14, 0)):
            self.bob.location.z = z
            self.bob.keyframe_insert('location', index=2, frame=t)

    def move(self, f0, f1, loc0, loc1, steps=True):
        self.root.location = loc0
        self.root.keyframe_insert('location', frame=f0)
        self.root.location = loc1
        self.root.keyframe_insert('location', frame=f1)
        if steps:
            self.walk(f0, f1)
            for f in range(int(f0), int(f1), 6):
                self.bob.location.z = 0.0
                self.bob.keyframe_insert('location', index=2, frame=f)
                self.bob.location.z = 0.06
                self.bob.keyframe_insert('location', index=2, frame=f + 3)

    # ------------------------------------------------------------- bake
    def bake(self, cam, frame_end):
        lt = self.card.constraints.new('LOCKED_TRACK')
        lt.target = cam
        lt.track_axis = 'TRACK_NEGATIVE_Y'
        lt.lock_axis = 'LOCK_Z'
        # random idle blinks
        f = self.rnd.randint(20, 60)
        while f < frame_end - 5:
            self.blink(f)
            f += self.rnd.randint(55, 110)
        keys = sorted(self.timeline.items())
        for e, ob in self.faces.items():
            ob.hide_render = True
            ob.keyframe_insert('hide_render', frame=0)
            ob.hide_viewport = True
            ob.keyframe_insert('hide_viewport', frame=0)
            last = None
            for t, k in keys:
                vis = (k == e)
                if vis != last:
                    ob.hide_render = not vis
                    ob.keyframe_insert('hide_render', frame=t)
                    ob.hide_viewport = not vis
                    ob.keyframe_insert('hide_viewport', frame=t)
                    last = vis


def finish(cam):
    fe = bpy.context.scene.frame_end
    for c in CHARS:
        c.bake(cam, fe)
