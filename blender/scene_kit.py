"""Shared helpers for the rendered Titanym scenes (run with the bpy module)."""
import math
import bpy

VOID = (0.0024, 0.0044, 0.0093, 1)  # #080E18 in linear


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def world(scene, color=VOID, strength=1.0):
    w = bpy.data.worlds.new('World')
    scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = color
    bg.inputs['Strength'].default_value = strength


def mat(name, color=(0.1, 0.1, 0.1, 1), metal=0.0, rough=0.5, emit=None, emit_strength=0.0,
        tex=None, alpha=1.0, transmission=0.0, ior=1.45, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    b.inputs['Alpha'].default_value = alpha
    b.inputs['Transmission Weight'].default_value = transmission
    b.inputs['IOR'].default_value = ior
    b.inputs['Coat Weight'].default_value = coat
    if tex:
        t = nt.nodes.new('ShaderNodeTexImage')
        t.image = bpy.data.images.load(tex)
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    if emit:
        b.inputs['Emission Color'].default_value = emit
        b.inputs['Emission Strength'].default_value = emit_strength
    return m


def bsdf(m):
    return m.node_tree.nodes['Principled BSDF']


def key_alpha(m, frame, value):
    """Keyframe a material's opacity (Cycles respects animated Alpha)."""
    b = bsdf(m)
    b.inputs['Alpha'].default_value = value
    b.inputs['Alpha'].keyframe_insert('default_value', frame=frame)


def key_emit(m, frame, value):
    b = bsdf(m)
    b.inputs['Emission Strength'].default_value = value
    b.inputs['Emission Strength'].keyframe_insert('default_value', frame=frame)


def box(name, size, loc, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new('Bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
        bpy.ops.object.shade_smooth()
        o.data.shade_auto_smooth() if hasattr(o.data, 'shade_auto_smooth') else None
    o.data.materials.append(m)
    return o


def cyl(name, r, depth, loc, m, verts=64, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    bpy.ops.object.shade_smooth()
    o.data.materials.append(m)
    return o


def top_uv(o):
    """Planar UVs from the top view, so a texture covers the top face edge to edge."""
    me = o.data
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    uv = me.uv_layers.new(name='UVMap') if not me.uv_layers else me.uv_layers[0]
    for poly in me.polygons:
        for li in poly.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((v.x - x0) / (x1 - x0 or 1), (v.y - y0) / (y1 - y0 or 1))


def area(scene, name, loc, energy, color, size, target=(0, 0, 0)):
    d = bpy.data.lights.new(name, 'AREA')
    d.energy = energy
    d.color = color
    d.size = size
    o = bpy.data.objects.new(name, d)
    o.location = loc
    scene.collection.objects.link(o)
    aim(o, target)
    return o


def aim(o, target):
    e = bpy.data.objects.new(o.name + '_target', None)
    e.location = target
    bpy.context.scene.collection.objects.link(e)
    c = o.constraints.new('TRACK_TO')
    c.target = e
    c.track_axis = 'TRACK_NEGATIVE_Z'
    c.up_axis = 'UP_Y'


def camera(scene, loc, target, lens=50):
    d = bpy.data.cameras.new('Cam')
    d.lens = lens
    o = bpy.data.objects.new('Cam', d)
    o.location = loc
    scene.collection.objects.link(o)
    scene.camera = o
    aim(o, target)
    return o


def render_settings(scene, w, h, samples=32):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.cycles.transmission_bounces = 6
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.fps = 24
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Punchy'
    scene.render.image_settings.file_format = 'JPEG'
    scene.render.image_settings.quality = 92


def interp(kind):
    """Interpolation for keyframes inserted from now on: 'LINEAR' or 'BEZIER'."""
    bpy.context.preferences.edit.keyframe_new_interpolation_type = kind


def render_range(scene, start, end, out):
    scene.frame_start = start
    scene.frame_end = end
    scene.render.filepath = out
    bpy.ops.render.render(animation=True)
