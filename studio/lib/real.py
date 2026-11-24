"""'Real light' look (EP06+), modelled on the newest Ricks Clips Shorts.

What changes from the old toon look:
  * sets get believable materials (painted concrete, brick, tiles, metal, wood) with grime,
    roughness variation and bump; NO ink lines on the world
  * characters keep their inverted-hull outlines + black stick limbs (the only drawn lines)
  * AgX colour, a strong sun with crisp shadows, light shafts through a volume box
  * compositor: soft bloom, gentle vignette, nothing else

    import real
    real.setup(pct, samples)
    m = real.mat('Wall', '#9FB4C4', 'paint')
    real.shafts((x, y, z), (sx, sy, sz), density=0.02)
    real.finish()                     # after all objects exist
"""
import math
import bpy
from toon import hexcol, _mats


def setup(pct=50, samples=8, sky='#A9C6E8', sky_strength=1.0, exposure=0.0):
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in
                                                               bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
    if __import__('os').environ.get('WIDE'):   # long form: 16:9
        sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.resolution_percentage = pct
    sc.render.fps = 30
    sc.render.image_settings.file_format = 'PNG'
    sc.eevee.taa_render_samples = samples
    for k, v in (('use_shadows', True), ('shadow_ray_count', 1), ('shadow_step_count', 6),
                 ('volumetric_tile_size', '8'), ('volumetric_samples', 48),
                 ('volumetric_shadow_samples', 16), ('use_volumetric_shadows', True),
                 ('volumetric_end', 60.0)):
        if hasattr(sc.eevee, k):
            try:
                setattr(sc.eevee, k, v)
            except Exception:
                pass
    # cheap screen-space GI + AO feel
    sc.eevee.use_raytracing = True
    sc.eevee.ray_tracing_method = 'PROBE'
    sc.eevee.use_fast_gi = True
    sc.eevee.fast_gi_method = 'GLOBAL_ILLUMINATION'
    sc.eevee.fast_gi_distance = 4.0
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    sc.view_settings.exposure = exposure
    w = sc.world or bpy.data.worlds.new('World')
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get('Background')
    bg.inputs[0].default_value = hexcol(sky)
    bg.inputs[1].default_value = sky_strength
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5


# ---------------------------------------------------------------- materials
def _n(N, t, **kw):
    n = N.new(t)
    for k, v in kw.items():
        if k in n.inputs:
            n.inputs[k].default_value = v
        else:
            setattr(n, k, v)
    return n


def _coords(N, L, mode, scale):
    """Object-space coordinates, flattened for walls ('wall': x+y, z) or floors ('floor': x, y)."""
    tc = N.new('ShaderNodeTexCoord')
    if mode == 'box':
        mp = _n(N, 'ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (scale,) * 3
        L.new(tc.outputs['Object'], mp.inputs['Vector'])
        return mp.outputs[0]
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['Object'], sep.inputs[0])
    comb = N.new('ShaderNodeCombineXYZ')
    if mode == 'wall':
        a = _n(N, 'ShaderNodeMath', operation='ADD')
        L.new(sep.outputs['X'], a.inputs[0])
        L.new(sep.outputs['Y'], a.inputs[1])
        L.new(a.outputs[0], comb.inputs['X'])
        L.new(sep.outputs['Z'], comb.inputs['Y'])
    elif mode == 'wallx':      # wall facing +-X (uses y, z)
        L.new(sep.outputs['Y'], comb.inputs['X'])
        L.new(sep.outputs['Z'], comb.inputs['Y'])
    else:
        L.new(sep.outputs['X'], comb.inputs['X'])
        L.new(sep.outputs['Y'], comb.inputs['Y'])
    mp = _n(N, 'ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale,) * 3
    L.new(comb.outputs[0], mp.inputs['Vector'])
    return mp.outputs[0]


def mat(name, hexc, kind='paint', mode='box', scale=1.0, line=None, size=(1.0, 0.5), rough=None,
        grime=0.25, emit=0.0, metal=None):
    """Believable stylised surface.

    kind: paint | concrete | brick | tile | wood | metal | plastic | flesh | fabric | glow
    mode: 'box' (any object) | 'wall' | 'wallx' | 'floor'   (how a pattern is laid out)
    size: (brick/tile width, height) in metres;  line: grout/mortar colour hex
    grime: 0..1 dirty patches / darkening variation
    """
    key = f'R_{name}'
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    out = N.new('ShaderNodeOutputMaterial')
    base = hexcol(hexc)
    if kind == 'glow':
        em = _n(N, 'ShaderNodeEmission', Strength=emit or 6.0)
        em.inputs['Color'].default_value = base
        L.new(em.outputs[0], out.inputs['Surface'])
        m.diffuse_color = base
        _mats[key] = m
        return m
    b = N.new('ShaderNodeBsdfPrincipled')
    L.new(b.outputs[0], out.inputs['Surface'])
    defaults = {'paint': 0.7, 'concrete': 0.9, 'brick': 0.85, 'tile': 0.25, 'wood': 0.6, 'metal': 0.35,
                'plastic': 0.4, 'flesh': 0.35, 'fabric': 0.95}
    b.inputs['Roughness'].default_value = rough if rough is not None else defaults.get(kind, 0.6)
    b.inputs['Metallic'].default_value = metal if metal is not None else (0.85 if kind == 'metal' else 0.0)
    if 'Specular IOR Level' in b.inputs:
        b.inputs['Specular IOR Level'].default_value = 0.35 if kind in ('tile', 'flesh', 'plastic') else 0.2
    uv = _coords(N, L, mode, scale)
    col = None          # colour socket
    height = None       # bump height socket
    dark = tuple(c * 0.72 for c in base[:3]) + (1,)
    if kind in ('brick', 'tile'):
        bw, bh = size
        br = _n(N, 'ShaderNodeTexBrick', Scale=1.0, Bias=0.0,
                **{'Mortar Size': 0.012 if kind == 'tile' else 0.018, 'Brick Width': bw, 'Row Height': bh,
                   'Mortar Smooth': 0.15})
        br.offset = 0.5 if kind == 'brick' else 0.0
        br.inputs['Color1'].default_value = base
        br.inputs['Color2'].default_value = tuple(c * (0.9 if kind == 'brick' else 0.97) for c in base[:3]) + (1,)
        br.inputs['Mortar'].default_value = hexcol(line) if line else tuple(c * 0.62 for c in base[:3]) + (1,)
        L.new(uv, br.inputs['Vector'])
        col = br.outputs['Color']
        height = br.outputs['Fac']
    elif kind == 'wood':
        mp = _n(N, 'ShaderNodeMapping')
        mp.inputs['Scale'].default_value = (0.2, 3.0, 1.0)
        L.new(uv, mp.inputs['Vector'])
        wv = _n(N, 'ShaderNodeTexWave', Scale=2.0, Distortion=7.0, Detail=2.0)
        wv.bands_direction = 'Y'
        L.new(mp.outputs[0], wv.inputs['Vector'])
        mx = _n(N, 'ShaderNodeMix', data_type='RGBA')
        L.new(wv.outputs['Fac'], mx.inputs[0])
        mx.inputs[6].default_value = base
        mx.inputs[7].default_value = dark
        col = mx.outputs[2]
    elif kind == 'flesh':
        vo = _n(N, 'ShaderNodeTexVoronoi', Scale=3.0)
        L.new(uv, vo.inputs['Vector'])
        mx = _n(N, 'ShaderNodeMix', data_type='RGBA')
        rr = _n(N, 'ShaderNodeMapRange', **{'From Min': 0.0, 'From Max': 0.6})
        L.new(vo.outputs['Distance'], rr.inputs['Value'])
        L.new(rr.outputs[0], mx.inputs[0])
        mx.inputs[6].default_value = tuple(min(1, c * 1.25) for c in base[:3]) + (1,)
        mx.inputs[7].default_value = base
        col = mx.outputs[2]
        height = vo.outputs['Distance']
        b.inputs['Subsurface Weight'].default_value = 0.15
        b.inputs['Subsurface Radius'].default_value = (1.0, 0.3, 0.2)
    elif kind == 'fabric':
        nz = _n(N, 'ShaderNodeTexNoise', Scale=60.0, Detail=2.0)
        L.new(uv, nz.inputs['Vector'])
        height = nz.outputs['Fac']
    # grime: large soft blotches + fine speckle darken the colour
    if grime:
        nz = _n(N, 'ShaderNodeTexNoise', Scale=1.6, Detail=6.0, Roughness=0.62)
        L.new(uv, nz.inputs['Vector'])
        rr = _n(N, 'ShaderNodeMapRange', **{'From Min': 0.42, 'From Max': 0.72, 'To Min': 0.0, 'To Max': grime})
        L.new(nz.outputs['Fac'], rr.inputs['Value'])
        mx = _n(N, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
        L.new(rr.outputs[0], mx.inputs[0])
        if col:
            L.new(col, mx.inputs[6])
        else:
            mx.inputs[6].default_value = base
        mx.inputs[7].default_value = tuple(c * 0.55 for c in base[:3]) + (1,)
        col = mx.outputs[2]
        # roughness varies with the grime
        rg = _n(N, 'ShaderNodeMapRange', **{'To Min': b.inputs['Roughness'].default_value * 0.8,
                                              'To Max': min(1.0, b.inputs['Roughness'].default_value * 1.2)})
        L.new(nz.outputs['Fac'], rg.inputs['Value'])
        L.new(rg.outputs[0], b.inputs['Roughness'])
        if kind in ('concrete', 'paint', 'metal') and height is None:
            fine = _n(N, 'ShaderNodeTexNoise', Scale=40.0 if kind == 'concrete' else 18.0, Detail=4.0)
            L.new(uv, fine.inputs['Vector'])
            height = fine.outputs['Fac']
    if col:
        L.new(col, b.inputs['Base Color'])
    else:
        b.inputs['Base Color'].default_value = base
    if height is not None:
        bump = _n(N, 'ShaderNodeBump', Strength={'brick': 0.5, 'tile': 0.35, 'concrete': 0.18, 'paint': 0.06,
                                                 'metal': 0.05, 'flesh': 0.25, 'fabric': 0.15}.get(kind, 0.1),
                  Distance=0.02)
        L.new(height, bump.inputs['Height'])
        L.new(bump.outputs[0], b.inputs['Normal'])
    if emit:
        b.inputs['Emission Color'].default_value = base
        b.inputs['Emission Strength'].default_value = emit
    m.diffuse_color = base
    _mats[key] = m
    return m


def glass(name='Glass', hexc='#CFE6F2', alpha=0.15):
    key = f'R_{name}'
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = hexcol(hexc)
    b.inputs['Roughness'].default_value = 0.05
    b.inputs['Alpha'].default_value = alpha
    m.surface_render_method = 'BLENDED' if hasattr(m, 'surface_render_method') else None
    _mats[key] = m
    return m


# ---------------------------------------------------------------- light
def shafts(loc, size, density=0.015, hexc='#FFFFFF', anisotropy=0.6, name='Haze', parent=None):
    """A box of thin haze: the sun / lamps light it up as visible beams (god rays)."""
    me = bpy.data.meshes.new(name)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
        v.co.z *= size[2]
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    if parent:
        ob.parent = parent
    m = bpy.data.materials.new(name + '_vol')
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.remove(N.get('Principled BSDF'))
    v = N.new('ShaderNodeVolumePrincipled')
    v.inputs['Density'].default_value = density
    v.inputs['Anisotropy'].default_value = anisotropy
    v.inputs['Color'].default_value = hexcol(hexc)
    L.new(v.outputs[0], N.get('Material Output').inputs['Volume'])
    me.materials.append(m)
    ob.visible_shadow = False
    return ob


def sun(rot=(50, 0, -35), strength=5.0, hexc='#FFE8C4', angle=1.5, name='Sun'):
    ld = bpy.data.lights.new(name, 'SUN')
    ld.energy = strength
    ld.color = hexcol(hexc)[:3]
    ld.angle = math.radians(angle)
    if hasattr(ld, 'shadow_filter_radius'):
        ld.shadow_filter_radius = 1.0
    if hasattr(ld, 'volume_factor'):
        ld.volume_factor = 1.0
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = [math.radians(a) for a in rot]
    return ob


def area(loc, rot, size, power, hexc='#FFFFFF', shadow=True, name='Area', volume=1.0):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.size = size
    ld.energy = power
    ld.color = hexcol(hexc)[:3]
    ld.use_shadow = shadow
    if hasattr(ld, 'volume_factor'):
        ld.volume_factor = volume
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    return ob


def spot(loc, rot, power, angle=60, hexc='#FFF1DC', blend=0.4, name='Spot', radius=0.1, volume=1.0):
    ld = bpy.data.lights.new(name, 'SPOT')
    ld.energy = power
    ld.spot_size = math.radians(angle)
    ld.spot_blend = blend
    ld.shadow_soft_size = radius
    ld.color = hexcol(hexc)[:3]
    if hasattr(ld, 'volume_factor'):
        ld.volume_factor = volume
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    return ob


# ---------------------------------------------------------------- finish
def finish(bloom=0.45, vignette=0.25, saturation=1.05):
    sc = bpy.context.scene
    ng = bpy.data.node_groups.new('RealLook', 'CompositorNodeTree')
    ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    sc.compositing_node_group = ng
    N, L = ng.nodes, ng.links
    rl = N.new('CompositorNodeRLayers')
    rl.scene = sc
    out = N.new('NodeGroupOutput')
    img = rl.outputs['Image']
    if bloom:
        g = N.new('CompositorNodeGlare')
        g.inputs['Type'].default_value = 'Bloom'
        g.inputs['Threshold'].default_value = 0.9
        g.inputs['Strength'].default_value = bloom
        g.inputs['Size'].default_value = 0.7
        L.new(img, g.inputs['Image'])
        img = g.outputs['Image']
    if saturation != 1.0:
        hs = N.new('CompositorNodeHueSat')
        hs.inputs['Saturation'].default_value = saturation
        L.new(img, hs.inputs['Image'])
        img = hs.outputs[0]
    if vignette:
        ell = N.new('CompositorNodeEllipseMask')
        ell.inputs['Size'].default_value = (0.95, 0.9)
        bl = N.new('CompositorNodeBlur')
        if 'Size' in bl.inputs:
            bl.inputs['Size'].default_value = (120, 120)
        L.new(ell.outputs[0], bl.inputs['Image'])
        mx = N.new('ShaderNodeMix')
        mx.data_type = 'RGBA'
        mx.blend_type = 'MULTIPLY'
        inv = N.new('ShaderNodeMath')
        inv.operation = 'SUBTRACT'
        inv.inputs[0].default_value = 1.0
        L.new(bl.outputs[0], inv.inputs[1])
        mul = N.new('ShaderNodeMath')
        mul.operation = 'MULTIPLY'
        mul.inputs[1].default_value = vignette
        L.new(inv.outputs[0], mul.inputs[0])
        L.new(mul.outputs[0], mx.inputs[0])
        L.new(img, mx.inputs[6])
        mx.inputs[7].default_value = (0.1, 0.1, 0.14, 1)
        img = mx.outputs[2]
    L.new(img, out.inputs[0])
    return ng


def glow_chars(rig, amount=0.35):
    """Keep doodle characters bright like the reference: a little self-light on every material of the rig."""
    done = set()
    for ob in [rig['mover']] + list(rig['mover'].children_recursive):
        if not getattr(ob, 'material_slots', None):
            continue
        for sl in ob.material_slots:
            m = sl.material
            if not m or m.name in done or not m.use_nodes or m.name == 'Outline':
                continue
            done.add(m.name)
            N, L = m.node_tree.nodes, m.node_tree.links
            b = next((n for n in N if n.type == 'BSDF_PRINCIPLED'), None)
            if not b:
                continue
            bc = b.inputs['Base Color']
            if bc.is_linked:
                L.new(bc.links[0].from_socket, b.inputs['Emission Color'])
            else:
                b.inputs['Emission Color'].default_value = bc.default_value
            b.inputs['Emission Strength'].default_value = amount


def point(loc, power, hexc='#FFFFFF', radius=0.3, name='Point', volume=0.5):
    ld = bpy.data.lights.new(name, 'POINT')
    ld.energy = power
    ld.shadow_soft_size = radius
    ld.color = hexcol(hexc)[:3]
    if hasattr(ld, 'volume_factor'):
        ld.volume_factor = volume
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    return ob
