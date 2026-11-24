"""Shared building blocks: soft cartoon materials, outlines, textures, shapes, render setup."""
import bpy
import bmesh
import math
from mathutils import Vector


def srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hexcol(h, a=1.0):
    h = h.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (srgb_to_lin(r), srgb_to_lin(g), srgb_to_lin(b), a)


LINE_HEX = '#2A2230'          # outline colour: very dark plum, not pure black
_mats = {}
PAINT = 0.0                   # >0: hand-painted colour variation on every material (pro look)


def _paint(N, L, bsdf, base):
    """Soft blotchy shade variation so flat colours look painted, not plastic."""
    src = bsdf.inputs['Base Color'].links[0].from_socket if bsdf.inputs['Base Color'].is_linked else None
    tc = N.new('ShaderNodeTexCoord')
    nz = N.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.9
    nz.inputs['Detail'].default_value = 3.0
    nz.inputs['Roughness'].default_value = 0.6
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    mix = N.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    rng = N.new('ShaderNodeMapRange')
    rng.inputs['From Min'].default_value = 0.35
    rng.inputs['From Max'].default_value = 0.65
    rng.inputs['To Min'].default_value = 0.0
    rng.inputs['To Max'].default_value = PAINT
    L.new(nz.outputs['Fac'], rng.inputs['Value'])
    L.new(rng.outputs[0], mix.inputs[0])
    if src:
        L.new(src, mix.inputs[6])
    else:
        mix.inputs[6].default_value = base
    mix.inputs[7].default_value = tuple(c * 0.55 for c in base[:3]) + (1,)
    L.new(mix.outputs[2], bsdf.inputs['Base Color'])


def _uv_from_object(N, L, mode):
    """Object-space coords → 2D: 'wall' uses (x+y, z), 'floor' uses (x, y)."""
    tc = N.new('ShaderNodeTexCoord')
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['Object'], sep.inputs[0])
    comb = N.new('ShaderNodeCombineXYZ')
    if mode == 'wall':
        add = N.new('ShaderNodeMath')
        add.operation = 'ADD'
        L.new(sep.outputs['X'], add.inputs[0])
        L.new(sep.outputs['Y'], add.inputs[1])
        L.new(add.outputs[0], comb.inputs['X'])
        L.new(sep.outputs['Z'], comb.inputs['Y'])
    else:
        L.new(sep.outputs['X'], comb.inputs['X'])
        L.new(sep.outputs['Y'], comb.inputs['Y'])
    return comb.outputs[0]


def _tex2(N, L, bsdf, base, tex):
    kind = tex[0]
    if kind == 'planks':
        _, line, w, mode = tex
        br = N.new('ShaderNodeTexBrick')
        br.offset, br.offset_frequency = 0.37, 1
        br.squash, br.squash_frequency = 1.0, 1
        br.inputs['Color1'].default_value = base
        br.inputs['Color2'].default_value = tuple(c * 0.78 for c in base[:3]) + (1,)
        br.inputs['Mortar'].default_value = hexcol(line)
        br.inputs['Scale'].default_value = 1.0
        br.inputs['Mortar Size'].default_value = 0.022
        br.inputs['Brick Width'].default_value = w * 6
        br.inputs['Row Height'].default_value = w
        br.inputs['Bias'].default_value = 0.0
        uv = _uv_from_object(N, L, mode)
        L.new(uv, br.inputs['Vector'])
        # grain: stretched wave bands along the boards
        mp = N.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (0.15, 1.6, 1.0)
        L.new(uv, mp.inputs['Vector'])
        wv = N.new('ShaderNodeTexWave')
        wv.bands_direction = 'Y'
        wv.inputs['Scale'].default_value = 1.6
        wv.inputs['Distortion'].default_value = 6.0
        wv.inputs['Detail'].default_value = 1.0
        L.new(mp.outputs[0], wv.inputs['Vector'])
        ramp = N.new('ShaderNodeMapRange')
        ramp.inputs['From Min'].default_value = 0.75
        ramp.inputs['To Max'].default_value = 0.35
        L.new(wv.outputs['Fac'], ramp.inputs['Value'])
        mix = N.new('ShaderNodeMix')
        mix.data_type, mix.blend_type = 'RGBA', 'MULTIPLY'
        L.new(ramp.outputs[0], mix.inputs[0])
        L.new(br.outputs['Color'], mix.inputs[6])
        mix.inputs[7].default_value = tuple(c * 0.6 for c in base[:3]) + (1,)
        L.new(mix.outputs[2], bsdf.inputs['Base Color'])
    elif kind == 'stripes':
        _, col, w, axis = tex
        tc = N.new('ShaderNodeTexCoord')
        sep = N.new('ShaderNodeSeparateXYZ')
        L.new(tc.outputs['Object'], sep.inputs[0])
        m1 = N.new('ShaderNodeMath')
        m1.operation = 'PINGPONG'
        m1.inputs[1].default_value = w
        L.new(sep.outputs['X' if axis == 'x' else 'Z'], m1.inputs[0])
        m2 = N.new('ShaderNodeMath')
        m2.operation = 'GREATER_THAN'
        m2.inputs[1].default_value = w * 0.5
        L.new(m1.outputs[0], m2.inputs[0])
        mix = N.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        L.new(m2.outputs[0], mix.inputs[0])
        mix.inputs[6].default_value = base
        mix.inputs[7].default_value = hexcol(col)
        L.new(mix.outputs[2], bsdf.inputs['Base Color'])
    elif kind == 'patch':
        _, cols, size = tex
        tc = N.new('ShaderNodeTexCoord')
        mp = N.new('ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (1 / size,) * 3
        L.new(tc.outputs['Object'], mp.inputs['Vector'])
        vor = N.new('ShaderNodeTexVoronoi')       # one random value per square
        vor.inputs['Randomness'].default_value = 0.0
        flo = N.new('ShaderNodeVectorMath')
        flo.operation = 'FLOOR'
        L.new(mp.outputs[0], flo.inputs[0])
        L.new(flo.outputs[0], vor.inputs['Vector'])
        ramp = N.new('ShaderNodeValToRGB')
        ramp.color_ramp.interpolation = 'CONSTANT'
        els = ramp.color_ramp.elements
        while len(els) < len(cols):
            els.new(0.5)
        for i, c in enumerate(cols):
            els[i].position = i / len(cols)
            els[i].color = hexcol(c)
        L.new(vor.outputs['Color'], ramp.inputs['Fac'])
        L.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])


def toon(name, hexc, emit=False, rough=0.75, tex=None):
    """Soft cartoon material.

    tex: None
         ('brick', mortar_hex, brick_w, brick_h, mode)   mode = 'wall' | 'floor'
         ('tiles', grout_hex, size)
         ('planks', line_hex, plank_w, mode)      staggered wood boards + grain
         ('stripes', stripe_hex, width, axis)     axis 'x' | 'z' (fabric, pyjamas, wallpaper)
         ('patch', [hex, ...], size)              patchwork quilt squares in several colours
    """
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    out = N.new('ShaderNodeOutputMaterial')
    base = hexcol(hexc)
    if emit:
        em = N.new('ShaderNodeEmission')
        em.inputs['Color'].default_value = base
        L.new(em.outputs[0], out.inputs['Surface'])
    else:
        bsdf = N.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = base
        bsdf.inputs['Roughness'].default_value = rough
        for nm, v in (('Specular IOR Level', 0.12), ('Specular', 0.12)):
            if nm in bsdf.inputs:
                bsdf.inputs[nm].default_value = v
                break
        L.new(bsdf.outputs[0], out.inputs['Surface'])
        if tex and tex[0] in ('planks', 'stripes', 'patch'):
            _tex2(N, L, bsdf, base, tex)
        elif tex:
            kind = tex[0]
            br = N.new('ShaderNodeTexBrick')
            dark = tuple(c * 0.86 for c in base[:3]) + (1,)
            br.inputs['Color1'].default_value = base
            br.inputs['Color2'].default_value = dark
            br.inputs['Mortar'].default_value = hexcol(tex[1])
            br.inputs['Scale'].default_value = 1.0
            if kind == 'brick':
                _, _, bw, bh, mode = tex
                br.offset = 0.5
                br.inputs['Mortar Size'].default_value = 0.025
                br.inputs['Brick Width'].default_value = bw
                br.inputs['Row Height'].default_value = bh
                br.inputs['Bias'].default_value = -0.6
            else:
                size = tex[2]
                mode = tex[3] if len(tex) > 3 else 'floor'
                br.offset = 0.0
                br.inputs['Mortar Size'].default_value = 0.02
                br.inputs['Brick Width'].default_value = size
                br.inputs['Row Height'].default_value = size
                br.inputs['Bias'].default_value = -0.4
            L.new(_uv_from_object(N, L, mode), br.inputs['Vector'])
            L.new(br.outputs['Color'], bsdf.inputs['Base Color'])
            if PAINT:      # mortar/grout reads as drawn lines: darker version of the surface
                br.inputs['Mortar'].default_value = tuple(c * 0.5 for c in base[:3]) + (1,)
        if PAINT:
            _paint(N, L, bsdf, base)
    m.diffuse_color = base
    _mats[name] = m
    return m


def glassy(name, hexc, alpha=0.5, emit_strength=0.0):
    """See-through material (ice, glass, water drops)."""
    if name in _mats:
        return _mats[name]
    m = toon(name, hexc, rough=0.2)
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Alpha'].default_value = alpha
    if emit_strength:
        bsdf.inputs['Emission Color'].default_value = hexcol(hexc)
        bsdf.inputs['Emission Strength'].default_value = emit_strength
    m.surface_render_method = 'BLENDED'
    m.use_backface_culling = False
    return m


def water_mat(name='WaterStream', hexc='#CFF0FF', speed=0.32):
    """Streaky falling water: stretched noise that scrolls downward each frame."""
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    out = N.new('ShaderNodeOutputMaterial')
    bsdf = N.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = hexcol(hexc)
    bsdf.inputs['Roughness'].default_value = 0.1
    bsdf.inputs['Emission Color'].default_value = hexcol(hexc)
    bsdf.inputs['Emission Strength'].default_value = 0.35
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (7.0, 7.0, 0.5)
    L.new(tc.outputs['Object'], mp.inputs['Vector'])
    fc = mp.inputs['Location'].driver_add('default_value', 2)
    fc.driver.type = 'SCRIPTED'
    fc.driver.expression = f'frame*{speed}'
    nz = N.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 3.0
    nz.inputs['Detail'].default_value = 1.0
    L.new(mp.outputs[0], nz.inputs['Vector'])
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (0.8, 0.8, 0.8, 1)
    L.new(nz.outputs['Fac'], ramp.inputs['Fac'])
    L.new(ramp.outputs['Color'], bsdf.inputs['Alpha'])
    L.new(bsdf.outputs[0], out.inputs['Surface'])
    m.surface_render_method = 'BLENDED'
    m.use_backface_culling = False
    _mats[name] = m
    return m


def key_color(mat, frame, hexc):
    """Animate a toon material's colour (e.g. skin turning blue from cold)."""
    inp = mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']
    inp.default_value = hexcol(hexc)
    inp.keyframe_insert('default_value', frame=frame)


def key_energy(light_ob, frame, energy):
    light_ob.data.energy = energy
    light_ob.data.keyframe_insert('energy', frame=frame)


_font = None


def text_obj(name, body, size, loc, mat, rot=(90, 0, 0), extrude=0.04, parent=None):
    global _font
    if _font is None:
        try:
            _font = bpy.data.fonts.load('C:/Windows/Fonts/ariblk.ttf')
        except Exception:
            _font = False
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    if _font:
        cu.font = _font
    cu.size = size
    cu.extrude = extrude
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    cu.materials.append(mat)
    if parent:
        ob.parent = parent
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    return ob


def cone(name, r_bottom, r_top, depth, loc=(0, 0, 0), mat=None, parent=None, outline=0.0, verts=40, rot=None, caps=True):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=caps, segments=verts, radius1=r_bottom, radius2=r_top, depth=depth)
    bm.to_mesh(me)
    bm.free()
    ob = _link(name, me, loc, mat, parent, 0)
    for p in me.polygons:
        p.use_smooth = len(p.vertices) == 4
    if rot:
        ob.rotation_euler = [math.radians(a) for a in rot]
    if outline:
        add_outline(ob, outline)
    return ob


class SetBuilder:
    """Build a set around (0,0,0), then move all of it to `origin` in one go.

        with SetBuilder('Bathroom', (0, 0, 0)) as root: ...build objects...
    """
    def __init__(self, name, origin):
        self.name, self.origin = name, origin

    def __enter__(self):
        self.before = set(bpy.data.objects)
        self.root = bpy.data.objects.new(self.name, None)
        bpy.context.scene.collection.objects.link(self.root)
        return self.root

    def __exit__(self, *exc):
        for ob in set(bpy.data.objects) - self.before:
            if ob is not self.root and ob.parent is None:
                ob.parent = self.root
        self.root.location = self.origin
        return False


def outline_mat():
    if 'Outline' in _mats:
        return _mats['Outline']
    m = toon('Outline', LINE_HEX, emit=True)
    m.use_backface_culling = True
    m.use_backface_culling_shadow = True
    # the shell must not cast shadows, or it speckles the object it wraps (shadow acne)
    N, L = m.node_tree.nodes, m.node_tree.links
    out = N.get('Material Output')
    em = out.inputs['Surface'].links[0].from_node
    lp = N.new('ShaderNodeLightPath')
    tr = N.new('ShaderNodeBsdfTransparent')
    mix = N.new('ShaderNodeMixShader')
    L.new(lp.outputs['Is Shadow Ray'], mix.inputs[0])
    L.new(em.outputs[0], mix.inputs[1])
    L.new(tr.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    m.surface_render_method = 'DITHERED'
    if hasattr(m, 'use_transparent_shadow'):
        m.use_transparent_shadow = True
    return m


def add_outline(ob, thick=0.03):
    """Inverted-hull outline: a slightly bigger dark shell, inside-out."""
    ob.data.materials.append(outline_mat())
    mod = ob.modifiers.new('Outline', 'SOLIDIFY')
    mod.thickness = thick
    mod.offset = 1
    mod.use_flip_normals = True
    mod.use_rim = False
    mod.material_offset = len(ob.data.materials) - 1


def _link(name, me, loc, mat, parent, outline, smooth=True):
    for p in me.polygons:
        p.use_smooth = smooth
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if mat:
        me.materials.append(mat)
    if parent:
        ob.parent = parent
    ob.location = loc
    if outline:
        add_outline(ob, outline)
    return ob


def ellipsoid(name, radii, loc=(0, 0, 0), mat=None, parent=None, outline=0.0, segs=48, rings=24):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * radii[0], v.co.y * radii[1], v.co.z * radii[2]))
    bm.to_mesh(me)
    bm.free()
    return _link(name, me, loc, mat, parent, outline)


def box(name, size, loc=(0, 0, 0), mat=None, parent=None, outline=0.0, bevel=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    bm.to_mesh(me)
    bm.free()
    ob = _link(name, me, loc, mat, parent, 0, smooth=False)
    if bevel:
        b = ob.modifiers.new('Bevel', 'BEVEL')
        b.width = bevel
        b.segments = 1
    if outline:
        add_outline(ob, outline)
    return ob


def cylinder(name, radius, depth, loc=(0, 0, 0), mat=None, parent=None, outline=0.0, verts=40, rot=None):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=radius, radius2=radius, depth=depth)
    bm.to_mesh(me)
    bm.free()
    ob = _link(name, me, loc, mat, parent, 0)
    for p in me.polygons:
        p.use_smooth = len(p.vertices) == 4
    if rot:
        ob.rotation_euler = [math.radians(a) for a in rot]
    if outline:
        add_outline(ob, outline)
    return ob


def tube(name, pts, radius, mat, parent=None, outline=0.0, loc=(0, 0, 0), radii=None):
    """A smooth round tube through a list of points (limbs, hair strands, mouths)."""
    cu = bpy.data.curves.new(name + '_c', 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = radius
    cu.bevel_resolution = 4
    cu.use_fill_caps = True
    cu.resolution_u = 8
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(pts) - 1)
    for i, (bp, p) in enumerate(zip(sp.bezier_points, pts)):
        bp.co = Vector(p)
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
        if radii:
            bp.radius = radii[i]
    tmp = bpy.data.objects.new(name + '_tmp', cu)
    bpy.context.scene.collection.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp)
    bpy.data.curves.remove(cu)
    me.name = name
    return _link(name, me, loc, mat, parent, outline)


def empty(name, loc=(0, 0, 0), parent=None):
    ob = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(ob)
    if parent:
        ob.parent = parent
    ob.location = loc
    return ob


def clear_scene():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)


def setup_render(res_pct=100, samples=24, sky_hex='#9CB8E0', sky_strength=1.0):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    ee = sc.eevee
    ee.taa_render_samples = samples
    ee.use_shadows = True
    ee.use_raytracing = True
    ee.use_fast_gi = True
    ee.fast_gi_distance = 2.0
    sc.render.resolution_x = 1080
    sc.render.resolution_y = 1920
    sc.render.resolution_percentage = res_pct
    sc.render.fps = 30
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.render.image_settings.file_format = 'PNG'
    w = sc.world or bpy.data.worlds.new('World')
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get('Background')
    bg.inputs[0].default_value = hexcol(sky_hex)
    bg.inputs[1].default_value = sky_strength


def setup_lines(enable=True, thickness=2.2, crease_deg=125):
    """Freestyle edge lines on hard edges (desk corners, door frames ...)."""
    sc = bpy.context.scene
    sc.render.use_freestyle = enable
    if not enable:
        return
    sc.render.line_thickness_mode = 'ABSOLUTE'
    sc.render.line_thickness = thickness
    fs = sc.view_layers[0].freestyle_settings
    fs.crease_angle = math.radians(crease_deg)
    ls = fs.linesets[0] if len(fs.linesets) else fs.linesets.new('Lines')
    ls.select_by_visibility = True
    ls.select_by_edge_types = True
    ls.select_silhouette = True
    ls.select_border = True
    ls.select_crease = True
    ls.linestyle.color = hexcol(LINE_HEX)[:3]
    ls.linestyle.thickness = thickness


def sun(rot_deg=(50, 0, -35), strength=4.0, hexc='#FFE7A8', angle=2):
    ld = bpy.data.lights.new('Sun', 'SUN')
    ld.energy = strength
    ld.color = hexcol(hexc)[:3]
    ld.angle = math.radians(angle)
    ob = bpy.data.objects.new('Sun', ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = [math.radians(a) for a in rot_deg]
    return ob


def area_light(loc, rot_deg, size, power, hexc='#FFFFFF', name='Area'):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.size = size
    ld.energy = power
    ld.color = hexcol(hexc)[:3]
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot_deg]
    return ob


def point_light(loc, power, hexc='#FFFFFF', radius=0.3, name='Point'):
    ld = bpy.data.lights.new(name, 'POINT')
    ld.energy = power
    ld.shadow_soft_size = radius
    ld.color = hexcol(hexc)[:3]
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    return ob


def camera(loc, target, lens=24, name='Cam'):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.clip_start = 0.05
    cam = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    tgt = empty(name + 'Target', target)
    c = cam.constraints.new('TRACK_TO')
    c.target = tgt
    c.track_axis = 'TRACK_NEGATIVE_Z'
    c.up_axis = 'UP_Y'
    bpy.context.scene.camera = cam
    return cam, tgt


def dof(cam, focus_obj, fstop=2.0):
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = focus_obj
    cam.data.dof.aperture_fstop = fstop


def key(ob, path, frame, value):
    setattr(ob, path, value)
    ob.keyframe_insert(data_path=path, frame=frame)


def show(objs, frame, visible):
    """Keyframe visibility (used to swap facial expressions)."""
    for o in objs:
        o.hide_render = not visible
        o.keyframe_insert('hide_render', frame=frame)
        for c in o.children_recursive:
            c.hide_render = not visible
            c.keyframe_insert('hide_render', frame=frame)
