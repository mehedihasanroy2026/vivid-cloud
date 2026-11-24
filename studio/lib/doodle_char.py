"""Doodle characters in the 'story Shorts' style.

Cream round head with a thick outline, solid hair shape, tall bean body wearing
clothes, long stick legs, drawn-on face with swappable expressions.
Faces -Y. Feet at the root origin. About 6 units tall.

    rig = build('Ken', look={'outfit': 'jacket', 'hair': 'bowl'})
    rig['expr']['happy']  -> list of objects for that expression
"""
import math
import bmesh
import bpy
from mathutils import Vector
import toon as _toon
from toon import toon, ellipsoid, tube, empty, add_outline, LINE_HEX, _link

import os
FACE_ATLAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'faces', 'face_atlas.png')
FACE_CELLS = ['neutral', 'smug', 'happy', 'shocked', 'worried',
              'angry', 'sleep', 'awkward', 'deadpan', 'grimace',
              'dizzy', 'silly', 'talk', 'blink', 'sideeye',
              'sad', 'excited', 'determined', 'wince', 'love',
              'yawn', 'stifle', 'blank', 'proud', 'yawnsmall']
FACE_ALIAS = {'freeze': 'grimace'}       # old toothy name -> the one rare toothy face
ATLAS_COLS, ATLAS_ROWS = 5, 5
FACE_SPAN, FACE_ZOFF = 1.1, -0.08     # atlas cell covers +-SPAN head units, centred at ZOFF

HEAD_R = (1.0, 0.9, 0.92)
TORSO_R = (0.62, 0.5, 1.1)
TORSO_Z = 3.3
NECK_Z = 4.3
HEAD_LOCAL_Z = 0.7          # head centre above the neck pivot
FRONT = -math.pi / 2

DEFAULT = {
    'skin': '#F7F2EC',          # clean cartoon white (Ricks style)
    'hair': 'bowl',            # bowl | side | bald | bun
    'hair_col': '#5E3F2B',
    'outfit': 'jacket',        # jacket | suit | hoodie | dress
    'cloth': '#1FA39A',
    'cloth2': '#FFFFFF',       # shirt / zipper / strings
    'tie': '#2E8B57',
    'shoes': '#5B3A26',
    'mustache': False,
    'glasses': False,
    'badge': False,
}


def surf(theta, phi, lift=0.0, r=HEAD_R):
    d = Vector((math.sin(theta) * math.cos(phi), math.sin(theta) * math.sin(phi), math.cos(theta)))
    t = 1 / math.sqrt((d.x / r[0]) ** 2 + (d.y / r[1]) ** 2 + (d.z / r[2]) ** 2)
    p = d * t
    n = Vector((p.x / r[0] ** 2, p.y / r[1] ** 2, p.z / r[2] ** 2)).normalized()
    return p + n * lift, n


def place(ob, p, n):
    ob.location = p
    ob.rotation_euler = n.to_track_quat('Z', 'Y').to_euler()
    return ob


def arc(theta_fn, phi_fn, lift, n=9, r=HEAD_R):
    return [surf(theta_fn(k / (n - 1)), phi_fn(k / (n - 1)), lift, r)[0] for k in range(n)]


# ---------------------------------------------------------------------------
HAIR_S = 1.04               # hair shell sits just outside the head
HAIR_T = 0.045              # hair thickness (thin = drawn, thick = helmet)


def _hair_edge(phi, style):
    """Lowest point (as theta from the top) the hair reaches at this azimuth."""
    front = max(0.0, -math.sin(phi))                  # 1 at the face
    cut = -0.25 + 0.86 * front ** 0.7                 # high fringe at front, low at back
    if style == 'side':
        cut += 0.16 * math.cos(phi) * front           # fringe sweeps to one side
    if style == 'bun':
        cut = -0.1 + 0.75 * front ** 0.6
    if style == 'cap':
        cut = 0.05 + 0.5 * front ** 0.6
    return math.acos(max(-1.0, min(1.0, cut)))


def _hair_cap(name, parent, mat, style):
    """Smooth-edged hair shell built from a (theta, phi) grid."""
    U, V = 72, 22
    r = [c * HAIR_S for c in HEAD_R]
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    pole = bm.verts.new(surf(0.0, 0.0, 0.0, r)[0])
    rings = []
    for j in range(1, V + 1):
        ring = []
        for i in range(U):
            phi = 2 * math.pi * i / U
            th = _hair_edge(phi, style) * j / V
            ring.append(bm.verts.new(surf(th, phi, 0.0, r)[0]))
        rings.append(ring)
    for i in range(U):
        bm.faces.new((pole, rings[0][(i + 1) % U], rings[0][i]))
    for j in range(V - 1):
        a, b = rings[j], rings[j + 1]
        for i in range(U):
            k = (i + 1) % U
            bm.faces.new((a[i], a[k], b[k], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    ob = _link(name, me, (0, 0, 0), mat, parent, 0)
    sol = ob.modifiers.new('Thick', 'SOLIDIFY')
    sol.thickness = HAIR_T
    sol.offset = 1
    add_outline(ob, 0.04)
    return ob


def _hair(name, head, look, M):
    style = look['hair']
    if style == 'bald':
        for s in (1, -1):        # little side tufts
            p, n = surf(1.45, s * 0.05 + (0 if s > 0 else math.pi), 0.03)
            place(ellipsoid(f'{name}_tuft{s}', (0.28, 0.42, 0.12), p, M['hair'], head, outline=0.03), p, n)
        return
    if style == 'none':
        return
    cap = _hair_cap(f'{name}_hair', head, M['hair'], 'bowl' if style in ('helmet', 'wild') else style)
    if style == 'helmet':        # hard hat: brim + ridge
        z = surf(_hair_edge(FRONT, 'bowl'), FRONT, 0, tuple(c * HAIR_S for c in HEAD_R))[0].z
        ellipsoid(f'{name}_brim', (1.2, 1.12, 0.05), (0, -0.1, z), M['hair'], head, outline=0.025)
        tube(f'{name}_ridge', arc(lambda t: -0.9 + 1.8 * t, lambda t: math.pi / 2, HAIR_T + 0.03, n=9,
                                  r=tuple(c * HAIR_S for c in HEAD_R)), 0.07, M['hair'], head, outline=0.02)
        return
    if style == 'wild':          # caveman spikes
        for i in range(9):
            ph = 2 * math.pi * i / 9
            base, n = surf(0.5 + 0.25 * (i % 2), ph, HAIR_T)
            place(ellipsoid(f'{name}_spike{i}', (0.18, 0.18, 0.42), (0, 0, 0), M['hair'], head,
                            outline=0.03, segs=16, rings=8), base + n * 0.25, n)
        return
    dark = toon(f'{name}_hairline', look['hair_col'])
    # a few strand lines drawn on the hair
    hr = tuple(c * HAIR_S for c in HEAD_R)
    for i, ph in enumerate((-0.55, 0.05, 0.6)):
        end = _hair_edge(FRONT + ph, style) * 0.75
        pts = arc(lambda t, end=end: 0.25 + (end - 0.25) * t,
                  lambda t, ph=ph: FRONT + ph + 0.22 * t * (1 if ph >= 0 else -1),
                  lift=HAIR_T + 0.005, n=7, r=hr)
        tube(f'{name}_strand{i}', pts, 0.016, M['line'], head)
    if style == 'bun':
        p, n = surf(0.35, math.pi / 2, 0.25)
        place(ellipsoid(f'{name}_bun', (0.38, 0.38, 0.34), p, M['hair'], head, outline=0.035), p, n)


def _face(name, head, M, look):
    white = M['white']
    ex = {'neutral': [], 'happy': [], 'shocked': [], 'angry': []}
    TE, PE = 1.42, 0.3                       # eye height / spacing

    def eye_dot(tag, s, sx=0.07, sy=0.1):
        p, n = surf(TE, FRONT + s * PE, 0.0)
        return place(ellipsoid(f'{name}_{tag}eye{s}', (sx, sy, 0.03), p, M['line'], head, segs=20, rings=10), p, n)

    def brow(tag, s, th, tilt, lift=0.02):
        pts = arc(lambda t: th + tilt * (t - 0.5) * s, lambda t: FRONT + s * (PE - 0.13 + 0.26 * t), lift, n=5)
        return tube(f'{name}_{tag}brow{s}', pts, 0.032, M['line'], head)

    # neutral: dot eyes, flat brows, small smirk
    for s in (1, -1):
        ex['neutral'] += [eye_dot('n', s), brow('n', s, 1.16, 0.0)]
    ex['neutral'].append(tube(f'{name}_nmouth', arc(lambda t: 1.86 - 0.05 * t * t, lambda t: FRONT - 0.16 + 0.36 * t, 0.015, n=6),
                              0.028, M['line'], head))

    # happy: ^ ^ eyes, raised brows, toothy grin
    for s in (1, -1):
        ex['happy'].append(tube(f'{name}_heye{s}', arc(lambda t: TE - 0.1 * (1 - (2 * t - 1) ** 2) + 0.03,
                                                       lambda t: FRONT + s * PE - 0.12 + 0.24 * t, 0.015, n=9), 0.03, M['line'], head))
        ex['happy'].append(brow('h', s, 1.08, -0.06))
    p, n = surf(1.88, FRONT, -0.01)
    grin = place(ellipsoid(f'{name}_grin', (0.36, 0.16, 0.06), p, white, head, outline=0.028, segs=32, rings=16), p, n)
    W, H, D = 0.36, 0.16, 0.06

    def gz(x, y):
        return D * math.sqrt(max(0.0, 1 - (x / W) ** 2 - (y / H) ** 2)) + 0.006
    for i, x in enumerate((-0.24, -0.12, 0.0, 0.12, 0.24)):
        ym = H * math.sqrt(1 - (x / W) ** 2) * 0.92
        tube(f'{name}_tooth{i}', [(x, y, gz(x, y)) for y in (-ym, -ym / 2, 0, ym / 2, ym)], 0.012, M['line'], grin)
    xm = W * 0.95
    tube(f'{name}_teethline', [(x, 0, gz(x, 0)) for x in (-xm, -xm / 2, 0, xm / 2, xm)], 0.012, M['line'], grin)
    ex['happy'].append(grin)

    # shocked: big white eyes with pupils, high brows, little O mouth
    for s in (1, -1):
        p, n = surf(TE - 0.02, FRONT + s * (PE + 0.02), 0.0)
        e = place(ellipsoid(f'{name}_seye{s}', (0.15, 0.17, 0.05), p, white, head, outline=0.025, segs=24, rings=12), p, n)
        ellipsoid(f'{name}_spupil{s}', (0.05, 0.06, 0.03), (0, 0, 0.04), M['line'], e, segs=16, rings=8)
        ex['shocked'] += [e, brow('s', s, 1.02, 0.1, 0.03)]
    p, n = surf(1.9, FRONT, 0.0)
    ex['shocked'].append(place(ellipsoid(f'{name}_smouth', (0.1, 0.13, 0.03), p, M['line'], head, segs=20, rings=10), p, n))

    # angry: dot eyes, slanted brows, frown
    for s in (1, -1):
        ex['angry'] += [eye_dot('a', s), brow('a', s, 1.2, -0.22)]
    ex['angry'].append(tube(f'{name}_amouth', arc(lambda t: 1.9 - 0.06 * (1 - (2 * t - 1) ** 2), lambda t: FRONT - 0.18 + 0.36 * t, 0.015, n=7),
                            0.028, M['line'], head))

    # freeze (the 🥶 face): wide eyes with tiny pupils + clenched teeth
    for s in (1, -1):
        p, n = surf(TE - 0.03, FRONT + s * (PE + 0.03), 0.0)
        e = place(ellipsoid(f'{name}_feye{s}', (0.16, 0.18, 0.05), p, white, head, outline=0.025, segs=24, rings=12), p, n)
        ellipsoid(f'{name}_fpupil{s}', (0.035, 0.04, 0.03), (0, 0.02, 0.045), M['line'], e, segs=12, rings=6)
        ex.setdefault('freeze', []).extend([e, brow('f', s, 1.0, 0.18, 0.03)])
    p, n = surf(1.9, FRONT, -0.01)
    fg = place(ellipsoid(f'{name}_fgrin', (0.4, 0.15, 0.06), p, white, head, outline=0.028, segs=32, rings=16), p, n)
    W2, H2 = 0.4, 0.15
    for i, x in enumerate((-0.28, -0.14, 0.0, 0.14, 0.28)):
        ym = H2 * math.sqrt(1 - (x / W2) ** 2) * 0.92
        tube(f'{name}_ftooth{i}', [(x, y, 0.06 * math.sqrt(max(0, 1 - (x / W2) ** 2 - (y / H2) ** 2)) + 0.006)
                                   for y in (-ym, 0, ym)], 0.012, M['line'], fg)
    tube(f'{name}_fteethline', [(x, 0, 0.06 * math.sqrt(max(0, 1 - (x / W2) ** 2)) + 0.006)
                                for x in (-0.37, -0.18, 0, 0.18, 0.37)], 0.012, M['line'], fg)
    ex['freeze'].append(fg)

    # sleep: closed eyes (gentle downward curves), relaxed brows, tiny calm mouth
    ex['sleep'] = []
    for s in (1, -1):
        ex['sleep'].append(tube(f'{name}_zeye{s}', arc(lambda t: TE + 0.07 * (1 - (2 * t - 1) ** 2),
                                                       lambda t: FRONT + s * PE - 0.12 + 0.24 * t, 0.015, n=9),
                                0.026, M['line'], head))
        ex['sleep'].append(brow('z', s, 1.2, 0.04))
    ex['sleep'].append(tube(f'{name}_zmouth', arc(lambda t: 1.88, lambda t: FRONT - 0.08 + 0.16 * t, 0.015, n=3),
                            0.024, M['line'], head))

    # awkward / embarrassed: worried brows, wobbly mouth, pink cheeks
    blush = toon('Blush', '#F28C9A')
    ex['awkward'] = []
    for s in (1, -1):
        ex['awkward'] += [eye_dot('w', s), brow('w', s, 1.14, 0.2)]
        p, n = surf(1.66, FRONT + s * 0.52, 0.0)
        ex['awkward'].append(place(ellipsoid(f'{name}_blush{s}', (0.16, 0.09, 0.03), p, blush, head, segs=16, rings=8), p, n))
    ex['awkward'].append(tube(f'{name}_wmouth', arc(lambda t: 1.88 + 0.03 * math.sin(t * 2 * math.pi * 1.5),
                                                    lambda t: FRONT - 0.18 + 0.36 * t, 0.015, n=9),
                              0.024, M['line'], head))

    if look.get('beard'):
        p, n = surf(2.2, FRONT, 0.02)
        place(ellipsoid(f'{name}_beard', (0.55, 0.42, 0.2), p, M['hair'], head, outline=0.035), p, n)
    if look['mustache']:
        for s in (1, -1):
            p, n = surf(1.7, FRONT + s * 0.12, 0.01)
            place(ellipsoid(f'{name}_stache{s}', (0.16, 0.06, 0.04), p, M['hair'], head, outline=0.02), p, n)
    if look['glasses']:
        for s in (1, -1):
            c, n = surf(TE, FRONT + s * PE, 0.05)
            ring = [surf(TE + 0.2 * math.sin(a), FRONT + s * PE + 0.2 * math.cos(a), 0.05)[0]
                    for a in [i * math.pi / 8 for i in range(17)]]
            tube(f'{name}_glass{s}', ring, 0.022, M['line'], head)
        tube(f'{name}_bridge', arc(lambda t: TE, lambda t: FRONT - 0.1 + 0.2 * t, 0.05, n=3), 0.02, M['line'], head)
    return ex


def _outfit(name, root, look, M):
    o = look['outfit']

    def tsurf(theta, phi, lift=0.0):
        return surf(theta, phi, lift, TORSO_R)

    def onbody(nm, radii, theta, phi, mat, lift=0.0, outline=0.0):
        p, n = tsurf(theta, phi, lift)
        ob = ellipsoid(nm, radii, p + Vector((0, 0, TORSO_Z)), mat, root, outline=outline, segs=24, rings=12)
        ob.rotation_euler = n.to_track_quat('Z', 'Y').to_euler()
        return ob

    if o == 'suit':
        onbody(f'{name}_shirt', (0.2, 0.38, 0.04), 0.55, FRONT, M['cloth2'], -0.01, outline=0.02)
        onbody(f'{name}_tie', (0.07, 0.36, 0.035), 0.62, FRONT, M['tie'], 0.02, outline=0.018)
        for s in (1, -1):   # lapel lines
            pts = [tsurf(0.25 + 0.6 * t, FRONT + s * (0.38 - 0.2 * t), 0.015)[0] + Vector((0, 0, TORSO_Z)) for t in (0, 0.5, 1)]
            tube(f'{name}_lapel{s}', pts, 0.02, M['line'], root)
    elif o == 'jacket':
        onbody(f'{name}_tee', (0.18, 0.22, 0.04), 0.4, FRONT, M['cloth2'], -0.01, outline=0.02)
        pts = [tsurf(0.55 + 2.0 * t, FRONT, 0.012)[0] + Vector((0, 0, TORSO_Z)) for t in (0, 0.25, 0.5, 0.75, 1)]
        tube(f'{name}_zip', pts, 0.022, M['line'], root)
    elif o == 'towel':          # bare chest, towel round the waist
        ellipsoid(f'{name}_towel', (0.69, 0.57, 0.5), (0, 0, TORSO_Z - 0.62), M['cloth2'], root, outline=0.04)
        pts = [tsurf(2.05, FRONT - 0.9 + 0.9 * t, 0.07)[0] + Vector((0, 0, TORSO_Z)) for t in (0, 0.5, 1)]
        tube(f'{name}_towelfold', pts, 0.02, M['line'], root)
        onbody(f'{name}_navel', (0.04, 0.05, 0.02), 1.55, FRONT, M['line'], 0.0)
    elif o == 'caveman':        # spotted fur with one shoulder strap
        import random
        rnd = random.Random(7)
        for i in range(9):
            onbody(f'{name}_spot{i}', (0.08, 0.06, 0.025), rnd.uniform(0.6, 2.4), FRONT + rnd.uniform(-1.0, 1.0),
                   M['tie'], 0.0)
        pts = [tsurf(0.25 + 1.1 * t, FRONT + 0.55 - 1.0 * t, 0.02)[0] + Vector((0, 0, TORSO_Z)) for t in (0, 0.5, 1)]
        tube(f'{name}_strap', pts, 0.05, M['tie'], root)
    elif o == 'labcoat':
        onbody(f'{name}_shirt', (0.18, 0.34, 0.04), 0.5, FRONT, M['cloth2'], -0.01, outline=0.02)
        onbody(f'{name}_tie', (0.06, 0.3, 0.03), 0.6, FRONT, M['tie'], 0.02, outline=0.016)
        for s in (1, -1):
            pts = [tsurf(0.3 + 1.4 * t, FRONT + s * (0.36 - 0.1 * t), 0.015)[0] + Vector((0, 0, TORSO_Z)) for t in (0, 0.5, 1)]
            tube(f'{name}_coatedge{s}', pts, 0.018, M['line'], root)
        onbody(f'{name}_pocket', (0.15, 0.1, 0.02), 1.15, FRONT + 0.5, M['cloth'], 0.01, outline=0.012)
    elif o == 'overalls':
        onbody(f'{name}_bib', (0.3, 0.4, 0.04), 1.2, FRONT, M['cloth2'], 0.0, outline=0.02)
        for s in (1, -1):
            onbody(f'{name}_button{s}', (0.045, 0.045, 0.03), 0.9, FRONT + s * 0.32, M['tie'], 0.02)
    elif o == 'pajamas':        # collar, button placket, chest pocket
        for s in (1, -1):
            c = onbody(f'{name}_collar{s}', (0.2, 0.12, 0.04), 0.32, FRONT + s * 0.2, M['cloth2'], 0.02, outline=0.018)
            c.rotation_euler.rotate_axis('Z', s * 0.5)
        pts = [tsurf(0.45 + 1.6 * t, FRONT, 0.012)[0] + Vector((0, 0, TORSO_Z)) for t in (0, 0.5, 1)]
        tube(f'{name}_placket', pts, 0.016, M['line'], root)
        for i in range(4):
            onbody(f'{name}_pjbutton{i}', (0.04, 0.04, 0.025), 0.6 + 0.4 * i, FRONT + 0.07, M['cloth2'], 0.02)
        onbody(f'{name}_pjpocket', (0.15, 0.12, 0.02), 0.85, FRONT - 0.45, M['cloth2'], 0.01, outline=0.012)
    elif o == 'hoodie':
        for s in (1, -1):
            pts = [tsurf(0.5 + 0.7 * t, FRONT + s * 0.14, 0.015)[0] + Vector((0, 0, TORSO_Z)) for t in (0, 0.5, 1)]
            tube(f'{name}_string{s}', pts, 0.02, M['cloth2'], root)
        pts = [tsurf(1.95, FRONT - 0.5 + t, 0.012)[0] + Vector((0, 0, TORSO_Z)) for t in (0, 0.5, 1)]
        tube(f'{name}_pocket', pts, 0.018, M['line'], root)
    if look['badge']:
        onbody(f'{name}_badge', (0.1, 0.13, 0.03), 1.2, FRONT + 0.35, M['cloth2'], 0.02, outline=0.015)


def _face_material(name, skin_hex):
    """Skin material with the drawn-face atlas projected onto the front of the head.
    A Value node ('FaceCell') picks the expression; keyframe it to change faces."""
    m = bpy.data.materials.new(f'{name}_face')
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    out = N.new('ShaderNodeOutputMaterial')
    bsdf = N.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value = 0.75
    for nm in ('Specular IOR Level', 'Specular'):
        if nm in bsdf.inputs:
            bsdf.inputs[nm].default_value = 0.1
            break
    L.new(bsdf.outputs[0], out.inputs['Surface'])

    def mth(op, a, b=None):
        n = N.new('ShaderNodeMath')
        n.operation = op
        for k, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[k].default_value = v
            else:
                L.new(v, n.inputs[k])
        return n.outputs[0]
    tc = N.new('ShaderNodeTexCoord')
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['Object'], sep.inputs[0])
    u = mth('DIVIDE', mth('ADD', sep.outputs['X'], FACE_SPAN), 2 * FACE_SPAN)
    v = mth('DIVIDE', mth('ADD', mth('SUBTRACT', sep.outputs['Z'], FACE_ZOFF), FACE_SPAN), 2 * FACE_SPAN)
    cell = N.new('ShaderNodeValue')
    cell.name = cell.label = 'FaceCell'
    col = mth('MODULO', cell.outputs[0], ATLAS_COLS)
    row = mth('FLOOR', mth('DIVIDE', cell.outputs[0], ATLAS_COLS))
    U = mth('DIVIDE', mth('ADD', col, mth('MAXIMUM', mth('MINIMUM', u, 0.999), 0.001)), ATLAS_COLS)
    V = mth('DIVIDE', mth('ADD', mth('SUBTRACT', ATLAS_ROWS - 1, row),
                          mth('MAXIMUM', mth('MINIMUM', v, 0.999), 0.001)), ATLAS_ROWS)
    uv = N.new('ShaderNodeCombineXYZ')
    L.new(U, uv.inputs['X'])
    L.new(V, uv.inputs['Y'])
    img = N.new('ShaderNodeTexImage')
    img.image = bpy.data.images.load(os.path.normpath(FACE_ATLAS), check_existing=True)
    img.interpolation = 'Cubic'
    img.extension = 'CLIP'
    L.new(uv.outputs[0], img.inputs['Vector'])
    inside = mth('MULTIPLY', mth('MULTIPLY', mth('GREATER_THAN', u, 0.0), mth('LESS_THAN', u, 1.0)),
                 mth('MULTIPLY', mth('GREATER_THAN', v, 0.0), mth('LESS_THAN', v, 1.0)))
    front = mth('LESS_THAN', sep.outputs['Y'], 0.0)
    fac = mth('MULTIPLY', mth('MULTIPLY', inside, front), img.outputs['Alpha'])
    mix = N.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    L.new(fac, mix.inputs[0])
    mix.inputs[6].default_value = _toon.hexcol(skin_hex)
    L.new(img.outputs['Color'], mix.inputs[7])
    L.new(mix.outputs[2], bsdf.inputs['Base Color'])
    m.diffuse_color = _toon.hexcol(skin_hex)
    return m, cell


def _glove(name, sh, s, mat):
    """Cartoon 4-finger glove at the end of the arm."""
    side = 'L' if s > 0 else 'R'
    hand = empty(f'{name}_hand{side}', (s * 0.27, -0.06, -1.38), sh)
    hand.scale = (1.5, 1.5, 1.5)
    ellipsoid(f'{name}_palm{side}', (0.1, 0.075, 0.11), (0, 0, -0.04), mat, hand, outline=0.022, segs=16, rings=8)
    for i, dy in enumerate((-0.05, 0.0, 0.05)):
        ellipsoid(f'{name}_finger{side}{i}', (0.032, 0.03, 0.075), (s * 0.01, dy, -0.16), mat, hand, outline=0.016,
                  segs=10, rings=6)
    t = ellipsoid(f'{name}_thumb{side}', (0.03, 0.03, 0.065), (-s * 0.06, -0.07, -0.05), mat, hand, outline=0.016,
                  segs=10, rings=6)
    t.rotation_euler = (0.6, 0, -s * 0.6)
    ellipsoid(f'{name}_cuff{side}', (0.09, 0.09, 0.035), (0, 0, 0.07), mat, hand, outline=0.018, segs=16, rings=6)
    return hand


def _hat(name, head, look, M):
    hat = look.get('hat')
    if not hat:
        return
    hm = toon(f'{name}_hat', look.get('hat_col', '#E8393C'))
    if hat == 'cap':
        global HAIR_S
        old = HAIR_S
        HAIR_S = 1.09
        _hair_cap(f'{name}_capdome', head, hm, 'cap')
        HAIR_S = old
        b = ellipsoid(f'{name}_capbrim', (0.72, 0.6, 0.06), (0, -1.05, 0.52), hm, head, outline=0.03)
        b.rotation_euler = (math.radians(-8), 0, 0)
        ellipsoid(f'{name}_capbutton', (0.1, 0.1, 0.06), (0, 0.0, 1.0), hm, head, outline=0.015)
        band = toon(f'{name}_capband', look.get('hat_col2', '#FFFFFF'))
        p, n = surf(0.75, FRONT, 0.13, tuple(c * 1.09 for c in HEAD_R))
        place(ellipsoid(f'{name}_capfront', (0.3, 0.22, 0.03), p, band, head, outline=0.018), p, n)
    c2 = toon(f'{name}_hat2', look.get('hat_col2', '#FFFFFF'))
    if hat == 'beanie':          # knit dome + folded rim + pompom
        ellipsoid(f'{name}_hatDome', (0.97, 0.88, 0.56), (0, 0.02, 0.6), hm, head, outline=0.035, segs=32, rings=16)
        ellipsoid(f'{name}_hatRim', (1.0, 0.91, 0.17), (0, 0.02, 0.38), hm, head, outline=0.03, segs=32, rings=10)
        ellipsoid(f'{name}_hatPom', (0.24, 0.24, 0.22), (0, 0.05, 1.2), c2, head, outline=0.025, segs=16, rings=8)
    elif hat == 'chef':          # band + tall puffy top
        ellipsoid(f'{name}_hatBand', (0.95, 0.86, 0.22), (0, 0.02, 0.5), c2, head, outline=0.03, segs=32, rings=10)
        for i, (x, z, r) in enumerate(((0, 1.1, 0.7), (-0.42, 0.95, 0.5), (0.42, 0.95, 0.5), (0, 1.35, 0.55))):
            ellipsoid(f'{name}_hatPuff{i}', (r, r * 0.9, r * 0.8), (x, 0.05, z), c2, head, outline=0.03, segs=24, rings=12)
    elif hat in ('bowler', 'explorer'):
        wide = 1.38 if hat == 'explorer' else 1.22
        ellipsoid(f'{name}_hatBrim', (wide, wide * 0.93, 0.05), (0, 0.0, 0.5), hm, head, outline=0.03, segs=40, rings=8)
        ellipsoid(f'{name}_hatDome', (0.78, 0.72, 0.52 if hat == 'bowler' else 0.42), (0, 0.02, 0.78), hm, head, outline=0.035, segs=32, rings=16)
        ellipsoid(f'{name}_hatBand', (0.8, 0.74, 0.1), (0, 0.02, 0.6), c2, head, outline=0.02, segs=32, rings=8)
    elif hat == 'beret':
        b = ellipsoid(f'{name}_hatDome', (1.0, 0.92, 0.3), (0.12, 0.05, 0.82), hm, head, outline=0.035, segs=32, rings=12)
        b.rotation_euler = (0, math.radians(-12), 0)
    elif hat == 'headphones':
        pts = [(1.02 * math.cos(a), 0.05, 0.25 + 0.98 * math.sin(a)) for a in [math.pi * k / 16 for k in range(17)]]
        tube(f'{name}_hatBandP', pts, 0.07, hm, head, outline=0.02)
        for sx in (1, -1):
            ellipsoid(f'{name}_hatCup{sx}', (0.2, 0.36, 0.4), (sx * 1.02, 0.05, 0.15), hm, head, outline=0.03, segs=20, rings=10)
            ellipsoid(f'{name}_hatPad{sx}', (0.1, 0.3, 0.33), (sx * 0.9, 0.05, 0.15), c2, head, segs=16, rings=8)


def build(name='Ken', loc=(0, 0, 0), look=None):
    look = dict(DEFAULT, **(look or {}))
    paint, _toon.PAINT = _toon.PAINT, min(_toon.PAINT, 0.07)    # characters stay clean
    M = {
        'skin': toon(f'{name}_skin', look['skin']),
        'hair': toon(f'{name}_hair', look['hair_col']),
        'cloth': toon(f'{name}_cloth', look['cloth'] if look['cloth'] != 'skin' else look['skin'],
                      tex=look.get('pattern')),     # e.g. ('stripes', '#FFFFFF', 0.18, 'x')
        'cloth2': toon(f'{name}_cloth2', look['cloth2']),
        'tie': toon(f'{name}_tie', look['tie']),
        'shoes': toon(f'{name}_shoes', look['shoes']),
        'line': toon('Ink', LINE_HEX, rough=0.9),
        'white': toon('FaceWhite', '#FFFFFF'),
    }
    if look['cloth'] == 'skin':          # bare body shares the skin material
        M['cloth'] = M['skin']
    drawn = look.get('face', 'drawn') == 'drawn'
    if drawn:
        M['face'], face_cell = _face_material(name, look['skin'])
    M['glove'] = toon('Glove', look.get('glove', '#F7F4EC'))
    _toon.PAINT = paint
    # mover: place / turn / walk the character.  root: shakes, bounces (child of mover)
    mover = empty(name, loc)
    mover.scale = (look.get('scale', 1.0),) * 3
    root = empty(f'{name}_body', (0, 0, 0), mover)
    rig = {'mover': mover, 'root': root, 'look': look, 'mats': M}

    # body
    torso_shape = TORSO_R if look['outfit'] != 'dress' else (0.7, 0.55, 1.15)
    rig['torso'] = ellipsoid(f'{name}_torso', torso_shape, (0, 0, TORSO_Z), M['cloth'], root, outline=0.05)
    _outfit(name, root, look, M)
    bare_feet = look['outfit'] in ('caveman',)
    for s, side in ((1, 'L'), (-1, 'R')):
        hip = empty(f'{name}_hip{side}', (s * 0.22, 0, 2.5), root)
        tube(f'{name}_leg{side}', [(0, 0, 0), (s * 0.01, 0, -1.3), (s * 0.02, 0, -2.38)], 0.055, M['line'], hip)
        foot = M['skin'] if bare_feet else M['shoes']
        ellipsoid(f'{name}_shoe{side}', (0.17, 0.28, 0.12), (s * 0.03, -0.09, -2.4), foot, hip, outline=0.03)
        rig[f'hip{side}'] = hip
        sh = empty(f'{name}_shoulder{side}', (s * 0.5, 0, 3.85), root)
        tube(f'{name}_arm{side}', [(0, 0, 0), (s * 0.2, -0.02, -0.7), (s * 0.27, -0.06, -1.35)], 0.045, M['line'], sh)
        if look.get('gloves', True):
            rig[f'hand{side}'] = _glove(name, sh, s, M['glove'])
        else:
            ellipsoid(f'{name}_hand{side}', (0.075, 0.075, 0.075), (s * 0.27, -0.06, -1.38), M['line'], sh,
                      segs=16, rings=8)
        rig[f'shoulder{side}'] = sh

    # head
    neck = empty(f'{name}_neck', (0, 0, NECK_Z), root)
    head = ellipsoid(f'{name}_head', HEAD_R, (0, 0, HEAD_LOCAL_Z), M['face'] if drawn else M['skin'], neck,
                     outline=0.065, segs=96, rings=48)
    rig['neck'], rig['head'] = neck, head
    _hair(name, head, look, M)
    _hat(name, head, look, M)
    if drawn:
        rig['face_cell'] = face_cell
        rig['expr'] = {}
        _face_extras(name, head, M, look)
    else:
        rig['expr'] = _face(name, head, M, look)
    set_expression(rig, 'neutral')
    for ob in head.children_recursive:        # hair / hats never shade the face (keeps faces bright)
        if any(k in ob.name for k in ('_hair', '_cap', '_tuft', '_bun', '_brim', '_spike', '_hat')):
            ob.visible_shadow = False
    return rig


def _face_extras(name, head, M, look):
    """3D bits that sit on top of a drawn face: mustache, glasses, beard."""
    if look.get('beard'):
        p, n = surf(2.2, FRONT, 0.02)
        place(ellipsoid(f'{name}_beard', (0.55, 0.42, 0.2), p, M['hair'], head, outline=0.035), p, n)
    if look['mustache']:
        for s in (1, -1):
            p, n = surf(1.72, FRONT + s * 0.12, 0.01)
            place(ellipsoid(f'{name}_stache{s}', (0.16, 0.06, 0.04), p, M['hair'], head, outline=0.02), p, n)
    if look['glasses']:
        for s in (1, -1):
            ring = [surf(1.42 + 0.21 * math.sin(a), FRONT + s * 0.3 + 0.21 * math.cos(a), 0.05)[0]
                    for a in [i * math.pi / 8 for i in range(17)]]
            tube(f'{name}_glass{s}', ring, 0.022, M['line'], head)
        tube(f'{name}_bridge', arc(lambda t: 1.42, lambda t: FRONT - 0.1 + 0.2 * t, 0.05, n=3), 0.02, M['line'], head)


def set_expression(rig, which, frame=None):
    """Show one expression. With a frame number the change is keyframed."""
    if 'face_cell' in rig:
        which = FACE_ALIAS.get(which, which)
        node = rig['face_cell']
        node.outputs[0].default_value = float(FACE_CELLS.index(which))
        if frame is not None:
            node.outputs[0].keyframe_insert('default_value', frame=frame)
            ad = node.id_data.animation_data
            if ad and ad.action:
                for fc in _all_fcurves(ad.action):
                    for kp in fc.keyframe_points:
                        kp.interpolation = 'CONSTANT'
        return
    for k, objs in rig['expr'].items():
        vis = (k == which)
        for o in objs:
            for ob in [o] + list(o.children_recursive):
                ob.hide_render = not vis
                ob.hide_viewport = not vis
                if frame is not None:
                    ob.keyframe_insert('hide_render', frame=frame)


def _all_fcurves(act):
    if hasattr(act, 'fcurves') and len(getattr(act, 'fcurves', [])):
        return list(act.fcurves)
    out = []
    for layer in getattr(act, 'layers', []):
        for strip in layer.strips:
            for cb in strip.channelbags:
                out.extend(cb.fcurves)
    return out
