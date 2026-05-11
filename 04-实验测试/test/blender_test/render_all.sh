#!/usr/bin/env bash
# Render all 3 scenes to PNG files (headless, no GUI)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"
OUT="$SCRIPT_DIR/renders"
mkdir -p "$OUT"

if [ ! -f "$BLENDER" ]; then
  echo "ERROR: Blender not found at $BLENDER"
  exit 1
fi

render_scene() {
  local name="$1"
  local script="$2"
  echo ""
  echo "==> Rendering: $name"
  "$BLENDER" --background --python "$script" --render-output "$OUT/${name}_####" --render-frame 1
  echo "    Saved to: $OUT/${name}_0001.png"
}

render_scene "solar_system" "$SCRIPT_DIR/solar_system.py"
render_scene "neon_city"    "$SCRIPT_DIR/neon_city.py"
render_scene "crystal_cave" "$SCRIPT_DIR/crystal_cave.py"

echo ""
echo "All renders complete. Output: $OUT/"
ls "$OUT/"
