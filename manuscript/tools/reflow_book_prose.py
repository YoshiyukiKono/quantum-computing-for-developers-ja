from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRS = (
    ROOT / "content" / "01-first-circuits",
    ROOT / "content" / "02-quantum-effects",
)
MAX_PARAGRAPH_LENGTH = 220


@dataclass
class Block:
    kind: str
    lines: list[str]

    @property
    def text(self) -> str:
        return "".join(part.strip() for part in self.lines)


def block_kind(line: str) -> str:
    stripped = line.strip()
    if stripped.startswith("#"):
        return "heading"
    if stripped == "---":
        return "rule"
    if stripped.startswith(">"):
        return "quote"
    if stripped.startswith("|"):
        return "table"
    if re.match(r"^(?:[-*+]\s|\d+[.)]\s)", stripped):
        return "list"
    return "paragraph"


def parse_blocks(text: str) -> list[Block]:
    lines = text.splitlines()
    blocks: list[Block] = []
    i = 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        stripped = lines[i].strip()
        if stripped.startswith("```"):
            block = [lines[i]]
            i += 1
            while i < len(lines):
                block.append(lines[i])
                if lines[i].strip().startswith("```"):
                    i += 1
                    break
                i += 1
            blocks.append(Block("fence", block))
            continue
        if stripped == "$$":
            block = [lines[i]]
            i += 1
            while i < len(lines):
                block.append(lines[i])
                if lines[i].strip() == "$$":
                    i += 1
                    break
                i += 1
            blocks.append(Block("math", block))
            continue

        kind = block_kind(lines[i])
        block = [lines[i]]
        i += 1
        while i < len(lines) and lines[i].strip() and block_kind(lines[i]) == kind:
            block.append(lines[i])
            i += 1
        blocks.append(Block(kind, block))
    return blocks


def smart_join(left: str, right: str) -> str:
    left = left.rstrip()
    right = right.lstrip()
    if not left:
        return right
    if not right:
        return left
    separator = " " if (
        (left[-1].isascii() and right[0].isascii())
        or left.endswith("**")
        or right.startswith("**")
    ) else ""
    return left + separator + right


def join_colon_phrase(left: str, right: str) -> str:
    stem = left.rstrip()[:-1].rstrip()
    if stem.startswith("この章で扱う") and stem.endswith("が"):
        stem = "この章では" + stem[len("この章で扱う") : -1] + "である"
    comma_leads = (
        "つまり",
        "例えば",
        "たとえば",
        "具体的には",
        "逆に",
        "そして",
        "そのため",
        "だから",
        "ここで",
        "一方で",
        "結論から言うと",
        "整理すると",
        "まとめると",
    )
    if stem.endswith(comma_leads):
        stem += "、"
    elif stem.endswith("答え"):
        stem += "は"
    elif stem.endswith(("は", "が", "を", "と", "なら", "すると", "では", "には", "こそ", "である")):
        pass
    else:
        stem += "、"
    return smart_join(stem, right)


def can_merge(left: Block, right: Block) -> bool:
    if left.kind != "paragraph" or right.kind != "paragraph":
        return False
    if left.text.startswith("(本書は、筆者が") or right.text.startswith("(本書は、筆者が"):
        return False
    if len(left.text) + len(right.text) > MAX_PARAGRAPH_LENGTH:
        return False
    return True


def reflow(text: str) -> tuple[str, int, int]:
    blocks = parse_blocks(text)
    colon_changes = 0
    merges = 0

    i = 0
    while i < len(blocks):
        block = blocks[i]
        if block.kind == "paragraph" and block.text.endswith("："):
            if i + 1 < len(blocks) and blocks[i + 1].kind == "paragraph":
                combined = join_colon_phrase(block.text, blocks[i + 1].text)
                blocks[i] = Block("paragraph", [combined])
                del blocks[i + 1]
                colon_changes += 1
                merges += 1
                continue
        i += 1

    i = 0
    while i + 1 < len(blocks):
        if can_merge(blocks[i], blocks[i + 1]):
            combined = smart_join(blocks[i].text, blocks[i + 1].text)
            blocks[i] = Block("paragraph", [combined])
            del blocks[i + 1]
            merges += 1
            continue
        i += 1

    rendered = "\n\n".join("\n".join(block.lines) for block in blocks).rstrip() + "\n"
    rendered = rendered.replace("これまでの回で", "これまでの章で")
    return rendered, colon_changes, merges


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Reflow fragmented blog prose into book paragraphs.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--samples", type=int, default=5)
    args = parser.parse_args()

    changed: list[tuple[Path, str, str, int, int]] = []
    for directory in DEFAULT_DIRS:
        for path in sorted(directory.glob("*.md")):
            original = path.read_text(encoding="utf-8")
            rendered, colon_changes, merges = reflow(original)
            if rendered != original:
                changed.append((path, original, rendered, colon_changes, merges))

    for path, original, rendered, colons, merges in changed[: args.samples]:
        old_lines = len(original.splitlines())
        new_lines = len(rendered.splitlines())
        print(
            f"{path.relative_to(ROOT)}: lines {old_lines}->{new_lines}, "
            f"colons {colons}, merges {merges}"
        )
        print("  BEFORE:", " | ".join(original.splitlines()[5:18]))
        print("  AFTER: ", " | ".join(rendered.splitlines()[5:14]))
    print(f"FILES: {len(changed)}")
    print(f"COLON_CHANGES: {sum(item[3] for item in changed)}")
    print(f"PARAGRAPH_MERGES: {sum(item[4] for item in changed)}")

    if args.write:
        for path, _, rendered, _, _ in changed:
            path.write_text(rendered, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
