import argparse
import csv
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
import certifi_win32  # noqa: F401

from xray_search import build_query


SERPAPI_URL = "https://serpapi.com/search.json"
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Search LinkedIn profiles through a search API and save results to CSV."
    )
    parser.add_argument("--title", action="append", default=[], help="Job title")
    parser.add_argument("--skill", action="append", default=[], help="Skill keyword")
    parser.add_argument("--location", action="append", default=[], help="Location")
    parser.add_argument("--extra", action="append", default=[], help="Extra keyword")
    parser.add_argument(
        "--with-defaults",
        action="store_true",
        help="Add common IT title synonyms automatically",
    )
    parser.add_argument(
        "--output",
        default="output/linkedin_profiles.csv",
        help="Output CSV path",
    )
    parser.add_argument(
        "--num",
        type=int,
        default=None,
        help="Number of results to request from the provider",
    )
    parser.add_argument(
        "--titles-file",
        default=None,
        help="Path to a text file with one job title per line",
    )
    parser.add_argument(
        "--skills-file",
        default=None,
        help="Path to a text file with one skill per line",
    )
    parser.add_argument(
        "--locations-file",
        default=None,
        help="Path to a text file with one location per line",
    )
    parser.add_argument(
        "--provider",
        choices=["serpapi", "brave"],
        default=None,
        help="Override the provider from .env",
    )
    return parser.parse_args()


def ensure_output_dir(output_path):
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    return output_file


def load_config():
    load_dotenv()

    provider = os.getenv("SEARCH_PROVIDER", "serpapi").strip().lower()
    default_num = os.getenv("SEARCH_RESULTS_PER_QUERY", "10").strip()

    return {
        "provider": provider,
        "default_num": int(default_num),
        "serpapi_api_key": os.getenv("SERPAPI_API_KEY", "").strip(),
        "brave_api_key": os.getenv("BRAVE_SEARCH_API_KEY", "").strip(),
    }


def build_titles(args):
    titles = list(args.title)
    if args.with_defaults:
        defaults = ["software engineer", "developer", "programmer"]
        for item in defaults:
            if item not in titles:
                titles.append(item)
    return titles


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


def build_queries(args):
    titles = merge_unique(build_titles(args), read_lines(args.titles_file))
    skills = merge_unique(args.skill, read_lines(args.skills_file))
    locations = merge_unique(args.location, read_lines(args.locations_file))
    extras = list(args.extra)

    if not titles:
        titles = [""]
    if not skills:
        skills = [""]
    if not locations:
        locations = [""]

    queries = []
    for title in titles:
        for skill in skills:
            for location in locations:
                query = build_query(
                    titles=[title] if title else [],
                    skills=[skill] if skill else [],
                    locations=[location] if location else [],
                    extras=extras,
                )
                queries.append(
                    {
                        "query": query,
                        "title_input": title,
                        "skill_input": skill,
                        "location_input": location,
                    }
                )
    return queries


def search_serpapi(api_key, query, num):
    params = {
        "key": api_key,
        "engine": "google",
        "q": query,
        "num": num,
    }
    response = requests.get(SERPAPI_URL, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def search_brave(api_key, query, num):
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key,
    }
    params = {
        "q": query,
        "count": num,
    }
    response = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def normalize_serpapi_items(query, payload):
    items = payload.get("organic_results", [])
    normalized = []
    for item in items:
        title = item.get("title", "")
        normalized.append(
            {
                "query": query,
                "title": title,
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
                "display_link": item.get("displayed_link", ""),
                "name": extract_name(title),
                "headline": extract_headline(title),
                "source": "serpapi",
            }
        )
    return normalized


def normalize_brave_items(query, payload):
    items = payload.get("web", {}).get("results", [])
    normalized = []
    for item in items:
        title = item.get("title", "")
        normalized.append(
            {
                "query": query,
                "title": title,
                "link": item.get("url", ""),
                "snippet": item.get("description", ""),
                "display_link": item.get("meta_url", {}).get("display", ""),
                "name": extract_name(title),
                "headline": extract_headline(title),
                "source": "brave",
            }
        )
    return normalized


def extract_name(title):
    cleaned = title.replace("â€“", "-").replace("–", "-")
    parts = [part.strip() for part in cleaned.split(" - ") if part.strip()]
    if parts:
        return parts[0]
    return title.strip()


def extract_headline(title):
    cleaned = title.replace("â€“", "-").replace("–", "-")
    parts = [part.strip() for part in cleaned.split(" - ") if part.strip()]
    if len(parts) > 1:
        return " - ".join(parts[1:])
    return ""


def normalize_link(url):
    value = (url or "").strip()
    if not value:
        return value
    value = re.sub(r"[?#].*$", "", value)
    return value.rstrip("/")


def dedupe_rows(rows):
    seen = {}
    for row in rows:
        key = normalize_link(row.get("link", ""))
        if not key:
            key = f"{row.get('title', '')}|{row.get('query', '')}"
        if key not in seen:
            seen[key] = row
    return list(seen.values())


def save_csv(rows, output_path):
    fieldnames = [
        "query",
        "title_input",
        "skill_input",
        "location_input",
        "name",
        "headline",
        "title",
        "link",
        "snippet",
        "display_link",
        "source",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    args = parse_args()

    try:
        config = load_config()
    except Exception as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(1)

    provider = args.provider or config["provider"]
    result_count = args.num or config["default_num"]
    if not 1 <= result_count <= 20:
        print("Error: --num must be between 1 and 20.", file=sys.stderr)
        raise SystemExit(1)

    queries = build_queries(args)
    all_rows = []
    try:
        for query_info in queries:
            query = query_info["query"]
            if provider == "serpapi":
                if not config["serpapi_api_key"]:
                    print("Configuration error: Missing SERPAPI_API_KEY in .env", file=sys.stderr)
                    raise SystemExit(1)
                payload = search_serpapi(
                    api_key=config["serpapi_api_key"],
                    query=query,
                    num=result_count,
                )
                rows = normalize_serpapi_items(query, payload)
            elif provider == "brave":
                if not config["brave_api_key"]:
                    print("Configuration error: Missing BRAVE_SEARCH_API_KEY in .env", file=sys.stderr)
                    raise SystemExit(1)
                payload = search_brave(
                    api_key=config["brave_api_key"],
                    query=query,
                    num=result_count,
                )
                rows = normalize_brave_items(query, payload)
            else:
                print(f"Configuration error: Unsupported provider '{provider}'", file=sys.stderr)
                raise SystemExit(1)

            for row in rows:
                row["title_input"] = query_info["title_input"]
                row["skill_input"] = query_info["skill_input"]
                row["location_input"] = query_info["location_input"]
            all_rows.extend(rows)
    except requests.HTTPError as exc:
        message = exc.response.text if exc.response is not None else str(exc)
        print(f"Provider API error: {message}", file=sys.stderr)
        raise SystemExit(1)
    except requests.RequestException as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        raise SystemExit(1)

    rows = dedupe_rows(all_rows)
    output_file = ensure_output_dir(args.output)
    save_csv(rows, output_file)

    print(f"Provider: {provider}")
    print(f"Queries: {len(queries)}")
    print(f"Saved {len(rows)} rows to {output_file}")


if __name__ == "__main__":
    main()
