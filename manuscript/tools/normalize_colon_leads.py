from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = (ROOT / "content", ROOT / "appendices")
UNSAFE_LEADS = {"よくある誤解"}

# These constructs intentionally keep the colon: it introduces a block rather
# than a prose sentence.
STRUCTURAL = re.compile(
    r"^(?:#{1,6}\s|[-*+]\s|\d+[.)]\s|[①-⑳]|>|\||```|~~~|\$\$|---+$|<!--|\[(?:OK|NG)\])"
)
FRAGMENT_LEAD = re.compile(r"^(?:(?:は|が|を|に|で|と|の|か)|ため)")
CONTINUATION = re.compile(
    r"^(?:は|が|を|に|で|と|の|から|だけ|こと|という|して|させ|"
    r"です|でした|になります|になり|と呼び|でき|必要|が必要|を扱|を使|を意味)"
)
SENTENCE_END = re.compile(r"[。！？!?]$")
TRANSITION_END = (
    "つまり",
    "例えば",
    "たとえば",
    "ここで",
    "そして",
    "さらに",
    "一方",
    "逆に",
    "しかし",
    "だから",
    "したがって",
    "すると",
    "そこで",
    "実際",
    "実は",
    "なぜなら",
    "まとめると",
    "整理すると",
)
DIRECT_END = ("は", "が", "を", "に", "の", "では", "には", "とは", "から")
LABEL_REPLACEMENTS = {
    "テーマ": "テーマは",
    "答え": "答えは",
    "内容": "内容は",
    "特徴": "特徴は",
    "役割": "役割は",
    "理由": "理由は",
    "目的": "目的は",
    "ポイント": "ポイントは",
    "意味": "意味は",
    "イメージ": "イメージとしては",
    "結果": "結果として",
    "定義": "定義は",
    "直感": "直感的には",
    "例": "例えば、",
    "重要な事実": "重要な事実は",
    "唯一の例外": "唯一の例外は",
    "よくある誤解": "よくある誤解は",
    "重要な現実": "重要な現実は",
    "重要なポイント": "重要なポイントは",
    "対象は最も基本的な例": "対象は",
    "利点": "利点は",
    "現時点の整理": "現時点では、",
    "名前の由来は、物理学者": "名前の由来となった物理学者は",
    "一般的な段階": "一般的な段階として、",
    "まず最も基本的な誤り訂正": "まず扱う最も基本的な誤りは",
    "まず結論": "まず結論として、",
    "現在の予測": "現在の予測では、",
    "これまでに扱った": "これまでに扱った",
    "代表例": "代表例は",
    "測定ベース量子計算": "測定ベース量子計算とは",
    "ここで重要": "ここで重要なのは",
}


def is_plain_body(line: str) -> bool:
    value = line.strip()
    if not value or STRUCTURAL.match(value) or value.endswith("："):
        return False
    # A standalone inline formula is also a displayed object, not prose.
    if value.startswith("$") and value.endswith("$"):
        return False
    return True


def emphasize(value: str) -> str:
    """Bold the payload while leaving sentence punctuation outside bold."""
    value = value.strip()
    match = re.match(r"^(.*?)([。！？!?])?$", value)
    assert match
    core, punctuation = match.group(1), match.group(2) or ""
    if core.startswith("**") and core.endswith("**") and core.count("**") == 2:
        emphasized = core
    else:
        emphasized = f"**{core.replace('**', '')}**"
    return emphasized + punctuation


def normalize_lead(value: str, payload: str) -> str:
    stem = value.rstrip()[:-1].rstrip()
    if SENTENCE_END.search(payload):
        sentence_labels = {
            "重要な事実": "重要な事実として、",
            "重要な現実": "重要な現実として、",
            "重要なポイント": "重要なポイントとして、",
            "よくある誤解": "よくある誤解ですが、",
            "ここで重要": "ここで重要な点として、",
        }
        if stem in sentence_labels:
            return sentence_labels[stem]
    if stem in LABEL_REPLACEMENTS:
        replacement = LABEL_REPLACEMENTS[stem]
        return replacement if replacement.endswith("、") else replacement + " "
    if stem.endswith(("です", "ます", "でした", "ません")):
        return stem + "。"
    if stem.endswith(TRANSITION_END):
        return stem + "、"
    if stem.endswith(
        DIRECT_END
        + ("な", "単に", "代わりに", "ここから", "実際には", "理論的には", "必ず", "すべて", "でも", "も", "ている")
    ):
        return stem + " "
    # Conditional and connective clauses read naturally with a comma.
    return stem + "、"


def next_nonblank(lines: list[str], start: int) -> int | None:
    index = start
    while index < len(lines) and not lines[index].strip():
        index += 1
    return index if index < len(lines) else None


def normalize(text: str) -> tuple[str, list[tuple[int, str, str]]]:
    lines = text.splitlines()
    candidates: list[tuple[int, int, int | None]] = []
    in_code = False
    in_math = False

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            in_code = not in_code
            continue
        if not in_code and stripped == "$$":
            in_math = not in_math
            continue
        if in_code or in_math or not line.rstrip().endswith("："):
            continue
        lead_stem = line.rstrip()[:-1].strip()
        if "**" in lead_stem or FRAGMENT_LEAD.match(lead_stem) or lead_stem in UNSAFE_LEADS:
            continue

        payload_index = next_nonblank(lines, index + 1)
        if payload_index is None or not is_plain_body(lines[payload_index]):
            continue
        payload = lines[payload_index].strip()
        continuation_index = next_nonblank(lines, payload_index + 1)
        has_continuation = (
            continuation_index is not None
            and is_plain_body(lines[continuation_index])
            and CONTINUATION.match(lines[continuation_index].strip()) is not None
            and SENTENCE_END.search(lines[continuation_index].strip()) is not None
        )

        # Only transform prose whose sentence boundary is unambiguous. Short
        # labels, formulas, and step sequences remain colon-led blocks.
        if SENTENCE_END.search(payload) or has_continuation:
            candidates.append(
                (index, payload_index, continuation_index if has_continuation else None)
            )

    changes: list[tuple[int, str, str]] = []
    for lead_index, payload_index, continuation_index in reversed(candidates):
        lead = lines[lead_index]
        payload = lines[payload_index].strip()
        merged = f"{normalize_lead(lead, payload)}{emphasize(payload)}"
        end_index = payload_index
        if continuation_index is not None:
            merged += " " + lines[continuation_index].strip()
            end_index = continuation_index
        lines[lead_index : end_index + 1] = [merged]
        changes.append((lead_index + 1, lead, merged))

    return "\n".join(lines).rstrip() + "\n", list(reversed(changes))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Merge unambiguous prose after colon-led lines and preserve emphasis."
    )
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--samples", type=int, default=60)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()

    changed: list[tuple[Path, str]] = []
    all_changes: list[tuple[Path, int, str, str]] = []
    for source_dir in SOURCE_DIRS:
        for path in sorted(source_dir.rglob("*.md")):
            original = path.read_text(encoding="utf-8")
            normalized, changes = normalize(original)
            if changes:
                changed.append((path, normalized))
                all_changes.extend(
                    (path, line, before, after) for line, before, after in changes
                )

    for path, line, before, after in all_changes[args.offset : args.offset + args.samples]:
        print(f"{path.relative_to(ROOT)}:{line}\n  - {before}\n  + {after}")
    print(f"FILES: {len(changed)}")
    print(f"CHANGES: {len(all_changes)}")

    if args.write:
        for path, normalized in changed:
            path.write_text(normalized, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
