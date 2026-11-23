#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 milk-ddp contributors
# Render a few frames with Mesa software GL and prove a DDP stream arrives
# on localhost. No GPU and no window system are required.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${MILK_DDP_BIN:-${ROOT}/build/milk-ddp}"
LISTEN="${ROOT}/tests/ddp_listen.py"
PORT="${DDP_TEST_PORT:-14048}"
WIDTH=32
HEIGHT=32
FRAMES=4

if [[ ! -x "${BIN}" ]]; then
  echo "missing binary: ${BIN} (configure and build first)" >&2
  exit 1
fi

python3 "${LISTEN}" --bind 127.0.0.1 --port "${PORT}" --width "${WIDTH}" --height "${HEIGHT}" \
  --frames "${FRAMES}" --timeout 60 --dump-ppm /tmp/milk-ddp-last.ppm &
LISTENER_PID=$!
cleanup() {
  kill "${LISTENER_PID}" 2>/dev/null || true
}
trap cleanup EXIT
sleep 0.3

GALLIUM_DRIVER=llvmpipe MESA_LOADER_DRIVER_OVERRIDE=llvmpipe \
  "${BIN}" \
  --software-gl \
  --width "${WIDTH}" --height "${HEIGHT}" --fps 15 --frames "${FRAMES}" \
  --ddp "127.0.0.1:${PORT}" \
  --audio sine \
  --preset-path "${ROOT}/presets" \
  --preset "${ROOT}/presets/milk-ddp-bars.milk" \
  --set beat_sensitivity=1.5 \
  --quiet

wait "${LISTENER_PID}"
trap - EXIT
echo "DDP stream validated without a hardware display (see /tmp/milk-ddp-last.ppm)"
