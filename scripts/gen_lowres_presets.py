#!/usr/bin/env python3
"""Generate original GPL-3.0 Milkdrop presets for milk-ddp LED matrices.

Motifs follow popular Milkdrop families (spectrum, tunnel, radial bloom,
spiral, circle wave, plasma) but equations and parameters are newly written
for matrices from 64×64 through 256×256: thick waves, high contrast, strong
beat coupling, no texture dependencies.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "presets" / "lowres"

HEADER = """\
[preset00]
fRating=3.000000
fGammaAdj={gamma:.6f}
fDecay={decay:.6f}
fVideoEchoZoom=1.000000
fVideoEchoAlpha=0.000000
nVideoEchoOrientation=0
nWaveMode={wave_mode}
bAdditiveWaves={additive}
bWaveDots={dots}
bWaveThick=1
bModWaveAlphaByVolume=0
bMaximizeWaveColor=1
bTexWrap=1
bDarkenCenter={darken_center}
bRedBlueStereo=0
bBrighten=0
bDarken=0
bSolarize=0
bInvert=0
fWaveAlpha={wave_alpha:.6f}
fWaveScale={wave_scale:.6f}
fWaveSmoothing=0.700000
fWaveParam=0.000000
fModWaveAlphaStart=0.750000
fModWaveAlphaEnd=0.950000
fWarpAnimSpeed=1.000000
fWarpScale={warp_scale:.6f}
fZoomExponent=1.000000
fShader=0.000000
zoom={zoom:.6f}
rot={rot:.6f}
cx=0.500000
cy=0.500000
dx={dx:.6f}
dy={dy:.6f}
warp={warp:.6f}
sx=1.000000
sy=1.000000
wave_r={wr:.6f}
wave_g={wg:.6f}
wave_b={wb:.6f}
wave_x=0.500000
wave_y={wave_y:.6f}
ob_size={ob_size:.6f}
ob_r=0.000000
ob_g=0.000000
ob_b=0.000000
ob_a={ob_a:.6f}
ib_size={ib_size:.6f}
ib_r=0.200000
ib_g=0.200000
ib_b=0.250000
ib_a={ib_a:.6f}
nMotionVectorsX=12.000000
nMotionVectorsY=9.000000
mv_dx=0.000000
mv_dy=0.000000
mv_l=0.900000
mv_r=1.000000
mv_g=1.000000
mv_b=1.000000
mv_a=0.000000
"""


def write(name: str, body: str, per_frame: list[str], per_pixel: list[str] | None = None) -> None:
    lines = [body.rstrip("\n")]
    for i, expr in enumerate(per_frame, start=1):
        lines.append(f"per_frame_{i}={expr}")
    if per_pixel:
        for i, expr in enumerate(per_pixel, start=1):
            lines.append(f"per_pixel_{i}={expr}")
    path = ROOT / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT.parent.parent)}")


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)

    write(
        "01-spectrum-pulse.milk",
        HEADER.format(
            gamma=1.1,
            decay=0.94,
            wave_mode=0,
            additive=0,
            dots=0,
            darken_center=0,
            wave_alpha=0.95,
            wave_scale=1.4,
            warp_scale=1.0,
            zoom=1.01,
            rot=0.0,
            dx=0.0,
            dy=0.0,
            warp=0.0,
            wr=0.3,
            wg=0.8,
            wb=1.0,
            wave_y=0.5,
            ob_size=0.02,
            ob_a=0.4,
            ib_size=0.0,
            ib_a=0.0,
        ),
        [
            "wave_r = 0.25 + 0.75*bass_att;",
            "wave_g = 0.35 + 0.55*mid_att;",
            "wave_b = 0.55 + 0.45*treb_att;",
            "zoom = 1.005 + 0.04*bass;",
            "wave_mystery = 0.1*sin(time);",
        ],
    )

    write(
        "02-radial-bloom.milk",
        HEADER.format(
            gamma=1.2,
            decay=0.92,
            wave_mode=7,
            additive=1,
            dots=0,
            darken_center=1,
            wave_alpha=0.85,
            wave_scale=0.9,
            warp_scale=1.2,
            zoom=1.04,
            rot=0.0,
            dx=0.0,
            dy=0.0,
            warp=0.12,
            wr=1.0,
            wg=0.45,
            wb=0.2,
            wave_y=0.5,
            ob_size=0.0,
            ob_a=0.0,
            ib_size=0.02,
            ib_a=0.25,
        ),
        [
            "zoom = 1.02 + 0.08*bass_att;",
            "warp = 0.08 + 0.12*mid;",
            "wave_r = 0.6 + 0.4*bass;",
            "wave_g = 0.25 + 0.35*mid;",
            "wave_b = 0.15 + 0.5*treb;",
            "cx = 0.5 + 0.02*sin(time*0.3);",
            "cy = 0.5 + 0.02*cos(time*0.4);",
        ],
        [
            "zoom = zoom + 0.06*rad*bass_att;",
            "rot = 0.02*(1-rad)*sin(time);",
        ],
    )

    write(
        "03-spiral-orbit.milk",
        HEADER.format(
            gamma=1.0,
            decay=0.96,
            wave_mode=1,
            additive=0,
            dots=0,
            darken_center=0,
            wave_alpha=0.8,
            wave_scale=1.1,
            warp_scale=1.5,
            zoom=1.02,
            rot=0.03,
            dx=0.0,
            dy=0.0,
            warp=0.05,
            wr=0.7,
            wg=0.3,
            wb=0.9,
            wave_y=0.5,
            ob_size=0.015,
            ob_a=0.3,
            ib_size=0.0,
            ib_a=0.0,
        ),
        [
            "rot = 0.02 + 0.03*sin(time*0.25) + 0.02*treb;",
            "zoom = 1.015 + 0.03*mid_att;",
            "wave_r = 0.5 + 0.5*sin(time*0.7);",
            "wave_g = 0.3 + 0.4*sin(time*0.9 + 2);",
            "wave_b = 0.6 + 0.4*sin(time*1.1 + 4);",
            "warp = 0.04 + 0.06*bass;",
        ],
        [
            "rot = rot + 0.08*rad;",
            "zoom = zoom + 0.03*(0.5-rad);",
        ],
    )

    write(
        "04-circle-wave.milk",
        HEADER.format(
            gamma=1.15,
            decay=0.93,
            wave_mode=2,
            additive=0,
            dots=0,
            darken_center=0,
            wave_alpha=0.9,
            wave_scale=1.0,
            warp_scale=1.0,
            zoom=1.01,
            rot=0.0,
            dx=0.0,
            dy=0.0,
            warp=0.02,
            wr=0.2,
            wg=1.0,
            wb=0.6,
            wave_y=0.5,
            ob_size=0.0,
            ob_a=0.0,
            ib_size=0.025,
            ib_a=0.35,
        ),
        [
            "wave_scale = 0.85 + 0.4*bass_att;",
            "wave_r = 0.2 + 0.6*treb;",
            "wave_g = 0.5 + 0.5*mid;",
            "wave_b = 0.4 + 0.6*bass;",
            "zoom = 1.008 + 0.025*mid;",
            "ib_a = 0.2 + 0.3*bass_att;",
        ],
    )

    write(
        "05-plasma-drift.milk",
        HEADER.format(
            gamma=1.3,
            decay=0.97,
            wave_mode=5,
            additive=1,
            dots=0,
            darken_center=0,
            wave_alpha=0.55,
            wave_scale=1.6,
            warp_scale=2.0,
            zoom=1.005,
            rot=0.005,
            dx=0.002,
            dy=0.001,
            warp=0.2,
            wr=0.9,
            wg=0.4,
            wb=0.7,
            wave_y=0.55,
            ob_size=0.0,
            ob_a=0.0,
            ib_size=0.0,
            ib_a=0.0,
        ),
        [
            "dx = 0.004*sin(time*0.2) + 0.002*mid;",
            "dy = 0.003*cos(time*0.17);",
            "warp = 0.15 + 0.15*bass_att;",
            "wave_r = 0.5 + 0.5*sin(time*0.4 + bass);",
            "wave_g = 0.3 + 0.4*sin(time*0.55 + mid);",
            "wave_b = 0.5 + 0.5*sin(time*0.7 + treb);",
            "rot = 0.01*sin(time*0.1);",
        ],
        [
            "dx = dx + 0.01*sin(ang*3 + time);",
            "dy = dy + 0.01*cos(ang*2 - time);",
        ],
    )

    write(
        "06-bass-thump.milk",
        HEADER.format(
            gamma=1.25,
            decay=0.90,
            wave_mode=0,
            additive=1,
            dots=0,
            darken_center=1,
            wave_alpha=1.0,
            wave_scale=1.5,
            warp_scale=1.0,
            zoom=1.06,
            rot=0.0,
            dx=0.0,
            dy=0.0,
            warp=0.0,
            wr=1.0,
            wg=0.2,
            wb=0.1,
            wave_y=0.5,
            ob_size=0.03,
            ob_a=0.5,
            ib_size=0.0,
            ib_a=0.0,
        ),
        [
            "zoom = 1.02 + 0.12*bass_att;",
            "decay = 0.88 + 0.06*(1-bass);",
            "wave_r = 0.7 + 0.3*bass;",
            "wave_g = 0.15 + 0.25*mid;",
            "wave_b = 0.1 + 0.4*treb;",
            "ob_a = 0.25 + 0.5*bass_att;",
            "wave_thick = above(bass_att, 0.6);",
        ],
    )

    write(
        "07-ring-echo.milk",
        HEADER.format(
            gamma=1.1,
            decay=0.95,
            wave_mode=2,
            additive=0,
            dots=0,
            darken_center=0,
            wave_alpha=0.75,
            wave_scale=0.7,
            warp_scale=1.0,
            zoom=1.03,
            rot=0.0,
            dx=0.0,
            dy=0.0,
            warp=0.0,
            wr=0.4,
            wg=0.9,
            wb=1.0,
            wave_y=0.5,
            ob_size=0.0,
            ob_a=0.0,
            ib_size=0.04,
            ib_a=0.4,
        ),
        [
            "zoom = 1.02 + 0.05*bass;",
            "wave_scale = 0.55 + 0.45*mid_att;",
            "ib_size = 0.02 + 0.04*bass_att;",
            "ib_r = 0.2 + 0.5*sin(time);",
            "ib_g = 0.3 + 0.4*cos(time*0.8);",
            "ib_b = 0.5 + 0.5*sin(time*1.2);",
            "ib_a = 0.25 + 0.4*treb_att;",
        ],
        [
            "zoom = zoom + 0.05*pow(rad, 1.5);",
        ],
    )

    write(
        "08-diagonal-flow.milk",
        HEADER.format(
            gamma=1.05,
            decay=0.955,
            wave_mode=3,
            additive=0,
            dots=0,
            darken_center=0,
            wave_alpha=0.85,
            wave_scale=1.2,
            warp_scale=1.0,
            zoom=1.01,
            rot=0.0,
            dx=0.01,
            dy=0.008,
            warp=0.03,
            wr=0.95,
            wg=0.75,
            wb=0.25,
            wave_y=0.45,
            ob_size=0.01,
            ob_a=0.2,
            ib_size=0.0,
            ib_a=0.0,
        ),
        [
            "dx = 0.008 + 0.01*mid + 0.006*sin(time*0.5);",
            "dy = 0.006 + 0.008*bass + 0.004*cos(time*0.4);",
            "wave_r = 0.7 + 0.3*sin(time + bass);",
            "wave_g = 0.5 + 0.4*mid;",
            "wave_b = 0.2 + 0.3*treb;",
            "rot = 0.01*sin(time*0.2);",
        ],
    )

    write(
        "09-star-dots.milk",
        HEADER.format(
            gamma=1.4,
            decay=0.91,
            wave_mode=0,
            additive=1,
            dots=1,
            darken_center=1,
            wave_alpha=1.0,
            wave_scale=1.8,
            warp_scale=1.0,
            zoom=1.03,
            rot=0.01,
            dx=0.0,
            dy=0.0,
            warp=0.0,
            wr=1.0,
            wg=1.0,
            wb=0.6,
            wave_y=0.5,
            ob_size=0.0,
            ob_a=0.0,
            ib_size=0.0,
            ib_a=0.0,
        ),
        [
            "zoom = 1.015 + 0.05*bass_att;",
            "rot = 0.015*sin(time*0.6) + 0.01*treb;",
            "wave_r = 0.6 + 0.4*treb_att;",
            "wave_g = 0.6 + 0.4*mid_att;",
            "wave_b = 0.3 + 0.5*bass;",
            "wave_scale = 1.2 + 0.8*mid;",
        ],
        [
            "zoom = zoom + 0.04*(1-rad);",
        ],
    )

    write(
        "10-square-frame.milk",
        HEADER.format(
            gamma=1.0,
            decay=0.94,
            wave_mode=6,
            additive=0,
            dots=0,
            darken_center=0,
            wave_alpha=0.7,
            wave_scale=1.0,
            warp_scale=1.0,
            zoom=1.0,
            rot=0.0,
            dx=0.0,
            dy=0.0,
            warp=0.0,
            wr=0.5,
            wg=0.9,
            wb=0.5,
            wave_y=0.5,
            ob_size=0.04,
            ob_a=0.7,
            ib_size=0.02,
            ib_a=0.5,
        ),
        [
            "ob_a = 0.4 + 0.5*bass_att;",
            "ib_a = 0.3 + 0.4*mid_att;",
            "ob_r = 0.1 + 0.6*bass;",
            "ob_g = 0.2 + 0.5*mid;",
            "ob_b = 0.4 + 0.6*treb;",
            "ib_r = 1 - ob_r;",
            "ib_g = 1 - ob_g;",
            "ib_b = 1 - ob_b;",
            "zoom = 1.0 + 0.03*bass;",
            "wave_a = 0.4 + 0.4*treb_att;",
        ],
    )

    write(
        "11-tunnel-rush.milk",
        HEADER.format(
            gamma=1.2,
            decay=0.98,
            wave_mode=7,
            additive=0,
            dots=0,
            darken_center=0,
            wave_alpha=0.7,
            wave_scale=0.6,
            warp_scale=1.4,
            zoom=1.05,
            rot=0.02,
            dx=0.0,
            dy=0.0,
            warp=0.18,
            wr=0.9,
            wg=0.5,
            wb=0.2,
            wave_y=0.5,
            ob_size=0.0,
            ob_a=0.0,
            ib_size=0.01,
            ib_a=0.15,
        ),
        [
            "zoom = 1.03 + 0.06*mid_att;",
            "rot = 0.015 + 0.02*sin(time*0.35);",
            "warp = 0.12 + 0.15*bass;",
            "wave_r = 0.8 + 0.2*bass;",
            "wave_g = 0.35 + 0.35*mid;",
            "wave_b = 0.15 + 0.4*treb;",
        ],
        [
            "zoom = zoom + 0.08*rad;",
            "rot = rot + 0.03*(rad-0.5);",
        ],
    )

    write(
        "12-horiz-sweep.milk",
        HEADER.format(
            gamma=1.1,
            decay=0.93,
            wave_mode=4,
            additive=1,
            dots=0,
            darken_center=0,
            wave_alpha=0.9,
            wave_scale=1.3,
            warp_scale=1.0,
            zoom=1.01,
            rot=0.0,
            dx=0.02,
            dy=0.0,
            warp=0.0,
            wr=0.3,
            wg=0.6,
            wb=1.0,
            wave_y=0.5,
            ob_size=0.0,
            ob_a=0.0,
            ib_size=0.0,
            ib_a=0.0,
        ),
        [
            "dx = 0.015 + 0.02*bass_att*sin(time);",
            "wave_y = 0.45 + 0.1*sin(time*0.8);",
            "wave_r = 0.25 + 0.5*mid;",
            "wave_g = 0.4 + 0.5*treb;",
            "wave_b = 0.7 + 0.3*bass;",
            "zoom = 1.005 + 0.02*mid;",
        ],
    )


if __name__ == "__main__":
    main()
