from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
ENDING = re.compile(
    r"^(?:です|でした|ます|ません|になります|となります|ということです|"
    r"なのです|のです|ではありません|だけです|を意味します|と呼びます)[。！？]?$"
)
BRIDGE = re.compile(r"^(?:は|が|を|と|に|の|から)$")
STRUCTURAL = re.compile(
    r"^(?:#{1,6}\s|[-*+]\s|\d+[.)]\s|[①-⑳]\s|[→←]|>|\||```|~~~|\$\$|---+$|<!--)"
)


def line_kinds(lines: list[str]) -> list[str]:
    kinds: list[str] = []
    in_code = False
    in_math = False
    for line in lines:
        value = line.strip()
        if value.startswith(("```", "~~~")):
            kinds.append("fence")
            in_code = not in_code
            continue
        if not in_code and value == "$$":
            kinds.append("math")
            in_math = not in_math
            continue
        if in_code:
            kinds.append("fence")
        elif in_math:
            kinds.append("math")
        elif not value:
            kinds.append("blank")
        elif STRUCTURAL.match(value) or (value.startswith("$") and value.endswith("$")):
            kinds.append("structural")
        else:
            kinds.append("prose")
    return kinds


def adjacent(kinds: list[str], start: int, step: int) -> int | None:
    index = start + step
    while 0 <= index < len(kinds) and kinds[index] == "blank":
        index += step
    return index if 0 <= index < len(kinds) else None


def join(left: str, right: str) -> str:
    left = left.rstrip()
    right = right.lstrip()
    if not left or not right:
        return left + right
    if left.endswith("**") or right.startswith("**"):
        return left + " " + right
    return left + right


def normalize(text: str) -> tuple[str, list[tuple[int, str, str]]]:
    lines = text.splitlines()
    kinds = line_kinds(lines)
    candidates: list[tuple[str, int, int, int | None]] = []

    for index, line in enumerate(lines):
        if kinds[index] != "prose":
            continue
        value = line.strip()
        previous = adjacent(kinds, index, -1)
        following = adjacent(kinds, index, 1)
        if (
            ENDING.fullmatch(value)
            and previous is not None
            and kinds[previous] == "prose"
            and not re.search(r"[。！？!?]$", lines[previous].strip())
        ):
            candidates.append(("ending", index, previous, None))
        elif (
            BRIDGE.fullmatch(value)
            and previous is not None
            and following is not None
            and kinds[previous] == "prose"
            and kinds[following] == "prose"
        ):
            candidates.append(("bridge", index, previous, following))

    changes: list[tuple[int, str, str]] = []
    for mode, index, previous, following in reversed(candidates):
        if mode == "ending":
            before = f"{lines[previous]} / {lines[index]}"
            merged = join(lines[previous].strip(), lines[index].strip())
            lines[previous : index + 1] = [merged]
        else:
            assert following is not None
            before = f"{lines[previous]} / {lines[index]} / {lines[following]}"
            merged = join(join(lines[previous].strip(), lines[index].strip()), lines[following].strip())
            lines[previous : following + 1] = [merged]
        changes.append((previous + 1, before, merged))

    return "\n".join(lines).rstrip() + "\n", list(reversed(changes))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Merge unambiguous prose-only sentence fragments.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--samples", type=int, default=80)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()

    changed: list[tuple[Path, str]] = []
    all_changes: list[tuple[Path, int, str, str]] = []
    for path in sorted(CONTENT.rglob("*.md")):
        original = path.read_text(encoding="utf-8")
        normalized, changes = normalize(original)
        if changes:
            changed.append((path, normalized))
            all_changes.extend((path, line, before, after) for line, before, after in changes)

    for path, line, before, after in all_changes[args.offset : args.offset + args.samples]:
        print(f"{path.relative_to(ROOT)}:{line}\n  - {before}\n  + {after}")
    print(f"FILES: {len(changed)}")
    print(f"CHANGES: {len(all_changes)}")

    if args.write:
        for path, normalized in changed:
            path.write_text(normalized, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
