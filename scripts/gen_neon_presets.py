#!/usr/bin/env python3
"""Generate vivid neon-style GPL MilkDrop 2 presets for milk-ddp.

Bold high-saturation patterns: neon grids, tube glow, laser streaks, signage
flicker. Colours stay neon (magenta / cyan / lime / electric blue) and react
to bass, mid, treb, and kick. No MilkDrop 3 get_fft().
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "presets" / "neon"


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
float3 neon_hue(float h)
{
  float3 k = abs(frac(h + float3(0.0, 0.66667, 0.33333))*6.0 - 3.0) - 1.0;
  return saturate(k);
}
float3 neon_mix(float u)
{
  float h = frac(q11 + u * 0.35 + 0.15 * q4);
  float3 c = neon_hue(h);
  c = lerp(c, float3(1.0, 0.05, 0.85), saturate(q2 * 0.55));
  c = lerp(c, float3(0.05, 1.0, 0.55), saturate(q3 * 0.45));
  c = lerp(c, float3(0.1, 0.85, 1.0), saturate(q4 * 0.55));
  return saturate(c);
}
float glow_line(float d, float w)
{
  return exp(-abs(d) / max(w, 0.001));
}
float3 led_tonemap(float3 col)
{
  float lum = max(dot(col, float3(0.30, 0.59, 0.11)), 0.0001);
  float mapped = 1.0 - exp(-lum * 0.95);
  mapped = min(mapped, 0.92);
  float3 outc = (col / lum) * mapped * q13;
  outc += float3(1.0, 1.0, 1.0) * pow(mapped, 3.0) * q1 * 0.65;
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
bAdditiveWaves=1
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
fWaveSmoothing=0.500000
fWaveParam=0.000000
fModWaveAlphaStart=0.750000
fModWaveAlphaEnd=0.950000
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
warp=0.000000
sx=1.000000
sy=1.000000
wave_r=1.000000
wave_g=0.200000
wave_b=0.900000
wave_x=0.500000
wave_y=0.500000
ob_size=0.010000
ob_r=0.000000
ob_g=0.000000
ob_b=0.000000
ob_a=0.000000
ib_size=0.015000
ib_r=0.000000
ib_g=1.000000
ib_b=1.000000
ib_a=0.350000
nMotionVectorsX=0.000000
nMotionVectorsY=0.000000
mv_dx=0.000000
mv_dy=0.000000
mv_l=0.000000
mv_r=0.000000
mv_g=0.000000
mv_b=0.000000
mv_a=0.000000
wavecode_0_enabled=1
wavecode_0_samples=512
wavecode_0_sep=0
wavecode_0_bSpectrum=1
wavecode_0_bUseDots=0
wavecode_0_bDrawThick=1
wavecode_0_bAdditive=1
wavecode_0_scaling=1.400000
wavecode_0_smoothing=0.350000
wavecode_0_r=1.000000
wavecode_0_g=0.100000
wavecode_0_b=0.900000
wavecode_0_a=1.000000
wavecode_1_enabled=1
wavecode_1_samples=512
wavecode_1_sep=0
wavecode_1_bSpectrum=0
wavecode_1_bUseDots=0
wavecode_1_bDrawThick=1
wavecode_1_bAdditive=1
wavecode_1_scaling=1.100000
wavecode_1_smoothing=0.400000
wavecode_1_r=0.100000
wavecode_1_g=1.000000
wavecode_1_b=0.900000
wavecode_1_a=1.000000
wavecode_2_enabled=1
wavecode_2_samples=256
wavecode_2_sep=0
wavecode_2_bSpectrum=1
wavecode_2_bUseDots=1
wavecode_2_bDrawThick=1
wavecode_2_bAdditive=1
wavecode_2_scaling=1.000000
wavecode_2_smoothing=0.300000
wavecode_2_r=1.000000
wavecode_2_g=1.000000
wavecode_2_b=0.200000
wavecode_2_a=0.950000
wavecode_3_enabled=0
"""

WAVE_POINTS = """\
wave_0_per_point1=x = sample * 0.96 + 0.02;
wave_0_per_point2=y = 0.12 + value * 0.65;
wave_0_per_point3=r = 0.6 + 0.4 * bass_att + 0.5 * sample;
wave_0_per_point4=g = 0.05 + 0.4 * mid_att;
wave_0_per_point5=b = 0.7 + 0.3 * treb_att + 0.3 * (1 - sample);
wave_0_per_point6=a = 0.75 + 0.25 * value;
wave_1_per_point1=x = sample * 0.96 + 0.02;
wave_1_per_point2=y = 0.88 - value * 0.45;
wave_1_per_point3=r = 0.05 + 0.3 * bass;
wave_1_per_point4=g = 0.7 + 0.3 * mid_att;
wave_1_per_point5=b = 0.8 + 0.2 * treb;
wave_1_per_point6=a = 0.7 + 0.3 * value;
wave_2_per_point1=x = 0.5 + 0.42 * cos(sample * 6.2832 + time);
wave_2_per_point2=y = 0.5 + 0.42 * sin(sample * 6.2832 + time) * (0.4 + 0.6 * value);
wave_2_per_point3=r = 1.0;
wave_2_per_point4=g = 0.85 + 0.15 * treb_att;
wave_2_per_point5=b = 0.1 + 0.4 * mid;
wave_2_per_point6=a = 0.55 + 0.45 * value;
"""

PER_FRAME = """\
per_frame_1=dt = min(max(time - tl, 0.004), 0.08); tl = time;
per_frame_2=bm = bm + (bass - bm) * (1 - exp(-dt / 0.45));
per_frame_3=bd = bd + (abs(bass - bm) - bd) * (1 - exp(-dt / 1.5));
per_frame_4=hit = min(max(((bass - bm) / max(bd, 0.06) - 0.5) / 1.1, 0), 1);
per_frame_5=kick = max(kick * pow(0.80, 60 * dt), hit);
per_frame_6=k60 = pow(0.90, 60 * dt);
per_frame_7=sb = sb * k60 + bass_att * (1 - k60);
per_frame_8=sm = sm * k60 + mid_att * (1 - k60);
per_frame_9=st = st * k60 + treb_att * (1 - k60);
per_frame_10=ang = ang + dt * ({spin:.4f} + {spin_treb:.4f} * st + 0.15 * kick);
per_frame_11=scroll = scroll + dt * ({scroll:.4f} + 0.35 * st + 0.2 * sb);
per_frame_12=hue_shift = {hue:.4f} + 0.12 * time + 0.18 * st - 0.08 * sb + 0.05 * kick; hue_shift = hue_shift - int(hue_shift);
per_frame_13=ib_a = 0.25 + 0.45 * st + 0.25 * kick;
per_frame_14=ib_r = 0.1 + 0.7 * st; ib_g = 0.7 + 0.3 * sm; ib_b = 1.0;
per_frame_15=wave_r = min(0.4 + 0.8 * sb + 0.5 * kick, 1);
per_frame_16=wave_g = min(0.15 + 0.7 * sm + 0.4 * st, 1);
per_frame_17=wave_b = min(0.5 + 0.7 * st + 0.3 * sm, 1);
per_frame_18=q1 = kick; q2 = sb; q3 = sm; q4 = st; q5 = ang;
per_frame_19=q6 = scroll; q7 = {hue:.4f}; q8 = {scale:.4f}; q9 = {thick:.4f}; q10 = {density:.4f};
per_frame_20=q11 = hue_shift; q12 = min(0.85 + 0.25 * (sb+sm+st), 1.15); q13 = 0.78 + 0.18 * (sb+sm+st);
"""

WARP_NEON = COMMON + """
shader_body
{
  float2 suv = uv + float2(-0.003 - 0.004 * q2, 0.002 * sin(q6 * 5.0 + uv.x * 12.0));
  float3 prev = tex2D(sampler_main, suv).rgb;
  prev = lerp(prev, GetBlur1(suv), 0.08);
  float3 ink = tex2D(sampler_main, uv).rgb;
  ret = max(prev * (0.88 + 0.04 * q2), ink * (1.0 + 0.18 * q1));
  ret *= 0.96 + 0.03 * q4;
  ret = max(ret - 0.0012, 0.0);
}
"""

PRESETS = [
    {
        "file": "01-neon-grid.milk",
        "title": "Neon perspective grid",
        "decay": 0.960,
        "wave_mode": 5,
        "wave_alpha": 0.7,
        "wave_scale": 1.3,
        "pf": dict(spin=0.05, spin_treb=0.12, scroll=0.25, hue=0.85, scale=1.0, thick=0.012, density=14.0),
        "warp": WARP_NEON,
        "comp": COMMON
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float y = abs(p.y) + 0.08;
  float2 g = float2(p.x / y, 1.0 / y);
  g.x += q6 * 1.5;
  g.y += q6 * 0.8 + time * 0.4;
  float2 f = abs(frac(g * q10) - 0.5);
  float line = min(f.x, f.y);
  float beam = glow_line(line, q9 * (0.55 + 0.35 * q1));
  float horizon = exp(-abs(p.y) * 3.5);
  float3 tex = tex2D(sampler_main, uv).rgb;
  float3 col = neon_mix(g.x * 0.05) * beam * (0.95 + 0.45 * q4);
  col += neon_mix(0.3 + q3) * horizon * (0.18 + 0.28 * q2);
  col += tex * neon_mix(uv.x) * 0.22;
  col += neon_hue(q11 + 0.5) * pow(beam, 3.0) * 0.85;
  ret = led_tonemap(col);
}
""",
    },
    {
        "file": "02-neon-tubes.milk",
        "title": "Neon tube ribbons",
        "decay": 0.955,
        "wave_mode": 6,
        "wave_alpha": 0.65,
        "wave_scale": 1.2,
        "pf": dict(spin=0.22, spin_treb=0.35, scroll=0.2, hue=0.92, scale=1.1, thick=0.035, density=5.0),
        "warp": WARP_NEON,
        "comp": COMMON
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 q = rot2(p, q5 * 0.4);
  float3 col = float3(0.0, 0.0, 0.02);
  for (int i = 0; i < 5; i++)
  {
    float fi = float(i);
    float phase = q6 * (1.2 + 0.3 * fi) + fi * 1.7;
    float amp = (0.18 + 0.12 * q2 + 0.08 * q1) * (1.0 - 0.12 * fi);
    float wavy = amp * sin(q.x * (3.0 + fi) + phase + 2.0 * q3);
    float d = q.y - wavy - (fi - 2.0) * 0.16;
    float g = glow_line(d, q9 * (0.7 + 0.35 * q4 + 0.25 * q1));
    float3 c = neon_mix(0.15 * fi + q11);
    col += c * g * (0.9 + 0.25 * q1);
    col += c * pow(g, 4.0) * 1.1;
  }
  float3 tex = tex2D(sampler_main, uv).rgb;
  col += tex * neon_mix(uv.x + q6) * 0.28;
  float ring = glow_line(length(p) - (0.35 + 0.15 * q2), 0.02 + 0.015 * q1);
  col += neon_hue(q11 + 0.45) * ring * (0.55 + 0.45 * q4);
  ret = led_tonemap(col);
}
""",
    },
    {
        "file": "03-neon-lasers.milk",
        "title": "Neon laser starburst",
        "decay": 0.945,
        "wave_mode": 7,
        "wave_alpha": 0.75,
        "wave_scale": 1.4,
        "pf": dict(spin=0.35, spin_treb=0.55, scroll=0.3, hue=0.08, scale=1.0, thick=0.01, density=18.0),
        "warp": COMMON
        + """
shader_body
{
  float2 p = (uv - 0.5);
  float2 suv = uv + p * (-0.01 - 0.02 * q1) + float2(0.003 * q4, -0.002 * q2);
  float3 prev = tex2D(sampler_main, suv).rgb * (0.86 + 0.04 * q2);
  float3 ink = tex2D(sampler_main, uv).rgb;
  ret = max(prev, ink * (1.0 + 0.2 * q1));
  ret = max(ret - 0.0015, 0.0);
}
""",
        "comp": COMMON
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 r = rot2(p, q5);
  float theta = atan2(r.y, r.x);
  float rr = length(r);
  float spokes = abs(frac(theta / 6.2832 * q10 + q6) - 0.5);
  float beam = glow_line(spokes, q9 * (0.5 + 0.45 * q1 + 0.25 * q4));
  beam *= smoothstep(1.2, 0.05, rr);
  float rings = glow_line(frac(rr * (6.0 + 4.0 * q2) - q6 * 2.0) - 0.5, 0.03 + 0.02 * q3);
  float3 col = neon_mix(theta * 0.15) * beam * (1.05 + 0.35 * q1);
  col += neon_hue(q11 + 0.33) * rings * (0.45 + 0.4 * q3);
  col += neon_hue(q11) * exp(-rr * 4.0) * (0.25 + 0.35 * q1);
  float3 tex = tex2D(sampler_main, uv).rgb;
  col += tex * neon_mix(uv.y) * 0.25;
  ret = led_tonemap(col);
}
""",
    },
    {
        "file": "04-neon-signage.milk",
        "title": "Neon signage flicker blocks",
        "decay": 0.950,
        "wave_mode": 3,
        "wave_alpha": 0.6,
        "wave_scale": 1.1,
        "pf": dict(spin=0.02, spin_treb=0.08, scroll=0.22, hue=0.78, scale=1.0, thick=0.04, density=8.0),
        "warp": WARP_NEON,
        "comp": COMMON
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 g = p * q10 + float2(q6 * 0.7, -q6 * 0.25);
  float2 id = floor(g);
  float2 f = frac(g) - 0.5;
  float n = frac(sin(dot(id, float2(127.1, 311.7))) * 43758.5);
  float flicker = 0.55 + 0.45 * sin(time * (4.0 + 8.0 * n) + n * 20.0);
  flicker = lerp(flicker, 1.0, saturate(q1 * 1.5));
  float box = max(abs(f.x), abs(f.y));
  float edge = glow_line(box - 0.32, q9 * (0.5 + 0.5 * q4));
  float fill = smoothstep(0.38, 0.28, box);
  float3 c = neon_mix(n + q11);
  float3 col = c * fill * flicker * (0.22 + 0.28 * q2 + 0.22 * q3);
  col += c * edge * (0.95 + 0.55 * q4) * flicker;
  col += neon_hue(q11 + 0.5) * pow(edge, 3.0) * 0.9;
  float3 tex = tex2D(sampler_main, uv).rgb;
  col += tex * neon_mix(uv.x) * 0.22 * flicker;
  float scan = 0.88 + 0.12 * sin(uv.y * 480.0 + time * 20.0);
  col *= scan;
  ret = led_tonemap(col);
}
""",
    },
    {
        "file": "05-neon-circuit.milk",
        "title": "Neon circuit traces",
        "decay": 0.958,
        "wave_mode": 0,
        "wave_alpha": 0.0,
        "wave_scale": 1.0,
        "pf": dict(spin=0.08, spin_treb=0.15, scroll=0.28, hue=0.55, scale=1.0, thick=0.015, density=10.0),
        "warp": WARP_NEON,
        "comp": COMMON
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 q = rot2(p, q5 * 0.15) * q10 + float2(q6, q6 * 0.4);
  float2 f = frac(q) - 0.5;
  float2 id = floor(q);
  float rnd = frac(sin(dot(id, float2(12.9898, 78.233))) * 43758.5);
  float hx = abs(f.x);
  float hy = abs(f.y);
  float trace = min(hx, hy);
  float prefer = step(0.5, rnd);
  trace = lerp(hx, hy, prefer * 0.35);
  float pulse = frac(q6 * 0.5 + rnd + time * (0.2 + 0.5 * q4));
  float traveling = glow_line(pulse - saturate(max(f.x, f.y) + 0.5), 0.05 + 0.04 * q1);
  float g = glow_line(trace - 0.02, q9 * (0.7 + 0.8 * q3));
  float3 c = neon_mix(rnd + q11);
  float3 col = c * g * (1.05 + 0.40 * q2);
  col += neon_hue(q11 + 0.25) * traveling * g * (1.1 + 0.65 * q1);
  col += c * pow(g, 4.0) * 1.05;
  float node = glow_line(length(f) - 0.02, 0.02 + 0.015 * q1);
  col += neon_hue(q11 + 0.1) * node * (0.45 + 0.35 * q4);
  float3 tex = tex2D(sampler_main, uv).rgb;
  col += tex * neon_mix(uv.y) * 0.2;
  ret = led_tonemap(col);
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
        )
        + WAVE_POINTS
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
