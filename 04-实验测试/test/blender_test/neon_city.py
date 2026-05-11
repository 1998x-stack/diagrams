"""
Neon City - Blender Scene Script
Extracted from live Blender session data.
Run via: blender --python neon_city.py
Or paste into Blender's Scripting editor and press Run Script.
"""

import bpy
import math
import random


# ─────────────────────────────────────────────
# 1. CLEAR SCENE
# ─────────────────────────────────────────────
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        bpy.data.materials.remove(block)
    for block in bpy.data.cameras:
        bpy.data.cameras.remove(block)
    for block in bpy.data.lights:
        bpy.data.lights.remove(block)


clear_scene()


# ─────────────────────────────────────────────
# 2. WORLD / BACKGROUND  (dark night sky)
# ─────────────────────────────────────────────
world = bpy.context.scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg is None:
    bg = world.node_tree.nodes.new("ShaderNodeBackground")
bg.inputs["Color"].default_value = (0.01, 0.0, 0.02, 1.0)
bg.inputs["Strength"].default_value = 0.1


# ─────────────────────────────────────────────
# 3. HELPER: make material (Principled BSDF)
# ─────────────────────────────────────────────
def make_material(name, base_color, metallic=0.0, roughness=0.5,
                  emission_color=None, emission_strength=0.0,
                  transmission=0.0, ior=1.5, alpha=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    ec = emission_color if emission_color is not None else base_color
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*ec, 1.0)
    else:
        bsdf.inputs["Emission"].default_value = (*ec, 1.0)
    bsdf.inputs["Emission Strength"].default_value = emission_strength
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    else:
        bsdf.inputs["Transmission"].default_value = transmission
    bsdf.inputs["IOR"].default_value = ior
    return mat


# ─────────────────────────────────────────────
# 4. MATERIALS
# ─────────────────────────────────────────────
mat_ground   = make_material("GroundMat",    (0.02, 0.02, 0.04), metallic=0.8, roughness=0.2)
mat_concrete = make_material("ConcreteMat",  (0.08, 0.07, 0.1),  metallic=0.0, roughness=0.9)
mat_glass    = make_material("GlassMat",     (0.05, 0.05, 0.1),  metallic=0.0, roughness=0.05,
                             transmission=0.9, ior=1.5)
mat_neon_cyan    = make_material("NeonCyan",    (0.0, 0.8, 1.0),
                                 emission_color=(0.0, 1.0, 0.9),  emission_strength=8.0)
mat_neon_magenta = make_material("NeonMagenta", (1.0, 0.0, 0.6),
                                 emission_color=(1.0, 0.0, 0.8),  emission_strength=8.0)
mat_neon_orange  = make_material("NeonOrange",  (1.0, 0.4, 0.0),
                                 emission_color=(1.0, 0.3, 0.0),  emission_strength=6.0)
mat_neon_purple  = make_material("NeonPurple",  (0.6, 0.0, 1.0),
                                 emission_color=(0.5, 0.0, 1.0),  emission_strength=6.0)
mat_metal    = make_material("MetalMat",     (0.3, 0.3, 0.35), metallic=1.0, roughness=0.15)


# ─────────────────────────────────────────────
# 5. GROUND PLANE
# ─────────────────────────────────────────────
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(mat_ground)


# ─────────────────────────────────────────────
# 6. BUILDINGS
#    36 cube meshes were present in the orphaned data.
#    Buildings are boxes (default cube scaled) arranged in a grid city layout.
# ─────────────────────────────────────────────
random.seed(7)

building_data = []

# City grid: buildings along X and Y axes around center
# Layout: two main avenues (X and Y), buildings fill blocks
grid_positions = []

# Left block (negative X)
for row in range(4):
    for col in range(3):
        x = -12 + col * 4 - 2
        y = -6 + row * 4
        grid_positions.append((x, y))

# Right block (positive X)
for row in range(4):
    for col in range(3):
        x = 6 + col * 4
        y = -6 + row * 4
        grid_positions.append((x, y))

# Far back block
for col in range(6):
    x = -10 + col * 4
    y = 14
    grid_positions.append((x, y))

# Near foreground sides
for row in range(2):
    x = -18
    y = -4 + row * 6
    grid_positions.append((x, y))
for row in range(2):
    x = 18
    y = -4 + row * 6
    grid_positions.append((x, y))

# Pick neon material for window accents cycling through colors
neon_mats = [mat_neon_cyan, mat_neon_magenta, mat_neon_orange, mat_neon_purple]

for i, (bx, by) in enumerate(grid_positions[:36]):
    height = random.uniform(3, 18)
    width  = random.uniform(1.5, 3.5)
    depth  = random.uniform(1.5, 3.5)

    # Main building body
    bpy.ops.mesh.primitive_cube_add(location=(bx, by, height / 2))
    bldg = bpy.context.active_object
    bldg.name = f"Building{i:02d}"
    bldg.scale = (width / 2, depth / 2, height / 2)
    bpy.ops.object.transform_apply(scale=True)

    # Pick material: glass or concrete
    if random.random() > 0.5:
        bldg.data.materials.append(mat_glass)
    else:
        bldg.data.materials.append(mat_concrete)

    # Neon accent strip on top of building
    neon_mat = neon_mats[i % len(neon_mats)]
    bpy.ops.mesh.primitive_cube_add(location=(bx, by, height + 0.15))
    strip = bpy.context.active_object
    strip.name = f"NeonStrip{i:02d}"
    strip.scale = (width / 2 + 0.05, depth / 2 + 0.05, 0.15)
    bpy.ops.object.transform_apply(scale=True)
    strip.data.materials.append(neon_mat)

    building_data.append((bldg, height))


# ─────────────────────────────────────────────
# 7. STREET ELEMENTS
# ─────────────────────────────────────────────

# Central road surface
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.01))
road = bpy.context.active_object
road.name = "MainRoad"
road.scale = (2.5, 30, 1)
bpy.ops.object.transform_apply(scale=True)
road_mat = make_material("RoadMat", (0.03, 0.03, 0.05), metallic=0.3, roughness=0.4)
road.data.materials.append(road_mat)

# Road lane markings
for i in range(-8, 9, 4):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, i, 0.015))
    mark = bpy.context.active_object
    mark.name = f"LaneMark{i}"
    mark.scale = (0.1, 1.5, 1)
    bpy.ops.object.transform_apply(scale=True)
    mark_mat = make_material(f"LaneMarkMat{i}", (0.9, 0.9, 0.7),
                             emission_color=(1.0, 1.0, 0.8), emission_strength=1.0)
    mark.data.materials.append(mark_mat)


# ─────────────────────────────────────────────
# 8. STREET LIGHTS (lamp posts)
# ─────────────────────────────────────────────
def add_lamp_post(name, location, neon_color, mat_color):
    # Post (thin tall cube)
    bpy.ops.mesh.primitive_cube_add(location=(location[0], location[1], 2.5))
    post = bpy.context.active_object
    post.name = name + "_post"
    post.scale = (0.08, 0.08, 2.5)
    bpy.ops.object.transform_apply(scale=True)
    post.data.materials.append(mat_metal)

    # Lamp head
    bpy.ops.mesh.primitive_cube_add(location=(location[0], location[1] + 0.3, 5.1))
    head = bpy.context.active_object
    head.name = name + "_head"
    head.scale = (0.25, 0.4, 0.12)
    bpy.ops.object.transform_apply(scale=True)
    head_mat = make_material(name + "_headmat", mat_color,
                             emission_color=mat_color, emission_strength=6.0)
    head.data.materials.append(head_mat)


lamp_specs = [
    ("LampL1", (-3.5, -10), (0.0, 1.0, 0.9), (0.0, 0.9, 1.0)),
    ("LampL2", (-3.5,  -3), (0.0, 1.0, 0.9), (0.0, 0.9, 1.0)),
    ("LampL3", (-3.5,   4), (0.0, 1.0, 0.9), (0.0, 0.9, 1.0)),
    ("LampR1", ( 3.5, -10), (1.0, 0.0, 0.8), (1.0, 0.0, 0.8)),
    ("LampR2", ( 3.5,  -3), (1.0, 0.0, 0.8), (1.0, 0.0, 0.8)),
    ("LampR3", ( 3.5,   4), (1.0, 0.0, 0.8), (1.0, 0.0, 0.8)),
]
for spec in lamp_specs:
    add_lamp_post(*spec)


# ─────────────────────────────────────────────
# 9. LIGHTS
# ─────────────────────────────────────────────

# General ambient fill (white, low energy)
bpy.ops.object.light_add(type='POINT', location=(0, 0, 20))
ambient_light = bpy.context.active_object
ambient_light.name = "AmbientLight"
ambient_light.data.energy = 1000.0
ambient_light.data.color = (1.0, 1.0, 1.0)
ambient_light.data.shadow_soft_size = 0.1

# Cyan neon fill (left side)
bpy.ops.object.light_add(type='POINT', location=(-5, 0, 8))
neon_cyan_light = bpy.context.active_object
neon_cyan_light.name = "NeonCyanLight"
neon_cyan_light.data.energy = 800.0
neon_cyan_light.data.color = (0.0, 1.0, 0.9)

# Magenta neon fill (right side)
bpy.ops.object.light_add(type='POINT', location=(5, 0, 8))
neon_mag_light = bpy.context.active_object
neon_mag_light.name = "NeonMagentaLight"
neon_mag_light.data.energy = 600.0
neon_mag_light.data.color = (1.0, 0.0, 0.8)


# ─────────────────────────────────────────────
# 10. CAMERA
# ─────────────────────────────────────────────
bpy.ops.object.camera_add(location=(0, -22, 8))
cam_obj = bpy.context.active_object
cam_obj.name = "CityCamera"
cam_obj.rotation_euler = (math.radians(72), 0, 0)
cam_obj.data.lens = 50.0
cam_obj.data.clip_end = 1000.0
bpy.context.scene.camera = cam_obj


# ─────────────────────────────────────────────
# 11. RENDER SETTINGS
# ─────────────────────────────────────────────
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

print("Neon City scene built successfully.")
