# Neon presets (GPL-3.0-or-later)

Vivid high-saturation MilkDrop 2 presets: neon grids, tube ribbons, laser
starbursts, signage flicker, and circuit traces. Colours stay in the magenta /
cyan / lime / electric-blue range and react to bass, mid, treb, and kick.
Exposure is capped for LED matrices; full-white is reserved for kick strobes.

No MilkDrop 3 `get_fft()`. Prefer **128×128+**. Regenerate:

```bash
python3 scripts/gen_neon_presets.py
```

| File | Motif |
|---|---|
| `01-neon-grid.milk` | Perspective neon floor/ceiling grid |
| `02-neon-tubes.milk` | Glowing tube ribbons |
| `03-neon-lasers.milk` | Radial laser starburst + rings |
| `04-neon-signage.milk` | Flickering neon signage blocks |
| `05-neon-circuit.milk` | Circuit-board traces with traveling pulse |

```bash
./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/neon --switch-delay 35 \
  --ddp 192.168.1.50:4048 --audio pulse
```

Licence: GPL-3.0-or-later (same as `../LICENSE`).
