# Third-party components

milk-ddp itself is licensed under the **GNU General Public License v3 or later**
(see `LICENSE`). The components below have their own terms. Recipients of
binaries must receive the corresponding source offers required by those licences.

## libprojectM

| Field | Value |
|---|---|
| Project | [projectM-visualizer/projectm](https://github.com/projectM-visualizer/projectm) |
| Default version | tag `v4.1.8` (`MILK_DDP_PROJECTM_GIT_TAG`) |
| Licence | **GNU LGPL-2.1 or later** |
| How obtained | FetchContent, `third_party/projectm/`, `MILK_DDP_PROJECTM_SOURCE`, or system `find_package(projectM4)` |

When milk-ddp is distributed as a binary that statically or dynamically
links libprojectM, the LGPL requires that recipients can obtain the libprojectM
source used for that build and can relink against a modified libprojectM. The
matching tag is recorded in CMake (`MILK_DDP_PROJECTM_GIT_TAG`) and in
release assets.

libprojectM also vendors its own dependencies (for example projectM-eval, hlslparser,
SOIL2/stb, GLM when not using the system copy). Their licences ship inside the
libprojectM source tree.

## In-tree presets (`presets/`)

| Path | Licence | Notes |
|---|---|---|
| `presets/*.milk`, `presets/lowres/` | **GPL-3.0-or-later** | Original works for LED matrices 64×64–256×256. See `presets/LICENSE`. |
| `presets/modern/` | **MIT** | Curated MilkDrop 2 / mock-3D selection from [M0Rf30/projectm-presets](https://github.com/M0Rf30/projectm-presets). See `presets/modern/LICENSE`. |

## Recommended external preset packs (optional)

Clone separately and pass `--preset-path` / `--texture-path`. Check each pack’s
own licence and attribution before redistribution.

| Pack | Repository | Notes |
|---|---|---|
| M0Rf30 modern presets (full upstream) | [M0Rf30/projectm-presets](https://github.com/M0Rf30/projectm-presets) | MIT. A subset is already under `presets/modern/`. MilkDrop 3 `.milk2` needs a MilkDrop 3 player, not projectM. |
| Cream of the Crop | [projectM-visualizer/presets-cream-of-the-crop](https://github.com/projectM-visualizer/presets-cream-of-the-crop) | ~10k curated presets (Fractal, Hypnotic, …); default in modern projectM frontends. Treated as public-domain redistribution by that repo; individual authors may still assert rights. |
| Milkdrop texture pack | [projectM-visualizer/presets-milkdrop-texture-pack](https://github.com/projectM-visualizer/presets-milkdrop-texture-pack) | Base textures many classic presets expect; use with `--texture-path`. |
| Classic projectM presets | [projectM-visualizer/presets-projectm-2.0](https://github.com/projectM-visualizer/presets-projectm-2.0) | Older projectM collection. |
| Milkdrop 2 presets | See projectM org / Winamp Milkdrop collections | Original Milkdrop 1/2 sets; licence varies by author. |

Original Milkdrop presets are typically redistributed under terms set by their
individual authors. Prefer the projectM-visualizer GitHub mirrors for packs
intended for projectM.

## Mesa / EGL / PulseAudio / ALSA

Runtime system libraries (Mesa llvmpipe, libpulse, libasound) are linked
dynamically from the host or container image and are not redistributed as
source in this tree. Their licences are those of the OS packages.

## DDP protocol

The Distributed Display Protocol is documented by 3waylabs / WLED. This
repository implements a sender only; no third-party DDP library is vendored.
