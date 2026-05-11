import re
import time
from math import ceil
from urllib.parse import urlparse

import requests

from src.country_codes import country_metadata_from_target_locations
from src.dedupe import dedupe_rows
from src.devpost_normalizer import normalize_devpost_rows
from src.location_policy import annotate_location_match, row_matches_strict_locations
from src.text_utils import clean_text
from src.tavily_client import search_tavily
from src.tavily_normalizer import normalize_tavily_items
from src.tavily_query_builder import build_tavily_query_variants
from src.search_strategy import summarize_search_strategy


HYBRID_DEFAULT_PROVIDERS = ["tavily", "bing_serpapi"]
SUPPORTED_PROVIDERS = {"serpapi", "bing_serpapi", "tavily", "serper"}
PAGINATED_PROVIDERS = {"serpapi", "bing_serpapi", "serper"}
SEARCH_DEPTH_PAGE_CAPS = {
    "standard": 1,
    "medium": 2,
    "extended": 3,
    "max": 10,
}
SEARCH_DEPTH_LABELS = {
    "standard": "Standard",
    "medium": "Medium",
    "extended": "Extended",
    "max": "Max",
}
ADAPTIVE_WAVE_MIN_REQUESTED_COUNT = 100
ADAPTIVE_WAVE_LABELS = {
    1: "Focused groups",
    2: "Alternate groups",
    3: "Broad discovery",
}
CREDIT_ERROR_MARKERS = (
    "credit",
    "credits",
    "quota",
    "billing",
    "balance",
    "payment",
    "out of searches",
    "run out",
    "exceeded your plan",
    "monthly limit",
    "usage limit",
    "insufficient",
)
RATE_LIMIT_MARKERS = ("rate limit", "too many requests", "throttle")
AUTH_ERROR_MARKERS = ("invalid api key", "unauthorized", "forbidden", "missing api key")


def parse_provider_list(value):
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        raw_values = value
    else:
        raw_values = str(value).replace(";", ",").split(",")
    providers = []
    seen = set()
    for item in raw_values:
        provider = str(item).strip().lower()
        if provider and provider not in seen:
            seen.add(provider)
            providers.append(provider)
    return providers


def resolve_providers(search_input, config):
    requested_providers = parse_provider_list(search_input.get("providers"))
    if requested_providers:
        return requested_providers

    provider = (search_input.get("provider") or config.get("provider") or "serpapi").strip().lower()
    if provider == "hybrid":
        return parse_provider_list(config.get("providers")) or HYBRID_DEFAULT_PROVIDERS
    return parse_provider_list(provider)


def sanitize_provider_message(message):
    text = str(message or "")
    text = re.sub(r"(?i)(api[_-]?key=)[^\s&]+", r"\1***", text)
    text = re.sub(r"(?i)(x-api-key:\s*)[^\s]+", r"\1***", text)
    return text.strip()


def collect_error_text(value):
    if isinstance(value, dict):
        texts = []
        for key in ("error", "message", "detail", "description", "title"):
            if key in value:
                texts.append(collect_error_text(value.get(key)))
        if texts:
            return " ".join(text for text in texts if text)
        return " ".join(collect_error_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(collect_error_text(item) for item in value)
    if value is None:
        return ""
    return sanitize_provider_message(value)


def classify_provider_error(status_code, message):
    normalized = str(message or "").lower()
    if status_code == 402 or any(marker in normalized for marker in CREDIT_ERROR_MARKERS):
        return "credits"
    if status_code == 429 or any(marker in normalized for marker in RATE_LIMIT_MARKERS):
        return "rate_limit"
    if status_code in {401, 403} or any(marker in normalized for marker in AUTH_ERROR_MARKERS):
        return "auth"
    if normalized.startswith("missing "):
        return "configuration"
    return "api_error"


def build_provider_user_message(provider, kind, message):
    provider_label = provider.replace("_", " ")
    if kind == "credits":
        return f"{provider_label} has no credits/quota left. Search continued with the remaining providers."
    if kind == "rate_limit":
        return f"{provider_label} hit a rate limit. Try again later or use a lighter Search Depth."
    if kind == "auth":
        return f"{provider_label} rejected the API key or access. Check the provider key/settings."
    if kind == "configuration":
        return f"{provider_label} is not configured. Add the missing key in .env or choose another Search Depth."
    return f"{provider_label} returned an API error. Search continued with the remaining providers."


def describe_provider_error(provider, exc):
    if isinstance(exc, requests.HTTPError):
        response = exc.response
        status_code = response.status_code if response is not None else ""
        detail = ""
        if response is not None:
            try:
                payload = response.json()
            except ValueError:
                payload = {}
            if isinstance(payload, dict):
                detail = collect_error_text(payload)
            detail = detail or response.reason
        detail = sanitize_provider_message(detail or "Provider API error")
        kind = classify_provider_error(status_code, detail)
        return {
            "provider": provider,
            "status_code": status_code,
            "kind": kind,
            "message": detail,
            "user_message": build_provider_user_message(provider, kind, detail),
        }
    if isinstance(exc, requests.RequestException):
        message = f"Network error: {exc.__class__.__name__}"
        kind = classify_provider_error("", message)
        return {
            "provider": provider,
            "status_code": "",
            "kind": kind,
            "message": message,
            "user_message": build_provider_user_message(provider, kind, message),
        }
    message = sanitize_provider_message(str(exc))
    kind = classify_provider_error("", message)
    return {
        "provider": provider,
        "status_code": "",
        "kind": kind,
        "message": message,
        "user_message": build_provider_user_message(provider, kind, message),
    }


def expand_queries_for_provider(provider, base_queries, requested_count):
    if provider != "tavily":
        return list(base_queries)

    expanded_queries = []
    for query_info in base_queries:
        for variant_query in build_tavily_query_variants(query_info["query"], requested_count):
            variant_info = dict(query_info)
            variant_info["query"] = variant_query
            expanded_queries.append(variant_info)
    return expanded_queries


def page_cap_for_provider(provider, search_input, requested_count, page_size):
    if provider not in PAGINATED_PROVIDERS:
        return 1
    if requested_count <= page_size:
        return 1
    search_depth = str(search_input.get("search_depth") or "").strip().lower()
    return SEARCH_DEPTH_PAGE_CAPS.get(search_depth, SEARCH_DEPTH_PAGE_CAPS["extended"])


def add_pagination_context(query_info, provider, page_index, page_size):
    paginated_info = dict(query_info)
    paginated_info["provider"] = provider
    paginated_info["page"] = page_index + 1
    paginated_info["page_size"] = page_size
    if provider == "serpapi":
        paginated_info["start"] = page_index * page_size
    elif provider == "bing_serpapi":
        paginated_info["first"] = (page_index * page_size) + 1
    elif provider == "serper":
        paginated_info["serper_page"] = page_index + 1
    return paginated_info


def adaptive_wave_count(requested_count, base_query_count):
    if requested_count < ADAPTIVE_WAVE_MIN_REQUESTED_COUNT or base_query_count <= 1:
        return 1
    if requested_count >= 200 and base_query_count >= 3:
        return 3
    return min(2, base_query_count)


def split_queries_into_adaptive_waves(base_queries, requested_count):
    queries = list(base_queries or [])
    wave_count = adaptive_wave_count(requested_count, len(queries))
    if wave_count <= 1:
        return [
            {
                "wave": 1,
                "label": ADAPTIVE_WAVE_LABELS[1],
                "activation": "initial",
                "queries": queries,
            }
        ]

    chunk_size = max(ceil(len(queries) / wave_count), 1)
    waves = []
    for index in range(wave_count):
        chunk = queries[index * chunk_size : (index + 1) * chunk_size]
        if not chunk:
            continue
        wave_number = index + 1
        waves.append(
            {
                "wave": wave_number,
                "label": ADAPTIVE_WAVE_LABELS.get(wave_number, f"Wave {wave_number}"),
                "activation": "initial" if wave_number == 1 else "target_not_reached",
                "queries": chunk,
            }
        )
    return waves or [
        {
            "wave": 1,
            "label": ADAPTIVE_WAVE_LABELS[1],
            "activation": "initial",
            "queries": queries,
        }
    ]


def add_wave_context(query_info, wave):
    wave_info = dict(query_info)
    wave_info["adaptive_wave"] = wave["wave"]
    wave_info["adaptive_wave_label"] = wave["label"]
    wave_info["adaptive_wave_activation"] = wave["activation"]
    return wave_info


def build_query_plan(providers, query_waves, requested_count, page_size, search_input):
    provider_page_caps = {}
    for provider in providers:
        provider_page_caps[provider] = page_cap_for_provider(provider, search_input, requested_count, page_size)

    plan = []
    max_pages = max(provider_page_caps.values() or [1])
    for wave in query_waves:
        provider_queries = {
            provider: expand_queries_for_provider(provider, wave["queries"], requested_count)
            for provider in providers
        }
        for page_index in range(max_pages):
            for provider in providers:
                if page_index >= provider_page_caps[provider]:
                    continue
                for query_info in provider_queries[provider]:
                    paginated_info = add_pagination_context(query_info, provider, page_index, page_size)
                    plan.append(add_wave_context(paginated_info, wave))
    return plan


def build_adaptive_wave_summaries(query_waves, query_plan):
    planned_calls = {}
    for query_info in query_plan:
        wave_number = int(query_info.get("adaptive_wave", 1) or 1)
        planned_calls[wave_number] = planned_calls.get(wave_number, 0) + 1

    summaries = []
    for wave in query_waves:
        summaries.append(
            {
                "wave": wave["wave"],
                "label": wave["label"],
                "activation": wave["activation"],
                "base_query_count": len(wave["queries"]),
                "planned_calls": planned_calls.get(wave["wave"], 0),
                "executed_calls": 0,
                "raw_rows": 0,
                "quality_rows": 0,
                "accepted_rows": 0,
                "started_unique_candidates": None,
                "unique_candidates_after_wave": None,
                "status": "not_needed",
            }
        )
    return summaries


def finalize_adaptive_wave_summaries(wave_summaries, final_unique_count, requested_count):
    for summary in wave_summaries:
        if not summary["executed_calls"]:
            summary["status"] = "not_needed"
            continue
        if final_unique_count >= requested_count and summary["executed_calls"] < summary["planned_calls"]:
            summary["status"] = "stopped_at_target"
        else:
            summary["status"] = "completed"
        if summary["unique_candidates_after_wave"] is None:
            summary["unique_candidates_after_wave"] = final_unique_count
        if summary["started_unique_candidates"] is None:
            summary["started_unique_candidates"] = 0
    return wave_summaries


def attach_query_context(rows, query_info):
    for row in rows:
        row["role"] = query_info["title_input"]
        row["technology"] = query_info["skill_input"]
        row["target_location"] = query_info["location_input"]
        row["location"] = row.get("location", "")
        row["source_site"] = query_info["source_site"]
        row["search_page"] = query_info.get("page", 1)
    return rows


def linkedin_profile_key(url):
    parsed = urlparse(url or "")
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2 or parts[0].lower() != "in":
        return ""
    return parts[1].lower().strip()


def build_location_verification_query(row, target_locations):
    target_location = clean_text((target_locations or [""])[0])
    if not target_location:
        return ""

    profile_slug = linkedin_profile_key(row.get("profile_url", ""))
    profile_name = clean_text(row.get("profile_name", ""))
    profile_anchor = profile_slug or profile_name
    if not profile_anchor:
        return ""
    return f'site:linkedin.com/in/ "{profile_anchor}" "{target_location}"'


def build_diagnostics(verification_limit):
    return {
        "raw_rows": 0,
        "quality_rows": 0,
        "accepted_rows": 0,
        "strict_location_rejected": 0,
        "missing_current_location": 0,
        "conflicting_current_location": 0,
        "free_text_location_only": 0,
        "confirmed_location": 0,
        "verification_attempted": 0,
        "verification_confirmed": 0,
        "verification_limit": verification_limit,
        "by_provider": {},
    }


def provider_diagnostics(diagnostics, provider):
    providers = diagnostics.setdefault("by_provider", {})
    if provider not in providers:
        providers[provider] = {
            "raw_rows": 0,
            "quality_rows": 0,
            "accepted_rows": 0,
            "strict_location_rejected": 0,
            "missing_current_location": 0,
            "conflicting_current_location": 0,
            "free_text_location_only": 0,
            "confirmed_location": 0,
            "verification_attempted": 0,
            "verification_confirmed": 0,
        }
    return providers[provider]


def add_diagnostic(diagnostics, provider, key, count=1):
    diagnostics[key] = diagnostics.get(key, 0) + count
    provider_stats = provider_diagnostics(diagnostics, provider)
    provider_stats[key] = provider_stats.get(key, 0) + count


def count_items_by_provider(items, *, provider_key="provider", include_verification=True):
    counts = {}
    for item in items or []:
        if not include_verification and item.get("query_type") == "location_verification":
            continue
        provider = item.get(provider_key) or "unknown"
        counts[provider] = counts.get(provider, 0) + 1
    return counts


def ordered_provider_keys(providers, *provider_maps):
    ordered = []
    seen = set()
    for provider in providers or []:
        if provider and provider not in seen:
            ordered.append(provider)
            seen.add(provider)
    for provider_map in provider_maps:
        for provider in provider_map or {}:
            if provider and provider not in seen:
                ordered.append(provider)
                seen.add(provider)
    return ordered


def provider_warning_counts(provider_errors):
    counts = {}
    for error in provider_errors or []:
        provider = error.get("provider") or "unknown"
        counts[provider] = counts.get(provider, 0) + 1
    return counts


def build_provider_contribution_report(
    *,
    providers,
    query_plan,
    executed_queries,
    diagnostics,
    final_rows,
    provider_errors,
    requested_count,
    location_policy,
):
    by_provider = diagnostics.get("by_provider", {}) if isinstance(diagnostics, dict) else {}
    planned_calls = count_items_by_provider(query_plan, include_verification=False)
    executed_calls = count_items_by_provider(executed_queries, include_verification=False)
    verification_calls = count_items_by_provider(
        [item for item in executed_queries or [] if item.get("query_type") == "location_verification"],
        include_verification=True,
    )
    final_candidates = count_items_by_provider(final_rows, provider_key="search_provider")
    warnings = provider_warning_counts(provider_errors)
    provider_keys = ordered_provider_keys(
        providers,
        planned_calls,
        executed_calls,
        verification_calls,
        by_provider,
        final_candidates,
        warnings,
    )

    provider_rows = []
    for provider in provider_keys:
        stats = by_provider.get(provider, {})
        accepted_rows = int(stats.get("accepted_rows", 0) or 0)
        final_count = int(final_candidates.get(provider, 0) or 0)
        raw_rows = int(stats.get("raw_rows", 0) or 0)
        strict_rejected = int(stats.get("strict_location_rejected", 0) or 0)
        provider_rows.append(
            {
                "provider": provider,
                "planned_calls": int(planned_calls.get(provider, 0) or 0),
                "executed_calls": int(executed_calls.get(provider, 0) or 0),
                "verification_calls": int(verification_calls.get(provider, 0) or 0),
                "raw_rows": raw_rows,
                "quality_rows": int(stats.get("quality_rows", 0) or 0),
                "strict_location_rejected": strict_rejected,
                "accepted_rows": accepted_rows,
                "final_candidates": final_count,
                "unique_lift": final_count,
                "deduped_or_capped_out": max(accepted_rows - final_count, 0),
                "warning_count": int(warnings.get(provider, 0) or 0),
            }
        )

    totals = {
        "requested_candidates": int(requested_count or 0),
        "planned_calls": sum(item["planned_calls"] for item in provider_rows),
        "executed_calls": sum(item["executed_calls"] for item in provider_rows),
        "verification_calls": sum(item["verification_calls"] for item in provider_rows),
        "raw_rows": int((diagnostics or {}).get("raw_rows", 0) or 0),
        "quality_rows": int((diagnostics or {}).get("quality_rows", 0) or 0),
        "strict_location_rejected": int((diagnostics or {}).get("strict_location_rejected", 0) or 0),
        "accepted_rows": int((diagnostics or {}).get("accepted_rows", 0) or 0),
        "final_candidates": len(final_rows or []),
        "provider_warnings": len(provider_errors or []),
    }
    totals["deduped_or_capped_out"] = max(totals["accepted_rows"] - totals["final_candidates"], 0)

    return {
        "location_policy": location_policy,
        "providers": provider_rows,
        "totals": totals,
        "notes": [
            "Raw rows are provider results before quality and strict-location filtering.",
            "Accepted rows are quality rows that survived strict-location filtering.",
            "Final unique candidates are counted after dedupe and result-limit capping.",
            "Unique lift is attributed to the provider whose row survived dedupe first.",
        ],
    }


def add_location_rejection_diagnostics(diagnostics, provider, row):
    add_diagnostic(diagnostics, provider, "strict_location_rejected")
    match = row.get("location_match") or {}
    if match.get("current_location_missing"):
        add_diagnostic(diagnostics, provider, "missing_current_location")
    if match.get("current_location_conflict"):
        add_diagnostic(diagnostics, provider, "conflicting_current_location")
    if match.get("free_text_location_only"):
        add_diagnostic(diagnostics, provider, "free_text_location_only")


def verification_candidates(rows, target_locations, verification_state):
    if not target_locations:
        return []
    candidates = []
    for row in rows:
        if row_matches_strict_locations(row, target_locations):
            continue
        match = row.get("location_match") or {}
        should_verify = (
            match.get("current_location_missing")
            or match.get("current_location_conflict")
            or match.get("free_text_location_only")
        )
        if not should_verify:
            continue
        key = linkedin_profile_key(row.get("profile_url", "")) or clean_text(row.get("profile_name", "")).lower()
        if not key or key in verification_state["attempted_keys"]:
            continue
        candidates.append((key, row))
    return candidates


def resolve_location_verification_providers(config):
    providers = parse_provider_list(config.get("location_verification_providers"))
    return providers or ["serper", "serpapi"]


def resolve_location_verification_target_providers(config):
    providers = parse_provider_list(config.get("location_verification_target_providers"))
    return set(providers)


def verification_provider_is_configured(provider, config):
    if provider == "serper":
        return bool(config.get("serper_api_key"))
    if provider in {"serpapi", "bing_serpapi"}:
        return bool(config.get("serpapi_api_key"))
    if provider == "tavily":
        return bool(config.get("tavily_api_key"))
    return False


def apply_verified_location(row, verification_rows, target_locations, verification_query, verification_provider, location_metadata=None):
    expected_key = linkedin_profile_key(row.get("profile_url", ""))
    for verification_row in verification_rows:
        if expected_key and linkedin_profile_key(verification_row.get("profile_url", "")) != expected_key:
            continue
        verification_row = annotate_location_match(verification_row, target_locations, location_metadata)
        if not row_matches_strict_locations(verification_row, target_locations):
            continue
        row["location"] = verification_row.get("location", "") or row.get("location", "")
        row["location_match"] = dict(verification_row.get("location_match", {}))
        row["location_match"]["verified_by_provider"] = verification_provider
        row["location_match"]["verified_by_query"] = verification_query
        row["location_verification_query"] = verification_query
        row["location_verification_description"] = verification_row.get("short_description", "")
        return True
    return False


def search_location_verification_provider(
    provider,
    *,
    query,
    config,
    per_request_limit,
    normalize_serpapi_items,
    normalize_bing_serpapi_items,
    normalize_serper_items,
    search_serpapi,
    search_bing_serpapi,
    search_serper,
):
    limit = min(per_request_limit, 5)
    if provider == "serper":
        payload = search_serper(config["serper_api_key"], query, limit)
        return normalize_serper_items(query, payload)
    if provider == "serpapi":
        payload = search_serpapi(config["serpapi_api_key"], query, limit)
        return normalize_serpapi_items(query, payload)
    if provider == "bing_serpapi":
        payload = search_bing_serpapi(config["serpapi_api_key"], query, limit)
        return normalize_bing_serpapi_items(query, payload)
    raise RuntimeError(f"Unsupported location verification provider: {provider}")


def verify_candidate_locations(
    rows,
    *,
    target_locations,
    query_info,
    config,
    per_request_limit,
    location_metadata,
    normalize_serpapi_items,
    normalize_bing_serpapi_items,
    normalize_serper_items,
    search_serpapi,
    search_bing_serpapi,
    search_serper,
    executed_queries,
    provider_errors,
    diagnostics,
    verification_state,
):
    if not target_locations or not rows:
        return rows
    if verification_state["attempts"] >= verification_state["limit"]:
        return rows

    for key, row in verification_candidates(rows, target_locations, verification_state):
        if verification_state["attempts"] >= verification_state["limit"]:
            break
        verification_query = build_location_verification_query(row, target_locations)
        if not verification_query:
            verification_state["attempted_keys"].add(key)
            continue

        verification_state["attempted_keys"].add(key)
        for verification_provider in verification_state["providers"]:
            if verification_state["attempts"] >= verification_state["limit"]:
                break
            if not verification_provider_is_configured(verification_provider, config):
                continue

            verification_state["attempts"] += 1
            add_diagnostic(diagnostics, verification_provider, "verification_attempted")
            verification_query_info = dict(query_info)
            verification_query_info["provider"] = verification_provider
            verification_query_info["query"] = verification_query
            verification_query_info["query_type"] = "location_verification"
            verification_query_info["verification_for"] = row.get("profile_url", "")
            verification_query_info["page"] = 1
            verification_query_info["page_size"] = min(per_request_limit, 5)
            executed_queries.append(verification_query_info)

            try:
                verification_rows = search_location_verification_provider(
                    verification_provider,
                    query=verification_query,
                    config=config,
                    per_request_limit=per_request_limit,
                    normalize_serpapi_items=normalize_serpapi_items,
                    normalize_bing_serpapi_items=normalize_bing_serpapi_items,
                    normalize_serper_items=normalize_serper_items,
                    search_serpapi=search_serpapi,
                    search_bing_serpapi=search_bing_serpapi,
                    search_serper=search_serper,
                )
            except (RuntimeError, requests.RequestException) as exc:
                error = describe_provider_error(verification_provider, exc)
                if error not in provider_errors:
                    provider_errors.append(error)
                continue

            verification_rows = attach_query_context(verification_rows, verification_query_info)
            for verification_row in verification_rows:
                verification_row["search_provider"] = verification_provider

            if apply_verified_location(row, verification_rows, target_locations, verification_query, verification_provider, location_metadata):
                verification_state["confirmed"] += 1
                add_diagnostic(diagnostics, verification_provider, "verification_confirmed")
                break
    return rows


def run_search(
    search_input,
    *,
    config,
    build_queries,
    normalize_serpapi_items,
    normalize_bing_serpapi_items,
    normalize_serper_items,
    search_serpapi,
    search_bing_serpapi,
    search_serper,
    row_filter,
    progress_callback=None,
):
    providers = resolve_providers(search_input, config)
    if not providers:
        raise RuntimeError("At least one search provider is required")
    unsupported_providers = [provider for provider in providers if provider not in SUPPORTED_PROVIDERS]
    if unsupported_providers:
        raise RuntimeError(f"Unsupported provider: {', '.join(unsupported_providers)}")

    requested_count = search_input.get("num") or config["default_num"]
    try:
        requested_count = int(requested_count)
    except (TypeError, ValueError):
        raise RuntimeError("num must be a number")
    if requested_count < 1:
        raise RuntimeError("num must be at least 1")

    if len(providers) == 1 and providers[0] not in {"tavily", *PAGINATED_PROVIDERS} and requested_count > 20:
        raise RuntimeError(f"{providers[0]} supports up to 20 results per search")

    base_queries = build_queries(search_input)
    query_waves = split_queries_into_adaptive_waves(base_queries, requested_count)
    started_at = time.time()
    per_request_limit = min(requested_count, 20)
    query_plan = build_query_plan(providers, query_waves, requested_count, per_request_limit, search_input)
    adaptive_wave_summaries = build_adaptive_wave_summaries(query_waves, query_plan)
    adaptive_wave_map = {item["wave"]: item for item in adaptive_wave_summaries}
    executed_queries = []
    all_rows = []
    location_policy = search_input.get("location_policy") or "strict"
    target_locations = search_input.get("display_locations") or search_input.get("locations", [])
    provider_errors = []
    failed_providers = set()
    verification_limit = max(int(config.get("location_verification_limit", 20) or 0), 0)
    diagnostics = build_diagnostics(verification_limit)
    location_metadata = country_metadata_from_target_locations(target_locations)
    verification_state = {
        "attempts": 0,
        "confirmed": 0,
        "limit": verification_limit,
        "attempted_keys": set(),
        "providers": resolve_location_verification_providers(config),
        "target_providers": resolve_location_verification_target_providers(config),
    }

    for index, query_info in enumerate(query_plan, start=1):
        if len(dedupe_rows(all_rows)) >= requested_count:
            break
        if progress_callback:
            progress_callback(index, len(query_plan), query_info, started_at, len(all_rows))

        query = query_info["query"]
        provider = query_info["provider"]
        wave_number = int(query_info.get("adaptive_wave", 1) or 1)
        wave_summary = adaptive_wave_map.get(wave_number)
        if wave_summary and wave_summary["started_unique_candidates"] is None:
            wave_summary["started_unique_candidates"] = len(dedupe_rows(all_rows))
        if provider in failed_providers:
            continue
        executed_queries.append(query_info)
        if wave_summary:
            wave_summary["executed_calls"] += 1
        try:
            if provider == "serpapi":
                if not config["serpapi_api_key"]:
                    raise RuntimeError("Missing SERPAPI_API_KEY in .env")
                payload = search_serpapi(config["serpapi_api_key"], query, per_request_limit, start=query_info.get("start"))
                rows = normalize_serpapi_items(query, payload)
            elif provider == "bing_serpapi":
                if not config["serpapi_api_key"]:
                    raise RuntimeError("Missing SERPAPI_API_KEY in .env")
                payload = search_bing_serpapi(config["serpapi_api_key"], query, per_request_limit, first=query_info.get("first"))
                rows = normalize_bing_serpapi_items(query, payload)
            elif provider == "serper":
                if not config["serper_api_key"]:
                    raise RuntimeError("Missing SERPER_API_KEY in .env")
                payload = search_serper(config["serper_api_key"], query, per_request_limit, page=query_info.get("serper_page"))
                rows = normalize_serper_items(query, payload)
            else:
                payload = search_tavily(config["tavily_api_key"], query, per_request_limit)
                rows = normalize_tavily_items(query, payload)
        except (RuntimeError, requests.RequestException) as exc:
            error = describe_provider_error(provider, exc)
            if len(providers) == 1:
                status = f" {error['status_code']}" if error.get("status_code") else ""
                raise RuntimeError(f"{provider} API error{status}: {error['message']}") from exc
            if error not in provider_errors:
                provider_errors.append(error)
            if error.get("kind") in {"credits", "rate_limit", "auth", "configuration"}:
                failed_providers.add(provider)
            continue

        for row in rows:
            row["search_provider"] = provider
        rows = attach_query_context(rows, query_info)
        rows = normalize_devpost_rows(rows)
        rows = [annotate_location_match(row, target_locations, location_metadata) for row in rows]
        add_diagnostic(diagnostics, provider, "raw_rows", len(rows))
        if wave_summary:
            wave_summary["raw_rows"] += len(rows)
        quality_rows = [row for row in rows if row_filter(row)]
        add_diagnostic(diagnostics, provider, "quality_rows", len(quality_rows))
        if wave_summary:
            wave_summary["quality_rows"] += len(quality_rows)
        if provider in verification_state["target_providers"] and location_policy == "strict" and verification_limit:
            quality_rows = verify_candidate_locations(
                quality_rows,
                target_locations=target_locations,
                query_info=query_info,
                config=config,
                per_request_limit=per_request_limit,
                location_metadata=location_metadata,
                normalize_serpapi_items=normalize_serpapi_items,
                normalize_bing_serpapi_items=normalize_bing_serpapi_items,
                normalize_serper_items=normalize_serper_items,
                search_serpapi=search_serpapi,
                search_bing_serpapi=search_bing_serpapi,
                search_serper=search_serper,
                executed_queries=executed_queries,
                provider_errors=provider_errors,
                diagnostics=diagnostics,
                verification_state=verification_state,
            )
        for row in quality_rows:
            if row_matches_strict_locations(row, target_locations):
                if target_locations:
                    add_diagnostic(diagnostics, provider, "confirmed_location")
            elif location_policy == "strict":
                add_location_rejection_diagnostics(diagnostics, provider, row)
        if location_policy == "strict":
            quality_rows = [row for row in quality_rows if row_matches_strict_locations(row, target_locations)]
        add_diagnostic(diagnostics, provider, "accepted_rows", len(quality_rows))
        all_rows.extend(quality_rows)
        if wave_summary:
            wave_summary["accepted_rows"] += len(quality_rows)
            wave_summary["unique_candidates_after_wave"] = len(dedupe_rows(all_rows))

    rows = dedupe_rows(all_rows)[:requested_count]
    adaptive_wave_summaries = finalize_adaptive_wave_summaries(
        adaptive_wave_summaries,
        len(rows),
        requested_count,
    )
    search_strategy = summarize_search_strategy(search_input, executed_queries)
    search_depth = str(search_input.get("search_depth") or "extended").strip().lower()
    search_strategy["search_depth"] = search_depth
    search_strategy["search_depth_label"] = SEARCH_DEPTH_LABELS.get(search_depth, "Extended")
    search_strategy["base_query_count"] = len(base_queries)
    search_strategy["provider_passes"] = int(len(query_plan) / max(len(base_queries), 1))
    search_strategy["planned_query_count"] = len(query_plan)
    search_strategy["executed_query_count"] = len(executed_queries)
    search_strategy["provider_errors"] = provider_errors
    search_strategy["adaptive_waves"] = {
        "enabled": requested_count >= ADAPTIVE_WAVE_MIN_REQUESTED_COUNT and len(query_waves) > 1,
        "planned_wave_count": len(query_waves),
        "completed_wave_count": len([item for item in adaptive_wave_summaries if item["executed_calls"]]),
        "waves": adaptive_wave_summaries,
    }
    search_strategy["country_location"] = location_metadata or {}
    search_strategy["location_verification_providers"] = verification_state["providers"]
    search_strategy["location_verification_target_providers"] = sorted(verification_state["target_providers"])
    diagnostics["final_candidates"] = len(rows)
    diagnostics["location_verification_providers"] = verification_state["providers"]
    diagnostics["location_verification_target_providers"] = sorted(verification_state["target_providers"])
    diagnostics["verification_attempted"] = verification_state["attempts"]
    diagnostics["verification_confirmed"] = verification_state["confirmed"]
    search_strategy["result_diagnostics"] = diagnostics
    search_strategy["provider_contribution_report"] = build_provider_contribution_report(
        providers=providers,
        query_plan=query_plan,
        executed_queries=executed_queries,
        diagnostics=diagnostics,
        final_rows=rows,
        provider_errors=provider_errors,
        requested_count=requested_count,
        location_policy=location_policy,
    )
    return {
        "provider": "hybrid" if len(providers) > 1 else providers[0],
        "providers": providers,
        "queries": executed_queries,
        "search_strategy": search_strategy,
        "provider_errors": provider_errors,
        "rows": rows,
        "duration_seconds": time.time() - started_at,
    }
