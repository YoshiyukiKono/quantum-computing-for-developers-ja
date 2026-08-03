from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
BOOK = HERE / "book.json"
REGISTRY = HERE / "editorial" / "sources.json"
REFERENCES = HERE / "backmatter" / "references.md"
SOURCE_ID = re.compile(r"R\d{3}")


def fail(messages: list[str]) -> None:
    for message in messages:
        print(f"ERROR: {message}")
    raise SystemExit(1)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    book = json.loads(BOOK.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    reference_text = REFERENCES.read_text(encoding="utf-8")
    errors: list[str] = []

    records = registry.get("sources", [])
    ids = [record.get("id", "") for record in records]
    counts = Counter(ids)
    for source_id, count in counts.items():
        if count != 1:
            errors.append(f"source ID {source_id!r} occurs {count} times in sources.json")
        if not SOURCE_ID.fullmatch(source_id):
            errors.append(f"invalid source ID: {source_id!r}")

    registered = set(ids)
    for record in records:
        source_id = record.get("id", "<missing>")
        if not str(record.get("url", "")).startswith("https://"):
            errors.append(f"{source_id} does not have an HTTPS URL")
        if record.get("type") == "official-doc" and not record.get("accessed"):
            errors.append(f"{source_id} is an official document without an access date")

    cited: set[str] = set()
    entries = [chapter for part in book.get("parts", []) for chapter in part.get("chapters", [])]
    entries.extend(book.get("appendices", []))
    for entry in entries:
        path = HERE / entry.get("path", "")
        if not path.is_file():
            errors.append(f"missing manuscript file: {path}")
        sources = entry.get("sources", [])
        if not sources:
            errors.append(f"no sources assigned to {entry.get('path', '<unknown>')}")
        for source_id in sources:
            cited.add(source_id)
            if source_id not in registered:
                errors.append(f"unknown source {source_id} in {entry.get('path', '<unknown>')}")

    for item in book.get("backmatter", []):
        path = HERE / item.get("path", "")
        if not path.is_file():
            errors.append(f"missing backmatter file: {path}")

    heading_ids = re.findall(r"^### \[(R\d{3})\]\s*$", reference_text, flags=re.MULTILINE)
    heading_counts = Counter(heading_ids)
    for source_id in sorted(registered):
        count = heading_counts[source_id]
        if count != 1:
            errors.append(f"{source_id} has {count} bibliography headings; expected 1")
    for source_id in sorted(set(heading_ids) - registered):
        errors.append(f"bibliography contains unregistered source {source_id}")
    for source_id in sorted(registered - cited):
        errors.append(f"registered source {source_id} is not assigned to any chapter or appendix")

    if errors:
        fail(errors)

    print(f"SOURCES: {len(registered)}")
    print(f"CITED_ENTRIES: {len(entries)}")
    print(f"BACKMATTER_FILES: {len(book.get('backmatter', []))}")
    print("REFERENCE_AUDIT: OK")


if __name__ == "__main__":
    main()
