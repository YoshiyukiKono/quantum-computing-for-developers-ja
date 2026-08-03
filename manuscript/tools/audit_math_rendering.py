from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from build_pdf import inline_markup, latex_to_unicode


HERE = Path(__file__).resolve().parents[1]
LEFTOVER_COMMAND = re.compile(r"\\[A-Za-z]+")
INLINE_MATH = re.compile(r"(?<!\\)\$([^$\n]+?)(?<!\\)\$")


def manuscript_paths() -> list[Path]:
    config = json.loads((HERE / "book.json").read_text(encoding="utf-8"))
    entries = [chapter for part in config["parts"] for chapter in part["chapters"]]
    entries.extend(config["appendices"])
    entries.extend(config.get("backmatter", []))
    return [HERE / entry["path"] for entry in entries]


def math_fragments(path: Path) -> list[tuple[int, str]]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    fragments: list[tuple[int, str]] = []
    in_display = False
    display_start = 0
    display_buffer: list[str] = []
    in_math_fence = False
    fence_start = 0
    fence_buffer: list[str] = []

    for number, line in enumerate(lines, start=1):
        if line.startswith("```"):
            if in_math_fence:
                fragments.append((fence_start, "\n".join(fence_buffer)))
                fence_buffer.clear()
                in_math_fence = False
            elif line[3:].strip().partition(":")[0].lower() == "math":
                in_math_fence = True
                fence_start = number + 1
            continue
        if in_math_fence:
            fence_buffer.append(line)
            continue

        if line.strip() == "$$":
            if in_display:
                fragments.append((display_start, "\n".join(display_buffer)))
                display_buffer.clear()
                in_display = False
            else:
                in_display = True
                display_start = number + 1
            continue
        if in_display:
            display_buffer.append(line)
            continue

        fragments.extend((number, match.group(1)) for match in INLINE_MATH.finditer(line))

    return fragments


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    errors: list[str] = []
    regressions = {
        r"\rightarrow": "→",
        r"\Rightarrow": "⇒",
        r"\leftrightarrow": "↔",
        r"\infty": "∞",
        r"\left( x \right)": "( x )",
    }
    for source, expected in regressions.items():
        actual = latex_to_unicode(source)
        if actual != expected:
            errors.append(f"conversion regression: {source!r} -> {actual!r}; expected {expected!r}")

    inline_regressions = {
        "例えば、$1$に掛ける": "例えば、 1 に掛ける",
        "90°回転します": "90° 回転します",
        "量子`Python`コード": (
            "量子 <font name='BIZUDGothic' color='#123354' "
            "backColor='#DCEAF7'>Python</font> コード"
        ),
    }
    for source, expected in inline_regressions.items():
        actual = inline_markup(source)
        if actual != expected:
            errors.append(f"inline regression: {source!r} -> {actual!r}; expected {expected!r}")

    inline_math = inline_markup("複素数は$i$です")
    if "backColor" in inline_math or "#7C3E00" in inline_math or "#FFF0C2" in inline_math:
        errors.append(f"inline math decoration leaked into output: {inline_math!r}")

    fragment_count = 0
    for path in manuscript_paths():
        for line_number, fragment in math_fragments(path):
            fragment_count += 1
            rendered = latex_to_unicode(fragment)
            leftovers = LEFTOVER_COMMAND.findall(rendered)
            if leftovers:
                errors.append(
                    f"{path.relative_to(HERE)}:{line_number}: unconverted commands "
                    f"{sorted(set(leftovers))}: {rendered!r}"
                )
            if "arrow" in fragment and "arrow" in rendered:
                errors.append(
                    f"{path.relative_to(HERE)}:{line_number}: arrow command leaked as text: {rendered!r}"
                )

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)

    print(f"MATH_FRAGMENTS: {fragment_count}")
    print("MATH_RENDERING_AUDIT: OK")


if __name__ == "__main__":
    main()
