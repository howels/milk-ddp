#!/usr/bin/env python3
"""Generate original GPL-3.0 MilkDrop 2 fractal presets for milk-ddp.

MilkDrop 2 warp/comp shaders (no MilkDrop 3 get_fft). Iteration counts are
kept moderate so 128×128 matrices stay interactive on Mesa llvmpipe.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "presets" / "fractal"

HEADER = """\
[preset00]
MILKDROP_PRESET_VERSION=201
PSVERSION=2
PSVERSION_WARP=2
PSVERSION_COMP=2
fRating=4.000000
fGammaAdj=1.000000
fDecay=0.980000
fVideoEchoZoom=1.000000
fVideoEchoAlpha=0.000000
nVideoEchoOrientation=0
nWaveMode=0
bAdditiveWaves=0
bWaveDots=0
bWaveThick=0
bModWaveAlphaByVolume=0
bMaximizeWaveColor=0
bTexWrap=1
bDarkenCenter=0
bRedBlueStereo=0
bBrighten=0
bDarken=0
bSolarize=0
bInvert=0
fWaveAlpha=0.000000
fWaveScale=1.000000
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
wave_r=0.500000
wave_g=0.500000
wave_b=0.500000
wave_x=0.500000
wave_y=0.500000
ob_size=0.000000
ob_r=0.000000
ob_g=0.000000
ob_b=0.000000
ob_a=0.000000
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
per_frame_2=bm = bm + (bass - bm) * (1 - exp(-dt / 0.7));
per_frame_3=bd = bd + (abs(bass - bm) - bd) * (1 - exp(-dt / 2.0));
per_frame_4=hit = min(max(((bass - bm) / max(bd, 0.08) - 0.7) / 1.4, 0), 1);
per_frame_5=kick = max(kick * pow(0.88, 60 * dt), hit);
per_frame_6=k60 = pow(0.96, 60 * dt);
per_frame_7=sb = sb * k60 + bass_att * (1 - k60);
per_frame_8=sm = sm * k60 + mid_att * (1 - k60);
per_frame_9=st = st * k60 + treb_att * (1 - k60);
per_frame_10=zoom_amt = {zoom_base:.4f} + {zoom_bass:.4f} * sb + {zoom_kick:.4f} * kick;
per_frame_11=ang = ang + dt * ({spin:.4f} + {spin_treb:.4f} * st + 0.08 * kick);
per_frame_12=cx_j = {cx:.4f} + {cx_amp:.4f} * sin(time * {cx_freq:.4f}) + 0.04 * sin(time * 0.61) * st;
per_frame_13=cy_j = {cy:.4f} + {cy_amp:.4f} * cos(time * {cy_freq:.4f} + 0.7) + 0.03 * cos(time * 0.47) * sm;
per_frame_14=q1 = kick; q2 = cx_j; q3 = cy_j; q4 = zoom_amt; q5 = ang;
per_frame_15=q6 = sb; q7 = sm; q8 = st; q9 = {hue:.4f}; q10 = {scale:.4f};
per_frame_16=q11 = sin(time * 0.37 + 0.9 * st); q12 = cos(time * 0.23 + 0.6 * sm); q13 = sin(time * 0.51 + sb);
"""

# Extra per-frame lines for forward-rush presets (MilkDrop zoom + depth clock).
RUSH_PER_FRAME = """\
per_frame_17=zoom = {md_zoom:.4f} + {md_zoom_bass:.4f} * sb + {md_zoom_kick:.4f} * kick;
per_frame_18=depth = depth + dt * ({depth_speed:.4f} + {depth_bass:.4f} * sb + {depth_kick:.4f} * kick);
per_frame_19=q14 = depth; q15 = zoom;
"""


def lines(prefix: str, body: str) -> str:
    out = []
    n = 0
    for raw in body.strip().splitlines():
        if not raw.strip():
            continue
        n += 1
        out.append(f"{prefix}_{n}=`{raw}")
    return "\n".join(out) + "\n"


COMMON_FUNCS = """\
float2 cmul(float2 a, float2 b)
{
  return float2(a.x*b.x - a.y*b.y, a.x*b.y + a.y*b.x);
}
float2 rot2(float2 p, float a)
{
  float c = cos(a); float s = sin(a);
  return float2(c*p.x - s*p.y, s*p.x + c*p.y);
}
float3 hue(float h, float s)
{
  float3 k = abs(frac(h + float3(0.0, 0.66667, 0.33333))*6.0 - 3.0) - 1.0;
  return (1.0 - s) + s*saturate(k);
}
float3 led_tonemap(float3 col)
{
  float lum = max(dot(col, float3(0.30, 0.59, 0.11)), 0.0001);
  float mapped = 1.0 - exp(-lum * 1.05);
  mapped = min(mapped, 0.92);
  float3 outc = (col / lum) * mapped;
  outc += float3(1.0, 1.0, 1.0) * pow(mapped, 3.0) * q1 * 0.45;
  return saturate(outc * 1.08);
}
float hash11(float n)
{
  return frac(sin(n) * 43758.5453);
}
float noise2(float2 p)
{
  float2 i = floor(p);
  float2 f = frac(p);
  f = f * f * (3.0 - 2.0 * f);
  float a = hash11(i.x + i.y * 57.0);
  float b = hash11(i.x + 1.0 + i.y * 57.0);
  float c = hash11(i.x + (i.y + 1.0) * 57.0);
  float d = hash11(i.x + 1.0 + (i.y + 1.0) * 57.0);
  return lerp(lerp(a, b, f.x), lerp(c, d, f.x), f.y);
}
float fbm2(float2 p)
{
  float a = 0.0;
  float w = 0.5;
  for (int i = 0; i < 5; i++)
  {
    a += w * noise2(p);
    p = p * 2.03 + float2(17.0, 9.0);
    w *= 0.5;
  }
  return a;
}
"""

PRESETS = [
    {
        "file": "01-julia-lattice.milk",
        "title": "Julia lattice",
        "pf": dict(
            zoom_base=1.35,
            zoom_bass=0.25,
            zoom_kick=0.35,
            spin=0.08,
            spin_treb=0.12,
            cx=-0.12,
            cy=0.65,
            cx_amp=0.18,
            cy_amp=0.14,
            cx_freq=0.11,
            cy_freq=0.09,
            hue=0.08,
            scale=1.15,
        ),
        "warp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 s = rot2(p, q5) * (0.92 + 0.08 * q1);
  float2 suv = s / float2(ar, 1.0) + 0.5;
  float3 prev = tex2D(sampler_main, suv).rgb;
  float2 z = p * q10;
  float2 c = float2(q2, q3);
  float m = 9.0;
  float n = 0.0;
  for (int i = 0; i < 12; i++)
  {
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    float d2 = dot(z, z);
    m = min(m, abs(z.x * z.y));
    n += step(d2, 64.0);
  }
  float rim = smoothstep(4.0, 10.0, n) * (1.0 - smoothstep(10.0, 12.0, n));
  float3 em = hue(q9 + 0.05 * sqrt(m), 0.9) * exp(-m * 18.0);
  em += float3(1.0, 0.75, 0.4) * rim * 0.45;
  ret = prev * 0.90 + em * (0.02 + 0.03 * q1);
  ret = max(ret - 0.002, 0.0);
}
""",
        "comp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float r = length(p);
  float2 z = p * q10;
  float2 c = float2(q2, q3);
  float m1 = 9.0;
  float m2 = 9.0;
  float nu = 0.0;
  float esc = 0.0;
  for (int i = 0; i < 28; i++)
  {
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    float d2 = dot(z, z);
    m1 = min(m1, abs(z.x));
    m2 = min(m2, abs(z.y));
    if (d2 > 256.0)
    {
      nu = float(i) + 1.0 - log2(0.5 * log2(d2));
      esc = 1.0;
      break;
    }
  }
  float f = frac(nu * 0.35 + q8 * 0.1);
  float3 pane = hue(q9 + 0.12 * floor(nu), 1.0) * (0.15 + 0.85 * pow(sin(3.14159 * f), 1.2));
  float edge = min(f, 1.0 - f);
  pane += float3(1.0, 0.8, 0.45) * exp(-edge * edge * 900.0) * 0.5;
  pane += hue(q9 + 0.55, 1.0) * exp(-min(m1, m2) * 40.0) * 0.6;
  float3 col = lerp(pane * 0.35, pane, esc);
  float3 tr = tex2D(sampler_main, uv).rgb;
  col = col + tr * 0.25 + GetBlur2(uv) * 0.08;
  col *= lerp(0.35, 1.0, smoothstep(1.3, 0.25, r));
  ret = led_tonemap(col);
}
""",
    },
    {
        "file": "02-burning-ship.milk",
        "title": "Burning ship",
        "pf": dict(
            zoom_base=1.55,
            zoom_bass=0.2,
            zoom_kick=0.4,
            spin=-0.03,
            spin_treb=0.05,
            cx=-1.75,
            cy=-0.04,
            cx_amp=0.08,
            cy_amp=0.05,
            cx_freq=0.07,
            cy_freq=0.05,
            hue=0.02,
            scale=0.55,
        ),
        "warp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 s = p * (1.0 - 0.04 * q1);
  float2 suv = s / float2(ar, 1.0) + 0.5;
  float3 prev = tex2D(sampler_main, suv).rgb;
  float2 z = float2(0.0, 0.0);
  float2 c = float2(q2, q3) + p * q10 * q4;
  float n = 0.0;
  for (int i = 0; i < 10; i++)
  {
    z = float2(abs(z.x), abs(z.y));
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    n += step(dot(z, z), 64.0);
  }
  float3 em = hue(q9 + 0.08 * n, 0.95) * smoothstep(2.0, 9.0, n) * 0.03;
  em += float3(1.0, 0.35, 0.1) * q1 * 0.02;
  ret = prev * 0.93 + em;
  ret = max(ret - 0.003, 0.0);
}
""",
        "comp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 z = float2(0.0, 0.0);
  float2 c = float2(q2, q3) + rot2(p, q5) * q10 * q4;
  float nu = 0.0;
  float esc = 0.0;
  float trap = 9.0;
  for (int i = 0; i < 26; i++)
  {
    z = float2(abs(z.x), abs(z.y));
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    float d2 = dot(z, z);
    trap = min(trap, abs(z.y));
    if (d2 > 256.0)
    {
      nu = float(i) + 1.0 - log2(0.5 * log2(d2));
      esc = 1.0;
      break;
    }
  }
  float3 fire = hue(q9 + 0.04 * nu + 0.1 * q7, 1.0);
  fire *= 0.2 + 0.9 * smoothstep(0.0, 18.0, nu);
  fire += float3(1.0, 0.55, 0.15) * exp(-trap * 25.0);
  float3 col = lerp(fire * 0.25, fire, esc);
  col += tex2D(sampler_main, uv).rgb * 0.2;
  ret = led_tonemap(col);
}
""",
    },
    {
        "file": "03-mandelbrot-drift.milk",
        "title": "Mandelbrot drift",
        "pf": dict(
            # Wide window on the main cardioid: colour lives in the exterior, so
            # a deep zoom into the set left only a dark body with edge filaments.
            # scale/zoom ≈ 1.7 → half-height ~0.85, set spans most of a square frame.
            zoom_base=0.85,
            zoom_bass=0.18,
            zoom_kick=0.28,
            spin=0.015,
            spin_treb=0.06,
            cx=-0.70,
            cy=0.0,
            cx_amp=0.14,
            cy_amp=0.10,
            cx_freq=0.05,
            cy_freq=0.07,
            hue=0.55,
            scale=1.45,
        ),
        "warp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 s = rot2(p, q5 * 0.25) * (0.97 - 0.05 * q1);
  float2 suv = s / float2(ar, 1.0) + 0.5;
  float3 prev = lerp(tex2D(sampler_main, suv).rgb, GetBlur1(suv), 0.2);
  float2 c = float2(q2, q3) + p / q4 * q10;
  float2 z = float2(0.0, 0.0);
  float n = 0.0;
  for (int i = 0; i < 11; i++)
  {
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    n += step(dot(z, z), 16.0);
  }
  float3 em = hue(q9 + 0.03 * n, 0.85) * smoothstep(3.0, 10.0, n) * 0.025;
  ret = max(prev * 0.91 + em * (1.0 + q1), 0.0);
}
""",
        "comp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 c = float2(q2, q3) + rot2(p, q5) / q4 * q10;
  float2 z = float2(0.0, 0.0);
  float nu = 0.0;
  float esc = 0.0;
  float m = 9.0;
  for (int i = 0; i < 30; i++)
  {
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    float d2 = dot(z, z);
    m = min(m, length(z - float2(0.0, 0.0)));
    if (d2 > 256.0)
    {
      nu = float(i) + 1.0 - log2(0.5 * log2(d2));
      esc = 1.0;
      break;
    }
  }
  float bands = frac(nu * 0.2 + time * 0.03);
  float3 col = hue(q9 + 0.15 * floor(nu * 0.25), 1.0);
  col *= 0.12 + 0.9 * pow(sin(3.14159 * bands), 1.1);
  col += float3(0.7, 0.9, 1.0) * exp(-m * 8.0) * 0.4;
  col = lerp(col * 0.3, col, esc);
  col += tex2D(sampler_main, uv).rgb * 0.22 + GetBlur3(uv) * 0.06;
  ret = led_tonemap(col);
}
""",
    },
    {
        "file": "04-tricorn-mirror.milk",
        "title": "Tricorn mirror",
        "pf": dict(
            zoom_base=1.4,
            zoom_bass=0.22,
            zoom_kick=0.3,
            spin=0.11,
            spin_treb=0.15,
            cx=-0.2,
            cy=0.0,
            cx_amp=0.2,
            cy_amp=0.18,
            cx_freq=0.13,
            cy_freq=0.1,
            hue=0.72,
            scale=1.05,
        ),
        "warp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 s = rot2(p, -q5 * 0.5) * (0.94 + 0.06 * q8);
  float2 suv = abs(s) / float2(ar, 1.0) * float2(sign(s.x + 0.0001), sign(s.y + 0.0001)) + 0.5;
  float3 prev = tex2D(sampler_main, suv).rgb;
  float2 z = p * q10;
  float2 c = float2(q2, q3);
  float n = 0.0;
  for (int i = 0; i < 12; i++)
  {
    z = float2(z.x*z.x - z.y*z.y, -2.0*z.x*z.y) + c;
    n += step(dot(z, z), 36.0);
  }
  float3 em = hue(q9 - 0.04 * n, 0.9) * smoothstep(3.0, 11.0, n) * 0.028;
  ret = max(prev * 0.89 + em * (1.0 + 1.2 * q1), 0.0);
}
""",
        "comp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 z = rot2(p, q5) * q10;
  float2 c = float2(q2, q3);
  float nu = 0.0;
  float esc = 0.0;
  float trap = 9.0;
  for (int i = 0; i < 26; i++)
  {
    z = float2(z.x*z.x - z.y*z.y, -2.0*z.x*z.y) + c;
    float d2 = dot(z, z);
    trap = min(trap, abs(abs(z.x) - abs(z.y)));
    if (d2 > 200.0)
    {
      nu = float(i) + 1.0 - log2(0.5 * log2(d2));
      esc = 1.0;
      break;
    }
  }
  float3 col = hue(q9 + 0.07 * nu + 0.05 * q7, 1.0);
  col *= 0.15 + 0.85 * smoothstep(0.0, 20.0, nu);
  col += float3(0.9, 0.7, 1.0) * exp(-trap * 35.0) * 0.7;
  col = lerp(col * 0.28, col, esc);
  float2 mir = float2(1.0 - uv.x, uv.y);
  col += tex2D(sampler_main, mir).rgb * 0.18;
  col += GetBlur2(uv).rgb * 0.07;
  ret = led_tonemap(col);
}
""",
    },
    {
        "file": "05-barnsley-fern.milk",
        "title": "Barnsley fern canopy",
        "pf": dict(
            zoom_base=1.25,
            zoom_bass=0.35,
            zoom_kick=0.45,
            spin=0.14,
            spin_treb=0.28,
            cx=0.0,
            cy=5.0,
            cx_amp=1.1,
            cy_amp=1.4,
            cx_freq=0.17,
            cy_freq=0.13,
            hue=0.32,
            scale=0.095,
        ),
        "warp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 s = rot2(p, q5 * 0.55 + 0.15 * q11) * (0.94 - 0.08 * q1);
  s += float2(0.01 * q12, 0.008 * q13);
  float2 suv = s / float2(ar, 1.0) + 0.5;
  float3 prev = lerp(tex2D(sampler_main, suv).rgb, GetBlur1(suv), 0.18);
  float sc = q10 * (0.85 + 0.2 * q4) * (1.0 + 0.12 * q12);
  float2 tgt = rot2(p, q5 * 0.35) / sc + float2(q2 * 0.25, 4.5 + q3 * 0.08);
  float2 z = float2(0.0, 0.0);
  float d = 9.0;
  float sway = 0.04 + 0.035 * q11 + 0.02 * q8;
  for (int i = 0; i < 40; i++)
  {
    float r = hash11(float(i) * 1.7 + time * 2.8 + q6 * 4.0 + 0.7 * q13);
    if (r < 0.01)
    {
      z = float2(0.0, 0.16 * z.y);
    }
    else if (r < 0.86)
    {
      z = float2(0.85 * z.x + sway * z.y, -sway * z.x + 0.85 * z.y + 1.6);
    }
    else if (r < 0.93)
    {
      z = float2(0.20 * z.x - 0.26 * z.y, 0.23 * z.x + 0.22 * z.y + 1.6);
    }
    else
    {
      z = float2(-0.15 * z.x + 0.28 * z.y, 0.26 * z.x + 0.24 * z.y + 0.44);
    }
    d = min(d, length(z - tgt));
  }
  float leaf = exp(-d * d * (50.0 + 20.0 * q7));
  float3 em = hue(q9 + 0.12 * time + 0.08 * tgt.y * 0.1, 0.95) * leaf;
  em *= 0.05 + 0.07 * q1 + 0.03 * q8;
  ret = max(prev * 0.88 + em, 0.0);
}
""",
        "comp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float sc = q10 * (0.85 + 0.2 * q4) * (1.0 + 0.15 * q12);
  float2 tgt = rot2(p, q5 * 0.45 + 0.1 * q11) / sc;
  tgt += float2(q2 * 0.2, 4.8 + 0.12 * q3 + 0.25 * q13);
  float2 z = float2(0.0, 0.0);
  float d = 9.0;
  float stem = 9.0;
  float sway = 0.04 + 0.04 * q11 + 0.025 * q8;
  for (int i = 0; i < 52; i++)
  {
    float r = hash11(float(i) * 1.7 + time * 3.1 + q6 * 3.5 + 0.5 * q12);
    if (r < 0.01)
    {
      z = float2(0.0, 0.16 * z.y);
    }
    else if (r < 0.86)
    {
      z = float2(0.85 * z.x + sway * z.y, -sway * z.x + 0.85 * z.y + 1.6);
    }
    else if (r < 0.93)
    {
      z = float2(0.20 * z.x - 0.26 * z.y, 0.23 * z.x + 0.22 * z.y + 1.6);
    }
    else
    {
      z = float2(-0.15 * z.x + 0.28 * z.y, 0.26 * z.x + 0.24 * z.y + 0.44);
    }
    d = min(d, length(z - tgt));
    stem = min(stem, abs(z.x) + 0.15 * abs(z.y - tgt.y));
  }
  float leaf = exp(-d * d * (48.0 + 28.0 * q1));
  float vein = exp(-stem * stem * 65.0) * 0.5;
  float ground = smoothstep(0.55, 0.05, p.y + 0.35 + 0.08 * q12);
  float3 foliage = hue(q9 + 0.1 * time + 0.05 * tgt.y + 0.12 * q7, 1.0);
  float3 col = foliage * (leaf * 2.0 + vein);
  col += float3(0.15, 0.22, 0.08) * ground * (0.35 + 0.25 * q6);
  col += tex2D(sampler_main, uv).rgb * 0.42;
  col += GetBlur2(uv) * 0.1;
  ret = led_tonemap(col);
}
""",
    },
    {
        "file": "06-branching-tree.milk",
        "title": "Branching fractal tree",
        "pf": dict(
            # Lower scale maps screen pixels into a smaller SDF domain so the
            # folded tree fills most of the frame rather than a mid-height strip.
            zoom_base=1.05,
            zoom_bass=0.22,
            zoom_kick=0.35,
            spin=0.10,
            spin_treb=0.28,
            cx=0.45,
            cy=0.30,
            cx_amp=0.28,
            cy_amp=0.22,
            cx_freq=0.22,
            cy_freq=0.18,
            hue=0.12,
            scale=0.72,
        ),
        "warp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 s = rot2(p, q5 * 0.35) * (0.95 - 0.08 * q1);
  s += float2(0.012 * q11, 0.01 * sin(time * 1.4 + q6));
  float2 suv = s / float2(ar, 1.0) + 0.5;
  float3 prev = tex2D(sampler_main, suv).rgb;
  float2 q = float2(p.x, p.y + 0.52) * q10 * (0.78 + 0.10 * q4);
  q = rot2(q, 0.2 * q11);
  float d = 9.0;
  for (int i = 0; i < 8; i++)
  {
    q.x = abs(q.x);
    float2 a = q - float2(0.0, 0.20 + 0.04 * q2);
    d = min(d, length(float2(a.x, max(a.y, 0.0))) - (0.042 - 0.004 * float(i)));
    float wind = q2 * 0.55 + 0.4 * q11 + 0.18 * sin(time * 1.7 + float(i));
    q = rot2(q, wind) * (1.28 + 0.10 * q7 + 0.04 * q1) - float2(0.0, 0.24);
  }
  float3 em = hue(q9 + 0.08 * time + 0.05 * q8, 0.9) * exp(-d * d * 280.0);
  em *= 0.06 + 0.07 * q1;
  ret = max(prev * 0.88 + em, 0.0);
}
""",
        "comp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 q = float2(p.x, p.y + 0.55) * q10 * (0.75 + 0.12 * q4);
  q = rot2(q, q5 * 0.15 + 0.25 * q11);
  float d = 9.0;
  float leaf_d = 9.0;
  for (int i = 0; i < 11; i++)
  {
    q.x = abs(q.x);
    float thick = 0.05 - 0.0038 * float(i);
    float2 a = q - float2(0.0, 0.18 + 0.035 * q6 + 0.025 * q12);
    d = min(d, length(float2(a.x, max(a.y, 0.0))) - thick);
    leaf_d = min(leaf_d, length(q - float2(0.0, 0.04)) - (0.11 - 0.007 * float(i)));
    float bend = q2 * 0.75 + 0.35 * q11 + 0.25 * q8 + 0.12 * sin(time * 2.1 + float(i));
    q = rot2(q, bend) * (1.26 + 0.12 * q7 + 0.05 * q1) - float2(0.0, 0.22 + 0.025 * q13);
  }
  float trunk = exp(-d * d * (160.0 + 55.0 * q1));
  float canopy = exp(-leaf_d * leaf_d * 42.0) * smoothstep(0.55, -0.35, p.y + 0.04 * q12);
  float soil = smoothstep(0.72, 0.42, p.y);
  float3 bark = float3(0.35, 0.18, 0.08) * (0.7 + 0.3 * q6);
  float3 leaves = hue(q9 + 0.18 + 0.1 * time + 0.12 * q7, 1.0);
  float3 col = bark * trunk * 2.0 + leaves * canopy * 1.7;
  col += float3(0.12, 0.2, 0.06) * soil * 0.28;
  col += float3(0.45, 0.7, 1.0) * pow(saturate(0.05 - p.y), 2.0) * 0.2;
  col += tex2D(sampler_main, uv).rgb * 0.4;
  ret = led_tonemap(col);
}
""",
    },
    {
        "file": "07-coastline-fjord.milk",
        "title": "Coastline fjord Mandelbrot",
        "pf": dict(
            zoom_base=2.4,
            zoom_bass=0.55,
            zoom_kick=0.75,
            spin=0.1,
            spin_treb=0.22,
            cx=-0.65,
            cy=0.45,
            cx_amp=0.28,
            cy_amp=0.22,
            cx_freq=0.11,
            cy_freq=0.14,
            hue=0.55,
            scale=0.85,
        ),
        "warp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 s = rot2(p, q5 * 0.4 + 0.08 * q11) * (0.96 - 0.07 * q1);
  s += float2(0.006 * q12, 0.004 * q13);
  float2 suv = s / float2(ar, 1.0) + 0.5;
  float3 prev = lerp(tex2D(sampler_main, suv).rgb, GetBlur1(suv), 0.2);
  float2 c = float2(q2, q3) + rot2(p, q5 * 0.25) / q4 * q10;
  float2 z = float2(0.0, 0.0);
  float n = 0.0;
  for (int i = 0; i < 12; i++)
  {
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    n += step(dot(z, z), 16.0);
  }
  float3 foam = float3(0.7, 0.9, 1.0) * smoothstep(4.0, 11.0, n);
  foam *= 0.025 + 0.03 * q1 + 0.015 * q8;
  ret = max(prev * 0.89 + foam, 0.0);
}
""",
        "comp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 c = float2(q2, q3) + rot2(p, q5 + 0.15 * q11) / q4 * q10;
  c += 0.04 * float2(q12, q13);
  float2 z = float2(0.0, 0.0);
  float nu = 0.0;
  float esc = 0.0;
  float trap = 9.0;
  for (int i = 0; i < 28; i++)
  {
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    float d2 = dot(z, z);
    trap = min(trap, abs(z.y));
    if (d2 > 256.0)
    {
      nu = float(i) + 1.0 - log2(0.5 * log2(d2));
      esc = 1.0;
      break;
    }
  }
  float bands = frac(nu * 0.22 + time * 0.07 + 0.1 * q8);
  float depth = saturate(nu / 22.0);
  float3 deep = float3(0.02, 0.08, 0.22);
  float3 shallow = hue(q9 + 0.08 * time + 0.1 * bands, 0.85) * float3(0.15, 0.7, 0.85);
  float3 foam = float3(0.75, 0.9, 1.0);
  float3 land = hue(q9 + 0.15 + 0.1 * q6 + 0.05 * q11, 0.9) * float3(0.55, 0.75, 0.28);
  float3 sea = lerp(deep, shallow, depth);
  sea = lerp(sea, foam, exp(-trap * 28.0) * esc * (0.7 + 0.3 * sin(time * 3.0 + nu)));
  float3 col = lerp(land * (0.45 + 0.4 * q7), sea, esc);
  float horizon = smoothstep(0.25, -0.05, p.y + 0.06 * q12);
  col = lerp(col, float3(0.35, 0.55, 0.85), horizon * 0.35 * (1.0 - esc));
  col += tex2D(sampler_main, uv).rgb * 0.28;
  ret = led_tonemap(col);
}
""",
    },
    {
        "file": "08-mountain-range.milk",
        "title": "Fractal mountain range",
        "pf": dict(
            zoom_base=1.25,
            zoom_bass=0.3,
            zoom_kick=0.4,
            spin=0.04,
            spin_treb=0.1,
            cx=0.0,
            cy=0.15,
            cx_amp=1.6,
            cy_amp=0.45,
            cx_freq=0.14,
            cy_freq=0.09,
            hue=0.08,
            scale=2.4,
        ),
        "warp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 suv = uv + float2(-0.01 - 0.008 * q6 - 0.006 * q12, 0.003 * sin(time * 1.2 + q6 * 4.0));
  float3 prev = lerp(tex2D(sampler_main, suv).rgb, GetBlur1(suv), 0.22);
  float sc = q10 * (0.85 + 0.2 * q4);
  float h = fbm2(float2(p.x * sc + q2 + time * 0.55, q3 + time * 0.12 + q6 * 0.3));
  float ridge = exp(-abs(p.y + 0.15 + 0.05 * q11 - (h - 0.55) * 0.9) * 16.0);
  float3 em = hue(q9 + 0.1 * h + 0.08 * time, 0.85) * ridge;
  em *= 0.03 + 0.04 * q1 + 0.02 * q8;
  ret = max(prev * 0.87 + em, 0.0);
}
""",
        "comp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float scroll = time * 0.42 + q2 * 0.9 + q6 * 1.1 + 0.35 * q12;
  float sc = q10 * (0.8 + 0.25 * q4);
  float h1 = fbm2(float2(p.x * sc + scroll, 1.7 + q3 + 0.2 * q11));
  float h2 = fbm2(float2(p.x * (sc * 1.6) + scroll * 1.35, 4.2 + 0.15 * q13));
  float h3 = fbm2(float2(p.x * (sc * 0.55) + scroll * 0.45, 0.8 + time * 0.05));
  float ridge = (h1 - 0.42) * 0.85 + (h2 - 0.5) * 0.25 + 0.04 * q1;
  float far = (h3 - 0.45) * 0.55 - 0.08;
  float y = p.y + 0.12 + 0.06 * q11 + 0.04 * sin(time * 0.7);
  float near_m = smoothstep(0.02, -0.02, y - ridge);
  float far_m = smoothstep(0.03, -0.01, y - far) * (1.0 - near_m);
  float sky_m = 1.0 - saturate(near_m + far_m);
  float snow = smoothstep(0.32, 0.6, ridge + 0.18 * q1 + 0.05 * q8);
  float3 rock = hue(q9 + 0.06 * h1 + 0.04 * time, 0.6) * float3(0.55, 0.42, 0.32);
  float3 snowc = float3(0.85, 0.9, 0.95);
  float3 near_col = lerp(rock, snowc, snow);
  near_col *= 0.45 + 0.55 * saturate((ridge - y) * 3.0 + 0.3);
  float3 far_col = float3(0.35, 0.4, 0.5) * (0.6 + 0.3 * h3);
  float day = 0.5 + 0.5 * q12;
  float3 sky = lerp(float3(0.25, 0.35, 0.65), float3(0.95, 0.55, 0.28), saturate(q8 * 0.7 + 0.3 * day));
  sky = lerp(sky, float3(0.55, 0.72, 0.95), day);
  sky *= 0.75 + 0.25 * (1.0 - abs(p.x));
  float3 col = sky * sky_m + far_col * far_m + near_col * near_m;
  float treeline = near_m * smoothstep(0.25, 0.05, ridge) * smoothstep(-0.05, 0.1, ridge);
  col = lerp(col, float3(0.1, 0.28, 0.12), treeline * 0.55);
  col += tex2D(sampler_main, uv).rgb * 0.28;
  ret = led_tonemap(col);
}
""",
    },
    {
        "file": "09-lightning-rivers.milk",
        "title": "Lightning river veins",
        "pf": dict(
            zoom_base=1.55,
            zoom_bass=0.4,
            zoom_kick=0.7,
            spin=0.18,
            spin_treb=0.45,
            cx=-0.1,
            cy=0.65,
            cx_amp=0.45,
            cy_amp=0.35,
            cx_freq=0.2,
            cy_freq=0.16,
            hue=0.58,
            scale=1.25,
        ),
        "warp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 s = rot2(p, q5 * 0.75 + 0.2 * q11) * (0.90 - 0.12 * q1);
  s += 0.015 * float2(q12, q13);
  float2 suv = s / float2(ar, 1.0) + 0.5;
  float3 prev = tex2D(sampler_main, suv).rgb * (0.84 + 0.05 * q6);
  float2 z = rot2(p, q5 * 0.3) * q10 * (0.9 + 0.15 * q4);
  float2 c = float2(q2, q3) + 0.05 * float2(q11, q12);
  float trap = 9.0;
  for (int i = 0; i < 14; i++)
  {
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    trap = min(trap, abs(z.x * z.y));
  }
  float bolt = exp(-trap * (35.0 + 55.0 * q1));
  float3 em = hue(q9 + 0.12 * time + 0.1 * q8, 1.0) * bolt;
  em *= 0.04 + 0.1 * q1 + 0.03 * q8;
  ret = max(prev + em, 0.0);
  ret = max(ret - 0.003, 0.0);
}
""",
        "comp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 z = rot2(p, q5 + 0.25 * q11) * q10 * (0.88 + 0.2 * q4);
  float2 c = float2(q2, q3) + 0.06 * float2(q12, q13);
  float trap = 9.0;
  float nu = 0.0;
  float esc = 0.0;
  for (int i = 0; i < 26; i++)
  {
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    float d2 = dot(z, z);
    trap = min(trap, min(abs(z.x), abs(z.y)));
    if (d2 > 200.0)
    {
      nu = float(i) + 1.0 - log2(0.5 * log2(max(d2, 1.0)));
      esc = 1.0;
      break;
    }
  }
  float bolt = exp(-trap * (50.0 + 80.0 * q1));
  float branch = exp(-trap * 16.0) * (0.15 + 0.55 * esc);
  float pulse = 0.7 + 0.3 * sin(time * 6.0 + nu + 4.0 * q1);
  float3 plasma = hue(q9 + 0.1 * time + 0.05 * nu * 0.1, 1.0);
  float3 col = plasma * bolt * (1.5 + 2.0 * q1) * pulse;
  col += plasma * branch * 0.65;
  col += float3(0.02, 0.04, 0.1) * (1.0 - bolt);
  float2 river_uv = float2(uv.x + 0.02 * q11, uv.y + 0.18 * sin(uv.x * 12.0 + time * 1.5 + q6));
  col += tex2D(sampler_main, river_uv).rgb * 0.48;
  col += GetBlur1(uv) * plasma * (0.12 + 0.2 * q1);
  ret = led_tonemap(col);
}
""",
    },
    {
        "file": "10-mandelbrot-hyperspace.milk",
        "title": "Mandelbrot hyperspace rush",
        "rush": dict(
            md_zoom=1.045,
            md_zoom_bass=0.04,
            md_zoom_kick=0.08,
            depth_speed=0.55,
            depth_bass=0.45,
            depth_kick=0.9,
        ),
        "pf": dict(
            zoom_base=2.8,
            zoom_bass=0.7,
            zoom_kick=1.1,
            spin=0.08,
            spin_treb=0.2,
            cx=-0.745,
            cy=0.1,
            cx_amp=0.08,
            cy_amp=0.06,
            cx_freq=0.09,
            cy_freq=0.07,
            hue=0.62,
            scale=0.55,
        ),
        "warp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float rush = 0.92 - 0.08 * q1 - 0.04 * q6;
  float2 s = rot2(p, q5 * 0.15) * rush;
  float2 suv = s / float2(ar, 1.0) + 0.5;
  float3 prev = lerp(tex2D(sampler_main, suv).rgb, GetBlur1(suv), 0.18);
  float2 c = float2(q2, q3) + p / (q4 * (1.0 + 0.15 * q14)) * q10;
  float2 z = float2(0.0, 0.0);
  float n = 0.0;
  for (int i = 0; i < 12; i++)
  {
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    n += step(dot(z, z), 16.0);
  }
  float3 em = hue(q9 + 0.04 * n + 0.05 * q14, 0.9) * smoothstep(3.0, 11.0, n);
  em *= 0.03 + 0.04 * q1;
  float streak = exp(-length(p) * 2.5) * (0.02 + 0.05 * q1);
  ret = max(prev * 0.86 + em + hue(q9 + 0.3, 1.0) * streak, 0.0);
}
""",
        "comp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float dive = q4 * (1.0 + 0.2 * frac(q14 * 0.15));
  float2 c = float2(q2, q3) + rot2(p, q5 * 0.25) / dive * q10;
  float2 z = float2(0.0, 0.0);
  float nu = 0.0;
  float esc = 0.0;
  float trap = 9.0;
  for (int i = 0; i < 30; i++)
  {
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    float d2 = dot(z, z);
    trap = min(trap, length(z));
    if (d2 > 256.0)
    {
      nu = float(i) + 1.0 - log2(0.5 * log2(d2));
      esc = 1.0;
      break;
    }
  }
  float bands = frac(nu * 0.18 + q14 * 0.25 + time * 0.05);
  float3 col = hue(q9 + 0.12 * floor(nu * 0.2) + 0.08 * q14, 1.0);
  col *= 0.12 + 0.9 * pow(sin(3.14159 * bands), 1.15);
  col += float3(0.7, 0.85, 1.0) * exp(-trap * 10.0) * 0.55;
  col = lerp(col * 0.25, col, esc);
  float vig = smoothstep(1.4, 0.15, length(p));
  col *= 0.35 + 0.75 * vig;
  float speedlines = abs(frac(atan2(p.y, p.x) * 0.15915 * 18.0 + q14) - 0.5);
  col += hue(q9 + 0.4, 1.0) * exp(-speedlines * 40.0) * exp(-length(p) * 1.2) * (0.2 + 0.5 * q1);
  col += tex2D(sampler_main, uv).rgb * 0.3;
  ret = led_tonemap(col);
}
""",
    },
    {
        "file": "11-julia-warp-rush.milk",
        "title": "Julia warp rush",
        "rush": dict(
            md_zoom=1.055,
            md_zoom_bass=0.05,
            md_zoom_kick=0.1,
            depth_speed=0.7,
            depth_bass=0.5,
            depth_kick=1.1,
        ),
        "pf": dict(
            zoom_base=1.6,
            zoom_bass=0.4,
            zoom_kick=0.7,
            spin=0.22,
            spin_treb=0.4,
            cx=-0.12,
            cy=0.68,
            cx_amp=0.22,
            cy_amp=0.18,
            cx_freq=0.15,
            cy_freq=0.12,
            hue=0.12,
            scale=1.05,
        ),
        "warp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float rush = 0.88 - 0.1 * q1 - 0.05 * q6;
  float2 s = rot2(p, q5 * 0.45) * rush;
  float2 suv = s / float2(ar, 1.0) + 0.5;
  float3 prev = tex2D(sampler_main, suv).rgb;
  prev = lerp(prev, GetBlur1(suv), 0.15);
  float2 z = p * q10 * (1.0 + 0.25 * frac(q14));
  float2 c = float2(q2, q3);
  float m = 9.0;
  float n = 0.0;
  for (int i = 0; i < 14; i++)
  {
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    m = min(m, abs(z.x * z.y));
    n += step(dot(z, z), 64.0);
  }
  float3 em = hue(q9 + 0.05 * sqrt(m) + 0.08 * q14, 0.95) * exp(-m * 16.0);
  em += hue(q9 + 0.5, 1.0) * smoothstep(5.0, 12.0, n) * 0.03;
  em *= 1.0 + 1.2 * q1;
  ret = max(prev * 0.84 + em * 0.05, 0.0);
}
""",
        "comp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 z = rot2(p, q5) * q10 * (1.0 + 0.35 * frac(q14 * 0.5));
  float2 c = float2(q2, q3);
  float nu = 0.0;
  float esc = 0.0;
  float m1 = 9.0;
  float m2 = 9.0;
  for (int i = 0; i < 28; i++)
  {
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    float d2 = dot(z, z);
    m1 = min(m1, abs(z.x));
    m2 = min(m2, abs(z.y));
    if (d2 > 256.0)
    {
      nu = float(i) + 1.0 - log2(0.5 * log2(d2));
      esc = 1.0;
      break;
    }
  }
  float f = frac(nu * 0.3 + q14 * 0.4);
  float3 pane = hue(q9 + 0.1 * floor(nu) + 0.05 * q14, 1.0);
  pane *= 0.15 + 0.85 * pow(sin(3.14159 * f), 1.2);
  pane += float3(1.0, 0.75, 0.4) * exp(-min(f, 1.0 - f) * min(f, 1.0 - f) * 800.0) * 0.5;
  pane += hue(q9 + 0.55, 1.0) * exp(-min(m1, m2) * 35.0) * 0.55;
  float3 col = lerp(pane * 0.3, pane, esc);
  float rr = length(p);
  col *= lerp(0.25, 1.0, smoothstep(1.35, 0.2, rr));
  float spokes = abs(frac(atan2(p.y, p.x) * 0.15915 * 14.0 + q14 * 1.5) - 0.5);
  col += hue(q9 + 0.25, 1.0) * exp(-spokes * 55.0) * exp(-rr * 1.5) * (0.25 + 0.7 * q1);
  col += tex2D(sampler_main, uv).rgb * 0.35;
  ret = led_tonemap(col);
}
""",
    },
    {
        "file": "12-burning-ship-dive.milk",
        "title": "Burning ship dive",
        "rush": dict(
            md_zoom=1.04,
            md_zoom_bass=0.035,
            md_zoom_kick=0.07,
            depth_speed=0.48,
            depth_bass=0.4,
            depth_kick=0.85,
        ),
        "pf": dict(
            zoom_base=2.0,
            zoom_bass=0.5,
            zoom_kick=0.85,
            spin=-0.06,
            spin_treb=0.12,
            cx=-1.76,
            cy=-0.04,
            cx_amp=0.06,
            cy_amp=0.04,
            cx_freq=0.08,
            cy_freq=0.06,
            hue=0.04,
            scale=0.4,
        ),
        "warp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float rush = 0.93 - 0.07 * q1;
  float2 s = p * rush;
  float2 suv = s / float2(ar, 1.0) + 0.5;
  float3 prev = lerp(tex2D(sampler_main, suv).rgb, GetBlur1(suv), 0.2);
  float2 z = float2(0.0, 0.0);
  float2 c = float2(q2, q3) + p * q10 * q4 * (1.0 + 0.2 * frac(q14));
  float n = 0.0;
  for (int i = 0; i < 11; i++)
  {
    z = float2(abs(z.x), abs(z.y));
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    n += step(dot(z, z), 64.0);
  }
  float3 em = hue(q9 + 0.06 * n + 0.04 * q14, 0.95) * smoothstep(2.0, 10.0, n) * 0.035;
  em += float3(1.0, 0.4, 0.1) * q1 * 0.03;
  ret = max(prev * 0.87 + em, 0.0);
}
""",
        "comp": COMMON_FUNCS
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 z = float2(0.0, 0.0);
  float2 c = float2(q2, q3) + rot2(p, q5 * 0.2) * q10 * q4 * (1.0 + 0.25 * frac(q14 * 0.7));
  float nu = 0.0;
  float esc = 0.0;
  float trap = 9.0;
  for (int i = 0; i < 26; i++)
  {
    z = float2(abs(z.x), abs(z.y));
    z = float2(z.x*z.x - z.y*z.y, 2.0*z.x*z.y) + c;
    float d2 = dot(z, z);
    trap = min(trap, abs(z.y));
    if (d2 > 256.0)
    {
      nu = float(i) + 1.0 - log2(0.5 * log2(d2));
      esc = 1.0;
      break;
    }
  }
  float3 fire = hue(q9 + 0.04 * nu + 0.08 * q14 + 0.08 * q7, 1.0);
  fire *= 0.2 + 0.9 * smoothstep(0.0, 18.0, nu);
  fire += float3(1.0, 0.5, 0.12) * exp(-trap * 22.0);
  float3 col = lerp(fire * 0.22, fire, esc);
  float rr = length(p);
  col *= lerp(0.3, 1.0, smoothstep(1.3, 0.18, rr));
  float tunnel = abs(frac(rr * (5.0 + 3.0 * q6) - q14 * 2.0) - 0.5);
  col += float3(1.0, 0.7, 0.3) * exp(-tunnel * 35.0) * (0.2 + 0.5 * q1);
  col += tex2D(sampler_main, uv).rgb * 0.28;
  ret = led_tonemap(col);
}
""",
    },
]


def write_preset(spec: dict) -> Path:
    path = ROOT / spec["file"]
    body = HEADER + PER_FRAME.format(**spec["pf"])
    if "rush" in spec:
        body += RUSH_PER_FRAME.format(**spec["rush"])
    body += lines("warp", spec["warp"]) + lines("comp", spec["comp"])
    path.write_text(body, encoding="utf-8")
    return path


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for spec in PRESETS:
        path = write_preset(spec)
        print(f"wrote {path.relative_to(ROOT.parent.parent)} ({spec['title']})")


if __name__ == "__main__":
    main()
