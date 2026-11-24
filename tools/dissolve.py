"""Join per-shot renders into one frame sequence with Ricks-style dissolves instead of hard cuts.

ep_common.render with HANDLE > 0 writes <root>/shots/NN_name/f_#####.png + <root>/shots/plan.json.
Inside one set a shot renders a few extra tail frames, so the dissolve blends two moving shots;
across sets it fades out of the outgoing shot's last frame. plan[i]['trans'] = dissolve frames into shot i (0 = cut).

    python tools/dissolve.py --root ../renders/ep11v/ --out ../renders/ep11v/frames
"""
import os
import json
import argparse
import numpy as np
from PIL import Image


def load(p):
    return np.asarray(Image.open(p).convert('RGB'), dtype=np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    sd = os.path.join(a.root, 'shots')
    plan = json.load(open(os.path.join(sd, 'plan.json')))
    os.makedirs(a.out, exist_ok=True)
    fr = lambda shot, f: os.path.join(sd, shot['dir'], f'f_{f:05d}.png')
    n = 0
    for i, s in enumerate(plan):
        prev = plan[i - 1] if i else None
        H = s['trans'] if prev else 0
        for f in range(s['f0'], s['f1'] + 1):
            dst = os.path.join(a.out, f'f_{f:05d}.png')
            src = fr(s, f)
            if not os.path.exists(src):
                raise SystemExit(f'missing {src}')
            k = f - s['f0']
            if H and k < H:
                pa = fr(prev, f)
                if not os.path.exists(pa):
                    pa = fr(prev, prev['f1'])          # across sets: fade out of the last frame
                x = (k + 1) / (H + 1)
                x = x * x * (3 - 2 * x)                # smoothstep
                img = load(pa) * (1 - x) + load(src) * x
                Image.fromarray(np.clip(img + 0.5, 0, 255).astype(np.uint8)).save(dst)
            else:
                if os.path.exists(dst):
                    os.remove(dst)
                try:
                    os.link(src, dst)
                except OSError:
                    Image.open(src).save(dst)
            n += 1
    print(f'{n} frames -> {a.out}')


if __name__ == '__main__':
    main()
