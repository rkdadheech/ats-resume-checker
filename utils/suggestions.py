"""
Generates a suggested sentence/bullet for each missing keyword, so the user
has a concrete starting point to add to their resume rather than just a
bare list of words to work in themselves.

These are templates, not magic -- the user should still edit them to be
truthful and specific to their own experience. We say this explicitly in
the UI so nobody pastes an unedited template into a real resume.
"""

TEMPLATES = {
    "soft_skill": [
        "Demonstrated strong {term} while coordinating with cross-functional teams to meet operational targets.",
        "Applied {term} to resolve day-to-day challenges and improve team output.",
    ],
    "tool": [
        "Used {term} to analyze data and support decision-making.",
        "Leveraged {term} to build reports and streamline reporting workflows.",
    ],
    "domain": [
        "Managed {term} processes to improve efficiency and reduce costs.",
        "Implemented {term} practices that contributed to measurable operational improvements.",
    ],
    "certification": [
        "Certified in {term}, applied to improve process quality and consistency.",
    ],
    "general": [
        "Incorporate the term \"{term}\" naturally into a relevant bullet point describing your related experience.",
    ],
}


KNOWN_ACRONYMS = {
    "sap", "wm", "mm", "erp", "vba", "api", "etl", "aws", "gst", "pmp",
    "cscp", "cpim", "cltd", "fifo", "fefo", "eoq", "fsn", "tat", "5s",
    "wms", "bi", "otif", "3pl", "iso", "kpi", "roi", "sql", "sop", "vsm",
}


def title_case_term(term: str) -> str:
    # Keep known acronyms upper-case (SAP, OTIF, 3PL, etc.), title-case the rest
    words = term.split()
    out = []
    for w in words:
        if w.lower() in KNOWN_ACRONYMS or any(ch.isdigit() for ch in w):
            out.append(w.upper())
        else:
            out.append(w.capitalize())
    return " ".join(out)


def generate_suggestions(missing_keywords: list[dict], max_suggestions: int = 10) -> list[dict]:
    """
    Returns a list of {term, category, suggestion} dicts, one suggested
    sentence per missing keyword (highest-priority keywords first).
    """
    suggestions = []
    ranked = sorted(missing_keywords, key=lambda x: -x["score"])[:max_suggestions]

    for kw in ranked:
        category = kw.get("category", "general")
        templates = TEMPLATES.get(category, TEMPLATES["general"])
        template = templates[0]
        display_term = title_case_term(kw["term"])
        suggestions.append({
            "term": kw["term"],
            "category": category,
            "suggestion": template.format(term=display_term),
        })

    return suggestions
