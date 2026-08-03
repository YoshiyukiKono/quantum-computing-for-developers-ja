"""Audit fenced blocks and enforce the manuscript's code classification rules."""

from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT = ROOT / "manuscript"
EXAMPLES = ROOT / "examples"
EXECUTABLE_LANGUAGES = {
    "python", "py", "bash", "sh", "shell", "powershell", "ps1",
    "javascript", "js", "typescript", "ts", "java", "c", "cpp",
    "csharp", "cs", "go", "rust", "ruby", "php", "sql",
}
ALLOWED_LANGUAGES = EXECUTABLE_LANGUAGES | {"", "text", "math"}
CODE_IN_UNTYPED = re.compile(
    r"(?m)^(?:from\s+\w+\s+import|import\s+\w+|def\s+\w+|class\s+\w+|"
    r"(?:qc|circuit)\.\w+\s*\()"
)


@dataclass(frozen=True)
class Block:
    path: Path
    line: int
    language: str
    filename: str
    body: str

    @property
    def kind(self) -> str:
        if self.language == "math":
            return "math"
        if self.language in EXECUTABLE_LANGUAGES:
            return "executable" if self.filename else "snippet"
        return "text"


def source_paths() -> list[Path]:
    paths = sorted((MANUSCRIPT / "content").rglob("*.md"))
    paths.extend([
        MANUSCRIPT / "appendices" / "a01-qiskit-setup.md",
        MANUSCRIPT / "appendices" / "a02-classical-and-quantum-gates.md",
    ])
    return paths


def parse_blocks(path: Path) -> list[Block]:
    blocks: list[Block] = []
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    opening: tuple[int, str, str] | None = None
    body: list[str] = []
    for line_number, line in enumerate(lines, start=1):
        if line.startswith("```"):
            if opening is None:
                info = line[3:].strip()
                language, separator, filename = info.partition(":")
                opening = (
                    line_number,
                    language.lower().strip(),
                    filename.strip() if separator else "",
                )
                body = []
            else:
                start, language, filename = opening
                blocks.append(Block(path, start, language, filename, "\n".join(body)))
                opening = None
                body = []
        elif opening is not None:
            body.append(line)
    if opening is not None:
        raise AssertionError(f"{path.relative_to(ROOT)}:{opening[0]}: unclosed fence")
    return blocks


def main() -> None:
    blocks = [block for path in source_paths() for block in parse_blocks(path)]
    errors: list[str] = []
    for block in blocks:
        location = f"{block.path.relative_to(ROOT)}:{block.line}"
        if block.language not in ALLOWED_LANGUAGES:
            errors.append(f"{location}: unknown fence language {block.language!r}")
        if block.filename:
            if block.language not in EXECUTABLE_LANGUAGES:
                errors.append(f"{location}: filename requires a code language")
            if Path(block.filename).name != block.filename:
                errors.append(f"{location}: show only a basename, not a path")
            if not (EXAMPLES / block.filename).is_file():
                errors.append(f"{location}: examples/{block.filename} does not exist")
        if block.language in {"python", "py"}:
            try:
                ast.parse(block.body)
            except SyntaxError as exc:
                errors.append(f"{location}: invalid Python snippet ({exc.msg})")
        if block.language == "" and CODE_IN_UNTYPED.search(block.body):
            errors.append(f"{location}: code-like content in an untyped fence")

    counts = Counter(block.kind for block in blocks)
    print(
        "BLOCKS "
        + " ".join(f"{kind}={counts[kind]}" for kind in ("executable", "snippet", "text", "math"))
    )
    print("APPENDIX_C excluded pending author review")
    if errors:
        raise AssertionError("\n".join(errors))
    print(f"PASS classified {len(blocks)} fenced blocks")


if __name__ == "__main__":
    main()
