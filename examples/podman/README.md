# Podman kube play examples (MoonLight + milk-ddp)

| File | Podman store | Play |
|---|---|---|
| [moonlight-milkddp-rootful.yaml](moonlight-milkddp-rootful.yaml) | rootful (`sudo podman`); milk-ddp `v0.1.4` + host `/dev/dri` (Panfrost) | `sudo podman kube play … --network=host --replace` |
| [moonlight-milkddp-rootless.yaml](moonlight-milkddp-rootless.yaml) | rootless (user) | `podman kube play … --network=host --replace --userns=keep-id` then attach milk-ddp with `--group-add keep-groups` (see file header) |

Both use `hostNetwork: true`. Ports (all unprivileged):

| Port | Role |
|---|---|
| TCP **8080** | MoonLight HTTP UI |
| UDP **4048** | milk-ddp / WLED DDP default (`--ddp HOST` or `HOST:4048`) |
| UDP **4049** | Common MoonLight DDP listen port (examples target `127.0.0.1:4049`) |

**Host volumes** bind under `/srv/moonlight/` (shared path, not a home directory). Relative bind paths are unreliable with `podman kube play` (they depend on the play cwd), so the examples keep absolute paths:

```bash
sudo mkdir -p /srv/moonlight/MoonLight /srv/moonlight/sendspin-cpp-cli
sudo chown -R 1000:1000 /srv/moonlight          # rootful UID 1000
# or, for rootless:
sudo chown -R "$(id -u):$(id -g)" /srv/moonlight
```

| Host path | Role |
|---|---|
| `/srv/moonlight/MoonLight/` | MoonLight state |
| `/srv/moonlight/sendspin-cpp-cli` | sendspin-cpp-cli `--state-dir` |

`CAP_NET_RAW` on MoonLight does not require rootful Podman.

DRM / Mesa details: [../../docs/container-gpu.md](../../docs/container-gpu.md).
