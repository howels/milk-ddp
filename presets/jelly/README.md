# Jelly / machine-code presets (GPL-3.0-or-later)

Original MilkDrop 2 presets inspired by the Butterchurn / Cream of the Crop
look of *Machine Code (Relief Block Mix) (Jelly)* (Stahlregen & Boz + Eo.S +
Geiss + Phat + Rovastar + Zylot). These files are new work, not copies of
that preset.

Shared mechanisms:

1. Vertical scroll of waveform / spectrum (or synthetic) ink.
2. Warp trail with max-blend, posterize colour hold, and slow darken.
3. Composite gelatinous relief from luminance gradients (fake normals).
4. Block / bit / cascade overlays for a machine-code feel.

No MilkDrop 3 `get_fft()`. Prefer **128×128+**. Regenerate:

```bash
python3 scripts/gen_jelly_presets.py
```

| File | Motif |
|---|---|
| `01-jelly-relief-scroll.milk` | Scroll + trail + gelatinous relief |
| `02-jelly-bitgrid.milk` | Machine-code bit grid with jelly emboss |
| `03-jelly-hex-lattice.milk` | Hexagonal jelly lattice |
| `04-jelly-cascade.milk` | Cascading code-rain columns |
| `05-jelly-plasma-blocks.milk` | Posterized plasma blocks |

```bash
./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/jelly --switch-delay 35 \
  --ddp 192.168.1.50:4048 --audio pulse
```

Licence: GPL-3.0-or-later (same as `../LICENSE`).
