from urllib.parse import urlparse

from src.text_utils import clean_text


def extract_name(title):
    parts = [part.strip() for part in clean_text(title).split(" - ") if part.strip()]
    if parts:
        return parts[0]
    return clean_text(title)


def extract_linkedin_metadata(url):
    parsed = urlparse(url or "")
    path = (parsed.path or "").strip()
    normalized_path = path.strip("/")
    parts = [part for part in normalized_path.split("/") if part]
    is_profile = len(parts) >= 2 and parts[0] == "in"
    return {"is_profile": is_profile}


def normalize_serpapi_items(query, payload):
    items = payload.get("organic_results", [])
    normalized = []
    for item in items:
        title = clean_text(item.get("title", ""))
        link = item.get("link", "")
        linkedin_meta = extract_linkedin_metadata(link)
        normalized.append(
            {
                "search_query": clean_text(query),
                "profile_name": extract_name(title),
                "result_title": title,
                "profile_url": link,
                "is_linkedin_profile": linkedin_meta["is_profile"],
                "short_description": clean_text(item.get("snippet", "")),
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
        linkedin_meta = extract_linkedin_metadata(link)
        normalized.append(
            {
                "search_query": clean_text(query),
                "profile_name": extract_name(title),
                "result_title": title,
                "profile_url": link,
                "is_linkedin_profile": linkedin_meta["is_profile"],
                "short_description": clean_text(item.get("description", "")),
                "result_position": "",
            }
        )
    return normalized
