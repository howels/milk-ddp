# Presets (GPL-3.0-or-later)

Root samples, `lowres/`, `fractal/`, `surfaces/`, `neon/`, `jelly/`,
`rush/`, and `cellular/` are **original GPL-3.0-or-later** works for
milk-ddp LED matrices. `lowres/` targets **64×64–256×256** with thick
waves and strong beat coupling. `fractal/` is MilkDrop 2 shader fractals
(classic sets, nature / landscape, and zoom-rush dives). `surfaces/` maps
waveform/spectrum textures onto fake-3D convex, concave, and landscape
geometry (128×128+). `neon/` is high-saturation neon grids, tubes, lasers,
signage, and circuit traces. `jelly/` is gelatinous relief / machine-code
scroll presets inspired by Butterchurn Machine Code (Jelly) aesthetics.
`rush/` is forward-zoom tunnels built from waveform-driven geometric
patterns. `cellular/` is Voronoi molten-gold cells whose amber fill grows
from zero with bass and kick.

`modern/` is a **MIT** curated selection of post-classic MilkDrop 2 presets
(shaders, mock-3D, fractals) from M0Rf30 — see `modern/README.md`.

## Pack layout

| Path | Contents |
|---|---|
| `milk-ddp-bars.milk` | First-light / CI waveform (GPL) |
| `milk-ddp-tunnel.milk` | Soft warp sample (GPL) |
| `lowres/` | Twelve GPL presets for 64×64–256×256 matrices |
| `fractal/` | Twelve GPL MilkDrop 2 fractal presets (classic, nature, zoom-rush) |
| `surfaces/` | Four GPL waveform→texture→3D surface presets (sphere, bowl, hills, torus) |
| `neon/` | Five GPL vivid neon pattern presets (grid, tubes, lasers, signage, circuit) |
| `jelly/` | Five GPL jelly relief / machine-code scroll presets |
| `rush/` | Twelve GPL forward-zoom waveform geometry / flyover presets |
| `cellular/` | Five GPL presets: mercury puddles, Giger radial, heat-temper neon |
| `modern/` | Nine MIT MilkDrop 2 / mock-3D presets (M0Rf30) |
| `LICENSE` | GPL notice for the original in-tree presets |

### `lowres/` (64×64–256×256 WLED matrices)

| File | Motif |
|---|---|
| `01-spectrum-pulse.milk` | Spectrum-style waveform, bass zoom |
| `02-radial-bloom.milk` | Radial bloom / centre darken |
| `03-spiral-orbit.milk` | Slow spiral orbit |
| `04-circle-wave.milk` | Circular wave + inner border |
| `05-plasma-drift.milk` | Soft plasma drift |
| `06-bass-thump.milk` | Aggressive bass zoom / border |
| `07-ring-echo.milk` | Concentric ring zoom |
| `08-diagonal-flow.milk` | Diagonal flow |
| `09-star-dots.milk` | Dot waveform starfield |
| `10-square-frame.milk` | Beat-reactive frame borders |
| `11-tunnel-rush.milk` | Tunnel rush (low-res friendly) |
| `12-horiz-sweep.milk` | Horizontal sweep |

Regenerate from the recipe script (optional):

```bash
python3 scripts/gen_lowres_presets.py
```

## Use

Design range: **`--width` / `--height` from 64 to 256** (square or rectangular
within that band). Below 64, features still run but look blocky; above 256,
prefer a denser third-party pack plus textures.

```bash
# 64×64 matrix, lowres pack
./build/milk-ddp --width 64 --height 64 \
  --preset-path ./presets/lowres --ddp 192.168.1.50:4048 --audio pulse

# 256×256 matrix
./build/milk-ddp --width 256 --height 256 \
  --preset-path ./presets/lowres --ddp 192.168.1.50:4048 --audio pulse

# Modern MilkDrop 2 / mock-3D pack (128×128+)
./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/modern \
  --switch-delay 45 \
  --ddp 192.168.1.50:4048 --audio pulse

# Entire in-tree tree (GPL samples + lowres + modern)
./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets --preset-duration 30 \
  --ddp 192.168.1.50:4048 --audio pulse
```

`--preset-duration` / `--switch-delay` set how long each playlist preset is
shown before the next transition (libprojectM default is 30 seconds).

## Larger third-party packs (optional, not GPL-cleared as a set)

For thousands of classic Milkdrop looks, clone packs separately. Their
authorship is mixed; projectM documents Cream of the Crop as freely released /
treated as public domain, which is **not** the same as GPL-3.0. Do not mix
those files into this `presets/` tree if you need a pure GPL-3.0 distribution.

```bash
git clone --depth 1 \
  https://github.com/projectM-visualizer/presets-cream-of-the-crop.git \
  ~/presets/cream-of-the-crop

git clone --depth 1 \
  https://github.com/projectM-visualizer/presets-milkdrop-texture-pack.git \
  ~/presets/textures

./build/milk-ddp \
  --preset-path ~/presets/cream-of-the-crop \
  --texture-path ~/presets/textures \
  --ddp 192.168.1.50:4048
```

| Pack | URL |
|---|---|
| Cream of the Crop | https://github.com/projectM-visualizer/presets-cream-of-the-crop |
| Texture pack | https://github.com/projectM-visualizer/presets-milkdrop-texture-pack |
| Classic projectM 2.x | https://github.com/projectM-visualizer/presets-projectm-2.0 |
