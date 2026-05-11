"""
Crystal Cave - Blender Scene Script
Extracted from live Blender session via MCP tool.
All values (locations, rotations, radii, depths, material properties,
light energies/colors, camera transform) are exact data from the live scene.

Run via: blender --python crystal_cave.py
Or paste into Blender's Scripting editor and press Run Script.
"""

import bpy
import math


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
# 2. WORLD / BACKGROUND  (very dark violet)
# ─────────────────────────────────────────────
world = bpy.context.scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg is None:
    bg = world.node_tree.nodes.new("ShaderNodeBackground")
# Exact values from session: (0.01, 0.0, 0.02) strength=0.1
bg.inputs["Color"].default_value = (0.009999999776482582, 0.0, 0.019999999552965164, 1.0)
bg.inputs["Strength"].default_value = 0.10000000149011612


# ─────────────────────────────────────────────
# 3. HELPER: make material (Principled BSDF)
# ─────────────────────────────────────────────
def make_material(name, base_color, metallic=0.0, roughness=0.5,
                  emission_color=(1, 1, 1), emission_strength=0.0,
                  transmission=0.0, ior=1.5):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*emission_color, 1.0)
    else:
        bsdf.inputs["Emission"].default_value = (*emission_color, 1.0)
    bsdf.inputs["Emission Strength"].default_value = emission_strength
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    else:
        bsdf.inputs["Transmission"].default_value = transmission
    bsdf.inputs["IOR"].default_value = ior
    return mat


# ─────────────────────────────────────────────
# 4. MATERIALS  (exact values from live session)
# ─────────────────────────────────────────────

# CaveRock: dark grey-purple, very rough, opaque
mat_rock = make_material(
    "CaveRock",
    base_color=(0.07999999821186066, 0.05999999865889549, 0.10000000149011612),
    metallic=0.0,
    roughness=0.949999988079071,
    emission_color=(1.0, 1.0, 1.0),
    emission_strength=0.0,
    transmission=0.0,
    ior=1.5,
)

# PurpleCrystal
mat_purple = make_material(
    "PurpleCrystal",
    base_color=(0.5, 0.0, 0.8999999761581421),
    metallic=0.0,
    roughness=0.05000000074505806,
    emission_color=(1.0, 1.0, 1.0),
    emission_strength=0.0,
    transmission=0.949999988079071,
    ior=1.600000023841858,
)

# BlueCrystal
mat_blue = make_material(
    "BlueCrystal",
    base_color=(0.05000000074505806, 0.20000000298023224, 1.0),
    metallic=0.0,
    roughness=0.05000000074505806,
    emission_color=(1.0, 1.0, 1.0),
    emission_strength=0.0,
    transmission=0.949999988079071,
    ior=1.600000023841858,
)

# GreenCrystal
mat_green = make_material(
    "GreenCrystal",
    base_color=(0.0, 0.8999999761581421, 0.30000001192092896),
    metallic=0.0,
    roughness=0.05000000074505806,
    emission_color=(1.0, 1.0, 1.0),
    emission_strength=0.0,
    transmission=0.949999988079071,
    ior=1.600000023841858,
)

# PinkCrystal
mat_pink = make_material(
    "PinkCrystal",
    base_color=(0.8999999761581421, 0.10000000149011612, 0.6000000238418579),
    metallic=0.0,
    roughness=0.05000000074505806,
    emission_color=(1.0, 1.0, 1.0),
    emission_strength=0.0,
    transmission=0.949999988079071,
    ior=1.600000023841858,
)

# TealCrystal
mat_teal = make_material(
    "TealCrystal",
    base_color=(0.0, 0.800000011920929, 0.800000011920929),
    metallic=0.0,
    roughness=0.05000000074505806,
    emission_color=(1.0, 1.0, 1.0),
    emission_strength=0.0,
    transmission=0.949999988079071,
    ior=1.600000023841858,
)


# ─────────────────────────────────────────────
# 5. HELPER: add crystal (hexagonal cone, 6 sides)
#    radius1 and depth extracted from live mesh bounds.
#    Crystals are upward-pointing (Z-up) cones with 6 vertices.
# ─────────────────────────────────────────────
def add_crystal(name, radius1, depth, location, rotation_euler, material):
    """
    radius1  – base radius  (extracted from local mesh bounds)
    depth    – cone height  (extracted from local mesh bounds)
    location – (x, y, z) world location  (centre of base)
    rotation_euler – (rx, ry, rz) in radians
    material – bpy material
    """
    bpy.ops.mesh.primitive_cone_add(
        vertices=6,
        radius1=radius1,
        radius2=0.0,
        depth=depth,
        end_fill_type='NGON',
        location=(location[0], location[1], location[2]),
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler = rotation_euler
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth()
    return obj


# ─────────────────────────────────────────────
# 6. CAVE STRUCTURE  (planes used as walls/floor/ceiling)
#    All planes are default Blender planes (4 verts, 1 poly).
#    Size derived from object dimensions: 16x16 each.
# ─────────────────────────────────────────────

# Floor  – flat, at Z=0
bpy.ops.mesh.primitive_plane_add(size=16, location=(0.0, 0.0, 0.0))
cave_floor = bpy.context.active_object
cave_floor.name = "CaveFloor"
cave_floor.data.materials.append(mat_rock)

# Ceiling – flat, at Z=8
bpy.ops.mesh.primitive_plane_add(size=16, location=(0.0, 0.0, 8.0))
cave_ceiling = bpy.context.active_object
cave_ceiling.name = "CaveCeiling"
cave_ceiling.data.materials.append(mat_rock)

# Wall Left  – rotated 90° around Y axis, at X=-8, centre Z=4
bpy.ops.mesh.primitive_plane_add(size=16, location=(-8.0, 0.0, 4.0))
wall_left = bpy.context.active_object
wall_left.name = "WallLeft"
wall_left.rotation_euler = (0.0, math.pi / 2, 0.0)   # 90° around Y
wall_left.data.materials.append(mat_rock)

# Wall Right – same but X=+8
bpy.ops.mesh.primitive_plane_add(size=16, location=(8.0, 0.0, 4.0))
wall_right = bpy.context.active_object
wall_right.name = "WallRight"
wall_right.rotation_euler = (0.0, math.pi / 2, 0.0)
wall_right.data.materials.append(mat_rock)

# Wall Back  – rotated 90° around X axis, at Y=8, centre Z=4
bpy.ops.mesh.primitive_plane_add(size=16, location=(0.0, 8.0, 4.0))
wall_back = bpy.context.active_object
wall_back.name = "WallBack"
wall_back.rotation_euler = (math.pi / 2, 0.0, 0.0)   # 90° around X
wall_back.data.materials.append(mat_rock)


# ─────────────────────────────────────────────
# 7. CRYSTALS  (exact loc / rot / radius / depth from live session)
#
#    All rotation_euler values are exact floats from the Blender session.
#    The Z location is the object origin which is at the cone's geometric
#    centre (depth/2 above base), so loc.z = base_z + depth/2.
# ─────────────────────────────────────────────

# ── Purple cluster (centre) ──────────────────
add_crystal("CrystalPurple1",
            radius1=0.3031, depth=3.5,
            location=(0.0, 0.0, 1.75),
            rotation_euler=(0.05000000074505806, 0.0, 0.30000001192092896),
            material=mat_purple)

add_crystal("CrystalPurple2",
            radius1=0.2165, depth=2.8,
            location=(0.5, 0.20000000298023224, 1.399999976158142),
            rotation_euler=(-0.07999999821186066, 0.0, 1.0),
            material=mat_purple)

add_crystal("CrystalPurple3",
            radius1=0.2598, depth=3.0,
            location=(-0.4000000059604645, 0.30000001192092896, 1.5),
            rotation_euler=(0.10000000149011612, 0.0, 2.0),
            material=mat_purple)

# ── Blue cluster (left side) ─────────────────
add_crystal("CrystalBlue1",
            radius1=0.3464, depth=4.0,
            location=(-2.0, 0.5, 2.0),
            rotation_euler=(0.05000000074505806, 0.0, 0.5),
            material=mat_blue)

add_crystal("CrystalBlue2",
            radius1=0.2425, depth=3.2,
            location=(-2.5999999046325684, -0.30000001192092896, 1.600000023841858),
            rotation_euler=(-0.10000000149011612, 0.0, 1.5),
            material=mat_blue)

add_crystal("CrystalBlue3",
            radius1=0.1732, depth=2.5,
            location=(-1.5, -0.800000011920929, 1.25),
            rotation_euler=(0.07999999821186066, 0.0, 0.800000011920929),
            material=mat_blue)

add_crystal("CrystalBlue4",
            radius1=0.1559, depth=2.0,
            location=(-3.0, 0.800000011920929, 1.0),
            rotation_euler=(0.11999999731779099, 0.0, 2.5),
            material=mat_blue)

# ── Green cluster (right side) ───────────────
add_crystal("CrystalGreen1",
            radius1=0.3291, depth=3.8,
            location=(2.5, 0.0, 1.899999976158142),
            rotation_euler=(-0.05000000074505806, 0.0, 0.699999988079071),
            material=mat_green)

add_crystal("CrystalGreen2",
            radius1=0.2165, depth=2.9,
            location=(3.0, 0.800000011920929, 1.4500000476837158),
            rotation_euler=(0.10000000149011612, 0.0, 1.7999999523162842),
            material=mat_green)

add_crystal("CrystalGreen3",
            radius1=0.1905, depth=2.3,
            location=(2.0, 1.0, 1.149999976158142),
            rotation_euler=(-0.07999999821186066, 0.0, 3.0),
            material=mat_green)

# ── Pink cluster (back-centre) ────────────────
add_crystal("CrystalPink1",
            radius1=0.2771, depth=3.2,
            location=(1.0, 2.5, 1.600000023841858),
            rotation_euler=(0.07000000029802322, 0.0, 1.100000023841858),
            material=mat_pink)

add_crystal("CrystalPink2",
            radius1=0.1905, depth=2.5,
            location=(-1.0, 2.0, 1.25),
            rotation_euler=(-0.05999999865889549, 0.0, 2.200000047683716),
            material=mat_pink)

# ── Teal cluster (far back) ──────────────────
add_crystal("CrystalTeal1",
            radius1=0.3031, depth=3.5,
            location=(0.5, 4.0, 1.75),
            rotation_euler=(0.05999999865889549, 0.0, 0.4000000059604645),
            material=mat_teal)

add_crystal("CrystalTeal2",
            radius1=0.2165, depth=2.7,
            location=(-1.5, 3.5, 1.350000023841858),
            rotation_euler=(-0.07000000029802322, 0.0, 1.7000000476837158),
            material=mat_teal)

# ── Small accent crystals ─────────────────────
add_crystal("SmallBlue1",
            radius1=0.1039, depth=1.5,
            location=(-0.800000011920929, 1.5, 0.75),
            rotation_euler=(0.0, 0.0, 0.6000000238418579),
            material=mat_blue)

add_crystal("SmallPurple1",
            radius1=0.1299, depth=1.8,
            location=(1.5, -0.5, 0.8999999761581421),
            rotation_euler=(0.0, 0.0, 2.0999999046325684),
            material=mat_purple)

add_crystal("SmallGreen1",
            radius1=0.0866, depth=1.3,
            location=(-2.5, 2.0, 0.6499999761581421),
            rotation_euler=(0.0, 0.0, 3.5),
            material=mat_green)

add_crystal("SmallTeal1",
            radius1=0.1126, depth=1.6,
            location=(3.5, -0.5, 0.800000011920929),
            rotation_euler=(0.10000000149011612, 0.0, 1.0),
            material=mat_teal)

# ── Stalactites (ceiling-hanging crystals, flipped via pi rotation on X) ──
#    rotation_euler X = pi (3.14159…) flips cone to hang down.
add_crystal("Stalac1",
            radius1=0.1732, depth=1.8,
            location=(0.5, 1.0, 7.099999904632568),
            rotation_euler=(3.1415927410125732, 0.0, 0.30000001192092896),
            material=mat_blue)

add_crystal("Stalac2",
            radius1=0.1299, depth=2.2,
            location=(-1.5, 2.0, 6.900000095367432),
            rotation_euler=(3.1415927410125732, 0.0, 1.100000023841858),
            material=mat_purple)

add_crystal("Stalac3",
            radius1=0.1559, depth=1.5,
            location=(2.0, 0.5, 7.25),
            rotation_euler=(3.1415927410125732, 0.0, 2.0),
            material=mat_teal)

add_crystal("Stalac4",
            radius1=0.1039, depth=1.0,
            location=(-0.5, 3.5, 7.5),
            rotation_euler=(3.1415927410125732, 0.0, 0.699999988079071),
            material=mat_blue)


# ─────────────────────────────────────────────
# 8. LIGHTS  (exact values from live session)
# ─────────────────────────────────────────────

# CaveMainLight – overhead purple, large soft radius
bpy.ops.object.light_add(type='POINT', location=(0.0, 0.0, 5.0))
main_light = bpy.context.active_object
main_light.name = "CaveMainLight"
main_light.data.energy = 200.0
main_light.data.color = (0.6000000238418579, 0.10000000149011612, 1.0)
main_light.data.shadow_soft_size = 3.0

# BlueCrystalLight – fills the blue cluster
bpy.ops.object.light_add(type='POINT', location=(-2.5, 0.0, 2.0))
blue_light = bpy.context.active_object
blue_light.name = "BlueCrystalLight"
blue_light.data.energy = 300.0
blue_light.data.color = (0.10000000149011612, 0.30000001192092896, 1.0)
blue_light.data.shadow_soft_size = 0.0

# GreenCrystalLight – fills the green cluster
bpy.ops.object.light_add(type='POINT', location=(2.5, 0.0, 2.0))
green_light = bpy.context.active_object
green_light.name = "GreenCrystalLight"
green_light.data.energy = 300.0
green_light.data.color = (0.0, 1.0, 0.4000000059604645)
green_light.data.shadow_soft_size = 0.0

# BackLight – fills the back/pink/teal area
bpy.ops.object.light_add(type='POINT', location=(0.0, 5.0, 3.0))
back_light = bpy.context.active_object
back_light.name = "BackLight"
back_light.data.energy = 150.0
back_light.data.color = (0.800000011920929, 0.5, 1.0)
back_light.data.shadow_soft_size = 0.0


# ─────────────────────────────────────────────
# 9. CAMERA  (exact values from live session)
# ─────────────────────────────────────────────
bpy.ops.object.camera_add(
    location=(-1.0, -9.0, 4.0)
)
cam_obj = bpy.context.active_object
cam_obj.name = "CaveCamera"
cam_obj.rotation_euler = (
    1.3962633609771729,   # ~80°
    0.0,
    -0.0872664600610733,  # ~-5°
)
cam_obj.data.lens = 35.0
cam_obj.data.clip_end = 1000.0
bpy.context.scene.camera = cam_obj


# ─────────────────────────────────────────────
# 10. RENDER SETTINGS
# ─────────────────────────────────────────────
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080

print("Crystal Cave scene built successfully.")
