#!/usr/bin/env python3
"""Synthetic marker_single stand-in for tests. Not an installed conversion."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

HELP = """
Usage: marker_single [OPTIONS] FPATH

  --mode [fast|accurate]
  --disable_ocr
  --output_format [markdown|json|html]
  --disable_tqdm
  --output_dir PATH

marker-pdf 2.0.0
"""


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--help" in argv or "-h" in argv:
        sys.stdout.write(HELP)
        return 0
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("fpath")
    parser.add_argument("--mode")
    parser.add_argument("--disable_ocr", action="store_true")
    parser.add_argument("--output_format")
    parser.add_argument("--disable_tqdm", action="store_true")
    parser.add_argument("--output_dir")
    parser.add_argument("--sleep", type=float, default=0.0)
    parser.add_argument("--fail", action="store_true")
    args, _unknown = parser.parse_known_args(argv)
    if args.sleep:
        time.sleep(args.sleep)
    if args.fail:
        sys.stderr.write("synthetic converter failure\n")
        return 2
    output_dir = Path(args.output_dir or ".")
    dest = output_dir / "original"
    dest.mkdir(parents=True, exist_ok=True)
    source = Path(args.fpath)
    markdown = dest / "original.md"
    markdown.write_text(
        "# Converted synthetic filing\n\n"
        f"Source name: {source.name}\n\n"
        "Greater China: Mainland China, Hong Kong, Taiwan\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
