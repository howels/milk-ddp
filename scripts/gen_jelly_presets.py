#!/usr/bin/env python3
"""Generate GPL MilkDrop 2 presets inspired by Machine Code (Jelly) aesthetics.

Reference look (Butterchurn / Cream of the Crop): Stahlregen & Boz + Eo.S +
Geiss + Phat + Rovastar + Zylot - Machine Code (Relief Block Mix) (Jelly).

Mechanisms mirrored as original work (not a copy of that file):
  - continuous vertical scroll of waveform / spectrum ink
  - warp trail with max-blend + posterize colour hold + slow darken
  - composite gelatinous relief from luminance gradients (fake normals)
  - block / bit / cascade overlays for a machine-code feel

MilkDrop 2 only (no get_fft). Prefer 128×128+ LED matrices.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "presets" / "jelly"


def lines(prefix: str, body: str) -> str:
    out = []
    n = 0
    for raw in body.strip().splitlines():
        if not raw.strip():
            continue
        n += 1
        out.append(f"{prefix}_{n}=`{raw}")
    return "\n".join(out) + "\n"


COMMON = """\
float2 rot2(float2 p, float a)
{
  float c = cos(a); float s = sin(a);
  return float2(c*p.x - s*p.y, s*p.x + c*p.y);
}
float hash11(float n)
{
  return frac(sin(n) * 43758.5453);
}
float3 hue(float h, float s)
{
  float3 k = abs(frac(h + float3(0.0, 0.66667, 0.33333))*6.0 - 3.0) - 1.0;
  return (1.0 - s) + s*saturate(k);
}
float lum_sample(float2 u)
{
  float3 w = float3(0.55, 0.30, 0.12);
  float3 a = tex2D(sampler_main, u).rgb;
  float3 b = GetBlur1(u);
  float3 c = GetBlur2(u);
  return dot(a, w) * 0.55 + dot(b, w) * 0.30 + dot(c, w) * 0.15;
}
float3 jelly_relief(float2 u)
{
  float2 px = texsize.zw;
  float gx = lum_sample(u + float2(px.x, 0.0)) - lum_sample(u - float2(px.x, 0.0));
  float gy = lum_sample(u + float2(0.0, px.y)) - lum_sample(u - float2(0.0, px.y));
  float3 n = normalize(float3(gx, gy, 0.12 + 0.04 * q1));
  float3 rel = 0.5 + 0.5 * n;
  float edge = saturate(length(rel.xy - 0.5) * (4.5 + 2.0 * q4));
  rel *= edge;
  return rel;
}
float3 led_tonemap(float3 col)
{
  float lum = max(dot(col, float3(0.30, 0.59, 0.11)), 0.0001);
  float mapped = 1.0 - exp(-lum * 1.05);
  mapped = min(mapped, 0.90);
  float3 outc = (col / lum) * mapped * q13;
  outc += float3(1.0, 1.0, 1.0) * pow(mapped, 3.0) * q1 * 0.4;
  return saturate(outc);
}
"""

HEADER = """\
[preset00]
MILKDROP_PRESET_VERSION=201
PSVERSION=2
PSVERSION_WARP=2
PSVERSION_COMP=2
fRating=5.000000
fGammaAdj=1.200000
fDecay={decay:.6f}
fVideoEchoZoom=1.000000
fVideoEchoAlpha=0.000000
nVideoEchoOrientation=0
nWaveMode={wave_mode}
bAdditiveWaves=0
bWaveDots=0
bWaveThick=1
bModWaveAlphaByVolume=0
bMaximizeWaveColor=1
bTexWrap=1
bDarkenCenter=0
bRedBlueStereo=0
bBrighten=0
bDarken=0
bSolarize=0
bInvert=0
fWaveAlpha={wave_alpha:.6f}
fWaveScale={wave_scale:.6f}
fWaveSmoothing=0.150000
fWaveParam={wave_param:.6f}
fModWaveAlphaStart=0.500000
fModWaveAlphaEnd=1.000000
fWarpAnimSpeed=1.000000
fWarpScale=1.000000
fZoomExponent=1.000000
fShader=0.000000
zoom=1.000000
rot=0.000000
cx=0.500000
cy=0.500000
dx=0.000000
dy=0.000000
warp=0.010000
sx=1.000000
sy=1.000000
wave_r=0.500000
wave_g=0.500000
wave_b=0.500000
wave_x=0.500000
wave_y={wave_y:.6f}
ob_size=0.005000
ob_r=0.000000
ob_g=0.000000
ob_b=0.000000
ob_a=0.450000
ib_size=0.000000
ib_r=0.000000
ib_g=0.000000
ib_b=0.000000
ib_a=0.000000
nMotionVectorsX=0.000000
nMotionVectorsY=0.000000
mv_dx=0.000000
mv_dy=0.000000
mv_l=0.000000
mv_r=0.000000
mv_g=0.000000
mv_b=0.000000
mv_a=0.000000
"""

PER_FRAME = """\
per_frame_1=dt = min(max(time - tl, 0.004), 0.08); tl = time;
per_frame_2=bm = bm + (bass - bm) * (1 - exp(-dt / 0.5));
per_frame_3=bd = bd + (abs(bass - bm) - bd) * (1 - exp(-dt / 1.6));
per_frame_4=hit = min(max(((bass - bm) / max(bd, 0.06) - 0.5) / 1.1, 0), 1);
per_frame_5=kick = max(kick * pow(0.82, 60 * dt), hit);
per_frame_6=k60 = pow(0.92, 60 * dt);
per_frame_7=sb = sb * k60 + bass_att * (1 - k60);
per_frame_8=sm = sm * k60 + mid_att * (1 - k60);
per_frame_9=st = st * k60 + treb_att * (1 - k60);
per_frame_10=scroll = scroll + dt * ({scroll:.4f} + 0.25 * st + 0.15 * sb + 0.35 * kick);
per_frame_11=dy = -({dy:.5f} + 0.004 * st + 0.006 * kick);
per_frame_12=ang = ang + dt * ({spin:.4f} + {spin_treb:.4f} * st);
per_frame_13=hue_shift = {hue:.4f} + 0.07 * time + 0.15 * st - 0.06 * sb; hue_shift = hue_shift - int(hue_shift);
per_frame_14=wave_r = min(0.2 + 0.7 * sb + 0.4 * kick + 0.2 * sin(time * 1.3), 1);
per_frame_15=wave_g = min(0.25 + 0.55 * sm + 0.3 * st + 0.15 * cos(time * 0.8), 1);
per_frame_16=wave_b = min(0.3 + 0.7 * st + 0.25 * sm, 1);
per_frame_17=q1 = kick; q2 = sb; q3 = sm; q4 = st; q5 = ang;
per_frame_18=q6 = scroll; q7 = {hue:.4f}; q8 = {block:.4f}; q9 = {poster:.4f}; q10 = {relief:.4f};
per_frame_19=q11 = hue_shift; q12 = sin(time * 0.41 + st); q13 = 0.85 + 0.2 * (sb + sm + st) * 0.35;
"""

WARP_TRAIL = COMMON + """
shader_body
{
  float2 suv = lerp(uv, uv_orig, 0.30 + 0.08 * q2);
  float3 prev = tex2D(sampler_main, uv).rgb;
  float3 trail = tex2D(sampler_main, suv).rgb * (0.93 + 0.03 * q2);
  float3 retc = max(prev, trail);
  float3 m = float3(q9, q9 * 0.85, q9 * 1.1);
  retc = lerp(retc, floor(retc * m + 0.25) / m, 0.12 + 0.08 * q3);
  float center = 1.0 - saturate(length(uv - uv_orig) * 35.0);
  retc = retc * (0.992 - 0.01 * q4) - 0.0012 - center * 0.0015;
  ret = max(retc, 0.0);
}
"""


PRESETS = [
    {
        "file": "01-jelly-relief-scroll.milk",
        "title": "Jelly relief scroll",
        "decay": 1.0,
        "wave_mode": 4,
        "wave_alpha": 1.4,
        "wave_scale": 0.02,
        "wave_param": -0.2,
        "wave_y": 0.02,
        "pf": dict(scroll=0.35, dy=0.009, spin=0.02, spin_treb=0.06, hue=0.08, block=24.0, poster=7.0, relief=1.0),
        "warp": WARP_TRAIL,
        "comp": COMMON
        + """
shader_body
{
  float3 rel = jelly_relief(uv);
  float3 ink = tex2D(sampler_main, uv).rgb;
  float3 tint = hue(q11 + 0.08 * q4, 0.85);
  float3 col = (0.55 + 0.55 * rel) * (0.35 + 1.1 * ink);
  col *= tint;
  col += tint * pow(rel.z, 2.0) * (0.35 + 0.55 * q1);
  col += GetBlur2(uv) * tint * 0.15;
  float3 diff = GetBlur3(uv) - GetBlur1(uv);
  col *= lerp(float3(1.0, 1.0, 1.0), 1.0 + diff * 1.4, 0.45);
  ret = led_tonemap(col * (1.1 + 0.25 * q10));
}
""",
    },
    {
        "file": "02-jelly-bitgrid.milk",
        "title": "Jelly machine-code bitgrid",
        "decay": 1.0,
        "wave_mode": 5,
        "wave_alpha": 0.9,
        "wave_scale": 0.35,
        "wave_param": 0.0,
        "wave_y": 0.5,
        "pf": dict(scroll=0.55, dy=0.011, spin=0.04, spin_treb=0.1, hue=0.55, block=28.0, poster=6.0, relief=1.15),
        "warp": COMMON
        + """
shader_body
{
  float2 suv = lerp(uv, uv_orig, 0.28);
  float3 prev = tex2D(sampler_main, uv).rgb;
  float3 trail = tex2D(sampler_main, suv + float2(0.0, 0.01 + 0.01 * q4)).rgb * 0.94;
  float3 retc = max(prev, trail);
  float2 gid = floor(uv * float2(q8, q8 * 1.35) + float2(q6 * 2.0, -q6 * 6.0));
  float bit = step(0.55 - 0.15 * q2, hash11(dot(gid, float2(12.9898, 78.233)) + floor(q6)));
  float edge = step(0.92, max(frac(uv.x * q8), frac(uv.y * q8 * 1.35)));
  float3 tint = hue(q11 + 0.05 * gid.y * 0.02, 1.0);
  retc += tint * bit * (0.045 + 0.06 * q1) * (1.0 - edge);
  retc += tint * edge * 0.02;
  float3 m = float3(q9, q9, q9 * 1.15);
  retc = lerp(retc, floor(retc * m + 0.2) / m, 0.18);
  retc = retc * 0.99 - 0.0015;
  ret = max(retc, 0.0);
}
""",
        "comp": COMMON
        + """
shader_body
{
  float3 rel = jelly_relief(uv);
  float3 ink = tex2D(sampler_main, uv).rgb + GetBlur1(uv) * 0.35;
  float3 tint = hue(q11 + ink.y * 0.2, 0.9);
  float3 col = tint * (0.25 + 1.2 * ink) * (0.45 + 0.7 * rel);
  col += float3(0.6, 0.9, 1.0) * pow(rel.z, 3.0) * (0.25 + 0.7 * q1);
  float2 gid = floor(uv * float2(q8, q8 * 1.35));
  float scan = 0.85 + 0.15 * sin(gid.y * 1.7 + time * 8.0 + 3.0 * q4);
  col *= scan;
  ret = led_tonemap(col * q10);
}
""",
    },
    {
        "file": "03-jelly-hex-lattice.milk",
        "title": "Jelly hex lattice",
        "decay": 0.995,
        "wave_mode": 0,
        "wave_alpha": 0.0,
        "wave_scale": 1.0,
        "wave_param": 0.0,
        "wave_y": 0.5,
        "pf": dict(scroll=0.4, dy=0.006, spin=0.08, spin_treb=0.18, hue=0.78, block=10.0, poster=8.0, relief=1.2),
        "warp": COMMON
        + """
shader_body
{
  float2 p = (uv - 0.5);
  float2 s = rot2(p, q5 * 0.15) * (0.98 - 0.04 * q1) + 0.5;
  float3 prev = tex2D(sampler_main, s).rgb;
  float3 trail = tex2D(sampler_main, lerp(s, uv_orig, 0.25)).rgb * 0.94;
  float3 retc = max(prev, trail);
  float2 g = uv * q8 + float2(q6 * 0.7, -q6 * 0.35);
  g.x += 0.5 * floor(g.y);
  float2 f = frac(g) - 0.5;
  float hex = max(abs(f.x) * 1.732 + abs(f.y) * 0.15, abs(f.y));
  float cell = smoothstep(0.48, 0.32, hex);
  float edge = exp(-abs(hex - 0.38) * 40.0);
  float3 tint = hue(q11 + 0.08 * floor(g.x + g.y), 1.0);
  retc += tint * cell * (0.03 + 0.05 * q2 + 0.04 * q1);
  retc += tint * edge * (0.05 + 0.08 * q4);
  float3 m = float3(q9, q9 * 0.9, q9);
  retc = lerp(retc, floor(retc * m + 0.25) / m, 0.14);
  ret = max(retc * 0.99 - 0.001, 0.0);
}
""",
        "comp": COMMON
        + """
shader_body
{
  float3 rel = jelly_relief(uv);
  float3 ink = tex2D(sampler_main, uv).rgb;
  float3 tint = hue(q11 + 0.12 * q3, 0.9);
  float3 col = tint * ink * (0.5 + 0.9 * rel);
  col += tint * pow(saturate(rel.z), 2.5) * (0.4 + 0.6 * q1);
  col += GetBlur2(uv) * hue(q11 + 0.33, 0.8) * 0.2;
  ret = led_tonemap(col * (1.05 + 0.2 * q10));
}
""",
    },
    {
        "file": "04-jelly-cascade.milk",
        "title": "Jelly code cascade",
        "decay": 1.0,
        "wave_mode": 3,
        "wave_alpha": 0.7,
        "wave_scale": 0.6,
        "wave_param": 0.0,
        "wave_y": 0.15,
        "pf": dict(scroll=0.85, dy=0.014, spin=0.03, spin_treb=0.12, hue=0.42, block=40.0, poster=5.5, relief=1.1),
        "warp": COMMON
        + """
shader_body
{
  float2 suv = uv + float2(0.002 * sin(uv.y * 40.0 + q6 * 5.0), 0.012 + 0.01 * q4);
  float3 prev = tex2D(sampler_main, uv).rgb;
  float3 trail = tex2D(sampler_main, lerp(suv, uv_orig, 0.22)).rgb * 0.92;
  float3 retc = max(prev, trail);
  float col_i = floor(uv.x * q8);
  float row = floor((1.0 - uv.y) * q8 * 1.6 + q6 * 8.0 + col_i * 1.7);
  float head = frac(row * 0.07 + q6 * 0.3 + hash11(col_i) * 0.5);
  float drop = smoothstep(0.15, 0.0, abs(frac(uv.y * q8 * 1.6 + q6 * 3.0 + hash11(col_i)) - head));
  float glyph = step(0.35, hash11(col_i * 19.0 + row));
  float3 tint = hue(q11 + 0.02 * col_i, 1.0);
  retc += tint * drop * glyph * (0.06 + 0.08 * q1 + 0.04 * q4);
  float3 m = float3(q9, q9 * 1.1, q9 * 0.9);
  retc = lerp(retc, floor(retc * m + 0.2) / m, 0.16);
  ret = max(retc * 0.988 - 0.0012, 0.0);
}
""",
        "comp": COMMON
        + """
shader_body
{
  float3 rel = jelly_relief(uv);
  float3 ink = tex2D(sampler_main, uv).rgb;
  float3 tint = hue(q11 + ink.x * 0.25, 0.95);
  float3 col = tint * (0.2 + 1.25 * ink) * (0.4 + 0.75 * rel);
  col += float3(0.7, 1.0, 0.85) * pow(rel.z, 2.5) * (0.2 + 0.8 * q1);
  float rain = smoothstep(0.7, 1.0, ink.g + ink.b);
  col += tint * rain * 0.25;
  ret = led_tonemap(col * q10);
}
""",
    },
    {
        "file": "05-jelly-plasma-blocks.milk",
        "title": "Jelly plasma blocks",
        "decay": 0.992,
        "wave_mode": 6,
        "wave_alpha": 0.55,
        "wave_scale": 0.8,
        "wave_param": 0.0,
        "wave_y": 0.5,
        "pf": dict(scroll=0.3, dy=0.005, spin=0.1, spin_treb=0.25, hue=0.92, block=12.0, poster=5.0, relief=1.25),
        "warp": COMMON
        + """
shader_body
{
  float2 p = (uv - 0.5);
  float2 s = rot2(p, q5 * 0.2) * (0.97 - 0.05 * q1) + 0.5;
  float3 prev = tex2D(sampler_main, s).rgb;
  float3 trail = tex2D(sampler_main, lerp(s, uv_orig, 0.35)).rgb * 0.93;
  float3 retc = max(prev, trail);
  float2 gid = floor((uv + float2(q6 * 0.15, -q6 * 0.1)) * q8);
  float2 f = frac((uv + float2(q6 * 0.15, -q6 * 0.1)) * q8) - 0.5;
  float n1 = sin(gid.x * 0.7 + time * 0.8 + q2);
  float n2 = cos(gid.y * 0.9 - time * 0.6 + q3);
  float plasma = 0.5 + 0.5 * sin(n1 + n2 + length(f) * 6.0 + q4);
  float box = 1.0 - smoothstep(0.42, 0.48, max(abs(f.x), abs(f.y)));
  float3 tint = hue(q11 + 0.15 * plasma + 0.05 * gid.x, 1.0);
  retc += tint * plasma * box * (0.05 + 0.07 * q1);
  float3 m = float3(q9, q9 * 0.8, q9 * 1.2);
  retc = lerp(retc, floor(retc * m + 0.3) / m, 0.22);
  ret = max(retc * 0.99 - 0.001, 0.0);
}
""",
        "comp": COMMON
        + """
shader_body
{
  float3 rel = jelly_relief(uv);
  float3 ink = tex2D(sampler_main, uv).rgb;
  float3 tint = hue(q11 + 0.2 * ink.x + 0.1 * q4, 0.9);
  float3 col = tint * (0.3 + 1.15 * ink) * (0.35 + 0.85 * rel);
  col += tint * pow(rel.z, 2.0) * (0.35 + 0.65 * q1);
  float3 diff = abs(GetBlur2(uv) - GetBlur1(uv));
  col += diff * hue(q11 + 0.5, 1.0) * 0.55;
  ret = led_tonemap(col * (1.05 + 0.2 * q10));
}
""",
    },
]


def write_preset(spec: dict) -> Path:
    path = ROOT / spec["file"]
    body = (
        HEADER.format(
            decay=spec["decay"],
            wave_mode=spec["wave_mode"],
            wave_alpha=spec["wave_alpha"],
            wave_scale=spec["wave_scale"],
            wave_param=spec["wave_param"],
            wave_y=spec["wave_y"],
        )
        + PER_FRAME.format(**spec["pf"])
        + lines("warp", spec["warp"])
        + lines("comp", spec["comp"])
    )
    path.write_text(body, encoding="utf-8")
    return path


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for spec in PRESETS:
        path = write_preset(spec)
        print(f"wrote {path.relative_to(ROOT.parent.parent)} ({spec['title']})")


if __name__ == "__main__":
    main()
