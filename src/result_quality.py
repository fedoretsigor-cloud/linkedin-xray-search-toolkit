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


def has_candidate_like_name(value):
    name = clean_text(value)
    if not name:
        return False
    if name.lower() in GENERIC_PROFILE_NAMES:
        return False
    if any(marker in name.lower() for marker in ("job description", "hiring guide", "integrate with recruiter")):
        return False
    return bool(re.search(r"[A-Za-z]", name))


def is_quality_search_row(row):
    source_site = row.get("source_site", "")
    if source_site == "devpost":
        return has_devpost_candidate(row)
    if source_site == "linkedin":
        if not row.get("is_linkedin_profile"):
            return False
        if not has_candidate_like_name(row.get("profile_name", "")):
            return False
    return True
