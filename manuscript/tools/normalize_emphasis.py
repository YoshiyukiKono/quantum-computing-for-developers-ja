from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = (ROOT / "content", ROOT / "appendices")
QUOTE_RE = re.compile(r"^>\s?(.*)$")
STRUCTURAL_RE = re.compile(r"^(?:[-*+]\s|\d+[.)]\s|#{1,6}\s|```|\||\$\$)")
CONTINUATION_RE = re.compile(
    r"^(?:です|でした|である|となる|になります|になり|を意味|を表|を指|を作|を持|"
    r"と呼|という|に相当|に対応|が重要|が基本|が本質|こそ|なので|のこと)"
)
TERMINAL_RE = re.compile(r"[。！？!?]$")


def join_fragments(parts: list[str]) -> str:
    result = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if part in {"↓", "→"}:
            result = result.rstrip() + " → "
            continue
        if result and result[-1].isascii() and part[0].isascii():
            result += " "
        result += part
    return result


def is_plain_continuation(line: str) -> bool:
    stripped = line.strip()
    if not stripped or STRUCTURAL_RE.match(stripped) or stripped.startswith(">"):
        return False
    return bool(CONTINUATION_RE.match(stripped))


def bold(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("**") and stripped.endswith("**") and len(stripped) >= 4:
        return stripped
    # The whole former callout becomes one emphasis span, so remove nested spans.
    stripped = stripped.replace("**", "")
    return f"**{stripped}**"


def normalize(text: str) -> tuple[str, list[tuple[int, str, str]]]:
    lines = text.splitlines()
    output: list[str] = []
    changes: list[tuple[int, str, str]] = []
    in_fence = False
    i = 0

    while i < len(lines):
        line = lines[i]
        if re.match(r"^\s*```", line):
            in_fence = not in_fence
            output.append(line)
            i += 1
            continue

        quote_match = QUOTE_RE.match(line)
        if not in_fence and quote_match:
            quote_end = i
            quote_parts: list[str] = []
            while quote_end < len(lines):
                match = QUOTE_RE.match(lines[quote_end])
                if not match:
                    break
                quote_parts.append(match.group(1))
                quote_end += 1
            quote = join_fragments(quote_parts)
            is_complex = any(
                not part.strip() or STRUCTURAL_RE.match(part.strip())
                for part in quote_parts
            )
            if (
                quote.startswith("編集元:")
                or not quote
                or is_complex
                or STRUCTURAL_RE.match(quote)
            ):
                output.extend(lines[i:quote_end])
            else:
                replacement = bold(quote)
                output.append(replacement)
                output.append("")
                changes.append((i + 1, line.strip(), replacement))
            i = quote_end
            while i < len(lines) and not lines[i].strip():
                i += 1
            continue

        if in_fence or not line.rstrip().endswith("："):
            output.append(line)
            i += 1
            continue

        quote_start = i + 1
        while quote_start < len(lines) and not lines[quote_start].strip():
            quote_start += 1
        if quote_start >= len(lines) or not QUOTE_RE.match(lines[quote_start]):
            output.append(line)
            i += 1
            continue

        quote_end = quote_start
        quote_parts: list[str] = []
        while quote_end < len(lines):
            match = QUOTE_RE.match(lines[quote_end])
            if not match:
                break
            quote_parts.append(match.group(1))
            quote_end += 1

        quote = join_fragments(quote_parts)
        if not quote or STRUCTURAL_RE.match(quote):
            output.append(line)
            i += 1
            continue

        next_line = quote_end
        while next_line < len(lines) and not lines[next_line].strip():
            next_line += 1

        intro = line.rstrip()[:-1].rstrip()
        replacement = f"{intro} {bold(quote)}"
        consumed_to = quote_end
        if (
            not TERMINAL_RE.search(quote)
            and next_line < len(lines)
            and is_plain_continuation(lines[next_line])
        ):
            replacement += f" {lines[next_line].strip()}"
            consumed_to = next_line + 1

        output.append(replacement)
        output.append("")
        changes.append((i + 1, line.strip(), replacement))
        i = consumed_to
        while i < len(lines) and not lines[i].strip():
            i += 1

    return "\n".join(output).rstrip() + "\n", changes


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Convert emphasis blockquotes into inline or standalone bold prose."
    )
    parser.add_argument("--write", action="store_true", help="write changes to source files")
    parser.add_argument("--samples", type=int, default=20, help="number of examples to print")
    args = parser.parse_args()

    all_changes: list[tuple[Path, int, str, str]] = []
    changed_files: list[tuple[Path, str]] = []
    for source_dir in SOURCE_DIRS:
        for path in sorted(source_dir.rglob("*.md")):
            original = path.read_text(encoding="utf-8")
            normalized, changes = normalize(original)
            if not changes:
                continue
            changed_files.append((path, normalized))
            all_changes.extend((path, line, before, after) for line, before, after in changes)

    for path, line, before, after in all_changes[: args.samples]:
        relative = path.relative_to(ROOT)
        print(f"{relative}:{line}\n  - {before}\n  + {after}")
    print(f"FILES: {len(changed_files)}")
    print(f"CHANGES: {len(all_changes)}")

    if args.write:
        for path, normalized in changed_files:
            path.write_text(normalized, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
