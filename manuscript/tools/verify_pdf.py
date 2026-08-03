from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from pypdf import PdfReader


DEFAULT_PHRASES = (
    "量子計算とは",
    "量子アルゴリズムの構造が一気に見通せるようになります",
    "現在の予測では",
    "ここで重要な点として",
    "qc = QuantumCircuit(1, 1)",
    "以上が基本的な流れです",
    "Groverアルゴリズムは、正解の確率だけを増やすアルゴリズムです",
    "Barren Plateauとは勾配が消える問題",
    "まず必要なのは次の4つです",
)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Run textual QA on the generated book PDF.")
    parser.add_argument("pdf", type=Path)
    args = parser.parse_args()

    reader = PdfReader(args.pdf)
    blank_pages: list[int] = []
    replacement_pages: list[int] = []
    nul_pages: list[int] = []
    editorial_pages: list[int] = []
    markdown_marker_pages: list[int] = []
    markdown_marker_snippets: list[tuple[int, str]] = []
    phrase_pages = {phrase: [] for phrase in DEFAULT_PHRASES}

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if not text.strip():
            blank_pages.append(page_number)
        if "\ufffd" in text:
            replacement_pages.append(page_number)
        if "\x00" in text:
            nul_pages.append(page_number)
        if "編集元:" in text or "<!--" in text or "-->" in text:
            editorial_pages.append(page_number)
        marker_match = re.search(r"(?<![A-Za-z0-9_])\*\*|\*\*(?![A-Za-z0-9_])", text)
        if marker_match:
            markdown_marker_pages.append(page_number)
            marker_index = marker_match.start()
            markdown_marker_snippets.append(
                (page_number, text[max(0, marker_index - 50) : marker_index + 80].replace("\n", " "))
            )
        compact = "".join(text.split())
        for phrase in DEFAULT_PHRASES:
            if "".join(phrase.split()) in compact:
                phrase_pages[phrase].append(page_number)

    print(f"PAGES: {len(reader.pages)}")
    print(f"BLANK_PAGES: {blank_pages}")
    print(f"REPLACEMENT_PAGES: {replacement_pages}")
    print(f"NUL_PAGES: {nul_pages}")
    print(f"EDITORIAL_MARKER_PAGES: {editorial_pages}")
    print(f"MARKDOWN_MARKER_PAGES: {markdown_marker_pages}")
    print(f"MARKDOWN_MARKER_SNIPPETS: {markdown_marker_snippets}")
    for phrase, pages in phrase_pages.items():
        print(f"PHRASE: {phrase} -> {pages}")


if __name__ == "__main__":
    main()
