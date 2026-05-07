import csv
import os
import platform
import time
from pathlib import Path

if platform.system() == "Windows":
    import certifi_win32  # noqa: F401
from dotenv import load_dotenv

from src.facebook_filter import is_facebook_open_to_work_row
from src.result_quality import is_quality_search_row
from src.search_clients import search_brave, search_serpapi
from src.search_normalizer import normalize_brave_items, normalize_serpapi_items
from src.search_orchestrator import run_search as run_search_pipeline
from src.search_strategy import compact_search_input, is_query_within_limit
from src.text_utils import clean_text
from src.xray_search import build_query


SITE_FILTERS = {
    "linkedin": "site:linkedin.com/in/",
    "facebook": "site:facebook.com",
    "github": "site:github.com",
    "stackoverflow": "site:stackoverflow.com/users",
    "wellfound": "site:wellfound.com",
    "devpost": "site:devpost.com",
}


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
    compacted_input = compact_search_input(search_input)
    for title in compacted_input["titles"]:
        for skill_group in compacted_input["skill_groups"]:
            for location in compacted_input["locations"]:
                for source_site in compacted_input["source_sites"]:
                    query = build_query(
                        titles=[title] if title else [],
                        skills=skill_group,
                        locations=[location] if location else [],
                        extras=compacted_input["extras"],
                        site_filter=SITE_FILTERS[source_site],
                    )
                    if not is_query_within_limit(query):
                        continue
                    queries.append(
                        {
                            "query": query,
                            "title_input": title,
                            "skill_input": " | ".join(skill_group),
                            "location_input": location,
                            "source_site": source_site,
                        }
                    )
    if not queries:
        raise RuntimeError("Could not build a Tavily-friendly query under 400 characters. Please shorten role, skills, or location.")
    return queries


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
    return run_search_pipeline(
        search_input,
        config=config or load_config(),
        build_queries=build_queries,
        normalize_serpapi_items=normalize_serpapi_items,
        normalize_brave_items=normalize_brave_items,
        search_serpapi=search_serpapi,
        search_brave=search_brave,
        row_filter=lambda row: is_facebook_open_to_work_row(row) and is_quality_search_row(row),
        progress_callback=progress_callback,
    )


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
