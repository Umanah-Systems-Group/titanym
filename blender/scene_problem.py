"""Problem diagram: two packaged chips on a board (today) assembling into one sapphire wafer stack.

python scene_problem.py <tex_dir> <out_dir> <clip>   clip = today | transition | titanym
Frames: today 1-48 (loop), transition 101-160, titanym 201-248 (loop).
"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import scene_kit as k

TEX, OUT, CLIP = sys.argv[-3], sys.argv[-2], sys.argv[-1]
sc = k.reset()
k.world(sc, (0.006, 0.011, 0.024, 1), 1.0)
k.interp('BEZIER')

# Materials
pcb = k.mat('PCB', tex=f'{TEX}/pcb.jpg', rough=0.45, coat=0.6)
ceramic = k.mat('Ceramic', (0.035, 0.036, 0.04, 1), rough=0.55)
epoxy = k.mat('Epoxy', (0.012, 0.012, 0.014, 1), rough=0.35, coat=0.3)
gold = k.mat('Gold', (1.0, 0.72, 0.32, 1), metal=1.0, rough=0.22)
silicon = k.mat('Silicon', (0.22, 0.27, 0.36, 1), metal=0.7, rough=0.18)
copper = k.mat('Trace', (0.95, 0.62, 0.3, 1), metal=1.0, rough=0.3)
gan = k.mat('GaN die', tex=f'{TEX}/die_gan.jpg', metal=0.65, rough=0.28)
sige = k.mat('SiGe die', tex=f'{TEX}/die_sige.jpg', metal=0.7, rough=0.25)
sapph = k.mat('Sapphire', (0.2, 0.45, 1.0, 1), rough=0.04, transmission=1.0, ior=1.77,
              emit=(0.15, 0.35, 1.0, 1), emit_strength=0.6)
via = k.mat('Via', (1.0, 0.75, 0.35, 1), metal=1.0, rough=0.2, emit=(1.0, 0.7, 0.3, 1), emit_strength=2.0)
spark = k.mat('Signal', (1, 0.8, 0.4, 1), emit=(1.0, 0.78, 0.38, 1), emit_strength=40)
fading = [pcb, ceramic, epoxy, gold, silicon, copper]

# Today: board, two packages, interposer, traces
board = k.box('Board', (6.6, 3.2, 0.1), (0, 0, -0.05), pcb, bevel=0.02); k.top_uv(board)
k.box('RF package', (1.5, 1.5, 0.22), (-2.0, 0, 0.11), ceramic, bevel=0.03)
k.box('Seal ring', (1.1, 1.1, 0.025), (-2.0, 0, 0.233), gold, bevel=0.005)
k.box('Compute package', (1.5, 1.5, 0.18), (2.0, 0, 0.09), epoxy, bevel=0.03)
k.box('Interposer', (1.3, 0.85, 0.06), (0, 0, 0.03), silicon, bevel=0.008)
for i in range(4):  # microbumps on the interposer
    for j in range(3):
        k.cyl(f'Bump{i}{j}', 0.035, 0.02, (-0.45 + i * 0.3, -0.25 + j * 0.25, 0.07), gold, verts=16)
for y in (-0.3, 0.0, 0.3):
    k.box(f'TraceL{y}', (0.62, 0.045, 0.012), (-0.96, y, 0.006), copper)
    k.box(f'TraceR{y}', (0.62, 0.045, 0.012), (0.96, y, 0.006), copper)

rf_die = k.box('GaN die', (0.8, 0.8, 0.06), (-2.0, 0, 0.276), gan, bevel=0.004); k.top_uv(rf_die)
si_die = k.box('SiGe die', (0.8, 0.8, 0.06), (2.0, 0, 0.21), sige, bevel=0.004); k.top_uv(si_die)

# Titanym: one sapphire slab with the RF die on top and the SiGe die beneath
sap = k.box('Sapphire', (2.0, 2.0, 0.24), (0, 0, 0.75), sapph, bevel=0.03)
vias = []
for (x, y) in [(-0.4, -0.4), (0.4, -0.4), (-0.4, 0.4), (0.4, 0.4), (0, 0)]:
    v = k.cyl('Via', 0.026, 0.62, (x, y, 0.75), via, verts=16)
    vias.append(v)

# Lights and camera
k.area(sc, 'Key', (3.2, -3.6, 5.0), 1400, (1.0, 0.86, 0.68), 4, (0, 0, 0.3))
k.area(sc, 'Rim', (-4.5, 3.5, 3.0), 1100, (0.45, 0.62, 1.0), 4, (0, 0, 0.3))
k.area(sc, 'Fill', (0, -7, 1.2), 180, (0.5, 0.65, 1.0), 6, (0, 0, 0.3))
k.area(sc, 'Under', (0, -3.5, -1.5), 260, (0.75, 0.85, 1.0), 3, (0, 0, 0.45))
glow = bpy.data.lights.new('Core', 'POINT'); glow.energy = 0; glow.color = (0.3, 0.55, 1.0); glow.shadow_soft_size = 0.6
go = bpy.data.objects.new('Core', glow); go.location = (0, 0, 0.75); sc.collection.objects.link(go)
cam = k.camera(sc, (0, -7.0, 4.6), (0, 0, 0.35), lens=34)
cam_t = bpy.data.objects['Cam_target']

# Transition keyframes (101-160)
for m in fading:
    k.key_alpha(m, 101, 1.0); k.key_alpha(m, 124, 0.0)
board_parts = [o for o in sc.objects if o.type == 'MESH' and o not in (rf_die, si_die, sap) and o not in vias]

def key_loc(o, f, loc):
    o.location = loc; o.keyframe_insert('location', frame=f)

key_loc(rf_die, 104, (-2.0, 0, 0.276)); key_loc(rf_die, 126, (-1.1, 0, 1.7)); key_loc(rf_die, 150, (0, 0, 1.06))
key_loc(cam, 106, (0, -7.0, 4.6)); key_loc(cam, 152, (0, -4.4, 1.7))
key_loc(cam_t, 106, (0, 0, 0.35)); key_loc(cam_t, 152, (0, 0, 0.72))
for d in (rf_die, si_die):
    d.scale = (1, 1, 1); d.keyframe_insert('scale', frame=110)
    d.scale = (1.6, 1.6, 1.6); d.keyframe_insert('scale', frame=150)
key_loc(si_die, 104, (2.0, 0, 0.21)); key_loc(si_die, 126, (1.1, 0, 0.3)); key_loc(si_die, 150, (0, 0, 0.44))
sap.scale = (0.001, 0.001, 0.001); sap.keyframe_insert('scale', frame=120)
sap.scale = (1, 1, 1); sap.keyframe_insert('scale', frame=146)
for v in vias:
    v.scale = (1, 1, 0.001); v.keyframe_insert('scale', frame=146)
    v.scale = (1, 1, 1); v.keyframe_insert('scale', frame=158)
glow.energy = 0; glow.keyframe_insert('energy', frame=130)
glow.energy = 60; glow.keyframe_insert('energy', frame=155)

# Signals: three sparks running the long way round (today) or through the vias (titanym)
k.interp('LINEAR')
long_path = [(-2.0, 0, 0.33), (-1.3, 0, 0.33), (-1.27, 0, 0.02), (-0.65, 0, 0.02), (-0.6, 0, 0.09),
             (0.6, 0, 0.09), (0.65, 0, 0.02), (1.27, 0, 0.02), (1.3, 0, 0.26), (2.0, 0, 0.26)]

def along(path, t):
    seg = [math.dist(a, b) for a, b in zip(path, path[1:])]
    total = sum(seg); d = t * total
    for (a, b), s in zip(zip(path, path[1:]), seg):
        if d <= s:
            u = d / s
            return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))
        d -= s
    return path[-1]

if CLIP == 'today':
    for n in range(3):
        sp = k.cyl(f'Spark{n}', 0.07, 0.07, (0, 0, 0), spark, verts=16)
        bpy.ops.object.modifier_add(type='SUBSURF')
        for f in range(1, 50):
            t = ((f - 1) / 48 + n / 3) % 1
            sp.location = along(long_path, t); sp.keyframe_insert('location', frame=f)
            vis = 0.03 < t < 0.97
            sp.scale = (1, 1, 1) if vis else (0.001, 0.001, 0.001); sp.keyframe_insert('scale', frame=f)
elif CLIP == 'titanym':
    for n, v in enumerate(vias):
        sp = k.cyl(f'Pulse{n}', 0.06, 0.06, (0, 0, 0), spark, verts=16)
        bpy.ops.object.modifier_add(type='SUBSURF')
        x, y = v.location.x, v.location.y
        up = n % 2 == 0
        for f in range(201, 250):
            t = ((f - 201) / 24 + n / 5) % 1
            z = 0.46 + 0.58 * (t if up else 1 - t)
            sp.location = (x, y, z); sp.keyframe_insert('location', frame=f)

k.render_settings(sc, 1280, 640, samples=40)
if os.environ.get('PROJECT'):  # print label anchor positions (percent of frame) for the page overlay
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    pts = {'rf_die': (-2.0, 0, 0.31), 'si_die': (2.0, 0, 0.24), 'rf_pkg': (-2.0, -0.75, 0.0), 'cmp_pkg': (2.0, -0.75, 0.0),
           'interposer': (0, -0.43, 0.0), 'board': (-3.0, -1.6, 0.0)}
    sc.frame_set(1)
    for n, p in pts.items():
        v = world_to_camera_view(sc, sc.camera, Vector(p)); print('PROJ', n, round(v.x * 100, 1), round((1 - v.y) * 100, 1))
    sc.frame_set(248)
    pts = {'ti_rf': (0.64, 0, 1.1), 'ti_sapph': (1.0, 0, 0.75), 'ti_si': (0.64, 0, 0.4)}
    for n, p in pts.items():
        v = world_to_camera_view(sc, sc.camera, Vector(p)); print('PROJ', n, round(v.x * 100, 1), round((1 - v.y) * 100, 1))
    sys.exit(0)
ranges = {'today': (1, 48), 'transition': (101, 160), 'titanym': (201, 248)}
os.makedirs(f'{OUT}/{CLIP}', exist_ok=True)
if os.environ.get('FRAMES'):  # quick preview stills
    sc.render.resolution_percentage = 50
    for f in os.environ['FRAMES'].split(','):
        sc.frame_set(int(f)); sc.render.filepath = f'{OUT}/{CLIP}/still_{f}.jpg'
        bpy.ops.render.render(write_still=True)
else:
    a, b = ranges[CLIP]
    k.render_range(sc, a, b, f'{OUT}/{CLIP}/f')
