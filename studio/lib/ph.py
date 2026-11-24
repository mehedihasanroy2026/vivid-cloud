"""Realistic set helpers built on Poly Haven CC0 assets (tools/polyhaven.py downloads them).

    import ph
    ph.setup(pct=100, samples=32)
    m = ph.pbr('rock', 'rock_wall_08', scale=0.5)
    wall = ph.slab('wall', (8, 4), loc, rot, m, disp=('rock_wall_08', 0.25), cuts=160)
    ph.model('Lantern_01', loc, rot, scale)
"""
import math
import os
import bpy
import bmesh
from mathutils import Vector

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'polyhaven')


QUALITY = os.environ.get('DGN_QUALITY', 'draft').lower()     # draft (laptop stills) | final | ultra (cloud)

# Eevee quality profiles. 'draft' keeps laptop test stills cheap; the cloud notebook sets
# DGN_QUALITY=final/ultra for the real render (full-res raytracing, fine volumetrics, soft shadows).
PROFILES = {
    'draft': dict(shadow_ray_count=1, shadow_step_count=6, shadow_resolution_scale=0.5,
                  ray_tracing_method='SCREEN', rt_res='2', rt_quality=0.25, rt_rough=0.5,
                  fast_gi_resolution='4', fast_gi_step_count=4, fast_gi_ray_count=2, fast_gi_quality=0.25,
                  volumetric_tile_size='8', volumetric_samples=32, volumetric_shadow_samples=8,
                  motion_blur_steps=1, filter_size=1.5, jitter=False),
    'final': dict(shadow_ray_count=3, shadow_step_count=12, shadow_resolution_scale=1.0,
                  ray_tracing_method='SCREEN', rt_res='1', rt_quality=1.0, rt_rough=0.6,
                  fast_gi_resolution='2', fast_gi_step_count=12, fast_gi_ray_count=4, fast_gi_quality=0.8,
                  volumetric_tile_size='2', volumetric_samples=96, volumetric_shadow_samples=24,
                  motion_blur_steps=2, filter_size=1.5, jitter=True),
    'ultra': dict(shadow_ray_count=4, shadow_step_count=16, shadow_resolution_scale=1.0,
                  ray_tracing_method='SCREEN', rt_res='1', rt_quality=1.0, rt_rough=0.8,
                  fast_gi_resolution='1', fast_gi_step_count=16, fast_gi_ray_count=8, fast_gi_quality=1.0,
                  volumetric_tile_size='2', volumetric_samples=128, volumetric_shadow_samples=32,
                  motion_blur_steps=3, filter_size=1.5, jitter=True),
}


def _set(obj, k, v, miss):
    try:
        setattr(obj, k, v)
    except Exception:
        miss.append(k)


def setup(pct=100, samples=32, fps=30, frames=180, view='Khronos PBR Neutral', look='None', exposure=0.0):
    """view: 'Khronos PBR Neutral' keeps flat characters paper-white and colours true (AgX greyed them)."""
    sc = bpy.context.scene
    ids = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
    sc.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in ids else 'BLENDER_EEVEE_NEXT'
    sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
    sc.render.resolution_percentage = pct
    sc.render.fps = fps
    sc.frame_start, sc.frame_end = 1, frames
    P = PROFILES.get(QUALITY, PROFILES['draft'])
    ee = sc.eevee
    ee.taa_render_samples = samples
    miss = []
    for k, v in (('use_shadows', True), ('shadow_ray_count', P['shadow_ray_count']),
                 ('shadow_step_count', P['shadow_step_count']), ('shadow_resolution_scale', P['shadow_resolution_scale']),
                 ('use_raytracing', True), ('ray_tracing_method', P['ray_tracing_method']),
                 ('use_fast_gi', True), ('fast_gi_method', 'GLOBAL_ILLUMINATION'), ('fast_gi_distance', 3.0),
                 ('fast_gi_resolution', P['fast_gi_resolution']), ('fast_gi_step_count', P['fast_gi_step_count']),
                 ('fast_gi_ray_count', P['fast_gi_ray_count']), ('fast_gi_quality', P['fast_gi_quality']),
                 ('volumetric_tile_size', P['volumetric_tile_size']), ('volumetric_samples', P['volumetric_samples']),
                 ('volumetric_end', 30.0), ('use_volumetric_shadows', True),
                 ('volumetric_shadow_samples', P['volumetric_shadow_samples']),
                 ('motion_blur_steps', P['motion_blur_steps']), ('clamp_surface_indirect', 10.0),
                 ('use_overscan', QUALITY != 'draft'), ('overscan_size', 3.0),
                 # 512 MB default overflowed at full res ('Shadow buffer full' -> missing shadows); cloud GPUs have 16+ GB
                 ('shadow_pool_size', '512' if QUALITY == 'draft' else '2048')):
        _set(ee, k, v, miss)
    rt = ee.ray_tracing_options
    for k, v in (('resolution_scale', P['rt_res']), ('screen_trace_quality', P['rt_quality']),
                 ('trace_max_roughness', P['rt_rough']), ('use_denoise', True), ('denoise_spatial', True),
                 ('denoise_temporal', True), ('denoise_bilateral', True)):
        _set(rt, k, v, miss)
    _set(sc.render, 'use_motion_blur', True, miss)
    _set(sc.render, 'motion_blur_shutter', 0.5, miss)
    _set(sc.render, 'filter_size', P['filter_size'], miss)
    _set(sc.render, 'use_high_quality_normals', QUALITY != 'draft', miss)
    if miss:
        print('DGN: quality settings not in this Blender:', miss)
    print(f'DGN: quality {QUALITY}  {round(1080 * pct / 100)}x{round(1920 * pct / 100)}  samples {samples}')
    sc.view_settings.view_transform = view
    try:
        sc.view_settings.look = look
    except Exception:
        pass
    sc.view_settings.exposure = exposure
    sc.render.film_transparent = False
    if os.environ.get('DGN_ENGINE', '').upper() == 'CYCLES':
        cycles_gpu(sc, samples)
    return sc


def soft_shadows():
    """Final/ultra: jittered (truly soft, ray-traced-looking) shadows on every light. Call once after all lights exist."""
    if QUALITY == 'draft':
        return
    for ld in bpy.data.lights:
        if ld.use_shadow:
            try:
                ld.use_shadow_jitter = True
                ld.shadow_jitter_overblur = 10.0
                ld.shadow_maximum_resolution = 0.001
            except Exception:
                pass


def cycles_gpu(sc, samples=32):
    """Cloud fallback when Eevee can't open a GPU context (headless Linux): Cycles on the GPU + denoise."""
    sc.render.engine = 'CYCLES'
    prefs = bpy.context.preferences.addons['cycles'].preferences
    for kind in ('OPTIX', 'CUDA'):
        try:
            prefs.compute_device_type = kind
            prefs.get_devices()
            devs = [d for d in prefs.devices if d.type == kind]
            if devs:
                for d in prefs.devices:
                    d.use = (d.type == kind)
                break
        except Exception:
            continue
    cy = sc.cycles
    cy.device = 'GPU'
    cy.samples = max(12, samples)
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.03
    cy.use_denoising = True
    for k, v in (('denoiser', 'OPTIX'), ('denoising_use_gpu', True), ('use_light_tree', True),
                 ('max_bounces', 3), ('diffuse_bounces', 2), ('glossy_bounces', 1), ('transmission_bounces', 2),
                 ('volume_bounces', 0), ('transparent_max_bounces', 8), ('caustics_reflective', False),
                 ('caustics_refractive', False), ('blur_glossy', 1.0)):
        try:
            setattr(cy, k, v)
        except Exception:
            pass
    sc.render.use_persistent_data = True     # keep textures/BVH between frames
    print('DGN: Cycles on', prefs.compute_device_type, 'samples', cy.samples)


def drop_volumes():
    """Haze volumes are very slow in Cycles: remove the world volume (call after world())."""
    w = bpy.context.scene.world
    if w and w.use_nodes:
        out = next((n for n in w.node_tree.nodes if n.bl_idname == 'ShaderNodeOutputWorld'), None)
        if out:
            for l in list(out.inputs['Volume'].links):
                w.node_tree.links.remove(l)


def world(col='#1B2238', strength=0.35, haze=0.0, haze_col='#FFE2B8'):
    w = bpy.data.worlds.get('W') or bpy.data.worlds.new('W')
    bpy.context.scene.world = w
    w.use_nodes = True
    N, L = w.node_tree.nodes, w.node_tree.links
    N.clear()
    out = N.new('ShaderNodeOutputWorld')
    bg = N.new('ShaderNodeBackground')
    bg.inputs[0].default_value = hexc(col)
    bg.inputs[1].default_value = strength
    L.new(bg.outputs[0], out.inputs['Surface'])
    if haze > 0:
        v = N.new('ShaderNodeVolumePrincipled')
        v.inputs['Density'].default_value = haze
        v.inputs['Color'].default_value = hexc(haze_col)
        try:
            v.inputs['Anisotropy'].default_value = 0.45
        except Exception:
            pass
        L.new(v.outputs[0], out.inputs['Volume'])
        if bpy.context.scene.render.engine == 'CYCLES':
            drop_volumes()
    return w


def hexc(h, a=1.0):
    h = h.lstrip('#')
    s = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in s]
    return (*lin, a)


def _img(path, non_color=False):
    im = bpy.data.images.load(path, check_existing=True)
    if non_color:
        im.colorspace_settings.name = 'Non-Color'
    return im


def tex_path(tid, name):
    for ext in ('jpg', 'png'):
        p = os.path.join(ROOT, 'tex', tid, f'{name}.{ext}')
        if os.path.exists(p):
            return p
    return None


def pbr(name, tid, scale=1.0, tint=None, tint_mix=0.0, rough_mul=1.0, bump=1.0, rot=0.0, bright=1.0):
    """Principled material from a Poly Haven texture set. scale = repeats per metre."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    bsdf = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (scale, scale, scale)
    mp.inputs['Rotation'].default_value = (0, 0, rot)
    L.new(tc.outputs['UV'], mp.inputs['Vector'])

    def tex(map_name, non_color):
        p = tex_path(tid, map_name)
        if not p:
            return None
        t = N.new('ShaderNodeTexImage')
        t.image = _img(p, non_color)
        L.new(mp.outputs[0], t.inputs['Vector'])
        return t
    d = tex('diff', False)
    col = d.outputs['Color']
    if bright != 1.0 or tint:
        mix = N.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY' if tint else 'MIX'
        mix.inputs['Factor'].default_value = tint_mix if tint else 0.0
        L.new(col, mix.inputs[6])
        mix.inputs[7].default_value = hexc(tint) if tint else (1, 1, 1, 1)
        col = mix.outputs[2]
        if bright != 1.0:
            hsv = N.new('ShaderNodeHueSaturation')
            hsv.inputs['Value'].default_value = bright
            L.new(col, hsv.inputs['Color'])
            col = hsv.outputs[0]
    L.new(col, bsdf.inputs['Base Color'])
    r = tex('rough', True)
    if r:
        if rough_mul != 1.0:
            mm = N.new('ShaderNodeMath')
            mm.operation = 'MULTIPLY'
            mm.inputs[1].default_value = rough_mul
            L.new(r.outputs['Color'], mm.inputs[0])
            L.new(mm.outputs[0], bsdf.inputs['Roughness'])
        else:
            L.new(r.outputs['Color'], bsdf.inputs['Roughness'])
    n = tex('nor_gl', True)
    if n:
        nm = N.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = bump
        L.new(n.outputs['Color'], nm.inputs['Color'])
        L.new(nm.outputs[0], bsdf.inputs['Normal'])
    return m


def slab(name, size, loc, rot, mat, cuts=96, disp=None, uv_scale=None, noise=0.0, noise_scale=1.5):
    """A subdivided plane (XY, normal +Z before rot) with real displacement from the texture's
    height map, so rock and planks have true relief in silhouette."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=cuts, y_segments=max(2, int(cuts * size[1] / size[0])), size=0.5)
    for v in bm.verts:
        v.co.x *= size[0]
        v.co.y *= size[1]
    uv = bm.loops.layers.uv.new()
    for f in bm.faces:
        for lp in f.loops:
            lp[uv].uv = (lp.vert.co.x, lp.vert.co.y)       # 1 UV unit = 1 metre
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    if disp:
        tid, strength = disp[0], disp[1]
        sc = disp[2] if len(disp) > 2 else 1.0
        p = tex_path(tid, 'disp')
        if p:
            t = bpy.data.textures.new(name + '_d', 'IMAGE')
            t.image = _img(p, True)
            t.extension = 'REPEAT'
            md = ob.modifiers.new('disp', 'DISPLACE')
            md.texture = t
            md.texture_coords = 'UV'
            md.strength = strength
            md.mid_level = 0.5
            if sc != 1.0:
                # match the material's scale: scale UVs is done by repeat
                t.repeat_x = t.repeat_y = max(1, int(round(sc)))
    if noise > 0:
        t = bpy.data.textures.new(name + '_n', 'CLOUDS')
        t.noise_scale = noise_scale
        md = ob.modifiers.new('noise', 'DISPLACE')
        md.texture = t
        md.texture_coords = 'GLOBAL'
        md.strength = noise
    return ob


def box(name, dims, loc, mat, rot=(0, 0, 0), bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = dims
    ob.rotation_euler = [math.radians(a) for a in rot]
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    # box-project UVs in metres
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for lp in f.loops:
            c = lp.vert.co
            u, v = [(c.y, c.z), (c.x, c.z), (c.x, c.y)][ax]
            if ax == 0 or ax == 1:
                u, v = (u, v) if dims[2] < max(dims[0], dims[1]) else (v, u)
            lp[uv].uv = (u, v)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    if bevel:
        b = ob.modifiers.new('bev', 'BEVEL')
        b.width = bevel
        b.segments = 2
    return ob


def model(mid, loc, rot=(0, 0, 0), scale=1.0, name=None):
    p = os.path.join(ROOT, 'models', mid, f'{mid}.gltf')
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=p)
    new = [o for o in bpy.data.objects if o not in before]
    root = bpy.data.objects.new(name or mid, None)
    bpy.context.collection.objects.link(root)
    for o in new:
        if o.parent is None:
            o.parent = root
    root.location = loc
    root.rotation_euler = [math.radians(a) for a in rot]
    root.scale = (scale, scale, scale)
    return root


def point(name, loc, col='#FFB060', power=100, radius=0.05, shadow=True):
    ld = bpy.data.lights.new(name, 'POINT')
    ld.color = hexc(col)[:3]
    ld.energy = power
    ld.shadow_soft_size = radius
    ld.use_shadow = shadow
    ob = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    return ob


def spot(name, loc, target, col='#FFD9A0', power=1000, angle=40, blend=0.4, radius=0.1):
    ld = bpy.data.lights.new(name, 'SPOT')
    ld.color = hexc(col)[:3]
    ld.energy = power
    ld.spot_size = math.radians(angle)
    ld.spot_blend = blend
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    aim(ob, target)
    return ob


def area(name, loc, target, col='#9FB4FF', power=100, size=3.0, shadow=False):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.color = hexc(col)[:3]
    ld.energy = power
    ld.size = size
    ld.use_shadow = shadow
    ob = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    aim(ob, target)
    return ob


def aim(ob, target):
    d = Vector(target) - Vector(ob.location)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def camera(name='Cam', lens=32):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    cd.clip_start = 0.05
    ob = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    return ob


def emissive(name, col, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = hexc(col)
    b.inputs['Emission Color'].default_value = hexc(col)
    b.inputs['Emission Strength'].default_value = strength
    return m


def plain(name, col, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = hexc(col)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    return m


def glare(strength=0.4, threshold=1.0, size=7):
    """Soft bloom in the compositor (Eevee Next has no bloom)."""
    sc = bpy.context.scene
    try:
        sc.use_nodes = True
        tree = sc.node_tree
    except Exception:
        tree = None
    if tree is None:
        try:
            tree = bpy.data.node_groups.new('Comp', 'CompositorNodeTree')
            sc.compositing_node_group = tree
            gi = tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
        except Exception as e:
            print('glare: no compositor', e)
            return
    N, L = tree.nodes, tree.links
    rl = next((n for n in N if n.bl_idname == 'CompositorNodeRLayers'), None) or N.new('CompositorNodeRLayers')
    outn = next((n for n in N if n.bl_idname in ('CompositorNodeComposite', 'NodeGroupOutput')), None)
    if outn is None:
        try:
            outn = N.new('CompositorNodeComposite')
        except Exception:
            outn = N.new('NodeGroupOutput')
    g = N.new('CompositorNodeGlare')
    for k, v in (('glare_type', 'FOG_GLOW'), ('quality', 'HIGH'), ('mix', strength - 1.0), ('threshold', threshold), ('size', size)):
        try:
            setattr(g, k, v)
        except Exception:
            pass
    for k, v in (('Type', 'Fog Glow'), ('Threshold', threshold), ('Strength', strength), ('Size', 0.6)):
        if k in g.inputs:
            try:
                g.inputs[k].default_value = v
            except Exception:
                pass
    L.new(rl.outputs['Image'], g.inputs['Image'])
    L.new(g.outputs['Image'], outn.inputs[0])


# ====================================================================== outdoor
def hdri_world(hid, res='4k', strength=1.0, rot=0.0, bg_strength=None, sat=1.0, clamp=None):
    """Poly Haven HDRI sky (python tools/polyhaven.py hdri <id> --res 4k). Lights the scene and is the
    visible sky. bg_strength: brightness of the sky seen by the camera (default = strength)."""
    w = bpy.data.worlds.get('W') or bpy.data.worlds.new('W')
    bpy.context.scene.world = w
    w.use_nodes = True
    N, L = w.node_tree.nodes, w.node_tree.links
    N.clear()
    out = N.new('ShaderNodeOutputWorld')
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0, 0, math.radians(rot))
    L.new(tc.outputs['Generated'], mp.inputs['Vector'])
    env = N.new('ShaderNodeTexEnvironment')
    path = os.path.join(ROOT, 'hdri', f'{hid}_{res}.hdr')
    env.image = bpy.data.images.load(path, check_existing=True)
    L.new(mp.outputs[0], env.inputs['Vector'])
    col = env.outputs['Color']
    if clamp:   # very hot pixels (a moon at 300 000) overflow Eevee's half-float probes -> NaN frame
        vm = N.new('ShaderNodeVectorMath')
        vm.operation = 'MINIMUM'
        vm.inputs[1].default_value = (clamp, clamp, clamp)
        L.new(col, vm.inputs[0])
        col = vm.outputs[0]
    if sat != 1.0:
        hs = N.new('ShaderNodeHueSaturation')
        hs.inputs['Saturation'].default_value = sat
        L.new(col, hs.inputs['Color'])
        col = hs.outputs[0]
    bg = N.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = strength
    L.new(col, bg.inputs['Color'])
    if bg_strength is None or bg_strength == strength:
        L.new(bg.outputs[0], out.inputs['Surface'])
    else:   # camera sees the sky at a different brightness than the light it casts
        bg2 = N.new('ShaderNodeBackground')
        bg2.inputs['Strength'].default_value = bg_strength
        L.new(col, bg2.inputs['Color'])
        lp = N.new('ShaderNodeLightPath')
        mx = N.new('ShaderNodeMixShader')
        L.new(lp.outputs['Is Camera Ray'], mx.inputs[0])
        L.new(bg.outputs[0], mx.inputs[1])
        L.new(bg2.outputs[0], mx.inputs[2])
        L.new(mx.outputs[0], out.inputs['Surface'])
    return w


def sun(name, elev=40, azim=-30, col='#FFF1DC', power=4.0, angle=1.5):
    """Sun from azimuth azim (deg, 0 = from -Y i.e. behind the camera, + = from the right) at elevation elev."""
    ld = bpy.data.lights.new(name, 'SUN')
    ld.color = hexc(col)[:3]
    ld.energy = power
    ld.angle = math.radians(angle)
    ob = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(ob)
    e, a = math.radians(elev), math.radians(azim)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))   # direction TO the sun
    ob.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    return ob


def model_set(name, mids, include=None, exclude=None):
    """Import Poly Haven models into a hidden collection for scattering (every mesh moved to the origin)."""
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    for mid in mids:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'models', mid, f'{mid}.gltf'))
        for o in [o for o in bpy.data.objects if o not in before]:
            keep = o.type == 'MESH' and (not include or any(k in o.name for k in include)) \
                and not (exclude and any(k in o.name for k in exclude))
            for c in list(o.users_collection):
                c.objects.unlink(o)
            if keep:
                o.location = (0, 0, 0)
                coll.objects.link(o)
            else:
                bpy.data.objects.remove(o)
    lc = bpy.context.view_layer.layer_collection.children.get(coll.name)
    if lc:
        lc.exclude = True          # hidden source, only the instances render
    return coll


def paint_mask(ob, group, fn):
    """Vertex group weights from fn(x, y) -> 0..1 (world XY, before displacement)."""
    vg = ob.vertex_groups.get(group) or ob.vertex_groups.new(name=group)
    mw = ob.matrix_world
    for v in ob.data.vertices:
        p = mw @ v.co
        w = max(0.0, min(1.0, fn(p.x, p.y)))
        if w > 0:
            vg.add([v.index], w, 'REPLACE')
    return vg


def scatter(ground, coll, density=10.0, seed=0, scale=(0.8, 1.4), tilt=0.12, mask=None, name='scatter'):
    """Geometry-nodes scatter of a collection's meshes over ground (keeps the ground itself).
    density = instances per m2 at mask weight 1; mask = vertex group name (paint it with paint_mask)."""
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    N, L = ng.nodes, ng.links
    gi, go = N.new('NodeGroupInput'), N.new('NodeGroupOutput')
    dist = N.new('GeometryNodeDistributePointsOnFaces')
    dist.distribute_method = 'RANDOM'
    dist.inputs['Density'].default_value = density
    dist.inputs['Seed'].default_value = seed
    L.new(gi.outputs[0], dist.inputs['Mesh'])
    if mask:
        na = N.new('GeometryNodeInputNamedAttribute')
        na.data_type = 'FLOAT'
        na.inputs['Name'].default_value = mask
        mul = N.new('ShaderNodeMath')
        mul.operation = 'MULTIPLY'
        mul.inputs[1].default_value = density
        L.new(na.outputs['Attribute'], mul.inputs[0])
        L.new(mul.outputs[0], dist.inputs['Density'])
    ci = N.new('GeometryNodeCollectionInfo')
    ci.inputs['Collection'].default_value = coll
    ci.inputs['Separate Children'].default_value = True
    ci.inputs['Reset Children'].default_value = True
    iop = N.new('GeometryNodeInstanceOnPoints')
    L.new(dist.outputs['Points'], iop.inputs['Points'])
    L.new(ci.outputs[0], iop.inputs['Instance'])
    iop.inputs['Pick Instance'].default_value = True
    ri = N.new('FunctionNodeRandomValue')
    ri.data_type = 'INT'
    ri.inputs['Min'].default_value = 0
    ri.inputs['Max'].default_value = max(0, len(coll.objects) - 1)
    ri.inputs['Seed'].default_value = seed + 1
    L.new(ri.outputs['Value'], iop.inputs['Instance Index'])
    rr = N.new('FunctionNodeRandomValue')
    rr.data_type = 'FLOAT_VECTOR'
    rr.inputs['Min'].default_value = (-tilt, -tilt, 0)
    rr.inputs['Max'].default_value = (tilt, tilt, 6.283)
    rr.inputs['Seed'].default_value = seed + 2
    L.new(rr.outputs['Value'], iop.inputs['Rotation'])
    rs = N.new('FunctionNodeRandomValue')
    rs.data_type = 'FLOAT'
    rs.inputs['Min'].default_value = scale[0]
    rs.inputs['Max'].default_value = scale[1]
    rs.inputs['Seed'].default_value = seed + 3
    L.new(rs.outputs['Value'], iop.inputs['Scale'])
    j = N.new('GeometryNodeJoinGeometry')
    L.new(gi.outputs[0], j.inputs[0])
    L.new(iop.outputs[0], j.inputs[0])
    L.new(j.outputs[0], go.inputs[0])
    md = ground.modifiers.new(name, 'NODES')
    md.node_group = ng
    return md


def grass_material(name='grass_blades', base='#24500E', mid='#4F9A22', tip='#B9DC4A', tip2='#E2D870', translucency=0.35):
    """Lush stylised-real grass: dark root -> bright tip gradient along the blade (UV v), a per-clump colour
    shift, and back-lit translucency so the sun glows through the blades."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    out = N.new('ShaderNodeOutputMaterial')
    uv = N.new('ShaderNodeUVMap')
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(uv.outputs[0], sep.inputs[0])
    ramp = N.new('ShaderNodeValToRGB')
    cr = ramp.color_ramp
    cr.elements[0].position, cr.elements[0].color = 0.0, hexc(base)
    cr.elements[1].position, cr.elements[1].color = 1.0, hexc(tip)
    e = cr.elements.new(0.45)
    e.color = hexc(mid)
    L.new(sep.outputs['Y'], ramp.inputs[0])
    oi = N.new('ShaderNodeObjectInfo')
    mix = N.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mr = N.new('ShaderNodeMapRange')       # only some clumps get a dry/yellow tint
    mr.inputs['From Min'].default_value = 0.75
    mr.inputs['From Max'].default_value = 1.0
    mr.inputs['To Max'].default_value = 0.6
    L.new(oi.outputs['Random'], mr.inputs['Value'])
    L.new(mr.outputs[0], mix.inputs['Factor'])
    L.new(ramp.outputs[0], mix.inputs[6])
    mix.inputs[7].default_value = hexc(tip2)
    mix.blend_type = 'MIX'
    bsdf = N.new('ShaderNodeBsdfPrincipled')
    L.new(mix.outputs[2], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.55
    try:
        bsdf.inputs['Specular IOR Level'].default_value = 0.35
    except Exception:
        pass
    tr = N.new('ShaderNodeBsdfTranslucent')
    L.new(mix.outputs[2], tr.inputs['Color'])
    ms = N.new('ShaderNodeMixShader')
    ms.inputs[0].default_value = translucency
    L.new(bsdf.outputs[0], ms.inputs[1])
    L.new(tr.outputs[0], ms.inputs[2])
    L.new(ms.outputs[0], out.inputs['Surface'])
    m.use_backface_culling = False
    return m


def grass_clumps(name='grass_clumps', variants=8, blades=36, h=(0.12, 0.32), spread=0.09, seed=1,
                 mat=None, flowers=0.0, flower_cols=('#FFE04A', '#FFFFFF', '#FF9BD0')):
    """Hidden collection of procedural grass clumps (tapered, curved blades). Scatter it with scatter().
    flowers = chance per clump of a few small flower heads."""
    import random
    rnd = random.Random(seed)
    mat = mat or grass_material()
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    fmats = [emissive(f'flower{i}', c, 0.15) for i, c in enumerate(flower_cols)] if flowers else []
    for vi in range(variants):
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new()
        for b in range(blades):
            r = spread * math.sqrt(rnd.random())
            a0 = rnd.random() * 6.283
            bx, by = r * math.cos(a0), r * math.sin(a0)
            hh = rnd.uniform(*h)
            w = rnd.uniform(0.008, 0.016)
            lean = rnd.uniform(0.15, 0.55) * hh             # how far the tip bends over
            ld = rnd.random() * 6.283
            face_a = rnd.random() * 6.283
            ox, oy = math.cos(face_a) * w, math.sin(face_a) * w
            segs = 4
            rows = []
            for s in range(segs + 1):
                t = s / segs
                cx = bx + math.cos(ld) * lean * t * t
                cy = by + math.sin(ld) * lean * t * t
                cz = hh * t * (1 - 0.18 * t * t)
                k = 1 - t * 0.92
                rows.append((bm.verts.new((cx - ox * k, cy - oy * k, cz)), bm.verts.new((cx + ox * k, cy + oy * k, cz)), t))
            for (a1, b1, t1), (a2, b2, t2) in zip(rows, rows[1:]):
                f = bm.faces.new((a1, b1, b2, a2))
                for lp, uvc in zip(f.loops, ((0, t1), (1, t1), (1, t2), (0, t2))):
                    lp[uvl].uv = uvc
        fm = None
        if fmats and rnd.random() < flowers:
            from mathutils import Matrix
            fm = rnd.choice(fmats)
            for k in range(rnd.randint(1, 3)):
                loc = (rnd.uniform(-spread, spread), rnd.uniform(-spread, spread), rnd.uniform(h[0], h[1]) * 1.05)
                res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=rnd.uniform(0.012, 0.02),
                                                 matrix=Matrix.Translation(loc) @ Matrix.Diagonal((1, 1, 0.6, 1)))
                vs = set(res['verts'])
                for f in bm.faces:
                    if all(v in vs for v in f.verts):
                        f.material_index = 1
        me = bpy.data.meshes.new(f'{name}_{vi}')
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        me.materials.append(mat)
        if fm:
            me.materials.append(fm)
        ob = bpy.data.objects.new(f'{name}_{vi}', me)
        coll.objects.link(ob)
    lc = bpy.context.view_layer.layer_collection.children.get(coll.name)
    if lc:
        lc.exclude = True
    return coll
