#!/usr/bin/env bash
# Run Solar System scene in Blender (background render)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"

if [ ! -f "$BLENDER" ]; then
  echo "ERROR: Blender not found at $BLENDER"
  exit 1
fi

echo "==> Loading Solar System scene..."
"$BLENDER" --python "$SCRIPT_DIR/solar_system.py" "$@"
