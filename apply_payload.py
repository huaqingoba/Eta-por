#!/usr/bin/env python3
"""Decode a base64(xz) payload uploaded through the GitHub web editor.

Pasting long text into GitHub's editor can silently reorder or truncate it.
This helper tolerates the "two halves swapped" failure mode and verifies the
result against an expected sha256 when one is supplied.

usage: apply_payload.py <b64-file> <out-file> [expected-sha256]
"""
import base64
import hashlib
import lzma
import sys


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return "".join(fh.read().split())


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: apply_payload.py <b64-file> <out-file> [expected-sha256]")
    src, dst = sys.argv[1], sys.argv[2]
    expected = sys.argv[3].lower() if len(sys.argv) > 3 else None

    data = load(src)
    half = len(data) // 2
    candidates = [("as-is", data), ("halves-swapped", data[half:] + data[:half])]

    errors = []
    for name, candidate in candidates:
        try:
            raw = lzma.decompress(base64.b64decode(candidate, validate=True))
        except Exception as exc:  # noqa: BLE001 - report and try the next shape
            errors.append(f"{name}: {exc}")
            continue
        digest = hashlib.sha256(raw).hexdigest()
        if expected and digest != expected:
            errors.append(f"{name}: sha mismatch {digest}")
            continue
        with open(dst, "wb") as fh:
            fh.write(raw)
        print(f"ok order={name} bytes={len(raw)} sha256={digest}")
        return
    sys.exit("cannot decode payload -> " + "; ".join(errors))


if __name__ == "__main__":
    main()
