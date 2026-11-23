# Butterchurn MilkDrop presets (MIT pack)

MilkDrop 2 `.milk` sources from
[jberg/butterchurn-presets](https://github.com/jberg/butterchurn-presets)
(`presets/milkdrop/`). Butterchurn’s browser JSON conversions are **not**
shipped here: milk-ddp / libprojectM load `.milk` only.

**504** presets. Authors are credited in the filenames (Geiss, Flexi, martin,
Aderrasi, Zylot, Eo.S., Rovastar, and many others). The pack aggregation and
Butterchurn conversion tooling are MIT-licensed by Jordan Berg — see `LICENSE`.

Prefer **128×128 and above**. Many of these assume desktop resolution and
optional MilkDrop textures; on small matrices detail collapses and some looks
need `--texture-path` to a MilkDrop texture pack.

No MilkDrop 3 `get_fft()` calls were found in this set at import time.

```bash
./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/butterchurn \
  --switch-delay 40 \
  --ddp 192.168.1.50:4048 --audio pulse
```

With textures (optional; many classic presets look better with them):

```bash
git clone --depth 1 \
  https://github.com/projectM-visualizer/presets-milkdrop-texture-pack.git \
  ~/presets/textures

./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/butterchurn \
  --texture-path ~/presets/textures \
  --ddp 192.168.1.50:4048 --audio pulse
```

| Field | Value |
|---|---|
| Upstream | https://github.com/jberg/butterchurn-presets |
| Upstream path | `presets/milkdrop/` |
| Pack licence | MIT (`LICENSE` — Copyright (c) 2013–2018 Jordan Berg) |
| Individual presets | Author-named in each `.milk` filename; terms follow each author’s release into this pack |
| Not included | `presets/converted/*.json`, `presets/full/*.json` (Butterchurn-only) |

Do not treat this directory as GPL. Keep it separate from the original
GPL packs under `presets/lowres/`, `fractal/`, and so on.
