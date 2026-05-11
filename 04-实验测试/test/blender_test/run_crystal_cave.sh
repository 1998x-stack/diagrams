#!/usr/bin/env bash
# Run Crystal Cave scene in Blender
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"

if [ ! -f "$BLENDER" ]; then
  echo "ERROR: Blender not found at $BLENDER"
  exit 1
fi

echo "==> Loading Crystal Cave scene..."
"$BLENDER" --python "$SCRIPT_DIR/crystal_cave.py" "$@"
