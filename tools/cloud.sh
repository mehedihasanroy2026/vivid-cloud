#!/usr/bin/env bash
# Render a VIVID episode on free GitHub runners, then assemble it on the laptop with the voice (audio never leaves the laptop).
#   tools/cloud.sh <episode_dir> <NN> <Title_With_Underscores> [chunks=20] [pct=50]
# env: MAXF=N   test run, only N frames per shot (no assembly, just frames)
#      CAPS=1   burn word captions (captions.json) into the video
#      RUN=<id> skip push/trigger and just fetch + assemble an existing run
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"; LF="$(dirname "$REPO")"
EP="$1"; NN="$2"; TITLE="$3"; CH="${4:-20}"; PCT="${5:-50}"
[ -f "$REPO/studio/episodes/$EP/build.py" ] || { echo "no studio/episodes/$EP/build.py"; exit 1; }
R="$LF/renders/${EP}_pct$PCT"
cd "$REPO"

if [ -z "$RUN" ]; then
  git add -A studio tools .github .gitignore
  git diff --cached --quiet || git commit -qm "episode $EP" && true
  git push -q
  BEFORE=$(gh run list --workflow render.yml --limit 1 --json databaseId --jq '.[0].databaseId // 0')
  gh workflow run render.yml -f ep="$EP" -f chunks="$CH" -f pct="$PCT" -f wide=1 -f maxf="${MAXF:-}"
  for i in $(seq 30); do
    RUN=$(gh run list --workflow render.yml --limit 1 --json databaseId --jq '.[0].databaseId')
    [ "$RUN" != "$BEFORE" ] && break; sleep 4
  done
  echo "run $RUN: https://github.com/$(gh repo view --json nameWithOwner --jq .nameWithOwner)/actions/runs/$RUN"
  if ! gh run watch "$RUN" --exit-status --interval 60 > /dev/null; then
    echo "RUN FAILED. See the link above. Retry the failed chunks with: gh run rerun $RUN --failed, then RUN=$RUN $0 $*"
    exit 1
  fi
fi

echo "downloading..."
rm -rf "$R/dl" "$R/shots" "$R/frames"; mkdir -p "$R/dl" "$R/shots"
gh run download "$RUN" -D "$R/dl"
for c in "$R"/dl/chunk-*; do
  cp "$c/plan.json" "$R/shots/plan.json"
  [ -f "$c/starts.txt" ] || continue
  while read -r name start; do
    mkdir -p "$R/shots/$name"
    ffmpeg -v error -y -i "$c/$name.mp4" -start_number "$start" "$R/shots/$name/f_%05d.png"
  done < <(tr -d '\r' < "$c/starts.txt")
done
echo "$(find "$R/shots" -name '*.png' | wc -l) frames in $R/shots"
[ -n "$MAXF" ] && { echo "test run (MAXF): frames only, no assembly"; exit 0; }

python "$REPO/tools/dissolve.py" --root "$R" --out "$R/frames"
cd "$REPO/studio/episodes/$EP"
ARGS=(--shots "$R/frames" --wide --out "$LF/renders/LF${NN}_${TITLE}.mp4")
[ -f mix.wav ] && ARGS+=(--audio mix.wav) || echo "WARNING: no mix.wav, video will be silent"
[ "$CAPS" = 1 ] && ARGS+=(--captions captions.json)
python "$REPO/tools/assemble.py" "${ARGS[@]}"
echo DONE "$LF/renders/LF${NN}_${TITLE}.mp4"
