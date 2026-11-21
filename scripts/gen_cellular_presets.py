#!/usr/bin/env python3
"""Generate GPL MilkDrop 2 cellular / metallic presets.

1. Voronoi metaball mercury puddles — uneven liquid-metal lobes; each site
   drifts and beat-pops on its own seed while warp also zooms the frame.
2. Vanishing-point petri dish — log-polar tunnel, diplococcus coral cells,
   concentric rings, yellow core → olive → black, rotating spiral.
3. Heat-temper puddles — same mercury pools with marching purple/green/blue
   neon temper colours and a music-driven perimeter key light on the meniscus.

MilkDrop 2 only (no get_fft). Prefer 128×128+ LED matrices.
Do not redeclare MilkDrop builtins (rad, ang, …).
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "presets" / "cellular"


def lines(prefix: str, body: str) -> str:
    out = []
    n = 0
    for raw in body.strip().splitlines():
        if not raw.strip():
            continue  # blank HLSL lines break MilkDrop preset load
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
float2 hash22(float2 p)
{
  float n = sin(dot(p, float2(127.1, 311.7))) * 43758.5453;
  return frac(float2(n, n * 1.215433));
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
  for (int i = 0; i < 4; i++)
  {
    a += w * noise2(p);
    p = p * 2.07 + float2(17.0, 9.0);
    w *= 0.5;
  }
  return a;
}
float3 led_tonemap(float3 col)
{
  float lum = max(dot(col, float3(0.30, 0.59, 0.11)), 0.0001);
  float mapped = 1.0 - exp(-lum * 0.95);
  mapped = min(mapped, 0.82);
  float3 outc = (col / lum) * mapped * q13;
  outc += col * pow(mapped, 2.5) * q1 * 0.12;
  return saturate(outc);
}
float3 studio_env(float3 R)
{
  float u = R.y;
  float3 sky = lerp(float3(0.55, 0.42, 0.22), float3(0.18, 0.16, 0.28), saturate(0.3 + u * 0.55));
  float3 gnd = lerp(float3(0.02, 0.015, 0.01), float3(0.12, 0.08, 0.05), saturate(0.25 - u * 0.5));
  float3 env = lerp(gnd, sky, smoothstep(-0.2, 0.18, u));
  float box1 = pow(saturate(sin(R.x * 3.2 + R.z * 1.1 + q9 * 0.35)), 14.0);
  float box2 = pow(saturate(sin(R.x * -2.0 + R.y * 3.5 - q9 * 0.2)), 20.0);
  env += float3(0.85, 0.55, 0.18) * box1 * 0.55;
  env += float3(0.35, 0.55, 0.45) * box2 * 0.4;
  env += float3(0.4, 0.25, 0.55) * pow(saturate(-R.x * 0.45 + 0.15), 3.5) * 0.2;
  return env;
}
float3 heat_temper(float u)
{
  float t = frac(u);
  float3 purple = float3(0.75, 0.12, 0.95);
  float3 green = float3(0.08, 0.95, 0.35);
  float3 blue = float3(0.15, 0.45, 1.0);
  float3 c = lerp(purple, green, smoothstep(0.0, 0.38, t));
  c = lerp(c, blue, smoothstep(0.32, 0.72, t));
  c = lerp(c, purple, smoothstep(0.68, 1.0, t));
  return c;
}
float3 mercury_light(float3 Nor, float3 tint, float ht, float mask, float fres_amt)
{
  float3 V = float3(0.0, 0.0, 1.0);
  float3 R = float3(2.0 * Nor.z * Nor.x, 2.0 * Nor.z * Nor.y, 2.0 * Nor.z * Nor.z - 1.0);
  float3 env = studio_env(normalize(R + float3(0.0, 0.06, 0.0)));
  float ndv = saturate(dot(Nor, V));
  float fres = pow(1.0 - ndv, 2.2) * fres_amt;
  float3 valley = tint * 0.1;
  float3 crestc = tint * 1.35;
  float3 shade = lerp(valley, crestc, pow(saturate(ht), 1.15));
  float3 metal = shade * (0.5 + 0.75 * env);
  metal += env * fres * tint * 0.95;
  float3 L1 = normalize(float3(cos(q14) * 0.95, sin(q14) * 0.95, 0.38 + 0.22 * q15));
  float3 L2 = normalize(float3(cos(q14 + 2.3) * 0.55, sin(q14 + 2.3) * 0.55, 0.6));
  float shin = 36.0 + 100.0 * q11;
  float sp = pow(saturate(dot(R, L1)), shin) * 1.15 + pow(saturate(dot(R, L2)), shin * 0.55) * 0.5;
  metal += tint * 1.25 * sp;
  float edge = pow(1.0 - ndv, 1.5);
  metal += tint * edge * (0.55 + 0.6 * ht);
  float ndl = saturate(dot(Nor, L1) * 0.55 + 0.45);
  metal *= 0.5 + 0.5 * ndl;
  return metal * mask;
}
"""

# Shared metaball field → gfill / meniscus / Nor. Colour applied by preset body.
# q1=kick q2=bass q3=mid q4=treb q5=ang q6=grow q7=density q8=warp
# q9=scroll q10=site jitter q11=spec q12=flow q13=gain q14=light_ang q15=light_z
VORONOI_FIELD = """\
  float2 p = (uv - 0.5) * aspect.xy;
  p = rot2(p, q5 * 0.06);
  float2 warp = float2(
    fbm2(p * 2.4 + float2(q9 * 0.4, time * 0.05)),
    fbm2(p * 2.4 + float2(9.2, q9 * 0.3 - time * 0.04)));
  p += (warp - 0.5) * (0.28 + 0.22 * q8);
  p += float2(q12, -q12 * 0.7) * 0.04;
  float2 x = p * q7 + float2(q9 * 0.12, -q9 * 0.18);
  float2 n = floor(x);
  float2 f = frac(x);
  float field = 0.0;
  float field_x = 0.0;
  float field_y = 0.0;
  float2 cid = float2(0.0, 0.0);
  float best = 0.0;
  float2 eps = float2(0.035, 0.0);
  for (int j = -1; j <= 1; j++)
  {
    for (int i = -1; i <= 1; i++)
    {
      float2 g = float2(i, j);
      float2 id = n + g;
      float2 o = hash22(id);
      float seed = hash11(dot(id, float2(12.9898, 78.233)));
      float phase = seed * 6.2831853;
      float swell = 0.5 + 0.5 * sin(time * (1.1 + 2.8 * seed) + phase + q3 * 0.8);
      float beat_pop = smoothstep(seed - 0.05, seed + 0.2, q1) * q1;
      float local_g = saturate(
        q6 * (0.2 + 0.8 * seed) * (0.45 + 0.55 * swell)
        + beat_pop * (0.55 + 0.45 * seed)
        + q2 * (0.12 + 0.2 * (1.0 - seed)));
      float2 drift = float2(
        sin(time * (0.55 + 1.4 * seed) + phase),
        cos(time * (0.4 + 1.1 * seed) + phase * 1.3));
      drift += float2(
        sin(time * (1.8 + seed) + phase * 2.0 + q1 * 2.5),
        cos(time * (1.5 + 0.7 * seed) + q2 * 1.8)) * (0.35 + 0.65 * q1);
      o = 0.5 + 0.38 * sin(6.2831853 * o + float2(time * q10 * (0.35 + seed), time * q10 * 0.5 + phase));
      o += drift * (0.12 + 0.1 * q10 + 0.08 * local_g);
      float2 r = g + o - f;
      float d2 = dot(r, r);
      float sharp = 3.2 + 10.0 * (1.05 - local_g);
      float blob = local_g * exp(-d2 * sharp);
      field += blob;
      float2 rx = g + o - (f + eps.xy);
      float2 ry = g + o - (f + eps.yx);
      field_x += local_g * exp(-dot(rx, rx) * sharp);
      field_y += local_g * exp(-dot(ry, ry) * sharp);
      if (blob > best)
      {
        best = blob;
        cid = id;
      }
    }
  }
  float cell_var = hash11(dot(cid, float2(19.19, 47.47)));
  float rip1 = fbm2(p * 6.5 + float2(time * 0.11, cell_var));
  float rip2 = fbm2(p * 14.0 - float2(time * 0.19, cell_var * 3.0));
  float rip = (rip1 - 0.5) * 0.55 + (rip2 - 0.5) * 0.3;
  field += rip * 0.14 * saturate(field);
  float thresh = 0.42;
  float gfill = smoothstep(thresh - 0.08, thresh + 0.12 + 0.1 * q6, field);
  float meniscus = smoothstep(0.12, 0.5, gfill) * (1.0 - smoothstep(0.5, 0.98, gfill));
  float ht = saturate(gfill * 0.7 + meniscus * 0.7 + rip * 0.45 * gfill);
  float dhx = (field_x - field) / eps.x;
  float dhy = (field_y - field) / eps.x;
  dhx += (noise2(p * 13.0 + float2(time * 0.2, 1.3)) - 0.5) * 1.8;
  dhy += (noise2(p * 13.0 + float2(4.7, -time * 0.17)) - 0.5) * 1.8;
  dhx += (rip1 - rip2) * 1.2;
  float relief = 2.8 + 2.4 * ht + 0.9 * q11;
  float3 Nor = normalize(float3(-dhx * relief, -dhy * relief, 0.14 + 0.22 * ht + 0.05 * q1));
  float ridge = saturate(1.0 - abs(field - thresh) * 3.5);
"""

def voronoi_palette_body(
    hi: tuple[float, float, float],
    lo: tuple[float, float, float],
    charcoal: tuple[float, float, float] = (0.015, 0.012, 0.01),
    rim: tuple[float, float, float] | None = None,
) -> str:
    """Crest (hi) and valley (lo) metal F0 colours for a puddle preset.

    Optional rim: thin directional meniscus colour (≈1–2px at LED scale).
    """
    if rim is None:
        rim_block = """
  col += hi_f0 * pow(meniscus, 1.15) * gfill * (0.55 + 0.4 * q4);
"""
    else:
        rim_block = f"""
  float3 rim_hue = float3({rim[0]:.3f}, {rim[1]:.3f}, {rim[2]:.3f});
  float edge = smoothstep(0.2, 0.4, gfill) * (1.0 - smoothstep(0.4, 0.58, gfill));
  edge = pow(saturate(edge), 1.85);
  float3 Lrim = normalize(float3(cos(q14), sin(q14), 0.3 + 0.24 * q15));
  float lit_edge = pow(saturate(dot(Nor, Lrim)), 2.0);
  float grazing = pow(1.0 - saturate(Nor.z), 1.65);
  float rim = edge * lit_edge * (0.45 + 0.55 * grazing);
  float3 Rrim = reflect(-Lrim, Nor);
  float rim_spec = pow(saturate(dot(Rrim, float3(0.0, 0.0, 1.0))), 12.0 + 28.0 * q11) * edge * lit_edge;
  col += rim_hue * rim * gfill * (3.4 + 1.1 * q4 + 0.5 * q1);
  col += rim_hue * rim_spec * gfill * (2.1 + 0.85 * q11);
"""
    return (
        VORONOI_FIELD
        + f"""
  float3 charcoal = float3({charcoal[0]:.3f}, {charcoal[1]:.3f}, {charcoal[2]:.3f});
  float3 hi_f0 = float3({hi[0]:.3f}, {hi[1]:.3f}, {hi[2]:.3f});
  float3 lo_f0 = float3({lo[0]:.3f}, {lo[1]:.3f}, {lo[2]:.3f});
  float3 tint = lerp(lo_f0, hi_f0, saturate(ht * 0.85 + 0.15 * cell_var));
  float3 lit = mercury_light(Nor, tint, ht, gfill, 1.1);
  float3 col = lerp(charcoal, lit, gfill);
"""
        + rim_block
        + """
  col += lo_f0 * (1.0 - ht) * gfill * 0.25;
  col += hi_f0 * gfill * q1 * 0.1;
"""
    )


# Named palettes for 01–03.
PALETTE_YELLOW_GOLD = dict(hi=(0.95, 0.62, 0.18), lo=(0.70, 0.32, 0.08))
PALETTE_GREEN_GOLD = dict(
    hi=(0.72, 0.88, 0.28),
    lo=(0.18, 0.48, 0.14),
    charcoal=(0.012, 0.018, 0.012),
    rim=(0.0, 0.95, 0.55),
)
# 03: deep purple metal F0; sky-blue is a separate key light (not mixed into tint).
PALETTE_PURPLE_SKY = dict(
    metal=(0.55, 0.12, 0.85),
    metal_lo=(0.28, 0.05, 0.48),
    sky=(0.35, 0.78, 1.0),
    charcoal=(0.008, 0.005, 0.016),
)

# Purple body stays purple; sky-blue only on speculars + meniscus catch.
PURPLE_SKY_BODY = (
    VORONOI_FIELD
    + f"""
  float3 charcoal = float3({PALETTE_PURPLE_SKY['charcoal'][0]:.3f}, {PALETTE_PURPLE_SKY['charcoal'][1]:.3f}, {PALETTE_PURPLE_SKY['charcoal'][2]:.3f});
  float3 metal_hi = float3({PALETTE_PURPLE_SKY['metal'][0]:.3f}, {PALETTE_PURPLE_SKY['metal'][1]:.3f}, {PALETTE_PURPLE_SKY['metal'][2]:.3f});
  float3 metal_lo = float3({PALETTE_PURPLE_SKY['metal_lo'][0]:.3f}, {PALETTE_PURPLE_SKY['metal_lo'][1]:.3f}, {PALETTE_PURPLE_SKY['metal_lo'][2]:.3f});
  float3 sky = float3({PALETTE_PURPLE_SKY['sky'][0]:.3f}, {PALETTE_PURPLE_SKY['sky'][1]:.3f}, {PALETTE_PURPLE_SKY['sky'][2]:.3f});
  float3 tint = lerp(metal_lo, metal_hi, saturate(ht * 0.75 + 0.18 * cell_var));
  float3 lit = mercury_light(Nor, tint, ht, gfill, 0.85);
  lit *= float3(1.05, 0.72, 1.15);
  float3 Vdir = float3(0.0, 0.0, 1.0);
  float3 R = normalize(float3(2.0 * Nor.z * Nor.x, 2.0 * Nor.z * Nor.y, 2.0 * Nor.z * Nor.z - 1.0));
  float3 Lkey = normalize(float3(cos(q14) * 0.95, sin(q14) * 0.95, 0.35 + 0.3 * q15));
  float3 Lfill = normalize(float3(cos(q14 + 2.5) * 0.45, sin(q14 + 2.5) * 0.45, 0.75));
  float shin = 28.0 + 90.0 * q11;
  float sp = pow(saturate(dot(R, Lkey)), shin) * 1.5;
  sp += pow(saturate(dot(R, Lfill)), shin * 0.4) * 0.45;
  float men_pow = pow(saturate(meniscus), 0.55);
  float crest_catch = pow(saturate(ht), 1.4) * pow(saturate(dot(Nor, Lkey)), 2.0);
  float3 col = lerp(charcoal, lit, gfill);
  col += metal_lo * (1.0 - ht) * gfill * 0.45;
  col += metal_hi * gfill * 0.18;
  col += sky * sp * gfill * (1.4 + 0.7 * q11);
  col += sky * men_pow * gfill * (1.1 + 0.7 * q4 + 0.4 * q1);
  col += sky * crest_catch * gfill * 0.55;
  col += sky * gfill * q1 * 0.08;
"""
)

# Heat-temper neon march across mercury puddles + orbiting perimeter key light.
HEAT_VORONOI_BODY = (
    VORONOI_FIELD
    + """
  float3 charcoal = float3(0.012, 0.01, 0.02);
  float3 base_metal = float3(0.55, 0.5, 0.48);
  float heat_u = p.x * 0.55 + p.y * 0.4 + q9 * 1.35 + rip * 0.7 + cell_var * 0.45 + q2 * 0.25;
  float3 temper = heat_temper(heat_u);
  float temper_w = 0.35 + 0.45 * ht + 0.25 * q3 + 0.2 * q1;
  float3 tint = lerp(base_metal, temper, saturate(temper_w));
  float3 lit = mercury_light(Nor, tint, ht, gfill, 1.25);
  float3 col = lerp(charcoal, lit, gfill);
  float3 Lorb = normalize(float3(cos(q14), sin(q14), 0.28 + 0.22 * q15));
  float3 Vdir = float3(0.0, 0.0, 1.0);
  float3 Rorb = reflect(-Lorb, Nor);
  float men_pow = pow(saturate(meniscus), 0.65);
  float tension = pow(saturate(dot(Rorb, Vdir)), 18.0 + 40.0 * q11) * men_pow;
  float rim_catch = pow(saturate(dot(Nor, Lorb)), 2.2) * men_pow;
  float grazing = pow(1.0 - saturate(abs(dot(Nor, Lorb))), 2.5) * men_pow;
  float edge_fres = pow(1.0 - saturate(Nor.z), 1.5) * men_pow;
  float3 rim_col = lerp(temper, float3(0.85, 0.9, 1.0), 0.25);
  col += rim_col * tension * (1.6 + 0.9 * q4 + 0.6 * q1);
  col += temper * rim_catch * (1.2 + 0.6 * q15);
  col += temper * grazing * 0.9;
  col += tint * edge_fres * (0.75 + 0.45 * ht);
  col += temper * gfill * q1 * 0.15;
  col += base_metal * (1.0 - ht) * gfill * 0.1;
"""
)

# Vanishing-point petri dish: log-polar tunnel, diplococcus cells, concentric
# rings, yellow→olive→black falloff, coral metallic blobs, rotating spiral.
RADIAL_METAL_BODY = """\
  float2 foc = float2(-0.07, 0.03);
  float2 p = (uv - 0.5) * aspect.xy - foc;
  p = rot2(p, q5 * 0.12 + time * 0.045);
  float rr = length(p) + 0.0001;
  float an = atan2(p.y, p.x);
  float spiral = an + 0.42 * log(rr * 5.0 + 0.25) + time * 0.07 + q5 * 0.08;
  float lr = log(rr * 4.2 + 0.18);
  float2 w = float2(
    fbm2(float2(lr * 1.6, spiral * 0.55) + float2(q9 * 0.2, time * 0.03)),
    fbm2(float2(lr * 1.6, spiral * 0.55) + float2(5.5, -q9 * 0.15)));
  float2 pq = float2(lr, spiral);
  pq += (w - 0.5) * (0.08 + 0.06 * q8);
  float dens_r = 3.2 + 0.65 * q6 + 0.3 * q2;
  float dens_a = max(q7, 8.0) * 0.7;
  float2 x = float2(pq.x * dens_r + q9 * 0.08, pq.y * dens_a + q12 * 0.15);
  float2 n = floor(x);
  float2 f = frac(x);
  float near = saturate(1.0 - rr * 1.25);
  float field = 0.0;
  float field_x = 0.0;
  float field_y = 0.0;
  float2 cid = float2(0.0, 0.0);
  float best = 0.0;
  float2 eps = float2(0.04, 0.0);
  for (int j = -1; j <= 1; j++)
  {
    for (int i = -1; i <= 1; i++)
    {
      float2 g = float2(i, j);
      float2 id = n + g;
      float2 o = hash22(id);
      float seed = hash11(dot(id, float2(12.9898, 78.233)));
      float phase = seed * 6.2831853;
      float swell = 0.5 + 0.5 * sin(time * (0.9 + 2.2 * seed) + phase + q3 * 0.6);
      float beat_pop = smoothstep(seed - 0.05, seed + 0.2, q1) * q1;
      float local_g = saturate(
        q6 * (0.18 + 0.55 * seed) * (0.35 + 0.65 * swell)
        + beat_pop * (0.45 + 0.4 * seed)
        + q2 * (0.08 + 0.12 * (1.0 - seed)));
      local_g *= 0.55 + 0.55 * near;
      float2 drift = float2(
        sin(time * (0.45 + 1.1 * seed) + phase),
        cos(time * (0.35 + 0.9 * seed) + phase * 1.2)) * (0.08 + 0.08 * q10);
      o = 0.5 + 0.34 * sin(6.2831853 * o + float2(time * q10 * 0.3, phase));
      o += drift;
      float twin = 0.16 + 0.1 * seed;
      float2 r0 = g + o - f;
      float2 r1 = g + o + float2(0.0, twin) - f;
      float2 r2 = g + o - float2(0.0, twin) - f;
      float sharp = 4.0 + 9.0 * (1.05 - local_g);
      float b0 = local_g * exp(-dot(r0, r0) * sharp * 1.15);
      float b1 = local_g * 0.92 * exp(-dot(r1, r1) * sharp);
      float b2 = local_g * 0.92 * exp(-dot(r2, r2) * sharp);
      float blob = max(b0, max(b1, b2));
      field += b0 + b1 + b2;
      float2 rx0 = g + o - (f + eps.xy);
      float2 ry0 = g + o - (f + eps.yx);
      field_x += local_g * exp(-dot(rx0, rx0) * sharp * 1.15);
      field_y += local_g * exp(-dot(ry0, ry0) * sharp * 1.15);
      if (blob > best) { best = blob; cid = id; }
    }
  }
  float cell_var = hash11(dot(cid, float2(19.19, 47.47)));
  float rip1 = fbm2(float2(lr * 3.5, spiral * 1.2) + float2(time * 0.08, cell_var));
  float rip2 = fbm2(float2(lr * 7.0, spiral * 2.4) - float2(time * 0.12, cell_var * 2.0));
  float caustic = fbm2(float2(lr * 2.2 + spiral * 0.3, spiral * 0.8 - lr) + time * 0.04);
  field += (rip1 - 0.5) * 0.1 * saturate(field);
  float thresh = 0.5 - 0.05 * near;
  float gfill = smoothstep(thresh - 0.08, thresh + 0.1 + 0.08 * q6, field);
  gfill *= smoothstep(1.05, 0.12, rr);
  float meniscus = smoothstep(0.22, 0.4, gfill) * (1.0 - smoothstep(0.4, 0.58, gfill));
  float ht = saturate(gfill * 0.85 + meniscus * 0.15 + (rip1 - 0.5) * 0.25 * gfill);
  float dhx = (field_x - field) / eps.x;
  float dhy = (field_y - field) / eps.x;
  dhx += (rip1 - rip2) * 1.1 + (caustic - 0.5) * 0.8;
  dhy += (noise2(float2(lr * 8.0, spiral * 3.0) + time * 0.1) - 0.5) * 1.5;
  float relief = 2.5 + 2.2 * ht + 0.9 * q11;
  float3 Nor = normalize(float3(-dhx * relief, -dhy * relief, 0.15 + 0.2 * ht));
  float rings = abs(frac(lr * 9.0 + time * 0.035 + q9 * 0.04) - 0.5);
  float ring_line = 1.0 - smoothstep(0.0, 0.028 + 0.015 * rr, rings);
  float spokes = abs(frac(spiral * max(q7, 8.0) / 6.2831853) - 0.5);
  float spoke_line = 1.0 - smoothstep(0.0, 0.035, spokes);
  float spore = step(0.94, hash11(floor(lr * 32.0) + floor(spiral * 22.0) * 13.0));
  float3 ink = float3(0.004, 0.006, 0.003);
  float3 core_y = float3(1.0, 0.9, 0.3);
  float3 mid_g = float3(0.28, 0.42, 0.12);
  float3 far_g = float3(0.015, 0.03, 0.01);
  float3 bg = lerp(core_y, mid_g, smoothstep(0.0, 0.28, rr));
  bg = lerp(bg, far_g, smoothstep(0.18, 0.7, rr));
  bg = lerp(bg, ink, smoothstep(0.4, 1.0, rr));
  bg *= 0.45 + 0.5 * caustic;
  bg += core_y * pow(near, 2.8) * (0.85 + 0.45 * q1);
  bg = lerp(bg, ink, ring_line * 0.7);
  bg = lerp(bg, ink, spoke_line * 0.22 * smoothstep(0.12, 0.75, rr));
  bg *= 1.0 - spore * 0.4 * smoothstep(0.15, 0.95, rr);
  float3 coral_lo = float3(0.55, 0.12, 0.18);
  float3 coral_hi = float3(1.0, 0.45, 0.28);
  float3 chrome = float3(0.95, 0.92, 0.75);
  float3 men_a = float3(1.0, 0.2, 0.55);
  float3 men_b = float3(0.2, 0.85, 1.0);
  float3 men_c = float3(1.0, 0.7, 0.12);
  float3 men_d = float3(0.45, 1.0, 0.35);
  float3 men_e = float3(0.85, 0.35, 1.0);
  float hue_u = frac(cell_var * 3.7 + cid.x * 0.17 + cid.y * 0.31 + q9 * 0.08);
  float3 rim_hue = lerp(men_a, men_b, smoothstep(0.0, 0.22, hue_u));
  rim_hue = lerp(rim_hue, men_c, smoothstep(0.18, 0.42, hue_u));
  rim_hue = lerp(rim_hue, men_d, smoothstep(0.38, 0.65, hue_u));
  rim_hue = lerp(rim_hue, men_e, smoothstep(0.6, 0.88, hue_u));
  rim_hue = lerp(rim_hue, men_a, smoothstep(0.82, 1.0, hue_u));
  float3 tint = lerp(coral_lo, coral_hi, saturate(ht * 0.75 + 0.2 * cell_var));
  float3 lit = mercury_light(Nor, tint, ht, gfill, 0.85);
  float3 Vdir = float3(0.0, 0.0, 1.0);
  float3 R = normalize(float3(2.0 * Nor.z * Nor.x, 2.0 * Nor.z * Nor.y, 2.0 * Nor.z * Nor.z - 1.0));
  float3 Lcent = normalize(float3(-p.x, -p.y, 0.35 + 0.25 * q15) + float3(0.0, 0.0, 0.2));
  float3 Lcol = normalize(float3(cos(q14 + cell_var * 6.28), sin(q14 + cell_var * 6.28), 0.28 + 0.2 * q15));
  float shin = 24.0 + 75.0 * q11;
  float sp = pow(saturate(dot(R, Lcent)), shin) * 1.15;
  float glisten = pow(saturate(dot(R, Lcent)), 8.0 + 18.0 * q11) * (0.45 + 0.55 * ht);
  float edge = pow(saturate(meniscus), 1.8);
  float lit_edge = pow(saturate(dot(Nor, Lcol)), 2.2);
  float grazing = pow(1.0 - saturate(Nor.z), 1.7);
  float rim = edge * lit_edge * (0.5 + 0.5 * grazing);
  float3 Rcol = reflect(-Lcol, Nor);
  float rim_spec = pow(saturate(dot(Rcol, Vdir)), 14.0 + 32.0 * q11) * edge * lit_edge;
  float3 col = lerp(bg, lit, gfill);
  col += rim_hue * rim * gfill * (2.8 + 1.0 * q4 + 0.45 * q1);
  col += rim_hue * rim_spec * gfill * (1.8 + 0.75 * q11);
  col += chrome * sp * gfill * (0.55 + 0.3 * q11);
  col += chrome * glisten * gfill * (0.75 + 0.35 * q11);
  col += core_y * gfill * near * 0.1;
  col += coral_hi * gfill * q1 * 0.07;
  float vign = smoothstep(1.2, 0.1, rr);
  col *= 0.22 + 0.78 * vign;
"""

HEADER = """\
[preset00]
MILKDROP_PRESET_VERSION=201
PSVERSION=2
PSVERSION_WARP=2
PSVERSION_COMP=2
fRating=5.000000
fGammaAdj=1.100000
fDecay={decay:.6f}
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
per_frame_2=bm = bm + (bass - bm) * (1 - exp(-dt / 0.45));
per_frame_3=bd = bd + (abs(bass - bm) - bd) * (1 - exp(-dt / 1.5));
per_frame_4=hit = min(max(((bass - bm) / max(bd, 0.06) - 0.45) / 1.05, 0), 1);
per_frame_5=kick = max(kick * pow(0.80, 60 * dt), hit);
per_frame_6=k60 = pow(0.90, 60 * dt);
per_frame_7=sb = sb * k60 + bass_att * (1 - k60);
per_frame_8=sm = sm * k60 + mid_att * (1 - k60);
per_frame_9=st = st * k60 + treb_att * (1 - k60);
per_frame_10=energy = min(sb * 1.15 + sm * 0.35 + st * 0.15, 2.2);
per_frame_11=grow = min(max(energy * {grow_gain:.3f} + kick * {grow_kick:.3f}, 0), 1.15);
per_frame_12=ang = ang + dt * ({spin:.4f} + {spin_treb:.4f} * st + 0.05 * kick);
per_frame_13=scroll = scroll + dt * ({scroll:.4f} + 0.12 * sb + 0.08 * st);
per_frame_14=flow = sin(time * {flow_rate:.3f} + sm * 1.4);
per_frame_15=q1 = kick; q2 = sb; q3 = sm; q4 = st; q5 = ang;
per_frame_16=q6 = grow; q7 = {density:.3f}; q8 = {warp:.3f}; q9 = scroll;
per_frame_17=q10 = {site_motion:.3f}; q11 = {spec:.3f}; q12 = flow;
per_frame_18=q13 = 0.95 + 0.16 * energy + 0.1 * kick;
per_frame_19=light_ang = light_ang + dt * (0.55 + 1.55 * st + 1.05 * kick + 0.4 * sb);
per_frame_20=q14 = light_ang; q15 = 0.45 + 0.4 * energy;
"""

# Whole-frame zoom/trail plus soft liquid drift. Per-element motion is in comp.
WARP_SOFT = COMMON + """
shader_body
{
  float2 p = uv - 0.5;
  float z = 0.978 - 0.025 * q1 - 0.018 * q2;
  float2 suv = 0.5 + p * z;
  float2 w = float2(
    noise2(uv * 2.8 + float2(time * 0.03, q9 * 0.15)),
    noise2(uv * 2.8 + float2(4.7, time * 0.025)));
  suv += (w - 0.5) * (0.006 + 0.008 * q8);
  suv = lerp(suv, uv_orig, 0.16);
  float3 prev = tex2D(sampler_main, suv).rgb;
  float3 blur = GetBlur1(suv);
  float3 retc = prev * 0.93 + blur * 0.05;
  retc *= 0.99 - 0.006 * q1;
  ret = max(retc - 0.0012, 0.0);
}
"""

WARP_RADIAL = COMMON + """
shader_body
{
  float2 foc = float2(-0.07, 0.03);
  float2 p = uv - 0.5 - foc * 0.35;
  float z = 0.972 - 0.025 * q1 - 0.016 * q2;
  float2 suv = 0.5 + foc * 0.35 + rot2(p, 0.014 + 0.022 * q4 + 0.01 * q1) * z;
  float2 w = float2(
    noise2(uv * 2.2 + float2(q9 * 0.1, time * 0.025)),
    noise2(uv * 2.2 + float2(3.9, -q9 * 0.08)));
  suv += (w - 0.5) * (0.004 + 0.006 * q8);
  float3 prev = tex2D(sampler_main, suv).rgb;
  float3 blur = GetBlur1(suv);
  float3 retc = prev * 0.9 + blur * 0.05;
  retc *= 0.988 - 0.007 * q1;
  ret = max(retc - 0.0018, 0.0);
}
"""


PRESETS = [
    {
        "file": "01-molten-gold-cells.milk",
        "title": "Yellow-gold mercury puddles",
        "kind": "voronoi",
        "palette": PALETTE_YELLOW_GOLD,
        "decay": 0.988,
        "pf": dict(
            grow_gain=0.88,
            grow_kick=0.65,
            spin=0.008,
            spin_treb=0.02,
            scroll=0.06,
            flow_rate=0.18,
            density=6.8,
            warp=0.55,
            site_motion=0.45,
            spec=0.95,
        ),
        "comp_extra": """
  ret = led_tonemap(col);
""",
    },
    {
        "file": "02-honey-bloom.milk",
        "title": "Green-gold mercury bloom",
        "kind": "voronoi",
        "palette": PALETTE_GREEN_GOLD,
        "decay": 0.992,
        "pf": dict(
            grow_gain=0.98,
            grow_kick=0.75,
            spin=0.006,
            spin_treb=0.02,
            scroll=0.04,
            flow_rate=0.12,
            density=5.0,
            warp=0.48,
            site_motion=0.3,
            spec=1.05,
        ),
        "comp_extra": """
  col += hi_f0 * pow(gfill, 2.0) * (0.08 + 0.18 * q2);
  col += rim_hue * rim * gfill * (0.35 + 0.2 * q4);
  ret = led_tonemap(col * 1.04);
""",
    },
    {
        "file": "03-liquid-amber-flow.milk",
        "title": "Purple metal under sky-blue light",
        "kind": "purple_sky",
        "decay": 0.98,
        "pf": dict(
            grow_gain=0.8,
            grow_kick=0.55,
            spin=0.018,
            spin_treb=0.05,
            scroll=0.14,
            flow_rate=0.4,
            density=8.2,
            warp=0.7,
            site_motion=0.65,
            spec=1.15,
        ),
        "comp_extra": """
  float trail = saturate(dot(GetBlur2(uv), float3(0.25, 0.2, 0.45)));
  col += metal_hi * trail * gfill * 0.1;
  col += sky * trail * gfill * 0.08;
  ret = led_tonemap(col);
""",
    },
    {
        "file": "04-radial-metallic.milk",
        "title": "Vanishing-point petri mercury",
        "kind": "radial",
        "decay": 0.985,
        "pf": dict(
            grow_gain=0.78,
            grow_kick=0.5,
            spin=0.055,
            spin_treb=0.1,
            scroll=0.06,
            flow_rate=0.16,
            density=12.0,
            warp=0.35,
            site_motion=0.32,
            spec=1.15,
        ),
        "comp_extra": """
  col += chrome * glisten * gfill * 0.2;
  col += rim_hue * rim * gfill * (0.4 + 0.25 * q4);
  ret = led_tonemap(col);
""",
    },
    {
        "file": "05-heat-temper-puddles.milk",
        "title": "Heat-temper neon puddles",
        "kind": "heat",
        "decay": 0.986,
        "pf": dict(
            grow_gain=0.9,
            grow_kick=0.6,
            spin=0.01,
            spin_treb=0.03,
            scroll=0.2,
            flow_rate=0.28,
            density=6.5,
            warp=0.5,
            site_motion=0.4,
            spec=1.15,
        ),
        "comp_extra": """
  ret = led_tonemap(col);
""",
    },
]


def write_preset(spec: dict) -> Path:
    path = ROOT / spec["file"]
    kind = spec.get("kind", "voronoi")
    if kind == "radial":
        warp = WARP_RADIAL
        body = RADIAL_METAL_BODY
    elif kind == "heat":
        warp = WARP_SOFT
        body = HEAT_VORONOI_BODY
    elif kind == "purple_sky":
        warp = WARP_SOFT
        body = PURPLE_SKY_BODY
    else:
        warp = WARP_SOFT
        pal = spec.get("palette", PALETTE_YELLOW_GOLD)
        body = voronoi_palette_body(
            hi=pal["hi"],
            lo=pal["lo"],
            charcoal=pal.get("charcoal", (0.015, 0.012, 0.01)),
            rim=pal.get("rim"),
        )
    comp = (
        COMMON
        + """
shader_body
{
"""
        + body
        + spec["comp_extra"]
        + """
}
"""
    )
    text = (
        HEADER.format(decay=spec["decay"])
        + PER_FRAME.format(**spec["pf"])
        + lines("warp", warp)
        + lines("comp", comp)
    )
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for spec in PRESETS:
        path = write_preset(spec)
        print(f"wrote {path.relative_to(ROOT.parent.parent)} ({spec['title']})")


if __name__ == "__main__":
    main()
