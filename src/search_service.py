import csv
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlparse
import platform

if platform.system() == "Windows":
    import certifi_win32  # noqa: F401
import requests
from dotenv import load_dotenv

from src.xray_search import build_query


SERPAPI_URL = "https://serpapi.com/search.json"
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
SITE_FILTERS = {
    "linkedin": "site:linkedin.com/in/",
    "facebook": "site:facebook.com",
    "github": "site:github.com",
    "stackoverflow": "site:stackoverflow.com/users",
    "wellfound": "site:wellfound.com",
    "devpost": "site:devpost.com",
}
FACEBOOK_OPEN_TO_WORK_PATTERNS = [
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
FACEBOOK_HIRING_PATTERNS = [
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


def load_config():
    load_dotenv()
    provider = os.getenv("SEARCH_PROVIDER", "serpapi").strip().lower()
    default_num = os.getenv("SEARCH_RESULTS_PER_QUERY", "10").strip()
    return {
        "provider": provider,
        "default_num": int(default_num),
        "serpapi_api_key": os.getenv("SERPAPI_API_KEY", "").strip(),
        "brave_api_key": os.getenv("BRAVE_SEARCH_API_KEY", "").strip(),
        "tavily_api_key": os.getenv("TAVILY_API_KEY", "").strip(),
    }


def clean_text(value):
    if not value:
        return ""
    return (
        str(value)
        .replace("ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“", "-")
        .replace("Ã¢â‚¬â€œ", "-")
        .replace("Ã¢â‚¬â€", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\xa0", " ")
        .strip()
    )


def normalize_link(url):
    value = (url or "").strip()
    if not value:
        return value
    value = re.sub(r"[?#].*$", "", value)
    return value.rstrip("/")


def read_lines(path):
    if not path:
        return []
    file_path = Path(path)
    if not file_path.exists():
        raise RuntimeError(f"File not found: {file_path}")
    return [
        line.strip()
        for line in file_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def merge_unique(primary, secondary):
    seen = set()
    merged = []
    for item in list(primary) + list(secondary):
        key = item.strip().lower()
        if not item.strip() or key in seen:
            continue
        seen.add(key)
        merged.append(item.strip())
    return merged


def parse_skill_groups(values):
    groups = []
    seen = set()
    for value in values:
        raw = clean_text(value)
        if not raw:
            continue
        parts = [clean_text(part) for part in raw.split("|") if clean_text(part)]
        if not parts:
            continue
        key = " | ".join(part.lower() for part in parts)
        if key in seen:
            continue
        seen.add(key)
        groups.append(parts)
    return groups


def build_search_input_from_args(args):
    titles = list(args.title)
    if args.with_defaults:
        defaults = ["software engineer", "developer", "programmer"]
        for item in defaults:
            if item not in titles:
                titles.append(item)

    titles = merge_unique(titles, read_lines(args.titles_file))
    skill_groups = parse_skill_groups(merge_unique(args.skill, read_lines(args.skills_file)))
    locations = merge_unique(args.location, read_lines(args.locations_file))

    return {
        "titles": titles or [""],
        "skill_groups": skill_groups or [[]],
        "locations": locations or [""],
        "extras": list(args.extra),
        "source_sites": args.source_site or ["linkedin"],
        "num": args.num,
        "provider": args.provider,
    }


def build_queries(search_input):
    queries = []
    for title in search_input["titles"]:
        for skill_group in search_input["skill_groups"]:
            for location in search_input["locations"]:
                for source_site in search_input["source_sites"]:
                    query = build_query(
                        titles=[title] if title else [],
                        skills=skill_group,
                        locations=[location] if location else [],
                        extras=search_input["extras"],
                        site_filter=SITE_FILTERS[source_site],
                    )
                    queries.append(
                        {
                            "query": query,
                            "title_input": title,
                            "skill_input": " | ".join(skill_group),
                            "location_input": location,
                            "source_site": source_site,
                        }
                    )
    return queries


def search_serpapi(api_key, query, num):
    params = {"key": api_key, "engine": "google", "q": query, "num": num}
    response = requests.get(SERPAPI_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def search_brave(api_key, query, num):
    headers = {"Accept": "application/json", "X-Subscription-Token": api_key}
    params = {"q": query, "count": num}
    response = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def search_tavily(api_key, query, num):
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "query": query,
        "search_depth": "basic",
        "topic": "general",
        "max_results": num,
        "include_answer": False,
        "include_raw_content": False,
    }
    response = requests.post(TAVILY_SEARCH_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


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


def tavily_query_count_for_target_count(target_count):
    try:
        target_count = int(target_count)
    except (TypeError, ValueError):
        target_count = 20

    if target_count <= 20:
        return 1
    if target_count <= 40:
        return 2
    if target_count <= 60:
        return 3
    if target_count <= 100:
        return 5
    return 10


def build_tavily_query_variants(query, target_count):
    normalized_query = clean_text(query)
    variants = [normalized_query]
    boosters = [
        '"profile"',
        '"resume"',
        '"cv"',
        '"open to work"',
        '"engineer"',
        '"developer"',
        '"software engineer"',
        '"backend"',
        '"frontend"',
        '"remote"',
        '"candidate"',
        '"talent"',
    ]
    needed_queries = tavily_query_count_for_target_count(target_count)
    for booster in boosters:
        if len(variants) >= needed_queries:
            break
        variants.append(f"{normalized_query} {booster}".strip())
    return variants[:needed_queries]


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
    has_open_to_work = any(re.search(pattern, text) for pattern in FACEBOOK_OPEN_TO_WORK_PATTERNS)
    has_hiring_signal = any(re.search(pattern, text) for pattern in FACEBOOK_HIRING_PATTERNS)
    return has_open_to_work and not has_hiring_signal


def dedupe_rows(rows):
    seen = {}
    for row in rows:
        key = normalize_link(row.get("profile_url", ""))
        if not key:
            key = f"{row.get('result_title', '')}|{row.get('search_query', '')}"
        if key not in seen:
            seen[key] = row
    return list(seen.values())


def format_duration(seconds):
    seconds = max(int(seconds), 0)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def print_console_progress(current, total, query_info, started_at):
    width = 24
    filled = int(width * current / max(total, 1))
    bar = "#" * filled + "-" * (width - filled)
    elapsed = time.time() - started_at
    average = elapsed / max(current - 1, 1)
    remaining = average * max(total - current + 1, 0)
    print(f"[{bar}] {current}/{total}")
    print(
        "Site: {site} | Role: {role} | Tech: {tech} | Location: {location}".format(
            site=query_info.get("source_site", ""),
            role=query_info.get("title_input", "") or "-",
            tech=query_info.get("skill_input", "") or "-",
            location=query_info.get("location_input", "") or "-",
        )
    )
    print(f"Elapsed: {format_duration(elapsed)} | ETA: {format_duration(remaining)}")


def run_search(search_input, progress_callback=None, config=None):
    cfg = config or load_config()
    provider = search_input.get("provider") or cfg["provider"]
    requested_count = search_input.get("num") or cfg["default_num"]
    try:
        requested_count = int(requested_count)
    except (TypeError, ValueError):
        raise RuntimeError("num must be a number")
    if requested_count < 1:
        raise RuntimeError("num must be at least 1")

    if provider != "tavily" and requested_count > 20:
        raise RuntimeError(f"{provider} supports up to 20 results per search")

    base_queries = build_queries(search_input)
    expanded_queries = []
    if provider == "tavily":
        for query_info in base_queries:
            for variant_query in build_tavily_query_variants(query_info["query"], requested_count):
                variant_info = dict(query_info)
                variant_info["query"] = variant_query
                expanded_queries.append(variant_info)
    else:
        expanded_queries = list(base_queries)

    all_rows = []
    started_at = time.time()
    per_request_limit = min(requested_count, 20)

    for index, query_info in enumerate(expanded_queries, start=1):
        if progress_callback:
            progress_callback(index, len(expanded_queries), query_info, started_at, len(all_rows))

        query = query_info["query"]
        if provider == "serpapi":
            if not cfg["serpapi_api_key"]:
                raise RuntimeError("Missing SERPAPI_API_KEY in .env")
            payload = search_serpapi(cfg["serpapi_api_key"], query, per_request_limit)
            rows = normalize_serpapi_items(query, payload)
        elif provider == "brave":
            if not cfg["brave_api_key"]:
                raise RuntimeError("Missing BRAVE_SEARCH_API_KEY in .env")
            payload = search_brave(cfg["brave_api_key"], query, per_request_limit)
            rows = normalize_brave_items(query, payload)
        elif provider == "tavily":
            if not cfg["tavily_api_key"]:
                raise RuntimeError("Missing TAVILY_API_KEY in .env")
            payload = search_tavily(cfg["tavily_api_key"], query, per_request_limit)
            rows = normalize_tavily_items(query, payload)
        else:
            raise RuntimeError(f"Unsupported provider: {provider}")

        for row in rows:
            row["role"] = query_info["title_input"]
            row["technology"] = query_info["skill_input"]
            row["location"] = query_info["location_input"]
            row["source_site"] = query_info["source_site"]

        filtered_rows = [row for row in rows if is_facebook_open_to_work_row(row)]
        all_rows.extend(filtered_rows)

    rows = dedupe_rows(all_rows)[:requested_count]
    return {
        "provider": provider,
        "queries": expanded_queries,
        "rows": rows,
        "duration_seconds": time.time() - started_at,
    }


def save_csv(rows, output_path):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Search Query",
        "Source Site",
        "Role",
        "Technology",
        "Location",
        "Candidate Name",
        "Profile URL",
        "Is LinkedIn Profile",
        "Short Description",
    ]
    with output_file.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "Search Query": row.get("search_query", ""),
                    "Source Site": row.get("source_site", ""),
                    "Role": row.get("role", ""),
                    "Technology": row.get("technology", ""),
                    "Location": row.get("location", ""),
                    "Candidate Name": row.get("profile_name", ""),
                    "Profile URL": row.get("profile_url", ""),
                    "Is LinkedIn Profile": "Yes" if row.get("is_linkedin_profile", "") else "No",
                    "Short Description": row.get("short_description", ""),
                }
            )





