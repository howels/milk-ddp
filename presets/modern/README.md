# Modern MilkDrop 2 presets (MIT)

Curated selection from [M0Rf30/projectm-presets](https://github.com/M0Rf30/projectm-presets)
(MIT Licence — see `LICENSE` in this directory). These are **post-classic Milkdrop**
presets: MilkDrop 2 warp/composite pixel shaders, mock-3D flythroughs, fractals,
and kaleidoscopic geometry. They need **libprojectM ≥ 4.1** (shader path).

Prefer **128×128 and above**. On 64×64 they still run but fine detail collapses.

Presets that call MilkDrop 3 `get_fft()` (Event Horizon, Crystal Cathedral, …)
are omitted: plain projectM cannot compile those shaders. MilkDrop 3 `.milk2`
double presets are also omitted.

| File | Look |
|---|---|
| `M0Rf30 - Aurora Cathedral.milk` | Northern-lights curtains over a mirrored lake |
| `M0Rf30 - Bioluminescent Abyss.milk` | Deep-water jellyfish / plankton |
| `M0Rf30 - Liquid Chrome Kaleidoscope.milk` | 12-mirror molten chrome |
| `M0Rf30 - Nebula Forge.milk` | Hubble-like core + kick shock ring |
| `M0Rf30 - Neon Sacred Geometry.milk` | Flower-of-life mandala on a synthwave grid |
| `M0Rf30 - Tramonto sul Golfo.milk` | Sunset / Vesuvius seascape |
| `M0Rf30 - Fractal Sanctum.milk` | Morphing Julia / orbit-trap colouring |
| `M0Rf30 - Kali Nebula Flythrough.milk` | Kali-set nebula flythrough (mock-3D) |
| `M0Rf30 - Hyperspace.milk` | Warp-drive starfield (mock-3D) |

```bash
./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/modern \
  --shuffle-delay 45 \
  --ddp 192.168.1.50:4048 --audio pulse
```

Upstream: https://github.com/M0Rf30/projectm-presets  
Copyright (c) 2026 Gianluca Boiano (M0Rf30).
