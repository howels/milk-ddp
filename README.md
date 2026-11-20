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

- CMake 3.21 or newer, a C++17 compiler, git
- `libegl1-mesa-dev`, `libgl1-mesa-dev`, Mesa DRI (`libgl1-mesa-dri`) for software GL
- Optional: `libpulse-dev` for `--audio pulse`

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc)"
```

CMake fetches libprojectM v4.1.8 and the playlist library, and links them statically into `build/milkdrop-ddp`.

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
| `--audio sine\|pulse\|file:PATH\|stdin` | PCM source (default `sine`) |
| `--sample-rate N` | For `sine` and `stdin` (default 44100) |
| `--frames N` | Exit after N frames |
| `--dump-ppm FILE` | Write the last RGB frame as binary PPM |
| `--software-gl` | Force Mesa software rasteriser |
| `--no-shuffle` | Playlist order instead of random |
| `--quiet` | Suppress status on stderr |
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

```bash
docker build -t milkdrop-ddp .
docker run --rm --network host milkdrop-ddp \
  --software-gl --width 128 --height 128 --fps 30 \
  --ddp 192.168.1.50:4048 \
  --preset-path /usr/share/milkdrop-ddp/presets \
  --audio sine
```

`--network host` is the usual way to reach a LAN WLED node from the container. Pulse capture needs `/run/user/$UID/pulse` (or the PipeWire socket) bind-mounted; sine and file sources do not.

Ship extra preset packs as a volume:

```bash
docker run --rm --network host \
  -v /opt/presets/cream-of-the-crop:/presets:ro \
  milkdrop-ddp --software-gl --ddp 192.168.1.50 --preset-path /presets
```

The Cream of the Crop pack is not vendored (thousands of files). Clone [presets-cream-of-the-crop](https://github.com/projectM-visualizer/presets-cream-of-the-crop) and pass `--preset-path`. Texture-heavy packs also need `--texture-path` pointing at [presets-milkdrop-texture-pack](https://github.com/projectM-visualizer/presets-milkdrop-texture-pack).

## Validate without a matrix or a display

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc)"
bash tests/validate.sh
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

Application code is MIT (see `LICENSE`). libprojectM is LGPL-2.1-or-later and is fetched at build time (tag v4.1.8).
