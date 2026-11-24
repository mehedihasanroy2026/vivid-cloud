"""Turn rendered shots into a finished video (1080x1920 Short, or 1920x1080 with --wide).

  python assemble.py --shots <dir1> <dir2> ... --captions caps.json --out video.mp4
                     [--audio voice.wav] [--xfade 0.3] [--no-look]

Each shot folder holds that shot's PNG frames (ordered by the number at the end
of the name). Shots are joined with a quick dissolve, then the 'look' is applied
(soft glow, a little extra colour, vignette) and word captions pop in.

captions.json: [{"word": "Meet", "start": 0.3, "end": 0.8}, ...]   (seconds)
"""
import argparse
import json
import os
import re
import subprocess
import tempfile

FONT = 'C\\:/Windows/Fonts/ariblk.ttf'   # Arial Black (escaped for ffmpeg)
FPS = 30
SIZE = '1080:1920'    # --wide -> 1920:1080 (long form)
CAP = 80
CAPY = 0.70


def esc(text):
    return (text.replace('\\', '\\\\').replace("'", '’').replace(':', '\\:')
            .replace(',', '\\,').replace('%', '\\%'))


def frames_of(folder):
    files = [f for f in os.listdir(folder) if f.lower().endswith('.png')]
    return sorted(files, key=lambda f: int(re.findall(r'(\d+)\.png$', f, re.I)[0]))


def encode_shot(folder, out):
    files = frames_of(folder)
    lst = tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False)
    for f in files:
        p = os.path.abspath(os.path.join(folder, f)).replace('\\', '/')
        lst.write(f"file '{p}'\nduration {1 / FPS:.6f}\n")
    lst.close()
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst.name,
                    '-r', str(FPS), '-vf', f'scale={SIZE}:flags=lanczos',   # mixed render sizes -> full size
                    '-c:v', 'libx264', '-crf', '10', '-preset', 'fast',
                    '-pix_fmt', 'yuv420p', out], check=True)
    os.unlink(lst.name)
    return len(files) / FPS


def caption_filters(caps):
    out = []
    CAPY_ = CAPY
    for c in caps:
        st, en = c['start'], c['end']
        base = min(CAP, int(CAP * 13 / max(13, len(c['word']))))     # long words shrink to fit
        # pops in 18% bigger and settles over 0.12 s
        size = f"{base}*(1+0.18*max(0\\,1-(t-{st})/0.12))"
        out.append(
            f"drawtext=fontfile='{FONT}':text='{esc(c['word'])}':fontsize='{size}':fontcolor=white"
            f":borderw=6:bordercolor=0x1a1a1a:shadowx=0:shadowy=5:shadowcolor=black@0.45"
            f":x=(w-text_w)/2:y=h*{CAPY_}-text_h/2:enable='between(t\\,{st}\\,{en})'")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--shots', nargs='+', required=True)
    ap.add_argument('--captions')
    ap.add_argument('--audio')
    ap.add_argument('--out', required=True)
    ap.add_argument('--xfade', type=float, default=0.3)
    ap.add_argument('--no-look', action='store_true')
    ap.add_argument('--wide', action='store_true', help='1920x1080 long form, smaller captions low in frame')
    ap.add_argument('--grade', default='clean', choices=['clean', 'warm'], help='clean = Ricks-style restrained colour')
    a = ap.parse_args()
    global SIZE, CAP, CAPY
    if a.wide:
        SIZE, CAP, CAPY = '1920:1080', 64, 0.86

    tmp = tempfile.mkdtemp()
    clips, lens = [], []
    for i, s in enumerate(a.shots):
        p = os.path.join(tmp, f'shot{i}.mp4')
        lens.append(encode_shot(s, p))
        clips.append(p)

    cmd = ['ffmpeg', '-y', '-v', 'error']
    for c in clips:
        cmd += ['-i', c]
    if a.audio:
        cmd += ['-i', a.audio]

    # chain the shots with dissolves
    parts, last, t = [], '[0:v]', lens[0]
    for i in range(1, len(clips)):
        off = t - a.xfade
        parts.append(f"{last}[{i}:v]xfade=transition=fade:duration={a.xfade}:offset={off:.3f}[x{i}]")
        last = f'[x{i}]'
        t = off + lens[i]

    look = []
    if not a.no_look:
        # glow must be blended in RGB, otherwise colours shift purple
        parts.append(f"{last}format=gbrp,split[base][glowsrc]")
        parts.append("[glowsrc]gblur=sigma=24[glow]")
        parts.append("[base][glow]blend=all_mode=screen:all_opacity=0.16[bloomed]")
        last = '[bloomed]'
        # grade: gentle S-curve, vibrance, warm highlights / cool shadows, sharpen, vignette
        if a.grade == 'warm':
            look = ["curves=master='0/0 0.22/0.19 0.6/0.64 1/1'",
                    'vibrance=intensity=0.28',
                    'colorbalance=rs=-0.02:bs=0.04:rh=0.04:gh=0.01:bh=-0.03',
                    'cas=strength=0.35',
                    'vignette=angle=PI/6']
        else:       # clean: gentle contrast, no extra saturation, light vignette
            look = ["curves=master='0/0 0.25/0.23 0.75/0.78 1/1'",
                    'vibrance=intensity=0.05',
                    'cas=strength=0.25',
                    'vignette=angle=PI/8']
    caps = caption_filters(json.load(open(a.captions, encoding='utf-8'))) if a.captions else []
    parts.append(f"{last}" + ','.join(look + caps + ['format=yuv420p']) + '[v]')

    # the filter graph goes in a file: long caption lists overflow the Windows command line
    fg = tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False, encoding='utf-8')
    fg.write(';\n'.join(parts))
    fg.close()
    cmd += ['-/filter_complex', fg.name, '-map', '[v]']
    if a.audio:
        cmd += ['-map', f'{len(clips)}:a', '-c:a', 'aac', '-b:a', '192k', '-shortest']
    cmd += ['-r', str(FPS), '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
            '-movflags', '+faststart', a.out]
    subprocess.run(cmd, check=True)
    print(f'Wrote {a.out}  ({t:.2f}s)')


if __name__ == '__main__':
    main()
