"""Check the executable-example manifest and manuscript references."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = ROOT / "examples"
MANIFEST_PATH = EXAMPLES_DIR / "manifest.json"
LEGACY_PATTERNS = {
    "removed qiskit.Aer import": re.compile(r"from\s+qiskit\s+import\s+Aer(?:\s|,|$)"),
    "removed qiskit.execute call": re.compile(r"\bexecute\s*\("),
}


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    files = [entry["file"] for entry in manifest]
    if len(files) != len(set(files)):
        raise AssertionError("manifest contains duplicate example filenames")

    for entry in manifest:
        example_path = EXAMPLES_DIR / entry["file"]
        manuscript_path = ROOT / entry["manuscript"]
        source = example_path.read_text(encoding="utf-8")
        compile(source, str(example_path), "exec")

        manuscript = manuscript_path.read_text(encoding="utf-8")
        reference = f"examples/{entry['file']}"
        if reference not in manuscript:
            raise AssertionError(f"missing manuscript reference: {reference}")

    manuscript_paths = sorted((ROOT / "manuscript" / "content").rglob("*.md"))
    manuscript_paths += [
        ROOT / "manuscript" / "appendices" / "a01-qiskit-setup.md",
        ROOT / "manuscript" / "appendices" / "a02-classical-and-quantum-gates.md",
    ]
    for path in manuscript_paths:
        text = path.read_text(encoding="utf-8")
        for label, pattern in LEGACY_PATTERNS.items():
            if pattern.search(text):
                raise AssertionError(f"{path.relative_to(ROOT)}: {label}")

    print(f"PASS manifest and manuscript references for {len(manifest)} examples")


if __name__ == "__main__":
    main()
