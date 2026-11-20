# Fractal presets (GPL-3.0-or-later)

Original MilkDrop 2 warp/comp shader presets for milk-ddp, written for LED
matrices (**128×128 and above** preferred). No textures and no MilkDrop 3
`get_fft()`. Iteration counts are moderate so Mesa llvmpipe stays interactive.

Regenerate:

```bash
python3 scripts/gen_fractal_presets.py
```

| File | Fractal |
|---|---|
| `01-julia-lattice.milk` | Julia set with stained-glass bands |
| `02-burning-ship.milk` | Burning Ship (absolute-value fold) |
| `03-mandelbrot-drift.milk` | Mandelbrot zoom / pan on bass |
| `04-tricorn-mirror.milk` | Tricorn (conjugate Mandelbrot) with mirror bleed |
| `05-barnsley-fern.milk` | Barnsley fern IFS canopy |
| `06-branching-tree.milk` | Recursive branching tree and canopy |
| `07-coastline-fjord.milk` | Mandelbrot coastline / fjord with sea depth |
| `08-mountain-range.milk` | fBm mountain range, snow line, treeline |
| `09-lightning-rivers.milk` | Julia orbit-trap lightning / river veins |
| `10-mandelbrot-hyperspace.milk` | Mandelbrot dive — forward zoom rush |
| `11-julia-warp-rush.milk` | Julia warp rush with speedlines |
| `12-burning-ship-dive.milk` | Burning Ship tunnel dive |

```bash
./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/fractal --switch-delay 40 \
  --ddp 192.168.1.50:4048 --audio pulse
```

Licence: same GPL-3.0-or-later as `../LICENSE` / the application.
