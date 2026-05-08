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


def extract_profile_location(description, profile_name=""):
    lines = [clean_text(line) for line in clean_text(description).splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return ""

    normalized_name = clean_text(profile_name).lower()
    for line in lines[:8]:
        if normalized_name and line.lower() == normalized_name:
            continue
        if line.lower() in LOCATION_STOP_MARKERS:
            break
        if _looks_like_location_line(line):
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
