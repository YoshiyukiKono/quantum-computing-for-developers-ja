"""Run every book example in a fresh Python process."""

from __future__ import annotations

import os
import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    examples_dir = Path(__file__).resolve().parent
    manifest = json.loads((examples_dir / "manifest.json").read_text(encoding="utf-8"))
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    for entry in manifest:
        name = entry["file"]
        path = examples_dir / name
        print(f"RUN  {name}", flush=True)
        subprocess.run([sys.executable, str(path)], check=True, env=environment)
    print(f"PASS all {len(manifest)} examples")


if __name__ == "__main__":
    main()
