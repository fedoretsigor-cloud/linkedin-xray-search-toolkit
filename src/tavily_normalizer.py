from urllib.parse import urlparse


def _clean_text(value):
    if not value:
        return ""
    return (
        str(value)
        .replace("ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ", "-")
        .replace("ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“", "-")
        .replace("ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\xa0", " ")
        .strip()
    )


def _extract_name(title):
    parts = [part.strip() for part in _clean_text(title).split(" - ") if part.strip()]
    if parts:
        return parts[0]
    return _clean_text(title)


def _extract_linkedin_metadata(url):
    parsed = urlparse(url or "")
    path = (parsed.path or "").strip()
    normalized_path = path.strip("/")
    parts = [part for part in normalized_path.split("/") if part]
    is_profile = len(parts) >= 2 and parts[0] == "in"
    return {"is_profile": is_profile}


def normalize_tavily_items(query, payload):
    items = payload.get("results", [])
    normalized = []
    for index, item in enumerate(items, start=1):
        title = _clean_text(item.get("title", ""))
        link = item.get("url", "")
        linkedin_meta = _extract_linkedin_metadata(link)
        normalized.append(
            {
                "search_query": _clean_text(query),
                "profile_name": _extract_name(title),
                "result_title": title,
                "profile_url": link,
                "is_linkedin_profile": linkedin_meta["is_profile"],
                "short_description": _clean_text(item.get("content", "")),
                "result_position": index,
            }
        )
    return normalized
