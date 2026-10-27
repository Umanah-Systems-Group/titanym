"""Builds the Titanym two-sided sapphire wafer in Blender and exports images/titanym-wafer.glb.

Run headless:  python build_chip.py <texture_dir> <out_dir>
(uses the `bpy` module, i.e. Blender as a Python package)
"""
import math, sys
import bpy, bmesh

TEX, OUT = sys.argv[-2], sys.argv[-1]
SEG = 160

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def image(name):
    img = bpy.data.images.load(f'{TEX}/{name}')
    return img

def material(name, color=(0.1, 0.1, 0.1, 1), metal=0.0, rough=0.5, emit=None, emit_strength=1.0,
             tex=None, emit_tex=None, alpha=1.0, transmission=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = color
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    b.inputs['Alpha'].default_value = alpha
    b.inputs['Transmission Weight'].default_value = transmission
    if tex:
        t = nt.nodes.new('ShaderNodeTexImage'); t.image = image(tex)
        nt.links.new(t.outputs['Color'], b.inputs['Base Color'])
    if emit_tex:
        e = nt.nodes.new('ShaderNodeTexImage'); e.image = image(emit_tex)
        nt.links.new(e.outputs['Color'], b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value = emit_strength
    elif emit:
        b.inputs['Emission Color'].default_value = emit
        b.inputs['Emission Strength'].default_value = emit_strength
    if alpha < 1:
        m.surface_render_method = 'BLENDED'
    return m

def link(obj, parent):
    obj.parent = parent
    for c in obj.users_collection: c.objects.unlink(obj)
    scene.collection.objects.link(obj)

def disc(name, r, z, mat, flip=False):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    verts = [bm.verts.new((r * math.cos(2 * math.pi * i / SEG), r * math.sin(2 * math.pi * i / SEG), z)) for i in range(SEG)]
    f = bm.faces.new(verts[::-1] if flip else verts)
    uv = bm.loops.layers.uv.new()
    for loop in f.loops:
        x, y, _ = loop.vert.co
        loop[uv].uv = ((x / r + 1) / 2, (y / r + 1) / 2)
    bmesh.ops.triangulate(bm, faces=[f], quad_method='BEAUTY', ngon_method='BEAUTY')
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(mat)
    scene.collection.objects.link(ob)
    return ob

def band(name, r, z0, z1, mat):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    lo = [bm.verts.new((r * math.cos(2 * math.pi * i / SEG), r * math.sin(2 * math.pi * i / SEG), z0)) for i in range(SEG)]
    hi = [bm.verts.new((v.co.x, v.co.y, z1)) for v in lo]
    for i in range(SEG):
        j = (i + 1) % SEG
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(mat)
    scene.collection.objects.link(ob)
    return ob

def sector(name, a0, a1, h, top_mat, bottom_mat, side_mat, cut_mat, rim_mat=None, r=1.0):
    """One pie piece of a wafer layer, from angle a0 to a1 (degrees), with flat cut faces."""
    n = max(4, int(SEG * (a1 - a0) / 360))
    angs = [math.radians(a0 + (a1 - a0) * i / n) for i in range(n + 1)]
    mats = [top_mat, bottom_mat, side_mat, cut_mat] + ([rim_mat] if rim_mat else [])
    me = bpy.data.meshes.new(name)
    for m in mats: me.materials.append(m)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    def v(x, y, z): return bm.verts.new((x, y, z))
    ct, cb = v(0, 0, h), v(0, 0, -h)
    top = [v(r * math.cos(a), r * math.sin(a), h) for a in angs]
    bot = [v(r * math.cos(a), r * math.sin(a), -h) for a in angs]
    def face(vs, mi):
        f = bm.faces.new(vs); f.material_index = mi
        for loop in f.loops:
            x, y, _ = loop.vert.co
            loop[uv].uv = ((x / r + 1) / 2, (y / r + 1) / 2)
        return f
    for i in range(n):
        face((ct, top[i], top[i + 1]), 0)
        face((cb, bot[i + 1], bot[i]), 1)
        f = face((bot[i], bot[i + 1], top[i + 1], top[i]), 2); f.smooth = True
    face((cb, ct, top[0], bot[0]), 3)          # cut face at a0
    face((ct, cb, bot[-1], top[-1]), 3)        # cut face at a1
    if rim_mat:
        rr = r * 1.003
        rl = [v(rr * math.cos(a), rr * math.sin(a), h - 0.006) for a in angs]
        rh = [v(rr * math.cos(a), rr * math.sin(a), h + 0.002) for a in angs]
        for i in range(n):
            f = face((rl[i], rl[i + 1], rh[i + 1], rh[i]), 4); f.smooth = True
    bm.normal_update()
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    return ob

WEDGE = (-135, -45)   # the cutaway wedge faces the viewer (Blender -Y is glTF +Z)

def layer(name, thick, top_mat, side_mat, bottom_mat, cut_mat, rim_mat=None):
    root = bpy.data.objects.new(name, None)
    scene.collection.objects.link(root)
    h = thick / 2
    link(sector(f'{name}_main', WEDGE[1], WEDGE[0] + 360, h, top_mat, bottom_mat, side_mat, cut_mat, rim_mat), root)
    wedge = bpy.data.objects.new(f'{name}_wedge', None)
    link(wedge, root)
    link(sector(f'{name}_wedgebody', WEDGE[0], WEDGE[1], h, top_mat, bottom_mat, side_mat, cut_mat, rim_mat), wedge)
    return root

# Materials
dark = material('Underside', (0.03, 0.035, 0.05, 1), metal=0.6, rough=0.4)
rf_top = material('RF face', tex='rf_color.jpg', emit_tex='rf_emit.jpg', emit_strength=2.2, metal=0.55, rough=0.32)
rf_side = material('RF edge', (0.42, 0.29, 0.1, 1), metal=1.0, rough=0.22)
gold_rim = material('Gold rim', (0.9, 0.62, 0.2, 1), metal=1.0, rough=0.15, emit=(0.91, 0.63, 0.19, 1), emit_strength=1.6)
sa_top = material('Sapphire face', tex='sapph_color.jpg', emit_tex='sapph_emit.jpg', emit_strength=3.0, rough=0.08, alpha=0.85)
sa_side = material('Sapphire edge', (0.1, 0.3, 0.9, 1), rough=0.05, emit=(0.12, 0.38, 1.0, 1), emit_strength=2.6, alpha=0.75)
sa_bottom = material('Sapphire underside', (0.1, 0.25, 0.75, 1), rough=0.1, emit=(0.1, 0.3, 0.9, 1), emit_strength=1.2, alpha=0.6)
si_top = material('SiGe face', tex='sige_color.jpg', emit_tex='sige_emit.jpg', emit_strength=2.0, metal=0.5, rough=0.3)
si_side = material('SiGe edge', (0.25, 0.32, 0.42, 1), metal=1.0, rough=0.25)
blue_rim = material('Blue rim', (0.35, 0.6, 1.0, 1), metal=0.8, rough=0.2, emit=(0.3, 0.55, 1.0, 1), emit_strength=1.6)
rf_cut = material('RF cut', (0.32, 0.22, 0.08, 1), metal=0.9, rough=0.3, emit=(0.91, 0.55, 0.15, 1), emit_strength=0.5)
sa_cut = material('Sapphire cut', (0.15, 0.38, 1.0, 1), rough=0.05, emit=(0.2, 0.45, 1.0, 1), emit_strength=2.2, alpha=0.85)
si_cut = material('SiGe cut', (0.3, 0.37, 0.47, 1), metal=0.9, rough=0.3, emit=(0.3, 0.5, 0.9, 1), emit_strength=0.4)

# Layers, assembled (the web viewer moves them apart and slides the wedges out)
rf = layer('RF', 0.05, rf_top, rf_side, dark, rf_cut, gold_rim); rf.location.z = 0.085
sa = layer('Sapphire', 0.12, sa_top, sa_side, sa_bottom, sa_cut)
si = layer('SiGe', 0.05, si_top, si_side, si_top, si_cut, blue_rim); si.location.z = -0.085

bpy.ops.export_scene.gltf(
    filepath=f'{OUT}/titanym-wafer.glb', export_format='GLB',
    export_image_format='JPEG', export_jpeg_quality=85,
    export_yup=True, export_apply=False, export_lights=False, export_cameras=False)

import os
if os.environ.get('NO_RENDER'):
    bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/titanym-wafer.blend'); sys.exit(0)

# Poster still rendered in Cycles, exploded, for the page fallback and social card
rf.location.z = 0.42; si.location.z = -0.42
for n in ('RF_wedge', 'Sapphire_wedge', 'SiGe_wedge'): bpy.data.objects[n].location.y = -0.5
world = bpy.data.worlds.new('W'); scene.world = world; world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.012, 0.02, 0.035, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
def light(name, kind, loc, energy, color, size=2.0):
    d = bpy.data.lights.new(name, kind); d.energy = energy; d.color = color
    if kind == 'AREA': d.size = size
    o = bpy.data.objects.new(name, d); o.location = loc; scene.collection.objects.link(o)
    o.rotation_euler = (loc[0] and 0, 0, 0)
    c = o.constraints.new('TRACK_TO'); c.target = sa; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
light('Key', 'AREA', (2.5, -2.5, 3.5), 900, (1.0, 0.85, 0.65), 3)
light('Rim', 'AREA', (-3, 3, 1.0), 700, (0.45, 0.65, 1.0), 3)
light('Fill', 'AREA', (0, -4, -1.5), 250, (0.4, 0.6, 1.0), 4)
cam_d = bpy.data.cameras.new('Cam'); cam_d.lens = 50
cam = bpy.data.objects.new('Cam', cam_d); scene.collection.objects.link(cam); scene.camera = cam
cam.location = (0, -4.6, 2.9)
c = cam.constraints.new('TRACK_TO'); c.target = sa; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
sa.rotation_euler.z = rf.rotation_euler.z = si.rotation_euler.z = math.radians(20)
scene.render.engine = 'CYCLES'; scene.cycles.samples = 96; scene.cycles.device = 'CPU'
scene.render.resolution_x = 1400; scene.render.resolution_y = 1100
scene.render.film_transparent = True
scene.view_settings.view_transform = 'AgX'; scene.view_settings.look = 'AgX - Punchy'
scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGBA'
scene.render.filepath = f'{OUT}/titanym-wafer-render.png'
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/titanym-wafer.blend')
print('built')
