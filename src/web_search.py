import re
import uuid
from datetime import datetime, timezone

from src.enrichment import build_candidate_analysis
from src.scoring import score_candidate
from src.text_utils import clean_text


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
        "sources": payload.get("sources", ["linkedin"]),
        "experience": clean_text(payload.get("experience", "")),
        "availability": clean_text(payload.get("availability", "")),
        "results_limit": requested_num,
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

    search_input = {
        "titles": search["titles"],
        "skill_groups": [
            [part.strip() for part in group.split("|") if part.strip()]
            for group in search["tech_groups"]
        ] or [[]],
        "locations": search["locations"] or [""],
        "extras": [search["availability"]] if search["availability"] else [],
        "source_sites": search["sources"] or ["linkedin"],
        "num": requested_num,
        "provider": None,
    }
    search["stack_summary"] = ", ".join(search["tech_groups"])
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
                "stack": clean_text(row.get("technology", "")),
                "source": clean_text(row.get("source_site", "")),
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
        "search": search,
        "queries_count": len(search_result["queries"]),
        "duration_seconds": round(search_result["duration_seconds"], 2),
        "candidates": candidates,
    }
