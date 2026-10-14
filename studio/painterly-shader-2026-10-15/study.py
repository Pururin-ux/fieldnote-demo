"""Original procedural painterly shader study, Runproof Studio, 2026-10-15.

Run with Blender 5.x in background mode, no image textures or external assets.
This is an independent feasibility reference, not a client's commissioned scene.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

args = argparse.ArgumentParser()
args.add_argument('--outdir', default='out')
args.add_argument('--animate', action='store_true')
args.add_argument('--skip-still', action='store_true')
opt = args.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
out = Path(opt.outdir).resolve()
out.mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
for candidate in ('BLENDER_EEVEE', 'BLENDER_EEVEE_NEXT'):
    try:
        scene.render.engine = candidate
        break
    except TypeError:
        pass
else:
    raise RuntimeError('This material requires EEVEE Shader to RGB')

scene.render.resolution_x = 1280
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.use_file_extension = True
scene.render.use_stamp = False
# Disable metadata stamps too: filename stamps otherwise expose local paths
# even when burned-in stamps are disabled.
for prop in scene.render.bl_rna.properties:
    if prop.identifier.startswith('use_stamp') and prop.type == 'BOOLEAN' and not prop.is_readonly:
        setattr(scene.render, prop.identifier, False)
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0
scene.view_settings.gamma = 1
scene.world.color = (0.25, 0.25, 0.25)

def color(hexcode):
    def linear(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(linear(int(hexcode[i:i+2], 16) / 255) for i in (0, 2, 4)) + (1,)

def paint_material(name, palette):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    def node(kind, label, x, y):
        n = nodes.new(kind)
        n.label = label
        n.location = (x, y)
        return n
    coord = node('ShaderNodeTexCoord', 'Object-space anchoring', -1100, -220)
    mapping = node('ShaderNodeVectorMath', 'Directional brush aspect', -900, -220)
    mapping.operation = 'MULTIPLY'
    mapping.inputs[1].default_value = (3, 19, 5)
    links.new(coord.outputs['Generated'], mapping.inputs[0])
    strokes = node('ShaderNodeTexNoise', 'Directional pigment strokes', -690, -180)
    strokes.inputs['Scale'].default_value = 3.2
    strokes.inputs['Detail'].default_value = 2.2
    strokes.inputs['Roughness'].default_value = 0.65
    links.new(mapping.outputs['Vector'], strokes.inputs['Vector'])
    shade = node('ShaderNodeBsdfDiffuse', 'Actual scene illumination', -1100, 240)
    shade.inputs['Color'].default_value = (0.8, 0.8, 0.8, 1)
    rgb = node('ShaderNodeShaderToRGB', 'EEVEE illumination response', -880, 240)
    bw = node('ShaderNodeRGBToBW', 'Luminance', -690, 240)
    links.new(shade.outputs[0], rgb.inputs[0])
    links.new(rgb.outputs[0], bw.inputs[0])
    pigment = node('ShaderNodeMath', 'Pigment edge variation', -470, -160)
    pigment.operation = 'MULTIPLY_ADD'
    pigment.inputs[1].default_value = 0.27
    pigment.inputs[2].default_value = -0.095
    links.new(strokes.outputs['Fac'], pigment.inputs[0])
    value = node('ShaderNodeMath', 'Lighting + irregular paint boundary', -250, 240)
    value.operation = 'ADD'
    value.use_clamp = True
    links.new(bw.outputs[0], value.inputs[0])
    links.new(pigment.outputs[0], value.inputs[1])
    ramp = node('ShaderNodeValToRGB', 'Limited pigment palette', -20, 240)
    ramp.color_ramp.interpolation = 'EASE'
    stops = (0, 0.17, 0.36, 0.58, 0.78, 1)
    ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
    for index, (stop, pigment_color) in enumerate(zip(stops, palette)):
        e = ramp.color_ramp.elements[0] if index == 0 else ramp.color_ramp.elements.new(stop)
        e.position = stop
        e.color = color(pigment_color)
    links.new(value.outputs[0], ramp.inputs[0])
    grain = node('ShaderNodeMapRange', 'Subtle pigment density', -240, -100)
    grain.inputs['From Min'].default_value = 0
    grain.inputs['From Max'].default_value = 1
    grain.inputs['To Min'].default_value = 0.68
    grain.inputs['To Max'].default_value = 1
    links.new(strokes.outputs['Fac'], grain.inputs['Value'])
    mix = node('ShaderNodeMixRGB', 'Surface stroke density', 250, 180)
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 0.45
    links.new(ramp.outputs['Color'], mix.inputs[1])
    links.new(grain.outputs[0], mix.inputs[2])
    emission = node('ShaderNodeEmission', 'Painted colour', 470, 180)
    links.new(mix.outputs[0], emission.inputs[0])
    output = node('ShaderNodeOutputMaterial', 'Surface', 670, 180)
    links.new(emission.outputs[0], output.inputs['Surface'])
    return mat

warm = paint_material('Burnt sienna / original procedural pigment',
                      ['28313F', '59404D', '9B5654', 'CE865D', 'EFBF80', 'FBE1B4'])
cool = paint_material('Deep teal / original procedural pigment',
                      ['1E303C', '284B5D', '397786', '69A5A8', 'AED0BB', 'EBE2BE'])

def finish(obj, name, material):
    obj.name = name
    obj.data.materials.append(material)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj

bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.17, location=(-0.35, 0.35, 1.2))
finish(bpy.context.object, 'Sienna sphere', warm)
bpy.ops.mesh.primitive_torus_add(major_segments=72, minor_segments=24, major_radius=0.86, minor_radius=0.29, location=(1.45, -0.15, 0.91), rotation=(math.radians(67), math.radians(-12), math.radians(18)))
finish(bpy.context.object, 'Teal tilted torus', cool)
bpy.ops.mesh.primitive_cube_add(size=1.4, location=(-1.9, -0.7, 0.73), rotation=(0, 0, 0.18))
block = finish(bpy.context.object, 'Rounded painted block', cool)
bevel = block.modifiers.new('Soft original edges', 'BEVEL')
bevel.width, bevel.segments = 0.20, 5
block.modifiers.new('Weighted surface normals', 'WEIGHTED_NORMAL')

floor_mat = bpy.data.materials.new('Warm paper ground')
floor_mat.diffuse_color = color('E7DECF')
floor_mat.use_nodes = True
floor_mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = color('E7DECF')
floor_mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = 1
bpy.ops.mesh.primitive_plane_add(size=200)
bpy.context.object.name = 'Paper ground'
bpy.context.object.data.materials.append(floor_mat)

def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()

for name, loc, power, size in [('Key', (-3, -4, 7), 750, 4.2), ('Fill', (4, 1, 5), 170, 5)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    lamp = bpy.context.object
    lamp.name = name
    lamp.data.energy, lamp.data.shape, lamp.data.size = power, 'DISK', size
    aim(lamp, (0, 0, 0.7))

bpy.ops.object.camera_add(location=(6.8, -10.5, 7.2))
camera = bpy.context.object
aim(camera, (-0.15, 0, 0.85))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 7.8
scene.camera = camera

# These are renders of real shader nodes, not generated textures or a client scene.
scene.render.filepath = str(out / 'preview.png')
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'study.blend'))
if not opt.skip_still:
    bpy.ops.render.render(write_still=True)
if opt.animate:
    scene.render.resolution_percentage = 50
    scene.render.fps = 12
    scene.frame_start, scene.frame_end = 1, 24
    for name, delta in [('Sienna sphere', 0.65), ('Rounded painted block', 0.35), ('Teal tilted torus', -0.25)]:
        obj = bpy.data.objects[name]
        obj.keyframe_insert(data_path='rotation_euler', frame=1)
        obj.rotation_euler.z += delta
        obj.keyframe_insert(data_path='rotation_euler', frame=24)
    scene.render.image_settings.media_type = 'VIDEO'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    scene.render.filepath = str(out / 'motion.mp4')
    bpy.ops.render.render(animation=True)
    scene.frame_set(24)
    scene.render.image_settings.media_type = 'IMAGE'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(out / 'motion-end.png')
    bpy.ops.render.render(write_still=True)
report = {'blender': bpy.app.version_string, 'engine': scene.render.engine,
          'render_size': [1280, 960], 'original_primitives': 3,
          'image_texture_nodes': sum(n.type == 'TEX_IMAGE' for m in (warm, cool) for n in m.node_tree.nodes),
          'material_names': [warm.name, cool.name],
          'motion_rendered': opt.animate,
          'motion_settings': {'size': [640, 480], 'fps': 12, 'frames': 24, 'seconds': 2} if opt.animate else None,
          'limitations': ['Tiny rigid-object study; client scene, deformation and production stability untested',
                          'EEVEE-specific Shader to RGB, not a Cycles material',
                          'Painterly procedural shading, not hand-painted texture artwork'],
          'client_assets_used': False}
(out / 'verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print('STUDY_RESULT ' + json.dumps(report))
