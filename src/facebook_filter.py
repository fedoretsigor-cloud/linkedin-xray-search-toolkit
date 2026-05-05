import re

from src.text_utils import clean_text


OPEN_TO_WORK_PATTERNS = [
    r"\blooking for a job\b",
    r"\blooking for job\b",
    r"\blooking for work\b",
    r"\bcurrently looking\b",
    r"\bseeking opportunities\b",
    r"\bseeking opportunity\b",
    r"\bseeking job opportunities\b",
    r"\bopen to work\b",
    r"\bjob seeker\b",
    r"\bi am looking for\b",
    r"\bi'm looking for\b",
]

HIRING_PATTERNS = [
    r"\bhiring\b",
    r"\bwe are hiring\b",
    r"\bjob available\b",
    r"\bjob opportunity\b",
    r"\bdeveloper needed\b",
    r"\blooking for\s+\d",
    r"\bwe are looking for\b",
    r"\bposition\b",
    r"\bvaccancy\b",
    r"\bvacancy\b",
    r"\bapply now\b",
]


def is_facebook_open_to_work_row(row):
    if row.get("source_site", "") != "facebook":
        return True
    text = clean_text(
        " ".join(
            [
                row.get("profile_name", ""),
                row.get("result_title", ""),
                row.get("short_description", ""),
            ]
        )
    ).lower()
    has_open_to_work = any(re.search(pattern, text) for pattern in OPEN_TO_WORK_PATTERNS)
    has_hiring_signal = any(re.search(pattern, text) for pattern in HIRING_PATTERNS)
    return has_open_to_work and not has_hiring_signal
