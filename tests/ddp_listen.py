#!/usr/bin/env python3
"""Receive DDP UDP packets and reconstruct RGB frames.

WLED listens on UDP 4048. This process does the same so a headless
milk-ddp run can be checked without a matrix. Protocol layout is
the 10-byte header from http://www.3waylabs.com/ddp/ : version 1,
optional push bit, RGB24 type 0x0B, 32-bit big-endian byte offset,
16-bit big-endian length.
"""

from __future__ import annotations

import argparse
import socket
import sys

DDP_VER1 = 0x40
DDP_PUSH = 0x01
DDP_RGB24 = 0x0B
HEADER = 10


def parse_header(pkt: bytes) -> tuple[bool, int, int, int, bytes]:
    if len(pkt) < HEADER:
        raise ValueError(f"packet shorter than DDP header ({len(pkt)} bytes)")
    flags, seq, dtype, dest = pkt[0], pkt[1], pkt[2], pkt[3]
    offset = (pkt[4] << 24) | (pkt[5] << 16) | (pkt[6] << 8) | pkt[7]
    length = (pkt[8] << 8) | pkt[9]
    payload = pkt[HEADER:]
    if len(payload) != length:
        raise ValueError(f"payload {len(payload)} != header length {length}")
    if (flags & 0xC0) != DDP_VER1:
        raise ValueError(f"unexpected DDP version flags 0x{flags:02x}")
    if dtype != DDP_RGB24:
        raise ValueError(f"unexpected DDP data type 0x{dtype:02x} (want RGB24 0x0B)")
    if dest not in (1, 255):
        raise ValueError(f"unexpected DDP destination id {dest}")
    if seq == 0 or seq > 15:
        raise ValueError(f"DDP sequence {seq} is outside 1-15")
    return bool(flags & DDP_PUSH), offset, length, seq, payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4048)
    parser.add_argument("--frames", type=int, default=3)
    parser.add_argument("--width", type=int, default=32)
    parser.add_argument("--height", type=int, default=32)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--dump-ppm")
    parser.add_argument("--allow-black", action="store_true")
    args = parser.parse_args()

    expected = args.width * args.height * 3
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.bind, args.port))
    sock.settimeout(args.timeout)

    buf = bytearray(expected)
    filled = 0
    frames = 0
    last_rgb = bytes(buf)

    while frames < args.frames:
        try:
            pkt, _addr = sock.recvfrom(2048)
        except socket.timeout as exc:
            raise SystemExit(f"timed out after {frames} complete DDP frames") from exc
        push, offset, length, _seq, payload = parse_header(pkt)
        if offset + length > expected:
            raise SystemExit(
                f"DDP offset {offset}+{length} exceeds {args.width}x{args.height} RGB ({expected} bytes)"
            )
        buf[offset : offset + length] = payload
        filled = max(filled, offset + length)
        if push:
            if filled < expected:
                raise SystemExit(f"push with incomplete frame ({filled}/{expected} bytes)")
            last_rgb = bytes(buf)
            frames += 1
            filled = 0
            buf[:] = b"\x00" * expected

    nonzero = sum(1 for b in last_rgb if b)
    print(
        f"ok frames={frames} pixels={args.width}x{args.height} "
        f"last_nonzero_bytes={nonzero}/{expected}",
        flush=True,
    )
    if args.dump_ppm:
        with open(args.dump_ppm, "wb") as fh:
            fh.write(f"P6\n{args.width} {args.height}\n255\n".encode("ascii"))
            fh.write(last_rgb)
    if nonzero == 0 and not args.allow_black:
        print("last reconstructed frame was all zeros", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
