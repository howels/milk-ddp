# Forward-rush waveform history presets (GPL-3.0-or-later)

Classic MilkDrop zoom-trail mechanism:

1. Warp moves the previous frame away from the origin without blur: radial
   zoom from the centre, or scroll away from a horizon / canyon centre-line
   so each stroke stays a distinct ridge.
2. Custom waves paint a fresh high-contrast spectrum / waveform stroke.
3. Those strokes accumulate as parallel overlays marching toward the edges,
   forming a screen-spanning texture (mountain contours, cloud bands).

Comp only colour-grades and hardens ridge contrast. Prefer **128×128+**.
No MilkDrop 3 `get_fft()`. Regenerate:

```bash
python3 scripts/gen_rush_presets.py
```

| File | Motif |
|---|---|
| `01-spectrum-ring-tunnel.milk` | Polar spectrum rings from centre |
| `02-waveform-star-rush.milk` | Star-shaped waveform history |
| `03-hex-grid-tunnel.milk` | Lattice from polar waveform overlays |
| `04-diamond-pulse-rush.milk` | Diamond-leaning polar trails |
| `05-radial-spoke-rush.milk` | Dense radial waveform history |
| `06-triangle-chevron-rush.milk` | Chevron-biased waveform overlays |
| `07-square-grid-tunnel.milk` | Boxed polar waveform history |
| `08-waveform-petal-rush.milk` | Petal / multi-lobe overlays |
| `09-flyover-terrain.milk` | Mountain ridges from horizon spectrum |
| `10-under-cloud-canopy.milk` | Cloud bands from horizon spectrum |
| `11-canyon-flythrough.milk` | Canyon walls from side spectrum |
| `12-cloud-street-dive.milk` | Cloud streets from horizon bands |

```bash
./build/milk-ddp --width 128 --height 128 \
  --preset-path ./presets/rush --switch-delay 30 \
  --ddp 192.168.1.50:4048 --audio pulse
```

Licence: GPL-3.0-or-later (same as `../LICENSE`).
