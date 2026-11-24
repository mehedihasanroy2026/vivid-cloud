"""VIVID look (from EP11 v2): the Ricks Clips 2026 look, measured on 20 of his Shorts.

What his frames measure (mean of 20 videos)  vs  our EP06-11:
    brightness 0.46  (ours 0.31-0.40)       shadows p5 0.17 (ours 0.08)  -> lifted, tinted shadows
    saturation 0.45  (ours 0.32-0.40)       colourfulness 0.29 (ours 0.14-0.17)
    camera motion 3x ours, 0-1 hard cuts: shots change every ~2-3 s through 6-9 frame dissolves / fly-throughs

What it looks like:
  * painted gradient skies with clouds and a glowing sun on every outdoor shot (never a flat grey sky)
  * complementary colour pairs on every set: teal + red, yellow + purple, orange + blue. No grey rooms.
  * patterned surfaces: wallpaper, checker floors, rugs, planks, gravel, grass
  * bright, soft light; shadows lifted and tinted blue/violet, warm highlights, bloom glow
  * characters outlined everywhere (head, body, gloves) and kept bright white

    import vivid as V
    V.setup(pct, samples)                         # replaces real.setup
    V.sky('day')                                  # world = painted sky + coloured ambient
    m = V.pat('Floor', '#2BA3A0', '#F4EEDC', 'checker', scale=0.5, mode='floor')
    V.grade()                                     # replaces real.finish (call after all objects exist)
"""
import math
import bpy
import real
from toon import hexcol, _mats

VIEW = 'AgX'
LOOK = 'AgX - Punchy'


def setup(pct=50, samples=8, exposure=0.0):
    real.setup(pct, samples, sky='#8FB8E8', sky_strength=1.0, exposure=exposure)
    sc = bpy.context.scene
    sc.view_settings.view_transform = VIEW
    try:
        sc.view_settings.look = LOOK
    except Exception:
        pass
    sc.eevee.fast_gi_distance = 6.0
    return sc


def _n(N, t, **kw):
    n = N.new(t)
    for k, v in kw.items():
        if k in n.inputs:
            n.inputs[k].default_value = v
        else:
            setattr(n, k, v)
    return n


def _inp(node, name, kind=None):
    for i in node.inputs:
        if i.name == name and (kind is None or i.type == kind):
            return i
    raise KeyError(name)


# ---------------------------------------------------------------- painted sky
SKIES = {
    #          zenith     mid        horizon    sun col    clouds   amb col    amb   sun(elev, az) stars
    'day':    ('#2D6BD8', '#62A3F0', '#CFE7FA', '#FFF4D6', 0.55, '#9CC4F2', 0.9, (35, 30), 0),
    'golden': ('#3D5DC2', '#8FA6E6', '#FFD9A0', '#FFC27A', 0.5, '#C9B8E8', 0.85, (14, 25), 0),
    'sunset': ('#33307E', '#C8579A', '#FFB45E', '#FFB050', 0.45, '#B48AC8', 0.8, (5, 15), 0),
    'night':  ('#0A1038', '#1E2C7A', '#4A55B0', '#DDE6FF', 0.25, '#4B5CC0', 0.65, (30, -30), 1),
    'indoor': ('#7FA4D8', '#AFC8EC', '#F2E3CC', '#FFF0D8', 0.0, '#A9BEE0', 0.75, (40, 0), 0),
    'ocean':  ('#0B3F7A', '#1A8FB8', '#3FD0D8', '#CFF6FF', 0.0, '#3FA8D0', 0.9, (70, 0), 0),
    'body':   ('#C2185B', '#F27A8A', '#FFD0DA', '#FFE6EE', 0.0, '#FFB0C0', 0.8, (40, 0), 0),
    'neon':   ('#140A3A', '#3A1A7A', '#7A3AB8', '#FF7AD8', 0.0, '#7A5AD0', 0.6, (20, 0), 1),
}


def sky(preset='day', strength=1.0, ambient=None, sun_dir=None, clouds=None, seed=0.0):
    """World = painted gradient sky (what the camera sees) + flat coloured ambient (what lights the set).
    The ambient is what lifts and tints the shadows like Ricks' frames."""
    z, m_, h, sc_, cl, amb, ambs, (el, az), stars = SKIES[preset]
    if ambient is not None:
        ambs = ambient
    if sun_dir is not None:
        el, az = sun_dir
    if clouds is not None:
        cl = clouds
    w = bpy.context.scene.world
    w.use_nodes = True
    N, L = w.node_tree.nodes, w.node_tree.links
    N.clear()
    out = N.new('ShaderNodeOutputWorld')
    tc = N.new('ShaderNodeTexCoord')
    d = N.new('ShaderNodeVectorMath')
    d.operation = 'NORMALIZE'
    L.new(tc.outputs['Generated'], d.inputs[0])
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(d.outputs[0], sep.inputs[0])
    # vertical gradient
    rmp = N.new('ShaderNodeValToRGB')
    e = rmp.color_ramp.elements
    e[0].position, e[0].color = 0.0, hexcol(h)
    e[1].position, e[1].color = 0.55, hexcol(z)
    mid = e.new(0.16)
    mid.color = hexcol(m_)
    below = N.new('ShaderNodeMath')
    below.operation = 'MAXIMUM'
    L.new(sep.outputs['Z'], below.inputs[0])
    below.inputs[1].default_value = 0.0
    L.new(below.outputs[0], rmp.inputs[0])
    col = rmp.outputs[0]
    # clouds: soft noise blobs projected on a flat sky plane
    if cl > 0:
        dz = _n(N, 'ShaderNodeMath', operation='ADD')
        L.new(sep.outputs['Z'], dz.inputs[0])
        dz.inputs[1].default_value = 0.12
        u = _n(N, 'ShaderNodeMath', operation='DIVIDE')
        L.new(sep.outputs['X'], u.inputs[0])
        L.new(dz.outputs[0], u.inputs[1])
        v = _n(N, 'ShaderNodeMath', operation='DIVIDE')
        L.new(sep.outputs['Y'], v.inputs[0])
        L.new(dz.outputs[0], v.inputs[1])
        cxy = N.new('ShaderNodeCombineXYZ')
        L.new(u.outputs[0], cxy.inputs['X'])
        vv = _n(N, 'ShaderNodeMath', operation='MULTIPLY')
        L.new(v.outputs[0], vv.inputs[0])
        vv.inputs[1].default_value = 2.2
        L.new(vv.outputs[0], cxy.inputs['Y'])
        cxy.inputs['Z'].default_value = seed
        nz = _n(N, 'ShaderNodeTexNoise', Scale=0.9, Detail=5.0, Roughness=0.55)
        L.new(cxy.outputs[0], nz.inputs['Vector'])
        rr = _n(N, 'ShaderNodeMapRange', **{'From Min': 0.62 - 0.12 * cl, 'From Max': 0.72 - 0.1 * cl})
        L.new(nz.outputs['Fac'], rr.inputs['Value'])
        # fade clouds out near the horizon and below it
        fade = _n(N, 'ShaderNodeMapRange', **{'From Min': 0.02, 'From Max': 0.2})
        L.new(sep.outputs['Z'], fade.inputs['Value'])
        mask = _n(N, 'ShaderNodeMath', operation='MULTIPLY')
        L.new(rr.outputs[0], mask.inputs[0])
        L.new(fade.outputs[0], mask.inputs[1])
        # cloud shading: warm-white tops, lavender undersides (second noise offset)
        nz2 = _n(N, 'ShaderNodeTexNoise', Scale=0.9, Detail=5.0, Roughness=0.55)
        off = _n(N, 'ShaderNodeVectorMath', operation='ADD')
        L.new(cxy.outputs[0], off.inputs[0])
        off.inputs[1].default_value = (0.0, -0.08, 0.0)
        L.new(off.outputs[0], nz2.inputs['Vector'])
        shade = _n(N, 'ShaderNodeMapRange', **{'From Min': 0.55, 'From Max': 0.75})
        L.new(nz2.outputs['Fac'], shade.inputs['Value'])
        cmix = _n(N, 'ShaderNodeMix', data_type='RGBA')
        L.new(shade.outputs[0], cmix.inputs[0])
        cmix.inputs[6].default_value = tuple(min(1, c * 1.1) for c in hexcol(sc_)[:3]) + (1,)
        cmix.inputs[7].default_value = tuple(0.5 * a + 0.5 * b for a, b in zip(hexcol(m_)[:3], (0.85, 0.82, 0.95))) + (1,)
        mx = _n(N, 'ShaderNodeMix', data_type='RGBA')
        L.new(mask.outputs[0], mx.inputs[0])
        L.new(col, mx.inputs[6])
        L.new(cmix.outputs[2], mx.inputs[7])
        col = mx.outputs[2]
    # stars
    if stars:
        vo = _n(N, 'ShaderNodeTexVoronoi', Scale=180.0)
        L.new(d.outputs[0], vo.inputs['Vector'])
        st = _n(N, 'ShaderNodeMapRange', **{'From Min': 0.06, 'From Max': 0.0})
        L.new(vo.outputs['Distance'], st.inputs['Value'])
        up = _n(N, 'ShaderNodeMath', operation='MULTIPLY')
        L.new(st.outputs[0], up.inputs[0])
        L.new(below.outputs[0], up.inputs[1])
        add = _n(N, 'ShaderNodeMix', data_type='RGBA', blend_type='ADD')
        L.new(up.outputs[0], add.inputs[0])
        L.new(col, add.inputs[6])
        add.inputs[7].default_value = (1, 1, 1, 1)
        col = add.outputs[2]
    # sun glow: tight disc + wide warm halo
    sv = (math.cos(math.radians(el)) * math.sin(math.radians(az)), math.cos(math.radians(el)) * math.cos(math.radians(az)),
          math.sin(math.radians(el)))
    dot = _n(N, 'ShaderNodeVectorMath', operation='DOT_PRODUCT')
    L.new(d.outputs[0], dot.inputs[0])
    dot.inputs[1].default_value = sv
    for lo, hi, amt in ((0.996, 0.999, 3.0), (0.75, 1.0, 0.55)):
        g = _n(N, 'ShaderNodeMapRange', **{'From Min': lo, 'From Max': hi, 'To Max': amt})
        g.interpolation_type = 'SMOOTHSTEP'
        L.new(dot.outputs['Value'], g.inputs['Value'])
        add = _n(N, 'ShaderNodeMix', data_type='RGBA', blend_type='ADD')
        L.new(g.outputs[0], add.inputs[0])
        L.new(col, add.inputs[6])
        add.inputs[7].default_value = hexcol(sc_)
        col = add.outputs[2]
    painted = _n(N, 'ShaderNodeBackground', Strength=strength)
    L.new(col, painted.inputs['Color'])
    ambient_bg = _n(N, 'ShaderNodeBackground', Strength=ambs)
    ambient_bg.inputs['Color'].default_value = hexcol(amb)
    lp = N.new('ShaderNodeLightPath')
    mix = N.new('ShaderNodeMixShader')
    L.new(lp.outputs['Is Camera Ray'], mix.inputs[0])
    L.new(ambient_bg.outputs[0], mix.inputs[1])
    L.new(painted.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], out.inputs['Surface'])
    return sv


def sun_rot(el, az):
    """real.sun rotation that shines FROM the sky direction (el, az) used by sky()"""
    return (90 - el, 0, 180 - az)


# ---------------------------------------------------------------- patterned materials
def pat(name, c1, c2='#FFFFFF', kind='checker', scale=1.0, mode='box', rough=0.6, bump=0.1, c3=None, grime=0.12):
    """Ricks-style painted pattern surfaces.
    kind: checker | stripes | dots | wallpaper | planks | rug | grass | gravel | bricks | shingles | wavy"""
    key = f'V_{name}'
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    out = N.new('ShaderNodeOutputMaterial')
    b = N.new('ShaderNodeBsdfPrincipled')
    L.new(b.outputs[0], out.inputs['Surface'])
    b.inputs['Roughness'].default_value = rough
    if 'Specular IOR Level' in b.inputs:
        b.inputs['Specular IOR Level'].default_value = 0.25
    uv = real._coords(N, L, mode, scale)
    A, B = hexcol(c1), hexcol(c2)
    C = hexcol(c3) if c3 else B
    col, height = None, None
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(uv, sep.inputs[0])
    if kind == 'checker':
        ck = _n(N, 'ShaderNodeTexChecker', Scale=1.0)
        L.new(uv, ck.inputs['Vector'])
        ck.inputs['Color1'].default_value = A
        ck.inputs['Color2'].default_value = B
        col = ck.outputs['Color']
        height = ck.outputs['Fac']
    elif kind in ('stripes', 'wallpaper'):
        wv = _n(N, 'ShaderNodeTexWave', Scale=1.0, Distortion=0.0)
        wv.wave_profile = 'SAW' if kind == 'stripes' else 'SIN'
        wv.bands_direction = 'X'
        L.new(uv, wv.inputs['Vector'])
        rr = _n(N, 'ShaderNodeMapRange', **{'From Min': 0.48, 'From Max': 0.52})
        L.new(wv.outputs['Fac'], rr.inputs['Value'])
        mx = _n(N, 'ShaderNodeMix', data_type='RGBA')
        L.new(rr.outputs[0], mx.inputs[0])
        mx.inputs[6].default_value = A
        mx.inputs[7].default_value = B
        col = mx.outputs[2]
        if kind == 'wallpaper':
            # small motif dots between the stripes
            vo = _n(N, 'ShaderNodeTexVoronoi', Scale=3.0)
            vo.feature = 'F1'
            vo.inputs['Randomness'].default_value = 0.0
            L.new(uv, vo.inputs['Vector'])
            dt = _n(N, 'ShaderNodeMapRange', **{'From Min': 0.12, 'From Max': 0.08})
            L.new(vo.outputs['Distance'], dt.inputs['Value'])
            mx2 = _n(N, 'ShaderNodeMix', data_type='RGBA')
            L.new(dt.outputs[0], mx2.inputs[0])
            L.new(col, mx2.inputs[6])
            mx2.inputs[7].default_value = C
            col = mx2.outputs[2]
    elif kind == 'dots':
        vo = _n(N, 'ShaderNodeTexVoronoi', Scale=1.0)
        vo.inputs['Randomness'].default_value = 0.0
        L.new(uv, vo.inputs['Vector'])
        dt = _n(N, 'ShaderNodeMapRange', **{'From Min': 0.22, 'From Max': 0.18})
        L.new(vo.outputs['Distance'], dt.inputs['Value'])
        mx = _n(N, 'ShaderNodeMix', data_type='RGBA')
        L.new(dt.outputs[0], mx.inputs[0])
        mx.inputs[6].default_value = A
        mx.inputs[7].default_value = B
        col = mx.outputs[2]
    elif kind in ('planks', 'shingles', 'bricks'):
        bw, bh = {'planks': (2.2, 0.28), 'shingles': (0.5, 0.35), 'bricks': (0.5, 0.22)}[kind]
        br = _n(N, 'ShaderNodeTexBrick', Scale=1.0, **{'Mortar Size': 0.012, 'Brick Width': bw, 'Row Height': bh,
                                                         'Mortar Smooth': 0.2, 'Bias': 0.0})
        br.offset = 0.37 if kind == 'planks' else 0.5
        br.inputs['Color1'].default_value = A
        br.inputs['Color2'].default_value = tuple(0.82 * a + 0.18 * c for a, c in zip(A[:3], B[:3])) + (1,)
        br.inputs['Mortar'].default_value = tuple(c * 0.45 for c in A[:3]) + (1,)
        L.new(uv, br.inputs['Vector'])
        col = br.outputs['Color']
        height = br.outputs['Fac']
        if kind == 'planks':
            wv = _n(N, 'ShaderNodeTexWave', Scale=1.5, Distortion=6.0, Detail=2.0)
            wv.bands_direction = 'Y'
            mp = _n(N, 'ShaderNodeMapping')
            mp.inputs['Scale'].default_value = (0.3, 4.0, 1.0)
            L.new(uv, mp.inputs['Vector'])
            L.new(mp.outputs[0], wv.inputs['Vector'])
            gr = _n(N, 'ShaderNodeMapRange', **{'To Min': 0.0, 'To Max': 0.18})
            L.new(wv.outputs['Fac'], gr.inputs['Value'])
            mx = _n(N, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
            L.new(gr.outputs[0], mx.inputs[0])
            L.new(col, mx.inputs[6])
            mx.inputs[7].default_value = tuple(c * 0.6 for c in A[:3]) + (1,)
            col = mx.outputs[2]
    elif kind in ('rug', 'grass', 'gravel'):
        sc = {'rug': 120.0, 'grass': 40.0, 'gravel': 9.0}[kind]
        if kind == 'gravel':
            vo = _n(N, 'ShaderNodeTexVoronoi', Scale=sc)
            L.new(uv, vo.inputs['Vector'])
            mx = _n(N, 'ShaderNodeMix', data_type='RGBA')
            L.new(vo.outputs['Color'], mx.inputs[0])   # random per stone
            fac = vo.outputs['Distance']
        else:
            nz = _n(N, 'ShaderNodeTexNoise', Scale=sc, Detail=3.0)
            L.new(uv, nz.inputs['Vector'])
            mx = _n(N, 'ShaderNodeMix', data_type='RGBA')
            L.new(nz.outputs['Fac'], mx.inputs[0])
            fac = nz.outputs['Fac']
        mx.inputs[6].default_value = A
        mx.inputs[7].default_value = B
        col = mx.outputs[2]
        height = fac
        # big soft colour variation patches
        nz2 = _n(N, 'ShaderNodeTexNoise', Scale=0.25, Detail=2.0)
        L.new(uv, nz2.inputs['Vector'])
        mx2 = _n(N, 'ShaderNodeMix', data_type='RGBA')
        rr = _n(N, 'ShaderNodeMapRange', **{'From Min': 0.35, 'From Max': 0.65, 'To Max': 0.45})
        L.new(nz2.outputs['Fac'], rr.inputs['Value'])
        L.new(rr.outputs[0], mx2.inputs[0])
        L.new(col, mx2.inputs[6])
        mx2.inputs[7].default_value = C
        col = mx2.outputs[2]
    elif kind == 'wavy':
        wv = _n(N, 'ShaderNodeTexWave', Scale=1.0, Distortion=4.0, Detail=3.0)
        L.new(uv, wv.inputs['Vector'])
        mx = _n(N, 'ShaderNodeMix', data_type='RGBA')
        L.new(wv.outputs['Fac'], mx.inputs[0])
        mx.inputs[6].default_value = A
        mx.inputs[7].default_value = B
        col = mx.outputs[2]
        height = wv.outputs['Fac']
    if grime:
        nz = _n(N, 'ShaderNodeTexNoise', Scale=1.4, Detail=4.0)
        L.new(uv, nz.inputs['Vector'])
        rr = _n(N, 'ShaderNodeMapRange', **{'From Min': 0.45, 'From Max': 0.75, 'To Max': grime})
        L.new(nz.outputs['Fac'], rr.inputs['Value'])
        mx = _n(N, 'ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
        L.new(rr.outputs[0], mx.inputs[0])
        L.new(col, mx.inputs[6])
        mx.inputs[7].default_value = (0.6, 0.58, 0.68, 1)
        col = mx.outputs[2]
    L.new(col, b.inputs['Base Color'])
    if height is not None and bump:
        bp = _n(N, 'ShaderNodeBump', Strength=bump, Distance=0.02)
        L.new(height, bp.inputs['Height'])
        L.new(bp.outputs[0], b.inputs['Normal'])
    m.diffuse_color = A
    _mats[key] = m
    return m


def paint(name, hexc, rough=0.55, grime=0.1, kind='paint', **kw):
    """plain saturated painted surface (real.mat with lighter grime)"""
    return real.mat(name, hexc, kind, grime=grime, rough=rough, **kw)


# ---------------------------------------------------------------- characters
def ink_chars(rig, body=0.075, glow=0.4):
    """Thicker body outlines (like the head) + bright self-light so the doodles pop off colourful sets."""
    for ob in [rig['mover']] + list(rig['mover'].children_recursive):
        for md in getattr(ob, 'modifiers', []):
            if md.type == 'SOLIDIFY' and md.name == 'Outline' and ob.name.endswith('_torso'):
                md.thickness = body
    real.glow_chars(rig, glow)


# ---------------------------------------------------------------- grade
def grade(bloom=0.6, sat=1.12, lift=(0.035, 0.03, 0.075), gain=(1.04, 1.0, 0.95), vignette=0.18, glow=0.25,
          contrast=4.0):
    """Ricks-style finish: bloom + soft glow, lifted violet-blue shadows, warm highlights, extra colour, light vignette."""
    sc = bpy.context.scene
    ng = bpy.data.node_groups.new('VividLook', 'CompositorNodeTree')
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
        g.inputs['Threshold'].default_value = 0.8
        g.inputs['Strength'].default_value = bloom
        g.inputs['Size'].default_value = 0.75
        L.new(img, g.inputs['Image'])
        img = g.outputs['Image']
    if glow:
        # wide, low soft diffusion over everything (the dreamy glow in his skies and windows)
        g2 = N.new('CompositorNodeGlare')
        g2.inputs['Type'].default_value = 'Fog Glow'
        g2.inputs['Threshold'].default_value = 0.55
        g2.inputs['Strength'].default_value = glow
        g2.inputs['Size'].default_value = 0.8
        L.new(img, g2.inputs['Image'])
        img = g2.outputs['Image']
    # lift shadows towards violet-blue (additive, strongest in the darks), warm gain on highlights
    lum = N.new('CompositorNodeRGBToBW')
    L.new(img, lum.inputs[0])
    inv = N.new('ShaderNodeMath')
    inv.operation = 'POWER'
    one_minus = N.new('ShaderNodeMath')
    one_minus.operation = 'SUBTRACT'
    one_minus.inputs[0].default_value = 1.0
    L.new(lum.outputs[0], one_minus.inputs[1])
    L.new(one_minus.outputs[0], inv.inputs[0])
    inv.inputs[1].default_value = contrast * 0.5     # how fast the lift fades out towards the mids
    mx = N.new('ShaderNodeMix')
    mx.data_type = 'RGBA'
    mx.blend_type = 'ADD'
    L.new(inv.outputs[0], mx.inputs[0])
    L.new(img, mx.inputs[6])
    mx.inputs[7].default_value = lift + (1,)
    img = mx.outputs[2]
    mul = N.new('ShaderNodeMix')
    mul.data_type = 'RGBA'
    mul.blend_type = 'MULTIPLY'
    mul.inputs[0].default_value = 1.0
    L.new(img, mul.inputs[6])
    mul.inputs[7].default_value = gain + (1,)
    img = mul.outputs[2]
    if sat != 1.0:
        hs = N.new('CompositorNodeHueSat')
        hs.inputs['Saturation'].default_value = sat
        L.new(img, hs.inputs['Image'])
        img = hs.outputs[0]
    if vignette:
        ell = N.new('CompositorNodeEllipseMask')
        ell.inputs['Size'].default_value = (1.0, 0.95)
        bl = N.new('CompositorNodeBlur')
        if 'Size' in bl.inputs:
            bl.inputs['Size'].default_value = (160, 160)
        L.new(ell.outputs[0], bl.inputs['Image'])
        v = N.new('ShaderNodeMath')
        v.operation = 'SUBTRACT'
        v.inputs[0].default_value = 1.0
        L.new(bl.outputs[0], v.inputs[1])
        vm = N.new('ShaderNodeMath')
        vm.operation = 'MULTIPLY'
        vm.inputs[1].default_value = vignette
        L.new(v.outputs[0], vm.inputs[0])
        mv = N.new('ShaderNodeMix')
        mv.data_type = 'RGBA'
        mv.blend_type = 'MULTIPLY'
        L.new(vm.outputs[0], mv.inputs[0])
        L.new(img, mv.inputs[6])
        mv.inputs[7].default_value = (0.25, 0.2, 0.42, 1)    # violet edges, not black
        img = mv.outputs[2]
    L.new(img, out.inputs[0])
    return ng


# ---------------------------------------------------------------- assets
_tints = {}


def _tinted(mat, tint, amt):
    key = (mat.name, tint, amt)
    if key in _tints:
        return _tints[key]
    m = mat.copy()
    m.name = f'{mat.name}_x{tint}'
    N, L = m.node_tree.nodes, m.node_tree.links
    b = next((n for n in N if n.type == 'BSDF_PRINCIPLED'), None)
    if b:
        bc = b.inputs['Base Color']
        mx = N.new('ShaderNodeMix')
        mx.data_type = 'RGBA'
        mx.blend_type = 'MULTIPLY'
        mx.inputs[0].default_value = amt
        if bc.is_linked:
            L.new(bc.links[0].from_socket, mx.inputs[6])
        else:
            mx.inputs[6].default_value = bc.default_value
        mx.inputs[7].default_value = hexcol(tint)
        L.new(mx.outputs[2], bc)
    _tints[key] = m
    return m


def load(pack, name, loc=(0, 0, 0), size=1.0, rot=(0, 0, 0), tint=None, amt=1.0, center=True, parent=None):
    """Kenney model at `size` x its native units (our characters are ~6 units tall: a car ~ size 5.9).
    tint MULTIPLIES the model's own texture (white walls take the colour, windows and details stay)."""
    import assets
    root = assets.load(pack, name, loc=loc, scale=size / assets.SCALE, rot=rot, center=center, parent=parent)
    if tint:
        for o in root.children:
            o.data = o.data  # linked mesh stays shared; materials go on the object slots
            for sl in o.material_slots:
                if sl.material:
                    m = _tinted(sl.material, tint, amt)
                    sl.link = 'OBJECT'
                    sl.material = m
    return root


# ---------------------------------------------------------------- puffy painted trees (Ricks' round cartoon trees)
def _leaf(hexc):
    key = f'V_Leaf{hexc}'
    if key in _mats:
        return _mats[key]
    m = real.mat('Leaf' + hexc, hexc, 'paint', grime=0.0, rough=0.75)
    N, L = m.node_tree.nodes, m.node_tree.links
    b = next(n for n in N if n.type == 'BSDF_PRINCIPLED')
    # light tops, darker undersides: mix on the normal's Z + soft noise blotches
    geo = N.new('ShaderNodeNewGeometry')
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(geo.outputs['Normal'], sep.inputs[0])
    rr = _n(N, 'ShaderNodeMapRange', **{'From Min': -0.6, 'From Max': 0.9})
    L.new(sep.outputs['Z'], rr.inputs['Value'])
    nz = _n(N, 'ShaderNodeTexNoise', Scale=2.5, Detail=3.0)
    add = _n(N, 'ShaderNodeMath', operation='MULTIPLY_ADD')
    L.new(nz.outputs['Fac'], add.inputs[0])
    add.inputs[1].default_value = 0.35
    L.new(rr.outputs[0], add.inputs[2])
    ramp = N.new('ShaderNodeValToRGB')
    c = hexcol(hexc)
    ramp.color_ramp.elements[0].color = tuple(x * 0.55 for x in c[:3]) + (1,)
    ramp.color_ramp.elements[1].color = tuple(min(1, x * 1.25 + 0.04) for x in c[:3]) + (1,)
    L.new(add.outputs[0], ramp.inputs[0])
    L.new(ramp.outputs[0], b.inputs['Base Color'])
    _mats[key] = m
    return m


def puff_tree(name, loc, h=7.0, col='#5DBB4A', trunk='#8A5A3C', seed=0, parent=None):
    import random
    from toon import empty, ellipsoid, tube
    r = random.Random(seed)
    root = empty(name, loc, parent)
    tm = real.mat('Trunk' + trunk, trunk, 'wood', grime=0.1)
    tube(name + 'Trunk', [(0, 0, 0), (0.1, 0, h * 0.35), (-0.05, 0.05, h * 0.62)], h * 0.045, tm, root, outline=0.04)
    lm = _leaf(col)
    R = h * 0.26
    for i in range(7):
        a = i * 2.39 + r.random()
        rad = R * (0.75 + 0.35 * r.random())
        d = R * (0.0 if i == 0 else 0.75)
        z = h * 0.66 + (0 if i == 0 else (r.random() - 0.3) * R * 0.9)
        ellipsoid(f'{name}Leaf{i}', (rad, rad, rad * 0.9), (d * math.cos(a), d * math.sin(a), z), lm, root, outline=0.05, segs=24, rings=12)
    return root


def puff_bush(name, loc, s=1.0, col='#4FA83F', seed=0, parent=None):
    import random
    from toon import empty, ellipsoid
    r = random.Random(seed)
    root = empty(name, loc, parent)
    lm = _leaf(col)
    for i in range(4):
        a = i * 1.9 + r.random()
        ellipsoid(f'{name}B{i}', (s * (0.8 + 0.3 * r.random()),) * 2 + (s * 0.75,), (s * 0.7 * math.cos(a) * (i > 0), s * 0.7 * math.sin(a) * (i > 0), s * 0.5),
                  lm, root, outline=0.04, segs=20, rings=10)
    return root
