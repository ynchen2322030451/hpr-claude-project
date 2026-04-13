#!/usr/bin/env python3
"""Convert draft_paper_0411_v3.txt to a formatted Word document."""

import re
from datetime import datetime
from pathlib import Path

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

HERE = Path(__file__).parent
TXT_PATH = HERE / "draft_paper_0411_v3.txt"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
DOCX_PATH = HERE / f"draft_paper_0411_v3_{TIMESTAMP}.docx"
# Also keep a latest copy without timestamp for easy access
DOCX_LATEST = HERE / "draft_paper_0411_v3.docx"


def setup_styles(doc):
    """Configure document styles."""
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Times New Roman"
    font.size = Pt(11)
    pf = style.paragraph_format
    pf.space_after = Pt(6)
    pf.line_spacing = 1.15


def add_title(doc, title_en, title_cn):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(title_en)
    run.bold = True
    run.font.size = Pt(14)
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run2 = p2.add_run(title_cn)
    run2.bold = True
    run2.font.size = Pt(13)


def add_meta(doc, text):
    """Add author/affiliation block."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text.strip())
    run.font.size = Pt(10)


def add_section_heading(doc, text, level=1):
    doc.add_heading(text.strip(), level=level)


def add_body_paragraph(doc, text):
    """Add a normal paragraph. Highlight 【...】 markers in red."""
    p = doc.add_paragraph()
    # Split on 【...】 patterns
    parts = re.split(r'(【[^】]*】)', text)
    for part in parts:
        if part.startswith('【') and part.endswith('】'):
            run = p.add_run(part)
            run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
            run.bold = True
        else:
            p.add_run(part)


def add_placeholder(doc, text):
    """Add [TABLE]/[FIG] placeholder in blue italic."""
    p = doc.add_paragraph()
    run = p.add_run(text.strip())
    run.italic = True
    run.font.color.rgb = RGBColor(0x00, 0x55, 0xAA)
    run.font.size = Pt(10)


def add_comment_block(doc, text):
    """Add comment lines (starting with #) in gray."""
    p = doc.add_paragraph()
    run = p.add_run(text.strip())
    run.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
    run.font.size = Pt(9)
    run.italic = True


def add_table(doc, header_line, rows):
    """Add a simple markdown-style table."""
    cols = [c.strip() for c in header_line.split('|') if c.strip()]
    n_cols = len(cols)
    table = doc.add_table(rows=1 + len(rows), cols=n_cols)
    table.style = 'Light Grid Accent 1'
    # header
    for i, col in enumerate(cols):
        cell = table.rows[0].cells[i]
        cell.text = col
        for run in cell.paragraphs[0].runs:
            run.bold = True
    # data rows
    for r_idx, row_line in enumerate(rows):
        cells_text = [c.strip() for c in row_line.split('|') if c.strip()]
        for c_idx, ct in enumerate(cells_text):
            if c_idx < n_cols:
                table.rows[1 + r_idx].cells[c_idx].text = ct
    doc.add_paragraph()  # spacing


def parse_and_convert(txt_path, docx_path):
    doc = Document()
    setup_styles(doc)

    lines = txt_path.read_text(encoding="utf-8").splitlines()

    # Title
    add_title(
        doc,
        "Probabilistic Neural Surrogates for Uncertainty-to-Risk Analysis\n"
        "in Coupled Multi-Physics Systems: Application to a Heat-Pipe-Cooled Reactor",
        "概率神经代理模型在耦合多物理场系统不确定性\u2013风险分析中的应用\n"
        "\u2014\u2014以热管冷却反应堆为例",
    )

    # Version info
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"Draft v3 | Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
    doc.add_paragraph()  # spacer

    i = 0
    # Skip the header comment block (lines starting with #)
    while i < len(lines) and (lines[i].startswith('#') or lines[i].strip() == ''):
        i += 1

    # Collect paragraphs
    buf = []
    table_header = None
    table_rows = []
    in_table = False

    def flush_buf():
        nonlocal buf
        if not buf:
            return
        text = '\n'.join(buf).strip()
        if not text:
            buf = []
            return
        # Determine type
        if text.startswith('[TABLE') or text.startswith('[FIG'):
            add_placeholder(doc, text)
        elif text.startswith('%CN:') or text.startswith('#'):
            add_comment_block(doc, text)
        else:
            add_body_paragraph(doc, text)
        buf = []

    def flush_table():
        nonlocal table_header, table_rows, in_table
        if table_header and table_rows:
            add_table(doc, table_header, table_rows)
        table_header = None
        table_rows = []
        in_table = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Major section heading: ===...=== on prev/next line
        if re.match(r'^={10,}$', stripped):
            flush_buf()
            flush_table()
            # The heading text is on the next line (or was on prev line)
            # Look for pattern: === \n text \n ===
            if i + 2 < len(lines) and re.match(r'^={10,}$', lines[i + 2].strip()):
                heading_text = lines[i + 1].strip()
                add_section_heading(doc, heading_text, level=1)
                i += 3
                continue
            i += 1
            continue

        # Sub-section heading: ---...--- pattern
        if re.match(r'^-{10,}$', stripped):
            flush_buf()
            flush_table()
            if i + 2 < len(lines) and re.match(r'^-{10,}$', lines[i + 2].strip()):
                heading_text = lines[i + 1].strip()
                add_section_heading(doc, heading_text, level=2)
                i += 3
                continue
            i += 1
            continue

        # Table detection: lines with | separators
        if '|' in stripped and stripped.startswith('|') and stripped.endswith('|'):
            flush_buf()
            if re.match(r'^\|[-\s|]+\|$', stripped):
                # separator line, skip
                i += 1
                continue
            if not in_table:
                table_header = stripped
                in_table = True
            else:
                table_rows.append(stripped)
            i += 1
            continue
        elif in_table:
            flush_table()

        # Comment lines starting with %CN:
        if stripped.startswith('%CN:'):
            flush_buf()
            # Collect consecutive comment lines
            comment_lines = []
            while i < len(lines) and lines[i].strip().startswith('%CN:'):
                comment_lines.append(lines[i].strip())
                i += 1
            add_comment_block(doc, '\n'.join(comment_lines))
            continue

        # [TABLE ...] or [FIG ...] placeholders
        if stripped.startswith('[TABLE') or stripped.startswith('[FIG'):
            flush_buf()
            placeholder_lines = [stripped]
            i += 1
            # Sometimes multi-line
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('[') and not re.match(r'^[-=]{10,}$', lines[i].strip()):
                if lines[i].strip().startswith('['):
                    break
                # Check if it's still part of placeholder
                if lines[i].strip().startswith('[FIG') or lines[i].strip().startswith('[TABLE'):
                    break
                placeholder_lines.append(lines[i].strip())
                i += 1
            add_placeholder(doc, ' '.join(placeholder_lines))
            continue

        # Section label hints like [第一段：...]
        if re.match(r'^\[第.+段[：:]', stripped):
            flush_buf()
            add_placeholder(doc, stripped)
            i += 1
            continue

        # Empty line = paragraph break
        if stripped == '':
            flush_buf()
            i += 1
            continue

        # Header comment block at start
        if stripped.startswith('#'):
            flush_buf()
            comment_lines = [stripped]
            i += 1
            while i < len(lines) and lines[i].strip().startswith('#'):
                comment_lines.append(lines[i].strip())
                i += 1
            add_comment_block(doc, '\n'.join(comment_lines))
            continue

        # Regular text: accumulate into paragraph
        buf.append(line.rstrip())
        i += 1

    flush_buf()
    flush_table()

    # Save
    doc.save(str(docx_path))
    return docx_path


if __name__ == "__main__":
    out = parse_and_convert(TXT_PATH, DOCX_PATH)
    print(f"Word document saved to: {out}")
    # Also save latest
    parse_and_convert(TXT_PATH, DOCX_LATEST)
    print(f"Latest copy saved to:   {DOCX_LATEST}")
