#!/usr/bin/env python3
"""Build the deterministic resume evidence index from the master profile."""

from __future__ import annotations

import argparse
from pathlib import Path

from resume_lib import DEFAULT_INDEX, DEFAULT_MASTER, build_evidence_index, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", type=Path, default=DEFAULT_MASTER)
    parser.add_argument("--output", type=Path, default=DEFAULT_INDEX)
    args = parser.parse_args()
    index = build_evidence_index(args.master)
    write_json(args.output, index)
    bullet_count = sum(len(item["bullets"]) for item in index["items"])
    print(f"PASS: wrote {args.output}")
    print(f"items={len(index['items'])} bullets={bullet_count} source_sha256={index['source_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

