#!/usr/bin/env bash
#
# deploy.sh - push the generated config to the live ~/.conky dir and restart conky.
#
# The live overlay reads from ~/.conky/conky-grapes/ (a COPY of this repo, not a
# symlink). conky is launched at login from ~/.config/autostart/conky.desktop.
# This script mirrors that launch command so iterating matches real startup.
#
# Usage: tools/deploy.sh
#
set -euo pipefail

readonly REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly LIVE_DIR="$HOME/.conky/conky-grapes"
readonly RC="$LIVE_DIR/conky_gen.conkyrc"

[[ -d "$LIVE_DIR" ]] || { echo "live dir not found: $LIVE_DIR" >&2; exit 1; }

# Copy the runtime artifacts (generated rc + lua). Source of truth for the
# layout is create_config.py; conky_gen.conkyrc / rings-v2_gen.lua are generated.
cp -f "$REPO_DIR/conky_gen.conkyrc" "$LIVE_DIR/conky_gen.conkyrc"
cp -f "$REPO_DIR/rings-v2_gen.lua"  "$LIVE_DIR/rings-v2_gen.lua"

# Restart the daemon. (--pause=5 in autostart only delays first draw at login;
# omitted here so the overlay reappears fast during iteration.)
pkill -x conky 2>/dev/null || true
sleep 1
/usr/bin/conky --daemonize -q -m 1 -c "$RC" >/tmp/conky_run.log 2>&1
sleep 3   # allow conky to take samples before the first capture

pgrep -x conky >/dev/null && echo "conky restarted (pid $(pgrep -x conky))" \
  || { echo "conky FAILED to start - see /tmp/conky_run.log" >&2; cat /tmp/conky_run.log >&2; exit 1; }
