"""Looping scenes for the application cards and the Why Titanym cards.

python scene_cards.py <tex_dir> <out_dir> <scene>
scene = radar | telecom | space | rugged | closer | isolation | interfaces | heat | lattice
Every scene is a seamless loop of N frames: all motion is a periodic function of t = (frame - 1) / N.
FRAMES=1,30 renders preview stills at half size instead.
"""
import math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import scene_kit as k

TEX, OUT, NAME = sys.argv[-3], sys.argv[-2], sys.argv[-1]
N = 72
TAU = 2 * math.pi
random.seed(7)
sc = k.reset()
k.interp('LINEAR')


# ---------- helpers ----------
def key(o, path, value, f):
    setattr(o, path, value)
    o.keyframe_insert(path, frame=f)


def key_in(inp, value, f):
    inp.default_value = value
    inp.keyframe_insert('default_value', frame=f)


def bake(fn):
    for i in range(N + 1):
        fn(i / N, i + 1)


def glow(name, color, strength=4.0, fade_z=False, soft=False):
    """Additive light-like material. fade_z: brightest at the mesh's local top (generated Z=1)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    add = nt.nodes.new('ShaderNodeAddShader')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = color
    em.inputs['Strength'].default_value = strength
    nt.links.new(tr.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs[0])
    fac = None
    if fade_z:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        pw = nt.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 2.2
        nt.links.new(tc.outputs['Generated'], sep.inputs[0])
        nt.links.new(sep.outputs['Z'], pw.inputs[0])
        fac = pw.outputs[0]
    if soft:
        lw = nt.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.35
        inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
        nt.links.new(lw.outputs['Facing'], inv.inputs[1])
        if fac is not None:
            mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
            nt.links.new(fac, mul.inputs[0]); nt.links.new(inv.outputs[0], mul.inputs[1]); fac = mul.outputs[0]
        else:
            fac = inv.outputs[0]
    if fac is not None:
        mix = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(fac, mix.inputs[0])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(add.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs[0])
    m['em'] = em.name
    return m


def em_strength(m):
    return m.node_tree.nodes[m['em']].inputs['Strength']


def cells(name, c1, c2, mortar, scale, emit=0.0, metal=0.0, rough=0.4, mortar_size=0.02, offset=0.0):
    """Grid-of-cells material (solar cells, array elements, windows) from the brick texture."""
    m = k.mat(name, metal=metal, rough=rough)
    nt = m.node_tree
    b = k.bsdf(m)
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.offset = offset
    br.inputs['Color1'].default_value = c1
    br.inputs['Color2'].default_value = c2
    br.inputs['Mortar'].default_value = mortar
    br.inputs['Scale'].default_value = scale
    br.inputs['Mortar Size'].default_value = mortar_size
    br.inputs['Brick Width'].default_value = 0.5
    br.inputs['Row Height'].default_value = 0.5
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(tc.outputs['UV'], br.inputs['Vector'])
    nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    if emit:
        nt.links.new(br.outputs['Color'], b.inputs['Emission Color'])
        b.inputs['Emission Strength'].default_value = emit
    return m


def rod(name, p1, p2, r, m, verts=12):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(p1 + p2) / 2)
    o = bpy.context.object
    o.name = name
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = d.to_track_quat('Z', 'Y')
    o.data.materials.append(m)
    return o


def sphere(name, r, loc, m, seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.object
    o.name = name
    bpy.ops.object.shade_smooth()
    o.data.materials.append(m)
    return o


def torus(name, R, r, loc, m):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, major_segments=64, minor_segments=10)
    o = bpy.context.object
    o.name = name
    bpy.ops.object.shade_smooth()
    o.data.materials.append(m)
    return o


def cone(name, r_far, length, m):
    """A light cone with its apex at the object origin, pointing along local +Z... apex at top."""
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=r_far, radius2=0.01, depth=length, location=(0, 0, -length / 2))
    o = bpy.context.object
    o.name = name
    bpy.ops.object.transform_apply(location=True)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(m)
    return o  # apex at origin, opening towards -Z


def starry_world(strength=1.0, base=(0.004, 0.007, 0.016, 1)):
    w = bpy.data.worlds.new('World'); sc.world = w; w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 260
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.0; ramp.color_ramp.elements[0].color = (1, 1, 1, 1)
    ramp.color_ramp.elements[1].position = 0.06; ramp.color_ramp.elements[1].color = base
    nt.links.new(tc.outputs['Generated'], vor.inputs['Vector'])
    nt.links.new(vor.outputs['Distance'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    bg.inputs['Strength'].default_value = strength


def sun(name, rot, energy, color):
    d = bpy.data.lights.new(name, "SUN"); d.energy = energy; d.color = color[:3]; d.angle = math.radians(2)
    o = bpy.data.objects.new(name, d); o.rotation_euler = [math.radians(a) for a in rot]
    sc.collection.objects.link(o)
    return o


def point(name, loc, energy, color, r=0.2):
    d = bpy.data.lights.new(name, "POINT"); d.energy = energy; d.color = color[:3]; d.shadow_soft_size = r
    o = bpy.data.objects.new(name, d); o.location = loc; sc.collection.objects.link(o)
    return o


AMBER = (1.0, 0.62, 0.18, 1)
GOLD = (1.0, 0.78, 0.38, 1)
SAPPH = (0.25, 0.5, 1.0, 1)
gold = k.mat('Gold', (1.0, 0.72, 0.32, 1), metal=1.0, rough=0.22)
alu = k.mat('Anodized', (0.05, 0.055, 0.06, 1), metal=0.85, rough=0.38)
steel = k.mat('Steel', (0.5, 0.53, 0.57, 1), metal=1.0, rough=0.3)
white = k.mat('Panel white', (0.75, 0.77, 0.8, 1), rough=0.45)
ground_dark = k.mat('Ground', (0.012, 0.016, 0.024, 1), rough=0.8)
gan = k.mat('GaN die', tex=f'{TEX}/die_gan.jpg', metal=0.65, rough=0.28)
sige = k.mat('SiGe die', tex=f'{TEX}/die_sige.jpg', metal=0.7, rough=0.25)
sapph = k.mat('Sapphire', (0.2, 0.45, 1.0, 1), rough=0.04, transmission=1.0, ior=1.77,
              emit=(0.15, 0.35, 1.0, 1), emit_strength=0.5)
W, H = 960, 576   # application cards (5:3)


# ---------- application scenes ----------
def radar():
    k.world(sc, (0.004, 0.007, 0.016, 1), 1.0)
    g = k.box('Ground', (60, 60, 0.02), (0, 0, -0.01), ground_dark)
    grid = cells('Grid', (0.01, 0.015, 0.025, 1), (0.01, 0.015, 0.025, 1), (0.1, 0.25, 0.6, 1), 30, emit=0.0, mortar_size=0.015)
    k.bsdf(grid).inputs['Emission Strength'].default_value = 0
    # grid glow from the mortar lines
    nt = grid.node_tree; br = [n for n in nt.nodes if n.type == 'TEX_BRICK'][0]
    gm = nt.nodes.new('ShaderNodeMath'); gm.operation = 'MULTIPLY'; gm.inputs[1].default_value = 0.35
    nt.links.new(br.outputs['Fac'], gm.inputs[0]); nt.links.new(gm.outputs[0], k.bsdf(grid).inputs['Emission Strength'])
    k.bsdf(grid).inputs['Emission Color'].default_value = (0.12, 0.28, 0.7, 1)
    g.data.materials[0] = grid; k.top_uv(g)
    # Vehicle-mounted array: chassis, turret, tilted AESA face
    k.box('Chassis', (2.6, 1.5, 0.5), (-3, 0, 0.45), alu, bevel=0.05)
    for x in (-3.8, -2.2):
        for y in (-0.8, 0.8):
            o = k.cyl('Wheel', 0.36, 0.28, (x, y, 0.36), k.mat('Tyre', (0.01, 0.01, 0.01, 1), rough=0.9), rot=(math.radians(90), 0, 0))
    k.cyl('Turret', 0.5, 0.35, (-3, 0, 0.88), steel)
    piv = bpy.data.objects.new('Pivot', None); piv.location = (-3, 0, 1.9); sc.collection.objects.link(piv)
    panel = k.box('Array back', (0.18, 2.0, 1.5), (0, 0, 0), alu, bevel=0.03)
    elems = cells('Array elements', (1.0, 0.6, 0.15, 1), (0.7, 0.4, 0.1, 1), (0.02, 0.025, 0.03, 1), 14,
                  emit=1.5, metal=0.8, rough=0.3, mortar_size=0.03)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0.095, 0, 0), rotation=(0, math.radians(90), 0))
    face = bpy.context.object; face.scale = (1.4, 1.9, 1); bpy.ops.object.transform_apply(scale=True)
    face.data.materials.append(elems)
    for o in (panel, face):
        o.parent = piv
    piv.rotation_euler = (0, math.radians(-14), 0)
    rod('Strut', (-3, 0, 1.0), (-3, 0, 1.6), 0.12, steel)
    # Beam
    beam_m = glow('Beam', AMBER, 0.7, fade_z=True, soft=True)
    beam = cone('Beam', 3.2, 16, beam_m)
    beam_root = bpy.data.objects.new('BeamRoot', None); beam_root.location = (-2.85, 0, 1.9)
    sc.collection.objects.link(beam_root)
    beam.parent = beam_root; beam.rotation_euler = (0, math.radians(-96), 0)
    # Targets on a far circuit
    jet_m = k.mat('Jet', (0.3, 0.32, 0.36, 1), metal=0.6, rough=0.4)
    ping_m = glow('Ping', AMBER, 0.0)
    jets = []
    for n in range(3):
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.45, radius2=0, depth=0.08)
        j = bpy.context.object; j.data.materials.append(jet_m); j.scale = (1.6, 1, 1)
        ring = torus(f'Ping{n}', 0.6, 0.02, (0, 0, 0), ping_m if n == 0 else ping_m.copy())
        jets.append((j, ring, n))
    point('Array glow', (-1.8, 0, 2.0), 300, AMBER, 0.5)
    sun('Moon', (55, 0, 30), 0.6, (0.6, 0.7, 1.0))
    k.area(sc, 'Rim', (-6, 5, 5), 600, (0.5, 0.65, 1.0), 5, (-3, 0, 1))
    k.area(sc, 'Key', (2, -6, 5), 900, (1.0, 0.88, 0.75), 5, (-3, 0, 1))
    k.camera(sc, (3.5, -9.5, 3.4), (-0.5, 0, 1.6), lens=30)

    def frame(t, f):
        yaw = math.radians(32) * math.sin(TAU * t)
        key(beam_root, 'rotation_euler', (0, 0, yaw), f)
        key(piv, 'rotation_euler', (0, math.radians(-14), yaw), f)
        key_in(k.bsdf(elems).inputs['Emission Strength'], 1.2 + 0.8 * (0.5 + 0.5 * math.sin(TAU * 4 * t)), f)
        for j, ring, n in jets:
            a = TAU * (t + n / 3)
            ang = math.radians(-26 + n * 26) + math.radians(6) * math.sin(a)
            dist = 9 + n * 1.5
            pos = Vector((-2.85 + dist * math.cos(ang), dist * math.sin(ang), 3.4 + 0.6 * n + 0.2 * math.sin(a)))
            key(j, 'location', pos, f)
            key(j, 'rotation_euler', (0, 0, ang + math.radians(90)), f)
            key(ring, 'location', pos, f)
            # bright when the beam sweeps over the target
            d = abs(ang - yaw)
            hit = math.exp(-(d / math.radians(7)) ** 2)
            key(ring, 'scale', [0.4 + 1.6 * hit] * 3, f)
            key_in(em_strength(ring.data.materials[0]), 30 * hit, f)
    bake(frame)


def telecom():
    w = bpy.data.worlds.new('World'); sc.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes['Background']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.45; ramp.color_ramp.elements[0].color = (0.012, 0.018, 0.035, 1)
    ramp.color_ramp.elements[1].position = 0.65; ramp.color_ramp.elements[1].color = (0.004, 0.008, 0.02, 1)
    nt.links.new(tc.outputs['Generated'], sep.inputs[0]); nt.links.new(sep.outputs['Z'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bg.inputs['Color'])
    k.box('Ground', (80, 80, 0.02), (0, 0, -0.01), ground_dark)
    win = cells('Windows', (1.0, 0.75, 0.4, 1), (0.08, 0.1, 0.14, 1), (0.02, 0.025, 0.035, 1), 18,
                emit=0.7, rough=0.3, mortar_size=0.08)
    [n for n in win.node_tree.nodes if n.type == 'TEX_BRICK'][0].inputs['Bias'].default_value = 0.75
    concrete = k.mat('Concrete', (0.03, 0.035, 0.045, 1), rough=0.7)
    random.seed(3)
    roofs = []
    for i in range(70):
        a = random.uniform(0, TAU); r = random.uniform(4.5, 22)
        x, y = r * math.cos(a), r * math.sin(a)
        if y < -2 and abs(x) < 7:
            continue
        h = random.uniform(1.2, 6.5) * (1.3 if r > 10 else 1)
        bw = random.uniform(1.0, 2.2)
        b = k.box(f'Bldg{i}', (bw, bw, h), (x, y, h / 2), concrete)
        b.data.materials.append(win)
        # windows on the side faces only
        for p in b.data.polygons:
            if abs(p.normal.z) < 0.5:
                p.material_index = 1
        uv = b.data.uv_layers.new(name='UVMap')
        for p in b.data.polygons:
            for li in p.loop_indices:
                v = b.data.vertices[b.data.loops[li].vertex_index].co
                uv.data[li].uv = ((v.x + v.y) / 3, v.z / 3)
        roofs.append(Vector((x, y, h)))
    # Lattice tower
    Ht = 9.0
    def leg(i, z):
        s = 0.9 * (1 - z / Ht) + 0.22
        a = TAU * i / 3 + math.radians(90)
        return (s * math.cos(a), s * math.sin(a), z)
    tower_m = k.mat('Tower', (0.6, 0.62, 0.66, 1), metal=0.9, rough=0.35)
    levels = [Ht * i / 9 for i in range(10)]
    for i in range(3):
        rod(f'Leg{i}', leg(i, 0), leg(i, Ht), 0.05, tower_m)
        for z0, z1 in zip(levels, levels[1:]):
            rod('Brace', leg(i, z0), leg((i + 1) % 3, z1), 0.018, tower_m, 6)
            rod('Ring', leg(i, z1), leg((i + 1) % 3, z1), 0.018, tower_m, 6)
    # Sector antennas and a microwave dish
    for i in range(3):
        a = TAU * i / 3 + math.radians(30)
        p = Vector((0.55 * math.cos(a), 0.55 * math.sin(a), Ht - 0.6))
        o = k.box(f'Sector{i}', (0.12, 0.38, 1.4), p, white, bevel=0.03)
        o.rotation_euler = (0, 0, a)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.45, location=(0.2, -0.75, Ht - 2.4))
    dish = bpy.context.object; dish.scale = (1, 0.35, 1); dish.data.materials.append(white); bpy.ops.object.shade_smooth()
    top_m = k.mat('Beacon', (1, 0.1, 0.05, 1), emit=(1, 0.1, 0.05, 1), emit_strength=20)
    sphere('Beacon', 0.07, (0, 0, Ht + 0.08), top_m, 16)
    # Expanding coverage rings and links to rooftops
    ring_ms = [glow(f'Wave{n}', AMBER, 0) for n in range(4)]
    rings = [torus(f'Wave{n}', 1.0, 0.012, (0, 0, Ht - 0.6), ring_ms[n]) for n in range(4)]
    link_m = glow('Link', (0.35, 0.6, 1.0, 1), 1.2)
    pulse_m = glow('Pulse', GOLD, 40)
    targets = sorted(roofs, key=lambda v: (v - Vector((0, 0, 0))).length)[::7][:6]
    links = []
    for n, tgt in enumerate(targets):
        a = Vector((0, 0, Ht - 0.6))
        rod(f'Link{n}', a, tgt, 0.012, link_m, 6)
        links.append((a, tgt, sphere(f'Pulse{n}', 0.09, a, pulse_m, 12), n))
    sun('Moon', (60, 0, -40), 0.4, (0.55, 0.65, 1.0))
    k.area(sc, 'Tower light', (3, -4, 6), 500, (1.0, 0.8, 0.6), 4, (0, 0, 6))
    k.camera(sc, (5.2, -12.5, 2.2), (0, 0, 5.4), lens=28)

    def frame(t, f):
        for n, (r, m) in enumerate(zip(rings, ring_ms)):
            u = (t + n / 4) % 1
            s = 0.5 + 16 * u
            key(r, 'scale', (s, s, 1 + 6 * u), f)
            key_in(em_strength(m), 2.5 * (1 - u) ** 2, f)
        for a, b, p, n in links:
            u = (2 * t + n / 6) % 1
            key(p, 'location', a.lerp(b, u), f)
        key_in(k.bsdf(top_m).inputs['Emission Strength'], 30 if (t * 4) % 1 < 0.5 else 1, f)
    bake(frame)


def space():
    starry_world(1.0)
    # Earth below
    nt_m = bpy.data.materials.new('Earth'); nt_m.use_nodes = True
    nt = nt_m.node_tree; b = nt.nodes['Principled BSDF']
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 3.0; noise.inputs['Detail'].default_value = 8
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.52; ramp.color_ramp.elements[0].color = (0.01, 0.04, 0.12, 1)
    ramp.color_ramp.elements[1].position = 0.56; ramp.color_ramp.elements[1].color = (0.06, 0.08, 0.05, 1)
    nt.links.new(noise.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.6
    clouds = nt.nodes.new('ShaderNodeTexNoise'); clouds.inputs['Scale'].default_value = 7; clouds.inputs['Detail'].default_value = 6
    cr = nt.nodes.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].position = 0.55; cr.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr.color_ramp.elements[1].position = 0.7; cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    nt.links.new(clouds.outputs['Fac'], cr.inputs['Fac'])
    nt.links.new(cr.outputs['Color'], mix.inputs['Factor'])
    nt.links.new(ramp.outputs['Color'], mix.inputs['A'])
    mix.inputs['B'].default_value = (0.6, 0.65, 0.7, 1)
    nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
    earth = sphere('Earth', 12, (0, 0, -13.2), nt_m, 96)
    atm = glow('Atmosphere', (0.25, 0.55, 1.0, 1), 3.0)
    ant = atm.node_tree
    lw = ant.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.2
    em = ant.nodes[atm['em']]
    pw = ant.nodes.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 5
    mul = ant.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 5
    ant.links.new(lw.outputs['Facing'], pw.inputs[0]); ant.links.new(pw.outputs[0], mul.inputs[0])
    ant.links.new(mul.outputs[0], em.inputs['Strength'])
    sphere('Atmosphere', 12.35, (0, 0, -13.2), atm, 96)
    # Satellite
    sat = bpy.data.objects.new('Sat', None); sat.location = (0.3, 0, 1.5); sc.collection.objects.link(sat)
    foil = k.mat('Foil', (1.0, 0.7, 0.25, 1), metal=1.0, rough=0.35)
    fn = foil.node_tree
    bump = fn.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.4
    vn = fn.nodes.new('ShaderNodeTexVoronoi'); vn.inputs['Scale'].default_value = 30
    fn.links.new(vn.outputs['Distance'], bump.inputs['Height']); fn.links.new(bump.outputs['Normal'], k.bsdf(foil).inputs['Normal'])
    parts = [k.box('Bus', (0.7, 0.7, 0.9), (0, 0, 0), foil, bevel=0.02)]
    solar = cells('Solar cells', (0.03, 0.07, 0.22, 1), (0.02, 0.05, 0.18, 1), (0.5, 0.55, 0.6, 1), 10,
                  metal=0.6, rough=0.15, mortar_size=0.02)
    for s in (-1, 1):
        parts.append(rod('Boom', (s * 0.35, 0, 0), (s * 0.75, 0, 0), 0.025, steel))
        for seg in range(3):
            cx = s * (1.15 + seg * 0.82)
            bpy.ops.mesh.primitive_plane_add(size=1, location=(cx, 0, 0))
            p = bpy.context.object; p.scale = (0.78, 0.62, 1); bpy.ops.object.transform_apply(scale=True)
            p.data.materials.append(solar)
            sol = p.modifiers.new('Thick', 'SOLIDIFY'); sol.thickness = 0.02
            parts.append(p)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.32, location=(0, 0, -0.62))
    dish = bpy.context.object; dish.scale = (1, 1, 0.35); dish.data.materials.append(white); bpy.ops.object.shade_smooth()
    parts += [dish, rod('Feed', (0, 0, -0.62), (0, 0, -0.95), 0.015, steel), rod('Mast', (0.2, 0.2, 0.45), (0.2, 0.2, 0.95), 0.012, steel)]
    for p in parts:
        p.parent = sat
    # Downlink beam with travelling pulses
    beam = cone('Downlink', 1.8, 9.0, glow('Downlink', (0.35, 0.6, 1.0, 1), 1.6, fade_z=True, soft=True))
    beam.location = (0.3, 0, 0.6)
    pm = [glow(f'Pulse{n}', GOLD, 0) for n in range(3)]
    pulses = [torus(f'Pulse{n}', 0.3, 0.02, (0.3, 0, 0.5), pm[n]) for n in range(3)]
    sun('Sun', (60, 10, 70), 4.0, (1.0, 0.95, 0.88))
    k.area(sc, 'Earthshine', (0, 0, -6), 300, (0.3, 0.5, 1.0), 10, (0, 0, 1.5))
    k.camera(sc, (-2.4, -5.8, 2.2), (0.3, 0, 1.0), lens=32)

    def frame(t, f):
        key(sat, 'rotation_euler', (math.radians(4) * math.sin(TAU * t), 0, math.radians(18) + math.radians(10) * math.sin(TAU * t)), f)
        key(earth, 'rotation_euler', (0, math.radians(3) * math.sin(TAU * t), 0), f)
        for n, (p, m) in enumerate(zip(pulses, pm)):
            u = (t * 2 + n / 3) % 1
            key(p, 'location', (0.3, 0, 0.5 - 6.5 * u), f)
            s = 0.4 + 4.6 * u
            key(p, 'scale', (s, s, 1), f)
            key_in(em_strength(m), 18 * math.sin(math.pi * u) ** 2, f)
    bake(frame)


def rugged():
    k.world(sc, (0.05, 0.035, 0.02, 1), 0.6)
    sand = k.mat('Sand', (0.35, 0.24, 0.14, 1), rough=0.9)
    sn = sand.node_tree
    nz = sn.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 6
    bm = sn.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.6
    sn.links.new(nz.outputs['Fac'], bm.inputs['Height']); sn.links.new(bm.outputs['Normal'], k.bsdf(sand).inputs['Normal'])
    k.box('Ground', (60, 60, 0.02), (0, 0, -0.01), sand)
    root = bpy.data.objects.new('Module', None); sc.collection.objects.link(root)
    ano = k.mat('Housing', (0.08, 0.09, 0.08, 1), metal=0.9, rough=0.42)
    parts = [k.box('Housing', (2.8, 1.8, 0.7), (0, 0, 0.45), ano, bevel=0.06),
             k.box('Flange', (3.3, 2.0, 0.08), (0, 0, 0.08), ano, bevel=0.02)]
    for i in range(14):
        x = -1.25 + i * (2.5 / 13)
        parts.append(k.box('Fin', (0.05, 1.6, 0.42), (x, 0, 0.98), ano, bevel=0.01))
    for x in (-1.5, 1.5):
        for y in (-0.88, 0.88):
            parts.append(k.cyl('Bolt', 0.06, 0.05, (x, y, 0.14), steel, verts=6))
    conn = k.mat('Connector', (0.55, 0.5, 0.35, 1), metal=1.0, rough=0.3)
    for i, x in enumerate((-0.8, 0.0, 0.8)):
        c = k.cyl('Connector', 0.2, 0.3, (x, -0.98, 0.45), conn, verts=32, rot=(math.radians(90), 0, 0))
        parts.append(c)
        parts.append(k.cyl('Bore', 0.13, 0.31, (x, -0.99, 0.45), k.mat('Bore', (0.01, 0.01, 0.01, 1)), verts=32, rot=(math.radians(90), 0, 0)))
    leds = []
    for i, x in enumerate((1.1, 1.25, 1.4)):
        m = k.mat(f'LED{i}', (0.2, 1, 0.4, 1) if i < 2 else (1, 0.6, 0.1, 1), emit=(0.2, 1, 0.4, 1) if i < 2 else (1, 0.6, 0.1, 1), emit_strength=0)
        leds.append(sphere(f'LED{i}', 0.035, (x, -0.905, 0.72), m, 12))
    plate = k.mat('Label plate', (0.6, 0.62, 0.64, 1), metal=1.0, rough=0.25)
    parts.append(k.box('Plate', (0.8, 0.01, 0.22), (-0.2, -0.905, 0.72), plate))
    for p in parts + leds:
        p.parent = root
    # Blowing dust
    dust_m = k.mat('Dust', (0.75, 0.55, 0.35, 1), rough=1.0, alpha=0.6)
    dust = []
    for i in range(160):
        p = Vector((random.uniform(-9, 9), random.uniform(-6, 5), random.uniform(0.05, 3.2)))
        d = sphere('Dust', random.uniform(0.008, 0.025), p, dust_m, 8)
        dust.append((d, p, random.uniform(0.5, 1.5)))
    sun('Sun', (40, 0, 120), 5.0, (1.0, 0.82, 0.6))
    k.area(sc, 'Fill', (-3, -5, 2), 300, (0.6, 0.7, 1.0), 4, (0, 0, 0.5))
    k.camera(sc, (3.4, -5.6, 2.6), (0.1, 0, 0.5), lens=38)

    def frame(t, f):
        key(root, 'rotation_euler', (0, 0, math.radians(-14) + math.radians(14) * math.sin(TAU * t)), f)
        for i, l in enumerate(leds):
            on = 1 if ((t * 6 + i / 3) % 1) < 0.5 else 0.05
            key_in(k.bsdf(l.data.materials[0]).inputs['Emission Strength'], 25 * on, f)
        for d, p, sp in dust:
            x = (p.x + 18 * t + 9) % 18 - 9
            key(d, 'location', (x, p.y, p.z + 0.15 * math.sin(TAU * (t + p.y))), f)
    bake(frame)


# ---------- Why Titanym scenes ----------
def card_world():
    k.world(sc, (0.004, 0.007, 0.016, 1), 1.0)
    k.area(sc, 'Key', (3, -3.5, 4.5), 900, (1.0, 0.86, 0.68), 4, (0, 0, 0.3))
    k.area(sc, 'Rim', (-4, 3.5, 2.5), 900, (0.45, 0.62, 1.0), 4, (0, 0, 0.3))
    k.area(sc, 'Under', (0, -3, -1.6), 200, (0.7, 0.8, 1.0), 3, (0, 0, 0.3))


def die(name, m, loc, s=0.9, h=0.08):
    o = k.box(name, (s, s, h), loc, m, bevel=0.006); k.top_uv(o); return o


def closer():
    card_world()
    board = k.box('Board', (5.6, 2.6, 0.08), (0, 0, -0.04), k.mat('PCB', tex=f'{TEX}/pcb.jpg', rough=0.45, coat=0.6), bevel=0.02)
    k.top_uv(board)
    pk_m = k.mat('Package', (0.03, 0.032, 0.036, 1), rough=0.5, alpha=1.0)
    pk1 = k.box('PkgA', (1.3, 1.3, 0.16), (-1.7, 0, 0.08), pk_m, bevel=0.02)
    pk2 = k.box('PkgB', (1.3, 1.3, 0.16), (1.7, 0, 0.08), pk_m, bevel=0.02)
    a = die('GaN', gan, (-1.7, 0, 0.2)); b = die('SiGe', sige, (1.7, 0, 0.2))
    sap = k.box('Sapphire', (1.25, 1.25, 0.2), (0, 0, 0.4), sapph, bevel=0.02)
    line_m = glow('Link', GOLD, 3)
    pulse_m = glow('Pulse', GOLD, 40)
    pulses = [sphere(f'P{n}', 0.05, (0, 0, 0), pulse_m, 12) for n in range(3)]
    link = rod('Link', (-1, 0, 0.2), (1, 0, 0.2), 0.012, line_m, 8)
    k.camera(sc, (0, -5.2, 3.1), (0, 0, 0.25), lens=40)

    def frame(t, f):
        s = 0.5 - 0.5 * math.cos(TAU * t)          # 0 apart -> 1 together -> 0
        s = s * s * (3 - 2 * s)
        pa = Vector((-1.7, 0, 0.2)).lerp(Vector((0, 0, 0.54)), s)
        pb = Vector((1.7, 0, 0.2)).lerp(Vector((0, 0, 0.26)), s)
        key(a, 'location', pa, f); key(b, 'location', pb, f)
        key_in(k.bsdf(pk_m).inputs['Alpha'], 1 - s, f)
        sz = max(0.001, min(1, (s - 0.35) / 0.4))
        key(sap, 'scale', (sz, sz, sz), f)
        mid = (pa + pb) / 2; d = pb - pa
        key(link, 'location', mid, f)
        link.rotation_quaternion = d.to_track_quat('Z', 'Y'); link.keyframe_insert('rotation_quaternion', frame=f)
        key(link, 'scale', (1, 1, max(0.001, d.length / 2)), f)
        for n, p in enumerate(pulses):
            u = (t * 3 + n / 3) % 1
            key(p, 'location', pa.lerp(pb, u), f)
    bake(frame)


def isolation():
    card_world()
    top = die('GaN layer', gan, (0, 0, 0.42), 2.2, 0.1)
    sap = k.box('Sapphire', (2.2, 2.2, 0.5), (0, 0, 0.1), sapph, bevel=0.02)
    bot = die('SiGe layer', sige, (0, 0, -0.22), 2.2, 0.1)
    spark_ms, sparks = [], []
    random.seed(11)
    for n in range(16):
        m = glow(f'Spark{n}', GOLD, 0)
        p = Vector((random.uniform(-0.9, 0.9), random.uniform(-0.9, 0.9), 0.36))
        sparks.append((sphere(f'Spark{n}', 0.07, p, m, 12), p, random.random(), m))
    ring_m = glow('Block', (0.35, 0.6, 1.0, 1), 0)
    rings = [(torus(f'Block{n}', 0.16, 0.012, (0, 0, 0.35), ring_m.copy()), n) for n in range(4)]
    random.seed(5)
    ring_pos = [Vector((random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8), 0.352)) for _ in range(4)]
    k.camera(sc, (2.8, -4.8, 1.3), (0, 0, 0.12), lens=42)

    def frame(t, f):
        for o, p, ph, m in sparks:
            u = (t * 2 + ph) % 1
            key(o, 'location', (p.x, p.y, 0.36 - 0.16 * u), f)
            key_in(em_strength(m), 200 * math.sin(math.pi * u) * (1 - u), f)
        for (r, n) in rings:
            u = (t * 2 + n / 4) % 1
            r.location = ring_pos[n]; r.keyframe_insert('location', frame=f)
            key(r, 'scale', [0.3 + 2.4 * u] * 2 + [1], f)
            key_in(em_strength(r.data.materials[0]), 25 * (1 - u) ** 2, f)
    bake(frame)


def interfaces():
    card_world()
    top = die('GaN layer', gan, (0, 0, 0.7), 2.2, 0.1)
    sap = k.box('Sapphire', (2.2, 2.2, 0.4), (0, 0, 0.1), sapph, bevel=0.02)
    bot = die('SiGe layer', sige, (0, 0, -0.5), 2.2, 0.1)
    via_m = k.mat('Via', (1.0, 0.75, 0.35, 1), metal=1.0, rough=0.2, emit=(1.0, 0.7, 0.3, 1), emit_strength=0.6)
    pm = glow('Pulse', GOLD, 40)
    pts = [(-0.6, -0.6), (0, -0.6), (0.6, -0.6), (-0.6, 0), (0.6, 0), (-0.6, 0.6), (0, 0.6), (0.6, 0.6), (0, 0)]
    pulses = []
    for n, (x, y) in enumerate(pts):
        rod(f'Via{n}', (x, y, -0.45), (x, y, 0.65), 0.03, via_m, 12)
        pulses.append((sphere(f'Pulse{n}', 0.06, (x, y, 0), pm, 12), x, y, n))
    k.camera(sc, (2.8, -4.4, 1.9), (0, 0, 0.1), lens=40)

    def frame(t, f):
        for o, x, y, n in pulses:
            u = (t * 2 + n / 9) % 1
            up = n % 2 == 0
            z = -0.45 + 1.1 * (u if up else 1 - u)
            key(o, 'location', (x, y, z), f)
    bake(frame)


def heat():
    card_world()
    die('GaN layer', gan, (0, 0, 0.62), 2.0, 0.1)
    k.box('Sapphire', (2.0, 2.0, 0.34), (0, 0, 0.4), sapph, bevel=0.02)
    die('SiGe layer', sige, (0, 0, 0.18), 2.0, 0.1)
    cu = k.mat('Copper', (0.95, 0.55, 0.32, 1), metal=1.0, rough=0.3)
    k.box('Spreader', (2.3, 2.3, 0.12), (0, 0, 0.06), cu, bevel=0.01)
    for i in range(11):
        k.box('Fin', (0.06, 2.3, 0.7), (-1.1 + i * 0.22, 0, -0.35), cu, bevel=0.005)
    hot_m = k.mat('Hot spot', (1, 0.4, 0.1, 1), emit=(1.0, 0.35, 0.05, 1), emit_strength=0)
    hots = [k.box(f'Hot{n}', (0.32, 0.32, 0.01), (x, y, 0.675), hot_m) for n, (x, y) in enumerate([(-0.5, -0.4), (0.45, -0.3), (0.0, 0.45)])]
    waves = []
    for n in range(5):
        m = glow(f'Flow{n}', (1.0, 0.5, 0.15, 1), 0)
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
        p = bpy.context.object; p.scale = (1.96, 1.96, 1); p.data.materials.append(m)
        waves.append((p, m, n))
    random.seed(9)
    rise = []
    for n in range(18):
        m = glow(f'Rise{n}', (1.0, 0.45, 0.12, 1), 0)
        p = Vector((random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8), 0.7))
        rise.append((sphere(f'Rise{n}', 0.03, p, m, 10), p, random.random(), m))
    k.camera(sc, (2.9, -4.6, 2.1), (0, 0, 0.2), lens=40)

    def frame(t, f):
        key_in(k.bsdf(hot_m).inputs['Emission Strength'], 6 + 4 * math.sin(TAU * 2 * t), f)
        for p, m, n in waves:      # heat sheets travelling down through the stack into the fins
            u = (t * 2 + n / 5) % 1
            key(p, 'location', (0, 0, 0.66 - 1.3 * u), f)
            key_in(em_strength(m), 0.9 * math.sin(math.pi * u), f)
        for o, p, ph, m in rise:
            u = (t * 2 + ph) % 1
            key(o, 'location', (p.x + 0.1 * math.sin(TAU * (u + ph)), p.y, 0.7 + 1.0 * u), f)
            key_in(em_strength(m), 14 * math.sin(math.pi * u) * (1 - u), f)
    bake(frame)


def lattice():
    card_world()
    al = k.mat('Al', (0.3, 0.5, 1.0, 1), metal=0.2, rough=0.25, emit=(0.2, 0.4, 1.0, 1), emit_strength=0.6)
    ox = k.mat('O', (0.75, 0.82, 0.95, 1), rough=0.3)
    si = k.mat('Si', (0.55, 0.6, 0.68, 1), metal=0.7, rough=0.2)
    ge = k.mat('Ge', (1.0, 0.68, 0.25, 1), metal=0.8, rough=0.25)
    bond = k.mat('Bond', (0.4, 0.45, 0.55, 1), metal=0.6, rough=0.4)
    root = bpy.data.objects.new('Lattice', None); sc.collection.objects.link(root)
    objs = []
    a = 0.42
    # sapphire: hexagonal layers
    for layer in range(3):
        z = -0.9 + layer * 0.26
        for i in range(-6, 7):
            for j in range(-6, 7):
                x = (i + 0.5 * j + (0.33 if layer % 2 else 0)) * a; y = j * a * 0.866
                if x * x + y * y > 2.3 ** 2:
                    continue
                objs.append(sphere('Al', 0.07, (x, y, z), al, 16))
                objs.append(sphere('O', 0.05, (x + a / 2, y + a * 0.29, z + 0.1), ox, 12))
    # silicon-germanium: cubic layers grown on top
    c = 0.4
    for layer in range(4):
        z = -0.1 + layer * c * 0.6
        for i in range(-6, 7):
            for j in range(-6, 7):
                x, y = i * c + (c / 2 if layer % 2 else 0), j * c + (c / 2 if layer % 2 else 0)
                if x * x + y * y > 2.3 ** 2:
                    continue
                m = ge if (i * 3 + j * 5 + layer) % 7 == 0 else si
                objs.append(sphere('SiGe', 0.08, (x, y, z), m, 16))
                if layer:
                    objs.append(rod('Bond', (x, y, z), (x - c / 2, y - c / 2, z - c * 0.6), 0.015, bond, 6))
    for o in objs:
        o.parent = root
    k.camera(sc, (0, -7.6, 3.0), (0, 0, -0.3), lens=42)

    def frame(t, f):
        key(root, 'rotation_euler', (0, 0, math.radians(30) * math.sin(TAU * t)), f)
    bake(frame)


SCENES = {'radar': radar, 'telecom': telecom, 'space': space, 'rugged': rugged,
          'closer': closer, 'isolation': isolation, 'interfaces': interfaces, 'heat': heat, 'lattice': lattice}
SIZES = {'lattice': (1152, 480)}
SCENES[NAME]()
w, h = SIZES.get(NAME, (W, H) if NAME in ('radar', 'telecom', 'space', 'rugged') else (800, 400))
k.render_settings(sc, w, h, samples=int(os.environ.get('SAMPLES', 24)))
sc.cycles.max_bounces = 4
os.makedirs(f'{OUT}/{NAME}', exist_ok=True)
if os.environ.get('FRAMES'):
    sc.render.resolution_percentage = 50
    for fr in os.environ['FRAMES'].split(','):
        sc.frame_set(int(fr)); sc.render.filepath = f'{OUT}/{NAME}/still_{fr}.jpg'
        bpy.ops.render.render(write_still=True)
else:
    k.render_range(sc, 1, N, f'{OUT}/{NAME}/f')
