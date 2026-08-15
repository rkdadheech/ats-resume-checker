"""
Handles extracting raw text from uploaded resume files (PDF or DOCX).
Also runs basic ATS-formatting checks that don't depend on keyword matching --
things like missing sections, multi-column layout hints, and file health.
"""

import re
import pdfplumber
from docx import Document
from utils.skills_db import EXPECTED_SECTIONS


def extract_text_from_pdf(file) -> str:
    text_chunks = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_chunks.append(page_text)
    return "\n".join(text_chunks)


def extract_text_from_docx(file) -> str:
    doc = Document(file)
    return "\n".join(p.text for p in doc.paragraphs)


def extract_resume_text(uploaded_file) -> str:
    """uploaded_file is a Streamlit UploadedFile object."""
    filename = uploaded_file.name.lower()
    if filename.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif filename.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    else:
        raise ValueError("Unsupported file type. Please upload a PDF or DOCX file.")


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


def check_formatting(raw_text: str, char_count_threshold: int = 200):
    """
    Basic heuristic formatting checks. Real ATS parsers vary, so these
    are best-effort signals, not guarantees.
    """
    issues = []
    lower_text = raw_text.lower()

    if len(raw_text.strip()) < char_count_threshold:
        issues.append(
            "Very little text was extracted from this file. If your resume "
            "uses text boxes, images, or heavy tables, many ATS systems "
            "will fail to read it the same way this tool did."
        )

    found_sections = [s for s in EXPECTED_SECTIONS if s in lower_text]
    missing_core = [s for s in ["experience", "education", "skills"] if s not in lower_text]
    if missing_core:
        issues.append(
            f"Missing or unlabeled standard section(s): {', '.join(missing_core)}. "
            "ATS systems look for these headers explicitly."
        )

    if re.search(r"[|]{2,}", raw_text) or raw_text.count("\t") > 20:
        issues.append(
            "Detected patterns consistent with a multi-column or table-based "
            "layout. These often get scrambled by ATS parsers -- a single-column "
            "layout is safer."
        )

    email_found = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", raw_text))
    if not email_found:
        issues.append("No email address detected -- make sure your contact info is in plain text, not an image.")

    return {
        "issues": issues,
        "sections_found": found_sections,
        "formatting_score": max(0, 100 - len(issues) * 20),
    }
