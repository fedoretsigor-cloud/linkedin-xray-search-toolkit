import re

from src.devpost_normalizer import has_devpost_candidate
from src.text_utils import clean_text


GENERIC_PROFILE_NAMES = {
    "linkedin",
    "linkedin hiring integrations | integrate with recruiter & jobs",
    "java developer job description",
    "software engineer job description",
    "developer job description",
    "jobs",
    "job search",
}

AMBIGUOUS_TARGET_TERMS = {
    "front",
    "office",
    "power",
    "business",
    "senior",
    "lead",
    "principal",
    "professional",
}

NON_TARGET_HEADLINE_PREFIXES = (
    "teacher",
    "student",
    "professor",
    "realtor",
    "real estate",
    "attorney",
    "lawyer",
    "nurse",
    "physician",
    "doctor",
    "driver",
    "cashier",
)


def has_candidate_like_name(value):
    name = clean_text(value)
    if not name:
        return False
    if name.lower() in GENERIC_PROFILE_NAMES:
        return False
    if any(marker in name.lower() for marker in ("job description", "hiring guide", "integrate with recruiter")):
        return False
    return bool(re.search(r"[A-Za-z]", name))


def tokenize(value):
    return [
        token
        for token in re.split(r"[^a-z0-9+#.]+", clean_text(value).lower())
        if token
    ]


def extract_profile_headline(row):
    description = clean_text(row.get("short_description", ""))
    if not description:
        return ""
    first_line = clean_text(description.splitlines()[0])
    if " - Experience:" in first_line:
        return clean_text(first_line.split(" - Experience:", 1)[0])
    return first_line


def positive_target_terms(row):
    terms = []
    for value in [row.get("role", ""), row.get("technology", "")]:
        text = clean_text(value)
        if not text:
            continue
        for part in re.split(r"[|,;/]+", text):
            phrase = clean_text(part).lower()
            if len(phrase) >= 4:
                terms.append(phrase)
        for token in tokenize(text):
            if len(token) >= 4 and token not in AMBIGUOUS_TARGET_TERMS:
                terms.append(token)
    return dedupe_values(terms)


def contains_term(text, term):
    term = clean_text(term).lower()
    if not term:
        return False
    if " " in term:
        return term in text
    return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None


def has_positive_target_evidence(row):
    evidence = clean_text(
        " ".join(
            [
                row.get("result_title", ""),
                row.get("short_description", ""),
            ]
        )
    ).lower()
    return any(contains_term(evidence, term) for term in positive_target_terms(row))


def has_non_target_headline(row):
    headline = extract_profile_headline(row).lower()
    return any(
        re.search(rf"^{re.escape(prefix)}(\b| at\b|,)", headline)
        for prefix in NON_TARGET_HEADLINE_PREFIXES
    )


def is_obvious_role_mismatch(row):
    return has_non_target_headline(row) and not has_positive_target_evidence(row)


def is_quality_search_row(row):
    source_site = row.get("source_site", "")
    if source_site == "devpost":
        return has_devpost_candidate(row)
    if source_site == "linkedin":
        if not row.get("is_linkedin_profile"):
            return False
        if not has_candidate_like_name(row.get("profile_name", "")):
            return False
        if is_obvious_role_mismatch(row):
            return False
    return True


def dedupe_values(values):
    deduped = []
    seen = set()
    for value in values:
        text = clean_text(value)
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            deduped.append(text)
    return deduped
