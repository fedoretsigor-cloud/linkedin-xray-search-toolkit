import re


def normalize_link(url):
    value = (url or "").strip()
    if not value:
        return value
    value = re.sub(r"[?#].*$", "", value)
    return value.rstrip("/")


def dedupe_rows(rows):
    seen = {}
    for row in rows:
        key = normalize_link(row.get("profile_url", ""))
        if not key:
            key = f"{row.get('result_title', '')}|{row.get('search_query', '')}"
        if key not in seen:
            seen[key] = row
    return list(seen.values())
