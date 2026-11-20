#!/usr/bin/env python3
"""Generate GPL MilkDrop 2 presets: waveform → texture → fake-3D surfaces.

Colour is driven by audio characteristics (not a fixed palette):
  - bass / bass_att  → warm red–orange weight
  - mid / mid_att    → green–yellow weight
  - treb / treb_att  → cyan–magenta weight
  - kick             → white flash + saturation boost
  - spectrum bin (sample) → hue along the strip
  - overall energy   → brightness / exposure

No MilkDrop 3 get_fft(). Prefer 128×128+ LED matrices.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "presets" / "surfaces"


def lines(prefix: str, body: str) -> str:
    out = []
    n = 0
    for raw in body.strip().splitlines():
        if not raw.strip():
            continue  # blank HLSL lines break MilkDrop preset load
        n += 1
        out.append(f"{prefix}_{n}=`{raw}")
    return "\n".join(out) + "\n"


# Shared HLSL helpers. q1=kick q2=bass q3=mid q4=treb q11=hue_shift q12=sat q13=gain
COMMON = """\
float2 rot2(float2 p, float a)
{
  float c = cos(a); float s = sin(a);
  return float2(c*p.x - s*p.y, s*p.x + c*p.y);
}
float3 hue(float h, float sat)
{
  float3 k = abs(frac(h + float3(0.0, 0.66667, 0.33333))*6.0 - 3.0) - 1.0;
  return (1.0 - sat) + sat*saturate(k);
}
float3 wave_tex(float2 tc)
{
  float2 u = frac(tc);
  float3 a = tex2D(sampler_main, u).rgb;
  float3 b = GetBlur1(u);
  float3 c = GetBlur2(u);
  return a * 0.50 + b * 0.30 + c * 0.20;
}
float3 audio_tint(float u_coord)
{
  float h = frac(q11 + u_coord * 0.55 + 0.08 * q4 - 0.05 * q2);
  float sat = saturate(0.70 + 0.25 * q12 + 0.15 * q1);
  float3 band = hue(h, sat);
  float3 warm = float3(1.0, 0.35, 0.08) * q2;
  float3 midc = float3(0.25, 1.0, 0.35) * q3;
  float3 cool = float3(0.25, 0.55, 1.0) * q4;
  return saturate(band * 0.85 + warm * 0.45 + midc * 0.40 + cool * 0.45);
}
float3 colourise(float3 tex, float u_coord, float shade)
{
  float lum = dot(tex, float3(0.30, 0.59, 0.11));
  float3 tint = audio_tint(u_coord);
  float3 col = tint * (0.42 + 1.05 * lum) * shade;
  col += tint * lum * lum * 0.40;
  col += float3(1.0, 0.95, 0.9) * pow(lum, 4.0) * q1 * 0.55;
  col *= q13;
  return col;
}
float3 led_tonemap(float3 col)
{
  float lum = max(dot(col, float3(0.30, 0.59, 0.11)), 0.0001);
  float mapped = 1.0 - exp(-lum * 1.05);
  mapped = min(mapped, 0.88);
  return saturate((col / lum) * mapped);
}
"""

HEADER = """\
[preset00]
MILKDROP_PRESET_VERSION=201
PSVERSION=2
PSVERSION_WARP=2
PSVERSION_COMP=2
fRating=4.500000
fGammaAdj=1.700000
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
fWaveSmoothing=0.650000
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
wave_g=0.700000
wave_b=1.000000
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
wavecode_0_enabled=1
wavecode_0_samples=512
wavecode_0_sep=0
wavecode_0_bSpectrum=1
wavecode_0_bUseDots=0
wavecode_0_bDrawThick=1
wavecode_0_bAdditive=1
wavecode_0_scaling=1.200000
wavecode_0_smoothing=0.450000
wavecode_0_r=1.000000
wavecode_0_g=1.000000
wavecode_0_b=1.000000
wavecode_0_a=1.000000
wavecode_1_enabled=1
wavecode_1_samples=512
wavecode_1_sep=0
wavecode_1_bSpectrum=0
wavecode_1_bUseDots=0
wavecode_1_bDrawThick=1
wavecode_1_bAdditive=1
wavecode_1_scaling=1.000000
wavecode_1_smoothing=0.550000
wavecode_1_r=1.000000
wavecode_1_g=1.000000
wavecode_1_b=1.000000
wavecode_1_a=1.000000
wavecode_2_enabled=1
wavecode_2_samples=512
wavecode_2_sep=0
wavecode_2_bSpectrum=1
wavecode_2_bUseDots=0
wavecode_2_bDrawThick=1
wavecode_2_bAdditive=1
wavecode_2_scaling=0.900000
wavecode_2_smoothing=0.500000
wavecode_2_r=1.000000
wavecode_2_g=1.000000
wavecode_2_b=1.000000
wavecode_2_a=0.900000
wavecode_3_enabled=0
"""

# Per-point colours follow audio bands + spectrum position (sample).
WAVE_POINTS = """\
wave_0_per_point1=x = sample * 0.96 + 0.02;
wave_0_per_point2=y = 0.06 + value * 0.55;
wave_0_per_point3=r = 0.15 + 0.95 * bass_att + 0.55 * sample;
wave_0_per_point4=g = 0.15 + 0.95 * mid_att + 0.35 * value;
wave_0_per_point5=b = 0.20 + 0.95 * treb_att + 0.40 * (1 - sample);
wave_0_per_point6=a = 0.65 + 0.35 * value;
wave_1_per_point1=x = sample * 0.96 + 0.02;
wave_1_per_point2=y = 0.94 - value * 0.40;
wave_1_per_point3=r = 0.70 + 0.30 * bass;
wave_1_per_point4=g = 0.25 + 0.55 * mid + 0.20 * value;
wave_1_per_point5=b = 0.15 + 0.70 * treb;
wave_1_per_point6=a = 0.50 + 0.50 * value;
wave_2_per_point1=x = 0.50 + 0.48 * cos(sample * 6.2832);
wave_2_per_point2=y = 0.50 + 0.48 * sin(sample * 6.2832) * (0.35 + 0.65 * value);
wave_2_per_point3=r = 0.20 + 0.80 * treb_att + 0.40 * sample;
wave_2_per_point4=g = 0.20 + 0.70 * mid_att;
wave_2_per_point5=b = 0.35 + 0.65 * bass_att + 0.35 * (1 - sample);
wave_2_per_point6=a = 0.40 + 0.55 * value;
"""

PER_FRAME = """\
per_frame_1=dt = min(max(time - tl, 0.004), 0.08); tl = time;
per_frame_2=bm = bm + (bass - bm) * (1 - exp(-dt / 0.55));
per_frame_3=bd = bd + (abs(bass - bm) - bd) * (1 - exp(-dt / 1.8));
per_frame_4=hit = min(max(((bass - bm) / max(bd, 0.07) - 0.55) / 1.2, 0), 1);
per_frame_5=kick = max(kick * pow(0.84, 60 * dt), hit);
per_frame_6=k60 = pow(0.93, 60 * dt);
per_frame_7=sb = sb * k60 + bass_att * (1 - k60);
per_frame_8=sm = sm * k60 + mid_att * (1 - k60);
per_frame_9=st = st * k60 + treb_att * (1 - k60);
per_frame_10=ang = ang + dt * ({spin:.4f} + {spin_treb:.4f} * st + 0.08 * kick);
per_frame_11=scroll = scroll + dt * ({scroll:.4f} + {scroll_bass:.4f} * sb + 0.15 * st);
per_frame_12=energy = min(sb + sm + st, 2.5);
per_frame_13=hue_shift = {hue:.4f} + 0.08 * time + 0.12 * st - 0.07 * sb + 0.05 * sm; hue_shift = hue_shift - int(hue_shift);
per_frame_14=sat_lvl = min(0.55 + 0.30 * energy + 0.15 * kick, 1.1);
per_frame_15=gain = 0.95 + 0.28 * energy;
per_frame_16=wave_r = min(0.25 + 0.90 * sb + 0.35 * kick, 1);
per_frame_17=wave_g = min(0.20 + 0.85 * sm + 0.25 * st, 1);
per_frame_18=wave_b = min(0.30 + 0.90 * st + 0.20 * sm, 1);
per_frame_19=q1 = kick; q2 = sb; q3 = sm; q4 = st; q5 = ang;
per_frame_20=q6 = scroll; q7 = {hue:.4f}; q8 = {radius:.4f}; q9 = {cam_z:.4f}; q10 = {amp:.4f};
per_frame_21=q11 = hue_shift; q12 = sat_lvl; q13 = gain;
"""

WARP_SCROLL = COMMON + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float2 suv = uv + float2(-0.0055 - 0.004 * q2 - 0.002 * q4, 0.002 * sin(q6 * 4.0 + uv.y * 9.0));
  float3 prev = tex2D(sampler_main, suv).rgb;
  prev = lerp(prev, GetBlur1(suv), 0.12);
  float2 breathe = p * (0.003 + 0.01 * q1 + 0.004 * q3);
  float3 ink = tex2D(sampler_main, uv + breathe / float2(ar, 1.0)).rgb;
  ret = max(prev * (0.90 + 0.03 * q2), ink * (1.0 + 0.18 * q1));
  ret = max(ret - 0.0012, 0.0);
}
"""


def shade_tail() -> str:
    return """
  ret = led_tonemap(col);
}
"""


PRESETS = [
    {
        "file": "01-convex-sphere-skin.milk",
        "title": "Convex sphere with audio-coloured waveform skin",
        "decay": 0.975,
        "wave_mode": 5,
        "wave_alpha": 0.55,
        "wave_scale": 1.15,
        "pf": dict(spin=0.18, spin_treb=0.28, scroll=0.18, scroll_bass=0.25, hue=0.55, radius=0.40, cam_z=2.0, amp=0.35),
        "warp": WARP_SCROLL,
        "comp": COMMON
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float ca = cos(q5); float sa = sin(q5);
  float2 pr = float2(ca * p.x - sa * p.y, sa * p.x + ca * p.y);
  float sph_r = q8 * (1.35 + 0.18 * q1 + 0.12 * q2);
  float rr = length(pr);
  float3 col = audio_tint(uv.x) * 0.03;
  if (rr < sph_r)
  {
    float z = sqrt(max(sph_r * sph_r - rr * rr, 0.0));
    float3 n = normalize(float3(pr.x, pr.y, z));
    float2 tuv = float2(atan2(n.y, n.x) * 0.1591549 + 0.5 + q6 * 0.12, n.z * 0.5 + 0.5);
    float3 tex = wave_tex(tuv * float2(2.4, 1.5) + float2(q6 * 0.4, q4 * 0.1));
    float ndl = saturate(dot(n, normalize(float3(0.35, 0.55, 0.75))));
    float fres = pow(1.0 - saturate(n.z), 2.0);
    float shade = 0.55 + 0.90 * ndl;
    col = colourise(tex, tuv.x, shade);
    col += audio_tint(tuv.x + 0.2) * fres * (0.30 + 0.25 * q4);
    col += float3(1.0, 0.92, 0.80) * fres * fres * q1 * 0.40;
  }
  else
  {
    float sky = exp(-rr * 1.1);
    col += audio_tint(uv.x + q6) * sky * (0.05 + 0.08 * q3);
  }
"""
        + shade_tail(),
    },
    {
        "file": "02-concave-bowl.milk",
        "title": "Concave bowl - audio-coloured inner waveform skin",
        "decay": 0.978,
        "wave_mode": 6,
        "wave_alpha": 0.45,
        "wave_scale": 1.0,
        "pf": dict(spin=-0.12, spin_treb=0.2, scroll=0.15, scroll_bass=0.28, hue=0.08, radius=0.80, cam_z=0.32, amp=0.60),
        "warp": WARP_SCROLL,
        "comp": COMMON
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float3 ro = float3(0.12 * sin(q5), 0.52 + 0.10 * q2, q9);
  float3 rd = normalize(float3(p.x, -0.85, p.y * 0.9 - 0.2));
  float ca = cos(q5 * 0.35); float sa = sin(q5 * 0.35);
  rd = float3(ca * rd.x - sa * rd.z, rd.y, sa * rd.x + ca * rd.z);
  float3 col = audio_tint(uv.x) * 0.035;
  float t = 0.0;
  float hit = 0.0;
  float3 pos = float3(0.0, 0.0, 0.0);
  for (int i = 0; i < 32; i++)
  {
    pos = ro + rd * t;
    float r2 = pos.x * pos.x + pos.z * pos.z;
    float dish = pos.y - (r2 * q8 - q10 - 0.18 * q1);
    float wall = 0.95 - length(pos.xz);
    float d = max(dish, -wall);
    if (abs(d) < 0.003) { hit = 1.0; break; }
    t += clamp(abs(d), 0.008, 0.12);
    if (t > 5.0) break;
  }
  if (hit > 0.5)
  {
    float3 n = normalize(float3(-2.0 * q8 * pos.x, 1.0, -2.0 * q8 * pos.z));
    if (dot(n, -rd) < 0.0) n = -n;
    float u_ang = atan2(pos.z, pos.x) * 0.1591549 + 0.5 + q6 * 0.12;
    float v_rad = saturate(length(pos.xz) * 0.9 + 0.05 * q3);
    float2 tuv = float2(u_ang, v_rad);
    float3 tex = wave_tex(tuv * float2(2.2, 1.5) + float2(0.0, q6 * 0.2));
    float ndl = saturate(dot(n, normalize(float3(0.2, 0.9, 0.3))));
    float rim = pow(1.0 - saturate(dot(n, -rd)), 2.3);
    col = colourise(tex, u_ang, 0.35 + 0.8 * ndl);
    col += audio_tint(u_ang + 0.33) * rim * (0.30 + 0.22 * q4);
    col += float3(1.0, 0.75, 0.35) * exp(-length(pos.xz) * 2.5) * (0.08 + 0.35 * q1);
  }
  else
  {
    col += colourise(wave_tex(float2(uv.x + q6 * 0.25, 0.12)), uv.x, 0.55) * 0.08;
  }
"""
        + shade_tail(),
    },
    {
        "file": "03-waveform-hills.milk",
        "title": "Landscape - audio-coloured waveform drape",
        "decay": 0.972,
        "wave_mode": 3,
        "wave_alpha": 0.50,
        "wave_scale": 1.2,
        "pf": dict(spin=0.05, spin_treb=0.08, scroll=0.25, scroll_bass=0.40, hue=0.30, radius=0.55, cam_z=0.95, amp=0.75),
        "warp": COMMON
        + """
shader_body
{
  float2 suv = uv + float2(-0.007 - 0.005 * q2 - 0.002 * q4, 0.001 * sin(time * 0.8 + uv.x * 10.0));
  float3 prev = tex2D(sampler_main, suv).rgb;
  prev = lerp(prev, GetBlur1(suv), 0.15);
  float3 ink = tex2D(sampler_main, uv).rgb;
  ret = max(prev * (0.93 + 0.04 * q2), ink * (1.05 + 0.4 * q1));
  ret = max(ret - 0.0004, 0.0);
}
""",
        "comp": COMMON
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float3 ro = float3(0.0, 0.40 + 0.14 * q2, q9);
  float3 rd = normalize(float3(p.x, p.y * 0.65 - 0.18, -1.05));
  float ca = cos(q5); float sa = sin(q5);
  rd.xz = float2(ca * rd.x - sa * rd.z, sa * rd.x + ca * rd.z);
  float3 col = audio_tint(uv.x + q6) * 0.05;
  float t = 0.0;
  float hit = 0.0;
  float3 pos = float3(0.0, 0.0, 0.0);
  for (int i = 0; i < 36; i++)
  {
    pos = ro + rd * t;
    float2 xz = pos.xz + float2(q6 * 1.5, q6 * 0.4);
    float h = 0.28 * sin(xz.x * 1.7 + q6) * cos(xz.y * 1.3);
    h += 0.14 * sin(xz.x * 3.7 - xz.y * 2.1 + q3 * 2.0);
    h += 0.07 * sin(xz.x * 7.1 + xz.y * 5.3 + q4);
    h *= q10 * (0.65 + 0.55 * q2 + 0.45 * q1);
    float d = pos.y - h;
    if (d < 0.004) { hit = 1.0; break; }
    t += clamp(d, 0.01, 0.16);
    if (t > 7.0) break;
  }
  if (hit > 0.5)
  {
    float2 xz = pos.xz + float2(q6 * 1.5, q6 * 0.4);
    float e = 0.05;
    float h0 = 0.28 * sin(xz.x * 1.7 + q6) * cos(xz.y * 1.3)
             + 0.14 * sin(xz.x * 3.7 - xz.y * 2.1 + q3 * 2.0)
             + 0.07 * sin(xz.x * 7.1 + xz.y * 5.3 + q4);
    float hx = 0.28 * sin((xz.x + e) * 1.7 + q6) * cos(xz.y * 1.3)
             + 0.14 * sin((xz.x + e) * 3.7 - xz.y * 2.1 + q3 * 2.0)
             + 0.07 * sin((xz.x + e) * 7.1 + xz.y * 5.3 + q4);
    float hz = 0.28 * sin(xz.x * 1.7 + q6) * cos((xz.y + e) * 1.3)
             + 0.14 * sin(xz.x * 3.7 - (xz.y + e) * 2.1 + q3 * 2.0)
             + 0.07 * sin(xz.x * 7.1 + (xz.y + e) * 5.3 + q4);
    float mul = q10 * (0.65 + 0.55 * q2 + 0.45 * q1);
    h0 *= mul; hx *= mul; hz *= mul;
    float3 n = normalize(float3(h0 - hx, e, h0 - hz));
    float2 tuv = frac(xz * 0.20 + float2(q6 * 0.30, q6 * 0.06));
    float3 tex = wave_tex(tuv);
    float ndl = saturate(dot(n, normalize(float3(0.3, 0.85, 0.35))));
    float fog = saturate(t / 6.0);
    col = colourise(tex, tuv.x, 0.30 + 0.95 * ndl);
    col = lerp(col, audio_tint(tuv.x + 0.5) * 0.2, fog * 0.65);
    col += float3(1.0, 0.88, 0.55) * pow(ndl, 6.0) * q1 * 0.45;
  }
  else
  {
    float sky = exp(-max(p.y, 0.0) * 1.1) * (0.06 + 0.10 * q3);
    col += audio_tint(uv.x + 0.25) * sky;
    col += colourise(wave_tex(float2(uv.x * 0.5 + q6, 0.08)), uv.x, 0.7) * 0.06;
  }
"""
        + shade_tail(),
    },
    {
        "file": "04-convex-torus-wrap.milk",
        "title": "Convex torus - audio-coloured waveform wrap",
        "decay": 0.976,
        "wave_mode": 7,
        "wave_alpha": 0.50,
        "wave_scale": 1.05,
        "pf": dict(spin=0.24, spin_treb=0.32, scroll=0.20, scroll_bass=0.25, hue=0.72, radius=0.27, cam_z=2.1, amp=0.4),
        "warp": WARP_SCROLL,
        "comp": COMMON
        + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float ca = cos(q5); float sa = sin(q5);
  float2 pr = float2(ca * p.x - sa * p.y, sa * p.x + ca * p.y);
  float major_r = 0.42 + 0.06 * q2;
  float tube_r = q8 * (1.05 + 0.2 * q1 + 0.1 * q3);
  float ring = abs(length(pr) - major_r);
  float3 col = audio_tint(uv.x) * 0.03;
  if (ring < tube_r)
  {
    float u = atan2(pr.y, pr.x) * 0.1591549 + 0.5;
    float v = (ring / max(tube_r, 0.001)) * 0.5 + 0.5;
    float2 tuv = float2(u * 2.2 + q6 * 0.35, v * 1.5 + q6 * 0.12);
    float3 tex = wave_tex(tuv);
    float ndl = 0.55 + 0.45 * (1.0 - ring / max(tube_r, 0.001));
    float fres = pow(ring / max(tube_r, 0.001), 2.0);
    col = colourise(tex, u, 0.55 + 0.85 * ndl);
    col += audio_tint(u + 0.4) * fres * (0.25 + 0.25 * q4);
    col += float3(1.0, 0.9, 0.8) * (1.0 - fres) * q1 * 0.35;
  }
  else
  {
    col += colourise(wave_tex(uv * 0.45 + float2(q6, 0.0)), uv.x, 0.6) * 0.06;
  }
"""
        + shade_tail(),
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
