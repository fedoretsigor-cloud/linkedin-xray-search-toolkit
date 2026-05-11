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
from src.search_clients import search_bing_serpapi, search_serpapi, search_serper
from src.search_normalizer import normalize_bing_serpapi_items, normalize_serpapi_items, normalize_serper_items
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

GROUPED_ANCHOR_WAVE_TYPES = {"evidence_core", "title_focus", "evidence_expansion"}


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
        "serper_api_key": os.getenv("SERPER_API_KEY", "").strip(),
        "tavily_api_key": os.getenv("TAVILY_API_KEY", "").strip(),
        "max_executed_call_cap": read_int_env("SEARCH_MAX_EXECUTED_CALL_CAP", 0),
        "location_verification_limit": read_int_env("LOCATION_VERIFICATION_LIMIT", 20),
        "location_verification_providers": parse_provider_list(os.getenv("LOCATION_VERIFICATION_PROVIDERS", "serper,serpapi")),
        "location_verification_target_providers": parse_provider_list(os.getenv("LOCATION_VERIFICATION_TARGET_PROVIDERS", "")),
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


def compact_skill_groups(skill_groups):
    return compact_search_input(
        {
            "titles": [""],
            "skill_groups": skill_groups or [[]],
            "locations": [""],
            "extras": [],
        }
    ).get("skill_groups", [[]])


def normalize_search_wave_types(values):
    if not values:
        return []
    if isinstance(values, str):
        raw_values = values.replace(";", ",").split(",")
    else:
        raw_values = values
    wave_types = []
    seen = set()
    for value in raw_values:
        wave_type = clean_text(value).lower().replace("-", "_").replace(" ", "_")
        if wave_type not in GROUPED_ANCHOR_WAVE_TYPES or wave_type in seen:
            continue
        seen.add(wave_type)
        wave_types.append(wave_type)
    return wave_types


def generic_wave_group_limit(target_count, wave_type):
    try:
        target_count = int(target_count)
    except (TypeError, ValueError):
        target_count = 20
    if wave_type == "evidence_expansion":
        if target_count >= 100:
            return 4
        if target_count > 40:
            return 3
        return 2
    if wave_type == "title_focus":
        if target_count >= 100:
            return 6
        if target_count > 40:
            return 4
        return 3
    if target_count >= 100:
        return 8
    if target_count > 40:
        return 5
    return 3


def generic_expansion_role_terms(role_pattern):
    base_terms = grouped_anchor_terms(role_pattern.get("role_terms", []))
    expansion_terms = [
        "Engineer",
        "Developer",
        "Consultant",
        "Specialist",
        "Lead",
        "Manager",
        "Architect",
        "Analyst",
        "Owner",
        "SME",
    ]
    return grouped_anchor_terms([*base_terms, *expansion_terms])


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
    wave_types = normalize_search_wave_types(
        search_input.get("query_wave_types") or search_input.get("search_wave_types")
    )
    if role_pattern.get("query_strategy") == "grouped_anchors":
        return build_grouped_anchor_queries(
            compacted_input=compacted_input,
            primary_title=primary_title,
            title_group=title_group,
            role_pattern=role_pattern,
            alternates_only=bool(search_input.get("grouped_anchor_alternates_only")),
            wave_types=wave_types,
        )
    if wave_types and role_pattern.get("mode") == "semantic":
        return build_generic_evidence_wave_queries(
            compacted_input=compacted_input,
            primary_title=primary_title,
            title_group=title_group,
            role_pattern=role_pattern,
            wave_types=wave_types,
            target_count=search_input.get("num", 20),
            alternate_skill_groups=compact_skill_groups(search_input.get("alternate_skill_groups", [])),
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


def build_grouped_anchor_queries(*, compacted_input, primary_title, title_group, role_pattern, alternates_only=False, wave_types=None):
    queries = []
    for location in compacted_input["locations"]:
        for source_site in compacted_input["source_sites"]:
            variant_infos = (
                build_grouped_anchor_wave_query_variants(
                    role_pattern=role_pattern,
                    wave_types=wave_types,
                    location=location,
                    extras=compacted_input["extras"],
                    site_filter=SITE_FILTERS[source_site],
                )
                if wave_types
                else build_grouped_anchor_alternate_query_variants(
                    role_pattern=role_pattern,
                    location=location,
                    extras=compacted_input["extras"],
                    site_filter=SITE_FILTERS[source_site],
                )
                if alternates_only
                else build_grouped_anchor_query_variants(
                    role_pattern=role_pattern,
                    location=location,
                    extras=compacted_input["extras"],
                    site_filter=SITE_FILTERS[source_site],
                )
            )
            for variant_info in variant_infos:
                query = variant_info["query"]
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
                        "skill_input": " | ".join(variant_info.get("terms", [])),
                        "query_group_label": variant_info.get("label", ""),
                        "wave_type": variant_info.get("wave_type", ""),
                        "wave_plan_enabled": bool(wave_types),
                        "location_input": location,
                        "source_site": source_site,
                    }
                )
    if not queries:
        raise RuntimeError("Could not build a Tavily-friendly grouped-anchor query under 400 characters. Please shorten role, tools, or location.")
    return queries


def build_generic_evidence_wave_queries(
    *,
    compacted_input,
    primary_title,
    title_group,
    role_pattern,
    wave_types,
    target_count,
    alternate_skill_groups=None,
):
    queries = []
    for location in compacted_input["locations"]:
        for source_site in compacted_input["source_sites"]:
            variant_infos = build_generic_evidence_wave_query_variants(
                role_pattern=role_pattern,
                title_group=title_group,
                skill_groups=compacted_input["skill_groups"],
                alternate_skill_groups=alternate_skill_groups or [],
                wave_types=wave_types,
                target_count=target_count,
                location=location,
                extras=compacted_input["extras"],
                site_filter=SITE_FILTERS[source_site],
            )
            for variant_info in variant_infos:
                query = variant_info["query"]
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
                        "skill_input": " | ".join(variant_info.get("terms", [])),
                        "query_group_label": variant_info.get("label", ""),
                        "wave_type": variant_info.get("wave_type", ""),
                        "wave_plan_enabled": True,
                        "location_input": location,
                        "source_site": source_site,
                    }
                )
    if not queries:
        raise RuntimeError("Could not build a Tavily-friendly evidence query under 400 characters. Please shorten role, skills, or location.")
    return queries


def build_generic_evidence_wave_query_variants(
    *,
    role_pattern,
    title_group,
    skill_groups,
    alternate_skill_groups,
    wave_types,
    target_count,
    location,
    extras,
    site_filter,
):
    variants = []
    seen = set()
    for wave_type in normalize_search_wave_types(wave_types):
        if wave_type == "evidence_expansion":
            source_groups = alternate_skill_groups or skill_groups
        else:
            source_groups = skill_groups
        limit = generic_wave_group_limit(target_count, wave_type)
        for skill_group in source_groups[:limit]:
            if wave_type == "title_focus":
                query = build_generic_title_focus_query(
                    title_group=title_group,
                    skill_group=skill_group,
                    location=location,
                    extras=extras,
                    site_filter=site_filter,
                )
                label = "Title Focus: " + generic_group_label(skill_group, role_pattern)
            else:
                query = build_generic_evidence_query(
                    role_pattern=role_pattern,
                    skill_group=skill_group,
                    wave_type=wave_type,
                    location=location,
                    extras=extras,
                    site_filter=site_filter,
                )
                label = f"{query_wave_label(wave_type)}: " + generic_group_label(skill_group, role_pattern)
            key = query.lower()
            if query and key not in seen:
                seen.add(key)
                variants.append(
                    {
                        "query": query,
                        "label": label,
                        "wave_type": wave_type,
                        "terms": grouped_anchor_terms(skill_group),
                    }
                )
    return variants


def query_wave_label(wave_type):
    labels = {
        "evidence_core": "Evidence Core",
        "title_focus": "Title Focus",
        "evidence_expansion": "Evidence Expansion",
    }
    return labels.get(wave_type, wave_type.replace("_", " ").title())


def generic_group_label(skill_group, role_pattern):
    terms = grouped_anchor_terms(skill_group)
    if terms:
        return " | ".join(terms)
    return role_pattern.get("family") or "Role evidence"


def build_generic_title_focus_query(*, title_group, skill_group, location, extras, site_filter):
    parts = [site_filter]
    title_query_group = build_or_group(grouped_anchor_terms(title_group))
    skill_query_group = build_or_group(grouped_anchor_terms(skill_group))
    for group in (title_query_group, skill_query_group):
        if group:
            parts.append(group)
    if location:
        parts.append(f"\"{location}\"")
    for extra in extras:
        extra = clean_text(extra)
        if extra:
            parts.append(f"\"{extra}\"")
    return " ".join(parts)


def build_generic_evidence_query(*, role_pattern, skill_group, wave_type, location, extras, site_filter):
    parts = [site_filter]
    core_group = build_or_group(grouped_anchor_terms(role_pattern.get("core_terms", [])))
    if wave_type == "evidence_expansion":
        role_group = build_or_group(generic_expansion_role_terms(role_pattern))
    else:
        role_group = build_or_group(grouped_anchor_terms(role_pattern.get("role_terms", [])))
    skill_query_group = build_or_group(grouped_anchor_terms(skill_group))
    for group in (core_group, role_group, skill_query_group):
        if group:
            parts.append(group)
    if location:
        parts.append(f"\"{location}\"")
    for extra in extras:
        extra = clean_text(extra)
        if extra:
            parts.append(f"\"{extra}\"")
    return " ".join(parts)


def build_grouped_anchor_wave_query_variants(*, role_pattern, wave_types, location, extras, site_filter):
    variants = []
    seen = set()
    for wave_type in normalize_search_wave_types(wave_types):
        if wave_type == "title_focus":
            wave_variants = build_grouped_anchor_query_variants(
                role_pattern=role_pattern,
                location=location,
                extras=extras,
                site_filter=site_filter,
            )
        else:
            wave_variants = build_grouped_anchor_evidence_query_variants(
                role_pattern=role_pattern,
                wave_type=wave_type,
                location=location,
                extras=extras,
                site_filter=site_filter,
            )
        for variant in wave_variants:
            query = variant.get("query", "")
            key = query.lower()
            if query and key not in seen:
                seen.add(key)
                variants.append(
                    {
                        **variant,
                        "wave_type": variant.get("wave_type") or wave_type,
                    }
                )
    return variants


def build_grouped_anchor_query_variants(*, role_pattern, location, extras, site_filter):
    variants = []
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
                variants.append(
                    {
                        "query": query,
                        "label": f"Title Focus: {domain_term}{f' + {tool_term}' if tool_term else ''}".strip(),
                        "wave_type": "title_focus",
                        "terms": grouped_anchor_terms(
                            [
                                *role_pattern.get("fixed_anchors", []),
                                domain_term,
                                tool_term,
                            ]
                        ),
                    }
                )

    broad_query = build_grouped_anchor_query(
        role_pattern={**role_pattern, "tool_terms": []},
        location=location,
        extras=extras,
        site_filter=site_filter,
    )
    key = broad_query.lower()
    if broad_query and key not in seen:
        variants.append(
            {
                "query": broad_query,
                "label": "Title Focus: grouped anchors",
                "wave_type": "title_focus",
                "terms": grouped_anchor_terms(
                    [
                        *role_pattern.get("fixed_anchors", []),
                        *role_pattern.get("domain_terms", []),
                    ]
                ),
            }
        )

    return variants


def build_grouped_anchor_alternate_query_variants(*, role_pattern, location, extras, site_filter):
    variants = []
    seen = set()
    for term_group in role_pattern.get("grouped_anchor_alternates", []) or []:
        terms = grouped_anchor_terms(term_group)
        if not terms:
            continue
        query = build_grouped_anchor_terms_query(
            role_pattern=role_pattern,
            terms=terms,
            location=location,
            extras=extras,
            site_filter=site_filter,
        )
        key = query.lower()
        if query and key not in seen:
            seen.add(key)
            variants.append(
                {
                    "query": query,
                    "label": "Alternate: " + " + ".join(terms),
                    "wave_type": "evidence_expansion",
                    "terms": terms,
                }
            )
    return variants


def build_grouped_anchor_evidence_query_variants(*, role_pattern, wave_type, location, extras, site_filter):
    variants = []
    seen = set()
    for group in role_pattern.get("evidence_query_groups", []) or []:
        if clean_text(group.get("wave_type", "")).lower() != wave_type:
            continue
        terms = evidence_query_group_terms(group)
        if not terms:
            continue
        query = build_evidence_group_query(
            group=group,
            location=location,
            extras=extras,
            site_filter=site_filter,
        )
        key = query.lower()
        if query and key not in seen:
            seen.add(key)
            variants.append(
                {
                    "query": query,
                    "label": group.get("label") or " + ".join(terms),
                    "wave_type": wave_type,
                    "terms": terms,
                }
            )
    return variants


def evidence_query_group_terms(group):
    terms = []
    terms.extend(grouped_anchor_terms(group.get("terms", [])))
    terms.extend(grouped_anchor_terms(group.get("required_terms", [])))
    for values in group.get("or_groups", []) or []:
        terms.extend(grouped_anchor_terms(values))
    return grouped_anchor_terms(terms)


def build_evidence_group_query(*, group, location, extras, site_filter):
    parts = [site_filter]
    for term in grouped_anchor_terms(group.get("required_terms", [])):
        parts.append(f"\"{term}\"")
    for values in group.get("or_groups", []) or []:
        or_group = build_or_group(grouped_anchor_terms(values))
        if or_group:
            parts.append(or_group)
    if location:
        parts.append(f"\"{location}\"")
    for extra in extras:
        extra = clean_text(extra)
        if extra:
            parts.append(f"\"{extra}\"")
    return " ".join(parts)


def grouped_anchor_terms(values):
    terms = []
    seen = set()
    for value in values or []:
        term = clean_text(value)
        key = term.lower()
        if term and key not in seen:
            seen.add(key)
            terms.append(term)
    return terms


def build_grouped_anchor_terms_query(*, role_pattern, terms, location, extras, site_filter):
    parts = [site_filter]
    title_pattern = role_pattern.get("title_pattern", "")
    if title_pattern:
        parts.append(title_pattern)
    for term in grouped_anchor_terms(terms):
        parts.append(f"\"{term}\"")
    if location:
        parts.append(f"\"{location}\"")
    for extra in extras:
        extra = clean_text(extra)
        if extra:
            parts.append(f"\"{extra}\"")
    return " ".join(parts)


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
        normalize_serper_items=normalize_serper_items,
        search_serpapi=search_serpapi,
        search_bing_serpapi=search_bing_serpapi,
        search_serper=search_serper,
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
