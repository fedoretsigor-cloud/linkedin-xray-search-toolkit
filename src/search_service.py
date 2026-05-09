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
from src.role_pattern_builder import build_role_pattern
from src.search_clients import search_bing_serpapi, search_brave, search_serpapi, search_serper, search_you
from src.search_normalizer import normalize_bing_serpapi_items, normalize_brave_items, normalize_serpapi_items, normalize_serper_items, normalize_you_items
from src.search_orchestrator import parse_provider_list, run_search as run_search_pipeline
from src.search_strategy import compact_search_input, is_query_within_limit
from src.text_utils import clean_text
from src.xray_search import build_or_group, build_pattern_query, build_query, build_query_from_title_pattern


SITE_FILTERS = {
    "linkedin": "site:linkedin.com/in/",
    "facebook": "site:facebook.com",
    "github": "site:github.com",
    "stackoverflow": "site:stackoverflow.com/users",
    "wellfound": "site:wellfound.com",
    "devpost": "site:devpost.com",
}


def read_int_env(name, default):
    try:
        return int(os.getenv(name, str(default)).strip() or default)
    except ValueError:
        return default


def load_config():
    load_dotenv()
    provider = os.getenv("SEARCH_PROVIDER", "serpapi").strip().lower()
    providers = parse_provider_list(os.getenv("SEARCH_PROVIDERS", ""))
    default_num = os.getenv("SEARCH_RESULTS_PER_QUERY", "10").strip()
    return {
        "provider": provider,
        "providers": providers,
        "default_num": int(default_num),
        "serpapi_api_key": os.getenv("SERPAPI_API_KEY", "").strip(),
        "brave_api_key": os.getenv("BRAVE_SEARCH_API_KEY", "").strip(),
        "serper_api_key": os.getenv("SERPER_API_KEY", "").strip(),
        "tavily_api_key": os.getenv("TAVILY_API_KEY", "").strip(),
        "you_api_key": os.getenv("YOU_API_KEY", "").strip(),
        "location_verification_limit": read_int_env("LOCATION_VERIFICATION_LIMIT", 20),
        "location_verification_providers": parse_provider_list(os.getenv("LOCATION_VERIFICATION_PROVIDERS", "serper,serpapi")),
        "location_verification_target_providers": parse_provider_list(os.getenv("LOCATION_VERIFICATION_TARGET_PROVIDERS", "you")),
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
    title_group = compacted_input["titles"]
    primary_title = title_group[0] if title_group and title_group[0] else ""
    title_variants = title_group[1:] if len(title_group) > 1 else []
    role_pattern = search_input.get("role_pattern") or build_role_pattern(primary_title, title_variants)
    if role_pattern.get("query_strategy") == "grouped_anchors":
        return build_grouped_anchor_queries(
            compacted_input=compacted_input,
            primary_title=primary_title,
            title_group=title_group,
            role_pattern=role_pattern,
        )

    for skill_group in compacted_input["skill_groups"]:
        for location in compacted_input["locations"]:
            for source_site in compacted_input["source_sites"]:
                query = ""
                title_pattern = role_pattern.get("title_pattern", "")
                selected_role_terms = list(role_pattern.get("role_terms", []))
                while title_pattern:
                    query = build_query_from_title_pattern(
                        title_pattern=title_pattern,
                        skills=skill_group,
                        locations=[location] if location else [],
                        extras=compacted_input["extras"],
                        site_filter=SITE_FILTERS[source_site],
                    )
                    if is_query_within_limit(query):
                        break
                    if role_pattern.get("mode") == "semantic" and selected_role_terms:
                        selected_role_terms = selected_role_terms[:-1]
                        trimmed_pattern = dict(role_pattern)
                        trimmed_pattern["role_terms"] = selected_role_terms
                        title_pattern = build_role_pattern(
                            " ".join(trimmed_pattern.get("core_terms", [])),
                            selected_role_terms,
                        )["title_pattern"]
                        continue
                    title_pattern = ""

                if not title_pattern or not is_query_within_limit(query):
                    selected_primary = primary_title
                    selected_variants = list(title_variants)
                    while selected_primary or selected_variants:
                        query = build_pattern_query(
                            primary_title=selected_primary,
                            title_variants=selected_variants,
                            skills=skill_group,
                            locations=[location] if location else [],
                            extras=compacted_input["extras"],
                            site_filter=SITE_FILTERS[source_site],
                        )
                        if is_query_within_limit(query):
                            title_pattern = " ".join([selected_primary, *selected_variants] if selected_primary else selected_variants)
                            break
                        if selected_variants:
                            selected_variants = selected_variants[:-1]
                        else:
                            selected_primary = ""

                if not title_pattern:
                    query = build_query(
                        titles=[],
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
                        "title_input": primary_title,
                        "title_group_input": " | ".join(title_group),
                        "title_pattern_input": role_pattern.get("title_pattern", ""),
                        "role_pattern_family": role_pattern.get("family", ""),
                        "role_pattern_mode": role_pattern.get("mode", ""),
                        "skill_input": " | ".join(skill_group),
                        "location_input": location,
                        "source_site": source_site,
                    }
                )
    if not queries:
        raise RuntimeError("Could not build a Tavily-friendly query under 400 characters. Please shorten role, skills, or location.")
    return queries


def build_grouped_anchor_queries(*, compacted_input, primary_title, title_group, role_pattern):
    queries = []
    for location in compacted_input["locations"]:
        for source_site in compacted_input["source_sites"]:
            skill_terms = [
                *role_pattern.get("fixed_anchors", []),
                *role_pattern.get("domain_terms", []),
                *role_pattern.get("tool_terms", []),
            ]
            for query in build_grouped_anchor_query_variants(
                role_pattern=role_pattern,
                location=location,
                extras=compacted_input["extras"],
                site_filter=SITE_FILTERS[source_site],
            ):
                if not is_query_within_limit(query):
                    continue
                queries.append(
                    {
                        "query": query,
                        "title_input": primary_title,
                        "title_group_input": " | ".join(title_group),
                        "title_pattern_input": role_pattern.get("title_pattern", ""),
                        "role_pattern_family": role_pattern.get("family", ""),
                        "role_pattern_mode": role_pattern.get("mode", ""),
                        "skill_input": " | ".join(skill_terms),
                        "location_input": location,
                        "source_site": source_site,
                    }
                )
    if not queries:
        raise RuntimeError("Could not build a Tavily-friendly grouped-anchor query under 400 characters. Please shorten role, tools, or location.")
    return queries


def build_grouped_anchor_query_variants(*, role_pattern, location, extras, site_filter):
    queries = []
    seen = set()
    for domain_term in role_pattern.get("domain_terms", []) or [""]:
        for tool_term in [*role_pattern.get("tool_terms", []), ""]:
            query = build_small_grouped_anchor_query(
                role_pattern=role_pattern,
                domain_term=domain_term,
                tool_term=tool_term,
                location=location,
                extras=extras,
                site_filter=site_filter,
            )
            key = query.lower()
            if query and key not in seen:
                seen.add(key)
                queries.append(query)

    broad_query = build_grouped_anchor_query(
        role_pattern={**role_pattern, "tool_terms": []},
        location=location,
        extras=extras,
        site_filter=site_filter,
    )
    key = broad_query.lower()
    if broad_query and key not in seen:
        queries.append(broad_query)

    return queries


def build_small_grouped_anchor_query(*, role_pattern, domain_term, tool_term, location, extras, site_filter):
    parts = [site_filter]
    title_pattern = role_pattern.get("title_pattern", "")
    fixed_anchors = role_pattern.get("fixed_anchors", [])

    if title_pattern:
        parts.append(title_pattern)
    for anchor in fixed_anchors:
        anchor = clean_text(anchor)
        if anchor:
            parts.append(f"\"{anchor}\"")
    for term in (domain_term, tool_term):
        term = clean_text(term)
        if term:
            parts.append(f"\"{term}\"")
    if location:
        parts.append(f"\"{location}\"")
    for extra in extras:
        extra = clean_text(extra)
        if extra:
            parts.append(f"\"{extra}\"")
    return " ".join(parts)


def build_grouped_anchor_query(*, role_pattern, location, extras, site_filter):
    parts = [site_filter]
    title_pattern = role_pattern.get("title_pattern", "")
    fixed_anchors = role_pattern.get("fixed_anchors", [])
    domain_group = build_or_group(role_pattern.get("domain_terms", []))
    tool_group = build_or_group(role_pattern.get("tool_terms", []))

    if title_pattern:
        parts.append(title_pattern)
    for anchor in fixed_anchors:
        anchor = clean_text(anchor)
        if anchor:
            parts.append(f"\"{anchor}\"")
    for group in (domain_group, tool_group):
        if group:
            parts.append(group)
    if location:
        parts.append(f"\"{location}\"")
    for extra in extras:
        extra = clean_text(extra)
        if extra:
            parts.append(f"\"{extra}\"")
    return " ".join(parts)


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
        "Provider: {provider} | Site: {site} | Role: {role} | Tech: {tech} | Location: {location}".format(
            provider=query_info.get("provider", "-"),
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
        normalize_bing_serpapi_items=normalize_bing_serpapi_items,
        normalize_brave_items=normalize_brave_items,
        normalize_serper_items=normalize_serper_items,
        normalize_you_items=normalize_you_items,
        search_serpapi=search_serpapi,
        search_bing_serpapi=search_bing_serpapi,
        search_brave=search_brave,
        search_serper=search_serper,
        search_you=search_you,
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
