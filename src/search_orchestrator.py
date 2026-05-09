import re
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
PAGINATED_PROVIDERS = {"serpapi", "bing_serpapi", "serper"}
SEARCH_DEPTH_PAGE_CAPS = {
    "standard": 1,
    "medium": 2,
    "extended": 3,
    "max": 5,
}
SEARCH_DEPTH_LABELS = {
    "standard": "Standard",
    "medium": "Medium",
    "extended": "Extended",
    "max": "Max",
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


def build_query_plan(providers, base_queries, requested_count, page_size, search_input):
    provider_queries = {}
    provider_page_caps = {}
    for provider in providers:
        provider_queries[provider] = expand_queries_for_provider(provider, base_queries, requested_count)
        provider_page_caps[provider] = page_cap_for_provider(provider, search_input, requested_count, page_size)

    plan = []
    max_pages = max(provider_page_caps.values() or [1])
    for page_index in range(max_pages):
        for provider in providers:
            if page_index >= provider_page_caps[provider]:
                continue
            for query_info in provider_queries[provider]:
                plan.append(add_pagination_context(query_info, provider, page_index, page_size))
    return plan


def attach_query_context(rows, query_info):
    for row in rows:
        row["role"] = query_info["title_input"]
        row["technology"] = query_info["skill_input"]
        row["target_location"] = query_info["location_input"]
        row["location"] = row.get("location", "")
        row["source_site"] = query_info["source_site"]
        row["search_page"] = query_info.get("page", 1)
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

    if len(providers) == 1 and providers[0] not in {"tavily", *PAGINATED_PROVIDERS} and requested_count > 20:
        raise RuntimeError(f"{providers[0]} supports up to 20 results per search")

    base_queries = build_queries(search_input)
    started_at = time.time()
    per_request_limit = min(requested_count, 20)
    query_plan = build_query_plan(providers, base_queries, requested_count, per_request_limit, search_input)
    executed_queries = []
    all_rows = []
    location_policy = search_input.get("location_policy") or "strict"
    target_locations = search_input.get("display_locations") or search_input.get("locations", [])
    provider_errors = []
    failed_providers = set()

    for index, query_info in enumerate(query_plan, start=1):
        if len(dedupe_rows(all_rows)) >= requested_count:
            break
        if progress_callback:
            progress_callback(index, len(query_plan), query_info, started_at, len(all_rows))

        query = query_info["query"]
        provider = query_info["provider"]
        if provider in failed_providers:
            continue
        executed_queries.append(query_info)
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
            elif provider == "brave":
                if not config["brave_api_key"]:
                    raise RuntimeError("Missing BRAVE_SEARCH_API_KEY in .env")
                payload = search_brave(config["brave_api_key"], query, per_request_limit)
                rows = normalize_brave_items(query, payload)
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
        rows = [annotate_location_match(row, target_locations) for row in rows]
        if location_policy == "strict":
            rows = [row for row in rows if row_matches_strict_locations(row, target_locations)]
        all_rows.extend([row for row in rows if row_filter(row)])

    rows = dedupe_rows(all_rows)[:requested_count]
    search_strategy = summarize_search_strategy(search_input, executed_queries)
    search_depth = str(search_input.get("search_depth") or "extended").strip().lower()
    search_strategy["search_depth"] = search_depth
    search_strategy["search_depth_label"] = SEARCH_DEPTH_LABELS.get(search_depth, "Extended")
    search_strategy["base_query_count"] = len(base_queries)
    search_strategy["provider_passes"] = int(len(query_plan) / max(len(base_queries), 1))
    search_strategy["planned_query_count"] = len(query_plan)
    search_strategy["executed_query_count"] = len(executed_queries)
    search_strategy["provider_errors"] = provider_errors
    return {
        "provider": "hybrid" if len(providers) > 1 else providers[0],
        "providers": providers,
        "queries": executed_queries,
        "search_strategy": search_strategy,
        "provider_errors": provider_errors,
        "rows": rows,
        "duration_seconds": time.time() - started_at,
    }
