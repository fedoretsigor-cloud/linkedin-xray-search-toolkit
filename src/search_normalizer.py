import re
from urllib.parse import urlparse

from src.text_utils import clean_text

LINKEDIN_PROFILE_BLOCKED_HOSTS = {"business.linkedin.com", "www.business.linkedin.com"}
LINKEDIN_PROFILE_BLOCKED_SLUGS = {
    "en",
    "jobs",
    "company",
    "school",
    "learning",
    "pulse",
    "feed",
    "groups",
    "showcase",
}


def extract_name(title):
    parts = [part.strip() for part in clean_text(title).split(" - ") if part.strip()]
    if parts:
        return parts[0]
    return clean_text(title)


LOCATION_STOP_MARKERS = {
    "about",
    "experience",
    "education",
    "contact info",
    "connections",
    "followers",
}

NON_LOCATION_ROLE_MARKERS = {
    "analyst",
    "engineer",
    "developer",
    "consultant",
    "manager",
    "architect",
    "owner",
    "leader",
    "trading",
    "risk",
    "agile",
    "delivery",
    "technology",
    "systems",
    "experience",
}

HEADER_LOCATION_FOLLOWING_MARKERS = {
    "connections",
    "followers",
    "contact info",
    "about",
    "experience",
}

ORG_LINE_MARKERS = {
    "academy",
    "ai",
    "college",
    "company",
    "corp",
    "corporation",
    "inc",
    "institute",
    "ltd",
    "llc",
    "school",
    "university",
}

PLACE_CONNECTOR_WORDS = {"and", "of", "the", "de", "da", "do", "del", "la"}
PROFILE_SEGMENT_SEPARATOR = re.compile(r"\s+(?:-|\u2013|\u2014)\s+")
SOCIAL_COUNT_MARKERS = ("connection", "contact", "follower", "kontakt")


def _looks_like_location_line(value):
    line = clean_text(value)
    if not line:
        return False

    lower = line.lower()
    if len(line) > 80:
        return False
    if lower in LOCATION_STOP_MARKERS:
        return False
    if any(marker in lower for marker in ("connections", "followers", "contact info")):
        return False
    if line.startswith("[") or "http" in lower:
        return False
    if "|" in line:
        return False
    if any(char.isdigit() for char in line):
        return False
    if any(marker in lower for marker in NON_LOCATION_ROLE_MARKERS):
        return False

    explicit_location_markers = (
        "greater ",
        " metroplex",
        " area",
        " metropolitan area",
        " region",
        " united states",
        " usa",
        " germany",
        " poland",
        " india",
        " canada",
        " uk",
        " united kingdom",
    )
    if any(marker in lower for marker in explicit_location_markers):
        return True

    comma_parts = [part.strip() for part in line.split(",") if part.strip()]
    return 2 <= len(comma_parts) <= 4


def _is_word_like_token(token):
    normalized = token.strip(".,;:()[]{}").replace("'", "").replace("-", "")
    return bool(normalized) and normalized.isalpha()


def _is_place_like_phrase(value):
    line = clean_text(value)
    if not line or len(line) > 60:
        return False
    if any(char.isdigit() for char in line):
        return False
    if any(separator in line for separator in ("|", "@", "://")):
        return False

    tokens = [token.strip(".,;:()[]{}") for token in line.split() if token.strip(".,;:()[]{}")]
    if not 1 <= len(tokens) <= 5:
        return False
    if not all(_is_word_like_token(token) for token in tokens):
        return False
    if len(tokens) > 1 and all(token.isupper() for token in tokens):
        return False

    lowered_tokens = [token.lower().strip(".") for token in tokens]
    blocked_terms = NON_LOCATION_ROLE_MARKERS | ORG_LINE_MARKERS
    if any(token in blocked_terms for token in lowered_tokens):
        return False

    for token in tokens:
        lowered = token.lower().strip(".")
        if lowered in PLACE_CONNECTOR_WORDS:
            continue
        if token.isupper() and len(token) <= 3 and len(tokens) == 1:
            continue
        if token[:1].isupper() or token.islower():
            continue
        return False
    return True


def _has_header_location_context(index, lines):
    if index <= 0 or index + 1 >= len(lines):
        return False

    previous_text = " ".join(lines[max(0, index - 2) : index]).lower()
    next_line = lines[index + 1].lower()
    has_headline_before = "|" in previous_text or any(
        marker in previous_text for marker in NON_LOCATION_ROLE_MARKERS
    )
    has_profile_marker_after = any(
        marker in next_line for marker in HEADER_LOCATION_FOLLOWING_MARKERS
    )
    return has_headline_before and has_profile_marker_after


def _looks_like_header_location_line(line, index, lines):
    if not _has_header_location_context(index, lines):
        return False
    return _is_place_like_phrase(line)


def _has_social_count_marker(value):
    lower = clean_text(value).lower()
    return any(char.isdigit() for char in lower) and any(
        marker in lower for marker in SOCIAL_COUNT_MARKERS
    )


def _field_value(segment):
    text = clean_text(segment)
    if ":" not in text:
        return text
    label, value = text.rsplit(":", 1)
    if len(label) > 45:
        return text
    return clean_text(value)


def _extract_location_before_social_count(description):
    segments = [
        clean_text(segment)
        for segment in PROFILE_SEGMENT_SEPARATOR.split(clean_text(description))
        if clean_text(segment)
    ]
    for index, segment in enumerate(segments):
        if index == 0 or not _has_social_count_marker(segment):
            continue
        candidate = _field_value(segments[index - 1])
        if _looks_like_location_line(candidate) or _is_place_like_phrase(candidate):
            return candidate
    return ""


def extract_profile_location(description, profile_name=""):
    social_context_location = _extract_location_before_social_count(description)
    if social_context_location:
        return social_context_location

    lines = [clean_text(line) for line in clean_text(description).splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return ""

    normalized_name = clean_text(profile_name).lower()
    for index, line in enumerate(lines[:8]):
        if normalized_name and line.lower() == normalized_name:
            continue
        if line.lower() in LOCATION_STOP_MARKERS:
            break
        if _looks_like_location_line(line) or _looks_like_header_location_line(line, index, lines):
            return line
    return ""


def extract_linkedin_metadata(url):
    parsed = urlparse(url or "")
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").strip()
    normalized_path = path.strip("/")
    parts = [part for part in normalized_path.split("/") if part]
    is_linkedin_host = host == "linkedin.com" or host.endswith(".linkedin.com")
    is_blocked_host = host in LINKEDIN_PROFILE_BLOCKED_HOSTS
    is_profile_path = (
        len(parts) >= 2
        and parts[0] == "in"
        and parts[1].lower() not in LINKEDIN_PROFILE_BLOCKED_SLUGS
    )
    return {
        "is_profile": is_linkedin_host and not is_blocked_host and is_profile_path,
        "host": host,
        "path_parts": parts,
    }


def normalize_serpapi_items(query, payload):
    items = payload.get("organic_results", [])
    normalized = []
    for item in items:
        title = clean_text(item.get("title", ""))
        link = item.get("link", "")
        description = clean_text(item.get("snippet", ""))
        linkedin_meta = extract_linkedin_metadata(link)
        normalized.append(
            {
                "search_query": clean_text(query),
                "profile_name": extract_name(title),
                "result_title": title,
                "profile_url": link,
                "is_linkedin_profile": linkedin_meta["is_profile"],
                "short_description": description,
                "location": extract_profile_location(description, extract_name(title)),
                "result_position": item.get("position", ""),
            }
        )
    return normalized


def normalize_bing_serpapi_items(query, payload):
    items = payload.get("organic_results", [])
    normalized = []
    for item in items:
        title = clean_text(item.get("title", ""))
        link = item.get("link") or item.get("url", "")
        description = clean_text(item.get("snippet") or item.get("description", ""))
        linkedin_meta = extract_linkedin_metadata(link)
        normalized.append(
            {
                "search_query": clean_text(query),
                "profile_name": extract_name(title),
                "result_title": title,
                "profile_url": link,
                "is_linkedin_profile": linkedin_meta["is_profile"],
                "short_description": description,
                "location": extract_profile_location(description, extract_name(title)),
                "result_position": item.get("position", ""),
            }
        )
    return normalized


def normalize_brave_items(query, payload):
    items = payload.get("web", {}).get("results", [])
    normalized = []
    for item in items:
        title = clean_text(item.get("title", ""))
        link = item.get("url", "")
        description = clean_text(item.get("description", ""))
        linkedin_meta = extract_linkedin_metadata(link)
        normalized.append(
            {
                "search_query": clean_text(query),
                "profile_name": extract_name(title),
                "result_title": title,
                "profile_url": link,
                "is_linkedin_profile": linkedin_meta["is_profile"],
                "short_description": description,
                "location": extract_profile_location(description, extract_name(title)),
                "result_position": "",
            }
        )
    return normalized


def normalize_serper_items(query, payload):
    items = payload.get("organic", [])
    normalized = []
    for item in items:
        title = clean_text(item.get("title", ""))
        link = item.get("link", "")
        description = clean_text(item.get("snippet", ""))
        linkedin_meta = extract_linkedin_metadata(link)
        normalized.append(
            {
                "search_query": clean_text(query),
                "profile_name": extract_name(title),
                "result_title": title,
                "profile_url": link,
                "is_linkedin_profile": linkedin_meta["is_profile"],
                "short_description": description,
                "location": extract_profile_location(description, extract_name(title)),
                "result_position": item.get("position", ""),
            }
        )
    return normalized
