# milk-ddp

Headless [projectM](https://github.com/projectM-visualizer/projectm) renderer that draws Milkdrop presets at a matrix-sized resolution and sends each frame as [Distributed Display Protocol (DDP)](https://kno.wled.ge/interfaces/ddp/) UDP packets to [WLED](https://kno.wled.ge/).

No window is created. OpenGL 3.3 runs through an EGL pbuffer. libprojectM 4.1 composites onto framebuffer 0, so a pbuffer (not only a user FBO) is required. On machines without a GPU or display, Mesa llvmpipe is selected with `--software-gl`.

## What it does

1. Creates an off-screen EGL OpenGL 3.3 core context and an FBO of `--width` × `--height`.
2. Instantiates libprojectM 4.1.8, feeds PCM, and renders into that FBO.
3. Reads RGB pixels (top-left origin) and writes them as DDP RGB24 packets to `HOST:PORT` (default port 4048).
4. Splits frames larger than 480 RGB pixels across packets of at most 1440 bytes. The last packet of each frame sets the DDP Push flag so WLED latches the buffer. WLED does not use DDP timecodes; this sender does not send them.

Default size is 128×128 (16384 LEDs). That is 35 DDP packets per frame at the 1440-byte WLED payload cap.

## Build

**Prerequisites:**

- CMake 3.21 or newer, a C++17 compiler, git, make
- `libegl1-mesa-dev`, `libgl1-mesa-dev`, Mesa DRI (`libgl1-mesa-dri`) for software GL
- Optional: `libpulse-dev` for `--audio pulse` (async libpulse)
- Optional: `libasound2-dev` for `--audio alsa`

```bash
make            # → build/milk-ddp
make validate   # headless DDP self-test
make reconfigure  # after moving the source tree (CMake caches absolute paths)
```

Equivalent without Make:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc)"
```

### Where libprojectM comes from

This program links [libprojectM](https://github.com/projectM-visualizer/projectm) **v4.1.8** (C API + playlist). CMake picks the first match:

| Priority | How | Network |
|---|---|---|
| 1 | `-DMILK_DDP_USE_SYSTEM_PROJECTM=ON` → `find_package(projectM4)` + `projectM4Playlist` | No |
| 2 | `-DMILK_DDP_PROJECTM_SOURCE=/path/to/projectm` | No |
| 3 | `third_party/projectm/` present (see below) | No |
| 4 | FetchContent clone of the GitHub tag into `build/_deps/` | Yes, first configure only |

Default (priority 4) downloads from `https://github.com/projectM-visualizer/projectm.git` at tag `v4.1.8` and builds it as a static library into `build/milk-ddp`.

**Offline / local source:**

```bash
# One-time clone (submodules required)
make vendor-projectm
# or:
git clone --branch v4.1.8 --depth 1 --recurse-submodules \
  https://github.com/projectM-visualizer/projectm.git third_party/projectm

make OFFLINE=1
# equivalent:
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
  -DFETCHCONTENT_FULLY_DISCONNECTED=ON
```

Point at any checkout (another disk, mirror, already-fetched `_deps` copy):

```bash
make PROJECTM_SOURCE=/opt/src/projectm
# or:
cmake -S . -B build -DMILK_DDP_PROJECTM_SOURCE=/opt/src/projectm
```

Use a distro / prefix install of libprojectM 4.x (headers + `libprojectM::projectM` / `libprojectM::playlist`):

```bash
make USE_SYSTEM_PROJECTM=1
# or:
cmake -S . -B build -DMILK_DDP_USE_SYSTEM_PROJECTM=ON
```

If FetchContent already populated `build/_deps/projectm-src` on a machine with network, copy that tree (or the whole `build/_deps`) to an offline host and pass it as `MILK_DDP_PROJECTM_SOURCE`, or set `FETCHCONTENT_FULLY_DISCONNECTED=ON` so CMake reuses the existing download without contacting GitHub.

CMake cache keys: `MILK_DDP_PROJECTM_SOURCE`, `MILK_DDP_USE_SYSTEM_PROJECTM`, `MILK_DDP_PROJECTM_GIT_TAG`, `MILK_DDP_PROJECTM_GIT_REPOSITORY`.

## Run

Point `--ddp` at the WLED controller (default port **4048**; MoonLight often listens on **4049**). Enable DDP (or “Realtime”) on the device. The LED count on WLED must be at least `width * height`. If the UDP endpoint is down, milk-ddp logs `DDP endpoint offline` (rate-limited) and keeps rendering; pass `--close-on-disconnect` to exit instead.

```bash
./build/milk-ddp \
  --width 128 --height 128 --fps 30 \
  --ddp 192.168.1.50:4048 \
  --preset-path ./presets \
  --audio sine
```

Live capture from PulseAudio (PipeWire’s Pulse shim is enough):

```bash
./build/milk-ddp --ddp 192.168.1.50 --audio pulse --preset-path ./presets
```

`--audio pulse` connects to Pulse’s default source. It does **not** exit if the source is missing at start: PCM is silence until a source appears. Source and server subscription events reopen the stream when a device is plugged in, the default source changes, or the previous source is removed.

`--audio-gain F` is linear amplitude (default `1.0`). On `--audio pulse` it sets the Pulse/PipeWire record-stream soft volume (server-side, no per-sample loop in the render thread). Other backends scale inside `fill()` and clamp to `[-1, 1]`. Quiet container monitors: start around `1.5`–`4.0`.

`--audio alsa` opens ALSA’s `default` capture PCM. `--audio alsa:plughw:1,0` (or any other PCM name) selects a card directly. Missing devices are retried every 500 ms.

List Pulse and ALSA capture devices:

```bash
./build/milk-ddp --list-audio
```

```bash
./build/milk-ddp --audio pulse:alsa_input.usb-Device-00.analog-stereo …
./build/milk-ddp --audio alsa:plughw:1,0 …
PULSE_SOURCE=alsa_input.usb-Device-00.analog-stereo ./build/milk-ddp --audio pulse …
```

A 16-bit PCM WAV, looping:

```bash
./build/milk-ddp --audio file:/path/to/track.wav --preset-path ./presets --ddp 192.168.1.50
```

Raw stereo s16le on stdin at `--sample-rate`:

```bash
ffmpeg -i track.mp3 -f s16le -ac 2 -ar 44100 - \
  | ./build/milk-ddp --audio stdin --ddp 192.168.1.50 --preset-path ./presets
```

Headless / no GPU:

```bash
./build/milk-ddp --software-gl --ddp 127.0.0.1:4048 --frames 10 --preset-path ./presets
```

`--software-gl` sets `LIBGL_ALWAYS_SOFTWARE=1` and prefers llvmpipe. `DISPLAY` may be unset.

### CLI

| Argument | Meaning |
|---|---|
| `--width` / `-W`, `--height` / `-H` | FBO and DDP pixel grid (default 128×128) |
| `--ddp HOST[:PORT]` | UDP destination (default `127.0.0.1:4048`) |
| `--fps N` | Render and send rate, also passed to projectM (default 30) |
| `--preset-path DIR` | Recursively add `.milk` files (repeatable) |
| `--texture-path DIR` | projectM texture search path (repeatable) |
| `--preset FILE\|idle://` | Load one preset; `idle://` is the built-in logo |
| `--audio sine\|pulse\|pulse:SOURCE\|alsa\|alsa:DEVICE\|file:PATH\|stdin` | PCM source (default `sine`) |
| `--audio-gain F` | Linear amplitude (default `1.0`). Pulse: stream soft volume; else scale in `fill()`. Try `1.5`–`4.0` for quiet monitors |
| `--list-audio` | List Pulse and ALSA capture devices and exit |
| `--sample-rate N` | For `sine` and `stdin` (default 44100) |
| `--frames N` | Exit after N frames |
| `--dump-ppm FILE` | Write the last RGB frame as binary PPM |
| `--software-gl` | Force Mesa software rasteriser |
| `--close-on-disconnect` | Exit when the DDP endpoint is offline (default: log `DDP endpoint offline` at most once per second and keep rendering) |
| `--shuffle` | Randomise playlist selection (off by default) |
| `--no-shuffle` | Alphabetical full-path order (default) |
| `--preset-duration SEC` | Seconds each playlist preset is shown before switching (default 30) |
| `--switch-delay SEC` | Alias for `--preset-duration` |
| `--quiet` | Suppress startup status and progress |
| `--progress` | Print periodic status with measured fps on stderr |
| `--transition-half-fps` | During soft cuts, pace at `fps/2` and feed 2× PCM (off by default) |
| `--no-transition-half-fps` | Disable transition half-fps (default) |
| `--warm-presets` | Cache warp/comp shaders for every playlist preset at startup (default; 1 frame each, DDP off); prints progress |
| `--no-warm-presets` | Skip startup shader warm-up |
| `--pause-when-silent` | Skip GL/DDP while PCM is idle (default); for Pulse monitors of idle players |
| `--no-pause-when-silent` | Keep rendering during silence |
| `--silence-hold SEC` | Seconds of silence before pause (default `30`) |
| `--silence-threshold F` | Peak `|sample|` treated as silence (default `0.001`) |
| `--set KEY=VALUE` | projectM property (repeatable) |

`--set` keys: `beat_sensitivity`, `hard_cut_duration`, `hard_cut_enabled`, `hard_cut_sensitivity`, `soft_cut_duration`, `preset_duration`, `mesh_size` (`WxH`), `aspect_correction`, `easter_egg`, `preset_locked`, `shuffle`.

Example:

```bash
./build/milk-ddp --ddp 192.168.1.50 \
  --preset-duration 20 --set beat_sensitivity=1.8 \
  --set hard_cut_enabled=true --set mesh_size=32x24 \
  --preset-path ./presets/modern
```

If no `--preset` and no `.milk` files are found, the idle logo preset is loaded so the process still produces a DDP stream.

## Container

Two images are kept: **Alpine** (`Dockerfile.alpine`, preferred for releases) and **Debian** (`Dockerfile.debian`). The root `Dockerfile` matches the Debian recipe for `docker build .` convenience; release tags and `make docker` set `:latest` to Alpine.

### Local build

```bash
make docker              # alpine (:latest) and debian
make docker-alpine       # preferred release image → :alpine and :latest
make docker-debian       # → :debian
```

### GHCR (release images)

Tagged releases push multi-arch (amd64 + arm64) images to GitHub Container Registry:

| Tag | Image |
|---|---|
| Preferred / newest | `ghcr.io/howels/milk-ddp:latest` |
| Version (Alpine) | `ghcr.io/howels/milk-ddp:vX.Y.Z` |
| Alpine explicitly | `ghcr.io/howels/milk-ddp:vX.Y.Z-alpine` |
| Debian | `ghcr.io/howels/milk-ddp:vX.Y.Z-debian` |

Per-architecture digests also exist as `…:vX.Y.Z-alpine-amd64`, `…-alpine-arm64`, `…-debian-amd64`, and `…-debian-arm64` (used to build the multi-arch manifests).

Package page: https://github.com/howels/milk-ddp/pkgs/container/milk-ddp

```bash
docker pull ghcr.io/howels/milk-ddp:latest
docker pull ghcr.io/howels/milk-ddp:v0.1.1
docker pull ghcr.io/howels/milk-ddp:v0.1.1-debian
```

### Run

```bash
docker run --rm --network host ghcr.io/howels/milk-ddp:latest \
  --software-gl --width 128 --height 128 --fps 30 \
  --ddp 192.168.1.50:4048 \
  --preset-path /usr/share/milk-ddp/presets \
  --audio sine
```

`--network host` is the usual way to reach a LAN WLED node from the container. Pulse capture needs `/run/user/$UID/pulse` (or the PipeWire socket) bind-mounted; sine and file sources do not. Hotplug still works inside the container as long as the Pulse/PipeWire socket stays mounted.

### Host GPU (DRM / Mesa)

Omit `--software-gl` and pass the host DRM nodes into the container. A
`hostPath` of `/dev/dri` alone is not enough under Podman: use
`--device=/dev/dri` (or kube-play `resources.limits.podman.io/device=/dev/dri`)
plus pod-level `supplementalGroups` for host `video` / `render` GIDs. Tags
≤`v0.1.3` bake `llvmpipe` ENV — set `MESA_LOADER_DRIVER_OVERRIDE=panfrost` (or
rebuild). Full procedure: [docs/container-gpu.md](docs/container-gpu.md).

MoonLight + milk-ddp kube-play examples (rootful and rootless, ports 8080 /
4049): [examples/podman/](examples/podman/).

Ship extra preset packs as a volume (do not bake third-party packs into the image unless their licence allows it):

```bash
docker run --rm --network host \
  -v /opt/presets/cream-of-the-crop:/presets:ro \
  ghcr.io/howels/milk-ddp:latest --software-gl --ddp 192.168.1.50 --preset-path /presets
```

GitHub Release assets are host binaries only (`milk-ddp-*-linux-{amd64,arm64}.tar.gz`). Pull containers from GHCR as above.

## Presets

### Shipped GPL-3.0 pack (64×64–256×256)

In-tree packs:

- `presets/milk-ddp-*.milk` / `presets/lowres/` — original **GPL-3.0-or-later** matrix presets (64×64–256×256)
- `presets/fractal/` — original **GPL** MilkDrop 2 fractals (classic, nature / landscape, zoom-rush dives)
- `presets/surfaces/` — original **GPL** waveform→texture mapped onto convex / concave / landscape surfaces
- `presets/neon/` — original **GPL** vivid neon grids, tubes, lasers, signage, circuit traces
- `presets/jelly/` — original **GPL** gelatinous relief / machine-code scrolls (Machine Code Jelly–inspired)
- `presets/rush/` — original **GPL** forward-zoom tunnels from waveform-driven geometry
- `presets/cellular/` — original **GPL** mercury puddles, Giger radial, heat-temper neon
- `presets/modern/` — **MIT** MilkDrop 2 / mock-3D selection (M0Rf30): Fractal Sanctum, hyperspace, nebulae, kaleidoscope

```bash
./build/milk-ddp --width 64 --height 64 \
  --preset-path ./presets/lowres --preset-duration 25 \
  --ddp 192.168.1.50:4048 --audio pulse

./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/fractal --switch-delay 40 \
  --ddp 192.168.1.50:4048 --audio pulse

./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/surfaces --switch-delay 40 \
  --ddp 192.168.1.50:4048 --audio pulse

./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/neon --switch-delay 35 \
  --ddp 192.168.1.50:4048 --audio pulse

./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/jelly --switch-delay 35 \
  --ddp 192.168.1.50:4048 --audio pulse

./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/rush --switch-delay 30 \
  --ddp 192.168.1.50:4048 --audio pulse

./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/cellular --switch-delay 35 \
  --ddp 192.168.1.50:4048 --audio pulse

./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/modern --switch-delay 45 \
  --ddp 192.168.1.50:4048 --audio pulse
```

Details: [`presets/README.md`](presets/README.md), [`presets/cellular/README.md`](presets/cellular/README.md), [`presets/rush/README.md`](presets/rush/README.md), [`presets/jelly/README.md`](presets/jelly/README.md), [`presets/neon/README.md`](presets/neon/README.md), [`presets/surfaces/README.md`](presets/surfaces/README.md), [`presets/fractal/README.md`](presets/fractal/README.md), [`presets/modern/README.md`](presets/modern/README.md).

CPU cost notes (software GL vs GPU, resolution, mesh): [`docs/PERFORMANCE.md`](docs/PERFORMANCE.md).

### Larger third-party packs (download separately)

Large Milkdrop collections are **not** vendored (size and third-party authorship). Clone them and pass `--preset-path` (recursive).

**Cream of the Crop** (recommended default for projectM):

```bash
git clone --depth 1 \
  https://github.com/projectM-visualizer/presets-cream-of-the-crop.git \
  ~/presets/cream-of-the-crop

./build/milk-ddp \
  --preset-path ~/presets/cream-of-the-crop \
  --ddp 192.168.1.50:4048 \
  --audio pulse
```

**Milkdrop texture pack** (many presets expect these textures):

```bash
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
| More packs | https://github.com/orgs/projectM-visualizer/repositories?q=presets |

External `.milk` files stay under their authors’ terms. See `THIRD_PARTY.md`.

## Continuous integration and releases

GitHub-compatible workflows live under `.github/workflows/`:

| Workflow | Trigger | Action |
|---|---|---|
| `ci.yml` | push / PR | Build and validate on amd64 and arm64; build Alpine and Debian images for both arches |
| `release.yml` | tag `v*` (must be on `main`); also `workflow_dispatch` | Attach amd64/arm64 host binary tarballs; push multi-arch images to `ghcr.io/howels/milk-ddp` (**Alpine** preferred: `:vX` / `:latest`; Debian `:vX-debian`) and link those pulls in the release notes. Re-pushing the same tag republishes. |
| `renovate.yml` | weekly cron (Monday 06:00 UTC) and `workflow_dispatch` | Self-hosted Renovate opens PRs for Actions, Docker base images, and the libprojectM FetchContent tag |

### Cutting a release

From a clean `main` tree (after commits are pushed or will be pushed by the script):

```bash
make release VERSION=v0.1.2
# equivalent: scripts/release.sh v0.1.2
```

`scripts/release.sh` runs `make validate`, keeps the CMake `project(… VERSION …)`
in sync with the tag, creates an annotated tag, pushes it to `origin`, and watches
the Release workflow until host binary tarballs are attached and GHCR images are
published. The workflow refuses tags whose commit is not reachable from `origin/main`.

Useful environment flags: `SKIP_VALIDATE=1`, `WATCH=0`, `RELEASE_ALLOW_DIRTY=1`.

To rebuild and republish an existing tag from current `main`:

```bash
REPUBLISH=1 make release VERSION=v0.1.2
```

That deletes the local and remote tag, recreates an annotated tag on `HEAD`,
force-pushes only that tag, and lets `release.yml` overwrite same-named release
assets and GHCR tags. Manual re-run without moving the tag: Actions → Release →
Run workflow → enter the tag name.

Manual first-time tag:

```bash
git tag -a v0.1.2 -m "v0.1.2"
git push origin v0.1.2
```

### Renovate

[`renovate.yml`](.github/workflows/renovate.yml) runs Renovate weekly against this
repository. [`renovate.json`](renovate.json) tracks:

- GitHub Actions used in workflows (including `renovatebot/github-action` itself)
- Docker base images in `Dockerfile`, `Dockerfile.alpine`, and `Dockerfile.debian`
- The libprojectM git tag in `CMakeLists.txt` / `Makefile` (`MILK_DDP_PROJECTM_GIT_TAG` / `vendor-projectm`)

**Prerequisite:** add a repository secret `RENOVATE_TOKEN` — a fine-grained PAT (or
GitHub App installation token) with permission to read the repo and open pull
requests (include `workflows` if Renovate should bump Actions that change workflow
files). Then run the Renovate workflow once via `workflow_dispatch`, or wait for
the Monday cron.

## Validate without a matrix or a display

```bash
make validate
```

`tests/validate.sh` starts `tests/ddp_listen.py` on a high UDP port, runs `milk-ddp --software-gl` for a few 32×32 frames, and checks that:

- each packet has a version-1 DDP header, RGB24 type `0x0B`, and sequence 1–15
- byte offsets reconstruct `width * height * 3` bytes
- the Push flag arrives on the last packet of each frame
- the last frame is not all zeros

A PPM of that frame is written to `/tmp/milk-ddp-last.ppm`.

## Mapping to a physical matrix

Pixels are sent row-major, left to right, top to bottom, RGB888. That matches a WLED 2D matrix with default serpentine **off** and the first LED at the top-left. If the panel is serpentine or rotated, set the matching 2D mapping in WLED rather than in this program.

## Licence

| Component | Licence |
|---|---|
| milk-ddp application (`src/`, `tests/`, build files) | **GPL-3.0-or-later** (`LICENSE`) |
| In-tree GPL presets (`presets/milk-ddp-*.milk`, `lowres/`, `fractal/`, `surfaces/`, `neon/`, `jelly/`, `rush/`, `cellular/`) | **GPL-3.0-or-later** |
| `presets/modern/` (M0Rf30 selection) | **MIT** |
| libprojectM (FetchContent / local / system) | **LGPL-2.1-or-later** — see `THIRD_PARTY.md` |
| External preset packs (Cream of the Crop, textures, …) | **Not shipped**; each pack’s own terms |

Distributing a binary that links libprojectM requires complying with both the GPL-3 for this program and the LGPL-2.1 obligations for libprojectM (source offer / relink rights). Release tarballs include `LICENSE`, `THIRD_PARTY.md`, and `BUILD_INFO.txt` naming the libprojectM tag used.
