from src.text_utils import clean_text


MAX_TITLE_LENGTH = 80
MAX_SKILL_LENGTH = 45
MAX_LOCATION_LENGTH = 60
MAX_SKILLS_PER_QUERY = 3
MAX_TAVILY_QUERY_LENGTH = 380


def compact_phrase(value, max_length):
    text = clean_search_phrase(value)
    if len(text) <= max_length:
        return text
    separators = ["(", " - ", " | ", " / ", ",", ":"]
    for separator in separators:
        if separator in text:
            candidate = clean_search_phrase(text.split(separator, 1)[0])
            if candidate and len(candidate) <= max_length:
                return candidate
    return clean_search_phrase(text[:max_length].rsplit(" ", 1)[0] or text[:max_length])


def clean_search_phrase(value):
    return clean_text(value).strip(" ,;:()[]{}-")


def dedupe_values(values):
    deduped = []
    seen = set()
    for value in values:
        text = clean_text(value)
        key = text.lower()
        if not text or key in seen:
            continue
        seen.add(key)
        deduped.append(text)
    return deduped


def split_skill_groups(skill_groups, max_skills_per_query=MAX_SKILLS_PER_QUERY):
    compact_groups = []
    for group in skill_groups or [[]]:
        skills = [
            compact_phrase(skill, MAX_SKILL_LENGTH)
            for skill in group
            if compact_phrase(skill, MAX_SKILL_LENGTH)
        ]
        skills = dedupe_values(skills)
        if not skills:
            compact_groups.append([])
            continue
        for index in range(0, len(skills), max_skills_per_query):
            compact_groups.append(skills[index : index + max_skills_per_query])
    return compact_groups or [[]]


def compact_search_input(search_input):
    compacted = dict(search_input)
    compacted["titles"] = dedupe_values(
        compact_phrase(title, MAX_TITLE_LENGTH)
        for title in search_input.get("titles", [])
    ) or [""]
    compacted["locations"] = dedupe_values(
        compact_phrase(location, MAX_LOCATION_LENGTH)
        for location in search_input.get("locations", [])
    ) or [""]
    compacted["skill_groups"] = split_skill_groups(search_input.get("skill_groups", [[]]))
    compacted["extras"] = dedupe_values(
        compact_phrase(extra, MAX_SKILL_LENGTH)
        for extra in search_input.get("extras", [])
    )
    return compacted


def is_query_within_limit(query, max_length=MAX_TAVILY_QUERY_LENGTH):
    return len(clean_text(query)) <= max_length


def summarize_search_strategy(search_input, queries):
    compacted = compact_search_input(search_input)
    return {
        "titles": compacted.get("titles", []),
        "skill_groups": compacted.get("skill_groups", []),
        "search_intent": search_input.get("search_intent", {}),
        "locations": compacted.get("locations", []),
        "location_policy": search_input.get("location_policy", "strict"),
        "sources": compacted.get("source_sites", []),
        "query_count": len(queries),
        "sample_queries": [item.get("query", "") for item in queries[:5]],
        "max_query_length": max([len(item.get("query", "")) for item in queries] or [0]),
    }
