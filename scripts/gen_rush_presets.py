#!/usr/bin/env python3
"""Generate GPL MilkDrop 2 forward-rush presets from historic waveform overlays.

MilkDrop mechanism (same as classic zoom trails):
  1. Warp copies the previous frame from a point slightly closer to the origin
     (screen centre, or a horizon line). No blur — history stays sharp.
  2. Custom waves paint a fresh high-contrast spectrum / waveform stroke.
  3. Those strokes accumulate as parallel overlays that slowly migrate from the
     origin toward the edges, forming a screen-spanning texture (terrain ridges,
     cloud bands, polar tunnels).

Comp only colour-grades and hardens contrast. It does not redraw geometry and
does not sample GetBlur*. Prefer 128×128+. No MilkDrop 3 get_fft().
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "presets" / "rush"


def lines(prefix: str, body: str) -> str:
    out = []
    n = 0
    for raw in body.strip().splitlines():
        if not raw.strip():
            continue
        n += 1
        out.append(f"{prefix}_{n}=`{raw}")
    return "\n".join(out) + "\n"


# q1=kick q2=bass q3=mid q4=treb q5=ang q6=depth
# q11=hue q13=gain q16=pull (radial) q15=scroll (horizon ridge spacing)
COMMON = """\
float3 hue(float h, float s)
{
  float3 k = abs(frac(h + float3(0.0, 0.66667, 0.33333))*6.0 - 3.0) - 1.0;
  return (1.0 - s) + s*saturate(k);
}
float3 sharp(float2 tc)
{
  return tex2D(sampler_main, saturate(tc)).rgb;
}
float lum3(float3 c)
{
  return dot(c, float3(0.30, 0.59, 0.11));
}
float3 boost_chroma(float3 c, float amt)
{
  float L = lum3(c);
  return saturate(L + (c - L) * amt);
}
float3 led_tonemap(float3 col)
{
  float lum = max(lum3(col), 0.0001);
  float mapped = 1.0 - exp(-lum * 1.1);
  mapped = min(mapped, 0.92);
  return saturate((col / lum) * mapped * q13);
}
"""

HEADER = """\
[preset00]
MILKDROP_PRESET_VERSION=201
PSVERSION=2
PSVERSION_WARP=2
PSVERSION_COMP=2
fRating=5.000000
fGammaAdj=1.400000
fDecay={decay:.6f}
fVideoEchoZoom=1.000000
fVideoEchoAlpha=0.000000
nVideoEchoOrientation=0
nWaveMode=0
bAdditiveWaves=0
bWaveDots=0
bWaveThick=1
bModWaveAlphaByVolume=0
bMaximizeWaveColor=0
bTexWrap=0
bDarkenCenter=0
bRedBlueStereo=0
bBrighten=0
bDarken=0
bSolarize=0
bInvert=0
fWaveAlpha=0.000000
fWaveScale=1.000000
fWaveSmoothing=0.150000
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
wavecode_0_bAdditive=0
wavecode_0_scaling=1.600000
wavecode_0_smoothing=0.120000
wavecode_0_r=0.500000
wavecode_0_g=0.700000
wavecode_0_b=1.000000
wavecode_0_a=1.000000
wavecode_1_enabled=1
wavecode_1_samples=512
wavecode_1_sep=0
wavecode_1_bSpectrum=1
wavecode_1_bUseDots=0
wavecode_1_bDrawThick=1
wavecode_1_bAdditive=0
wavecode_1_scaling=1.350000
wavecode_1_smoothing=0.140000
wavecode_1_r=1.000000
wavecode_1_g=0.500000
wavecode_1_b=0.300000
wavecode_1_a=0.950000
wavecode_2_enabled=1
wavecode_2_samples=512
wavecode_2_sep=0
wavecode_2_bSpectrum=0
wavecode_2_bUseDots=0
wavecode_2_bDrawThick=1
wavecode_2_bAdditive=0
wavecode_2_scaling=1.200000
wavecode_2_smoothing=0.150000
wavecode_2_r=0.300000
wavecode_2_g=1.000000
wavecode_2_b=0.600000
wavecode_2_a=0.900000
wavecode_3_enabled=1
wavecode_3_samples=512
wavecode_3_sep=0
wavecode_3_bSpectrum=1
wavecode_3_bUseDots=0
wavecode_3_bDrawThick=1
wavecode_3_bAdditive=0
wavecode_3_scaling=1.100000
wavecode_3_smoothing=0.160000
wavecode_3_r=0.900000
wavecode_3_g=0.400000
wavecode_3_b=1.000000
wavecode_3_a=0.850000
{wave_points}
"""

# Spectrum bin (sample) drives hue along each stroke so history carries colour variety.
WAVE_POINTS_POLAR = """\
wave_0_per_point1=x = 0.5 + (0.04 + 0.24 * value + 0.08 * bass_att) * cos(sample * 6.2832);
wave_0_per_point2=y = 0.5 + (0.04 + 0.24 * value + 0.08 * bass_att) * sin(sample * 6.2832);
wave_0_per_point3=r = 0.15 + 0.95 * bass_att + 0.7 * sample;
wave_0_per_point4=g = 0.15 + 0.95 * mid_att + 0.45 * value;
wave_0_per_point5=b = 0.2 + 0.95 * treb_att + 0.55 * (1 - sample);
wave_0_per_point6=a = 0.75 + 0.25 * value;
wave_1_per_point1=x = 0.5 + (0.02 + 0.15 * value + 0.05 * mid_att) * cos(sample * 6.2832 + time * 0.4);
wave_1_per_point2=y = 0.5 + (0.02 + 0.15 * value + 0.05 * mid_att) * sin(sample * 6.2832 + time * 0.4);
wave_1_per_point3=r = 0.9 + 0.1 * bass - 0.5 * sample;
wave_1_per_point4=g = 0.25 + 0.75 * mid_att + 0.4 * sample;
wave_1_per_point5=b = 0.3 + 0.7 * treb_att;
wave_1_per_point6=a = 0.7 + 0.3 * value;
wave_2_per_point1=x = 0.5 + (0.07 + 0.3 * value) * cos(sample * 6.2832 - time * 0.3);
wave_2_per_point2=y = 0.5 + (0.07 + 0.3 * value) * sin(sample * 6.2832 - time * 0.3) * (0.85 + 0.15 * value);
wave_2_per_point3=r = 0.2 + 0.6 * treb_att + 0.5 * (1 - sample);
wave_2_per_point4=g = 0.35 + 0.65 * mid_att + 0.35 * sample;
wave_2_per_point5=b = 0.5 + 0.5 * bass_att + 0.4 * sample;
wave_2_per_point6=a = 0.7 + 0.3 * value;
wave_3_per_point1=x = 0.5 + (0.01 + 0.11 * value) * cos(sample * 12.5664);
wave_3_per_point2=y = 0.5 + (0.01 + 0.11 * value) * sin(sample * 12.5664);
wave_3_per_point3=r = 0.55 + 0.45 * sample;
wave_3_per_point4=g = 0.3 + 0.5 * mid + 0.3 * (1 - sample);
wave_3_per_point5=b = 0.8 + 0.2 * treb;
wave_3_per_point6=a = 0.65 + 0.35 * value;
"""

WAVE_POINTS_STAR = """\
wave_0_per_point1=x = 0.5 + (0.03 + 0.22 * value + 0.07 * bass_att) * cos(sample * 6.2832);
wave_0_per_point2=y = 0.5 + (0.03 + 0.22 * value + 0.07 * bass_att) * sin(sample * 6.2832) * (0.65 + 0.35 * value);
wave_0_per_point3=r = 0.2 + 0.9 * bass_att + 0.65 * sample;
wave_0_per_point4=g = 0.15 + 0.85 * mid_att + 0.4 * value;
wave_0_per_point5=b = 0.25 + 0.85 * treb_att + 0.5 * (1 - sample);
wave_0_per_point6=a = 0.8 + 0.2 * value;
wave_1_per_point1=x = 0.5 + (0.05 + 0.26 * value) * cos(sample * 12.5664 + time * 0.5);
wave_1_per_point2=y = 0.5 + (0.05 + 0.26 * value) * sin(sample * 12.5664 + time * 0.5);
wave_1_per_point3=r = 1.0 - 0.55 * sample;
wave_1_per_point4=g = 0.35 + 0.55 * mid_att;
wave_1_per_point5=b = 0.4 + 0.6 * sample;
wave_1_per_point6=a = 0.7 + 0.3 * value;
wave_2_per_point1=x = 0.5 + (0.015 + 0.13 * value) * cos(sample * 6.2832 - time);
wave_2_per_point2=y = 0.5 + (0.015 + 0.13 * value) * sin(sample * 6.2832 - time);
wave_2_per_point3=r = 0.25 + 0.75 * treb_att;
wave_2_per_point4=g = 0.55 + 0.45 * sample;
wave_2_per_point5=b = 0.7 + 0.3 * bass_att;
wave_2_per_point6=a = 0.75 + 0.25 * value;
wave_3_per_point1=x = 0.5 + (0.09 + 0.22 * value) * cos(sample * 18.8496);
wave_3_per_point2=y = 0.5 + (0.09 + 0.22 * value) * sin(sample * 18.8496);
wave_3_per_point3=r = 0.7 + 0.3 * (1 - sample);
wave_3_per_point4=g = 0.35 + 0.5 * mid;
wave_3_per_point5=b = 0.55 + 0.45 * sample;
wave_3_per_point6=a = 0.65 + 0.35 * value;
"""

WAVE_POINTS_LAND = """\
wave_0_per_point1=x = sample * 0.98 + 0.01;
wave_0_per_point2=y = 0.48 + value * 0.42 + 0.1 * bass_att;
wave_0_per_point3=r = 0.2 + 0.95 * bass_att + 0.65 * sample;
wave_0_per_point4=g = 0.25 + 0.85 * mid_att + 0.35 * value;
wave_0_per_point5=b = 0.15 + 0.7 * treb_att + 0.4 * (1 - sample);
wave_0_per_point6=a = 0.9 + 0.1 * value;
wave_1_per_point1=x = sample * 0.98 + 0.01;
wave_1_per_point2=y = 0.5 + value * 0.3 + 0.04 * sin(sample * 22);
wave_1_per_point3=r = 0.55 + 0.45 * bass + 0.3 * sample;
wave_1_per_point4=g = 0.35 + 0.65 * mid;
wave_1_per_point5=b = 0.2 + 0.4 * treb + 0.35 * (1 - sample);
wave_1_per_point6=a = 0.85 + 0.15 * value;
wave_2_per_point1=x = sample * 0.98 + 0.01;
wave_2_per_point2=y = 0.45 + value * 0.2;
wave_2_per_point3=r = 0.15 + 0.55 * treb_att + 0.5 * (1 - sample);
wave_2_per_point4=g = 0.45 + 0.55 * mid_att;
wave_2_per_point5=b = 0.55 + 0.45 * bass_att + 0.35 * sample;
wave_2_per_point6=a = 0.8 + 0.2 * value;
wave_3_per_point1=x = sample * 0.98 + 0.01;
wave_3_per_point2=y = 0.53 + value * 0.24 * (0.55 + 0.45 * bass_att);
wave_3_per_point3=r = 0.7 + 0.3 * sample;
wave_3_per_point4=g = 0.4 + 0.5 * mid_att;
wave_3_per_point5=b = 0.25 + 0.5 * (1 - sample);
wave_3_per_point6=a = 0.82 + 0.18 * value;
"""

WAVE_POINTS_CANYON = """\
wave_0_per_point1=x = 0.22 + value * 0.24 + 0.05 * bass_att;
wave_0_per_point2=y = sample * 0.98 + 0.01;
wave_0_per_point3=r = 0.55 + 0.45 * bass_att + 0.4 * sample;
wave_0_per_point4=g = 0.25 + 0.45 * mid_att;
wave_0_per_point5=b = 0.1 + 0.35 * treb_att + 0.3 * (1 - sample);
wave_0_per_point6=a = 0.92;
wave_1_per_point1=x = 0.78 - value * 0.24 - 0.05 * bass_att;
wave_1_per_point2=y = sample * 0.98 + 0.01;
wave_1_per_point3=r = 0.45 + 0.4 * mid_att + 0.35 * (1 - sample);
wave_1_per_point4=g = 0.3 + 0.4 * bass;
wave_1_per_point5=b = 0.15 + 0.45 * treb + 0.35 * sample;
wave_1_per_point6=a = 0.92;
wave_2_per_point1=x = sample * 0.98 + 0.01;
wave_2_per_point2=y = 0.7 + value * 0.22;
wave_2_per_point3=r = 0.15 + 0.55 * treb_att + 0.4 * sample;
wave_2_per_point4=g = 0.4 + 0.55 * mid_att;
wave_2_per_point5=b = 0.65 + 0.35 * bass_att;
wave_2_per_point6=a = 0.88;
wave_3_per_point1=x = 0.2 + value * 0.14;
wave_3_per_point2=y = sample * 0.98 + 0.01;
wave_3_per_point3=r = 0.7 + 0.3 * sample;
wave_3_per_point4=g = 0.4 + 0.4 * mid;
wave_3_per_point5=b = 0.25 + 0.4 * (1 - sample);
wave_3_per_point6=a = 0.85;
"""

WAVE_POINTS_CLOUD = """\
wave_0_per_point1=x = sample * 0.98 + 0.01;
wave_0_per_point2=y = 0.42 + value * 0.32 + 0.03 * sin(sample * 16);
wave_0_per_point3=r = 0.45 + 0.4 * bass_att + 0.45 * sample;
wave_0_per_point4=g = 0.55 + 0.35 * mid_att + 0.25 * value;
wave_0_per_point5=b = 0.75 + 0.25 * treb_att + 0.2 * (1 - sample);
wave_0_per_point6=a = 0.88;
wave_1_per_point1=x = sample * 0.98 + 0.01;
wave_1_per_point2=y = 0.5 + value * 0.24;
wave_1_per_point3=r = 0.7 + 0.3 * treb_att - 0.25 * sample;
wave_1_per_point4=g = 0.65 + 0.3 * mid_att;
wave_1_per_point5=b = 0.9 + 0.1 * bass;
wave_1_per_point6=a = 0.84;
wave_2_per_point1=x = sample * 0.98 + 0.01;
wave_2_per_point2=y = 0.35 + value * 0.2;
wave_2_per_point3=r = 0.35 + 0.45 * bass_att + 0.4 * (1 - sample);
wave_2_per_point4=g = 0.5 + 0.45 * mid_att;
wave_2_per_point5=b = 0.85 + 0.15 * sample;
wave_2_per_point6=a = 0.8;
wave_3_per_point1=x = sample * 0.98 + 0.01;
wave_3_per_point2=y = 0.58 + value * 0.18;
wave_3_per_point3=r = 0.6 + 0.35 * sample;
wave_3_per_point4=g = 0.55 + 0.4 * mid;
wave_3_per_point5=b = 0.95;
wave_3_per_point6=a = 0.78;
"""

PER_FRAME = """\
per_frame_1=dt = min(max(time - tl, 0.004), 0.08); tl = time;
per_frame_2=bm = bm + (bass - bm) * (1 - exp(-dt / 0.5));
per_frame_3=bd = bd + (abs(bass - bm) - bd) * (1 - exp(-dt / 1.6));
per_frame_4=hit = min(max(((bass - bm) / max(bd, 0.06) - 0.55) / 1.2, 0), 1);
per_frame_5=kick = max(kick * pow(0.88, 60 * dt), hit * 0.65);
per_frame_6=k60 = pow(0.9, 60 * dt);
per_frame_7=sb = sb * k60 + bass_att * (1 - k60);
per_frame_8=sm = sm * k60 + mid_att * (1 - k60);
per_frame_9=st = st * k60 + treb_att * (1 - k60);
per_frame_10=ang = ang + dt * ({spin:.4f} + {spin_treb:.4f} * st);
per_frame_11=depth = depth + dt * ({depth:.4f} + {depth_bass:.4f} * sb);
per_frame_12=pull = {pull:.4f} - {pull_bass:.4f} * sb - {pull_kick:.4f} * kick;
per_frame_13=scroll = {scroll:.4f} + {scroll_bass:.4f} * sb + {scroll_kick:.4f} * kick;
per_frame_14=hue_shift = {hue:.4f} + 0.06 * time + 0.1 * st - 0.04 * sb; hue_shift = hue_shift - int(hue_shift);
per_frame_15=wave_r = min(0.7 + 0.3 * sb, 1);
per_frame_16=wave_g = min(0.65 + 0.35 * sm, 1);
per_frame_17=wave_b = min(0.6 + 0.4 * st, 1);
per_frame_18=q1 = kick; q2 = sb; q3 = sm; q4 = st; q5 = ang; q6 = depth;
per_frame_19=q11 = hue_shift; q13 = 1.0 + 0.12 * (sb + sm + st) * 0.25;
per_frame_20=q15 = scroll; q16 = pull;
"""

# Classic MilkDrop zoom-trail warp: sample toward origin, no blur.
WARP_RADIAL = COMMON + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  float pull = saturate(q16);
  float2 s = p * pull;
  float2 suv = s / float2(ar, 1.0) + 0.5;
  float3 hist = sharp(suv);
  float keep = 0.985 - 0.01 * q1;
  ret = max(hist * keep - 0.0015, 0.0);
}
"""

# Horizon origin: scroll history away from the paint line so each waveform
# remains a distinct ridge (classic MilkDrop dy trail), with mild lateral expand.
WARP_HORIZON = COMMON + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float hy = 0.48;
  float sc = max(q15, 0.004);
  float2 suv = uv;
  if (uv.y >= hy)
  {
    suv.y = uv.y - sc;
  }
  else
  {
    suv.y = uv.y + sc;
  }
  suv.x = 0.5 + (uv.x - 0.5) * saturate(q16);
  float3 hist = sharp(suv);
  float keep = 0.978 - 0.015 * q1;
  ret = max(hist * keep - 0.002, 0.0);
}
"""

# Canyon: scroll history outward from the vertical centre line.
WARP_CANYON = COMMON + """
shader_body
{
  float ar = texsize.x * texsize.w;
  float sc = max(q15, 0.004);
  float2 suv = uv;
  if (uv.x >= 0.5)
  {
    suv.x = uv.x - sc;
  }
  else
  {
    suv.x = uv.x + sc;
  }
  suv.y = 0.5 + (uv.y - 0.5) * saturate(q16);
  float3 hist = sharp(suv);
  float keep = 0.978 - 0.015 * q1;
  ret = max(hist * keep - 0.002, 0.0);
}
"""

# Preserve painted spectrum chroma; harden edges without flattening to one hue.
COMP_TRAIL = COMMON + """
shader_body
{
  float2 px = texsize.zw;
  float3 c = sharp(uv);
  float3 cx = sharp(uv + float2(px.x, 0.0));
  float3 cy = sharp(uv + float2(0.0, px.y));
  float L = lum3(c);
  float Lx = lum3(cx);
  float Ly = lum3(cy);
  float edge = saturate(abs(L - Lx) * 11.0 + abs(L - Ly) * 9.0);
  float peak = saturate((L - 0.05) * 2.2);
  float3 vivid = boost_chroma(c, 2.2 + 0.6 * q4);
  float3 col = vivid * (0.55 + 0.9 * peak);
  col += vivid * edge * 0.85;
  col += hue(q11 + L * 0.3 + uv.x * 0.2, 1.0) * pow(peak, 3.0) * 0.25 * q1;
  float ar = texsize.x * texsize.w;
  float2 p = (uv - 0.5) * float2(ar, 1.0);
  ret = led_tonemap(col * smoothstep(1.35, 0.12, length(p)));
}
"""

COMP_MOUNTAIN = COMMON + """
shader_body
{
  float2 px = texsize.zw;
  float3 c = sharp(uv);
  float3 cx = sharp(uv + float2(px.x, 0.0));
  float3 cy = sharp(uv + float2(0.0, px.y));
  float L = saturate(lum3(c) * 1.7);
  float Lx = saturate(lum3(cx) * 1.7);
  float Ly = saturate(lum3(cy) * 1.7);
  float edge = saturate(abs(L - Lx) * 12.0 + abs(L - Ly) * 9.0);
  float peak = smoothstep(0.04, 0.35, L);
  float hi = smoothstep(0.3, 0.8, L);
  float slope = saturate(0.4 + (L - Lx) * 6.0);
  float3 vivid = boost_chroma(c, 2.0);
  float3 sky = float3(0.15, 0.28, 0.55) * (0.5 + 0.5 * q4);
  sky += hue(q11 + 0.55, 0.7) * L * 0.2 * q3;
  float3 valley = float3(0.04, 0.1, 0.03);
  float3 forest = float3(0.08, 0.24, 0.07);
  float3 rock = float3(0.38, 0.28, 0.18);
  float3 snow = float3(0.9, 0.92, 0.96);
  float3 ground = lerp(valley, forest, saturate(peak * 1.3));
  ground = lerp(ground, rock, saturate(peak * 1.5 - 0.15));
  ground = lerp(ground, snow, hi);
  ground *= slope;
  ground = lerp(ground, vivid, saturate(peak * 0.85 + edge * 0.4));
  ground += vivid * edge * 0.7;
  ground += snow * edge * hi * 0.45;
  float land = max(smoothstep(0.18, 0.5, uv.y), peak);
  float3 col = lerp(sky, ground, land);
  ret = led_tonemap(col);
}
"""

COMP_CLOUD = COMMON + """
shader_body
{
  float2 px = texsize.zw;
  float3 c = sharp(uv);
  float3 cx = sharp(uv + float2(px.x, 0.0));
  float3 cy = sharp(uv + float2(0.0, px.y));
  float L = saturate(lum3(c) * 1.85);
  float Lx = saturate(lum3(cx) * 1.85);
  float Ly = saturate(lum3(cy) * 1.85);
  float edge = saturate(abs(L - Lx) * 13.0 + abs(L - Ly) * 10.0);
  float body = smoothstep(0.06, 0.28, L);
  float core = smoothstep(0.3, 0.7, L);
  float3 vivid = boost_chroma(c, 2.1);
  float3 sky = float3(0.08, 0.14, 0.34) * (0.55 + 0.45 * q4);
  float3 shade = float3(0.35, 0.42, 0.58);
  float lit = saturate(0.35 + (L - Lx) * 6.0);
  float3 mass = lerp(shade, vivid, 0.65);
  mass = lerp(mass, float3(0.92, 0.95, 1.0), lit * 0.45);
  float3 col = sky;
  col = lerp(col, mass, body);
  col = lerp(col, vivid * 1.1, core * 0.75);
  col += vivid * edge * 0.8;
  ret = led_tonemap(col);
}
"""

COMP_CANYON = COMMON + """
shader_body
{
  float2 px = texsize.zw;
  float3 c = sharp(uv);
  float3 cx = sharp(uv + float2(px.x, 0.0));
  float3 cy = sharp(uv + float2(0.0, px.y));
  float L = saturate(lum3(c) * 1.75);
  float Lx = saturate(lum3(cx) * 1.75);
  float Ly = saturate(lum3(cy) * 1.75);
  float edge = saturate(abs(L - Lx) * 12.0 + abs(L - Ly) * 9.0);
  float strata = saturate(abs(L - Ly) * 10.0);
  float peak = smoothstep(0.04, 0.35, L);
  float wall = smoothstep(0.08, 0.38, abs(uv.x - 0.5) * 2.0);
  wall = max(wall, peak * 0.75);
  float3 vivid = boost_chroma(c, 2.0);
  float3 rock = float3(0.48, 0.3, 0.16);
  rock = lerp(rock, float3(0.62, 0.4, 0.22), strata);
  rock = lerp(rock, vivid, 0.55);
  float3 floorc = float3(0.08, 0.18, 0.32);
  floorc = lerp(floorc, vivid, peak * 0.55);
  float3 col = lerp(floorc, rock * (0.5 + 0.7 * peak), wall);
  col += vivid * edge * 0.75;
  col += c * 0.25;
  ret = led_tonemap(col);
}
"""


def pf(**kwargs):
    defaults = dict(
        spin=0.02,
        spin_treb=0.06,
        depth=0.5,
        depth_bass=0.3,
        pull=0.982,
        pull_bass=0.006,
        pull_kick=0.01,
        scroll=0.010,
        scroll_bass=0.004,
        scroll_kick=0.006,
        hue=0.55,
    )
    defaults.update(kwargs)
    return defaults


PRESETS = [
    {
        "file": "01-spectrum-ring-tunnel.milk",
        "title": "Spectrum ring tunnel rush",
        "decay": 0.99,
        "wave_points": WAVE_POINTS_POLAR,
        "pf": pf(hue=0.55, pull=0.98),
        "warp": WARP_RADIAL,
        "comp": COMP_TRAIL,
    },
    {
        "file": "02-waveform-star-rush.milk",
        "title": "Waveform starfield rush",
        "decay": 0.985,
        "wave_points": WAVE_POINTS_STAR,
        "pf": pf(spin=0.04, hue=0.08, pull=0.984),
        "warp": WARP_RADIAL,
        "comp": COMP_TRAIL,
    },
    {
        "file": "03-hex-grid-tunnel.milk",
        "title": "Lattice waveform trail rush",
        "decay": 0.988,
        "wave_points": WAVE_POINTS_POLAR,
        "pf": pf(spin=0.015, hue=0.72, pull=0.983),
        "warp": WARP_RADIAL,
        "comp": COMP_TRAIL,
    },
    {
        "file": "04-diamond-pulse-rush.milk",
        "title": "Diamond pulse trail rush",
        "decay": 0.986,
        "wave_points": WAVE_POINTS_STAR,
        "pf": pf(spin=0.03, hue=0.92, pull=0.981),
        "warp": WARP_RADIAL,
        "comp": COMP_TRAIL,
    },
    {
        "file": "05-radial-spoke-rush.milk",
        "title": "Radial waveform rush",
        "decay": 0.984,
        "wave_points": WAVE_POINTS_STAR,
        "pf": pf(spin=0.05, spin_treb=0.12, hue=0.35, pull=0.979),
        "warp": WARP_RADIAL,
        "comp": COMP_TRAIL,
    },
    {
        "file": "06-triangle-chevron-rush.milk",
        "title": "Chevron waveform rush",
        "decay": 0.986,
        "wave_points": WAVE_POINTS_POLAR,
        "pf": pf(spin=0.035, hue=0.18, pull=0.981),
        "warp": WARP_RADIAL,
        "comp": COMP_TRAIL,
    },
    {
        "file": "07-square-grid-tunnel.milk",
        "title": "Boxed waveform trail rush",
        "decay": 0.988,
        "wave_points": WAVE_POINTS_POLAR,
        "pf": pf(spin=0.012, hue=0.48, pull=0.983),
        "warp": WARP_RADIAL,
        "comp": COMP_TRAIL,
    },
    {
        "file": "08-waveform-petal-rush.milk",
        "title": "Waveform petal rush",
        "decay": 0.985,
        "wave_points": WAVE_POINTS_STAR,
        "pf": pf(spin=0.045, spin_treb=0.1, hue=0.85, pull=0.98),
        "warp": WARP_RADIAL,
        "comp": COMP_TRAIL,
    },
    {
        "file": "09-flyover-terrain.milk",
        "title": "Mountain flyover rush",
        "decay": 0.99,
        "wave_points": WAVE_POINTS_LAND,
        "pf": pf(
            spin=0.0,
            spin_treb=0.0,
            hue=0.28,
            pull=0.992,
            pull_bass=0.002,
            pull_kick=0.004,
            scroll=0.011,
            scroll_bass=0.005,
            scroll_kick=0.007,
            depth=0.8,
            depth_bass=0.5,
        ),
        "warp": WARP_HORIZON,
        "comp": COMP_MOUNTAIN,
    },
    {
        "file": "10-under-cloud-canopy.milk",
        "title": "Cloud canopy rush",
        "decay": 0.985,
        "wave_points": WAVE_POINTS_CLOUD,
        "pf": pf(
            spin=0.01,
            hue=0.62,
            pull=0.993,
            pull_bass=0.002,
            pull_kick=0.003,
            scroll=0.012,
            scroll_bass=0.004,
            scroll_kick=0.006,
        ),
        "warp": WARP_HORIZON,
        "comp": COMP_CLOUD,
    },
    {
        "file": "11-canyon-flythrough.milk",
        "title": "Canyon flythrough rush",
        "decay": 0.986,
        "wave_points": WAVE_POINTS_CANYON,
        "pf": pf(
            spin=0.0,
            hue=0.08,
            pull=0.992,
            pull_bass=0.002,
            pull_kick=0.004,
            scroll=0.011,
            scroll_bass=0.005,
            scroll_kick=0.007,
            depth=0.9,
            depth_bass=0.55,
        ),
        "warp": WARP_CANYON,
        "comp": COMP_CANYON,
    },
    {
        "file": "12-cloud-street-dive.milk",
        "title": "Cloud street dive rush",
        "decay": 0.984,
        "wave_points": WAVE_POINTS_CLOUD,
        "pf": pf(
            spin=0.015,
            hue=0.58,
            pull=0.993,
            pull_bass=0.002,
            pull_kick=0.003,
            scroll=0.013,
            scroll_bass=0.004,
            scroll_kick=0.006,
        ),
        "warp": WARP_HORIZON,
        "comp": COMP_CLOUD,
    },
]


def write_preset(spec: dict) -> Path:
    path = ROOT / spec["file"]
    body = (
        HEADER.format(decay=spec["decay"], wave_points=spec["wave_points"])
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
