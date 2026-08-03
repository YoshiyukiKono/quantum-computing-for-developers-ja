from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = (ROOT / "content", ROOT / "appendices")
OPENERS = {"```", "```text"}
FORMULA_CHARS = re.compile(r"[=<>|{}\[\]()/\\^+*×≈∝⊂√θ−±〜～%$@⊗←→↔²³]")
VERSION_OR_PATH = re.compile(r"(?:\d+\.\d+|[_/\\]|\.[A-Za-z0-9]{1,5}$)")
DISPLAY_SYNTAX = re.compile(r"(?:^\s*[01](?:\s+[01])+$|^[01]{2,}$|^O\(.+\)$|::|:=|=>|\b(?:True|False|None)\b)")
STATE_EXPRESSION = re.compile(
    r"^(?:0|1|00|01|10|11)\s*(?:または|か|と|or\b)|^[xq][A-Za-z0-9_]*\s+は\s+",
    re.IGNORECASE,
)
PLAIN_MARKDOWN = re.compile(r"^(?!#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\||```|\$\$|---$).+")
CONTINUATION = re.compile(
    r"^(?:は|が|を|と|で|です|でした|であり|になります|になり|になれ|"
    r"の(?:です|で|方|が|を|ため)|から|だけ|こと|という|して|させ|できます|"
    r"必要|状態(?:が|を|に|で)|ゲート(?:が|を|に|で)|よう|ため)"
)
TERM_ENDINGS = re.compile(
    r"(?:状態|規則|ゲート|行列|測定|もつれ|演算子|作用素|反転|回転|"
    r"アルゴリズム|モデル|構造|型|クラス|オブジェクト|ビット|qubit|"
    r"完全|オラクル|テンソル|ベクトル|ハミルトニアン|structure)"
    r"(?:（[^）]+）)?$",
    re.IGNORECASE,
)
CLAUSE_MARKERS = re.compile(
    r"(?:\sは\s|が|を|に|へ|から|まで|する|して|され|なる|なり|でき|"
    r"決ま|作る|扱う|使う|見つ|表現でき|同時に|必要)"
)


def is_phrase(text: str) -> bool:
    value = text.strip()
    if not value or len(value) > 80:
        return False
    if re.search(r"\d", value):
        return False
    if FORMULA_CHARS.search(value) or VERSION_OR_PATH.search(value):
        return False
    if value.startswith(("{", "(", "[", "'", '"')):
        return False
    if re.fullmatch(r"[A-Za-z]", value):
        return False
    if re.fullmatch(r"[A-Z](?:,[A-Z])+", value):
        return False
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9.+-]{1,15}", value):
        return True
    if CLAUSE_MARKERS.search(value):
        return False
    return bool(TERM_ENDINGS.search(value))


def is_explanation(text: str) -> bool:
    value = text.strip()
    if not value or len(value) > 120:
        return False
    if (
        FORMULA_CHARS.search(value)
        or VERSION_OR_PATH.search(value)
        or DISPLAY_SYNTAX.search(value)
        or STATE_EXPRESSION.search(value)
    ):
        return False
    if value.startswith(("{", "(", "[", "'", '"')):
        return False
    if re.fullmatch(r"[A-Za-z]", value) or re.fullmatch(r"[A-Z](?:,[A-Z])+", value):
        return False
    if re.fullmatch(r"[\d\s.,:+-]+", value):
        return False
    if re.search(r"\w+\.\w+\s*\(", value):
        return False
    return bool(re.search(r"[一-龯ぁ-んァ-ヶ]", value))


def is_plain(line: str) -> bool:
    return bool(line.strip() and PLAIN_MARKDOWN.match(line.strip()))


def smart_join(left: str, right: str) -> str:
    left = left.rstrip()
    right = right.lstrip()
    if not left:
        return right
    if not right:
        return left
    if left.endswith("**") or right.startswith("**"):
        return left + " " + right
    if left[-1].isascii() and right[0].isascii():
        return left + " " + right
    return left + right


def complete_statement(line: str, phrase: str) -> str:
    value = line.rstrip()
    if re.search(r"[。！？!?]$", value) or value.endswith("："):
        return value
    if re.search(r"\d+世紀には", value):
        return value + "と位置づけられました。"
    if phrase.endswith(("？", "?", "！", "!")):
        return value
    if phrase.endswith(("ません", "できません")):
        return value + "。"
    verbal_noun = re.search(
        r"(?:強調|反転|回転|最大化|最小化|探索|更新|操作|実行|設計|計算|保存|変換|制限|決定|増加|分解)$",
        phrase,
    )
    prefix = value.split("**", 1)[0].rstrip()
    if verbal_noun:
        if prefix.endswith("は") and not prefix.endswith(("では", "には", "ては")):
            return value + "することです。"
        return value + "します。"
    predicate = re.search(
        r"(?:です|ます|でした|ました|ない|なる|なります|いる|ある|"
        r"できる|できません|未解決|有利|良い|いい|強い|多い|少ない|高い|低い|大きい|小さい|同じ|確率|半々|対象|"
        r"[一-龯ぁ-ん](?:う|く|ぐ|す|つ|ぬ|ぶ|む|る))$",
        phrase,
    )
    if predicate:
        if prefix.endswith(("理解するのは", "特徴は", "役割は", "結果は", "核心は", "自然な流れは")):
            return value + " ことです。"
        if prefix.endswith("は") and not prefix.endswith(("では", "には", "ては")):
            return value + " ことです。"
        return value + "。"
    return value + " です。"


def join_intro(intro: str, emphasis: str) -> str:
    stem = intro.rstrip()
    if not stem.endswith("："):
        return smart_join(stem, emphasis)
    stem = stem[:-1].rstrip()
    if re.search(r"この章で扱う.+が$", stem):
        stem = re.sub(r"この章で扱う(.+)が$", r"この章では\1である", stem)
    suffix_replacements = {
        "現在の量子コンピュータ": "現在の量子コンピュータは",
        "量子ビットは測定前": "量子ビットは測定前には",
        "ここで理解する": "ここで理解するのは",
        "直感": "直感的には",
        "VQE": "VQEでは",
        "QAOA": "QAOAでは",
        "断熱計算": "断熱計算では",
        "warm-start": "warm-startでは",
        "通常の初期状態": "通常の初期状態では",
        "パラメータ数": "パラメータ数は",
        "理由": "理由は",
        "用途": "用途は",
        "現在": "現在は",
        "短期": "短期的には",
        "長期": "長期的には",
        "最初の実用分野": "最初の実用分野は",
        "次": "次に",
        "その次": "その次に",
        "最後": "最後に",
        "量子探索アルゴリズムの基本アイデア": "量子探索アルゴリズの基本アイデアは",
        "整数因数分解の核心": "整数因数分解の核心は",
        "古典計算": "古典計算では",
        "意味": "意味は",
        "Stage 1": "Stage 1は",
        "現在の量子デバイス": "現在の量子デバイスは",
        "ランダム回路": "ランダム回路では",
        "普通のコンピュータ": "普通のコンピュータでは",
        "古典コンピュータ": "古典コンピュータでは",
        "量子コンピュータ": "量子コンピュータでは",
        "古典アルゴリズム": "古典アルゴリズムでは",
        "量子アルゴリズム": "量子アルゴリズムでは",
        "古典探索": "古典探索では",
        "量子探索": "量子探索では",
        "古典ビット": "古典ビットでは",
        "量子ビット": "量子ビットでは",
        "普通の説明": "通常の説明では",
        "設計者視点": "設計者の視点では",
        "浅い回路": "浅い回路では",
        "深い回路": "深い回路では",
        "入力": "入力は",
        "出力": "出力は",
        "答え": "答えは",
        "結果": "結果は",
        "内容": "内容は",
        "特徴": "特徴は",
        "テーマ": "テーマは",
        "よくある誤解": "よくある誤解は",
        "重要な関係": "重要な関係は",
        "関係": "関係は",
        "役割": "役割は",
        "イメージ": "イメージとしては",
        "例": "例として",
        "直積": "直積では",
        "テンソル積": "テンソル積では",
        "理論": "理論では",
        "実装": "実装では",
        "古典": "古典では",
        "量子": "量子では",
    }
    replacement = next(
        (value for suffix, value in suffix_replacements.items() if stem.endswith(suffix)),
        None,
    )
    if replacement:
        suffix = next(suffix for suffix in suffix_replacements if stem.endswith(suffix))
        stem = stem[: -len(suffix)] + replacement
    elif re.search(r"\d+世紀$", stem):
        stem += "には"
    elif stem.endswith(("つまり", "例えば", "たとえば", "逆に", "ここで", "だから", "そして", "さらに", "具体的には", "こう考えます")):
        stem += "、"
    elif stem.endswith(("は", "が", "を", "と", "なら", "では", "には", "でも", "から", "こそ", "である")):
        pass
    else:
        stem += "、"
    return smart_join(stem, emphasis)


def normalize(text: str, selector=is_phrase) -> tuple[str, list[tuple[int, str, str]]]:
    lines = text.splitlines()
    changes: list[tuple[int, str, str]] = []
    candidates: list[tuple[int, str]] = []
    i = 0
    while i + 2 < len(lines):
        if lines[i].strip() in OPENERS and lines[i + 2].strip() == "```":
            phrase = lines[i + 1].strip()
            if selector(phrase):
                candidates.append((i, phrase))
            i += 3
            continue
        i += 1

    for start, phrase in reversed(candidates):
        emphasis = f"**{phrase.replace('**', '')}**"
        lines[start : start + 3] = [emphasis]

        current = start
        previous = current - 1
        while previous >= 0 and not lines[previous].strip():
            previous -= 1
        following = current + 1
        while following < len(lines) and not lines[following].strip():
            following += 1

        replacement = emphasis
        merged_intro = False
        if previous >= 0 and is_plain(lines[previous]) and lines[previous].rstrip().endswith("："):
            replacement = join_intro(lines[previous], replacement)
            lines[previous : current + 1] = [replacement]
            current = previous
            merged_intro = True

        following = current + 1
        while following < len(lines) and not lines[following].strip():
            following += 1
        merged_following = False
        if (
            following < len(lines)
            and is_plain(lines[following])
            and CONTINUATION.match(lines[following].strip())
        ):
            following_text = lines[following].strip()
            if following_text in {"です", "です。"}:
                replacement = complete_statement(lines[current], phrase)
            else:
                replacement = smart_join(lines[current], following_text)
            lines[current : following + 1] = [replacement]
            merged_following = True

        if merged_intro and not merged_following:
            replacement = complete_statement(lines[current], phrase)
            lines[current] = replacement

        changes.append((start + 1, phrase, replacement))

    return "\n".join(lines).rstrip() + "\n", list(reversed(changes))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Move one-line prose callouts back into bold body text.")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--samples", type=int, default=40)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--scope", choices=("terms", "explanations"), default="terms")
    args = parser.parse_args()
    selector = is_phrase if args.scope == "terms" else is_explanation

    changed_files: list[tuple[Path, str]] = []
    all_changes: list[tuple[Path, int, str, str]] = []
    for source_dir in SOURCE_DIRS:
        for path in sorted(source_dir.rglob("*.md")):
            original = path.read_text(encoding="utf-8")
            normalized, changes = normalize(original, selector=selector)
            if not changes:
                continue
            changed_files.append((path, normalized))
            all_changes.extend((path, line, before, after) for line, before, after in changes)

    for path, line, before, after in all_changes[args.offset : args.offset + args.samples]:
        print(f"{path.relative_to(ROOT)}:{line}\n  - {before}\n  + {after}")
    print(f"FILES: {len(changed_files)}")
    print(f"CHANGES: {len(all_changes)}")

    if args.write:
        for path, normalized in changed_files:
            path.write_text(normalized, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
