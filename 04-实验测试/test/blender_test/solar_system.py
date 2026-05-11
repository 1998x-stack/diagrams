"""
Solar System - Blender Scene Script
Extracted from live Blender session data.
Run via: blender --python solar_system.py
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
# 2. WORLD / BACKGROUND
# ─────────────────────────────────────────────
world = bpy.context.scene.world
if world is None:
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node is None:
    bg_node = world.node_tree.nodes.new("ShaderNodeBackground")
# Deep space black
bg_node.inputs["Color"].default_value = (0.0, 0.0, 0.01, 1.0)
bg_node.inputs["Strength"].default_value = 0.0


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
    # Blender 4.x uses "Emission Color" + "Emission Strength"
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
# 4. MATERIALS
# ─────────────────────────────────────────────
mat_sun     = make_material("SunMat",     (1.0, 0.7, 0.1),  metallic=0.0, roughness=0.8,
                            emission_color=(1.0, 0.6, 0.1),  emission_strength=5.0)
mat_mercury = make_material("MercuryMat", (0.5, 0.45, 0.4), metallic=0.0, roughness=0.9)
mat_venus   = make_material("VenusMat",   (0.9, 0.75, 0.4), metallic=0.0, roughness=0.7,
                            emission_color=(0.9, 0.6, 0.2),  emission_strength=0.3)
mat_earth   = make_material("EarthMat",   (0.1, 0.4, 0.8),  metallic=0.0, roughness=0.6)
mat_mars    = make_material("MarsMat",    (0.8, 0.25, 0.1), metallic=0.0, roughness=0.8)
mat_ring    = make_material("RingMat",    (0.7, 0.6, 0.4),  metallic=0.2, roughness=0.9)
mat_space   = make_material("SpaceMat",   (0.0, 0.0, 0.02), metallic=0.0, roughness=1.0)


# ─────────────────────────────────────────────
# 5. HELPER: add sphere
# ─────────────────────────────────────────────
def add_sphere(name, radius, location, material, segments=64, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius,
        segments=segments,
        ring_count=rings,
        location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name + "Mesh"
    obj.data.materials.append(material)
    # Smooth shading
    bpy.ops.object.shade_smooth()
    return obj


# ─────────────────────────────────────────────
# 6. CELESTIAL BODIES
# ─────────────────────────────────────────────

# Sun  (radius=1.5, verts=1986 => segments≈64, rings≈32)
sun = add_sphere("Sun", radius=1.5, location=(0, 0, 0), material=mat_sun, segments=64, rings=32)

# Mercury  (radius=0.3, small planet)
mercury = add_sphere("Mercury", radius=0.3, location=(3.5, 0, 0), material=mat_mercury, segments=32, rings=16)

# Venus  (radius=0.4)
venus = add_sphere("Venus", radius=0.4, location=(5.5, 0, 0), material=mat_venus, segments=32, rings=16)

# Earth  (radius=0.4)
earth = add_sphere("Earth", radius=0.4, location=(8.0, 0, 0), material=mat_earth, segments=32, rings=16)

# Mars  (radius=0.3)
mars = add_sphere("Mars", radius=0.3, location=(11.0, 0, 0), material=mat_mars, segments=32, rings=16)

# Saturn-like planet with ring  (radius=0.7)
saturn = add_sphere("Saturn", radius=0.7, location=(15.0, 0, 0), material=mat_venus, segments=64, rings=32)

# Saturn ring  (torus: major_radius=1.38, minor_radius=0.08)
bpy.ops.mesh.primitive_torus_add(
    major_radius=1.38,
    minor_radius=0.08,
    major_segments=64,
    minor_segments=16,
    location=(15.0, 0, 0)
)
ring = bpy.context.active_object
ring.name = "SaturnRing"
ring.rotation_euler = (math.radians(20), 0, 0)
ring.data.materials.append(mat_ring)


# ─────────────────────────────────────────────
# 7. ORBIT CIRCLES (visual guides, thin tori)
# ─────────────────────────────────────────────
def add_orbit(name, radius, location=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=radius,
        minor_radius=0.02,
        major_segments=128,
        minor_segments=8,
        location=location
    )
    obj = bpy.context.active_object
    obj.name = name
    mat_orbit = make_material(name + "Mat", (0.3, 0.3, 0.5), roughness=1.0)
    obj.data.materials.append(mat_orbit)
    return obj


add_orbit("MercuryOrbit", 3.5)
add_orbit("VenusOrbit",   5.5)
add_orbit("EarthOrbit",   8.0)
add_orbit("MarsOrbit",   11.0)
add_orbit("SaturnOrbit", 15.0)


# ─────────────────────────────────────────────
# 8. STAR FIELD (particle-like small spheres spread around)
# ─────────────────────────────────────────────
import random
random.seed(42)
star_mat = make_material("StarMat", (1.0, 1.0, 1.0),
                         emission_color=(1.0, 1.0, 1.0), emission_strength=3.0)
for i in range(200):
    theta = random.uniform(0, 2 * math.pi)
    phi   = random.uniform(0, math.pi)
    r     = random.uniform(30, 60)
    x = r * math.sin(phi) * math.cos(theta)
    y = r * math.sin(phi) * math.sin(theta)
    z = r * math.cos(phi)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, segments=4, ring_count=4, location=(x, y, z))
    star = bpy.context.active_object
    star.name = f"Star{i:03d}"
    star.data.materials.append(star_mat)


# ─────────────────────────────────────────────
# 9. LIGHTS
# ─────────────────────────────────────────────

# Main sun point light (warm, high energy, large radius)
bpy.ops.object.light_add(type='POINT', location=(0, 0, 0))
sun_light = bpy.context.active_object
sun_light.name = "SunLight"
sun_light.data.energy = 5000.0
sun_light.data.color = (1.0, 0.9, 0.6)
sun_light.data.shadow_soft_size = 1.5

# Ambient space fill (sun-type, cool blue)
bpy.ops.object.light_add(type='SUN', location=(0, 0, 50))
ambient = bpy.context.active_object
ambient.name = "SpaceAmbient"
ambient.data.energy = 0.3
ambient.data.color = (0.5, 0.6, 1.0)

# Rim / back fill sun
bpy.ops.object.light_add(type='SUN', location=(0, -50, 20))
rim = bpy.context.active_object
rim.name = "SpaceRim"
rim.data.energy = 0.5
rim.data.color = (0.5, 0.6, 1.0)
rim.rotation_euler = (math.radians(30), 0, math.radians(180))


# ─────────────────────────────────────────────
# 10. CAMERA
# ─────────────────────────────────────────────
bpy.ops.object.camera_add(location=(0, -35, 12))
cam_obj = bpy.context.active_object
cam_obj.name = "SolarCamera"
cam_obj.rotation_euler = (math.radians(70), 0, 0)
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

print("Solar System scene built successfully.")
