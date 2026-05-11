import re
import uuid
from datetime import datetime, timezone

from src.enrichment import build_candidate_analysis
from src.location_policy import build_location_query_values
from src.profile_evidence import N_A, extract_profile_role, extract_profile_stack
from src.query_group_expander import build_skill_group_plan
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

SEARCH_DEPTH_QUERY_WAVE_TYPES = {
    "standard": ["evidence_core", "title_focus"],
    "medium": ["evidence_core", "title_focus"],
    "extended": ["evidence_core", "title_focus"],
    "max": ["evidence_core", "title_focus", "evidence_expansion"],
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


def resolve_search_depth_query_wave_types(search_depth, role_pattern):
    if role_pattern.get("mode") != "semantic":
        return []
    if role_pattern.get("query_strategy") == "grouped_anchors" and not role_pattern.get("evidence_query_groups"):
        return []
    depth = clean_text(search_depth).lower() or "extended"
    return SEARCH_DEPTH_QUERY_WAVE_TYPES.get(depth, SEARCH_DEPTH_QUERY_WAVE_TYPES["extended"])


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
    skill_group_plan = build_skill_group_plan(skill_groups, role_pattern, requested_num)
    skill_groups = skill_group_plan["active_groups"]
    query_wave_types = resolve_search_depth_query_wave_types(search["search_depth"], role_pattern)

    search_input = {
        "titles": search["titles"],
        "skill_groups": skill_groups,
        "alternate_skill_groups": skill_group_plan["alternate_groups"],
        "locations": build_location_query_values(search["locations"]) or [""],
        "display_locations": search["locations"],
        "location_policy": search["location_policy"],
        "extras": [search["availability"]] if search["availability"] else [],
        "source_sites": search["sources"] or ["linkedin"],
        "num": requested_num,
        "provider": None,
        "providers": search["providers"],
        "search_depth": search["search_depth"],
        "query_wave_types": query_wave_types,
        "search_intent": search_intent,
        "role_pattern": role_pattern,
    }
    search["search_intent"] = search_intent
    search["role_pattern"] = role_pattern
    search["query_wave_types"] = query_wave_types
    search["stack_summary"] = ", ".join(search["tech_groups"])
    search["provider_summary"] = ", ".join(search["providers"])
    return search, search_input


def transform_candidates(rows, search):
    candidates = []
    for index, row in enumerate(rows, start=1):
        analysis = score_candidate(row, search)
        evidence_role = extract_profile_role(row) or N_A
        evidence_stack = extract_profile_stack(row, search) or N_A
        display_row = {
            **row,
            "display_role": evidence_role,
            "display_stack": evidence_stack,
        }
        candidates.append(
            {
                "id": f"cand-{index}",
                "name": clean_text(row.get("profile_name", "")) or "Unknown candidate",
                "role": evidence_role,
                "location": clean_text(row.get("location", "")),
                "location_match": row.get("location_match", {}),
                "stack": evidence_stack,
                "matched_role_query": clean_text(row.get("query_role") or row.get("role", "")),
                "matched_stack_query": clean_text(row.get("query_technology") or row.get("technology", "")),
                "query_group_label": clean_text(row.get("query_group_label", "")),
                "query_wave_type": clean_text(row.get("query_wave_type", "")),
                "query_wave_type_label": clean_text(row.get("query_wave_type_label", "")),
                "adaptive_wave_type": clean_text(row.get("adaptive_wave_type", "")),
                "adaptive_wave_type_label": clean_text(row.get("adaptive_wave_type_label", "")),
                "result_title": clean_text(row.get("result_title", "")),
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
                "analysis": build_candidate_analysis(display_row, search, analysis),
            }
        )
    return sorted(candidates, key=lambda item: item["score"], reverse=True)


def candidate_evidence_row(candidate):
    legacy_role = clean_text(candidate.get("role", ""))
    legacy_stack = clean_text(candidate.get("stack", ""))
    matched_role = clean_text(candidate.get("matched_role_query", ""))
    matched_stack = clean_text(candidate.get("matched_stack_query", ""))
    return {
        "profile_name": clean_text(candidate.get("name") or candidate.get("profile_name", "")),
        "result_title": clean_text(candidate.get("result_title", "")),
        "short_description": clean_text(candidate.get("short_description", "")),
        "location": clean_text(candidate.get("location", "")),
        "query_role": matched_role or legacy_role,
        "role": matched_role or legacy_role,
        "query_technology": matched_stack or legacy_stack,
        "technology": matched_stack or legacy_stack,
    }


def hydrate_candidate_evidence(candidate, search):
    if not isinstance(candidate, dict):
        return candidate
    row = candidate_evidence_row(candidate)
    evidence_role = extract_profile_role(row) or N_A
    evidence_stack = extract_profile_stack(row, search or {}) or N_A
    hydrated = dict(candidate)
    legacy_role = clean_text(candidate.get("role", ""))
    legacy_stack = clean_text(candidate.get("stack", ""))
    if not clean_text(hydrated.get("matched_role_query", "")) and legacy_role and legacy_role != evidence_role:
        hydrated["matched_role_query"] = legacy_role
    if not clean_text(hydrated.get("matched_stack_query", "")) and legacy_stack and legacy_stack != evidence_stack:
        hydrated["matched_stack_query"] = legacy_stack
    hydrated["role"] = evidence_role
    hydrated["stack"] = evidence_stack
    return hydrated


def hydrate_run_candidate_evidence(run):
    if not isinstance(run, dict):
        return run
    search = run.get("search", {}) if isinstance(run.get("search"), dict) else {}
    hydrated = dict(run)
    hydrated["candidates"] = [
        hydrate_candidate_evidence(candidate, search)
        for candidate in run.get("candidates", []) or []
    ]
    return hydrated


def build_run_record(search, search_result):
    candidates = transform_candidates(search_result["rows"], search)
    search_strategy = search_result.get("search_strategy", {})
    return {
        "id": uuid.uuid4().hex[:10],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_id": search.get("project_id", ""),
        "search": search,
        "requirement_url": search.get("requirement_url", ""),
        "requirement_brief": search.get("requirement_brief"),
        "confirmed_brief": search.get("confirmed_brief"),
        "search_strategy": search_strategy,
        "provider_contribution_report": search_strategy.get("provider_contribution_report", {}),
        "query_group_contribution_report": search_strategy.get("query_group_contribution_report", {}),
        "provider_errors": search_result.get("provider_errors", []),
        "queries": search_result["queries"],
        "queries_count": len(search_result["queries"]),
        "duration_seconds": round(search_result["duration_seconds"], 2),
        "candidates": candidates,
    }
