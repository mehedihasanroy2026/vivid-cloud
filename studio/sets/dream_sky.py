"""Set: dream world. A chunk of night sidewalk floating in a purple starry sky, with cloud
banks below it to fall through.

Local layout: sidewalk runs along X (x -14..14) at y -1..2, top at z=0. Walk along +X.
Fall column: below the sidewalk end, x ~ 6, clouds from z -6 down to z -70.
"""
import math
import random
import bpy
from toon import toon, box, ellipsoid, cylinder, tube, point_light, area_light, SetBuilder, hexcol, empty


def sky_mat(name, top, bottom, strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.clear()
    out = N.new('ShaderNodeOutputMaterial')
    tc = N.new('ShaderNodeTexCoord')
    sep = N.new('ShaderNodeSeparateXYZ')
    L.new(tc.outputs['Object'], sep.inputs[0])
    rng = N.new('ShaderNodeMapRange')
    rng.inputs['From Min'].default_value = -1.0
    rng.inputs['From Max'].default_value = 1.0
    L.new(sep.outputs['Z'], rng.inputs['Value'])
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = hexcol(bottom)
    ramp.color_ramp.elements[1].color = hexcol(top)
    L.new(rng.outputs[0], ramp.inputs['Fac'])
    em = N.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = strength
    L.new(ramp.outputs['Color'], em.inputs['Color'])
    L.new(em.outputs[0], out.inputs['Surface'])
    m.use_backface_culling = False
    return m


def cloud(name, loc, scale, mat, rnd, parent=None, n=7):
    c = empty(name, loc, parent)
    for i in range(n):
        a = i / n * 2 * math.pi
        r = rnd.uniform(0.9, 1.5)
        ellipsoid(f'{name}_{i}', (r * 1.4, r, r * 0.8), (1.6 * math.cos(a), 0.6 * math.sin(a), rnd.uniform(-0.2, 0.5)),
                  mat, c, outline=0.05, segs=20, rings=10)
    ellipsoid(f'{name}_core', (2.4, 1.4, 1.2), (0, 0, 0.3), mat, c, outline=0.05, segs=24, rings=12)
    c.scale = (scale,) * 3
    return c


def build(origin=(0, 0, 0)):
    rnd = random.Random(11)
    with SetBuilder('Dream', origin) as root:
        sky = sky_mat('DreamSky', '#2A1F5C', '#C76BA8', 1.0)
        dome = ellipsoid('DreamDome', (120, 120, 120), (0, 0, -20), sky, segs=48, rings=24)
        star = toon('DreamStar', '#FFF6D8', emit=True)
        for i in range(140):
            th = rnd.uniform(0, 2 * math.pi)
            ph = rnd.uniform(-0.6, 1.3)
            d = 95
            ellipsoid('DreamStarDot', (0.35, 0.35, 0.35),
                      (d * math.cos(th) * math.cos(ph), d * math.sin(th) * math.cos(ph), -20 + d * math.sin(ph)),
                      star, segs=6, rings=3)
        moon = toon('DreamMoon', '#FFF1B8', emit=True)
        cylinder('DreamMoonDisc', 7, 0.2, (20, 80, 28), moon, rot=(90, 0, 0))

        # floating sidewalk chunk: pavement slabs, curb, a strip of road, rocky underside
        pave = toon('DreamPave', '#9A97B8', tex=('tiles', '#6E6A8E', 1.5))
        curb = toon('DreamCurb', '#C9C6DD')
        road = toon('DreamRoad', '#3E3A5C')
        dirt = toon('DreamDirt', '#6B4E6E')
        yellow = toon('DreamLine', '#F2D16B')
        box('DreamPavement', (28, 3.2, 0.4), (0, 0.6, -0.2), pave)
        box('DreamCurbOb', (28, 0.4, 0.55), (0, -1.2, -0.12), curb)
        box('DreamRoadOb', (28, 4.0, 0.3), (0, -3.4, -0.5), road)
        for x in range(-12, 14, 4):
            box('DreamDash', (1.6, 0.25, 0.04), (x, -3.4, -0.33), yellow)
        for i in range(9):
            x = -13 + i * 3.3
            ellipsoid('DreamRock', (2.2, 3.6, 2.4 + rnd.random() * 1.5), (x, -1.4, -2.2 - rnd.random()), dirt,
                      outline=0.05, segs=16, rings=8)

        # street props: lamppost with glow, hydrant, bench, mailbox
        metal = toon('DreamMetal', '#3A3556')
        glow = toon('DreamLampGlow', '#FFE6A0', emit=True)
        for x in (-8, 4):
            cylinder('DreamPost', 0.14, 7.0, (x, 1.8, 3.5), metal, outline=0.02)
            tube('DreamArm', [(x, 1.8, 7.0), (x, 1.2, 7.4), (x, 0.6, 7.2)], 0.08, metal)
            ellipsoid('DreamBulb', (0.45, 0.45, 0.3), (x, 0.6, 7.0), glow, outline=0.02)
            point_light((x, 0.6, 6.3), 500, '#FFD58A', 0.4, 'DreamLampLight')
        red = toon('DreamHydrant', '#D9483B')
        cylinder('DreamHyd', 0.3, 1.0, (-3, 1.6, 0.5), red, outline=0.02)
        ellipsoid('DreamHydTop', (0.32, 0.32, 0.25), (-3, 1.6, 1.0), red, outline=0.02)
        wood = toon('DreamBench', '#A0663E', tex=('planks', '#5A3420', 0.3, 'floor'))
        box('DreamBenchSeat', (3.0, 0.9, 0.15), (-11, 1.6, 1.3), wood)
        box('DreamBenchBack', (3.0, 0.15, 1.0), (-11, 2.05, 2.0), wood)
        for dx in (-1.3, 1.3):
            box('DreamBenchLeg', (0.12, 0.8, 1.3), (-11 + dx, 1.6, 0.65), metal)
        blue = toon('DreamMailbox', '#4F6FC9')
        box('DreamMail', (0.9, 0.9, 1.4), (9.5, 1.6, 1.3), blue, bevel=0.1)
        box('DreamMailLeg', (0.2, 0.2, 0.6), (9.5, 1.6, 0.3), metal)

        # cloud banks: around the chunk and stacked down the fall column
        cl = toon('DreamCloud', '#E9DDF2')
        cl2 = toon('DreamCloudPink', '#F2C6DD')
        for i in range(10):
            cloud(f'DreamCloudA{i}', (rnd.uniform(-30, 30), rnd.uniform(6, 30), rnd.uniform(-10, 6)),
                  rnd.uniform(1.2, 2.2), rnd.choice((cl, cl2)), rnd)
        for i in range(16):
            side = 1 if i % 2 else -1
            cloud(f'DreamCloudF{i}', (6 + side * rnd.uniform(4, 9), rnd.uniform(-4, 8), -8 - i * 4.2),
                  rnd.uniform(0.8, 1.5), rnd.choice((cl, cl2)), rnd)

        area_light((0, -14, 10), (55, 0, 0), 12, 1500, '#D9C8FF', 'DreamFront')
        area_light((10, 6, -30), (-30, 0, 0), 20, 3000, '#F7B8E0', 'DreamFallFill')
    return {'root': root, 'origin': origin}
