from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from build_pdf import split_markdown_table_row


HERE = Path(__file__).resolve().parents[1]
SEPARATOR = re.compile(r"^:?-{2,}:?$")


def manuscript_paths() -> list[Path]:
    config = json.loads((HERE / "book.json").read_text(encoding="utf-8"))
    entries = [chapter for part in config["parts"] for chapter in part["chapters"]]
    entries.extend(config["appendices"])
    entries.extend(config.get("backmatter", []))
    return [HERE / entry["path"] for entry in entries]


def is_separator(row: str) -> bool:
    cells = split_markdown_table_row(row)
    return bool(cells) and all(SEPARATOR.fullmatch(cell.strip()) for cell in cells)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    errors: list[str] = []
    table_count = 0
    math_cell_count = 0
    escaped_pipe_count = 0

    parser_cases = {
        "| $|0〉$ | value |": ["$|0〉$", "value"],
        "| `left|right` | value |": ["`left|right`", "value"],
        r"| \|a\|² | value |": [r"\|a\|²", "value"],
    }
    for row, expected_cells in parser_cases.items():
        actual_cells = split_markdown_table_row(row)
        if actual_cells != expected_cells:
            errors.append(
                f"table parser case failed: {row!r} -> {actual_cells!r}; "
                f"expected {expected_cells!r}"
            )

    for path in manuscript_paths():
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        index = 0
        while index + 1 < len(lines):
            if "|" not in lines[index] or not is_separator(lines[index + 1]):
                index += 1
                continue

            table_count += 1
            expected = len(split_markdown_table_row(lines[index]))
            separator_columns = len(split_markdown_table_row(lines[index + 1]))
            if separator_columns != expected:
                errors.append(
                    f"{path.relative_to(HERE)}:{index + 2}: separator has "
                    f"{separator_columns} columns; header has {expected}"
                )

            row_index = index + 2
            while row_index < len(lines) and lines[row_index].strip() and "|" in lines[row_index]:
                row = lines[row_index]
                cells = split_markdown_table_row(row)
                if len(cells) != expected:
                    errors.append(
                        f"{path.relative_to(HERE)}:{row_index + 1}: row has "
                        f"{len(cells)} columns; expected {expected}: {row}"
                    )
                math_cell_count += sum(1 for cell in cells if "$" in cell)
                escaped_pipe_count += row.count(r"\|")
                row_index += 1
            index = row_index

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)

    print(f"TABLES: {table_count}")
    print(f"MATH_CELLS: {math_cell_count}")
    print(f"ESCAPED_PIPES: {escaped_pipe_count}")
    print("TABLE_AUDIT: OK")


if __name__ == "__main__":
    main()
