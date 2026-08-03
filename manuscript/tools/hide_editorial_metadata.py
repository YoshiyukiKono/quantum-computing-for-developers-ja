from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = (ROOT / "content", ROOT / "appendices")
SOURCE_LINE = re.compile(r"^>\s*編集元:\s*(.+)$", re.MULTILINE)


def hide_metadata(text: str) -> tuple[str, int]:
    return SOURCE_LINE.subn(r"<!-- 編集元: \1 -->", text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Keep editorial source metadata in Markdown while hiding it from rendered output."
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    changes: list[tuple[Path, str, int]] = []
    for source_dir in SOURCE_DIRS:
        for path in sorted(source_dir.rglob("*.md")):
            original = path.read_text(encoding="utf-8")
            normalized, count = hide_metadata(original)
            if count:
                changes.append((path, normalized, count))

    for path, _, count in changes:
        print(f"{path.relative_to(ROOT)}: {count}")
    print(f"FILES: {len(changes)}")
    print(f"CHANGES: {sum(count for _, _, count in changes)}")

    if args.write:
        for path, normalized, _ in changes:
            path.write_text(normalized, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
