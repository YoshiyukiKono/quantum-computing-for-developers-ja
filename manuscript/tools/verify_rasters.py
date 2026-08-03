from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageStat


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Check rasterized PDF pages for empty images.")
    parser.add_argument("directory", type=Path)
    parser.add_argument("--expected", type=int, required=True)
    args = parser.parse_args()

    paths = sorted(args.directory.glob("*.png"))
    empty: list[str] = []
    unreadable: list[str] = []
    for path in paths:
        try:
            with Image.open(path) as image:
                grayscale = image.convert("L")
                extrema = grayscale.getextrema()
                mean = ImageStat.Stat(grayscale).mean[0]
                if extrema == (255, 255) or mean > 254.99:
                    empty.append(path.name)
        except Exception:
            unreadable.append(path.name)

    print(f"RASTERS: {len(paths)}")
    print(f"EXPECTED: {args.expected}")
    print(f"EMPTY: {empty}")
    print(f"UNREADABLE: {unreadable}")
    if len(paths) != args.expected or empty or unreadable:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
