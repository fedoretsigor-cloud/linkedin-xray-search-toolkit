from src.search_normalizer import extract_linkedin_metadata, extract_name, extract_profile_location
from src.text_utils import clean_text


def normalize_tavily_items(query, payload):
    items = payload.get("results", [])
    normalized = []
    for index, item in enumerate(items, start=1):
        title = clean_text(item.get("title", ""))
        link = item.get("url", "")
        description = clean_text(item.get("content", ""))
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
                "result_position": index,
            }
        )
    return normalized
