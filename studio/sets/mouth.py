"""Set: inside the mouth (a pink cave) + a pain-nerve tunnel next door.

Mouth (local x -8..8): cavity centred (0, 0, 5), radii (8, 11, 6). Tongue on the floor,
teeth rows near the front (y ~ -8), palate (roof) at z ~ 10.6 with blood vessels (red) and
nerves (yellow) running over it. Vessels are separate objects so they can shrink / bulge.

Nerve tunnel (local x = NX): a dark tube tunnel along +Y with a fat yellow nerve cable that
forks at y=FORK into a 'MOUTH' branch (down) and a 'FOREHEAD' branch (up). A glowing pulse
travels along it (animate PULSE location in the episode).
"""
import math
import random
from mathutils import Vector
from toon import toon, glassy, box, ellipsoid, cylinder, cone, tube, point_light, area_light, SetBuilder, text_obj, empty

C = Vector((0, 0, 5))
R = (8.0, 11.0, 6.0)
NX = 60.0
FORK = 14.0


def on_cavity(th, ph, inset=0.15):
    """Point on the inside of the cavity (th from the top, ph around Z)."""
    d = Vector((math.sin(th) * math.cos(ph), math.sin(th) * math.sin(ph), math.cos(th)))
    p = Vector((d.x * R[0], d.y * R[1], d.z * R[2]))
    return C + p * (1 - inset / R[2])


def ctube(name, pts, r, mat, outline=0.0):
    """Tube whose origin sits at its own middle, so it can shrink / bulge in place."""
    c = sum((Vector(p) for p in pts), Vector()) / len(pts)
    return tube(name, [tuple(Vector(p) - c) for p in pts], r, mat, outline=outline, loc=tuple(c))


def build(origin=(0, 0, 0)):
    rnd = random.Random(4)
    with SetBuilder('Mouth', origin) as root:
        gum = toon('MGum', '#E86A8A', tex=('stripes', '#DA5C7E', 0.9, 'z'))
        gum2 = toon('MGumDark', '#B8486A')
        tongue_m = toon('MTongue', '#F08AA0')
        tooth = toon('MTooth', '#FFFDF4')
        vessel = toon('MVessel', '#D3263C')
        nerve = toon('MNerve', '#F6D04D')
        throat = toon('MThroat', '#3A0F22', emit=True)

        cav = ellipsoid('MCavity', R, tuple(C), gum, segs=64, rings=32)
        # palate ridges (rugae) on the roof
        for k in range(5):
            th = 0.25 + 0.12 * k
            pts = [on_cavity(th, -math.pi / 2 + a, 0.25) for a in (-0.9, -0.45, 0.0, 0.45, 0.9)]
            tube('MRuga', [tuple(p) for p in pts], 0.12, gum2)
        # throat at the back, uvula
        ellipsoid('MThroatHole', (2.4, 0.4, 2.6), (0, 10.6, 5.0), throat)
        u = ellipsoid('MUvula', (0.5, 0.5, 1.2), (0, 9.6, 8.6), gum2, outline=0.03)
        # tongue
        tongue = empty('MTonguePivot', (0, 7.0, 1.6))
        ellipsoid('MTongueBody', (4.8, 8.5, 1.8), (0, -6.0, 0.4), tongue_m, tongue, outline=0.05, segs=48, rings=24)
        tube('MTongueGroove', [(0, -12.5, 2.1), (0, -6, 2.25), (0, 0.5, 1.7)], 0.08, gum2, tongue)
        # teeth: top and bottom rows along the front arc
        for row, z in (('T', 8.3), ('B', 1.9)):
            for i in range(10):
                a = math.radians(-60 + 120 * i / 9)
                x, y = 6.4 * math.sin(a), -8.0 * math.cos(a) + 0.2
                t = box(f'MTooth{row}', (1.0, 0.8, 1.5), (x, y, z), tooth, bevel=0.15)
                t.rotation_euler = (0, 0, a)
        # blood vessels over the roof: three big squiggly tubes + small branches
        vessels = []
        for k, ph0 in enumerate((-0.55, 0.0, 0.55)):
            pts = [tuple(on_cavity(0.15 + 0.17 * j, -math.pi / 2 + ph0 + 0.18 * math.sin(j * 1.7 + k), 0.3)) for j in range(7)]
            v = ctube(f'MVessel{k}', pts, 0.32, vessel, outline=0.03)
            vessels.append(v)
        for k in range(8):
            th = rnd.uniform(0.3, 1.0)
            ph = -math.pi / 2 + rnd.uniform(-0.9, 0.9)
            pts = [tuple(on_cavity(th + 0.08 * j, ph + 0.12 * j * (1 if k % 2 else -1), 0.3)) for j in range(4)]
            vessels.append(ctube(f'MVesselS{k}', pts, 0.14, vessel, outline=0.02))
        nerves = []
        for k, ph0 in enumerate((-0.3, 0.3)):
            pts = [tuple(on_cavity(0.2 + 0.18 * j, -math.pi / 2 + ph0 - 0.15 * math.cos(j), 0.34)) for j in range(6)]
            nerves.append(tube(f'MNerve{k}', pts, 0.16, nerve, outline=0.02))
        # cute face on the biggest vessel (eyes that can squeeze)
        mid = on_cavity(0.5, -math.pi / 2, 0.75)
        vface = empty('MVesselFace', tuple(mid))
        white = toon('FaceWhite', '#FFFFFF')
        ink = toon('Ink', '#2A2230')
        for s in (1, -1):
            e = ellipsoid(f'MVEye{s}', (0.32, 0.32, 0.12), (s * 0.45, 0, 0), white, vface, outline=0.03)
            ellipsoid(f'MVPupil{s}', (0.12, 0.12, 0.06), (0, 0, -0.1), ink, e)
        vface.rotation_euler = (math.radians(180), 0, 0)      # faces down toward the camera
        # mouth lighting: warm pink inner glow + light from the front (between the teeth)
        point_light((0, -3, 6), 1200, '#FFC2CF', 1.5, 'MInner')
        point_light((0, 4, 8), 500, '#FF9FB4', 1.0, 'MBack')
        area_light((0, -9.5, 5), (90, 0, 0), 4, 900, '#FFF4E8', 'MFrontGap')

        # ---------------- nerve tunnel ----------------
        dark = toon('NTunnel', '#6A4E9A', tex=('stripes', '#5C428A', 1.2, 'z'))
        tun = ellipsoid('NTunnelOb', (7, 30, 7), (NX, 12, 5), dark, segs=48, rings=24)
        main = tube('NMain', [(NX, -14, 2.5), (NX, 0, 3.0), (NX, FORK, 3.4)], 0.45, nerve, outline=0.04)
        up = tube('NUp', [(NX, FORK, 3.4), (NX + 1.5, FORK + 6, 7.5), (NX + 2.5, FORK + 14, 9.5)], 0.38, nerve, outline=0.04)
        down = tube('NDown', [(NX, FORK, 3.4), (NX - 1.5, FORK + 6, 1.4), (NX - 2.5, FORK + 14, 1.0)], 0.38, nerve,
                    outline=0.04)
        sign_m = toon('NSign', '#1E1730')
        yel = toon('PopYellow', '#FFD23F', emit=True)
        for nm, label, loc in (('NSignUp', 'FOREHEAD', (NX + 2.4, FORK + 10, 9.8)),
                               ('NSignDown', 'MOUTH', (NX - 2.4, FORK + 10, 3.6))):
            box(nm, (5.4, 0.2, 1.6), loc, sign_m, outline=0.03)
            text_obj(nm + 'Txt', label, 0.7, (loc[0], loc[1] - 0.14, loc[2] - 0.02), yel, extrude=0.02)
        pass
        pulse = empty('NPulse', (NX, -14, 2.5))
        ellipsoid('NPulseBall', (0.75, 0.75, 0.75), (0, 0, 0), glassy('NPulseGlow', '#FFF27A', alpha=1.0, emit_strength=6),
                  pulse, outline=0.03)
        pl = point_light((0, 0, 0), 900, '#FFE45C', 0.5, 'NPulseLight')
        pl.parent = pulse
        for i in range(14):      # little glowing specks on the tunnel wall
            a = rnd.uniform(0, 2 * math.pi)
            ellipsoid('NSpeck', (0.1, 0.1, 0.1), (NX + 6.3 * math.cos(a), rnd.uniform(-10, 30), 5 + 6.3 * math.sin(a)),
                      toon('NSpeckM', '#B79CFF', emit=True), segs=6, rings=3)
        area_light((NX, -16, 6), (90, 0, 0), 6, 3500, '#C9B4FF', 'NFront')
        point_light((NX, 20, 8), 2500, '#B79CFF', 2.0, 'NBack')
    return {'root': root, 'origin': origin, 'tongue': tongue, 'vessels': vessels, 'nerves': nerves,
            'vface': vface, 'pulse': pulse}
