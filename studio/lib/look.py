"""'Pro look' finishing pass, modelled on the Ricks Clips style.

Call pro_look() once, after every object is built:
  * ink lines on every object edge, fold and depth jump (compositor, cheap; no Freestyle)
  * soft bloom on bright things (lamps, screens, windows)
  * cooler, darker ambient fill so lamps and the key light shape the scene
  * a small saturation lift

    from look import pro_look
    pro_look(pct=args.pct)
"""
import math
import bpy
from toon import hexcol, LINE_HEX


def _index_objects(sc):
    """Give every visible thing its own pass index so the ink pass can find object edges."""
    i = 1
    for ob in sc.objects:
        if ob.type in ('MESH', 'CURVE', 'FONT', 'SURFACE', 'META'):
            ob.pass_index = i
            i += 1
    # EEVEE has no object-index pass, so every material writes it into an AOV
    for m in bpy.data.materials:
        if not m.use_nodes or m.node_tree.nodes.get('OID_AOV'):
            continue
        N, L = m.node_tree.nodes, m.node_tree.links
        info = N.new('ShaderNodeObjectInfo')
        aov = N.new('ShaderNodeOutputAOV')
        aov.name = 'OID_AOV'
        aov.aov_name = 'oid'
        L.new(info.outputs['Object Index'], aov.inputs['Value'])


def pro_look(pct=50, ink=True, ink_hex=LINE_HEX, ink_strength=0.92, line_px=None,
             normal_edge=0.55, depth_edge=0.06, bloom=0.35, saturation=1.12,
             ambient_hex=None, ambient=None, backdrop_hex='#2B2A45',
             key_sun=True, sun_rot=(52, 8, -38), sun_hex='#FFE2B0', sun_strength=2.2, fill_scale=0.7, ao=True, motion_blur=False, haze=None):
    """haze=(hex, start, end, amount): far things fade into this colour (atmospheric depth)."""
    sc = bpy.context.scene
    if motion_blur:      # Ricks-style smeared fast moves / whip pans
        sc.render.use_motion_blur = True
        sc.render.motion_blur_shutter = 0.6
    if ao:      # soft darkening in corners / under things (~1 s per frame extra)
        sc.eevee.use_raytracing = True
        sc.eevee.ray_tracing_method = 'PROBE'
        sc.eevee.use_fast_gi = True
        sc.eevee.fast_gi_method = 'GLOBAL_ILLUMINATION'
        sc.eevee.fast_gi_distance = 3.0
    # big soft area lights give shadow acne (triangle speckle) -> shadowless fill only;
    # one sun casts the crisp shadows instead
    for ob in sc.objects:
        if ob.type == 'LIGHT':
            ld = ob.data
            ld.shadow_filter_radius = 2.0
            if ld.type == 'AREA' and max(ld.size, getattr(ld, 'size_y', 0)) > 3:
                ld.use_shadow = False
                if key_sun:
                    ld.energy *= fill_scale
    if key_sun:
        sd = bpy.data.lights.new('KeySun', 'SUN')
        sd.energy = sun_strength
        sd.color = hexcol(sun_hex)[:3]
        sd.angle = math.radians(3)
        sd.shadow_filter_radius = 2.0
        so = bpy.data.objects.new('KeySun', sd)
        so.rotation_euler = [math.radians(a) for a in sun_rot]
        for c in sc.collection.children:      # sets live in their own collections: add to each
            c.objects.link(so)
        if not sc.collection.children:
            sc.collection.objects.link(so)
    vl = sc.view_layers[0]
    vl.use_pass_z = True
    vl.use_pass_normal = True
    if 'oid' not in vl.aovs:
        a = vl.aovs.add()
        a.name, a.type = 'oid', 'VALUE'
    _index_objects(sc)

    if ambient_hex or ambient is not None:
        bg = sc.world.node_tree.nodes.get('Background')
        if ambient_hex:
            bg.inputs[0].default_value = hexcol(ambient_hex)
        if ambient is not None:
            bg.inputs[1].default_value = ambient
    if backdrop_hex:      # what the camera sees in empty space (never the ambient colour)
        W, WL = sc.world.node_tree.nodes, sc.world.node_tree.links
        bg = W.get('Background')
        wout = W.get('World Output')
        lp = W.new('ShaderNodeLightPath')
        bd = W.new('ShaderNodeBackground')
        bd.inputs[0].default_value = hexcol(backdrop_hex)
        mx = W.new('ShaderNodeMixShader')
        WL.new(lp.outputs['Is Camera Ray'], mx.inputs[0])
        WL.new(bg.outputs[0], mx.inputs[1])
        WL.new(bd.outputs[0], mx.inputs[2])
        WL.new(mx.outputs[0], wout.inputs['Surface'])

    ng = bpy.data.node_groups.new('ProLook', 'CompositorNodeTree')
    ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    sc.compositing_node_group = ng
    N, L = ng.nodes, ng.links
    rl = N.new('CompositorNodeRLayers')
    rl.scene = sc
    out = N.new('NodeGroupOutput')

    def mop(op, a, b=None, clamp=False):
        m = N.new('ShaderNodeMath')
        m.operation = op
        m.use_clamp = clamp
        for k, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[k].default_value = v
            else:
                L.new(v, m.inputs[k])
        return m.outputs[0]

    def sobel(sock):
        f = N.new('CompositorNodeFilter')
        f.inputs['Type'].default_value = 'Sobel'
        L.new(sock, f.inputs['Image'])
        return f.outputs[0]

    def luma(col):
        """Any colour/vector -> one value (sum of channels)."""
        sep = N.new('CompositorNodeSeparateColor')
        L.new(col, sep.inputs[0])
        return mop('ADD', mop('ADD', sep.outputs[0], sep.outputs[1]), sep.outputs[2])

    img = rl.outputs['Image']
    if ink:
        # 1) object edges: object index changes
        e_obj = mop('GREATER_THAN', luma(sobel(rl.outputs['oid'])), 0.5)
        # 2) folds: surface normal changes sharply (box corners, wall/floor joins)
        e_nrm = mop('GREATER_THAN', luma(sobel(rl.outputs['Normal'])), normal_edge * 3)
        # 3) depth jumps relative to distance (overlapping parts of one object)
        dz = mop('DIVIDE', luma(sobel(rl.outputs['Depth'])), mop('MULTIPLY', rl.outputs['Depth'], 3.0))
        e_dep = mop('GREATER_THAN', dz, depth_edge)
        edge = mop('MAXIMUM', mop('MAXIMUM', e_obj, e_nrm), e_dep)
        # thicken for the render size (lines ~3 px at 1080 wide), then soften
        px = line_px if line_px is not None else max(0, round(pct / 50) - 1)
        if px:
            d = N.new('CompositorNodeDilateErode')
            d.inputs['Size'].default_value = px
            L.new(edge, d.inputs['Mask'])
            edge = d.outputs[0]
        bl = N.new('CompositorNodeBlur')
        if 'Size' in bl.inputs:
            bl.inputs['Size'].default_value = (1, 1)
        L.new(edge, bl.inputs['Image'])
        edge = mop('MULTIPLY', luma(bl.outputs[0]), ink_strength / 3, clamp=True)

        mix = N.new('ShaderNodeMix')
        mix.data_type = 'RGBA'
        L.new(edge, mix.inputs[0])
        L.new(img, mix.inputs[6])
        mix.inputs[7].default_value = hexcol(ink_hex)
        img = mix.outputs[2]

    if haze:
        hx, h0, h1, amt = haze
        mr = N.new('ShaderNodeMapRange')
        mr.clamp = True
        mr.inputs['From Min'].default_value = h0
        mr.inputs['From Max'].default_value = h1
        mr.inputs['To Max'].default_value = amt
        L.new(rl.outputs['Depth'], mr.inputs['Value'])
        hm = N.new('ShaderNodeMix')
        hm.data_type = 'RGBA'
        L.new(mr.outputs[0], hm.inputs[0])
        L.new(img, hm.inputs[6])
        hm.inputs[7].default_value = hexcol(hx)
        img = hm.outputs[2]

    if bloom:
        g = N.new('CompositorNodeGlare')
        g.inputs['Type'].default_value = 'Bloom'
        g.inputs['Threshold'].default_value = 0.85
        g.inputs['Strength'].default_value = bloom
        g.inputs['Size'].default_value = 0.6
        L.new(img, g.inputs['Image'])
        img = g.outputs['Image']

    if saturation != 1.0:
        hs = N.new('CompositorNodeHueSat')
        hs.inputs['Saturation'].default_value = saturation
        L.new(img, hs.inputs['Image'])
        img = hs.outputs[0]

    # smooth the ink lines (they are found per pixel, so they come out stair-stepped without this)
    aa = N.new('CompositorNodeAntiAliasing')
    aa.inputs['Threshold'].default_value = 0.05
    aa.inputs['Contrast Limit'].default_value = 2.0
    aa.inputs['Corner Rounding'].default_value = 0.4
    L.new(img, aa.inputs['Image'])
    img = aa.outputs[0]
    L.new(img, out.inputs[0])
    return ng
