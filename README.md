# milkdrop-ddp

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
make            # → build/milkdrop-ddp
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
| 1 | `-DMILKDROP_DDP_USE_SYSTEM_PROJECTM=ON` → `find_package(projectM4)` + `projectM4Playlist` | No |
| 2 | `-DMILKDROP_DDP_PROJECTM_SOURCE=/path/to/projectm` | No |
| 3 | `third_party/projectm/` present (see below) | No |
| 4 | FetchContent clone of the GitHub tag into `build/_deps/` | Yes, first configure only |

Default (priority 4) downloads from `https://github.com/projectM-visualizer/projectm.git` at tag `v4.1.8` and builds it as a static library into `build/milkdrop-ddp`.

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
cmake -S . -B build -DMILKDROP_DDP_PROJECTM_SOURCE=/opt/src/projectm
```

Use a distro / prefix install of libprojectM 4.x (headers + `libprojectM::projectM` / `libprojectM::playlist`):

```bash
make USE_SYSTEM_PROJECTM=1
# or:
cmake -S . -B build -DMILKDROP_DDP_USE_SYSTEM_PROJECTM=ON
```

If FetchContent already populated `build/_deps/projectm-src` on a machine with network, copy that tree (or the whole `build/_deps`) to an offline host and pass it as `MILKDROP_DDP_PROJECTM_SOURCE`, or set `FETCHCONTENT_FULLY_DISCONNECTED=ON` so CMake reuses the existing download without contacting GitHub.

CMake cache keys: `MILKDROP_DDP_PROJECTM_SOURCE`, `MILKDROP_DDP_USE_SYSTEM_PROJECTM`, `MILKDROP_DDP_PROJECTM_GIT_TAG`, `MILKDROP_DDP_PROJECTM_GIT_REPOSITORY`.

## Run

Point `--ddp` at the WLED controller. Enable DDP (or “Realtime”) on the device. The LED count on WLED must be at least `width * height`.

```bash
./build/milkdrop-ddp \
  --width 128 --height 128 --fps 30 \
  --ddp 192.168.1.50:4048 \
  --preset-path ./presets \
  --audio sine
```

Live capture from PulseAudio (PipeWire’s Pulse shim is enough):

```bash
./build/milkdrop-ddp --ddp 192.168.1.50 --audio pulse --preset-path ./presets
```

`--audio pulse` connects to Pulse’s default source. It does **not** exit if the source is missing at start: PCM is silence until a source appears. Source and server subscription events reopen the stream when a device is plugged in, the default source changes, or the previous source is removed.

`--audio alsa` opens ALSA’s `default` capture PCM. `--audio alsa:plughw:1,0` (or any other PCM name) selects a card directly. Missing devices are retried every 500 ms.

List Pulse and ALSA capture devices:

```bash
./build/milkdrop-ddp --list-audio
```

```bash
./build/milkdrop-ddp --audio pulse:alsa_input.usb-Device-00.analog-stereo …
./build/milkdrop-ddp --audio alsa:plughw:1,0 …
PULSE_SOURCE=alsa_input.usb-Device-00.analog-stereo ./build/milkdrop-ddp --audio pulse …
```

A 16-bit PCM WAV, looping:

```bash
./build/milkdrop-ddp --audio file:/path/to/track.wav --preset-path ./presets --ddp 192.168.1.50
```

Raw stereo s16le on stdin at `--sample-rate`:

```bash
ffmpeg -i track.mp3 -f s16le -ac 2 -ar 44100 - \
  | ./build/milkdrop-ddp --audio stdin --ddp 192.168.1.50 --preset-path ./presets
```

Headless / no GPU:

```bash
./build/milkdrop-ddp --software-gl --ddp 127.0.0.1:4048 --frames 10 --preset-path ./presets
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
| `--list-audio` | List Pulse and ALSA capture devices and exit |
| `--sample-rate N` | For `sine` and `stdin` (default 44100) |
| `--frames N` | Exit after N frames |
| `--dump-ppm FILE` | Write the last RGB frame as binary PPM |
| `--software-gl` | Force Mesa software rasteriser |
| `--no-shuffle` | Playlist order instead of random |
| `--quiet` | Suppress startup status and progress |
| `--progress` | Print a periodic frame counter on stderr |
| `--set KEY=VALUE` | projectM property (repeatable) |

`--set` keys: `beat_sensitivity`, `hard_cut_duration`, `hard_cut_enabled`, `hard_cut_sensitivity`, `soft_cut_duration`, `preset_duration`, `mesh_size` (`WxH`), `aspect_correction`, `easter_egg`, `preset_locked`, `shuffle`.

Example:

```bash
./build/milkdrop-ddp --ddp 192.168.1.50 \
  --set preset_duration=20 --set beat_sensitivity=1.8 \
  --set hard_cut_enabled=true --set mesh_size=32x24 \
  --preset-path ./presets
```

If no `--preset` and no `.milk` files are found, the idle logo preset is loaded so the process still produces a DDP stream.

## Container

Two images: Debian (`Dockerfile` / `Dockerfile.debian`) and a smaller Alpine musl image (`Dockerfile.alpine`).

```bash
make docker              # milkdrop-ddp:debian (:latest) and milkdrop-ddp:alpine
make docker-debian
make docker-alpine
```

```bash
docker run --rm --network host milkdrop-ddp:debian \
  --software-gl --width 128 --height 128 --fps 30 \
  --ddp 192.168.1.50:4048 \
  --preset-path /usr/share/milkdrop-ddp/presets \
  --audio sine
```

`--network host` is the usual way to reach a LAN WLED node from the container. Pulse capture needs `/run/user/$UID/pulse` (or the PipeWire socket) bind-mounted; sine and file sources do not. Hotplug still works inside the container as long as the Pulse/PipeWire socket stays mounted.

Ship extra preset packs as a volume (do not bake third-party packs into the image unless their licence allows it):

```bash
docker run --rm --network host \
  -v /opt/presets/cream-of-the-crop:/presets:ro \
  milkdrop-ddp:alpine --software-gl --ddp 192.168.1.50 --preset-path /presets
```

## Presets

### Shipped GPL-3.0 pack (64×64–256×256)

In-tree presets are original GPL-3.0-or-later works aimed at LED matrices from
**64×64 through 256×256**:

- `presets/milkdrop-ddp-*.milk` — first light / CI samples  
- `presets/lowres/` — twelve matrix-oriented presets (spectrum, bloom, spiral, tunnel, …)

```bash
./build/milkdrop-ddp --width 64 --height 64 \
  --preset-path ./presets/lowres --ddp 192.168.1.50:4048 --audio pulse
```

Details: [`presets/README.md`](presets/README.md).

### Larger third-party packs (download separately)

Large Milkdrop collections are **not** vendored (size and third-party authorship). Clone them and pass `--preset-path` (recursive).

**Cream of the Crop** (recommended default for projectM):

```bash
git clone --depth 1 \
  https://github.com/projectM-visualizer/presets-cream-of-the-crop.git \
  ~/presets/cream-of-the-crop

./build/milkdrop-ddp \
  --preset-path ~/presets/cream-of-the-crop \
  --ddp 192.168.1.50:4048 \
  --audio pulse
```

**Milkdrop texture pack** (many presets expect these textures):

```bash
git clone --depth 1 \
  https://github.com/projectM-visualizer/presets-milkdrop-texture-pack.git \
  ~/presets/textures

./build/milkdrop-ddp \
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
| `ci.yml` | push / PR | Build on Ubuntu, run `tests/validate.sh`, build Debian container, upload binary artifact |
| `release.yml` | tag `v*` | Build Linux tarball (binary + `LICENSE` + `THIRD_PARTY.md` + sample presets), Debian/Alpine image tarballs, GitHub Release |

Create a release:

```bash
git tag -a v0.1.0 -m "v0.1.0"
git push origin v0.1.0
```

### Renovate

[`renovate.json`](renovate.json) tracks GitHub Actions, Docker base images (`debian`, `alpine`), and the libprojectM git tag in `CMakeLists.txt` / `Makefile` (`MILKDROP_DDP_PROJECTM_GIT_TAG` / `vendor-projectm`). Enable the [Renovate GitHub App](https://github.com/apps/renovate) on the repository (or run Renovate in your own CI).

## Validate without a matrix or a display

```bash
make validate
```

`tests/validate.sh` starts `tests/ddp_listen.py` on a high UDP port, runs `milkdrop-ddp --software-gl` for a few 32×32 frames, and checks that:

- each packet has a version-1 DDP header, RGB24 type `0x0B`, and sequence 1–15
- byte offsets reconstruct `width * height * 3` bytes
- the Push flag arrives on the last packet of each frame
- the last frame is not all zeros

A PPM of that frame is written to `/tmp/milkdrop-ddp-last.ppm`.

## Mapping to a physical matrix

Pixels are sent row-major, left to right, top to bottom, RGB888. That matches a WLED 2D matrix with default serpentine **off** and the first LED at the top-left. If the panel is serpentine or rotated, set the matching 2D mapping in WLED rather than in this program.

## Licence

| Component | Licence |
|---|---|
| milkdrop-ddp application (`src/`, `tests/`, build files) | **GPL-3.0-or-later** (`LICENSE`) |
| In-tree presets (`presets/milkdrop-ddp-*.milk`) | **GPL-3.0-or-later** (original to this repo) |
| libprojectM (FetchContent / local / system) | **LGPL-2.1-or-later** — see `THIRD_PARTY.md` |
| External preset packs (Cream of the Crop, textures, …) | **Not shipped**; each pack’s own terms |

Distributing a binary that links libprojectM requires complying with both the GPL-3 for this program and the LGPL-2.1 obligations for libprojectM (source offer / relink rights). Release tarballs include `LICENSE`, `THIRD_PARTY.md`, and `BUILD_INFO.txt` naming the libprojectM tag used.
