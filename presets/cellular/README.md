# Cellular / metallic presets (GPL-3.0-or-later)

Motifs:

1. Voronoi metaball mercury puddles — uneven liquid-metal lobes. Each site
   drifts, swells, and beat-pops on its own seed while the warp pass also
   zooms the whole frame. A perimeter key light orbits with the music.
2. Giger-style biomechanical radial — bone ribs, gunmetal tubes, sickly
   green-grey metal; individual lanes drift and pulse under a shared zoom.
3. Heat-temper puddles — same pools with marching purple / green / blue neon
   discoloration and strong surface-tension meniscus reflections.

No MilkDrop 3 `get_fft()`. Prefer **128×128+**. Regenerate:

```bash
python3 scripts/gen_cellular_presets.py
```

| File | Motif |
|---|---|
| `01-molten-gold-cells.milk` | Yellow/gold mercury puddles |
| `02-honey-bloom.milk` | Green/gold mercury bloom; larger cells |
| `03-liquid-amber-flow.milk` | Deep purple metal under bright sky-blue light |
| `04-radial-metallic.milk` | Vanishing-point petri dish; coral diplococci + rings |
| `05-heat-temper-puddles.milk` | Heat-temper neon march + orbiting rim light |

```bash
./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/cellular --switch-delay 35 \
  --ddp 192.168.1.50:4048 --audio pulse
```

Licence: GPL-3.0-or-later (same as `../LICENSE`).
