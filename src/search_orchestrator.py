import time

from src.dedupe import dedupe_rows
from src.tavily_client import search_tavily
from src.tavily_normalizer import normalize_tavily_items
from src.tavily_query_builder import build_tavily_query_variants


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
        row["location"] = query_info["location_input"]
        row["source_site"] = query_info["source_site"]
    return rows


def run_search(
    search_input,
    *,
    config,
    build_queries,
    normalize_serpapi_items,
    normalize_brave_items,
    search_serpapi,
    search_brave,
    row_filter,
    progress_callback=None,
):
    provider = search_input.get("provider") or config["provider"]
    requested_count = search_input.get("num") or config["default_num"]
    try:
        requested_count = int(requested_count)
    except (TypeError, ValueError):
        raise RuntimeError("num must be a number")
    if requested_count < 1:
        raise RuntimeError("num must be at least 1")

    if provider != "tavily" and requested_count > 20:
        raise RuntimeError(f"{provider} supports up to 20 results per search")

    base_queries = build_queries(search_input)
    expanded_queries = expand_queries_for_provider(provider, base_queries, requested_count)
    all_rows = []
    started_at = time.time()
    per_request_limit = min(requested_count, 20)

    for index, query_info in enumerate(expanded_queries, start=1):
        if progress_callback:
            progress_callback(index, len(expanded_queries), query_info, started_at, len(all_rows))

        query = query_info["query"]
        if provider == "serpapi":
            if not config["serpapi_api_key"]:
                raise RuntimeError("Missing SERPAPI_API_KEY in .env")
            payload = search_serpapi(config["serpapi_api_key"], query, per_request_limit)
            rows = normalize_serpapi_items(query, payload)
        elif provider == "brave":
            if not config["brave_api_key"]:
                raise RuntimeError("Missing BRAVE_SEARCH_API_KEY in .env")
            payload = search_brave(config["brave_api_key"], query, per_request_limit)
            rows = normalize_brave_items(query, payload)
        elif provider == "tavily":
            payload = search_tavily(config["tavily_api_key"], query, per_request_limit)
            rows = normalize_tavily_items(query, payload)
        else:
            raise RuntimeError(f"Unsupported provider: {provider}")

        rows = attach_query_context(rows, query_info)
        all_rows.extend([row for row in rows if row_filter(row)])

    rows = dedupe_rows(all_rows)[:requested_count]
    return {
        "provider": provider,
        "queries": expanded_queries,
        "rows": rows,
        "duration_seconds": time.time() - started_at,
    }
