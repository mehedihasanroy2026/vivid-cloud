"""Haldane-style canary revival cage: metal box, round grilled opening with a glass door,
small oxygen cylinder + valve and a carry handle on top, flat canary sprite inside.

    import canary_cage as CC
    cage = CC.Cage(loc=(0, 0, 0.8), scale=1.0, rot_z=0)
    cage.bird(1, 'perch'); cage.bird(90, 'dizzy'); cage.bird(120, 'faint')
    cage.door(140, shut=True)          # arrives shut at frame 140
    cage.valve(150, turns=1.5)         # hand wheel spins
    cage.finish()                      # bakes the sprite switches

Local space: X width, front is -Y, base at z=0. About 0.44 wide, 0.34 tall (plus the cylinder).
"""
import math
import bpy
import bmesh
import ph
import flat_char as F

W, D, H = 0.44, 0.26, 0.34
R = 0.125                     # round opening
T = 0.012                     # wall thickness
BIRDS = ['perch', 'chirp', 'dizzy', 'faint', 'happy', 'whistle']


def _mat(name, fn):
    return bpy.data.materials.get(name) or fn()


def _glass():
    m = bpy.data.materials.new('cc_glass')
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    tr = N.new('ShaderNodeBsdfTransparent')
    gl = N.new('ShaderNodeBsdfGlossy')
    gl.inputs['Roughness'].default_value = 0.08
    gl.inputs['Color'].default_value = (0.85, 0.95, 1.0, 1)
    fr = N.new('ShaderNodeFresnel')
    fr.inputs['IOR'].default_value = 1.3
    mix = N.new('ShaderNodeMixShader')
    L.new(fr.outputs[0], mix.inputs[0])
    L.new(tr.outputs[0], mix.inputs[1])
    L.new(gl.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], N['Material Output'].inputs['Surface'])
    try:
        m.surface_render_method = 'DITHERED'
    except Exception:
        m.blend_method = 'HASHED'
    return m


def _prim(op, name, mat, parent, smooth=True, **kw):
    getattr(bpy.ops.mesh, op)(**kw)
    ob = bpy.context.active_object
    ob.name = name
    ob.data.materials.append(mat)
    if smooth:
        for p in ob.data.polygons:
            p.use_smooth = True
    ob.parent = parent
    return ob


class Cage:
    def __init__(self, name='cage', loc=(0, 0, 0), scale=1.0, rot_z=0.0):
        self.name = name
        body = _mat('cc_body', lambda: ph.plain('cc_body', '#5E8E86', rough=0.42, metal=0.55))
        inner = _mat('cc_inner', lambda: ph.plain('cc_inner', '#F1E3C0', rough=0.8))
        brass = _mat('cc_brass', lambda: ph.plain('cc_brass', '#E0A63A', rough=0.3, metal=1.0))
        tank = _mat('cc_tank', lambda: ph.plain('cc_tank', '#16181E', rough=0.28, metal=0.6))
        white = _mat('cc_white', lambda: ph.plain('cc_white', '#ECECE6', rough=0.4, metal=0.2))
        wood = _mat('cc_wood', lambda: ph.plain('cc_wood', '#8A5A2C', rough=0.7))
        red = _mat('cc_red', lambda: ph.plain('cc_red', '#D8362A', rough=0.4, metal=0.3))
        glass = _mat('cc_glass', _glass)

        root = self.root = bpy.data.objects.new(name, None)
        bpy.context.collection.objects.link(root)

        def box(n, dims, loc_, mat, bevel=0.006):
            o = ph.box(f'{name}_{n}', dims, loc_, mat, bevel=bevel)
            o.parent = root
            return o

        # shell: back, sides, top, bottom (front is the plate with the round opening)
        box('back', (W, T, H), (0, D / 2 - T / 2, H / 2), body)
        box('L', (T, D, H), (-W / 2 + T / 2, 0, H / 2), body)
        box('R', (T, D, H), (W / 2 - T / 2, 0, H / 2), body)
        box('top', (W + 0.02, D + 0.02, T * 1.4), (0, 0, H), body)
        box('bot', (W + 0.02, D + 0.02, T * 1.4), (0, 0, 0.0), body)
        # light interior lining so the bird reads against it
        box('lin_back', (W - 2 * T, 0.002, H - 2 * T), (0, D / 2 - T - 0.001, H / 2), inner, bevel=0)
        box('lin_bot', (W - 2 * T, D - 2 * T, 0.002), (0, 0, T), inner, bevel=0)
        for s in (-1, 1):
            box(f'lin_s{s}', (0.002, D - 2 * T, H - 2 * T), (s * (W / 2 - T - 0.001), 0, H / 2), inner, bevel=0)
            for y in (-1, 1):
                box(f'foot{s}{y}', (0.05, 0.05, 0.03), (s * (W / 2 - 0.04), y * (D / 2 - 0.04), -0.02), tank, bevel=0.008)

        # front plate with a round hole
        me = bpy.data.meshes.new(name + '_front')
        bm = bmesh.new()
        n = 64
        ring, rect = [], []
        for i in range(n):
            a = 2 * math.pi * i / n
            c, s = math.cos(a), math.sin(a)
            k = min((W / 2) / max(abs(c), 1e-6), (H / 2) / max(abs(s), 1e-6))
            ring.append(bm.verts.new((R * c, -D / 2, H / 2 + R * s)))
            rect.append(bm.verts.new((k * c, -D / 2, H / 2 + k * s)))
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((ring[i], rect[i], rect[j], ring[j]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(body)
        fp = bpy.data.objects.new(name + '_front', me)
        bpy.context.collection.objects.link(fp)
        fp.parent = root
        so = fp.modifiers.new('solid', 'SOLIDIFY')
        so.thickness = T
        so.offset = 0
        # brass rim around the opening + grille bars
        _prim('primitive_torus_add', name + '_rim', brass, root, major_radius=R, minor_radius=0.011,
              major_segments=48, minor_segments=10, location=(0, -D / 2 - 0.004, H / 2), rotation=(math.pi / 2, 0, 0))
        for i in range(-2, 3):
            x = i * 0.045
            ln = 2 * math.sqrt(R * R - x * x)
            _prim('primitive_cylinder_add', f'{name}_bar{i}', brass, root, radius=0.0035, depth=ln, vertices=10,
                  location=(x, -D / 2, H / 2))
        # rivets in the corners of the front plate
        for sx in (-1, 1):
            for sz in (-1, 1):
                _prim('primitive_uv_sphere_add', f'{name}_riv{sx}{sz}', brass, root, radius=0.009, segments=12, ring_count=8,
                      location=(sx * (W / 2 - 0.03), -D / 2 - 0.004, H / 2 + sz * (H / 2 - 0.03)))

        # door: glass disc in a brass ring, hinged on the left of the opening; starts open
        hp = self.hinge = bpy.data.objects.new(name + '_hinge', None)
        bpy.context.collection.objects.link(hp)
        hp.parent = root
        hp.location = (-R - 0.02, -D / 2 - 0.022, H / 2)
        _prim('primitive_cylinder_add', name + '_pin', brass, root, radius=0.008, depth=0.09, vertices=12,
              location=(-R - 0.02, -D / 2 - 0.022, H / 2))
        _prim('primitive_cylinder_add', name + '_doorglass', glass, hp, radius=R + 0.006, depth=0.004, vertices=48,
              location=(R + 0.02, 0, 0), rotation=(math.pi / 2, 0, 0))
        _prim('primitive_torus_add', name + '_doorrim', brass, hp, major_radius=R + 0.008, minor_radius=0.013,
              major_segments=48, minor_segments=10, location=(R + 0.02, 0, 0), rotation=(math.pi / 2, 0, 0))
        _prim('primitive_uv_sphere_add', name + '_latch', red, hp, radius=0.016, segments=14, ring_count=8,
              location=(2 * R + 0.035, -0.012, 0))
        self.OPEN = math.radians(-118)
        hp.rotation_euler.z = self.OPEN

        # perch
        _prim('primitive_cylinder_add', name + '_perch', wood, root, radius=0.008, depth=W - 2 * T, vertices=12,
              location=(0, 0.01, 0.105), rotation=(0, math.pi / 2, 0))

        # oxygen cylinder lying on top (black with a white shoulder, like a British O2 bottle)
        cz, cr, cl = H + T + 0.047, 0.042, 0.2
        for sx in (-1, 1):
            box(f'cradle{sx}', (0.022, 0.11, 0.03), (sx * 0.07 - 0.03, 0, H + T + 0.012), brass, bevel=0.004)
        _prim('primitive_cylinder_add', name + '_tank', tank, root, radius=cr, depth=cl, vertices=32,
              location=(-0.03, 0, cz), rotation=(0, math.pi / 2, 0))
        e0 = _prim('primitive_uv_sphere_add', name + '_tank_end', tank, root, radius=cr, segments=32, ring_count=16,
                   location=(-0.03 - cl / 2, 0, cz))
        e0.scale = (0.55, 1, 1)
        e1 = _prim('primitive_uv_sphere_add', name + '_tank_sh', white, root, radius=cr, segments=32, ring_count=16,
                   location=(-0.03 + cl / 2, 0, cz))
        e1.scale = (0.8, 1, 1)
        _prim('primitive_cylinder_add', name + '_neck', brass, root, radius=0.014, depth=0.05, vertices=16,
              location=(-0.03 + cl / 2 + 0.045, 0, cz), rotation=(0, math.pi / 2, 0))
        # valve block + hand wheel (spins) + feed pipe down into the cage
        vx = -0.03 + cl / 2 + 0.07
        box('vblock', (0.03, 0.03, 0.036), (vx, 0, cz), brass, bevel=0.004)
        _prim('primitive_cylinder_add', name + '_pipe', brass, root, radius=0.006, depth=cz - H, vertices=10,
              location=(vx, 0, (cz + H) / 2))
        vw = self.wheel = bpy.data.objects.new(name + '_wheel', None)
        bpy.context.collection.objects.link(vw)
        vw.parent = root
        vw.location = (vx, 0, cz + 0.034)
        _prim('primitive_torus_add', name + '_wheel_rim', red, vw, major_radius=0.026, minor_radius=0.006,
              major_segments=24, minor_segments=8, location=(0, 0, 0))
        for i in range(2):
            _prim('primitive_cylinder_add', f'{name}_spoke{i}', red, vw, radius=0.004, depth=0.052, vertices=8,
                  location=(0, 0, 0), rotation=(math.pi / 2, 0, i * math.pi / 2))
        _prim('primitive_cylinder_add', name + '_stem', brass, root, radius=0.005, depth=0.03, vertices=8,
              location=(vx, 0, cz + 0.022))

        # carry handle: a bent rod arching over the cylinder
        cu = bpy.data.curves.new(name + '_handle', 'CURVE')
        cu.dimensions = '3D'
        cu.bevel_depth = 0.008
        cu.bevel_resolution = 3
        cu.use_fill_caps = True
        sp = cu.splines.new('NURBS')
        pts = [(-0.17, H), (-0.17, H + 0.17), (-0.06, H + 0.2), (0.06, H + 0.2), (0.17, H + 0.17), (0.17, H)]
        sp.points.add(len(pts) - 1)
        for p, (x, z) in zip(sp.points, pts):
            p.co = (x, 0.075, z, 1)
        sp.order_u = 3
        sp.use_endpoint_u = True
        sp.resolution_u = 10
        cu.materials.append(brass)
        hd = bpy.data.objects.new(name + '_handle', cu)
        bpy.context.collection.objects.link(hd)
        hd.parent = root

        # the bird: one flat sprite per state on the perch (the fainted one lies on the floor)
        self.birdp = bpy.data.objects.new(name + '_bird', None)
        bpy.context.collection.objects.link(self.birdp)
        self.birdp.parent = root
        self.birdp.location = (0.0, 0.0, 0.105)
        self.sprites = {}
        bs = 0.24
        for st in BIRDS:
            cz_ = bs / 2 - 0.012 if st != 'faint' else -0.105 + T + bs / 2 - 0.03
            self.sprites[st] = F._plane(f'{name}_bird_{st}', 'canary_' + st, bs, bs, (0.005 if st != 'faint' else -0.03, cz_), 0.0, self.birdp)
        self.timeline = {1: 'perch'}

        root.location = loc
        root.rotation_euler.z = math.radians(rot_z)
        root.scale = (scale,) * 3

    # ------------------------------------------------------------- acting
    def bird(self, f, state):
        self.timeline[int(f)] = state

    def chirp(self, f0, f1, rate=5, a='perch', b='chirp'):
        f, i = int(f0), 0
        while f < f1:
            self.timeline[f] = (b, a)[i % 2]
            f += rate
            i += 1
        self.timeline[int(f1)] = a

    def sway(self, f0, f1, deg=14, period=14):
        """Bird rocks side to side on the perch."""
        for f in range(int(f0), int(f1) + 1, max(1, period // 2)):
            k = (f - f0) / max(1, f1 - f0)
            self.birdp.rotation_euler.y = math.radians(deg * k) * (1 if ((f - int(f0)) // max(1, period // 2)) % 2 else -1)
            self.birdp.keyframe_insert('rotation_euler', index=1, frame=f)
        self.birdp.rotation_euler.y = 0
        self.birdp.keyframe_insert('rotation_euler', index=1, frame=int(f1) + 2)

    def breathe(self, f0, f1, period=10, amp=0.05):
        """Tiny fast breaths (canaries breathe very quickly)."""
        for f in range(int(f0), int(f1) + 1, max(1, period // 2)):
            up = ((f - int(f0)) // max(1, period // 2)) % 2
            self.birdp.scale = (1 + amp * 0.6 * up, 1, 1 + amp * up)
            self.birdp.keyframe_insert('scale', frame=f)

    def door(self, f, shut=True, dur=8):
        self.hinge.keyframe_insert('rotation_euler', index=2, frame=f - dur)
        self.hinge.rotation_euler.z = 0.0 if shut else self.OPEN
        self.hinge.keyframe_insert('rotation_euler', index=2, frame=f)

    def valve(self, f, turns=1.5, dur=18):
        self.wheel.keyframe_insert('rotation_euler', index=2, frame=f)
        self.wheel.rotation_euler.z += turns * 2 * math.pi
        self.wheel.keyframe_insert('rotation_euler', index=2, frame=f + dur)

    def finish(self):
        keys = sorted(self.timeline.items())
        for st, ob in self.sprites.items():
            last = None
            ob.hide_render = ob.hide_viewport = True
            ob.keyframe_insert('hide_render', frame=0)
            ob.keyframe_insert('hide_viewport', frame=0)
            for t, k in keys:
                vis = (k == st)
                if vis != last:
                    ob.hide_render = ob.hide_viewport = not vis
                    ob.keyframe_insert('hide_render', frame=t)
                    ob.keyframe_insert('hide_viewport', frame=t)
                    last = vis
