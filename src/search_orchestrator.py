import time

import requests

from src.dedupe import dedupe_rows
from src.devpost_normalizer import normalize_devpost_rows
from src.location_policy import annotate_location_match, row_matches_strict_locations
from src.tavily_client import search_tavily
from src.tavily_normalizer import normalize_tavily_items
from src.tavily_query_builder import build_tavily_query_variants
from src.search_strategy import summarize_search_strategy


HYBRID_DEFAULT_PROVIDERS = ["tavily", "bing_serpapi"]
SUPPORTED_PROVIDERS = {"serpapi", "bing_serpapi", "brave", "tavily", "serper"}


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
                detail = payload.get("error", "")
            detail = detail or response.reason
        return {
            "provider": provider,
            "status_code": status_code,
            "message": detail or "Provider API error",
        }
    if isinstance(exc, requests.RequestException):
        return {
            "provider": provider,
            "status_code": "",
            "message": f"Network error: {exc.__class__.__name__}",
        }
    return {
        "provider": provider,
        "status_code": "",
        "message": str(exc),
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


def attach_query_context(rows, query_info):
    for row in rows:
        row["role"] = query_info["title_input"]
        row["technology"] = query_info["skill_input"]
        row["target_location"] = query_info["location_input"]
        row["location"] = row.get("location", "")
        row["source_site"] = query_info["source_site"]
    return rows


def run_search(
    search_input,
    *,
    config,
    build_queries,
    normalize_serpapi_items,
    normalize_bing_serpapi_items,
    normalize_brave_items,
    normalize_serper_items,
    search_serpapi,
    search_bing_serpapi,
    search_brave,
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

    if len(providers) == 1 and providers[0] != "tavily" and requested_count > 20:
        raise RuntimeError(f"{providers[0]} supports up to 20 results per search")

    base_queries = build_queries(search_input)
    expanded_queries = []
    for provider in providers:
        for query_info in expand_queries_for_provider(provider, base_queries, requested_count):
            expanded_info = dict(query_info)
            expanded_info["provider"] = provider
            expanded_queries.append(expanded_info)

    all_rows = []
    started_at = time.time()
    per_request_limit = min(requested_count, 20)
    location_policy = search_input.get("location_policy") or "strict"
    target_locations = search_input.get("display_locations") or search_input.get("locations", [])
    provider_errors = []
    failed_providers = set()

    for index, query_info in enumerate(expanded_queries, start=1):
        if progress_callback:
            progress_callback(index, len(expanded_queries), query_info, started_at, len(all_rows))

        query = query_info["query"]
        provider = query_info["provider"]
        if provider in failed_providers:
            continue
        try:
            if provider == "serpapi":
                if not config["serpapi_api_key"]:
                    raise RuntimeError("Missing SERPAPI_API_KEY in .env")
                payload = search_serpapi(config["serpapi_api_key"], query, per_request_limit)
                rows = normalize_serpapi_items(query, payload)
            elif provider == "bing_serpapi":
                if not config["serpapi_api_key"]:
                    raise RuntimeError("Missing SERPAPI_API_KEY in .env")
                payload = search_bing_serpapi(config["serpapi_api_key"], query, per_request_limit)
                rows = normalize_bing_serpapi_items(query, payload)
            elif provider == "brave":
                if not config["brave_api_key"]:
                    raise RuntimeError("Missing BRAVE_SEARCH_API_KEY in .env")
                payload = search_brave(config["brave_api_key"], query, per_request_limit)
                rows = normalize_brave_items(query, payload)
            elif provider == "serper":
                if not config["serper_api_key"]:
                    raise RuntimeError("Missing SERPER_API_KEY in .env")
                payload = search_serper(config["serper_api_key"], query, per_request_limit)
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
            if error.get("status_code") in {401, 403} or error.get("message", "").startswith("Missing "):
                failed_providers.add(provider)
            continue

        for row in rows:
            row["search_provider"] = provider
        rows = attach_query_context(rows, query_info)
        rows = normalize_devpost_rows(rows)
        rows = [annotate_location_match(row, target_locations) for row in rows]
        if location_policy == "strict":
            rows = [row for row in rows if row_matches_strict_locations(row, target_locations)]
        all_rows.extend([row for row in rows if row_filter(row)])

    rows = dedupe_rows(all_rows)[:requested_count]
    search_strategy = summarize_search_strategy(search_input, expanded_queries)
    search_strategy["provider_errors"] = provider_errors
    return {
        "provider": "hybrid" if len(providers) > 1 else providers[0],
        "providers": providers,
        "queries": expanded_queries,
        "search_strategy": search_strategy,
        "provider_errors": provider_errors,
        "rows": rows,
        "duration_seconds": time.time() - started_at,
    }
