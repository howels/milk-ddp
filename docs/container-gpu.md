# Host GPU (DRM / Mesa) inside the milk-ddp container

`milk-ddp` draws through EGL + OpenGL 3.3. With a host GPU, Mesa must open a DRM
render node under `/dev/dri` and load the matching Gallium driver (for example
`panfrost` on Mali Bifrost, `radeonsi` on AMD, `iris` / `crocus` on Intel).

A bind-mount of `/dev/dri` alone is not enough under Podman. The container also
needs a device-cgroup allow entry (what `podman run --device` adds) and the host
`video` / `render` group IDs on the process.

## What the host must provide

1. A render node, typically `/dev/dri/renderD128` (`ls -l /dev/dri`).
2. Kernel driver loaded (for example `panfrost` on Rockchip RK3568).
3. Process GIDs that match the device nodes. On Debian/Ubuntu those are usually
   `video` and `render`:

```bash
getent group video render
ls -ln /dev/dri
# example: card* mode 0660 gid=video; renderD* mode 0660 gid=render
```

Add the runtime user to both groups on the host if you run rootless.

Under `podman kube play`, put those GIDs on the **pod** `securityContext.supplementalGroups`
(not on the container). Container-level `supplementalGroups` is ignored, so the
process stays without `video`/`render` and Mesa gets `Permission denied` on
`/dev/dri` even when the nodes are mounted.

## Image contents

Release images ship Mesa DRI (`mesa-dri-gallium` on Alpine, `libgl1-mesa-dri` on
Debian), including `panfrost_dri.so` and the common desktop drivers. No host
Mesa libraries need to be bind-mounted.

Published tags through `v0.1.3` set:

```text
GALLIUM_DRIVER=llvmpipe
MESA_LOADER_DRIVER_OVERRIDE=llvmpipe
```

Those force software GL even when `/dev/dri` is usable. For GPU, set
`GALLIUM_DRIVER` / `MESA_LOADER_DRIVER_OVERRIDE` to the host driver (for example
`panfrost`) or rebuild from a tree that no longer bakes those `ENV` lines.
Empty-string overrides are unreliable. Prefer `--software-gl` only when you
intentionally want llvmpipe. A new published image is useful but not required
once the env overrides are set.

## podman run

```bash
# Host GIDs — substitute from getent
VIDEO_GID=$(getent group video | cut -d: -f3)
RENDER_GID=$(getent group render | cut -d: -f3)

podman run --rm --network=host \
  --device=/dev/dri \
  --group-add "$VIDEO_GID" \
  --group-add "$RENDER_GID" \
  --user 1000:1000 \
  -e GALLIUM_DRIVER=panfrost \
  -e MESA_LOADER_DRIVER_OVERRIDE=panfrost \
  -e MESA_GL_VERSION_OVERRIDE=3.3 \
  -e MESA_GLSL_VERSION_OVERRIDE=330 \
  -e LIBGL_ALWAYS_SOFTWARE=0 \
  -e HOME=/tmp \
  -e XDG_CACHE_HOME=/tmp/cache \
  ghcr.io/howels/milk-ddp:v0.1.4 \
  --preset-path /usr/share/milk-ddp/presets \
  --ddp 127.0.0.1:4048 \
  --audio sine
```

`--device=/dev/dri` creates the char devices inside the container and allows
them in the devices cgroup. `--group-add` supplies the host GIDs so mode `0660`
nodes are writable. Do not pass `--software-gl`.

Startup stderr should name the GPU driver, for example:

```text
GL Mesa / Mali-G52 r1 (Panfrost) / 3.3 (Core Profile) …
```

`llvmpipe` in that line means Mesa is still on the software path.

### Panfrost EGL_BAD_MATCH (NanoPi R3S / Mali Bifrost)

Panfrost often rejects a native OpenGL 3.3 core context. milk-ddp needs 3.3, so
set Mesa version overrides after selecting the Gallium driver:

```bash
-e GALLIUM_DRIVER=panfrost \
-e MESA_LOADER_DRIVER_OVERRIDE=panfrost \
-e MESA_GL_VERSION_OVERRIDE=3.3 \
-e MESA_GLSL_VERSION_OVERRIDE=330 \
```

Without the version overrides, EGL initialise can fail with `EGL_BAD_MATCH`
even when `/dev/dri` opens cleanly and `panfrost_dri.so` is loaded.

## podman kube play

`hostPath` of `/dev/dri` mounts the directory but does **not** add device-cgroup
rules. Use Podman’s CDI-style selector (Podman ≥ 5.x), which maps to `--device`.
Keep the process as UID 1000; grant DRM via pod-level groups, not `privileged`
or `runAsUser: 0`.

```yaml
spec:
  securityContext:
    runAsUser: 1000
    runAsGroup: 1000
    supplementalGroups:
      - 44    # video — from getent group video
      - 105   # render — from getent group render
  containers:
  - name: milk-ddp
    image: ghcr.io/howels/milk-ddp:latest
    args:
    - --preset-path
    - /usr/share/milk-ddp/presets
    - --ddp
    - 127.0.0.1:4048
    env:
    - name: HOME
      value: /tmp
    - name: XDG_CACHE_HOME
      value: /tmp/cache
    - name: GALLIUM_DRIVER
      value: panfrost
    - name: MESA_LOADER_DRIVER_OVERRIDE
      value: panfrost
    - name: LIBGL_ALWAYS_SOFTWARE
      value: "0"
    - name: MESA_GL_VERSION_OVERRIDE
      value: "3.3"
    - name: MESA_GLSL_VERSION_OVERRIDE
      value: "330"
    resources:
      limits:
        "podman.io/device=/dev/dri": 1
    securityContext:
      runAsUser: 1000
      runAsGroup: 1000
      privileged: false
    volumeMounts:
    - mountPath: /dev/dri
      name: dri
  volumes:
  - name: dri
    hostPath:
      path: /dev/dri
```

Empty-string Gallium overrides are unreliable; set the host driver name
explicitly (for example `panfrost`). See
`examples/podman/moonlight-milkddp-rootful.yaml` for the full working Pod.

`Permission denied` on `/dev/dri/card*` or `renderD*` is almost always missing
pod-level `supplementalGroups`, missing `podman.io/device=…`, or both.

### Rootless vs rootful

`CAP_NET_RAW` (MoonLight) does **not** require rootful Podman. In a user
namespace the capability is namespaced and works for the mapped root / UID.

Rootless DRM is the harder constraint: host GIDs `44` / `105` are outside the
default `subgid` range (`100000+`), so `supplementalGroups: [44, 105]` cannot
attach unless those GIDs are mapped or you use `keep-groups` with a process that
never calls `setgroups`. Rootful `kube play` with the pod `supplementalGroups`
above is the straightforward path for Panfrost on this host.

## Kubernetes (cluster)

Pass the render node with a device plugin or a privileged/`hostPath` pattern
your cluster already uses for DRM. Keep `supplementalGroups` set to the node’s
`video` and `render` GIDs (they can differ per node image). Clear the llvmpipe
`ENV` overrides as above. There is no `podman.io/device` key on stock Kubernetes;
that selector is Podman-only.

## Checklist when EGL still fails

| Symptom | Cause |
|---|---|
| `failed to open /dev/dri/…: Permission denied` | No `--device` / `podman.io/device`, or missing `supplementalGroups` |
| `GL … llvmpipe` with devices present | `GALLIUM_DRIVER` / `MESA_LOADER_DRIVER_OVERRIDE` still `llvmpipe`, or `--software-gl` |
| `EGL_BAD_MATCH` / eglInitialize fails with Panfrost loaded | Missing `MESA_GL_VERSION_OVERRIDE=3.3` (and GLSL 330) |
| `eglInitialize failed` with no DRI nodes in the container | Device not passed through |
| Works on host, fails in container, same user | Rootless user namespace dropped `video`/`render`; use rootful play or map those GIDs |

On the NanoPi R3S (RK3568 Mali Bifrost), confirm the host side first:

```bash
ls -l /dev/dri
# card1 + renderD128 owned by video/render, driver panfrost
cat /sys/class/drm/card1/device/uevent   # DRIVER=panfrost
```
