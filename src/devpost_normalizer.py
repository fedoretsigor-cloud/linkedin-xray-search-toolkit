import re

from src.text_utils import clean_text


DEVPOST_MAKER_PATTERNS = [
    re.compile(
        r"\b(?i:(?:built|created|developed|made|submitted)\s+by)\s+"
        r"([A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3})",
    ),
    re.compile(
        r"\b(?i:(?:team|makers?|authors?|creators?))[:\s-]+"
        r"([A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){0,3})",
    ),
]

GENERIC_MAKER_VALUES = {
    "a team",
    "the team",
    "team",
    "makers",
    "students",
    "developers",
    "devpost",
    "hackathon",
}


def extract_project_title(title):
    value = clean_text(title)
    if not value:
        return ""
    for suffix in (" | Devpost", " - Devpost"):
        if value.endswith(suffix):
            return clean_text(value[: -len(suffix)])
    return value


def _clean_maker_name(value):
    name = clean_text(value).strip(" .,:;-|")
    name = re.split(r"\s+(?:and|with|using|for|at|from|on)\s+", name, maxsplit=1, flags=re.IGNORECASE)[0]
    name = clean_text(name).strip(" .,:;-|")
    if not name or name.lower() in GENERIC_MAKER_VALUES:
        return ""
    if len(name.split()) > 4:
        return ""
    if not re.search(r"[A-Za-z]", name):
        return ""
    return name


def extract_devpost_maker(*values):
    text = clean_text(" ".join(clean_text(value) for value in values if value))
    if not text:
        return ""
    for pattern in DEVPOST_MAKER_PATTERNS:
        match = pattern.search(text)
        if match:
            maker = _clean_maker_name(match.group(1))
            if maker:
                return maker
    return ""


def normalize_devpost_row(row):
    if row.get("source_site") != "devpost":
        return row

    normalized = dict(row)
    title = clean_text(normalized.get("result_title", ""))
    description = clean_text(normalized.get("short_description", ""))
    project_title = extract_project_title(title)
    maker_name = extract_devpost_maker(title, description)

    normalized["project_title"] = project_title
    normalized["project_url"] = normalized.get("profile_url", "")
    normalized["maker_extraction_status"] = "found" if maker_name else "missing"
    normalized["candidate_type"] = "project_maker" if maker_name else "project"
    normalized["profile_name"] = maker_name
    return normalized


def normalize_devpost_rows(rows):
    return [normalize_devpost_row(row) for row in rows]


def has_devpost_candidate(row):
    if row.get("source_site") != "devpost":
        return True
    return row.get("candidate_type") == "project_maker" and bool(clean_text(row.get("profile_name", "")))
