#!/usr/bin/env python3

import argparse
import re
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import BaseDocTemplate, Frame, PageBreak, PageTemplate, Paragraph, Preformatted, Spacer
from reportlab.platypus.tableofcontents import TableOfContents


class MarkdownPdfTemplate(BaseDocTemplate):
    def __init__(self, filename: str, document_title: str, **kwargs):
        super().__init__(filename, **kwargs)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="body")
        self.addPageTemplates([PageTemplate(id="default", frames=[frame], onPage=self._draw_chrome)])
        self.document_title = document_title

    def _draw_chrome(self, canvas, doc):
        page_number = canvas.getPageNumber()
        if page_number == 1:
            return

        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D9D9D9"))
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, A4[1] - 18 * mm, A4[0] - doc.rightMargin, A4[1] - 18 * mm)

        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.setFont("Helvetica", 9)
        canvas.drawString(doc.leftMargin, A4[1] - 14 * mm, self.document_title)
        canvas.drawRightString(A4[0] - doc.rightMargin, 10 * mm, f"Page {page_number - 1}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        level = getattr(flowable, "_toc_level", None)
        if level is None:
            return

        text = flowable.getPlainText()
        key = getattr(flowable, "_bookmark_name", None)
        if not key:
            return

        self.canv.bookmarkPage(key)
        try:
            self.canv.addOutlineEntry(text, key, level=level, closed=False)
        except ValueError:
            pass
        self.notify("TOCEntry", (level, text, self.page, key))


def register_fonts() -> None:
    try:
        pdfmetrics.getFont("STSong-Light")
    except KeyError:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))


def build_styles():
    register_fonts()
    sample = getSampleStyleSheet()

    base = ParagraphStyle(
        "Base",
        parent=sample["BodyText"],
        fontName="STSong-Light",
        fontSize=11,
        leading=17,
        textColor=colors.black,
        wordWrap="CJK",
        spaceAfter=6,
    )
    meta = ParagraphStyle(
        "Meta",
        parent=base,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#666666"),
    )
    cover_title = ParagraphStyle(
        "CoverTitle",
        parent=base,
        fontSize=24,
        leading=30,
        textColor=colors.HexColor("#111111"),
        spaceAfter=12,
    )
    cover_subtitle = ParagraphStyle(
        "CoverSubtitle",
        parent=base,
        fontSize=12,
        leading=18,
        textColor=colors.HexColor("#4F4F4F"),
        spaceAfter=8,
    )
    h1 = ParagraphStyle(
        "Heading1",
        parent=base,
        fontSize=20,
        leading=26,
        textColor=colors.HexColor("#111111"),
        spaceBefore=4,
        spaceAfter=12,
    )
    h2 = ParagraphStyle(
        "Heading2",
        parent=base,
        fontSize=15,
        leading=21,
        textColor=colors.HexColor("#1F1F1F"),
        spaceBefore=12,
        spaceAfter=8,
    )
    h3 = ParagraphStyle(
        "Heading3",
        parent=base,
        fontSize=12.5,
        leading=18,
        textColor=colors.HexColor("#2C2C2C"),
        spaceBefore=10,
        spaceAfter=6,
    )
    bullet = ParagraphStyle(
        "Bullet",
        parent=base,
        leftIndent=16,
        firstLineIndent=0,
        bulletIndent=2,
        spaceBefore=1,
        spaceAfter=4,
    )
    quote = ParagraphStyle(
        "Quote",
        parent=base,
        leftIndent=14,
        borderPadding=8,
        borderWidth=0,
        borderColor=colors.HexColor("#DDDDDD"),
        backColor=colors.HexColor("#F7F7F7"),
        textColor=colors.HexColor("#444444"),
    )
    code = ParagraphStyle(
        "Code",
        parent=base,
        fontName="Courier",
        fontSize=9,
        leading=13,
        leftIndent=10,
        rightIndent=10,
        backColor=colors.HexColor("#F5F5F5"),
        borderPadding=6,
        spaceBefore=2,
        spaceAfter=8,
    )
    toc_heading = ParagraphStyle(
        "TocHeading",
        parent=base,
        fontSize=18,
        leading=24,
        spaceAfter=10,
    )

    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle(
            "TOCLevel1",
            parent=base,
            fontSize=11,
            leading=16,
            leftIndent=0,
            firstLineIndent=0,
            spaceBefore=2,
        ),
        ParagraphStyle(
            "TOCLevel2",
            parent=base,
            fontSize=10.5,
            leading=15,
            leftIndent=14,
            firstLineIndent=0,
            textColor=colors.HexColor("#333333"),
        ),
        ParagraphStyle(
            "TOCLevel3",
            parent=base,
            fontSize=10,
            leading=14,
            leftIndent=28,
            firstLineIndent=0,
            textColor=colors.HexColor("#555555"),
        ),
    ]

    return {
        "base": base,
        "meta": meta,
        "cover_title": cover_title,
        "cover_subtitle": cover_subtitle,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "bullet": bullet,
        "quote": quote,
        "code": code,
        "toc_heading": toc_heading,
        "toc": toc,
    }


def extract_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def extract_update_date(markdown: str) -> str | None:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("更新日期："):
            return stripped.split("：", 1)[1].strip()
    return None


def inline_markup(text: str) -> str:
    token_pattern = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^\)]+\))")
    pieces: list[str] = []
    last_index = 0

    for match in token_pattern.finditer(text):
        pieces.append(escape(text[last_index:match.start()]))
        token = match.group(0)

        if token.startswith("**") and token.endswith("**"):
            pieces.append(f"<b>{escape(token[2:-2])}</b>")
        elif token.startswith("`") and token.endswith("`"):
            pieces.append(f'<font name="Courier">{escape(token[1:-1])}</font>')
        else:
            link_match = re.match(r"\[([^\]]+)\]\(([^\)]+)\)", token)
            if link_match:
                label, url = link_match.groups()
                pieces.append(f'{escape(label)} <font color="#666666">({escape(url)})</font>')
            else:
                pieces.append(escape(token))

        last_index = match.end()

    pieces.append(escape(text[last_index:]))
    return "".join(pieces).replace("\n", "<br/>")


def make_heading(text: str, style: ParagraphStyle, level: int, bookmark_name: str) -> Paragraph:
    paragraph = Paragraph(inline_markup(text), style)
    paragraph._toc_level = level
    paragraph._bookmark_name = bookmark_name
    return paragraph


def add_cover(story: list, title: str, update_date: str | None, source_path: Path, styles: dict) -> None:
    story.append(Spacer(1, 42 * mm))
    story.append(Paragraph(inline_markup(title), styles["cover_title"]))
    story.append(Paragraph("正式版方案文档", styles["cover_subtitle"]))
    story.append(Spacer(1, 8 * mm))

    if update_date:
        story.append(Paragraph(f"更新日期：{escape(update_date)}", styles["meta"]))
    story.append(Paragraph(f"源文件：{escape(str(source_path))}", styles["meta"]))
    story.append(Paragraph("生成方式：Markdown → PDF（封面、目录、页码）", styles["meta"]))
    story.append(Spacer(1, 18 * mm))
    story.append(
        Paragraph(
            "本文件用于把“找工作”思维重构为“发现机会、估值机会、选择工作”的系统方案，便于打印、转发和正式讨论。",
            styles["base"],
        )
    )
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("阅读提示", styles["h3"]))
    for item in (
        "先看“设计定位”和“核心概念”，确认问题定义是否正确。",
        "再看“多 Agent 设计”和“数据模型”，确认系统边界与实现抓手。",
        "最后看“MVP 范围”和“成功指标”，判断是否值得启动。",
    ):
        story.append(Paragraph(inline_markup(item), styles["bullet"], bulletText="•"))
    story.append(PageBreak())


def add_toc(story: list, styles: dict) -> None:
    story.append(Paragraph("目录", styles["toc_heading"]))
    story.append(styles["toc"])
    story.append(PageBreak())


def iter_body_flowables(markdown: str, title: str, styles: dict) -> Iterable:
    paragraph_lines: list[str] = []
    code_lines: list[str] = []
    in_code_block = False
    skipped_title = False
    heading_index = 0

    def flush_paragraph():
        nonlocal paragraph_lines
        if not paragraph_lines:
            return None
        text = " ".join(line.strip() for line in paragraph_lines if line.strip())
        paragraph_lines = []
        if not text:
            return None
        return Paragraph(inline_markup(text), styles["base"])

    lines = markdown.splitlines()
    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if in_code_block:
            if stripped.startswith("```"):
                in_code_block = False
                yield Preformatted("\n".join(code_lines), styles["code"])
                code_lines = []
            else:
                code_lines.append(line)
            continue

        if stripped.startswith("```"):
            paragraph = flush_paragraph()
            if paragraph:
                yield paragraph
            in_code_block = True
            code_lines = []
            continue

        if not stripped:
            paragraph = flush_paragraph()
            if paragraph:
                yield paragraph
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            paragraph = flush_paragraph()
            if paragraph:
                yield paragraph

            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            if not skipped_title and level == 1 and heading_text == title:
                skipped_title = True
                continue

            heading_index += 1
            bookmark_name = f"heading-{heading_index}"
            if level == 1:
                yield make_heading(heading_text, styles["h1"], 0, bookmark_name)
            elif level == 2:
                yield make_heading(heading_text, styles["h2"], 1, bookmark_name)
            else:
                yield make_heading(heading_text, styles["h3"], 2, bookmark_name)
            continue

        if stripped.startswith("- "):
            paragraph = flush_paragraph()
            if paragraph:
                yield paragraph
            yield Paragraph(inline_markup(stripped[2:].strip()), styles["bullet"], bulletText="•")
            continue

        if stripped.startswith("> "):
            paragraph = flush_paragraph()
            if paragraph:
                yield paragraph
            yield Paragraph(inline_markup(stripped[2:].strip()), styles["quote"])
            continue

        if stripped.startswith("`") and stripped.endswith("`") and len(stripped) > 2:
            paragraph = flush_paragraph()
            if paragraph:
                yield paragraph
            yield Preformatted(stripped[1:-1], styles["code"])
            continue

        paragraph_lines.append(line)

    paragraph = flush_paragraph()
    if paragraph:
        yield paragraph

    if code_lines:
        yield Preformatted("\n".join(code_lines), styles["code"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a Markdown document to a styled PDF.")
    parser.add_argument("source", help="Source Markdown file.")
    parser.add_argument("output", help="Output PDF file.")
    parser.add_argument("--title", help="Override the PDF title.")
    return parser


def render(source_path: Path, output_path: Path, title_override: str | None = None) -> None:
    markdown = source_path.read_text(encoding="utf-8")
    title = title_override or extract_title(markdown, source_path.stem)
    update_date = extract_update_date(markdown)
    styles = build_styles()

    story = []
    add_cover(story, title, update_date, source_path, styles)
    add_toc(story, styles)
    story.extend(iter_body_flowables(markdown, title, styles))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = MarkdownPdfTemplate(
        str(output_path),
        document_title=title,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=24 * mm,
        bottomMargin=18 * mm,
        title=title,
        author="OpenAI Codex",
    )
    doc.multiBuild(story)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    render(Path(args.source), Path(args.output), args.title)


if __name__ == "__main__":
    main()
