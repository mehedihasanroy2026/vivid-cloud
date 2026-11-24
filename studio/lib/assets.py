"""Load downloaded 3D models (Kenney CC0 packs in studio/assets/kenney) and restyle them
to the toon / pro look: matte paint, soft colour variation, ink comes from the compositor.

    import assets
    assets.ROOT = os.path.join(studio, 'assets')
    tree = assets.load('nature-kit', 'tree_oak', loc=(3, 2, 0), scale=4.0, rot=(0, 0, 30))

Each call imports the .glb once and makes linked duplicates after that (cheap).
The returned object is an empty parent; the meshes hang under it.
"""
import os
import math
import glob
import bpy
import toon

ROOT = ''
SCALE = 3.5           # Kenney 1 unit ~ 1 m; our characters are ~6 units tall
_cache = {}
# Kenney's own palette is minty/pastel; map its material names onto our painted palette
RECOLOR = {
    'leafsGreen': '#5DB35A', 'leafsDark': '#3F8A4E', 'leafsFall': '#E39B3C', 'grass': '#6DBB5C',
    'woodBark': '#8A5A3C', 'woodBarkDark': '#6B4430', 'wood': '#C58A55', 'woodDark': '#8A5A3C',
    'dirt': '#B98A5E', 'stone': '#A7A2B8', 'stoneDark': '#7E7896',
}


def _find(pack, name):
    hits = glob.glob(os.path.join(ROOT, 'kenney', pack, 'Models', '*', name + '.glb'))
    if not hits:
        raise FileNotFoundError(f'{pack}/{name}.glb')
    return hits[0]


def _restyle(mat):
    if mat.get('restyled'):
        return
    mat['restyled'] = True
    N, L = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next((n for n in N if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf:
        return
    bsdf.inputs['Roughness'].default_value = 0.8
    bsdf.inputs['Metallic'].default_value = 0.0
    for nm in ('Specular IOR Level', 'Specular'):
        if nm in bsdf.inputs:
            bsdf.inputs[nm].default_value = 0.1
            break
    key = mat.name.split('.')[0]
    if key in RECOLOR and not bsdf.inputs['Base Color'].is_linked:
        bsdf.inputs['Base Color'].default_value = toon.hexcol(RECOLOR[key])
    base = tuple(bsdf.inputs['Base Color'].default_value)
    if toon.PAINT:
        toon._paint(N, L, bsdf, base)


def _import(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in meshes:
        for slot in o.material_slots:
            if slot.material:
                _restyle(slot.material)
        # soften the low-poly look: small rounded bevels + smooth shading on curved parts
        bv = o.modifiers.new('SoftEdges', 'BEVEL')
        bv.width = 0.025
        bv.segments = 3
        bv.limit_method = 'ANGLE'
        bv.harden_normals = True
        try:
            o.data.shade_smooth_by_angle(angle=math.radians(40))
        except Exception:
            pass
    # bake transforms into the meshes, drop the glTF empties
    for o in new:
        o.select_set(False)
    for o in meshes:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
    for o in new:
        if o.type != 'MESH':
            bpy.data.objects.remove(o)
    return meshes


def load(pack, name, loc=(0, 0, 0), scale=1.0, rot=(0, 0, 0), parent=None, tint=None, center=False):
    """Place one model. scale is on top of the global SCALE. rot in degrees."""
    key = (pack, name)
    if key not in _cache:
        meshes = _import(_find(pack, name))
        for o in meshes:                 # keep the originals as hidden templates
            for c in o.users_collection:
                c.objects.unlink(o)
        _cache[key] = meshes
    root = bpy.data.objects.new(f'{name}', None)
    bpy.context.scene.collection.objects.link(root)
    for src in _cache[key]:
        o = src.copy()                   # linked duplicate: shares mesh data
        bpy.context.scene.collection.objects.link(o)
        o.parent = root
        if tint:
            o.data = o.data.copy()
            m = toon.toon(f'{name}_tint_{tint}', tint)
            for i in range(len(o.material_slots)):
                o.material_slots[i].link = 'OBJECT'
                o.material_slots[i].material = m
    if center:      # Kenney pivots sit at a corner: centre the footprint on loc
        from mathutils import Vector
        pts = [src.matrix_world @ Vector(v) for src in _cache[key] for v in src.bound_box]
        cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
        cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
        for o in root.children:
            o.location = (o.location[0] - cx, o.location[1] - cy, o.location[2])
    if parent:
        root.parent = parent
    root.location = loc
    root.rotation_euler = [math.radians(a) for a in rot]
    root.scale = (SCALE * scale,) * 3
    return root
