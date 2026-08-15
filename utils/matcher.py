"""
Core matching engine:
1. Extract candidate keywords from the JD (frequency-based n-grams + curated skill taxonomy)
2. Check which of those keywords appear in the resume (exact + fuzzy match)
3. Produce an overall ATS score combining keyword match % and formatting score

Deliberately uses only the Python standard library (no scikit-learn/rapidfuzz).
Those packages build from source on some hosts and can make first deploys slow
or flaky -- this version installs in seconds anywhere.
"""

import re
from collections import Counter
from difflib import SequenceMatcher
from utils.skills_db import MASTER_SKILLS, STOPWORDS_EXTRA, SKILL_CATEGORY

BASIC_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "of", "to", "in",
    "on", "for", "with", "at", "by", "from", "as", "is", "are", "was",
    "were", "be", "been", "being", "this", "that", "these", "those",
    "it", "its", "you", "your", "we", "our", "they", "their", "he", "she",
    "his", "her", "not", "no", "so", "than", "too", "very", "can", "will",
    "should", "would", "could", "may", "might", "must", "have", "has", "had",
}


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _sentence_split(text: str) -> list[str]:
    sentences = re.split(r"[.\n;]", text)
    return [s.strip() for s in sentences if len(s.strip()) > 3]


def _ngrams_from_sentence(words: list[str], n: int) -> list[str]:
    return [" ".join(words[i:i + n]) for i in range(len(words) - n + 1)]


def extract_jd_keywords(jd_text: str, top_n: int = 30) -> list[dict]:
    """
    Returns a ranked list of {term, score, source} dicts.
    Combines: (a) curated skills found verbatim in the JD, weighted by frequency,
              (b) frequency-ranked unigrams/bigrams from the JD as a fallback
                  for anything not in the curated list (so niche/company-specific
                  terms still get caught).
    """
    norm_jd = _normalize(jd_text)
    results = {}

    # (a) curated skill taxonomy -- exact/substring match, weight by frequency
    for skill in MASTER_SKILLS:
        skill_norm = _normalize(skill)
        count = norm_jd.count(skill_norm)
        if count > 0:
            results[skill_norm] = {
                "term": skill, "score": 5 + count, "source": "taxonomy",
                "category": SKILL_CATEGORY.get(skill, "domain"),
            }

    # (b) frequency-based n-grams as fallback signal, built sentence-by-sentence
    # so phrases never span sentence boundaries
    sentences = _sentence_split(norm_jd) or [norm_jd]
    counter = Counter()
    for sent in sentences:
        words = [w for w in sent.split() if w not in BASIC_STOPWORDS and len(w) >= 3]
        counter.update(words)  # unigrams
        counter.update(_ngrams_from_sentence(words, 2))  # bigrams

    if counter:
        max_count = max(counter.values())
        score_cutoff = max(1, max_count * 0.2)
        for term, count in counter.most_common(200):
            if count < score_cutoff:
                continue
            if any(sw in term.split() for sw in STOPWORDS_EXTRA):
                continue
            if term not in results:
                results[term] = {"term": term, "score": float(count) * 3, "source": "freq", "category": "general"}

    # taxonomy matches are always kept; frequency terms fill remaining slots
    taxonomy_terms = sorted(
        [v for v in results.values() if v["source"] == "taxonomy"], key=lambda x: -x["score"]
    )
    freq_terms = sorted(
        [v for v in results.values() if v["source"] == "freq"], key=lambda x: -x["score"]
    )

    # drop any keyword that is just a substring of a higher-ranked keyword
    # (avoids showing both "demand" and "demand forecasting" separately)
    deduped = []
    for kw in taxonomy_terms + freq_terms:
        if not any(kw["term"] != other["term"] and kw["term"] in other["term"] for other in deduped):
            deduped.append(kw)
        if len(deduped) >= top_n:
            break

    return deduped[:top_n]


def match_keywords(resume_text: str, jd_keywords: list[dict], fuzzy_threshold: float = 0.85):
    """
    For each JD keyword, checks presence in resume text via substring match
    first, then fuzzy match (catches minor variations/typos/plurals) using
    the standard-library difflib SequenceMatcher.
    Returns matched and missing keyword lists.
    """
    norm_resume = _normalize(resume_text)
    matched, missing = [], []

    for kw in jd_keywords:
        term_norm = _normalize(kw["term"])
        if not term_norm:
            continue

        if term_norm in norm_resume:
            matched.append(kw)
            continue

        # fuzzy fallback: check against sliding window of resume words
        words = norm_resume.split()
        window_size = max(1, len(term_norm.split()))
        found_fuzzy = False
        for i in range(0, max(1, len(words) - window_size + 1)):
            window = " ".join(words[i:i + window_size])
            if SequenceMatcher(None, term_norm, window).ratio() >= fuzzy_threshold:
                found_fuzzy = True
                break

        if found_fuzzy:
            matched.append(kw)
        else:
            missing.append(kw)

    return matched, missing


def compute_ats_score(matched: list, missing: list, formatting_score: int) -> dict:
    total_keywords = len(matched) + len(missing)
    keyword_match_pct = round((len(matched) / total_keywords) * 100, 1) if total_keywords else 0

    # Weighted: keyword match matters more than formatting, but both count
    overall_score = round((keyword_match_pct * 0.75) + (formatting_score * 0.25))
    overall_score = max(0, min(100, overall_score))

    if overall_score >= 80:
        verdict = "Strong match -- likely to pass most ATS keyword filters."
    elif overall_score >= 60:
        verdict = "Moderate match -- add the missing keywords below to improve your odds."
    else:
        verdict = "Weak match -- this resume needs significant keyword and/or formatting work for this JD."

    return {
        "overall_score": overall_score,
        "keyword_match_pct": keyword_match_pct,
        "formatting_score": formatting_score,
        "verdict": verdict,
    }
