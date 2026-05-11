#!/usr/bin/env bash
# Run Neon City scene in Blender (background render)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"

if [ ! -f "$BLENDER" ]; then
  echo "ERROR: Blender not found at $BLENDER"
  exit 1
fi

echo "==> Loading Neon City scene..."
"$BLENDER" --python "$SCRIPT_DIR/neon_city.py" "$@"
