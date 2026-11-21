# CPU cost and efficiency

Measured on Mesa **llvmpipe** (software GL) with `--audio sine`, paced at 30 fps
(wall time ≈ frame count / fps). **User CPU** is the useful cost signal.

## Where time goes (per frame)

| Stage | Role | Cost driver |
|---|---|---|
| `projectm_opengl_render_frame` | Warp + composite shaders, blur pyramid, mesh | **Dominant** for MilkDrop 2 fractals / raymarch-style presets |
| `glReadPixels` + Y-flip | Copy RGB from GL → CPU for DDP | Scales with `width × height`; syncs the GL pipeline |
| DDP `send()` | UDP packets (≤1440 RGB bytes each) | Small at 64–256²; grows with pixel count |
| Audio `fill` + `pcm_add` | PCM into projectM | Negligible for sine; Pulse/ALSA is async |

`glFinish()` before readback was removed: `glReadPixels` already synchronises.
The flip buffer is reused across frames (no per-frame allocation).

## Benchmarks (llvmpipe, 60 frames @ 30 fps → ~2.1 s wall)

| Size | Preset | User CPU | ≈ ms/frame (user) | Notes |
|---|---|---:|---:|---|
| 64² | lowres spectrum | 0.20 s | ~3.3 | Easy |
| 128² | lowres spectrum | 0.28 s | ~4.7 | Easy |
| 128² | Fractal Sanctum | 0.72 s | ~12 | Comfortable |
| 128² | Kali Nebula | ~1.7 s / 60f* | ~28 | Heavy shader |
| 256² | lowres spectrum | 1.05 s / 120f* | ~8.8 | OK |
| 256² | Fractal Sanctum | 1.84–3.6 s* | ~30–60 | Often cannot hold 30 fps on CPU |

\*Exact user times vary with iteration count and blur samples; fractal / flythrough
presets dominate over mesh size.

`mesh_size` (warp mesh) is a **secondary** lever: at 128² Fractal Sanctum,
24×18 vs 64×48 changed user time only ~15–20%. Shader loops and resolution
matter more.

## Savings (largest first)

1. **Use a GPU** — omit `--software-gl` when an EGL/GBM or desktop GPU context
   is available. Fractal shaders move from CPU SIMD to the GPU; readback remains.
   Container hosts: pass `/dev/dri` via Podman `--device` (not only a bind mount)
   and clear baked `llvmpipe` env overrides — see [container-gpu.md](container-gpu.md).
2. **Lower resolution** — match the matrix (`--width` / `--height`). 128² is far
   cheaper than 256² for the same preset; WLED still maps the buffer.
3. **Prefer lighter presets on software GL** — `presets/lowres/` and simple
   modern scenes; keep heavy fractals / Kali / Hyperspace for GPU hosts.
4. **`--set mesh_size=24x18`** (or similar) — modest save on warp mesh fill.
5. **Lower `--fps`** — 15–20 fps is often enough on LED matrices and cuts render
   + readback rate linearly.
6. **`--transition-half-fps`** — soft cuts render both presets (~2× GPU). This
   paces at `fps/2` for `soft_cut_duration` and doubles PCM feed so wall-clock
   audio stays correct. Off by default; enable on Mali / LED hosts that hitch
   during blends. Tune length with `--set soft_cut_duration=1.5`.
7. **`--warm-presets` (default on for playlists)** — the pause *before* a soft
   cut is `Preset::Initialize()` compiling warp/comp GLSL on the GL thread.
   At startup milk-ddp hard-cuts through every playlist preset (1 frame each,
   no DDP/readback) and prints `shader cache i/n (pct%)` progress on stderr so
   Mesa can populate its on-disk shader cache. Use `--no-warm-presets` to skip.
   Keep `XDG_CACHE_HOME` on a persistent volume (not a tmpfs wiped each pod
   recreate) so the cache survives restarts.
8. **Avoid extra post-process in presets** — fewer `GetBlur*` taps and shorter
   fractal iteration caps (the in-tree `presets/fractal/` set uses moderate loops).

Not worth it for typical 64–256 matrices: SIMD Y-flip, packing RGB565, or
dropping DDP push frequency (WLED needs a full frame each update).

## Practical defaults

| Host | Suggested |
|---|---|
| Pi / NUC without useful GPU, 128² | `--software-gl --fps 20`, lowres or fractal pack |
| Desktop with GPU, 128–256² | no `--software-gl`, modern/fractal packs, `--fps 30` |
| Always | set `--width`/`--height` to the LED layout (e.g. 128×130 for 16640 LEDs) |
