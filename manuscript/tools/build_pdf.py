from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parents[1]
CONFIG = HERE / "book.json"
BUILD = HERE / "build"
OUTPUT = HERE / "output" / "pdf"


def assemble_book(config: dict) -> Path:
    """Assemble the editable manuscript sources without consulting docs/."""
    combined: list[str] = [f"# {config['title']}", "", config["subtitle"], "", f"_{config['edition']}_", ""]
    for part in config["parts"]:
        combined.extend(["", f"# {part['title']}", "", part["intro"], ""])
        for chapter in part["chapters"]:
            path = HERE / chapter["path"]
            if not path.is_file():
                raise FileNotFoundError(f"Manuscript chapter not found: {path}")
            combined.append(path.read_text(encoding="utf-8-sig").strip() + "\n")

    combined.extend(["", "# 付録", "", "本文の流れを止める実務手順、補助的な比較、長い思考ノートを収録する。", ""])
    for appendix in config["appendices"]:
        path = HERE / appendix["path"]
        if not path.is_file():
            raise FileNotFoundError(f"Manuscript appendix not found: {path}")
        combined.append(path.read_text(encoding="utf-8-sig").strip() + "\n")

    BUILD.mkdir(parents=True, exist_ok=True)
    book_path = BUILD / "book.md"
    book_path.write_text("\n".join(combined).strip() + "\n", encoding="utf-8", newline="\n")
    return book_path


GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ε",
    "theta": "θ", "lambda": "λ", "mu": "μ", "pi": "π", "phi": "φ",
    "psi": "ψ", "omega": "ω", "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ",
    "Lambda": "Λ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
}


def latex_to_unicode(value: str) -> str:
    """Make the source's small LaTeX subset readable without exposing commands."""
    value = value.strip()
    value = re.sub(r"\\text\{([^{}]*)\}", r"\1", value)
    value = re.sub(r"\\mathrm\{([^{}]*)\}", r"\1", value)
    value = re.sub(r"\\mathbf\{([^{}]*)\}", r"\1", value)
    value = re.sub(r"\\mathbb\{C\}", "C", value)
    value = re.sub(r"\\mathbb\{R\}", "R", value)
    value = re.sub(r"\\mathbb\{N\}", "N", value)
    value = re.sub(r"\\frac\{([^{}]+)\}\{\\sqrt\{([^{}]+)\}\}", r"(\1)/√(\2)", value)
    for _ in range(4):
        value = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", value)
        value = re.sub(r"\\sqrt\{([^{}]+)\}", r"√(\1)", value)
    value = re.sub(r"\\sqrt\s*([0-9A-Za-z-]+)", r"√\1", value)
    value = re.sub(r"√\(([0-9A-Za-z-]+)\)", r"√\1", value)
    replacements = {
        r"\\lvert": "|", r"\\rvert": "|", r"\\left": "", r"\\right": "",
        r"\\langle": "〈", r"\\rangle": "〉", r"\\ket": "ket",
        r"\\bra": "bra", r"\\rightarrow": "→", r"\\Rightarrow": "⇒",
        r"\\to": "→", r"\\otimes": "⊗", r"\\oplus": "⊕", r"\\times": "×",
        r"\\neq": "≠", r"\\approx": "≈", r"\\leq": "≤", r"\\geq": "≥",
        r"\\in": "∈", r"\\sum": "Σ", r"\\prod": "Π", r"\\cdot": "·",
        r"\\dagger": "†", r"\\pm": "±", r"\\infty": "∞",
        r"\\cdots": "…", r"\\ldots": "…", r"\\dots": "…",
        r"\\quad": "  ", r"\\;": " ", r"\\,": " ", r"\\!": "",
    }
    for source, target in replacements.items():
        value = re.sub(source, target, value)
    for name, symbol in GREEK.items():
        value = re.sub(r"\\" + name + r"(?![A-Za-z])", symbol, value)
    value = re.sub(r"\\vec\{([^{}]+)\}", r"\1", value)
    value = re.sub(r"\\begin\{(?:p|b|v|V)?matrix\}", "", value)
    value = re.sub(r"\\end\{(?:p|b|v|V)?matrix\}", "", value)
    value = re.sub(r"\\begin\{cases\}", "", value)
    value = re.sub(r"\\end\{cases\}", "", value)
    value = value.replace("&", "   ")
    value = re.sub(r"\\\\", "\n", value)
    value = re.sub(r"\^\{([^{}]+)\}", r"^(\1)", value)
    value = re.sub(r"_\{([^{}]+)\}", r"_(\1)", value)
    value = value.replace("{", "(").replace("}", ")")
    return value.strip()


def inline_markup(text: str) -> str:
    parts = re.split(r"(`[^`]+`|\$[^$\n]+\$)", text)
    rendered: list[str] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("`") and part.endswith("`"):
            code = html.escape(part[1:-1], quote=False)
            rendered.append(f"<font name='BIZUDGothic' color='#123354' backColor='#DCEAF7'>{code}</font>")
            continue
        if part.startswith("$") and part.endswith("$"):
            math = html.escape(latex_to_unicode(part[1:-1]), quote=False)
            rendered.append(f"<font name='NotoSansJP' color='#7C3E00' backColor='#FFF0C2'>{math}</font>")
            continue
        escaped = html.escape(latex_to_unicode(part), quote=False)
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
        escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", escaped)
        rendered.append(escaped)
    return "".join(rendered)


def make_pdf(config: dict) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
    from reportlab.lib.pagesizes import A5
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (
        BaseDocTemplate, Frame, HRFlowable, PageBreak, PageTemplate, Paragraph,
        Preformatted, Spacer, Table, TableStyle,
    )
    from reportlab.platypus.tableofcontents import TableOfContents

    class TintedPreformatted(Preformatted):
        """Preformatted block with a dependable borderless background."""
        fill_color = "#E8F3F8"

        def draw(self):
            self.canv.saveState()
            self.canv.setFillColor(colors.HexColor(self.fill_color))
            self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)
            self.canv.restoreState()
            super().draw()

    class ExecutablePreformatted(TintedPreformatted):
        fill_color = "#E2F1F8"

    class TextPreformatted(TintedPreformatted):
        fill_color = "#F1F0EC"

    font_regular = Path(r"C:\Windows\Fonts\NotoSansJP-VF.ttf")
    font_bold = Path(r"C:\Windows\Fonts\NotoSansJP-VF.ttf")
    if not font_regular.exists():
        raise FileNotFoundError("Noto Sans JP font is required")
    pdfmetrics.registerFont(TTFont("NotoSansJP", str(font_regular)))
    pdfmetrics.registerFont(TTFont("NotoSansJP-Bold", str(font_bold)))
    pdfmetrics.registerFontFamily("NotoSansJP", normal="NotoSansJP", bold="NotoSansJP-Bold")
    code_regular = Path(r"C:\Windows\Fonts\BIZ-UDGothicR.ttc")
    code_bold = Path(r"C:\Windows\Fonts\BIZ-UDGothicB.ttc")
    try:
        pdfmetrics.registerFont(TTFont("BIZUDGothic", str(code_regular), subfontIndex=0))
        pdfmetrics.registerFont(TTFont("BIZUDGothic-Bold", str(code_bold), subfontIndex=0))
    except Exception:
        pdfmetrics.registerFont(TTFont("BIZUDGothic", str(font_regular)))
        pdfmetrics.registerFont(TTFont("BIZUDGothic-Bold", str(font_bold)))
    pdfmetrics.registerFontFamily("BIZUDGothic", normal="BIZUDGothic", bold="BIZUDGothic-Bold")

    page_width, page_height = A5
    margin_x = 18 * mm
    margin_top = 18 * mm
    margin_bottom = 17 * mm

    class BookDocTemplate(BaseDocTemplate):
        def afterFlowable(self, flowable):
            if isinstance(flowable, Paragraph):
                level = getattr(flowable, "toc_level", None)
                if level is not None:
                    text = flowable.getPlainText()
                    key = f"heading-{self.seq.nextf('heading')}"
                    self.canv.bookmarkPage(key)
                    self.canv.addOutlineEntry(text, key, level=level, closed=False)
                    self.notify("TOCEntry", (level, text, self.page, key))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("NotoSansJP", 7)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(margin_x, 9 * mm, config["title"])
        canvas.drawRightString(page_width - margin_x, 9 * mm, str(doc.page))
        canvas.restoreState()

    styles = getSampleStyleSheet()
    base = ParagraphStyle("JPBody", parent=styles["BodyText"], fontName="NotoSansJP", fontSize=8.4,
                          leading=13.2, alignment=TA_JUSTIFY, wordWrap="CJK", textColor=colors.HexColor("#172033"),
                          spaceAfter=4.5)
    h1 = ParagraphStyle("JPH1", parent=base, fontName="NotoSansJP-Bold", fontSize=18, leading=25,
                        alignment=TA_LEFT, wordWrap="CJK", splitLongWords=True,
                        textColor=colors.HexColor("#0F3D56"), spaceBefore=0, spaceAfter=11, keepWithNext=True)
    h2 = ParagraphStyle("JPH2", parent=base, fontName="NotoSansJP-Bold", fontSize=13, leading=19,
                        textColor=colors.HexColor("#0E7490"), spaceBefore=11, spaceAfter=6, keepWithNext=True)
    h3 = ParagraphStyle("JPH3", parent=base, fontName="NotoSansJP-Bold", fontSize=10.5, leading=16,
                        textColor=colors.HexColor("#155E75"), spaceBefore=8, spaceAfter=4, keepWithNext=True)
    h4 = ParagraphStyle("JPH4", parent=base, fontName="NotoSansJP-Bold", fontSize=9.2, leading=14,
                        spaceBefore=6, spaceAfter=3, keepWithNext=True)
    quote = ParagraphStyle("JPQuote", parent=base, leftIndent=6 * mm, rightIndent=3 * mm,
                           borderColor=colors.HexColor("#67C4D4"), borderWidth=1.5, borderPadding=5,
                           backColor=colors.HexColor("#F1FAFC"), textColor=colors.HexColor("#334155"))
    bullet = ParagraphStyle("JPBullet", parent=base, leftIndent=5 * mm, firstLineIndent=-3 * mm,
                            bulletIndent=1 * mm, bulletFontName="NotoSansJP", bulletFontSize=7.5)
    filename_style = ParagraphStyle("JPFilename", parent=base, fontName="BIZUDGothic", fontSize=6.4,
                                    leading=9, leftIndent=2 * mm, rightIndent=0,
                                    textColor=colors.HexColor("#64748B"),
                                    spaceBefore=5, spaceAfter=2, keepWithNext=True)
    code = ParagraphStyle("JPCode", parent=base, fontName="BIZUDGothic", fontSize=6.8, leading=10,
                          leftIndent=0, rightIndent=0, borderWidth=0,
                          borderPadding=(7, 8, 7, 8), backColor=None,
                          textColor=colors.HexColor("#102A3E"), wordWrap="CJK", spaceBefore=0, spaceAfter=6)
    math_style = ParagraphStyle("JPMath", parent=base, fontName="NotoSansJP", fontSize=9.2, leading=15,
                                alignment=TA_CENTER, borderColor=colors.HexColor("#E9A23B"), borderWidth=.7,
                                borderPadding=(8, 9, 8, 9), backColor=colors.HexColor("#FFF8E7"),
                                textColor=colors.HexColor("#663C00"), spaceBefore=5, spaceAfter=7)
    small = ParagraphStyle("JPSmall", parent=base, fontSize=7.2, leading=10.5, textColor=colors.HexColor("#475569"))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    pdf_path = OUTPUT / "quantum-computing-for-developers-ja.pdf"
    doc = BookDocTemplate(str(pdf_path), pagesize=A5, leftMargin=margin_x, rightMargin=margin_x,
                          topMargin=margin_top, bottomMargin=margin_bottom,
                          title=config["title"], author="yoshiyuki_kono")
    frame = Frame(margin_x, margin_bottom, page_width - 2 * margin_x, page_height - margin_top - margin_bottom,
                  id="book-frame")
    doc.addPageTemplates(PageTemplate(id="book", frames=[frame], onPage=footer))

    story = [Spacer(1, 22 * mm),
             Paragraph(inline_markup(config["title"]), ParagraphStyle("TitleJP", parent=h1, fontSize=23,
                       leading=32, alignment=TA_CENTER, textColor=colors.HexColor("#083344"))),
             Spacer(1, 7 * mm),
             Paragraph(inline_markup(config["subtitle"]), ParagraphStyle("SubtitleJP", parent=base,
                       fontSize=11, leading=18, alignment=TA_CENTER, textColor=colors.HexColor("#475569"))),
             Spacer(1, 28 * mm),
             HRFlowable(width="40%", thickness=1, color=colors.HexColor("#22A3B6"), hAlign="CENTER"),
             Spacer(1, 7 * mm),
             Paragraph(inline_markup(config["edition"]), ParagraphStyle("EditionJP", parent=small, alignment=TA_CENTER)),
             Spacer(1, 5 * mm),
             Paragraph("本文の事実確認・API動作確認前の編集用ドラフト", ParagraphStyle("DraftJP", parent=small,
                       alignment=TA_CENTER, textColor=colors.HexColor("#B45309"))), PageBreak(),
             Paragraph("目次", h1)]
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("TOC1", fontName="NotoSansJP-Bold", fontSize=9, leading=14, leftIndent=0,
                       firstLineIndent=0, textColor=colors.HexColor("#0F3D56")),
        ParagraphStyle("TOC2", fontName="NotoSansJP", fontSize=7.6, leading=12, leftIndent=5 * mm,
                       firstLineIndent=0, textColor=colors.HexColor("#334155")),
    ]
    story.extend([toc, PageBreak()])

    markdown = (BUILD / "book.md").read_text(encoding="utf-8")
    lines = markdown.splitlines()
    paragraph_buffer: list[str] = []
    code_buffer: list[str] = []
    math_buffer: list[str] = []
    in_code = False
    in_math = False
    code_kind = "text"
    code_filename = ""
    first_h1 = True

    def flush_paragraph():
        if paragraph_buffer:
            joined = " ".join(x.strip() for x in paragraph_buffer)
            story.append(Paragraph(inline_markup(joined), base))
            paragraph_buffer.clear()

    def append_math_block(formula: str):
        story.append(Paragraph(formula or " ", math_style))
        # ReportLab draws paragraph borders into the padding area. Reserve an
        # explicit gap so the following baseline never touches that border.
        story.append(Spacer(1, 2 * mm))

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            flush_paragraph()
            if in_code:
                if code_kind == "math":
                    readable = latex_to_unicode("\n".join(code_buffer))
                    formula = html.escape(readable, quote=False).replace("\n", "<br/>")
                    append_math_block(formula)
                else:
                    if code_filename:
                        story.append(Paragraph(html.escape(code_filename), filename_style))
                    block_type = ExecutablePreformatted if code_kind == "executable" else TextPreformatted
                    story.append(block_type("\n".join(code_buffer), code, maxLineLength=76))
                code_buffer.clear()
                in_code = False
            else:
                fence_info = line[3:].strip()
                language, separator, filename = fence_info.partition(":")
                language = language.lower()
                code_filename = filename.strip() if separator else ""
                executable_languages = {
                    "python", "py", "bash", "sh", "shell", "powershell", "ps1",
                    "javascript", "js", "typescript", "ts", "java", "c", "cpp",
                    "csharp", "cs", "go", "rust", "ruby", "php", "sql",
                }
                if language == "math":
                    code_kind = "math"
                elif language in executable_languages:
                    code_kind = "executable"
                else:
                    code_kind = "text"
                in_code = True
            i += 1
            continue
        if in_code:
            code_buffer.append(line.expandtabs(4))
            i += 1
            continue
        if line.strip() == "$$":
            flush_paragraph()
            if in_math:
                readable = latex_to_unicode("\n".join(math_buffer))
                formula = html.escape(readable, quote=False).replace("\n", "<br/>")
                append_math_block(formula)
                math_buffer.clear()
                in_math = False
            else:
                in_math = True
            i += 1
            continue
        if in_math:
            math_buffer.append(line)
            i += 1
            continue
        if line.lstrip().startswith("<!--"):
            flush_paragraph()
            while "-->" not in line and i + 1 < len(lines):
                i += 1
                line = lines[i]
            i += 1
            continue
        heading = re.match(r"^(#{1,5})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            if level == 1:
                if first_h1:
                    first_h1 = False
                    i += 1
                    continue
                story.append(PageBreak())
            style = {1: h1, 2: h2, 3: h3}.get(level, h4)
            p = Paragraph(inline_markup(title), style)
            if level == 1:
                p.toc_level = 0 if (re.match(r"^第[IVX]+部", title) or title == "付録") else 1
            else:
                p.toc_level = None
            story.append(p)
            i += 1
            continue
        if i + 1 < len(lines) and "|" in line and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            flush_paragraph()
            table_lines = [line, lines[i + 1]]
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                table_lines.append(lines[i])
                i += 1
            def cells(row):
                return [c.strip() for c in row.strip().strip("|").split("|")]
            rows = [cells(table_lines[0])] + [cells(row) for row in table_lines[2:]]
            cols = max(len(row) for row in rows)
            rows = [row + [""] * (cols - len(row)) for row in rows]
            table_data = [[Paragraph(inline_markup(c), small) for c in row] for row in rows]
            available = page_width - 2 * margin_x
            table = Table(table_data, colWidths=[available / cols] * cols, repeatRows=1, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDF3F6")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F3D56")),
                ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#CBD5E1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.extend([table, Spacer(1, 2 * mm)])
            continue
        if not line.strip():
            flush_paragraph()
        elif re.match(r"^\s*[-*+]\s+", line):
            flush_paragraph()
            item = re.sub(r"^\s*[-*+]\s+", "", line)
            story.append(Paragraph(inline_markup(item), bullet, bulletText="•"))
        elif re.match(r"^\s*\d+[.)]\s+", line):
            flush_paragraph()
            match = re.match(r"^\s*(\d+)[.)]\s+(.*)$", line)
            story.append(Paragraph(inline_markup(match.group(2)), bullet, bulletText=match.group(1) + "."))
        elif line.startswith(">"):
            flush_paragraph()
            story.append(Paragraph(inline_markup(line.lstrip("> ")), quote))
        elif re.match(r"^\s*---+\s*$", line):
            flush_paragraph()
            story.append(Spacer(1, 2 * mm))
        else:
            paragraph_buffer.append(line)
        i += 1
    flush_paragraph()
    if code_buffer:
        if code_kind == "math":
            readable = latex_to_unicode("\n".join(code_buffer))
            append_math_block(html.escape(readable, quote=False).replace("\n", "<br/>"))
        else:
            if code_filename:
                story.append(Paragraph(html.escape(code_filename), filename_style))
            block_type = ExecutablePreformatted if code_kind == "executable" else TextPreformatted
            story.append(block_type("\n".join(code_buffer), code, maxLineLength=76))
    if math_buffer:
        readable = latex_to_unicode("\n".join(math_buffer))
        append_math_block(html.escape(readable, quote=False).replace("\n", "<br/>"))
    doc.multiBuild(story)
    return pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble the manuscript and build its review PDF.")
    parser.add_argument("--assemble-only", action="store_true", help="Only update manuscript/build/book.md")
    args = parser.parse_args()
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    print(assemble_book(config))
    if not args.assemble_only:
        print(make_pdf(config))


if __name__ == "__main__":
    main()
