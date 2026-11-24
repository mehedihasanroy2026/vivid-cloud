"""Shared machinery for real-light episodes (from EP08): word timing, cast helpers, camera shots, render loop.

    import ep_common as E
    E.init(here_dir, args)            # loads words.json, sets up the real-light render
    E.T = [...]; E.make_S()           # timeline
    rig = E.person('Leo', loc, look); E.face(rig, t, 'happy'); ...
    E.shot('name', origin, loc, target, lens, ...)
    E.render(args, set_names)         # set i lives at x = 300 * i
"""
import os
import re
import json
import math
import random
import bpy
from mathutils import Vector, Quaternion

import real
from toon import camera, dof, empty, ellipsoid, tube, box, cylinder, cone
from acting import F, deg, W, A, shake, _fcurves, ranges_visible, _linear
import doodle_char as dc

WORDS, NW, END_T, T, S = [], [], 0.0, [], {}
RIGS, FACES, cams, RIG = [], {}, {}, {}
rnd = random.Random(99)
sc = None


def init(here, args):
    global WORDS, NW, END_T, sc
    wpath = os.path.join(here, 'words.json')
    if not os.path.exists(wpath):
        raise SystemExit('No words.json yet: waiting for the voiceover.mp3 from ElevenLabs.')
    WORDS = json.load(open(wpath))
    NW = [re.sub(r'[^a-z0-9]', '', w['word'].lower()) for w in WORDS]
    END_T = WORDS[-1]['end'] + 0.7
    real.setup(args.pct, args.samples, sky='#9FB6CC', sky_strength=0.2)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, F(END_T)


def at(phrase, after=0.0, end=False):
    p = [re.sub(r'[^a-z0-9]', '', x.lower()) for x in phrase.split()]
    for i in range(len(NW) - len(p) + 1):
        if NW[i:i + len(p)] == p and WORDS[i]['start'] >= after - 1e-6:
            return WORDS[i + len(p) - 1]['end'] if end else WORDS[i]['start']
    raise KeyError(phrase)


def make_S(timeline):
    """timeline = [(name, phrase or None)]; each shot cuts 0.08 s before its word"""
    global T, S
    T = [(n, 0.0 if p is None else max(0.0, at(p) - 0.08)) for n, p in timeline]
    S = {n: (t, T[i + 1][1] if i + 1 < len(T) else END_T) for i, (n, t) in enumerate(T)}
    for n, (a, b) in S.items():
        print(f'  {n:10s} {a:6.2f} - {b:6.2f}  ({b - a:.2f}s)')
    return S


# ---------------------------------------------------------------- cast
def face(rig, t, which):
    dc.set_expression(rig, which, frame=F(t))
    FACES.setdefault(rig['mover'].name, []).append((t, which))


def person(name, loc, look, rot=0):
    rig = dc.build(name, loc, look)
    rig['mover'].rotation_euler = deg(0, 0, rot)
    RIGS.append(rig)
    face(rig, 0, 'neutral')
    return rig


def arms(rig, t, l, r, jump=False):
    f = A.jump if jump else A.set
    f(rig['shoulderL'], 'rotation_euler', t, deg(*l))
    f(rig['shoulderR'], 'rotation_euler', t, deg(*r))


def legs(rig, t, l, r, jump=False):
    f = A.jump if jump else A.set
    f(rig['hipL'], 'rotation_euler', t, deg(*l))
    f(rig['hipR'], 'rotation_euler', t, deg(*r))


def place(rig, t, loc, rot=None, tilt=None):
    A.jump(rig['mover'], 'location', t, loc)
    if rot is not None:
        A.jump(rig['mover'], 'rotation_euler', t, deg(tilt[0] if tilt else 0, tilt[1] if tilt else 0, rot))


def neck(rig, t, x=0, y=0, z=0, jump=False):
    (A.jump if jump else A.set)(rig['neck'], 'rotation_euler', t, deg(x, y, z))


def lean(rig, t, x=0, y=0, jump=False):
    (A.jump if jump else A.set)(rig['root'], 'rotation_euler', t, deg(x, y, 0))


def hold(rig, side, ob, loc=(0, -0.12, -0.15), rot=(0, 0, 0)):
    s = 1 if side == 'L' else -1
    ob.parent = rig['shoulder' + side]
    ob.location = (s * 0.27 + loc[0], -0.06 + loc[1], -1.38 + loc[2])
    ob.rotation_euler = deg(*rot)
    return ob


def sit(rig, t, loc, rot=0):
    """seated pose: loc = seat surface point under the hips (world)"""
    place(rig, t, (loc[0], loc[1], loc[2] - 2.45), rot)
    legs(rig, t, (-88, 0, 0), (-88, 0, 0), jump=True)


def stand(rig, t, loc, rot=0):
    place(rig, t, loc, rot)
    legs(rig, t, (0, 0, 0), (0, 0, 0), jump=True)
    lean(rig, t, 0, 0, jump=True)


def show(objs, ranges):
    ranges_visible(objs, ranges)


def head_pt(theta, phi, lift=0.0):
    return dc.surf(theta, phi, lift)[0]


TEARM = None


def tears(rig, name, big=False):
    global TEARM
    TEARM = TEARM or real.mat('Tear', '#8FD6FF', 'plastic', grime=0, rough=0.05, emit=0.4)
    out = []
    for s in (1, -1):
        phi = dc.FRONT + s * 0.3
        pts = [head_pt(1.5, phi, 0.05), head_pt(1.75, phi + s * 0.06, 0.05), head_pt(2.05, phi + s * 0.1, 0.05), head_pt(2.3, phi + s * 0.12, 0.05)]
        out.append(tube(f'{name}Stream{s}', pts, 0.07 if big else 0.055, TEARM, rig['head']))
    return out


def sweat(rig, name):
    m = real.mat('SweatDrop', '#9ED8FF', 'plastic', grime=0, rough=0.05)
    return [ellipsoid(name + 'Sweat', (0.12, 0.08, 0.18), (0.75, -0.6, 0.55), m, rig['head'])]


def blinks():
    NOBLINK = {'blink', 'sleep', 'happy', 'shocked', 'excited', 'grimace', 'wince', 'dizzy', 'yawn', 'proud'}
    for rg in RIGS:
        lst = sorted(FACES.get(rg['mover'].name, []))
        t = rnd.uniform(0.8, 2.5)
        while t < END_T - 0.3:
            cur = [w for tt, w in lst if tt <= t]
            nxt = [tt for tt, w in lst if tt > t]
            if cur and cur[-1] not in NOBLINK and (not nxt or nxt[0] - t > 0.3):
                dc.set_expression(rg, 'blink', frame=F(t))
                dc.set_expression(rg, cur[-1], frame=F(t + 0.1))
            t += rnd.uniform(2.0, 3.5)


# ---------------------------------------------------------------- small props
INK = None


def ink():
    global INK
    INK = INK or real.mat('PropInk', '#25303D', 'paint', grime=0)
    return INK


def phone(name, screen_hex='#7FD0FF'):
    p = empty(name)
    box(name + 'Body', (0.42, 0.06, 0.8), (0, 0, 0), real.mat('PhoneBody', '#22252E', 'plastic', grime=0.05, rough=0.3), p, outline=0.015)
    box(name + 'Screen', (0.36, 0.02, 0.7), (0, -0.035, 0), real.mat('PhoneScr' + screen_hex, screen_hex, 'glow', emit=2.5), p)
    return p


def sparkles(name, center, t0, t1, n=4, r=0.6, hexc='#FFF6B0', size=0.06):
    m = real.mat('Spark' + hexc, hexc, 'glow', emit=10.0)
    out = []
    for i in range(n):
        s = ellipsoid(f'{name}{i}', (size, size, size), (center[0] + r * math.cos(i * 1.7), center[1], center[2] + r * math.sin(i * 2.3)), m)
        t = t0 + i * 0.12
        while t < t1:
            A.set(s, 'scale', t, (0.001,) * 3)
            A.set(s, 'scale', t + 0.15, (1.6, 1.6, 1.6))
            A.set(s, 'scale', t + 0.3, (0.001,) * 3)
            t += 0.5
        out.append(s)
    show(out, [(t0, t1)])
    return out


def light_key(light, keys):
    """keys = [(t, energy)]; holds the first value before it"""
    for t, e in keys:
        light.data.energy = e
        light.data.keyframe_insert('energy', frame=F(t))


# ---------------------------------------------------------------- cameras
def handheld(ob, strength=0.04, scale=30.0):
    ob.keyframe_insert('location', frame=1)
    for fc in _fcurves(ob):
        if fc.data_path == 'location':
            mod = fc.modifiers.new('NOISE')
            mod.strength = strength
            mod.scale = scale
            mod.phase = rnd.random() * 100


def shot(name, origin, loc, target, lens=28, focus=None, fstop=2.0, move=None, tmove=None, roll=0.0, roll_to=None,
         zoom=(), shakes=(), top=False, hand=0.04, fly=None, fly_t=0.45, orbit=0.0, push=0.0, path=None, tpath=None,
         whip=None, whip_t=0.2, min_d=3.0):
    """fly=(dx, dy, dz): the camera arrives from loc+fly and settles on loc in fly_t s (Ricks' ease-out bursts),
    then creeps on to `move` if given."""
    t0, t1 = S[name]
    moving = bool(move or tmove or orbit or push or path or tpath or fly or zoom)
    if AUTO and not moving and not top:
        # never a dead hold (Ricks): slow orbit + push-in, alternating direction
        orbit = (1 if len(cams) % 2 else -1) * AUTO_ORBIT
        push = AUTO_PUSH
    if ENERGY != 1.0:
        # one knob for camera energy: scales orbits, pushes, moves, swoops and handheld
        orbit *= ENERGY
        push = min(0.5, push * ENERGY)
        if move:
            move = tuple(l + (m - l) * ENERGY for l, m in zip(loc, move))
        if path:
            p0 = path[0][1]
            path = [(u, tuple(a0 + (q - a0) * ENERGY for a0, q in zip(p0, p))) for u, p in path]
        hand *= ENERGY ** 0.5
    rig = empty(name + 'Rig', origin)
    drift = empty(name + 'Drift', (0, 0, 0), rig)
    shk = empty(name + 'Shake', (0, 0, 0), drift)
    cam, tgt = camera(W(origin, loc), W(origin, target), lens, name)
    cam.parent = shk
    cam.location = loc
    tgt.parent = rig
    tgt.location = target
    con = cam.constraints[0]
    con.use_target_z = True
    view = Vector(target) - Vector(loc)

    def tgt_rot(r):
        if top:
            return deg(-90, 0, -r)
        up = Quaternion(view.normalized(), math.radians(r)) @ Vector((0, 0, 1))
        return tuple(up.to_track_quat('Z', 'Y').to_euler())
    A.set(tgt, 'rotation_euler', t0, tgt_rot(roll))
    if roll_to is not None:
        A.set(tgt, 'rotation_euler', t1, tgt_rot(roll_to))
    if focus is not None:
        dof(cam, focus, fstop)
    if orbit or push:
        # circle the camera around the target by `orbit` degrees and move `push` (0..1) of the way in, over the shot
        tv = Vector(target)
        rel = Vector(loc) - tv
        path = []
        for k in range(5):
            u = k / 4
            q = Quaternion((0, 0, 1), math.radians(orbit * u))
            r = q @ rel
            r.xy *= (1 - push * u)
            path.append((u, tuple(tv + r)))
    if path:
        for u, p in path:
            A.set(cam, 'location', t0 + (t1 - t0) * u, p)
        if fly:
            A.set(cam, 'location', t0, tuple(l + d for l, d in zip(path[0][1], fly)))
    if tpath:
        for u, p in tpath:
            A.set(tgt, 'location', t0 + (t1 - t0) * u, p)
    if path:
        pass
    elif fly:
        A.set(cam, 'location', t0, tuple(l + d for l, d in zip(loc, fly)))
        A.set(cam, 'location', min(t0 + fly_t, (t0 + t1) / 2), loc)
        if move:
            A.set(cam, 'location', t1, move)
    elif move:
        A.set(cam, 'location', t0, loc)
        A.set(cam, 'location', t1, move)
    if tmove:
        A.set(tgt, 'location', t0, target)
        A.set(tgt, 'location', t1, tmove)
    if whip:
        # fast whip-pan out: the aim snaps sideways in the last whip_t seconds (motion blur does the rest)
        end = tuple(tpath[-1][1]) if tpath else (tuple(tmove) if tmove else tuple(target))
        A.set(tgt, 'location', t1 - whip_t, end)
        A.set(tgt, 'location', t1, tuple(e + w for e, w in zip(end, whip)))
    if zoom:
        A.set(cam.data, 'lens', t0, lens)
        for tz, lz in zoom:
            A.set(cam.data, 'lens', tz, lz)
    if hand:
        handheld(drift, hand)
    for ts, amp in shakes:
        shake(shk, ts, ts + 0.35, amp, seed=int(ts * 10))
    cams[name] = cam
    RIG[name] = rig
    META[name] = {'tgt': tgt, 'fly': bool(fly), 'top': top, 'min_d': min_d}
    sc.timeline_markers.new(name, frame=F(t0)).camera = cam
    return cam, tgt


def flashes(times):
    sc.view_settings.exposure = 0.0
    sc.view_settings.keyframe_insert('exposure', frame=1)
    for tf in times:
        f = F(tf)
        for df, v in ((-1, 0.0), (0, 1.6), (1, 0.7), (2, 0.0)):
            sc.view_settings.exposure = v
            sc.view_settings.keyframe_insert('exposure', frame=f + df)


def hide_named(prefixes):
    for ob in list(bpy.data.objects):
        if ob.name.startswith(tuple(prefixes)) or (ob.parent and ob.parent.name.startswith(tuple(prefixes))):
            ob.hide_render = True


# ---------------------------------------------------------------- render
AUTO = True         # shots without any camera move get a gentle orbit + push (no dead holds)
ENERGY = 2.0        # camera energy multiplier. 2.0 = EP17+ default (EP16 test: QA MOTION 0.008 -> 0.014; 2.5 dove through heads)
AUTO_ORBIT, AUTO_PUSH = 22.0, 0.22
DIVE, EMERGE = 0.45, 0.5     # fly-through between places: dive this fraction toward the subject / burst out from it
DIVE_T, EMERGE_T = 0.3, 0.4
META = {}


def _at(ob, path, t):
    """value of an animated (or static) vector property at time t"""
    f = F(t)
    ad = ob.animation_data
    out = list(getattr(ob, path))
    if ad and ad.action:
        for fc in _fcurves(ob):
            if fc.data_path == path:
                out[fc.array_index] = fc.evaluate(f)
    return Vector(out)


def fly_throughs(set_of):
    """Ricks-style place changes: the outgoing shot dives into its subject, the incoming shot bursts out of a close-up.
    Keeps min_d away from the aim point so the camera never enters a head."""
    names = [n for n, _ in T]
    for i, n in enumerate(names):
        cam, m = cams[n], META[n]
        if m['top']:
            continue
        t0, t1 = S[n]
        if DIVE and i + 1 < len(names) and set_of[names[i + 1]] != set_of[n] and t1 - t0 > 0.9:
            ta = t1 - DIVE_T
            L, Tg = _at(cam, 'location', ta), _at(m['tgt'], 'location', ta)
            d = (L - Tg).length
            k = max(1 - DIVE, m['min_d'] / d) if d > 0 else 1
            A.set(cam, 'location', ta, tuple(L))
            A.set(cam, 'location', t1 - 1 / 30, tuple(Tg + (L - Tg) * k))
        if EMERGE and i > 0 and set_of[names[i - 1]] != set_of[n] and not m['fly'] and t1 - t0 > 0.9:
            tb = t0 + EMERGE_T
            L, Tg = _at(cam, 'location', tb), _at(m['tgt'], 'location', t0)
            L0 = _at(cam, 'location', t0)
            d = (L0 - Tg).length
            k = max(1 - EMERGE, m['min_d'] / d) if d > 0 else 1
            A.set(cam, 'location', tb, tuple(L))
            A.set(cam, 'location', t0, tuple(Tg + (L0 - Tg) * k))


HOOKS = {}      # set name -> fn() run before that set's shots render (e.g. vivid.sky per set)
HANDLE = 0      # >0: each shot renders this many extra tail frames into its own folder (tools/dissolve.py blends them)
TRANS = {}      # shot name -> dissolve length (frames) INTO that shot; 0 = hard cut. default: 8 across sets, 4 inside


def render(args, sets, finish=None, glow=0.35):
    blinks()
    set_of = {n: sets[int(round(RIG[n].location.x / 300.0))] for n, _ in T}
    fly_throughs(set_of)
    for rg in RIGS:
        real.glow_chars(rg, glow)
    bpy.context.view_layer.update()
    colls = {}
    for nm in sets:
        c = bpy.data.collections.new('C_' + nm)
        sc.collection.children.link(c)
        colls[nm] = c
    for o in list(sc.collection.objects):
        idx = min(max(int(round(o.matrix_world.translation.x / 300.0)), 0), len(sets) - 1)
        colls[sets[idx]].objects.link(o)
        sc.collection.objects.unlink(o)
    # characters travel between sets: link every rig (and what it carries) into every set's collection
    for rg in RIGS:
        for o in [rg['mover']] + list(rg['mover'].children_recursive):
            for c in colls.values():
                if c not in o.users_collection:
                    c.objects.link(o)
    (finish or real.finish)()

    def only_set(nm):
        for k in colls:
            bpy.context.view_layer.layer_collection.children['C_' + k].exclude = (k != nm)
        if nm in HOOKS:
            HOOKS[nm]()
    sc.render.use_overwrite = False
    sc.render.use_placeholder = True
    if args.mode == 'still':
        base, ext = os.path.splitext(args.out)
        sc.render.use_overwrite = True
        times = list(args.t)
        if args.shots:
            names = args.shots if args.shots != ['all'] else [n for n, _ in T]
            times = [(S[n][0] + S[n][1]) / 2 for n in names]
        for t in times:
            nm = [n for n, t0 in T if t0 <= t][-1]
            only_set(set_of[nm])
            sc.camera = cams[nm]
            sc.frame_set(F(t))
            sc.render.filepath = f'{base}_{t:05.2f}_{nm}{ext or ".png"}'
            bpy.ops.render.render(write_still=True)
    else:
        plan = []
        for i, (n, t0) in enumerate(T):
            t1 = S[n][1]
            f0, f1 = F(t0), (F(t1) - 1 if n != T[-1][0] else F(END_T))
            prev = set_of[T[i - 1][0]] if i else None
            tr = TRANS.get(n, 0 if i == 0 else (8 if prev != set_of[n] else 4))
            plan.append(dict(name=n, f0=f0, f1=f1, set=set_of[n], trans=tr, dir=f'{i:02d}_{n}'))
        if HANDLE:
            root = os.path.dirname(os.path.dirname(os.path.abspath(args.out)))
            os.makedirs(os.path.join(root, 'shots'), exist_ok=True)
            json.dump(plan, open(os.path.join(root, 'shots', 'plan.json'), 'w'), indent=1)
            for mk in sc.timeline_markers:      # the camera is set per shot here; markers would switch it in the tails
                mk.camera = None
        for i, (n, t0) in enumerate(T):
            if args.only and n not in args.only:
                continue
            f0, f1 = plan[i]['f0'], plan[i]['f1']
            only_set(set_of[n])
            sc.camera = cams[n]
            if HANDLE:
                # tails only inside one set (characters keep acting); across sets dissolve.py fades from the last frame
                nxt = plan[i + 1]['trans'] if i + 1 < len(plan) and plan[i + 1]['set'] == plan[i]['set'] else 0
                f1 = f1 + nxt
                sc.render.filepath = os.path.join(root, 'shots', plan[i]['dir'], 'f_#####')
            else:
                sc.render.filepath = os.path.abspath(args.out)
            sc.frame_start, sc.frame_end = f0, f1
            if os.environ.get('MAXF'):   # cloud speed test: only the first MAXF frames
                sc.frame_end = min(f1, f0 + int(os.environ['MAXF']) - 1)
            print(f'### shot {n}: frames {f0}-{f1}', flush=True)
            bpy.ops.render.render(animation=True)


def std_args():
    import sys
    import argparse
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--mode', default='still')
    ap.add_argument('--t', type=float, nargs='*', default=[1.0])
    ap.add_argument('--shots', nargs='*', default=None)
    ap.add_argument('--only', nargs='*', default=None)
    ap.add_argument('--pct', type=int, default=50)
    ap.add_argument('--samples', type=int, default=8)
    ap.add_argument('--out', required=True)
    return ap.parse_args(argv)
