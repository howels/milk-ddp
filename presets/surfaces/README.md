# Waveform → texture → surface presets (GPL-3.0-or-later)

MilkDrop 2 presets that:

1. Draw thick **spectrum** and **waveform** ink into the framebuffer (custom waves).
2. **Warp** scrolls that ink into a persistent texture history (`sampler_main`).
3. **Comp** raymarches a fake-3D surface and maps that texture onto it.

Surface colour follows audio bands (bass → warm, mid → green–yellow, treb →
cyan–magenta, kick → coloured flash), not a fixed palette. Exposure is capped
for LED matrices (same approach as `cellular`); full-white is avoided.

No MilkDrop 3 `get_fft()`. Prefer **128×128+**. Regenerate with:

```bash
python3 scripts/gen_surface_presets.py
```

| File | Surface |
|---|---|
| `01-convex-sphere-skin.milk` | Convex sphere — audio-coloured waveform/spectrum skin |
| `02-concave-bowl.milk` | Concave bowl — audio-coloured texture on the inner wall |
| `03-waveform-hills.milk` | Landscape — audio-driven hills with draped waveform texture |
| `04-convex-torus-wrap.milk` | Convex torus — audio-coloured texture wraps the tube |

```bash
./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/surfaces --switch-delay 40 \
  --ddp 192.168.1.50:4048 --audio pulse
```

Licence: GPL-3.0-or-later (same as `../LICENSE`).
