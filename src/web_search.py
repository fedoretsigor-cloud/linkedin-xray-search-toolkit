import re
import uuid
from datetime import datetime, timezone

from src.enrichment import build_candidate_analysis
from src.location_policy import build_location_query_values
from src.query_group_expander import expand_skill_groups
from src.role_pattern_builder import build_role_pattern
from src.scoring import score_candidate
from src.search_intent import build_search_intent
from src.text_utils import clean_text

SEARCH_DEPTH_PROVIDERS = {
    "standard": ["tavily"],
    "medium": ["tavily", "bing_serpapi"],
    "extended": ["tavily", "bing_serpapi", "serpapi"],
    "max": ["tavily", "bing_serpapi", "serpapi", "serper"],
}


def contains_cyrillic(values):
    pattern = re.compile(r"[\u0400-\u04FF]")
    for value in values:
        if value and pattern.search(str(value)):
            return True
    return False


def merge_role_titles(role, titles):
    merged = []
    seen = set()
    for value in [role, *titles]:
        title = clean_text(value)
        key = title.lower()
        if not title or key in seen:
            continue
        seen.add(key)
        merged.append(title)
    return merged


def sanitize_search_intent(search_intent):
    if not isinstance(search_intent, dict):
        return {}

    def clean_values(values):
        cleaned = []
        for value in values if isinstance(values, list) else []:
            text = clean_text(value)
            if text and text.lower() not in {"object object", "[object object]"}:
                cleaned.append(text)
        return cleaned

    return {
        "role_titles": clean_values(search_intent.get("role_titles", [])),
        "must_have_keywords": clean_values(search_intent.get("must_have_keywords", [])),
        "domain_keywords": clean_values(search_intent.get("domain_keywords", [])),
        "tool_keywords": clean_values(search_intent.get("tool_keywords", [])),
        "optional_keywords": clean_values(search_intent.get("optional_keywords", [])),
        "skill_groups": [
            clean_values(group)
            for group in search_intent.get("skill_groups", [])
            if clean_values(group)
        ],
    }


def resolve_search_depth_providers(search_depth, providers):
    cleaned_providers = [clean_text(value).lower() for value in providers or [] if clean_text(value)]
    if cleaned_providers:
        return cleaned_providers
    return SEARCH_DEPTH_PROVIDERS.get(clean_text(search_depth).lower(), SEARCH_DEPTH_PROVIDERS["extended"])


def build_web_search_request(payload, default_results):
    requested_num = payload.get("num", default_results)
    try:
        requested_num = int(requested_num)
    except (TypeError, ValueError):
        raise RuntimeError("Search results limit must be a number")

    search = {
        "role": clean_text(payload.get("role", "")),
        "titles": [clean_text(value) for value in payload.get("titles", []) if clean_text(value)],
        "tech_groups": [clean_text(value) for value in payload.get("tech_groups", []) if clean_text(value)],
        "locations": [clean_text(value) for value in payload.get("locations", []) if clean_text(value)],
        "location_policy": clean_text(payload.get("location_policy", "strict")).lower() or "strict",
        "sources": payload.get("sources", ["linkedin"]),
        "search_depth": clean_text(payload.get("search_depth", "extended")).lower() or "extended",
        "providers": resolve_search_depth_providers(payload.get("search_depth", "extended"), payload.get("providers", [])),
        "experience": clean_text(payload.get("experience", "")),
        "availability": clean_text(payload.get("availability", "")),
        "results_limit": requested_num,
        "project_id": clean_text(payload.get("project_id", "")),
        "requirement_url": clean_text(payload.get("requirement_url", "")),
        "requirement_brief": payload.get("requirement_brief") or None,
        "confirmed_brief": payload.get("confirmed_brief") or None,
    }

    validation_values = [
        search["role"],
        *search["titles"],
        *search["tech_groups"],
        *search["locations"],
        search["experience"],
        search["availability"],
    ]
    if contains_cyrillic(validation_values):
        raise RuntimeError("Please use English only.")

    search["titles"] = merge_role_titles(search["role"], search["titles"])
    if not search["titles"]:
        raise RuntimeError("At least one role/title is required")

    confirmed_brief = search["confirmed_brief"] or {}
    search_intent = sanitize_search_intent(
        confirmed_brief.get("search_intent") or (build_search_intent(confirmed_brief) if confirmed_brief else {})
    )
    skill_groups = search_intent.get("skill_groups") or [
        [part.strip() for part in group.split("|") if part.strip()]
        for group in search["tech_groups"]
    ] or [[]]
    role_pattern = build_role_pattern(
        search["role"],
        search["titles"][1:],
        context={
            "confirmed_brief": confirmed_brief,
            "requirement_brief": search.get("requirement_brief"),
            "search_intent": search_intent,
            "tech_groups": search["tech_groups"],
        },
    )
    skill_groups = expand_skill_groups(skill_groups, role_pattern, requested_num)

    search_input = {
        "titles": search["titles"],
        "skill_groups": skill_groups,
        "locations": build_location_query_values(search["locations"]) or [""],
        "display_locations": search["locations"],
        "location_policy": search["location_policy"],
        "extras": [search["availability"]] if search["availability"] else [],
        "source_sites": search["sources"] or ["linkedin"],
        "num": requested_num,
        "provider": None,
        "providers": search["providers"],
        "search_intent": search_intent,
        "role_pattern": role_pattern,
    }
    search["search_intent"] = search_intent
    search["role_pattern"] = role_pattern
    search["stack_summary"] = ", ".join(search["tech_groups"])
    search["provider_summary"] = ", ".join(search["providers"])
    return search, search_input


def transform_candidates(rows, search):
    candidates = []
    for index, row in enumerate(rows, start=1):
        analysis = score_candidate(row, search)
        candidates.append(
            {
                "id": f"cand-{index}",
                "name": clean_text(row.get("profile_name", "")) or "Unknown candidate",
                "role": clean_text(row.get("role", "")),
                "location": clean_text(row.get("location", "")),
                "location_match": row.get("location_match", {}),
                "stack": clean_text(row.get("technology", "")),
                "source": clean_text(row.get("source_site", "")),
                "search_provider": clean_text(row.get("search_provider", "")),
                "status": analysis["status"],
                "score": analysis["score"],
                "profile_url": row.get("profile_url", ""),
                "short_description": clean_text(row.get("short_description", "")),
                "project_title": clean_text(row.get("project_title", "")),
                "candidate_type": clean_text(row.get("candidate_type", "")),
                "maker_extraction_status": clean_text(row.get("maker_extraction_status", "")),
                "is_linkedin_profile": "Yes" if row.get("is_linkedin_profile") else "No",
                "search_query": clean_text(row.get("search_query", "")),
                "analysis": build_candidate_analysis(row, search, analysis),
            }
        )
    return sorted(candidates, key=lambda item: item["score"], reverse=True)


def build_run_record(search, search_result):
    candidates = transform_candidates(search_result["rows"], search)
    return {
        "id": uuid.uuid4().hex[:10],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_id": search.get("project_id", ""),
        "search": search,
        "requirement_url": search.get("requirement_url", ""),
        "requirement_brief": search.get("requirement_brief"),
        "confirmed_brief": search.get("confirmed_brief"),
        "search_strategy": search_result.get("search_strategy", {}),
        "provider_errors": search_result.get("provider_errors", []),
        "queries_count": len(search_result["queries"]),
        "duration_seconds": round(search_result["duration_seconds"], 2),
        "candidates": candidates,
    }
