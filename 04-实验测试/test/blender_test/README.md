# Blender MCP — 3 Example Scenes

Three Blender scenes built via Claude Code + [blender-mcp](https://github.com/ahujasid/blender-mcp). Each scene is a standalone Python script you can load, edit, and render.

---

## Scenes

### 1. Solar System (`solar_system.py`)
A miniature solar system with:
- **Sun** — glowing emission shader (strength 5), warm yellow point light (5000W)
- **Mercury, Venus, Earth, Mars, Saturn** — scaled spheres with unique materials
- **Saturn's ring** — torus with tilt, golden material
- **Orbit paths** — thin torus rings showing each planet's path
- **200 background stars** — randomly scattered small emission spheres
- **Camera** — wide angled view framing all planets
- **Render** — Cycles, 1920×1080

### 2. Neon City (`neon_city.py`)
A futuristic cyberpunk cityscape with:
- **36 buildings** — random heights (3–18 m), glass or concrete materials
- **Neon rooftop strips** — cyan, magenta, orange, purple emission materials (strength 6–8)
- **Ground plane** — dark metallic reflective surface
- **Central road** — slightly raised dark road down the middle
- **3 lights** — ambient white (1000W), cyan neon (800W), magenta neon (600W)
- **Camera** — street-level perspective looking up the city canyon
- **Render** — Cycles, 1920×1080

### 3. Crystal Cave (`crystal_cave.py`)
An underground cavern filled with gemstone crystals:
- **Cave walls** — floor, ceiling, 3 rock-material planes enclosing the space
- **22 crystals** — hexagonal cone shapes in 5 color clusters:
  - Purple (center), Blue (left), Green (right), Pink, Teal
- **4 stalactites** — inverted crystals hanging from the ceiling
- **4 small accent crystals** — scattered around the floor
- **Crystal material** — Principled BSDF with 95% transmission, IOR 1.6 (glass-like)
- **4 point lights** — purple overhead, blue + green flanking, pink-purple backlight
- **Camera** — low angle looking into the crystal field (35mm lens)
- **Render** — Cycles, 1920×1080

---

## File Structure

```
blender_test/
├── addon.py              # BlenderMCP addon (install into Blender)
├── solar_system.py       # Scene 1 script
├── neon_city.py          # Scene 2 script
├── crystal_cave.py       # Scene 3 script
├── run_solar_system.sh   # Open Scene 1 in Blender GUI
├── run_neon_city.sh      # Open Scene 2 in Blender GUI
├── run_crystal_cave.sh   # Open Scene 3 in Blender GUI
├── render_all.sh         # Headless render all 3 scenes → renders/
└── README.md             # This file
```

---

## Requirements

- **Blender 5.1+** — `/Applications/Blender.app` (installed via `brew install --cask blender`)
- **Python** — bundled with Blender, no system Python needed
- **blender-mcp** — only needed for Claude Code ↔ Blender live connection (`uvx blender-mcp`)

---

## Usage

### Option A — Run in Blender GUI

```bash
# Make scripts executable (first time only)
chmod +x run_solar_system.sh run_neon_city.sh run_crystal_cave.sh render_all.sh

# Open a scene
./run_solar_system.sh
./run_neon_city.sh
./run_crystal_cave.sh
```

Blender will open with the scene loaded. Press **F12** to render.

### Option B — Paste into Blender Scripting Editor

1. Open Blender
2. Switch to the **Scripting** workspace (top bar)
3. Click **New** to create a new script
4. Paste the contents of any `.py` file
5. Click **Run Script** (or press `Alt+P`)

### Option C — Headless batch render (no GUI)

```bash
chmod +x render_all.sh
./render_all.sh
```

Renders all 3 scenes to `renders/` as PNG files:
- `renders/solar_system_0001.png`
- `renders/neon_city_0001.png`
- `renders/crystal_cave_0001.png`

### Option D — Direct Blender CLI

```bash
BLENDER="/Applications/Blender.app/Contents/MacOS/Blender"

# GUI (interactive)
"$BLENDER" --python solar_system.py

# Headless render
"$BLENDER" --background --python solar_system.py \
  --render-output ./renders/solar_system_#### \
  --render-frame 1
```

---

## BlenderMCP Setup (Claude Code integration)

This lets Claude Code control Blender live via natural language.

### 1. Install the addon in Blender

1. Open Blender → **Edit > Preferences > Add-ons > Install**
2. Select `addon.py` from this folder
3. Enable **"Interface: Blender MCP"** (check the box)

### 2. Connect Blender to Claude

1. In the **3D View**, press `N` to open the sidebar
2. Find the **BlenderMCP** tab
3. Click **"Connect to Claude"**
4. Blender MCP server starts on `localhost:9876`

### 3. Verify connection in Claude Code

```bash
claude mcp list
# blender: uvx blender-mcp - ✓ Connected
```

### 4. Add the MCP server (if not already done)

```bash
claude mcp add blender uvx blender-mcp
```

---

## Customization Tips

| Goal | What to change |
|------|---------------|
| Change planet colors | `mat_earth`, `mat_mars`, etc. base_color tuple |
| More/fewer buildings | Adjust `grid_positions` list length |
| Different crystal colors | Change `base_color` in `mat_purple`, `mat_blue`, etc. |
| Add animation | Set `obj.keyframe_insert("location", frame=1)` before/after moving |
| Change render engine | `scene.render.engine = 'BLENDER_EEVEE_NEXT'` for faster preview |
| Higher resolution | `scene.render.resolution_x = 3840` for 4K |
| More render samples | `scene.cycles.samples = 512` for cleaner output |

---

## Built with

- [Blender](https://www.blender.org/) 5.1
- [blender-mcp](https://github.com/ahujasid/blender-mcp) by ahujasid
- [Claude Code](https://claude.ai/claude-code) + Claude Sonnet 4.6
