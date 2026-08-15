"""
Positions the candidate's skills relative to the JD into two buckets:

- LAGGING: high-priority JD keywords the resume is missing (real gaps)
- FORWARD: keywords the resume already matches strongly, PLUS "bonus" skills
  from the curated taxonomy that appear in the resume but weren't even asked
  for in the JD (genuine differentiators vs. a typical candidate for this role)

This is relative to the JD, not to other real candidates -- we don't have
a pool of other applicants to compare against, so "forward" here means
"ahead of what this specific JD is asking for."
"""

from utils.skills_db import MASTER_SKILLS, SKILL_CATEGORY

CATEGORY_LABELS = {
    "soft_skill": "Soft Skills",
    "tool": "Tools & Tech",
    "domain": "Domain Expertise",
    "certification": "Certifications",
    "general": "Other Keywords",
}


def _normalize(text: str) -> str:
    return text.lower()


def find_bonus_skills(resume_text: str, jd_keywords: list[dict]) -> list[dict]:
    """
    Taxonomy skills present in the resume that the JD never asked for --
    these are differentiators, not requirements met.
    """
    norm_resume = resume_text.lower()
    jd_terms = {kw["term"].lower() for kw in jd_keywords}
    bonus = []
    for skill in MASTER_SKILLS:
        if skill in jd_terms:
            continue
        if skill in norm_resume:
            bonus.append({
                "term": skill,
                "category": SKILL_CATEGORY.get(skill, "domain"),
            })
    return bonus


def get_skill_positioning(matched: list, missing: list, resume_text: str,
                           jd_keywords: list, top_n: int = 8) -> dict:
    lagging = sorted(missing, key=lambda x: -x["score"])[:top_n]
    forward_core = sorted(matched, key=lambda x: -x["score"])[:top_n]
    bonus = find_bonus_skills(resume_text, jd_keywords)[:top_n]

    return {
        "lagging": lagging,
        "forward_core": forward_core,
        "bonus": bonus,
    }


def category_breakdown(matched: list, missing: list) -> dict:
    """
    Returns per-category matched/missing counts, used to draw a diverging
    bar chart (matched skills vs. gaps, grouped by skill type).
    """
    breakdown = {}
    for kw in matched:
        cat = kw.get("category", "general")
        breakdown.setdefault(cat, {"matched": 0, "missing": 0})
        breakdown[cat]["matched"] += 1
    for kw in missing:
        cat = kw.get("category", "general")
        breakdown.setdefault(cat, {"matched": 0, "missing": 0})
        breakdown[cat]["missing"] += 1
    return breakdown
