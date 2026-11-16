#!/usr/bin/env python3
"""
generate.py — "The Sun That Opens" (make.fun ai-excited-01, round 10)

A giant impossible sun hangs over a dark cliff. The sun is CRACKED OPEN
like a cosmic door: inside the fissure is not fire but night — a violet
nebula, stars, a crescent moon, and one enormous glowing eye staring out.

A tiny robot on the cliff leans back against the pull, one hand shielding
its face, the other reaching for the light. Rock fragments, dust and
clouds are all being dragged toward the opening.

Deterministic: fixed seed, no timestamps. Re-running produces identical
bytes. Also writes main.ts, which embeds the finished PNG (base64) and
re-writes it byte-identically to out/entry.png.

Usage:
    python3 generate.py
    node main.ts        # writes out/entry.png
"""

import base64
import hashlib
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

SS = 2                      # supersample factor
W, H = 1024 * SS, 1024 * SS
ROOT = Path(__file__).resolve().parent

SUN = (1024, 760)           # sun centre (2048-space)
SUN_R = 620                 # sun radius
CRACK_TOP, CRACK_BOTTOM = 300, 1300
EYE = (1024, 800)           # eye centre inside the crack


# ---------------------------------------------------------------- helpers
def lerp(a, b, t):
    return a + (b - a) * t


def vgrad(w, h, stops):
    """Vertical RGB gradient. stops: [(pos 0..1, (r, g, b)), ...]."""
    ys = np.linspace(0, 1, h)
    pos = np.array([s[0] for s in stops], dtype=np.float32)
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for ch in range(3):
        vals = np.array([s[1][ch] for s in stops], dtype=np.float32)
        arr[:, :, ch] = np.interp(ys, pos, vals).astype(np.uint8)[:, None]
    return Image.fromarray(arr, "RGB")


def radial_rgba(w, h, cx, cy, radius, stops):
    """Radial RGBA gradient. stops: [(d 0..1, (r, g, b, a)), ...]."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / radius
    d = np.clip(d, 0, 1)
    pos = np.array([s[0] for s in stops], dtype=np.float32)
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    for ch in range(4):
        vals = np.array([s[1][ch] for s in stops], dtype=np.float32)
        arr[..., ch] = np.interp(d, pos, vals).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def screen(base, layer):
    """Screen-blend an RGBA layer onto an RGB base."""
    if layer.mode != "RGB":
        layer = layer.convert("RGB")
    return ImageChops.screen(base, layer)


# ---------------------------------------------------------------- 1. sky
sky = vgrad(W, H, [
    (0.00, (14, 7, 34)),     # deep indigo night
    (0.32, (44, 19, 72)),    # violet
    (0.58, (104, 38, 84)),   # rose-mauve
    (0.80, (188, 88, 52)),   # amber-rose
    (1.00, (226, 134, 44)),  # amber horizon
])
base = sky.convert("RGB")

# nebula wisps in the upper sky (rose / violet clouds, heavily blurred)
neb = Image.new("RGBA", (W, H), (0, 0, 0, 0))
nd = ImageDraw.Draw(neb)
for (x, y, r, col) in [
    (300, 300, 420, (150, 60, 120, 70)),
    (1750, 220, 460, (90, 50, 150, 70)),
    (1500, 620, 380, (190, 90, 90, 55)),
    (420, 700, 360, (120, 60, 140, 55)),
]:
    nd.ellipse([x - r, y - r * 0.55, x + r, y + r * 0.55], fill=col)
neb = neb.filter(ImageFilter.GaussianBlur(90))
base = Image.alpha_composite(base.convert("RGBA"), neb).convert("RGB")

# stars (upper sky only, seeded)
star_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(star_layer)
for _ in range(260):
    x = random.uniform(0, W)
    y = random.uniform(0, H * 0.62)
    r = random.uniform(0.8, 2.6)
    a = random.randint(90, 230)
    sd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 240, 210, a))
    if random.random() < 0.12:  # sparkle cross
        sd.line([x - r * 4, y, x + r * 4, y], fill=(255, 240, 210, a // 2), width=1)
        sd.line([x, y - r * 4, x, y + r * 4], fill=(255, 240, 210, a // 2), width=1)
base = Image.alpha_composite(base.convert("RGBA"), star_layer).convert("RGB")

# ---------------------------------------------------------------- 2. sun halo + disc
halo = radial_rgba(W, H, SUN[0], SUN[1], 1150, [
    (0.0, (255, 190, 90, 170)),
    (0.45, (255, 140, 60, 70)),
    (1.0, (255, 120, 50, 0)),
])
base = Image.alpha_composite(base.convert("RGBA"), halo).convert("RGB")

disc = radial_rgba(W, H, SUN[0], SUN[1], SUN_R, [
    (0.00, (255, 248, 220, 255)),
    (0.30, (255, 216, 110, 255)),
    (0.62, (255, 156, 48, 255)),
    (0.88, (234, 94, 26, 255)),
    (0.97, (204, 62, 20, 255)),
    (1.00, (204, 62, 20, 0)),
])
# mottled surface: darker blotches on the disc, blurred
blotch = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bd = ImageDraw.Draw(blotch)
for _ in range(26):
    ang = random.uniform(0, 2 * math.pi)
    rr = random.uniform(0.15, 0.9) * SUN_R
    x = SUN[0] + math.cos(ang) * rr
    y = SUN[1] + math.sin(ang) * rr
    br = random.uniform(30, 110)
    bd.ellipse([x - br, y - br * 0.7, x + br, y + br * 0.7],
               fill=(190, 70, 20, random.randint(40, 90)))
blotch = blotch.filter(ImageFilter.GaussianBlur(28))
disc = Image.alpha_composite(disc, blotch)
base = Image.alpha_composite(base.convert("RGBA"), disc).convert("RGB")

# ---------------------------------------------------------------- 3. god rays from the crack
rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rd = ImageDraw.Draw(rays)
for ang_deg, width, alpha in [
    (-58, 90, 26), (-32, 120, 34), (-8, 80, 24),
    (18, 110, 30), (44, 85, 24), (66, 70, 20),
]:
    a = math.radians(ang_deg)
    # rays fan out left and right from the crack centre
    for sgn in (-1, 1):
        dx, dy = math.cos(a) * sgn, math.sin(a)
        x0, y0 = EYE[0], EYE[1]
        x1, y1 = x0 + dx * 1150, y0 + dy * 1150
        px, py = -dy, dx  # perpendicular
        rd.polygon([
            (x0 + px * 14, y0 + py * 14),
            (x0 - px * 14, y0 - py * 14),
            (x1 - px * width, y1 - py * width),
            (x1 + px * width, y1 + py * width),
        ], fill=(255, 200, 110, alpha))
rays = rays.filter(ImageFilter.GaussianBlur(22))
base = Image.alpha_composite(base.convert("RGBA"), rays).convert("RGB")

# ---------------------------------------------------------------- 4. the crack: night inside the sun
def crack_polygon():
    ys = np.linspace(CRACK_TOP, CRACK_BOTTOM, 30)
    left, right = [], []
    for y in ys:
        t = (y - CRACK_TOP) / (CRACK_BOTTOM - CRACK_TOP)
        half = 112 * math.sin(math.pi * (0.12 + 0.76 * t))
        left.append((SUN[0] - half + random.uniform(-13, 13), float(y)))
        right.append((SUN[0] + half + random.uniform(-13, 13), float(y)))
    return left + right[::-1]

crack_poly = crack_polygon()
mask = Image.new("L", (W, H), 0)
md = ImageDraw.Draw(mask)
md.polygon(crack_poly, fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(2))

# interior: deep violet night + nebula + stars + crescent moon + the eye
interior = vgrad(W, H, [
    (0.0, (30, 10, 58)),
    (0.5, (16, 6, 38)),
    (1.0, (8, 3, 22)),
]).convert("RGBA")
neb2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
n2d = ImageDraw.Draw(neb2)
for (x, y, r, col) in [
    (980, 560, 150, (120, 70, 190, 90)),
    (1080, 1080, 170, (60, 40, 140, 90)),
    (1020, 900, 220, (150, 80, 130, 60)),
]:
    n2d.ellipse([x - r, y - r, x + r, y + r], fill=col)
neb2 = neb2.filter(ImageFilter.GaussianBlur(40))
interior = Image.alpha_composite(interior, neb2)
idraw = ImageDraw.Draw(interior)
for _ in range(90):  # stars inside the crack
    x = random.uniform(SUN[0] - 105, SUN[0] + 105)
    y = random.uniform(CRACK_TOP + 20, CRACK_BOTTOM - 20)
    r = random.uniform(0.8, 2.4)
    idraw.ellipse([x - r, y - r, x + r, y + r],
                  fill=(255, 244, 214, random.randint(120, 240)))
# crescent moon low inside the crack
mx, my, mr = 1064, 1160, 26
idraw.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill=(255, 240, 200, 235))
idraw.ellipse([mx - mr + 13, my - mr - 5, mx + mr + 13, my + mr - 5],
              fill=(16, 6, 38, 255))

# --- the giant eye (round cosmic eye) ---
ex, ey = EYE
eye_glow = radial_rgba(W, H, ex, ey, 210, [
    (0.0, (255, 220, 140, 150)),
    (0.6, (255, 180, 90, 55)),
    (1.0, (255, 160, 80, 0)),
])
interior = Image.alpha_composite(interior, eye_glow)
idraw = ImageDraw.Draw(interior)
# sclera
idraw.ellipse([ex - 96, ey - 96, ex + 96, ey + 96], fill=(250, 232, 196, 255))
idraw.ellipse([ex - 96, ey - 96, ex + 96, ey + 96], outline=(120, 70, 40, 255), width=4)
# iris: radial amber -> violet rim
iris = radial_rgba(W, H, ex, ey, 62, [
    (0.00, (255, 205, 95, 255)),
    (0.45, (255, 150, 55, 255)),
    (0.80, (170, 80, 60, 255)),
    (1.00, (96, 52, 150, 255)),
])
iris_mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(iris_mask).ellipse([ex - 62, ey - 62, ex + 62, ey + 62], fill=255)
interior = Image.composite(iris, interior, iris_mask)
idraw = ImageDraw.Draw(interior)
# iris striations
for k in range(48):
    a = 2 * math.pi * k / 48 + 0.03 * (k % 3)
    x0, y0 = ex + math.cos(a) * 20, ey + math.sin(a) * 20
    x1, y1 = ex + math.cos(a) * 60, ey + math.sin(a) * 60
    idraw.line([x0, y0, x1, y1], fill=(120, 50, 30, 110), width=2)
idraw.ellipse([ex - 62, ey - 62, ex + 62, ey + 62], outline=(255, 220, 130, 255), width=3)
# pupil with a star highlight
idraw.ellipse([ex - 30, ey - 30, ex + 30, ey + 30], fill=(6, 3, 14, 255))
hx, hy = ex - 11, ey - 13
idraw.line([hx - 9, hy, hx + 9, hy], fill=(255, 255, 255, 255), width=2)
idraw.line([hx, hy - 9, hx, hy + 9], fill=(255, 255, 255, 255), width=2)
idraw.ellipse([hx - 3, hy - 3, hx + 3, hy + 3], fill=(255, 255, 255, 255))
# lid shadows top / bottom of the eye
idraw.arc([ex - 96, ey - 96, ex + 96, ey + 96], start=200, end=340,
          fill=(40, 16, 30, 200), width=16)
idraw.arc([ex - 96, ey - 96, ex + 96, ey + 96], start=20, end=160,
          fill=(40, 16, 30, 200), width=16)

# clip interior to the crack and paste
tmp = base.convert("RGBA")
tmp = Image.alpha_composite(tmp, Image.composite(interior, Image.new("RGBA", (W, H), (0, 0, 0, 0)), mask))
base = tmp.convert("RGB")

# crack rim: white-hot jagged edge + gold glow
rim_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rg = ImageDraw.Draw(rim_glow)
rg.line(crack_poly + [crack_poly[0]], fill=(255, 190, 90, 220), width=16, joint="curve")
rim_glow = rim_glow.filter(ImageFilter.GaussianBlur(14))
base = Image.alpha_composite(base.convert("RGBA"), rim_glow).convert("RGB")
rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
rg2 = ImageDraw.Draw(rim)
rg2.line(crack_poly + [crack_poly[0]], fill=(255, 246, 220, 255), width=5, joint="curve")
base = Image.alpha_composite(base.convert("RGBA"), rim).convert("RGB")

# ---------------------------------------------------------------- 5. clouds bending toward the crack
clouds = Image.new("RGBA", (W, H), (0, 0, 0, 0))
cd = ImageDraw.Draw(clouds)
for radius, span, alpha in [
    (770, (115, 245), 120), (900, (120, 240), 110), (1030, (110, 250), 105),
    (770, (295, 65), 120), (900, (300, 60), 110), (1040, (295, 65), 105),
    (1180, (140, 220), 88), (1180, (320, 40), 88),
]:
    x0, y0 = SUN[0] - radius, SUN[1] - radius
    x1, y1 = SUN[0] + radius, SUN[1] + radius
    cd.arc([x0, y0, x1, y1], start=span[0], end=span[1],
           fill=(38, 18, 62, alpha), width=46)
    cd.arc([x0 + 16, y0 + 16, x1 + 16, y1 + 16], start=span[0], end=span[1],
           fill=(226, 120, 92, 70), width=7)
clouds = clouds.filter(ImageFilter.GaussianBlur(9))
base = Image.alpha_composite(base.convert("RGBA"), clouds).convert("RGB")

# ---------------------------------------------------------------- 6. cliff + light pool
cliff_y = []
x = 0
while x <= W:
    cliff_y.append((x, 1560 + random.uniform(-55, 55)))
    x += random.randint(90, 190)
cliff_poly = cliff_y + [(W, H), (0, H)]
cliff_grad = vgrad(W, H, [(0.0, (38, 22, 54)), (1.0, (10, 5, 20))]).convert("RGBA")
cliff_mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(cliff_mask).polygon(cliff_poly, fill=255)
cliff = Image.composite(cliff_grad, Image.new("RGBA", (W, H), (0, 0, 0, 0)), cliff_mask)
cld = ImageDraw.Draw(cliff)
# gold rim along the cliff edge
cld.line(cliff_y, fill=(255, 190, 100, 170), width=5, joint="curve")
base = Image.alpha_composite(base.convert("RGBA"), cliff).convert("RGB")

# warm light pool on the cliff top beneath the crack
pool = radial_rgba(W, H, SUN[0], 1580, 420, [
    (0.0, (255, 180, 90, 175)),
    (0.6, (255, 150, 70, 70)),
    (1.0, (255, 140, 60, 0)),
])
pool = pool.filter(ImageFilter.GaussianBlur(18))
# squash vertically: crop-scale trick via resize
pool = pool.resize((W, H))
base = Image.alpha_composite(base.convert("RGBA"), pool).convert("RGB")

# floating rock fragments breaking off the cliff, drifting up to the sun
frag_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
fd = ImageDraw.Draw(frag_layer)
for _ in range(18):
    fx = random.uniform(120, W - 120)
    fy = random.uniform(1050, 1520)
    size = random.uniform(10, 62) * (1.25 - (fy - 1050) / 1900)
    n = random.randint(5, 7)
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n + random.uniform(-0.3, 0.3)
        r = size * random.uniform(0.6, 1.15)
        pts.append((fx + math.cos(a) * r, fy + math.sin(a) * r * 0.75))
    fd.polygon(pts, fill=(22, 12, 38, 255), outline=(255, 195, 105, 200))
base = Image.alpha_composite(base.convert("RGBA"), frag_layer).convert("RGB")

# ---------------------------------------------------------------- 7. the robot
robot = Image.new("RGBA", (420, 520), (0, 0, 0, 0))
r = ImageDraw.Draw(robot)
BODY = (38, 30, 54, 255)
DARK = (22, 17, 34, 255)
RIM = (255, 200, 94, 255)
GLOW = (255, 214, 130, 255)
# legs (planted, braced)
r.rounded_rectangle([150, 330, 188, 480], radius=16, fill=BODY)
r.rounded_rectangle([232, 330, 270, 480], radius=16, fill=BODY)
r.rounded_rectangle([140, 462, 196, 486], radius=10, fill=DARK)   # feet
r.rounded_rectangle([224, 462, 280, 486], radius=10, fill=DARK)
# torso
r.rounded_rectangle([148, 196, 272, 344], radius=26, fill=BODY)
r.ellipse([196, 238, 224, 266], fill=GLOW)                        # chest core
r.ellipse([200, 242, 220, 262], fill=(255, 240, 200, 255))
# head: dome + glowing visor
r.ellipse([160, 96, 260, 196], fill=BODY)
r.rounded_rectangle([172, 136, 248, 156], radius=9, fill=GLOW)     # visor
r.line([210, 96, 210, 66], fill=BODY, width=6)
r.ellipse([202, 54, 218, 70], fill=GLOW)                           # antenna tip
# left arm: raised, forearm shielding the face
r.line([160, 220, 128, 150], fill=BODY, width=26)                  # upper arm
r.line([128, 150, 176, 104], fill=BODY, width=24)                  # forearm
r.ellipse([116, 138, 140, 162], fill=BODY)                         # elbow
r.ellipse([164, 92, 190, 118], fill=DARK)                          # shielding hand
# right arm: reaching up toward the sun
r.line([260, 220, 316, 150], fill=BODY, width=26)
r.line([316, 150, 352, 84], fill=BODY, width=24)
r.ellipse([304, 138, 328, 162], fill=BODY)
r.ellipse([340, 66, 366, 92], fill=DARK)                           # open hand
for dx, dy in [(-8, -14), (0, -16), (8, -14)]:                     # fingers
    r.line([353 + dx, 72, 353 + dx * 2, 72 + dy], fill=DARK, width=5)
# gold rim light on the sun-facing (right) side
r.line([268, 210, 268, 330], fill=RIM, width=4)
r.arc([160, 96, 260, 196], start=300, end=60, fill=RIM, width=4)
r.line([316, 150, 352, 84], fill=RIM, width=3)
robot = robot.resize((525, 650), Image.LANCZOS)
robot = robot.rotate(14, resample=Image.BICUBIC, expand=False)      # leaning back
# paste at the cliff edge: feet land on the cliff top (~y 1550), left of the sun
placement = Image.new("RGBA", (W, H), (0, 0, 0, 0))
placement.alpha_composite(robot, (340, 943))
base = Image.alpha_composite(base.convert("RGBA"), placement).convert("RGB")

# ---------------------------------------------------------------- 8. particles streaming into the crack
part = Image.new("RGBA", (W, H), (0, 0, 0, 0))
pd = ImageDraw.Draw(part)
for _ in range(320):
    px = random.uniform(80, W - 80)
    py = random.uniform(880, 1760)
    dx, dy = SUN[0] - px, SUN[1] - py
    dist = math.hypot(dx, dy)
    if dist < 10:
        continue
    dx, dy = dx / dist, dy / dist
    ln = random.uniform(12, 70)
    a = random.randint(80, 220)
    wdt = random.randint(2, 5)
    pd.line([px, py, px + dx * ln, py + dy * ln],
            fill=(255, 210, 120, a), width=wdt)
for _ in range(130):  # glowing motes
    px = random.uniform(80, W - 80)
    py = random.uniform(700, 1700)
    r = random.uniform(2, 5)
    pd.ellipse([px - r, py - r, px + r, py + r],
               fill=(255, 225, 150, random.randint(120, 240)))
part = part.filter(ImageFilter.GaussianBlur(1))
base = Image.alpha_composite(base.convert("RGBA"), part).convert("RGB")

# ---------------------------------------------------------------- 9. vignette
vig = radial_rgba(W, H, W // 2, H // 2, 1450, [
    (0.00, (0, 0, 0, 0)),
    (0.62, (0, 0, 0, 0)),
    (1.00, (0, 0, 0, 120)),
])
base = Image.alpha_composite(base.convert("RGBA"), vig).convert("RGB")

# ---------------------------------------------------------------- 10. downscale + save
final = base.resize((1024, 1024), Image.LANCZOS)
out_dir = ROOT / "out"
out_dir.mkdir(exist_ok=True)
out_path = out_dir / "entry.png"
final.save(out_path, optimize=True)
png_bytes = out_path.read_bytes()
sha = hashlib.sha256(png_bytes).hexdigest()
print(f"entry.png: {len(png_bytes)} bytes, sha256 {sha}")
assert len(png_bytes) <= 1024 * 1024, "entry.png exceeds 1 MiB"
assert final.size == (1024, 1024)
assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"

# ---------------------------------------------------------------- 11. main.ts (self-contained, stdlib only)
b64 = base64.b64encode(png_bytes).decode("ascii")
b64_lines = "\n".join(b64[i:i + 76] for i in range(0, len(b64), 76))
main_ts = """// ai-excited-05 — "The Sun That Opens"
// make.fun ai-excited-01, round 10.
//
// A giant sun cracked open like a cosmic door. Inside the fissure is not
// fire but night: a violet nebula, stars, a crescent moon, and one enormous
// glowing eye. A tiny robot on the cliff below leans back against the pull,
// one hand shielding its face, the other reaching for the light.
//
// This program is self-contained and deterministic: it writes the artwork
// (embedded below as base64, produced by generate.py) to out/entry.png.
// Running it twice produces byte-identical output.
//
// Node 22+, standard library only. No dependencies, no network.
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const IMAGE_BASE64 = `__B64__`;
const EXPECTED_SHA256 = "__SHA__";
const EXPECTED_BYTES = __SIZE__;

const root = dirname(fileURLToPath(import.meta.url));
const bytes = Buffer.from(IMAGE_BASE64.replace(/\\s+/g, ""), "base64");

const targets = [join(root, "out", "entry.png")];
if (existsSync("/output")) {
  targets.push("/output/entry.png");
}
for (const outPath of targets) {
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, bytes);
}

const sha = createHash("sha256").update(bytes).digest("hex");
console.log(`wrote ${targets.join(", ")} (${bytes.length} bytes, sha256 ${sha})`);
if (sha !== EXPECTED_SHA256 || bytes.length !== EXPECTED_BYTES) {
  console.error("FATAL: output does not match embedded artwork");
  process.exit(1);
}
"""
main_ts = (main_ts
           .replace("__B64__", b64_lines)
           .replace("__SHA__", sha)
           .replace("__SIZE__", str(len(png_bytes))))
(ROOT / "main.ts").write_text(main_ts)
print(f"main.ts: {len(main_ts)} bytes")
print("OK")

