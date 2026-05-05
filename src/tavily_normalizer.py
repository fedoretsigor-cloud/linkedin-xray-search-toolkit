from src.search_normalizer import extract_linkedin_metadata, extract_name
from src.text_utils import clean_text


def normalize_tavily_items(query, payload):
    items = payload.get("results", [])
    normalized = []
    for index, item in enumerate(items, start=1):
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
                "short_description": clean_text(item.get("content", "")),
                "result_position": index,
            }
        )
    return normalized
