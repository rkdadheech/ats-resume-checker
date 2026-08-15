"""
Builds a shareable PDF report summarizing one ATS analysis run: score,
keyword breakdown, skill positioning, and suggested lines to add.
Uses reportlab (no external services, works entirely offline).
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

GREEN = colors.HexColor("#2E7D32")
RED = colors.HexColor("#C62828")
BLUE = colors.HexColor("#4F46E5")
GRAY = colors.HexColor("#6B7280")


def _keyword_list_str(keywords: list[dict], limit: int = 15) -> str:
    terms = [kw["term"] for kw in keywords[:limit]]
    return ", ".join(terms) if terms else "None"


def build_pdf_report(score_result: dict, matched: list, missing: list,
                      positioning: dict, suggestions: list,
                      formatting_issues: list) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCustom", parent=styles["Title"], fontSize=20, spaceAfter=4)
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], textColor=GRAY, fontSize=10)
    h2 = ParagraphStyle("H2Custom", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6)
    body = styles["Normal"]

    story = []
    story.append(Paragraph("ATS Resume Report", title_style))
    story.append(Paragraph(datetime.now().strftime("Generated on %d %b %Y, %H:%M"), subtitle_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#e5e7eb")))
    story.append(Spacer(1, 10))

    # ----- Score summary table -----
    score_color = GREEN if score_result["overall_score"] >= 80 else \
        colors.HexColor("#F9A825") if score_result["overall_score"] >= 60 else RED

    summary_data = [
        ["Overall ATS Score", f"{score_result['overall_score']} / 100"],
        ["Keyword Match", f"{score_result['keyword_match_pct']}%"],
        ["Formatting Score", f"{score_result['formatting_score']} / 100"],
    ]
    summary_table = Table(summary_data, colWidths=[2.5 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("TEXTCOLOR", (1, 0), (1, 0), score_color),
        ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e5e7eb")),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 6))
    story.append(Paragraph(score_result["verdict"], body))
    story.append(Spacer(1, 10))

    # ----- Keyword breakdown -----
    story.append(Paragraph("Keyword Breakdown", h2))
    story.append(Paragraph(f"<b>Matched ({len(matched)}):</b> {_keyword_list_str(matched)}", body))
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<b>Missing ({len(missing)}):</b> {_keyword_list_str(missing)}", body))

    # ----- Skill positioning -----
    story.append(Paragraph("Skill Positioning", h2))
    story.append(Paragraph(
        f"<b>Lagging (close these gaps):</b> {_keyword_list_str(positioning['lagging'])}", body))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"<b>Forward (you meet these):</b> {_keyword_list_str(positioning['forward_core'])}", body))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"<b>Bonus (beyond what was asked):</b> {_keyword_list_str(positioning['bonus'])}", body))

    # ----- Suggested lines -----
    if suggestions:
        story.append(Paragraph("Suggested Lines to Add", h2))
        for s in suggestions:
            story.append(Paragraph(f"<b>{s['term']}:</b> {s['suggestion']}", body))
            story.append(Spacer(1, 4))

    # ----- Formatting issues -----
    story.append(Paragraph("Formatting & Readability Notes", h2))
    if formatting_issues:
        for issue in formatting_issues:
            story.append(Paragraph(f"&bull; {issue}", body))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No major formatting issues detected.", body))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#e5e7eb")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "This is a directional estimate, not a guarantee -- real ATS platforms "
        "parse resumes differently from each other.", subtitle_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
