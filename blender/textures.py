"""Draws the wafer face textures used by build_chip.py (PIL, deterministic)."""
import math, random, sys
from PIL import Image, ImageDraw, ImageFilter

N = 2048
OUT = sys.argv[1] if len(sys.argv) > 1 else '.'

def circle_mask(r_frac=1.0):
    m = Image.new('L', (N, N), 0)
    d = ImageDraw.Draw(m)
    r = N / 2 * r_frac
    d.ellipse((N/2 - r, N/2 - r, N/2 + r, N/2 + r), fill=255)
    return m

def die_field(seed, base, die, line, pad, glow, glow_line, pitch=150, margin=0.965):
    rnd = random.Random(seed)
    col = Image.new('RGB', (N, N), base)
    emi = Image.new('RGB', (N, N), (0, 0, 0))
    dc, de = ImageDraw.Draw(col), ImageDraw.Draw(emi)
    c = N / 2
    lim = c * margin
    gap = 10
    start = c - pitch * math.ceil(lim / pitch)
    y = start
    while y < N:
        x = start
        while x < N:
            corners = [(x, y), (x + pitch, y), (x, y + pitch), (x + pitch, y + pitch)]
            if all(math.hypot(px - c, py - c) < lim for px, py in corners):
                x0, y0, x1, y1 = x + gap, y + gap, x + pitch - gap, y + pitch - gap
                shade = rnd.uniform(-8, 8)
                dc.rectangle((x0, y0, x1, y1), fill=tuple(int(v + shade) for v in die))
                dc.rectangle((x0, y0, x1, y1), outline=line, width=3)
                de.rectangle((x0, y0, x1, y1), outline=glow_line, width=2)
                # internal blocks
                for _ in range(rnd.randint(2, 5)):
                    bw, bh = rnd.randint(18, 60), rnd.randint(14, 50)
                    bx, by = rnd.randint(int(x0) + 8, int(x1) - bw - 8), rnd.randint(int(y0) + 8, int(y1) - bh - 8)
                    dc.rectangle((bx, by, bx + bw, by + bh), fill=tuple(int(v * 0.7) for v in die), outline=line, width=1)
                    if rnd.random() < 0.45:
                        de.rectangle((bx, by, bx + bw, by + bh), outline=glow, width=1)
                # traces
                for _ in range(rnd.randint(3, 7)):
                    tx = rnd.randint(int(x0) + 6, int(x1) - 6)
                    ty = rnd.randint(int(y0) + 6, int(y1) - 6)
                    if rnd.random() < 0.5:
                        dc.line((x0 + 4, ty, tx, ty, tx, y1 - 4), fill=line, width=2)
                    else:
                        dc.line((tx, y0 + 4, tx, ty, x1 - 4, ty), fill=line, width=2)
                # bond pads around the edge
                for k in range(6):
                    t = x0 + 10 + k * (x1 - x0 - 20) / 5
                    dc.rectangle((t - 3, y0 + 4, t + 3, y0 + 10), fill=pad)
                    dc.rectangle((t - 3, y1 - 10, t + 3, y1 - 4), fill=pad)
                if rnd.random() < 0.35:
                    de.rectangle((x0 + 4, y0 + 4, x1 - 4, y1 - 4), outline=glow, width=2)
            x += pitch
        y += pitch
    return col, emi

def rim(img, colour, width):
    d = ImageDraw.Draw(img)
    d.ellipse((width / 2, width / 2, N - width / 2, N - width / 2), outline=colour, width=int(width))

# III-nitride RF face: dark dies, gold circuitry
col, emi = die_field(7, (24, 21, 16), (30, 28, 25), (176, 128, 52), (232, 160, 48), (232, 160, 48), (120, 80, 24))
rim(col, (200, 150, 70), 22); rim(emi, (232, 160, 48), 10)
glare = Image.new('L', (N, N), 0)
ImageDraw.Draw(glare).ellipse((N * .55, N * .1, N * .95, N * .4), fill=90)
glare = glare.filter(ImageFilter.GaussianBlur(160))
col = Image.composite(Image.new('RGB', (N, N), (255, 214, 140)), col, glare)
col.save(f'{OUT}/rf_color.jpg', quality=88); emi.resize((1024, 1024), Image.LANCZOS).save(f'{OUT}/rf_emit.jpg', quality=85)

# Sapphire face: luminous blue with a fine lattice
sc = Image.new('RGB', (N, N), (40, 90, 190))
se = Image.new('RGB', (N, N), (0, 0, 0))
radial = Image.radial_gradient('L').resize((N, N))
sc = Image.composite(Image.new('RGB', (N, N), (28, 60, 140)), Image.new('RGB', (N, N), (110, 160, 240)), radial)
d, de = ImageDraw.Draw(sc), ImageDraw.Draw(se)
for i in range(0, N, 64):
    d.line((i, 0, i, N), fill=(150, 190, 255), width=2); de.line((i, 0, i, N), fill=(70, 120, 220), width=2)
    d.line((0, i, N, i), fill=(150, 190, 255), width=2); de.line((0, i, N, i), fill=(70, 120, 220), width=2)
for i in range(-N, N, 128):
    de.line((i, 0, i + N, N), fill=(40, 80, 170), width=1)
    de.line((i + N, 0, i, N), fill=(40, 80, 170), width=1)
for x in range(0, N, 64):
    for y in range(0, N, 64):
        de.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(190, 220, 255))
rim(sc, (200, 225, 255), 18); rim(se, (160, 200, 255), 12)
sc.resize((1024, 1024), Image.LANCZOS).save(f'{OUT}/sapph_color.jpg', quality=88); se.resize((1024, 1024), Image.LANCZOS).save(f'{OUT}/sapph_emit.jpg', quality=85)

# SiGe face: steel-blue dies with blue circuitry
col, emi = die_field(11, (14, 22, 36), (26, 40, 62), (110, 150, 200), (200, 214, 230), (90, 150, 255), (40, 80, 160), pitch=120)
rim(col, (150, 180, 220), 22); rim(emi, (90, 150, 255), 10)
col.save(f'{OUT}/sige_color.jpg', quality=88); emi.resize((1024, 1024), Image.LANCZOS).save(f'{OUT}/sige_emit.jpg', quality=85)
print('textures ok')

# ---- Textures for the rendered scenes (problem diagram, cards, applications) ----
def die_tile(seed, size, base, block, line, pad, pitch):
    rnd = random.Random(seed)
    im = Image.new('RGB', (size, size), base)
    d = ImageDraw.Draw(im)
    for y in range(0, size, pitch):
        for x in range(0, size, pitch):
            d.rectangle((x + 3, y + 3, x + pitch - 3, y + pitch - 3), outline=line, width=2)
            for _ in range(rnd.randint(1, 3)):
                bw, bh = rnd.randint(8, pitch // 2), rnd.randint(6, pitch // 2)
                bx, by = x + rnd.randint(6, pitch - bw - 6), y + rnd.randint(6, pitch - bh - 6)
                d.rectangle((bx, by, bx + bw, by + bh), fill=block)
    for k in range(0, size, 24):  # bond pads around the edge
        for (px, py) in ((k + 6, 4), (k + 6, size - 14), (4, k + 6), (size - 14, k + 6)):
            d.rectangle((px, py, px + 10, py + 10), fill=pad)
    return im

die_tile(3, 1024, (214, 150, 52), (150, 96, 24), (110, 70, 18), (255, 226, 160), 256).save(f'{OUT}/die_gan.jpg', quality=90)
die_tile(5, 1024, (150, 170, 192), (86, 104, 128), (60, 78, 100), (235, 240, 246), 256).save(f'{OUT}/die_sige.jpg', quality=90)

# Circuit board: dark solder mask with copper traces and vias
rnd = random.Random(21)
pcb = Image.new('RGB', (2048, 1024), (12, 24, 38))
d = ImageDraw.Draw(pcb)
for _ in range(260):
    x, y = rnd.randint(0, 2048), rnd.randint(0, 1024)
    L = rnd.randint(40, 260)
    if rnd.random() < .5:
        d.line((x, y, x + L, y, x + L + 30, y + 30), fill=(34, 56, 80), width=4)
    else:
        d.line((x, y, x, y + L, x + 30, y + L + 30), fill=(34, 56, 80), width=4)
    d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(150, 120, 60))
pcb.save(f'{OUT}/pcb.jpg', quality=88)
print('scene textures ok')
