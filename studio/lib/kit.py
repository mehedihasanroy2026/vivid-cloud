"""Shared episode kit for the FLAT REAL batch (EP32-41). Built from the EP31 helpers.

    import kit as K
    K.init(__file__, [('A', None), ('B', 'In 1942'), ...])    # segments start at script phrases (words.json)
    def build_x():
        sc = K.outdoor('farm_field', ...)
        ...
        K.cam_shots({'A': [(0, cam, aim, lens), (0.5, ...), (1, ...)], ...})   # fractions of each segment
        K.finish(cam)
        return sc
    K.run([('x', build_x, 'AB'), ...])

Camera keys are given as fractions of their segment: 0 = the cut in, 1 = 3 frames before the next cut
(EP31 bug: a key that rounds onto the cut frame freezes the whole move).
"""
import argparse
import json
import math
import os
import random
import re
import sys
import time
import bpy
from mathutils import Vector

LIB = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LIB)
import ph
import flat_char as F

FPS = int(os.environ.get('DGN_FPS', '30'))
HERE = ART = ''
SEG, CUTS, ORDER = {}, [], []
END = 0.0
F_END = 0
WORDS, NW = [], []
a = None


def T(s):
    return int(round(s * FPS)) + 1


# ---------------------------------------------------------------- init / timing
def _args():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', default='still')
    ap.add_argument('--t', default='30')
    ap.add_argument('--pct', type=int, default=25)
    ap.add_argument('--samples', type=int, default=8)
    ap.add_argument('--out', default='')
    ap.add_argument('--fs', type=int, default=0)
    ap.add_argument('--fe', type=int, default=0)
    ap.add_argument('--only', default='')
    ap.add_argument('--segs', default='')          # still mode: render the middle of these segments (e.g. ABC or all)
    return ap.parse_args(argv)


def at(phrase, after=0.0):
    p = [re.sub(r'[^a-z0-9]', '', x.lower()) for x in phrase.split()]
    for i in range(len(NW) - len(p) + 1):
        if NW[i:i + len(p)] == p and WORDS[i]['start'] >= after - 1e-6:
            return WORDS[i]['start']
    raise KeyError(phrase)


def at_end(phrase, after=0.0):
    p = [re.sub(r'[^a-z0-9]', '', x.lower()) for x in phrase.split()]
    for i in range(len(NW) - len(p) + 1):
        if NW[i:i + len(p)] == p and WORDS[i]['start'] >= after - 1e-6:
            return WORDS[i + len(p) - 1]['end']
    raise KeyError(phrase)


def init(build_file, timeline, tail=0.45):
    """timeline: [(name, phrase or None)]; each segment starts just before its phrase."""
    global HERE, ART, END, F_END, a, WORDS, NW
    HERE = os.path.dirname(os.path.abspath(build_file))
    ART = os.path.join(HERE, 'art')
    a = _args()
    if not a.out:
        a.out = os.path.join(HERE, 'out', 's_####.png')
    WORDS = json.load(open(os.path.join(HERE, 'words.json'), encoding='utf-8'))
    NW = [re.sub(r'[^a-z0-9]', '', w['word'].lower()) for w in WORDS]
    END = round(WORDS[-1]['end'] + tail, 2)
    F_END = T(END)
    ts = []
    for n, p in timeline:
        t = 0.0 if p is None else max(0.0, at(p) - 0.12)
        ts.append((n, round(t * FPS) / FPS))          # cuts land exactly on frames
    for i, (n, t) in enumerate(ts):
        SEG[n] = (t, ts[i + 1][1] if i + 1 < len(ts) else END + 0.04)
        ORDER.append(n)
    CUTS[:] = [t for _, t in ts[1:]]
    print('DGN: segments', {k: (round(v[0], 2), round(v[1], 2)) for k, v in SEG.items()}, 'END', END)


def s0(k):
    return SEG[k][0]


def s1(k):
    return SEG[k][1]


def sf(k, f):
    """Time at fraction f of segment k (f=1 -> 3 frames before the next cut)."""
    t0, t1 = SEG[k]
    t1 = t1 - 3.0 / FPS
    return t0 + (t1 - t0) * f


def frames_of(keys):
    """keys: segment letters and/or (t0, t1) time ranges."""
    out = []
    for k in keys:
        t0, t1 = SEG[k] if isinstance(k, str) else k
        out.append((T(t0), min(F_END, T(t1) - 1)))
    return out


def add_cut(t):
    """Extra hard cut inside a segment (camera jumps there)."""
    t = round(t * FPS) / FPS
    CUTS.append(t)
    return t


# ---------------------------------------------------------------- animation helpers
def fcurves(ob):
    ad = getattr(ob, 'animation_data', None)
    if not ad or not ad.action:
        return []
    act = ad.action
    try:
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        return list(action_get_channelbag_for_slot(act, ad.action_slot).fcurves)
    except Exception:
        return list(getattr(act, 'fcurves', []))


def const_keys(ob, path='location'):
    for fc in fcurves(ob):
        if fc.data_path == path:
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'


def key_loc(ob, t, loc):
    ob.location = loc
    ob.keyframe_insert('location', frame=T(t))


def ekeys(ob, keys):
    """Location keys [(t, loc, interp)] (interp leaves that key). Keys must be in time order."""
    keys = sorted(keys, key=lambda k: k[0])
    for t, loc, _ in keys:
        ob.location = loc
        ob.keyframe_insert('location', frame=0 if t <= 0 else T(t))
    m = {(0 if t <= 0 else T(t)): ip for t, _, ip in keys}
    for fc in fcurves(ob):
        if fc.data_path == 'location':
            for kp in fc.keyframe_points:
                x = int(round(kp.co.x))
                if x in m:                      # leave keys made by place()/walk() alone
                    kp.interpolation = m[x]


def place(c, keys):
    """Hard-switch a character (or object root) between spots: keys = [(t, loc)], CONSTANT."""
    r = getattr(c, 'root', c)
    for t, loc in sorted(keys, key=lambda k: k[0]):
        r.location = loc
        r.keyframe_insert('location', frame=0 if t <= 0 else T(t))
    const_keys(r)


def only(c, spans, home=None):
    """Character/object visible (at home) only inside spans; parked at z=-60 outside."""
    r = getattr(c, 'root', c)
    home = home or tuple(r.location)
    far = (home[0], home[1], -60)
    keys = [(0.0, far)]
    for t0, t1 in spans:
        keys += [(t0, home), (t1, far)]
    if spans and spans[0][0] <= 0:
        keys = keys[1:]
    place(c, keys)


def show(ob, spans):
    """hide_render switch for an object and its children (only for objects without separately animated kids)."""
    for o in [ob] + list(ob.children_recursive):
        o.hide_render = True
        o.keyframe_insert('hide_render', frame=0)
        for t0, t1 in spans:
            o.hide_render = False
            o.keyframe_insert('hide_render', frame=T(t0))
            o.hide_render = True
            o.keyframe_insert('hide_render', frame=T(t1))
        const_keys(o, 'hide_render')


def pop_scale(ob, t0, t1=None, s=1.0, over=1.25):
    """Scale 0 -> overshoot -> s at t0; back to 0 at t1."""
    seq = [(0.0, 0.0), (t0 - 0.02, 0.0), (t0 + 0.08, s * over), (t0 + 0.16, s * 0.94), (t0 + 0.22, s)]
    if t1:
        seq += [(t1 - 0.08, s), (t1, 0.0)]
    for t, v in seq:
        ob.scale = (v, v, v)
        ob.keyframe_insert('scale', frame=0 if t <= 0 else T(t))


def spin(ob, t0, t1, turns, axis=2):
    ob.rotation_euler[axis] = 0
    ob.keyframe_insert('rotation_euler', index=axis, frame=T(t0))
    ob.rotation_euler[axis] = 2 * math.pi * turns
    ob.keyframe_insert('rotation_euler', index=axis, frame=T(t1))
    for fc in fcurves(ob):
        if fc.data_path == 'rotation_euler':
            for kp in fc.keyframe_points:
                kp.interpolation = 'LINEAR'


def noise_on(ob, path, idx, strength, scale=5):
    ob.keyframe_insert(path, index=idx, frame=1)
    for fc in fcurves(ob):
        if fc.data_path == path and fc.array_index == idx:
            m = fc.modifiers.new('NOISE')
            m.scale = scale
            m.strength = strength


def wobble(ob, t, amp=0.07, n=6):
    base = tuple(ob.scale)
    ob.keyframe_insert('scale', frame=T(t))
    for i in range(1, n + 1):
        k = amp * (1 - i / (n + 1)) * (1 if i % 2 else -1)
        ob.scale = (base[0] * (1 - k * 0.5), base[1] * (1 + k), base[2] * (1 - k))
        ob.keyframe_insert('scale', frame=T(t) + i * 3)
    ob.scale = base
    ob.keyframe_insert('scale', frame=T(t) + (n + 1) * 3)


# ---------------------------------------------------------------- objects
def empty(name, par=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(e)
    e.parent = par
    e.location = loc
    return e


def P(ob, par):
    ob.parent = par
    return ob


def cyl(name, r, depth, loc, rot, mat, verts=28, smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.rotation_euler = [math.radians(v) for v in rot]
    ob.data.materials.append(mat)
    if smooth:
        bpy.ops.object.shade_smooth()
    return ob


def cone(name, r1, r2, depth, loc, rot, mat, verts=24):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.rotation_euler = [math.radians(v) for v in rot]
    ob.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return ob


def sphere(name, r, loc, mat, scale=(1, 1, 1), seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = scale
    ob.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return ob


def rod(name, p0, p1, r, mat, verts=12):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(p0 + p1) / 2)
    ob = bpy.context.active_object
    ob.name = name
    ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    ob.data.materials.append(mat)
    return ob


def blob(name, size, loc, mat, rot=(0, 0, 0)):
    ob = ph.box(name, size, loc, mat, rot=rot, bevel=min(size) * 0.42)
    ob.modifiers['bev'].segments = 5
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.shade_smooth()
    return ob


def top_z(root):
    bpy.context.view_layer.update()
    z = 0.0
    for o in [root] + list(root.children_recursive):
        if o.type == 'MESH':
            for c in o.bound_box:
                z = max(z, (o.matrix_world @ Vector(c)).z)
    return z


def model(mid, loc, rot_z=0.0, scale=1.0, name=None):
    ph.model(mid, loc, (0, 0, rot_z), scale, name=name)
    return bpy.data.objects[name or mid]


def inst(src, loc, rot_z=0.0, scale=1.0, name=None):
    """Linked copy of a model hierarchy (shares mesh data)."""
    def cp(o, par):
        n = o.copy()
        bpy.context.collection.objects.link(n)
        n.parent = par
        for ch in o.children:
            cp(ch, n)
        return n
    r = cp(src, None)
    r.name = name or src.name + '_i'
    r.location = loc
    r.rotation_euler = (0, 0, math.radians(rot_z))
    r.scale = (scale,) * 3
    return r


def plain(name, col, rough=0.6, metal=0.0):
    return ph.plain(name, col, rough, metal)


def glow(name, col, strength):
    return ph.emissive(name, col, strength)


# ---------------------------------------------------------------- flat art (signs, cards, tokens)
def art_mat(file, flat=0.0, rough=0.7, val=1.0, folder=None):
    key = 'ART_' + file + f'_{flat}_{val}'
    if key in bpy.data.materials:
        return bpy.data.materials[key]
    m = bpy.data.materials.new(key)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N['Principled BSDF']
    t = N.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(os.path.join(folder or ART, file + '.png'), check_existing=True)
    t.interpolation = 'Cubic'
    col = t.outputs['Color']
    if val != 1.0:
        hs = N.new('ShaderNodeHueSaturation')
        hs.inputs['Value'].default_value = val
        L.new(col, hs.inputs['Color'])
        col = hs.outputs[0]
    L.new(col, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    out = N['Material Output']
    sh = b.outputs[0]
    if flat:
        em = N.new('ShaderNodeEmission')
        L.new(t.outputs['Color'], em.inputs['Color'])
        em.inputs['Strength'].default_value = 1.0
        mx = N.new('ShaderNodeMixShader')
        mx.inputs[0].default_value = flat
        L.new(sh, mx.inputs[1])
        L.new(em.outputs[0], mx.inputs[2])
        sh = mx.outputs[0]
    tr = N.new('ShaderNodeBsdfTransparent')
    cut = N.new('ShaderNodeMixShader')
    L.new(t.outputs['Alpha'], cut.inputs[0])
    L.new(tr.outputs[0], cut.inputs[1])
    L.new(sh, cut.inputs[2])
    L.new(cut.outputs[0], out.inputs['Surface'])
    try:
        m.surface_render_method = 'DITHERED'
    except Exception:
        m.blend_method = 'HASHED'
    return m


def art_plane(name, file, w, h, loc, rot=(0, 0, 0), parent=None, flat=0.0, val=1.0, folder=None):
    """Quad in local XY (normal +Z), image top toward +Y. rot in degrees."""
    bpy.ops.mesh.primitive_plane_add(size=1)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = (w, h, 1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    ob.data.materials.append(art_mat(file, flat, val=val, folder=folder))
    ob.parent = parent
    ob.location = loc
    ob.rotation_euler = [math.radians(v) for v in rot]
    return ob


def sign(name, file, w, h, loc, rot_z=0, parent=None, flat=0.0):
    """Upright picture facing -Y (rot_z turns it)."""
    return art_plane(name, file, w, h, loc, (90, 0, rot_z), parent, flat)


def floor_art(name, file, w, h, loc, rot_z=0):
    return art_plane(name, file, w, h, loc, (0, 0, rot_z))


CAM = None


def card(name, file, t0, t1, w=0.08, aspect=2.37, y=0.035, x=0.0):
    """Title / word card glued to the camera (pops in with overshoot). Call after make_camera()."""
    ob = art_plane(name, file, w, w / aspect, (x, y, -0.2), parent=CAM, flat=1.0)
    pop_scale(ob, t0, t1, 1.0, 1.3)
    CARD_SPANS.append((t0, t1))
    return ob


CARD_SPANS = []


def _card_focus(cam, fstop):
    """Cards sit 0.2 m from the lens: stop the lens down while one is up so it is sharp."""
    d = cam.data.dof
    d.aperture_fstop = fstop
    d.keyframe_insert('aperture_fstop', frame=0)
    merged = []
    for t0, t1 in sorted(CARD_SPANS):
        if merged and t0 - merged[-1][1] < 0.25:
            merged[-1] = (merged[-1][0], max(t1, merged[-1][1]))
        else:
            merged.append((t0, t1))
    for t0, t1 in merged:
        d.aperture_fstop = 64.0
        d.keyframe_insert('aperture_fstop', frame=T(t0) - 1)
        d.aperture_fstop = fstop
        d.keyframe_insert('aperture_fstop', frame=T(t1) + 1)
    for fc in fcurves(cam.data):
        if 'fstop' in fc.data_path:
            for kp in fc.keyframe_points:
                kp.interpolation = 'CONSTANT'


class Fx:
    """Flat effect sprite (assets/flat/fx_*) that pops in/out; faces -Y."""

    def __init__(self, name, file, size, loc, aspect=1.0, parent=None):
        self.e = empty(name, parent, loc)
        F._plane(name + '_p', file, size, size / aspect, (0, 0), 0.0, self.e)
        self.e.scale = (0, 0, 0)
        self.e.keyframe_insert('scale', frame=0)

    def pop(self, t0, t1, rise=0.0, wobble=0.0):
        f0, f1 = T(t0), T(t1)
        for f, s in ((f0 - 3, 0), (f0 + 2, 1.2), (f0 + 5, 1.0), (f1, 1.0), (f1 + 4, 0)):
            self.e.scale = (s, s, s)
            self.e.keyframe_insert('scale', frame=f)
        if rise:
            z = self.e.location.z
            self.e.keyframe_insert('location', index=2, frame=f0)
            self.e.location.z = z + rise
            self.e.keyframe_insert('location', index=2, frame=f1 + 4)
        return self


def fx_at(name, file, size, loc, t0, t1, rise=0.0, parent=None, aspect=1.0):
    f = Fx(name, file, size, loc, aspect, parent)
    f.pop(t0, t1, rise)
    return f


def sweat(c, t0, t1):
    return fx_at(c.name + '_sweat%d' % int(t0 * 10), 'fx_sweat', 0.32, (0.5, -0.12, 3.0), t0, t1, -0.12, c.bob, 0.75)


def flashes(name, parent, loc, times, size=0.5, file='fx_flash'):
    fx = Fx(name, file, size, loc, parent=parent)
    e = fx.e
    for f in sorted({T(t) for t in times}):
        for df, s in ((-1, 0), (0, 1.0), (1, 0.7), (2, 0)):
            e.scale = (s, s, s)
            e.keyframe_insert('scale', frame=f + df)
    const_keys(e, 'scale')
    return fx


# ---------------------------------------------------------------- acting shortcuts (F.Char)
def person(name, head='head_side', body='body_sweater', hat=None, loc=(0, 0, -60), facing=1, acc=(), hat_z=0.0, scale=0.55):
    c = F.Char(name, head=head, body=body, hat=hat, loc=loc, scale=scale, facing=facing, acc=acc, hat_z=hat_z)
    c.breathe(1, F_END)
    return c


def rest(c, side, t, dur=6):
    sg = 1 if side == 'R' else -1
    c.arm(side, T(t), elbow=(sg * 0.54, 1.6), hand=(sg * 0.48, 1.25), dur=dur)


def rest_both(c, t, dur=6):
    rest(c, 'L', t, dur)
    rest(c, 'R', t, dur)


def point(c, side, t, up=0.0, dur=5):
    sg = 1 if side == 'R' else -1
    c.arm(side, T(t), elbow=(sg * 0.75, 1.95 + up * 0.3), hand=(sg * 1.15, 2.15 + up), dur=dur)


def overhead(c, t, dur=8, hands=('L', 'R')):
    for s in hands:
        sg = 1 if s == 'R' else -1
        c.arm(s, T(t), elbow=(sg * 0.6, 2.6), hand=(sg * 0.32, 3.15), dur=dur)


def hold_front(c, t, dur=6, z=1.7):
    """Both hands forward holding something at chest height."""
    for s, sg in (('L', -1), ('R', 1)):
        c.arm(s, T(t), elbow=(sg * 0.58, 1.72), hand=(sg * 0.22, z), dur=dur)


def flail(c, t0, t1, period=0.36):
    t, i = t0, 0
    while t < t1:
        up = i % 2
        c.arm('L', T(t), elbow=(-0.7, 2.2 if up else 1.8), hand=(-0.9, 2.7 if up else 1.9), dur=max(2, int(period * FPS / 2)))
        c.arm('R', T(t), elbow=(0.7, 1.8 if up else 2.2), hand=(0.95, 1.9 if up else 2.7), dur=max(2, int(period * FPS / 2)))
        t += period / 2
        i += 1


def dance(c, t0, t1, period=0.5, h=0.14, seed=0):
    """Wild dancing: arms swing up/out alternately, hops on the beat, head tilts."""
    rnd = random.Random(seed)
    t, i = t0, 0
    while t < t1:
        up = i % 2
        d = max(2, int(period * FPS / 2) - 1)
        c.arm('L', T(t), elbow=(-0.72, 2.3 if up else 1.9), hand=(-0.6 - 0.4 * rnd.random(), 3.0 if up else 2.0), dur=d)
        c.arm('R', T(t), elbow=(0.72, 1.9 if up else 2.3), hand=(0.6 + 0.4 * rnd.random(), 2.0 if up else 3.0), dur=d)
        if up:
            c.hop(T(t), h=h)
        t += period / 2
        i += 1


def talk(c, t0, t1, expr=None):
    if expr:
        c.expr(T(t0), expr)
    c.say(T(t0), T(t1))


def walk(c, t0, t1, p0, p1, steps=True):
    """Glide p0 -> p1 between t0 and t1 with stepping legs; holds p1 afterwards (safe with place()/only())."""
    f0, f1 = T(t0), T(t1)
    c.move(f0, f1, p0, p1, steps=steps)
    for fc in fcurves(c.root):
        if fc.data_path == 'location':
            for kp in fc.keyframe_points:
                x = int(round(kp.co.x))
                if x == f0:
                    kp.interpolation = 'LINEAR'
                elif x == f1:
                    kp.interpolation = 'CONSTANT'


# ---------------------------------------------------------------- sets / light
# exposure offsets per episode (outdoor, indoor), tuned from test stills against the target luma 0.30-0.40
EXPO_ADJ = {'32': (0.0, 1.1), '33': (0.0, 0.0), '34': (0.3, 1.7), '35': (0.6, 0.0), '36': (0.4, 1.7), '37': (0.0, 0.0),
            '38': (0.5, 1.5), '39': (0.7, 2.1), '40': (0.7, 1.9), '41': (0.4, 1.7)}


def setup(expo=None, indoor_=False):
    e = float(os.environ.get('EXPO', '-1.0')) if expo is None else expo
    adj = EXPO_ADJ.get(os.path.basename(HERE)[:2], (0.0, 0.0))
    e += adj[1] if indoor_ else adj[0]
    return ph.setup(a.pct, a.samples, fps=FPS, frames=F_END, exposure=e)


def outdoor(hdri='farm_field', hstr=1.0, hrot=0.0, sun_elev=35, sun_az=120, sun_col='#FFE2B8', sun_pow=4.0, expo=None, sat=1.05):
    sc = setup(expo)
    ph.hdri_world(hdri, strength=hstr, rot=hrot, bg_strength=1.0, sat=sat)
    ph.sun('sun', elev=sun_elev, azim=sun_az, col=sun_col, power=sun_pow, angle=2.0)
    return sc


def indoor(hdri='kloofendal_48d_partly_cloudy_puresky', hstr=0.35, expo=None, sun_pow=0.0, sun_elev=30, sun_az=120,
           sun_col='#FFE0B0'):
    """Room lit by its windows/lamps: a dim sky world, optional sun shaft through the windows."""
    sc = setup(expo, indoor_=True)
    ph.hdri_world(hdri, strength=hstr, rot=0, bg_strength=1.0, sat=1.0)
    if sun_pow:
        ph.sun('sun', elev=sun_elev, azim=sun_az, col=sun_col, power=sun_pow, angle=1.5)
    return sc


def ground(size=(120, 90), loc=(0, 15, 0), tex='aerial_grass_rock', tint='#8AA060', mix=0.4, scale=0.3, cuts=120, bump=0.8):
    return ph.slab('ground', size, loc, (0, 0, 0), ph.pbr('ground_m', tex, scale=scale, tint=tint, tint_mix=mix, bump=bump), cuts=cuts)


def grass(G, mask_fn, dens=6, seed=3, base='#24500E', mid='#4F9A22', tip='#B9DC4A', h=(0.12, 0.32), flowers=0.0):
    bpy.context.view_layer.update()                 # paint_mask reads matrix_world
    ph.paint_mask(G, 'grass', mask_fn)
    m = ph.grass_material('grass_m%d' % seed, base=base, mid=mid, tip=tip)
    cl = ph.grass_clumps('grassN%d' % seed, variants=8, blades=int(os.environ.get('WBLADES', '36')), h=h, spread=0.12, seed=seed,
                         mat=m, flowers=flowers)
    ph.scatter(G, cl, density=dens, seed=seed + 4, scale=(0.8, 1.25), tilt=0.1, mask='grass', name='grass%d' % seed)


def room(name, w, d, h, loc=(0, 0, 0), floor='old_wood_floor', wall='painted_plaster_wall', wall_tint='#E8DCC8', floor_tint=None,
         beams=True, window=None, back_only=False, ceiling=True, floor_scale=0.5, wall_scale=0.6, wall_mix=0.35):
    """Open-front room: floor, back wall (+y), side walls, ceiling with beams. window = (x, z, w, h) on the back wall."""
    x0, y0, z0 = loc
    fm = ph.pbr(name + '_floor', floor, scale=floor_scale, tint=floor_tint, tint_mix=0.3 if floor_tint else 0.0, bump=0.8)
    wm = ph.pbr(name + '_wall', wall, scale=wall_scale, tint=wall_tint, tint_mix=wall_mix, bump=0.6)
    ph.slab(name + '_fl', (w, d), (x0, y0 + d / 2, z0 + 0.005), (0, 0, 0), fm, cuts=20)
    ph.slab(name + '_apron', (w + 8, 8), (x0, y0 - 4.0, z0 + 0.004), (0, 0, 0), fm, cuts=20)    # floor in front (low cameras)
    if window:
        wx, wz, ww, wh = window
        # back wall made of 4 pieces around the hole
        left = (wx - ww / 2) - (-w / 2)
        right = (w / 2) - (wx + ww / 2)
        if left > 0.01:
            ph.slab(name + '_bwL', (left, h), (x0 - w / 2 + left / 2, y0 + d, z0 + h / 2), (90, 0, 0), wm, cuts=8)
        if right > 0.01:
            ph.slab(name + '_bwR', (right, h), (x0 + w / 2 - right / 2, y0 + d, z0 + h / 2), (90, 0, 0), wm, cuts=8)
        ph.slab(name + '_bwB', (ww, wz - wh / 2), (x0 + wx, y0 + d, z0 + (wz - wh / 2) / 2), (90, 0, 0), wm, cuts=4)
        top = h - (wz + wh / 2)
        ph.slab(name + '_bwT', (ww, top), (x0 + wx, y0 + d, z0 + h - top / 2), (90, 0, 0), wm, cuts=4)
        fr = plain(name + '_frame', '#5A3E28', 0.6)
        for dx in (-ww / 2, 0, ww / 2):
            ph.box(name + f'_mul{dx:.1f}', (0.07, 0.12, wh), (x0 + wx + dx, y0 + d, z0 + wz), fr)
        for dz in (-wh / 2, wh / 2):
            ph.box(name + f'_tr{dz:.1f}', (ww + 0.07, 0.14, 0.08), (x0 + wx, y0 + d, z0 + wz + dz), fr)
    else:
        ph.slab(name + '_bw', (w, h), (x0, y0 + d, z0 + h / 2), (90, 0, 0), wm, cuts=8)
    if not back_only:
        ph.slab(name + '_wl', (d, h), (x0 - w / 2, y0 + d / 2, z0 + h / 2), (90, 0, 90), wm, cuts=8)
        ph.slab(name + '_wr', (d, h), (x0 + w / 2, y0 + d / 2, z0 + h / 2), (90, 0, -90), wm, cuts=8)
    if ceiling:
        ph.slab(name + '_ce', (w, d), (x0, y0 + d / 2, z0 + h), (180, 0, 0), wm, cuts=4)
        if beams:
            bm = ph.pbr(name + '_beam', 'dark_wood', scale=0.6)
            for k in range(int(d / 1.6) + 1):
                ph.box(name + f'_beam{k}', (w, 0.22, 0.26), (x0, y0 + 0.4 + k * 1.6, z0 + h - 0.13), bm)
    ph.box(name + '_skirt', (w, 0.04, 0.16), (x0, y0 + d - 0.02, z0 + 0.08), plain(name + '_sk', '#4A3426', 0.6))


def window_glow(name, loc, w, h, col='#CFE4FF', strength=3.0, rot_z=0):
    """Bright 'sky' card behind a window hole (reads as daylight outside)."""
    ob = ph.box(name, (w, 0.02, h), loc, glow(name + '_m', col, strength), rot=(0, 0, rot_z))
    ob.visible_shadow = False
    return ob


def lamp_pool(name, loc, power=60, col='#FFC48C', radius=0.08):
    return ph.point(name, loc, col, power, radius=radius, shadow=True)


def water(name, size, loc, col='#3E6A78', rough=0.08):
    m = ph.plain(name + '_m', col, rough, 0.0)
    try:
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Specular IOR Level'].default_value = 0.8
    except Exception:
        pass
    ob = ph.slab(name, size, loc, (0, 0, 0), m, cuts=80, noise=0.05, noise_scale=0.8)
    return ob


def facade(name, x, y, w, h, wall_col='#C8B89A', roof_col='#5A3A2A', timber=False, rot_z=0.0, windows=2, door=True,
           depth=4.0, roof=True):
    """Simple townhouse block facing -Y with windows, door and a pitched roof."""
    root = empty(name, None, (x, y, 0))
    wm = ph.pbr(name + '_w', 'painted_plaster_wall', scale=0.6, tint=wall_col, tint_mix=0.6, bump=0.6)
    P(ph.box(name + '_body', (w, depth, h), (0, depth / 2, h / 2), wm), root)
    if roof:
        rm = plain(name + '_r', roof_col, 0.7)
        ang = 38
        rl = (depth / 2) / math.cos(math.radians(ang)) + 0.3
        for sg in (-1, 1):
            P(ph.box(name + f'_roof{sg}', (w + 0.4, rl, 0.12), (0, depth / 2 + sg * depth / 4, h + depth / 4 * math.tan(math.radians(ang))),
                     rm, rot=(sg * ang, 0, 0)), root)
        tri = plain(name + '_g', wall_col, 0.8)
    gl = plain(name + '_glass', '#2A3440', 0.15)
    fr = plain(name + '_fr', '#F0EADC', 0.6)
    floors = max(1, int(h / 2.6))
    for fl in range(floors):
        z = 1.5 + fl * 2.6
        for k in range(windows):
            wx = -w / 2 + (k + 0.5) * w / windows
            if door and fl == 0 and k == windows // 2:
                continue
            P(ph.box(name + f'_win{fl}{k}', (0.8, 0.06, 1.1), (wx, -0.02, z), gl), root)
            P(ph.box(name + f'_sill{fl}{k}', (0.95, 0.12, 0.08), (wx, -0.06, z - 0.6), fr), root)
    if door:
        P(ph.box(name + '_door', (1.0, 0.06, 2.0), (0, -0.02, 1.0), plain(name + '_d', '#4A2E1E', 0.6)), root)
    if timber:
        tm = plain(name + '_t', '#3A2A1E', 0.7)
        for k in range(int(w / 1.2) + 1):
            P(ph.box(name + f'_tv{k}', (0.14, 0.05, h), (-w / 2 + k * 1.2, -0.03, h / 2), tm), root)
        for fl in range(floors + 1):
            P(ph.box(name + f'_th{fl}', (w, 0.05, 0.16), (0, -0.03, 0.1 + fl * 2.6), tm), root)
        for k in range(int(w / 1.2)):
            x = -w / 2 + k * 1.2 + 0.6
            P(rod(name + f'_tx{k}', (x - 0.55, -0.04, 2.7), (x + 0.55, -0.04, 4.9), 0.06, tm), root)
    root.rotation_euler.z = math.radians(rot_z)
    return root


def ship(name, length=12.0, hull_col='#3A3E44', deck_col='#8A8478', funnels=2, guns=2, mast=True):
    """Simple steel warship along +X, waterline at z=0."""
    root = empty(name)
    hull = plain(name + '_hull', hull_col, 0.5, 0.3)
    deck = plain(name + '_deck', deck_col, 0.7)
    L, W = length, length * 0.14
    P(blob(name + '_h', (L, W, 1.6), (0, 0, 0.3), hull), root)
    P(blob(name + '_bow', (L * 0.2, W * 0.75, 1.5), (L * 0.5, 0, 0.45), hull, rot=(0, 0, 0)), root)
    P(ph.box(name + '_deck', (L * 0.98, W * 0.9, 0.08), (0, 0, 1.12), deck), root)
    P(ph.box(name + '_bridge', (L * 0.12, W * 0.6, 1.4), (L * 0.12, 0, 1.85), hull, bevel=0.05), root)
    P(ph.box(name + '_bridge2', (L * 0.08, W * 0.5, 0.6), (L * 0.12, 0, 2.85), hull, bevel=0.04), root)
    for k in range(funnels):
        P(cyl(name + f'_fun{k}', W * 0.13, 1.6, (-L * 0.05 - k * L * 0.12, 0, 2.2), (0, 0, 0), plain(name + '_f', '#2A2A2C', 0.5)), root)
    for k, x in enumerate([L * 0.32, -L * 0.36][:guns]):
        P(cyl(name + f'_tur{k}', W * 0.22, 0.4, (x, 0, 1.35), (0, 0, 0), hull), root)
        P(cyl(name + f'_gun{k}', 0.07, 2.0, (x + (1.0 if x > 0 else -1.0), 0, 1.45), (0, 90, 0), hull), root)
    if mast:
        P(cyl(name + '_mast', 0.06, 4.0, (L * 0.05, 0, 3.6), (0, 0, 0), plain(name + '_m', '#4A4A48', 0.5)), root)
        P(cyl(name + '_yard', 0.04, W * 0.9, (L * 0.05, 0, 4.8), (90, 0, 0), plain(name + '_m', '#4A4A48', 0.5)), root)
    return root


def tall_ship(name, length=12.0, hull_col='#4A3020', sail_col='#E8E0CC', masts=3, stripe='#C8A24A'):
    """Old wooden warship with sails (1850s Royal Navy) along +X."""
    root = empty(name)
    hull = ph.pbr(name + '_hull', 'dark_wood', scale=0.4, tint=hull_col, tint_mix=0.4)
    W = length * 0.16
    P(blob(name + '_h', (length, W, 1.8), (0, 0, 0.4), hull), root)
    P(ph.box(name + '_stripe', (length * 0.95, W * 1.02, 0.18), (0, 0, 0.95), plain(name + '_s', stripe, 0.5)), root)
    P(ph.box(name + '_stern', (length * 0.15, W * 0.95, 1.0), (-length * 0.44, 0, 1.6), hull, bevel=0.05), root)
    sail = plain(name + '_sail', sail_col, 0.9)
    for k in range(masts):
        x = length * (0.3 - k * 0.3)
        hgt = 6.5 - abs(k - 1) * 0.8
        P(cyl(name + f'_mast{k}', 0.09, hgt, (x, 0, 1.3 + hgt / 2), (0, 0, 0), hull), root)
        for j, (z, sw) in enumerate(((2.8, 2.6), (4.6, 2.1), (6.2, 1.5))):
            if z > hgt:
                continue
            s = ph.slab(name + f'_sail{k}{j}', (sw * 1.25, 1.6), (x, -0.25, z), (84, 0, 0), sail, cuts=6, noise=0.12)
            P(s, root)
    return root


# ---------------------------------------------------------------- camera
def make_camera(shots, fstop=2.8, shake=None, lens=30, linear=()):
    """shots: {seg: [(frac, cam_loc, aim_loc[, lens]), ...]} (fractions 0..1 of the segment).
    Extra cuts inside a segment: use add_cut(t) and give absolute times as ('t', t) in place of frac."""
    global CAM
    shake = float(os.environ.get('SHAKE', '0.018')) if shake is None else shake
    keys = []
    for k, lst in shots.items():
        for item in lst:
            fr = item[0]
            t = fr[1] if isinstance(fr, tuple) else sf(k, fr)
            keys.append((t,) + tuple(item[1:]))
    keys.sort(key=lambda k: k[0])
    cam = ph.camera(lens=lens)
    cd = cam.data
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = fstop
    tgt = empty('aim')
    cd.dof.focus_object = tgt
    tc = cam.constraints.new('TRACK_TO')
    tc.target = tgt
    tc.track_axis = 'TRACK_NEGATIVE_Z'
    tc.up_axis = 'UP_Y'
    for kk in keys:
        t, cl, tl = kk[:3]
        key_loc(cam, t, cl)
        key_loc(tgt, t, tl)
        cd.lens = kk[3] if len(kk) > 3 else lens
        cd.keyframe_insert('lens', frame=T(t))
    cut_frames = {T(c) for c in CUTS}
    lin = [(T(s0(k)), T(s1(k))) for k in linear]
    for fc in fcurves(cam) + fcurves(tgt) + fcurves(cd):
        kps = list(fc.keyframe_points)
        for i, kp in enumerate(kps):
            kp.interpolation = 'BEZIER'
            kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
            if any(a_ <= kp.co.x < b_ for a_, b_ in lin):
                kp.interpolation = 'LINEAR'
            if i + 1 < len(kps) and int(round(kps[i + 1].co.x)) in cut_frames:
                kp.interpolation = 'CONSTANT'
        fc.update()
    for fc in fcurves(cam):
        if fc.data_path == 'location':
            m = fc.modifiers.new('NOISE')
            m.scale = 40 * FPS / 30
            m.strength = shake
    CAM = cam
    return cam


def orbit(center, radius, height, a0, a1, n=3, lens=30, aim_z=None, f0=0.0, f1=1.0):
    """Keys circling `center` from angle a0 to a1 (degrees; 0 = camera at -Y)."""
    cx, cy, cz = center
    out = []
    for i in range(n):
        u = i / (n - 1)
        ang = math.radians(a0 + (a1 - a0) * u)
        out.append((f0 + (f1 - f0) * u, (cx + radius * math.sin(ang), cy - radius * math.cos(ang), height),
                    (cx, cy, cz if aim_z is None else aim_z), lens))
    return out


def finish(cam, glare=0.3, fstop=2.8):
    if CARD_SPANS:
        _card_focus(cam, fstop)
        CARD_SPANS.clear()
    F.finish(cam)
    ph.soft_shadows()
    ph.glare(glare, 1.0)


# ---------------------------------------------------------------- render loop
def run(builders):
    """builders: [(name, fn, 'ABC')]."""
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    if a.mode == 'still':
        if a.segs:
            ks = ORDER if a.segs == 'all' else list(a.segs)
            want = []
            for k in ks:
                want += [T(sf(k, 0.15)), T(sf(k, 0.85))]
        else:
            want = [int(x) for x in a.t.split(',')]
    for name, builder, segs in builders:
        if a.only and a.only != name:
            continue
        ranges = frames_of(segs)
        if a.mode == 'still':
            todo = [t for t in want if any(lo <= t <= hi for lo, hi in ranges)]
            if not todo:
                continue
        else:
            todo = [(max(lo, a.fs or lo), min(hi, a.fe or hi)) for lo, hi in ranges]
            todo = [r for r in todo if r[0] <= r[1]]
            if not todo:
                continue
        bpy.ops.wm.read_factory_settings(use_empty=True)
        F.CHARS.clear()
        tb = time.time()
        sc = builder()
        print(f'DGN: built {name} in {time.time() - tb:.1f}s', flush=True)
        if a.mode == 'still':
            for t in todo:
                sc.frame_set(t)
                sc.render.filepath = a.out.replace('####', f'{t:04d}')
                bpy.ops.render.render(write_still=True)
        else:
            for fs, fe in todo:
                sc.frame_start, sc.frame_end = fs, fe
                sc.render.use_overwrite = False
                sc.render.use_placeholder = True
                sc.render.filepath = a.out
                sc.render.image_settings.file_format = 'PNG'
                tr = time.time()
                bpy.ops.render.render(animation=True)
                print(f'DGN: TIMING {name} frames {fs}-{fe}: {time.time() - tr:.1f}s', flush=True)
    print('DGN: done', F_END, 'frames at', FPS, 'fps')


# ---------------------------------------------------------------- vehicles / camp props (from EP29/EP31)
def make_truck(name, body_col='#6E6448', dark_col='#2E2A22', cover=False, loc=(0, 0, 0), rot_z=0.0):
    body, dark = plain(name + '_paint', body_col, 0.55, 0.2), plain(name + '_dark', dark_col, 0.6)
    root = empty(name, None, loc)
    tyre = plain('tyre', '#1E1E1C', 0.6)
    for i, x in enumerate((2.2, -0.6, -1.7)):
        for sy in (-1, 1):
            P(cyl(f'{name}_w{i}{sy}', 0.5, 0.34, (x, sy * 1.0, 0.5), (90, 0, 0), tyre), root)
    P(ph.box(f'{name}_chassis', (6.0, 1.7, 0.3), (0, 0, 0.85), dark), root)
    P(blob(f'{name}_cab', (1.5, 2.1, 1.4), (1.5, 0, 1.7), body), root)
    P(blob(f'{name}_hood', (1.3, 1.8, 0.9), (2.85, 0, 1.35), body), root)
    P(ph.box(f'{name}_glass', (0.05, 1.6, 0.55), (2.26, 0, 2.05), plain('glass', '#1A2230', 0.1)), root)
    P(ph.box(f'{name}_bed', (3.6, 2.3, 0.6), (-1.05, 0, 1.3), body, bevel=0.08), root)
    if cover:
        cv = cyl(f'{name}_cover', 1.1, 3.6, (-1.05, 0, 1.62), (0, 90, 0), plain(name + '_cv', '#8A8A62', 0.9), verts=40)
        cv.scale = (0.8, 1, 1)
        P(cv, root)
    root.rotation_euler.z = math.radians(rot_z)
    return root


def make_cannon(name, body_col='#5A5E44', dark_col='#2E2E26', loc=(0, 0, 0), rot_z=0.0):
    body, dark = plain(name + '_b', body_col, 0.5, 0.3), plain(name + '_d', dark_col, 0.6)
    root = empty(name, None, loc)
    for sy in (-1, 1):
        P(cyl(f'{name}_w{sy}', 0.6, 0.22, (0, sy * 0.95, 0.6), (90, 0, 0), dark), root)
        P(rod(f'{name}_trail{sy}', (0, sy * 0.3, 0.6), (-2.4, sy * 0.7, 0.1), 0.09, body), root)
    P(blob(f'{name}_shield', (0.16, 1.9, 1.1), (0.25, 0, 1.05), body, rot=(0, -10, 0)), root)
    P(cyl(f'{name}_barrel', 0.13, 3.2, (1.5, 0, 1.25), (0, 78, 0), body), root)
    P(blob(f'{name}_breech', (0.7, 0.5, 0.5), (-0.1, 0, 1.0), body), root)
    root.rotation_euler.z = math.radians(rot_z)
    return root


def tent(name, x, y, w=6.0, d=6.4, h=3.4, col='#B9A47A', open_front=True, floor=True):
    """Ridge tent, open front at y, back wall at y + d."""
    canvas = plain(name + '_c', col, 0.85)
    pole = plain(name + '_p', '#5A3E26', 0.7)
    side = h * 0.5
    ang = math.degrees(math.atan2(h - side, w / 2))
    rl = math.hypot(w / 2, h - side) + 0.12
    cy = y + d / 2
    ph.slab(name + '_rL', (rl, d), (x - w / 4, cy, side + (h - side) / 2), (0, -ang, 0), canvas, cuts=24)
    ph.slab(name + '_rR', (rl, d), (x + w / 4, cy, side + (h - side) / 2), (0, ang, 0), canvas, cuts=24)
    ph.slab(name + '_wL', (d, side), (x - w / 2, cy, side / 2), (90, 0, 90), canvas, cuts=24)
    ph.slab(name + '_wR', (d, side), (x + w / 2, cy, side / 2), (90, 0, -90), canvas, cuts=24)
    ph.slab(name + '_wB', (w, h), (x, y + d, h / 2), (90, 0, 0), canvas, cuts=24)
    ph.box(name + '_ridge', (0.09, d, 0.09), (x, cy, h - 0.04), pole)
    for yy in (y - 0.1, y + d - 0.1):
        ph.box(name + f'_pole{yy:.1f}', (0.08, 0.08, h), (x, yy, h / 2), pole)
    if floor:
        ph.slab(name + '_fl', (w, d), (x, cy, 0.02), (0, 0, 0), ph.pbr(name + '_dirt', 'dirt_floor', scale=0.5), cuts=10)


def crate(name, loc, size=(0.9, 0.6, 0.5), col='#7A5A34', rot_z=0.0, label=None):
    m = ph.pbr(name + '_m', 'wood_planks_dirt', scale=0.3, tint=col, tint_mix=0.4)
    ob = ph.box(name, size, (loc[0], loc[1], loc[2] + size[2] / 2), m, rot=(0, 0, rot_z), bevel=0.02)
    if label:
        r = math.radians(rot_z)
        dy = -size[1] / 2 - 0.008
        sign(name + '_lbl', label, size[0] * 0.8, size[2] * 0.6,
             (loc[0] - dy * math.sin(r), loc[1] + dy * math.cos(r), loc[2] + size[2] / 2), rot_z)
    return ob


def smoke(name, loc, t0, t1, every=0.5, size=2.4, rise=2.0, col_file='fx_puff', seed=0):
    rnd = random.Random(seed)
    t, k = t0, 0
    while t < t1:
        x, y, z = loc
        fx_at(f'{name}{k}', col_file, size * rnd.uniform(0.8, 1.2), (x + rnd.uniform(-0.6, 0.6), y + rnd.uniform(-0.3, 0.3), z),
              t, t + 1.4, rise)
        t += every * rnd.uniform(0.7, 1.3)
        k += 1


def line_of(name, p0, p1, n, fn):
    """Call fn(i, (x, y, z)) at n points spread from p0 to p1."""
    out = []
    for i in range(n):
        u = i / max(1, n - 1)
        out.append(fn(i, tuple(a_ + (b_ - a_) * u for a_, b_ in zip(p0, p1))))
    return out


def carried(c, ob, at=(0.0, -0.12, 1.75)):
    """Parent a prop to a character's card (follows hops/moves; card units = 1/scale)."""
    ob.parent = c.bob
    ob.location = at
    return ob


def flag(name, file, loc, h=5.0, w=1.6, rot_z=0.0, pole_col='#D8D4C8'):
    """Flagpole with a cloth picture that flutters (noise on its turn). The cloth hangs toward +X, faces -Y."""
    x, y, z = loc
    cyl(name + '_pole', 0.05, h, (x, y, z + h / 2), (0, 0, 0), plain(name + '_pm', pole_col, 0.4, 0.5))
    sphere(name + '_knob', 0.09, (x, y, z + h + 0.05), plain('gold', '#C8A040', 0.3, 0.9))
    piv = empty(name + '_piv', None, (x, y, z + h - w * 0.3))
    cloth = art_plane(name + '_cloth', file, w, w * 0.56, (w / 2, 0, 0), (90, 0, 0), parent=piv)
    piv.rotation_euler.z = math.radians(rot_z)
    noise_on(piv, 'rotation_euler', 2, 0.25, scale=12)
    noise_on(piv, 'rotation_euler', 0, 0.06, scale=8)
    return piv


def rifle(name, length=1.25, col='#5A3A22'):
    """Long musket/rifle along +X (muzzle at +X)."""
    root = empty(name)
    wood, steel = plain(name + '_w', col, 0.6), plain('rifle_steel', '#2A2C30', 0.4, 0.7)
    P(ph.box(name + '_stock', (length * 0.55, 0.05, 0.08), (-length * 0.2, 0, 0), wood), root)
    P(ph.box(name + '_butt', (0.2, 0.05, 0.16), (-length * 0.47, 0, -0.04), wood), root)
    P(cyl(name + '_barrel', 0.016, length * 0.6, (length * 0.25, 0, 0.03), (0, 90, 0), steel, verts=10), root)
    return root


def shoulder_arms(c, name, t=0.05, side='R'):
    """Rifle held upright at the shoulder (card space)."""
    r = rifle(name)
    sg = 1 if side == 'R' else -1
    carried(c, r, (sg * 0.55, -0.15, 1.9))
    r.rotation_euler = (0, math.radians(-80), 0)
    r.scale = (1.8, 1.8, 1.8)
    c.arm(side, T(t), elbow=(sg * 0.62, 1.7), hand=(sg * 0.55, 1.62), dur=1)
    return r


def aim_rifle(c, name, t, side='R'):
    """Rifle levelled toward card +X (the character's right)."""
    r = rifle(name)
    carried(c, r, (0.55, -0.15, 2.05))
    r.rotation_euler = (0, math.radians(-4), 0)
    r.scale = (1.8, 1.8, 1.8)
    c.arm('R', T(t), elbow=(0.5, 1.9), hand=(0.4, 2.0), dur=3)
    c.arm('L', T(t), elbow=(0.2, 1.85), hand=(0.85, 2.02), dur=3)
    return r


def potatoes(name, x0, y0, rows=5, cols=8, dx=0.5, dy=0.7):
    m = plain(name + '_m', '#B89060', 0.8)
    leaf = plain(name + '_leaf', '#4A7A2A', 0.7)
    out = []
    for r in range(rows):
        for c_ in range(cols):
            x, y = x0 + c_ * dx, y0 + r * dy
            out.append(sphere(f'{name}{r}_{c_}', 0.09, (x, y, 0.06), m, (1.3, 1.0, 0.8), seg=10))
            cone(f'{name}L{r}_{c_}', 0.16, 0.0, 0.3, (x + 0.1, y + 0.15, 0.15), (0, 0, 0), leaf, verts=6)
    return out


def coast(G_y=20.0, x=0.0, w=220.0, sea_col='#3E6A78'):
    """Beach strip sloping from the ground edge at y=G_y into the sea (water at z=-0.5)."""
    sand = ph.pbr('sand', 'aerial_grass_rock', scale=0.3, tint='#D8C49A', tint_mix=0.8, bump=0.4)
    ang = math.degrees(math.atan2(0.9, 8.0))
    ph.slab('beach', (w, 8.1), (x, G_y + 4.0, -0.45), (-ang, 0, 0), sand, cuts=60)
    water('sea', (w, 140), (x, G_y + 74, -0.5), sea_col)


_T0 = [time.time()]


def tick(label):
    print(f'DGN: tick {label} {time.time() - _T0[0]:.1f}s', flush=True)
    _T0[0] = time.time()


def pine(name, loc, h=6.0, col='#2E5A2E'):
    """Cheap stylised conifer: trunk + 3 stacked cones (no Poly Haven trees: they load for minutes)."""
    x, y, z = loc
    cyl(name + '_t', 0.16 * h / 6, h * 0.3, (x, y, z + h * 0.15), (0, 0, 0), plain('trunk', '#4A3222', 0.8), verts=10)
    m = plain(name + '_m', col, 0.8)
    for k, (zz, r) in enumerate(((0.3, 0.32), (0.5, 0.26), (0.68, 0.19))):
        cone(f'{name}_c{k}', r * h * 0.55, 0.0, h * 0.38, (x, y, z + h * zz + h * 0.12), (0, 0, k * 17), m, verts=9)


def puff_tree(name, loc, h=5.0, col='#4E7A2E', seed=0):
    """Cheap broadleaf: trunk + a few squashed spheres."""
    rnd = random.Random(seed)
    x, y, z = loc
    cyl(name + '_t', 0.15 * h / 5, h * 0.5, (x, y, z + h * 0.25), (0, 0, 0), plain('trunk', '#4A3222', 0.8), verts=10)
    m = plain(name + '_m%d' % seed, col, 0.85)
    for k in range(4):
        r = h * rnd.uniform(0.2, 0.28)
        sphere(f'{name}_b{k}', r, (x + rnd.uniform(-0.3, 0.3) * h * 0.4, y + rnd.uniform(-0.3, 0.3) * h * 0.4,
                                    z + h * rnd.uniform(0.6, 0.8)), m, (1, 1, 0.85), seg=12)


def submarine(name, length=14.0, col='#2E3438'):
    """Soviet-style sub along +X, waterline at z=0 (hull mostly under)."""
    root = empty(name)
    m = plain(name + '_m', col, 0.45, 0.3)
    w = length * 0.11
    P(blob(name + '_hull', (length, w, w), (0, 0, 0.0), m), root)
    P(blob(name + '_sail', (length * 0.16, w * 0.45, w * 1.1), (length * 0.06, 0, w * 0.75), m), root)
    P(ph.box(name + '_planes', (length * 0.06, w * 1.2, 0.05), (length * 0.08, 0, w * 0.95), m), root)
    P(cyl(name + '_peri', 0.05, 1.0, (length * 0.08, 0, w * 1.6), (0, 0, 0), m, verts=8), root)
    P(ph.box(name + '_star', (0.02, 0.5, 0.5), (length * 0.06, -w * 0.23, w * 0.9), plain('redstar', '#B82020', 0.5)), root)
    return root


def soda(name, loc, label='can_label', h=0.3, r=0.07):
    """Soda can with a printed label."""
    root = empty(name, None, loc)
    P(cyl(name + '_c', r, h, (0, 0, h / 2), (0, 0, 0), plain('can_al', '#C8CCD0', 0.25, 0.9)), root)
    lab = art_plane(name + '_l', label, r * 1.9, h * 0.75, (0, -r - 0.003, h / 2), (90, 0, 0), parent=root)
    return root


def eiffel(name, loc, h=40.0, col='#8A6A4A'):
    """Procedural Eiffel-style lattice tower: 4 curved legs with cross bracing, 3 platforms, spire."""
    x0, y0, z0 = loc
    m = plain(name + '_m', col, 0.6, 0.4)
    base, top = h * 0.32, h * 0.022

    def half(z):
        u = min(1.0, z / (h * 0.92))
        return top + (base - top) * (1 - u) ** 2.2

    n = 14
    zs = [h * 0.92 * (i / n) ** 1.15 for i in range(n + 1)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            for i in range(n):
                za, zb = zs[i], zs[i + 1]
                wa, wb = half(za), half(zb)
                for d in (0.0, 0.25):                         # each leg = 2 parallel girders
                    rod(f'{name}_l{sx}{sy}{i}{d}', (x0 + sx * (wa - d), y0 + sy * (wa - d * 0.3), z0 + za),
                        (x0 + sx * (wb - d), y0 + sy * (wb - d * 0.3), z0 + zb), h * 0.006, m, verts=6)
    for i in range(1, n, 1):                                  # X bracing on each face
        za, zb = zs[i - 1], zs[i]
        wa, wb = half(za), half(zb)
        for (ax, ay), (bx, by) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
            rod(f'{name}_x{i}{ax}{ay}a', (x0 + ax * wa, y0 + ay * wa, z0 + za), (x0 + bx * wb, y0 + by * wb, z0 + zb), h * 0.003, m, verts=4)
            rod(f'{name}_x{i}{ax}{ay}b', (x0 + bx * wa, y0 + by * wa, z0 + za), (x0 + ax * wb, y0 + ay * wb, z0 + zb), h * 0.003, m, verts=4)
    for zf, k in ((0.15, 1.1), (0.37, 1.05), (0.88, 1.6)):
        z = h * zf
        w = half(z) * k
        ph.box(f'{name}_pl{zf}', (2 * w, 2 * w, h * 0.012), (x0, y0, z0 + z), m)
    for sx in (-1, 1):                                         # the big arches under level 1
        pts = [(x0 + sx * 0, y0 - half(h * 0.15), z0 + h * 0.15)]
        for k in range(9):
            a = math.pi * k / 8
            xa = x0 + math.cos(a) * half(h * 0.07) * 0.8
            za = z0 + h * 0.06 + math.sin(a) * h * 0.075
            if k:
                rod(f'{name}_arch{sx}{k}', prev, (xa, y0 + sx * half(h * 0.1), za), h * 0.005, m, verts=6)
            prev = (xa, y0 + sx * half(h * 0.1), za)
    cone(name + '_spire', h * 0.012, 0.0, h * 0.1, (x0, y0, z0 + h * 0.97), (0, 0, 0), m, verts=8)


def popsicle(name, col='#E8702A', loc=(0, 0, 0), s=1.0):
    """Ice pop: rounded block on a wooden stick (stick end at the origin, pop above)."""
    root = empty(name, None, loc)
    m = plain(name + '_ice', col, 0.15)
    try:
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Subsurface Weight'].default_value = 0.4
    except Exception:
        pass
    P(blob(name + '_pop', (0.09 * s, 0.035 * s, 0.17 * s), (0, 0, 0.17 * s), m), root)
    P(ph.box(name + '_stick', (0.022 * s, 0.006 * s, 0.12 * s), (0, 0, 0.05 * s), plain('stickw', '#E0C890', 0.7)), root)
    return root


def cup(name, loc, liquid='#E8702A', frozen=False):
    root = empty(name, None, loc)
    P(cyl(name + '_g', 0.06, 0.03, (0, 0, 0.125), (0, 0, 0), plain('cupglass', '#E8F0F4', 0.05)), root)      # rim
    P(cyl(name + '_l', 0.058, 0.12, (0, 0, 0.06), (0, 0, 0), plain(name + '_liq', liquid, 0.08 if not frozen else 0.45)), root)
    P(ph.box(name + '_stick', (0.012, 0.004, 0.2), (0.01, 0, 0.16), plain('stickw', '#E0C890', 0.7), rot=(0, 8, 0)), root)
    return root


def snow(name, center, area=(8, 6), n=40, t0=0.0, t1=10.0, h=5.0, seed=0):
    rnd = random.Random(seed)
    m = glow(name + '_m', '#FFFFFF', 1.5)
    for k in range(n):
        x = center[0] + rnd.uniform(-area[0] / 2, area[0] / 2)
        y = center[1] + rnd.uniform(-area[1] / 2, area[1] / 2)
        f = sphere(f'{name}{k}', 0.025, (x, y, h), m, seg=6)
        span = rnd.uniform(3, 5)
        st = t0 - rnd.uniform(0, span)
        tt = st
        keys = []
        while tt < t1:
            keys += [(max(0.0, tt), (x, y, h), 'LINEAR'), (max(0.01, tt + span - 0.07), (x + rnd.uniform(-0.4, 0.4), y, 0.0), 'CONSTANT')]
            tt += span
        keys = sorted({k_[0]: k_ for k_ in keys}.values(), key=lambda k_: k_[0])
        ekeys(f, keys)


def pineapple(name, loc=(0, 0, 0), s=1.0, rotten=False):
    root = empty(name, None, loc)
    body = plain(name + '_b', '#6A4A2A' if rotten else '#D8A030', 0.6)
    leaf = plain(name + '_l', '#5A5A2A' if rotten else '#3A8A2A', 0.6)
    P(sphere(name + '_body', 0.11 * s, (0, 0, 0.13 * s), body, (1, 1, 1.35), seg=16), root)
    dots = plain('pine_dot', '#3A2A10', 0.7)
    for k in range(18):
        a, z = k * 2.4, 0.06 + (k % 6) * 0.03
        P(sphere(f'{name}_d{k}', 0.012 * s, (0.105 * s * math.cos(a), 0.105 * s * math.sin(a), z * s + 0.02 * s), dots, seg=6), root)
    for k in range(7):
        a = 2 * math.pi * k / 7
        lean = 25 + (k % 2) * 15
        P(cone(f'{name}_lf{k}', 0.03 * s, 0.0, 0.2 * s, (0.04 * s * math.cos(a), 0.04 * s * math.sin(a), 0.36 * s),
               (lean * math.sin(a) * (-1), lean * math.cos(a), 0), leaf, verts=4), root)
    return root


def glasshouse(name, x, y, w=8.0, d=5.0, h=3.2):
    """Victorian-style glasshouse: low brick base, glass walls + pitched glass roof, iron frame."""
    glass = plain(name + '_glass', '#CFE8E8', 0.05)
    try:
        b = glass.node_tree.nodes['Principled BSDF']
        b.inputs['Transmission Weight'].default_value = 0.85
        glass.surface_render_method = 'BLENDED'
    except Exception:
        pass
    iron = plain(name + '_iron', '#2A3A30', 0.4, 0.6)
    brick = ph.pbr(name + '_brick', 'rock_wall_08', scale=0.4, tint='#A85A3A', tint_mix=0.5)
    ph.box(name + '_base', (w, d, 0.6), (x, y + d / 2, 0.3), brick)
    for (sx, sy, rz, ww) in ((0, 0, 0, w), (0, d, 0, w)):
        ph.box(name + f'_gw{sy}', (ww, 0.03, h - 1.2), (x, y + sy, 0.6 + (h - 1.2) / 2), glass)
    for sx in (-w / 2, w / 2):
        ph.box(name + f'_gs{sx}', (0.03, d, h - 1.2), (x + sx, y + d / 2, 0.6 + (h - 1.2) / 2), glass)
    ang = math.degrees(math.atan2(1.2, d / 2))
    for sg in (-1, 1):
        ph.box(name + f'_roof{sg}', (w, math.hypot(d / 2, 1.2), 0.03), (x, y + d / 2 + sg * d / 4, h - 0.6), glass, rot=(-sg * ang, 0, 0))
    for k in range(int(w / 1.0) + 1):
        xx = x - w / 2 + k * w / int(w / 1.0)
        ph.box(name + f'_mf{k}', (0.05, 0.06, h - 1.2), (xx, y - 0.02, 0.6 + (h - 1.2) / 2), iron)
    ph.box(name + '_ridge', (w, 0.08, 0.08), (x, y + d / 2, h), iron)


def tomato(name, loc, s=1.0):
    root = empty(name, None, loc)
    P(sphere(name + '_t', 0.07 * s, (0, 0, 0.06 * s), plain('tomato', '#D82A1A', 0.25), (1, 1, 0.82), seg=14), root)
    P(cone(name + '_c', 0.04 * s, 0.0, 0.02 * s, (0, 0, 0.12 * s), (0, 0, 0), plain('tomleaf', '#3A7A2A', 0.6), verts=5), root)
    return root


def bottle(name, loc, label=None, col='#B81A12', h=0.32):
    root = empty(name, None, loc)
    m = plain(name + '_g', col, 0.15)
    P(cyl(name + '_b', 0.05, h * 0.65, (0, 0, h * 0.325), (0, 0, 0), m), root)
    P(cone(name + '_n', 0.05, 0.018, h * 0.2, (0, 0, h * 0.75), (0, 0, 0), m, verts=16), root)
    P(cyl(name + '_cap', 0.02, 0.05, (0, 0, h * 0.88), (0, 0, 0), plain('cork', '#A87A4A', 0.7), verts=10), root)
    if label:
        P(art_plane(name + '_l', label, 0.09, 0.07, (0, -0.052, h * 0.33), (90, 0, 0)), root)
    return root


def pillbox(name, loc, label, s=1.0, rot_z=0.0):
    ob = ph.box(name, (0.22 * s, 0.14 * s, 0.1 * s), (loc[0], loc[1], loc[2] + 0.05 * s), plain('pbox', '#E8DCC0', 0.6), rot=(0, 0, rot_z))
    lb = art_plane(name + '_l', label, 0.2 * s, 0.086 * s, (0, 0, 0.051 * s), (0, 0, 0), parent=ob)
    return ob
