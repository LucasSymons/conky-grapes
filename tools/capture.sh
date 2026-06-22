#!/usr/bin/env bash
#
# capture.sh - screenshot the live conky overlay and crop to a section.
#
# Why this exists:
#   conky-grapes renders onto the live desktop. Tuning text-vs-ring alignment
#   used to mean taking screenshots by hand and sending them over. This script
#   removes that step: it grabs the whole desktop with spectacle (the only
#   screenshot tool that sees the KDE/Wayland compositor here - the X11 tools
#   like `import`/`xwininfo` cannot), then crops to the conky window or a named
#   section, upscaling so the text and arcs are legible.
#
# Usage:
#   tools/capture.sh [section] [zoom%]
#     section : full cpu iowait memory filesystem internet clock os  (default: full)
#     zoom%   : integer resize percent                               (default: 300, full: 180)
#
# Output: /tmp/conky_<section>.png  (path is printed on success)
#
# Geometry source of truth (conky_gen.conkyrc / conky_tpl):
#   minimum/maximum_width = 520, minimum_height = 600
#   alignment = top_right, gap_x = 20, gap_y = 112, xinerama_head = 3
#
#   The conky window's RIGHT edge sits at  (desktop_width - gap_x).
#   desktop_width is read from the screenshot at runtime, so this keeps working
#   if the resolution changes. This assumes head 3 is the right-most monitor and
#   its right edge is the canvas right edge - true on Lucas's 6000px layout.
#
# Section boxes below are in CONKY-LOCAL pixels (origin = top-left of the conky
# window). Tweak them if a section drifts out of frame - they are deliberately
# generous.
#
set -euo pipefail

# --- conky window geometry (must match conky_tpl / conky_gen.conkyrc) ---------
readonly GAP_X=20
readonly GAP_Y=112
readonly CONKY_W=520
readonly CONKY_H=600

# --- section presets: "local_x local_y w h" ----------------------------------
declare -A SECTION=(
  [full]="0 0 ${CONKY_W} ${CONKY_H}"
  [cpu]="20 0 300 200"
  [iowait]="300 20 220 180"
  [memory]="290 170 230 150"
  [filesystem]="20 190 320 130"
  [internet]="280 290 240 140"
  [clock]="180 300 260 130"
  [os]="120 540 320 60"
)

section="${1:-full}"
if [[ -z "${SECTION[$section]:-}" ]]; then
  echo "unknown section '$section'. valid: ${!SECTION[*]}" >&2
  exit 2
fi

# default zoom: full overview at 180%, sections at 300%
if [[ -n "${2:-}" ]]; then
  zoom="$2"
elif [[ "$section" == "full" ]]; then
  zoom=180
else
  zoom=300
fi

shot="/tmp/conky_full_$$.png"
out="/tmp/conky_${section}.png"

command -v spectacle >/dev/null || { echo "spectacle not found" >&2; exit 1; }
command -v magick    >/dev/null || { echo "imagemagick (magick) not found" >&2; exit 1; }

# 1. grab the whole desktop (non-interactive, no notification, no cursor)
spectacle -b -n -f -o "$shot" >/dev/null 2>&1
sleep 1
[[ -s "$shot" ]] || { echo "capture failed (empty file)" >&2; exit 1; }

# 2. derive conky window origin from the canvas width
width=$(magick identify -format '%w' "$shot")
conky_left=$(( width - GAP_X - CONKY_W ))
conky_top=$GAP_Y

# 3. crop to the requested section (convert local box -> screen box) and zoom
read -r lx ly lw lh <<<"${SECTION[$section]}"
sx=$(( conky_left + lx ))
sy=$(( conky_top + ly ))
magick "$shot" -crop "${lw}x${lh}+${sx}+${sy}" +repage -resize "${zoom}%" "$out"
rm -f "$shot"

echo "$out"
