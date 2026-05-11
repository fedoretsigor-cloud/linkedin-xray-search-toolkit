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
QUERY_WAVE_TYPE_LABELS = {
    "evidence_core": "Evidence Core",
    "title_focus": "Title Focus",
    "evidence_expansion": "Evidence Expansion",
    "mixed": "Mixed",
}
QUERY_WAVE_TYPE_ORDER = ("evidence_core", "title_focus", "evidence_expansion")
DEFAULT_QUERY_WAVE_TYPE = "title_focus"
MAX_SEARCH_CALL_CAPS = (
    (200, 480),
    (100, 320),
    (50, 160),
    (0, 80),
)
MAX_EXPANSION_MIN_CALLS = 20
ADAPTIVE_SELECTION_STOPWORDS = {
    "and",
    "api",
    "cloud",
    "engineer",
    "engineering",
    "for",
    "in",
    "linkedin",
    "or",
    "profile",
    "site",
    "software",
    "the",
    "with",
}
ADAPTIVE_REPLACEMENT_MAX_GROUPS = 2
ADAPTIVE_REPLACEMENT_STRONG_SIMILARITY_CEILING = 0.4
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


def positive_int(value, default=0):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def search_stop_reason_label(stop_reason):
    labels = {
        "target_reached": "Target reached",
        "call_cap_reached": "Call cap reached",
        "plan_exhausted": "Plan exhausted",
    }
    return labels.get(stop_reason, stop_reason or "Plan exhausted")


def first_query_index_for_wave_type(query_plan, wave_type):
    normalized_wave_type = normalize_query_wave_type(wave_type)
    for index, query_info in enumerate(query_plan or [], start=1):
        if normalize_query_wave_type(query_info.get("wave_type")) == normalized_wave_type:
            return index
    return 0


def default_max_search_call_cap(requested_count, query_plan):
    planned_count = len(query_plan or [])
    if not planned_count:
        return 0

    requested = positive_int(requested_count, 20)
    cap = planned_count
    for threshold, threshold_cap in MAX_SEARCH_CALL_CAPS:
        if requested >= threshold:
            cap = threshold_cap
            break

    expansion_start = first_query_index_for_wave_type(query_plan, "evidence_expansion")
    if expansion_start:
        expansion_budget = max(MAX_EXPANSION_MIN_CALLS, min(60, ceil(requested / 10)))
        cap = max(cap, expansion_start + expansion_budget - 1)
    return min(cap, planned_count)


def resolve_search_call_cap(search_input, config, query_plan, requested_count):
    planned_count = len(query_plan or [])
    if not planned_count:
        return 0

    search_depth = str(search_input.get("search_depth") or "extended").strip().lower()
    explicit_cap = positive_int(search_input.get("executed_call_cap"))
    if not explicit_cap and search_depth == "max":
        explicit_cap = positive_int(config.get("max_executed_call_cap"))
    if explicit_cap:
        return min(explicit_cap, planned_count)

    if search_depth == "max":
        return default_max_search_call_cap(requested_count, query_plan)
    return planned_count


def executed_search_call_count(executed_queries):
    return sum(1 for item in executed_queries or [] if item.get("query_type") != "location_verification")


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


def build_query_group_label(query_info, index):
    skill = clean_text(query_info.get("skill_input", ""))
    title = clean_text(query_info.get("title_input", ""))
    location = clean_text(query_info.get("location_input", ""))
    source = clean_text(query_info.get("source_site", ""))
    label = skill or title or f"Query group {index}"
    context = " / ".join(value for value in [source, location] if value)
    return f"{label} ({context})" if context else label


def normalize_query_wave_type(value, *, source=""):
    wave_type = clean_text(value).lower().replace("-", "_").replace(" ", "_")
    if wave_type in QUERY_WAVE_TYPE_LABELS:
        return wave_type
    if source == "adaptive_alternate":
        return "evidence_expansion"
    return DEFAULT_QUERY_WAVE_TYPE


def query_wave_type_label(wave_type):
    return QUERY_WAVE_TYPE_LABELS.get(normalize_query_wave_type(wave_type), QUERY_WAVE_TYPE_LABELS[DEFAULT_QUERY_WAVE_TYPE])


def annotate_query_groups(base_queries, *, start_index=1, id_prefix="group", source="planned", wave_type=None):
    annotated = []
    for index, query_info in enumerate(base_queries or [], start=start_index):
        group_info = dict(query_info)
        normalized_wave_type = normalize_query_wave_type(
            group_info.get("wave_type") or wave_type,
            source=source,
        )
        group_info["query_group_id"] = group_info.get("query_group_id") or f"{id_prefix}-{index}"
        group_info["query_group_index"] = int(group_info.get("query_group_index") or index)
        group_info["query_group_label"] = group_info.get("query_group_label") or build_query_group_label(group_info, index)
        group_info["query_group_source"] = group_info.get("query_group_source") or source
        group_info["wave_type"] = normalized_wave_type
        group_info["wave_type_label"] = query_wave_type_label(normalized_wave_type)
        annotated.append(group_info)
    return annotated


def build_adaptive_alternate_base_queries(search_input, build_queries, start_index):
    alternate_skill_groups = search_input.get("alternate_skill_groups") or []
    role_pattern = search_input.get("role_pattern") or {}
    has_grouped_anchor_alternates = (
        role_pattern.get("query_strategy") == "grouped_anchors"
        and bool(role_pattern.get("grouped_anchor_alternates"))
    )
    if not alternate_skill_groups and not has_grouped_anchor_alternates:
        return []

    alternate_input = dict(search_input)
    if has_grouped_anchor_alternates:
        alternate_input["grouped_anchor_alternates_only"] = True
    else:
        alternate_input["skill_groups"] = alternate_skill_groups
        if alternate_input.get("query_wave_types"):
            alternate_input["query_wave_types"] = ["evidence_expansion"]
    alternate_input["alternate_skill_groups"] = []
    try:
        alternate_queries = build_queries(alternate_input)
    except RuntimeError:
        return []
    return annotate_query_groups(
        alternate_queries,
        start_index=start_index,
        id_prefix="alt-group",
        source="adaptive_alternate",
        wave_type="evidence_expansion",
    )


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


def dominant_query_wave_type(queries):
    counts = {}
    for query_info in queries or []:
        wave_type = normalize_query_wave_type(query_info.get("wave_type"))
        counts[wave_type] = counts.get(wave_type, 0) + 1
    if not counts:
        return DEFAULT_QUERY_WAVE_TYPE
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return "mixed"
    return ranked[0][0]


def build_adaptive_wave(*, wave_number, label, activation, queries):
    wave_type = dominant_query_wave_type(queries)
    return {
        "wave": wave_number,
        "label": label,
        "wave_type": wave_type,
        "wave_type_label": query_wave_type_label(wave_type),
        "activation": activation,
        "queries": queries,
    }


def explicit_query_wave_type_order(queries):
    if not any(query_info.get("wave_plan_enabled") for query_info in queries or []):
        return []

    seen = set()
    for query_info in queries or []:
        wave_type = normalize_query_wave_type(query_info.get("wave_type"))
        if wave_type:
            seen.add(wave_type)
    ordered = [wave_type for wave_type in QUERY_WAVE_TYPE_ORDER if wave_type in seen]
    ordered.extend(sorted(seen - set(ordered)))
    return ordered


def split_queries_by_explicit_wave_type(queries):
    wave_types = explicit_query_wave_type_order(queries)
    if not wave_types:
        return []

    waves = []
    for index, wave_type in enumerate(wave_types, start=1):
        wave_queries = [
            query_info
            for query_info in queries
            if normalize_query_wave_type(query_info.get("wave_type")) == wave_type
        ]
        if not wave_queries:
            continue
        waves.append(
            build_adaptive_wave(
                wave_number=index,
                label=query_wave_type_label(wave_type),
                activation="initial" if index == 1 else "target_not_reached",
                queries=wave_queries,
            )
        )
    return waves


def split_queries_into_adaptive_waves(base_queries, requested_count):
    queries = list(base_queries or [])
    explicit_waves = split_queries_by_explicit_wave_type(queries)
    if explicit_waves:
        return explicit_waves

    wave_count = adaptive_wave_count(requested_count, len(queries))
    if wave_count <= 1:
        return [
            build_adaptive_wave(
                wave_number=1,
                label=ADAPTIVE_WAVE_LABELS[1],
                activation="initial",
                queries=queries,
            )
        ]

    chunk_size = max(ceil(len(queries) / wave_count), 1)
    waves = []
    for index in range(wave_count):
        chunk = queries[index * chunk_size : (index + 1) * chunk_size]
        if not chunk:
            continue
        wave_number = index + 1
        waves.append(
            build_adaptive_wave(
                wave_number=wave_number,
                label=ADAPTIVE_WAVE_LABELS.get(wave_number, f"Wave {wave_number}"),
                activation="initial" if wave_number == 1 else "target_not_reached",
                queries=chunk,
            )
        )
    return waves or [
        build_adaptive_wave(
            wave_number=1,
            label=ADAPTIVE_WAVE_LABELS[1],
            activation="initial",
            queries=queries,
        )
    ]


def add_wave_context(query_info, wave):
    wave_info = dict(query_info)
    wave_type = normalize_query_wave_type(wave_info.get("wave_type") or wave.get("wave_type"))
    wave_info["adaptive_wave"] = wave["wave"]
    wave_info["adaptive_wave_label"] = wave["label"]
    wave_info["adaptive_wave_type"] = wave_type
    wave_info["adaptive_wave_type_label"] = query_wave_type_label(wave_type)
    wave_info["wave_type"] = wave_type
    wave_info["wave_type_label"] = query_wave_type_label(wave_type)
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
                "wave_type": wave.get("wave_type") or DEFAULT_QUERY_WAVE_TYPE,
                "wave_type_label": wave.get("wave_type_label") or query_wave_type_label(wave.get("wave_type")),
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


def finalize_adaptive_wave_summaries(wave_summaries, final_unique_count, requested_count, stop_reason=None):
    for summary in wave_summaries:
        if not summary["executed_calls"]:
            summary["status"] = "not_needed"
            continue
        if stop_reason == "call_cap_reached" and summary["executed_calls"] < summary["planned_calls"]:
            summary["status"] = "stopped_at_call_cap"
        elif final_unique_count >= requested_count and summary["executed_calls"] < summary["planned_calls"]:
            summary["status"] = "stopped_at_target"
        else:
            summary["status"] = "completed"
        if summary["unique_candidates_after_wave"] is None:
            summary["unique_candidates_after_wave"] = final_unique_count
        if summary["started_unique_candidates"] is None:
            summary["started_unique_candidates"] = 0
    return wave_summaries


def summarize_evidence_expansion(wave_summaries, stop_reason):
    expansion_waves = [
        summary
        for summary in wave_summaries or []
        if normalize_query_wave_type(summary.get("wave_type")) == "evidence_expansion"
    ]
    if not expansion_waves:
        return {
            "planned": False,
            "ran": False,
            "status": "not_planned",
            "label": "Not planned",
            "reason": "Evidence Expansion is not part of this search depth.",
        }

    planned_calls = sum(int(summary.get("planned_calls", 0) or 0) for summary in expansion_waves)
    executed_calls = sum(int(summary.get("executed_calls", 0) or 0) for summary in expansion_waves)
    if executed_calls:
        status = "ran_partial" if executed_calls < planned_calls else "ran"
        return {
            "planned": True,
            "ran": True,
            "status": status,
            "label": "Ran partially" if status == "ran_partial" else "Ran",
            "planned_calls": planned_calls,
            "executed_calls": executed_calls,
            "reason": "Evidence Expansion ran because earlier waves did not fill the target before the run stopped.",
        }

    status_by_stop_reason = {
        "target_reached": ("skipped_target_reached", "Skipped: target reached", "Earlier waves filled the requested candidate target."),
        "call_cap_reached": ("skipped_call_cap", "Skipped: call cap reached", "The Max call cap was reached before Evidence Expansion."),
        "plan_exhausted": ("skipped_plan_exhausted", "Skipped: plan exhausted", "The run ended before Evidence Expansion had executable calls."),
    }
    status, label, reason = status_by_stop_reason.get(
        stop_reason,
        ("not_needed", "Not needed", "The run did not need Evidence Expansion."),
    )
    return {
        "planned": True,
        "ran": False,
        "status": status,
        "label": label,
        "planned_calls": planned_calls,
        "executed_calls": executed_calls,
        "reason": reason,
    }


def tokenize_query_group(query_info):
    text = " ".join(
        clean_text(query_info.get(key, ""))
        for key in ("query_group_label", "skill_input", "title_input", "role_pattern_family")
    )
    tokens = []
    seen = set()
    for token in re.findall(r"[a-zA-Z0-9+#.]+", text.lower()):
        if len(token) < 2 or token in ADAPTIVE_SELECTION_STOPWORDS or token in seen:
            continue
        seen.add(token)
        tokens.append(token)
    return set(tokens)


def query_group_similarity(left, right):
    left_tokens = tokenize_query_group(left)
    right_tokens = tokenize_query_group(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def unique_rows_by_query_group(rows):
    return count_items_by_query_group(dedupe_rows(rows or []))


def provider_lift_from_rows(rows):
    return count_items_by_provider(dedupe_rows(rows or []), provider_key="search_provider")


def dynamic_query_group_signal(query_info, strong_groups, weak_groups, provider_lift):
    strong_similarity = max([query_group_similarity(query_info, group) for group in strong_groups] or [0.0])
    weak_similarity = max([query_group_similarity(query_info, group) for group in weak_groups] or [0.0])
    provider_score = provider_lift.get(query_info.get("provider") or "", 0)
    score = (strong_similarity * 10.0) - (weak_similarity * 4.0) + min(provider_score, 20) / 20.0
    return {
        "score": score,
        "strong_similarity": strong_similarity,
        "weak_similarity": weak_similarity,
        "provider_score": provider_score,
    }


def dynamic_query_group_score(query_info, strong_groups, weak_groups, provider_lift):
    return dynamic_query_group_signal(query_info, strong_groups, weak_groups, provider_lift)["score"]


def query_group_identity(query_info):
    return "|".join(
        clean_text(value).lower()
        for value in [
            query_info.get("skill_input") or query_info.get("query_group_label") or "",
            query_info.get("location_input", ""),
            query_info.get("source_site", ""),
        ]
    )


def representative_query_groups(query_plan):
    groups = {}
    for query_info in query_plan or []:
        if query_info.get("query_type") == "location_verification":
            continue
        group_id = query_info.get("query_group_id") or "unknown"
        if group_id not in groups:
            groups[group_id] = query_info
    return groups


def available_alternate_groups(query_plan, alternate_base_queries):
    existing_keys = {
        query_group_identity(query_info)
        for query_info in query_plan or []
        if query_group_identity(query_info)
    }
    alternates = []
    seen = set()
    for query_info in alternate_base_queries or []:
        key = query_group_identity(query_info)
        if not key or key in existing_keys or key in seen:
            continue
        seen.add(key)
        alternates.append(query_info)
    return alternates


def search_scope_matches(left, right):
    return (
        clean_text(left.get("location_input", "")).lower() == clean_text(right.get("location_input", "")).lower()
        and clean_text(left.get("source_site", "")).lower() == clean_text(right.get("source_site", "")).lower()
    )


def select_replacement_alternate(candidate_query_info, alternates, used_alternate_ids):
    for alternate in alternates:
        alternate_id = alternate.get("query_group_id")
        if alternate_id in used_alternate_ids:
            continue
        if search_scope_matches(candidate_query_info, alternate):
            used_alternate_ids.add(alternate_id)
            return alternate
    for alternate in alternates:
        alternate_id = alternate.get("query_group_id")
        if alternate_id not in used_alternate_ids:
            used_alternate_ids.add(alternate_id)
            return alternate
    return None


def build_replacement_groups(query_plan, start_index, strong_groups, weak_groups, provider_lift, alternate_base_queries):
    if not weak_groups:
        return []

    alternates = available_alternate_groups(query_plan, alternate_base_queries)
    if not alternates:
        return []

    candidates = []
    for group_id, query_info in representative_query_groups(query_plan[start_index:]).items():
        if query_info.get("query_group_source") == "adaptive_alternate":
            continue
        signal = dynamic_query_group_signal(query_info, strong_groups, weak_groups, provider_lift)
        if signal["strong_similarity"] >= ADAPTIVE_REPLACEMENT_STRONG_SIMILARITY_CEILING:
            continue
        candidates.append(
            {
                "query_group_id": group_id,
                "query_group_label": query_info.get("query_group_label") or group_id,
                "adaptive_wave": int(query_info.get("adaptive_wave", 1) or 1),
                "wave_type": query_info.get("wave_type") or DEFAULT_QUERY_WAVE_TYPE,
                "wave_type_label": query_info.get("wave_type_label") or query_wave_type_label(query_info.get("wave_type")),
                "query_group_index": int(query_info.get("query_group_index", 0) or 0),
                "score": signal["score"],
                "strong_similarity": signal["strong_similarity"],
                "weak_similarity": signal["weak_similarity"],
                "query_info": query_info,
            }
        )

    candidates.sort(key=lambda item: (item["score"], -item["adaptive_wave"], item["query_group_index"]))
    replacement_count = min(len(candidates), len(alternates), len(weak_groups), ADAPTIVE_REPLACEMENT_MAX_GROUPS)
    replacements = []
    used_alternate_ids = set()
    for candidate in candidates:
        if len(replacements) >= replacement_count:
            break
        alternate = select_replacement_alternate(candidate["query_info"], alternates, used_alternate_ids)
        if not alternate:
            continue
        replacements.append(
            {
                "replaced_query_group_id": candidate["query_group_id"],
                "replaced_query_group_label": candidate["query_group_label"],
                "replacement_query_group_id": alternate.get("query_group_id") or "",
                "replacement_query_group_label": alternate.get("query_group_label") or alternate.get("skill_input", ""),
                "adaptive_wave": candidate["adaptive_wave"],
                "replaced_wave_type": candidate.get("wave_type", ""),
                "replaced_wave_type_label": candidate.get("wave_type_label", ""),
                "replacement_wave_type": alternate.get("wave_type", ""),
                "replacement_wave_type_label": alternate.get("wave_type_label", ""),
                "score": round(candidate["score"], 4),
                "strong_similarity": round(candidate["strong_similarity"], 4),
                "weak_similarity": round(candidate["weak_similarity"], 4),
                "reason": "Completed waves found weak groups; this later group ranked low, so an unused semantic-family alternate is tried instead.",
            }
        )
    return replacements


def build_dynamic_wave_selection(query_plan, start_index, diagnostics, all_rows, alternate_base_queries=None, current_wave=2):
    remaining_plan = query_plan[start_index:]
    if not remaining_plan:
        return None

    by_query_group = diagnostics.get("by_query_group", {}) if isinstance(diagnostics, dict) else {}
    final_by_group = unique_rows_by_query_group(all_rows)
    provider_lift = provider_lift_from_rows(all_rows)
    seen_groups = {}
    for query_info in query_plan[:start_index]:
        if query_info.get("query_type") == "location_verification":
            continue
        group_id = query_info.get("query_group_id") or "unknown"
        seen_groups[group_id] = query_info

    strong_groups = []
    weak_groups = []
    group_summaries = []
    for group_id, query_info in seen_groups.items():
        stats = by_query_group.get(group_id, {})
        has_group_stats = group_id in by_query_group
        final_count = int(final_by_group.get(group_id, 0) or 0)
        accepted_count = int(stats.get("accepted_rows", 0) or 0)
        summary = {
            "query_group_id": group_id,
            "query_group_label": query_info.get("query_group_label") or group_id,
            "accepted_rows": accepted_count,
            "final_candidates": final_count,
        }
        group_summaries.append(summary)
        if final_count > 0:
            strong_groups.append(query_info)
        elif has_group_stats and accepted_count == 0:
            weak_groups.append(query_info)

    if not strong_groups and not weak_groups:
        return None

    replacement_groups = build_replacement_groups(
        query_plan,
        start_index,
        strong_groups,
        weak_groups,
        provider_lift,
        alternate_base_queries or [],
    )
    ranked_remaining = []
    for query_info in remaining_plan:
        score = dynamic_query_group_score(query_info, strong_groups, weak_groups, provider_lift)
        ranked_remaining.append(
            {
                "query_group_id": query_info.get("query_group_id") or "unknown",
                "query_group_label": query_info.get("query_group_label") or query_info.get("skill_input", ""),
                "adaptive_wave": int(query_info.get("adaptive_wave", 1) or 1),
                "wave_type": query_info.get("wave_type") or DEFAULT_QUERY_WAVE_TYPE,
                "wave_type_label": query_info.get("wave_type_label") or query_wave_type_label(query_info.get("wave_type")),
                "provider": query_info.get("provider", ""),
                "page": int(query_info.get("page", 1) or 1),
                "score": round(score, 4),
            }
        )

    ranked_remaining.sort(key=lambda item: (item["adaptive_wave"], -item["score"], item["page"], item["provider"]))
    return {
        "applied_after_wave": max(int(current_wave or 2) - 1, 1),
        "applied_before_wave": int(current_wave or 2),
        "action": "reordered_and_replaced_remaining_query_plan" if replacement_groups else "reordered_remaining_query_plan",
        "replacement_mode": "replace_only",
        "replacement_group_count": len(replacement_groups),
        "alternate_group_count": len(available_alternate_groups(query_plan, alternate_base_queries or [])),
        "strong_group_count": len(strong_groups),
        "weak_group_count": len(weak_groups),
        "provider_lift": provider_lift,
        "completed_groups": sorted(group_summaries, key=lambda item: item["final_candidates"], reverse=True),
        "replacement_groups": replacement_groups,
        "remaining_groups_ranked": ranked_remaining[:20],
    }


def build_replaced_query_info(query_info, alternate_base_query, requested_count):
    provider = query_info.get("provider", "")
    page_size = int(query_info.get("page_size", 20) or 20)
    page_index = max(int(query_info.get("page", 1) or 1) - 1, 0)
    provider_alternates = expand_queries_for_provider(provider, [alternate_base_query], requested_count)
    replacement = dict(provider_alternates[0] if provider_alternates else alternate_base_query)
    replacement = add_pagination_context(replacement, provider, page_index, page_size)
    wave_type = normalize_query_wave_type(replacement.get("wave_type") or query_info.get("wave_type"))
    replacement["wave_type"] = wave_type
    replacement["wave_type_label"] = query_wave_type_label(wave_type)
    for key in ("adaptive_wave", "adaptive_wave_label", "adaptive_wave_activation"):
        replacement[key] = query_info.get(key)
    replacement["adaptive_wave_type"] = wave_type
    replacement["adaptive_wave_type_label"] = query_wave_type_label(wave_type)
    replacement["adaptive_replacement"] = True
    replacement["replaced_query_group_id"] = query_info.get("query_group_id", "")
    replacement["replaced_query_group_label"] = query_info.get("query_group_label", "")
    return replacement


def apply_dynamic_replacements(remaining_plan, selection, alternate_base_queries, requested_count):
    replacement_items = selection.get("replacement_groups") or []
    if not replacement_items:
        return remaining_plan
    alternate_by_id = {
        query_info.get("query_group_id"): query_info
        for query_info in alternate_base_queries or []
        if query_info.get("query_group_id")
    }
    replacement_map = {
        item.get("replaced_query_group_id"): alternate_by_id.get(item.get("replacement_query_group_id"))
        for item in replacement_items
        if item.get("replaced_query_group_id") and alternate_by_id.get(item.get("replacement_query_group_id"))
    }
    if not replacement_map:
        return remaining_plan
    replaced = []
    for query_info in remaining_plan:
        alternate = replacement_map.get(query_info.get("query_group_id"))
        if alternate:
            replaced.append(build_replaced_query_info(query_info, alternate, requested_count))
        else:
            replaced.append(query_info)
    return replaced


def apply_dynamic_wave_selection(query_plan, start_index, selection, diagnostics, all_rows, alternate_base_queries=None, requested_count=20):
    if not selection:
        return query_plan

    by_query_group = diagnostics.get("by_query_group", {}) if isinstance(diagnostics, dict) else {}
    final_by_group = unique_rows_by_query_group(all_rows)
    provider_lift = provider_lift_from_rows(all_rows)
    seen_groups = {}
    for query_info in query_plan[:start_index]:
        if query_info.get("query_type") == "location_verification":
            continue
        group_id = query_info.get("query_group_id") or "unknown"
        seen_groups[group_id] = query_info
    strong_groups = [query_info for group_id, query_info in seen_groups.items() if final_by_group.get(group_id, 0) > 0]
    weak_groups = [
        query_info
        for group_id, query_info in seen_groups.items()
        if group_id in by_query_group
        and final_by_group.get(group_id, 0) == 0
        and int((by_query_group.get(group_id, {}) or {}).get("accepted_rows", 0) or 0) == 0
    ]

    untouched = query_plan[:start_index]
    remaining = list(query_plan[start_index:])
    remaining.sort(
        key=lambda query_info: (
            int(query_info.get("adaptive_wave", 1) or 1),
            -dynamic_query_group_score(query_info, strong_groups, weak_groups, provider_lift),
            int(query_info.get("page", 1) or 1),
            query_info.get("provider", ""),
            int(query_info.get("query_group_index", 0) or 0),
        )
    )
    remaining = apply_dynamic_replacements(remaining, selection, alternate_base_queries or [], requested_count)
    return untouched + remaining


def summarize_dynamic_wave_selections(selection_records):
    records = [record for record in selection_records or [] if record]
    if not records:
        return {
            "action": "not_applied",
            "reason": "No later wave reached or no completed wave signal was available.",
        }
    if len(records) == 1:
        return records[0]

    replacement_groups = []
    for record in records:
        replacement_groups.extend(record.get("replacement_groups") or [])
    last_record = records[-1]
    action = (
        "reordered_and_replaced_remaining_query_plan"
        if replacement_groups
        else "reordered_remaining_query_plan"
    )
    return {
        **last_record,
        "action": action,
        "selection_count": len(records),
        "selection_events": [
            {
                "applied_after_wave": record.get("applied_after_wave"),
                "applied_before_wave": record.get("applied_before_wave"),
                "action": record.get("action"),
                "replacement_group_count": record.get("replacement_group_count", 0),
                "strong_group_count": record.get("strong_group_count", 0),
                "weak_group_count": record.get("weak_group_count", 0),
            }
            for record in records
        ],
        "replacement_group_count": len(replacement_groups),
        "replacement_groups": replacement_groups,
    }


def attach_query_context(rows, query_info):
    for row in rows:
        row["query_role"] = query_info["title_input"]
        row["query_technology"] = query_info["skill_input"]
        row["role"] = query_info["title_input"]
        row["technology"] = query_info["skill_input"]
        row["target_location"] = query_info["location_input"]
        row["location"] = row.get("location", "")
        row["source_site"] = query_info["source_site"]
        row["search_page"] = query_info.get("page", 1)
        row["query_group_id"] = query_info.get("query_group_id", "")
        row["query_group_index"] = query_info.get("query_group_index", 0)
        row["query_group_label"] = query_info.get("query_group_label", "")
        row["adaptive_wave"] = query_info.get("adaptive_wave", 1)
        row["adaptive_wave_label"] = query_info.get("adaptive_wave_label", "")
        row["adaptive_wave_type"] = query_info.get("adaptive_wave_type", "")
        row["adaptive_wave_type_label"] = query_info.get("adaptive_wave_type_label", "")
        row["query_wave_type"] = query_info.get("wave_type", "")
        row["query_wave_type_label"] = query_info.get("wave_type_label", "")
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
        "by_query_group": {},
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


def query_group_diagnostics(diagnostics, query_info):
    groups = diagnostics.setdefault("by_query_group", {})
    group_id = query_info.get("query_group_id") or "unknown"
    if group_id not in groups:
        groups[group_id] = {
            "query_group_id": group_id,
            "query_group_index": int(query_info.get("query_group_index") or 0),
            "query_group_label": query_info.get("query_group_label") or group_id,
            "adaptive_wave": int(query_info.get("adaptive_wave", 1) or 1),
            "adaptive_wave_label": query_info.get("adaptive_wave_label", ""),
            "wave_type": query_info.get("wave_type") or DEFAULT_QUERY_WAVE_TYPE,
            "wave_type_label": query_info.get("wave_type_label") or query_wave_type_label(query_info.get("wave_type")),
            "title_input": query_info.get("title_input", ""),
            "skill_input": query_info.get("skill_input", ""),
            "location_input": query_info.get("location_input", ""),
            "source_site": query_info.get("source_site", ""),
            "sample_query": query_info.get("query", ""),
            "raw_rows": 0,
            "quality_rows": 0,
            "accepted_rows": 0,
            "strict_location_rejected": 0,
        }
    return groups[group_id]


def add_query_group_diagnostic(diagnostics, query_info, key, count=1):
    group_stats = query_group_diagnostics(diagnostics, query_info)
    group_stats[key] = group_stats.get(key, 0) + count


def count_items_by_provider(items, *, provider_key="provider", include_verification=True):
    counts = {}
    for item in items or []:
        if not include_verification and item.get("query_type") == "location_verification":
            continue
        provider = item.get(provider_key) or "unknown"
        counts[provider] = counts.get(provider, 0) + 1
    return counts


def count_items_by_query_group(items, *, include_verification=True):
    counts = {}
    for item in items or []:
        if not include_verification and item.get("query_type") == "location_verification":
            continue
        group_id = item.get("query_group_id") or "unknown"
        counts[group_id] = counts.get(group_id, 0) + 1
    return counts


def provider_counts_by_query_group(items, *, provider_key="provider", include_verification=True):
    counts = {}
    for item in items or []:
        if not include_verification and item.get("query_type") == "location_verification":
            continue
        group_id = item.get("query_group_id") or "unknown"
        provider = item.get(provider_key) or "unknown"
        counts.setdefault(group_id, {})
        counts[group_id][provider] = counts[group_id].get(provider, 0) + 1
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


def ordered_query_group_keys(query_plan, by_query_group, final_candidates):
    ordered = []
    seen = set()
    for query_info in query_plan or []:
        if query_info.get("query_type") == "location_verification":
            continue
        group_id = query_info.get("query_group_id") or "unknown"
        if group_id not in seen:
            seen.add(group_id)
            ordered.append(group_id)
    for group_map in (by_query_group or {}, final_candidates or {}):
        for group_id in group_map:
            if group_id not in seen:
                seen.add(group_id)
                ordered.append(group_id)
    return ordered


def build_query_group_contribution_report(
    *,
    query_plan,
    executed_queries,
    diagnostics,
    final_rows,
):
    by_query_group = diagnostics.get("by_query_group", {}) if isinstance(diagnostics, dict) else {}
    planned_calls = count_items_by_query_group(query_plan, include_verification=False)
    executed_calls = count_items_by_query_group(executed_queries, include_verification=False)
    final_candidates = count_items_by_query_group(final_rows)
    executed_providers = provider_counts_by_query_group(executed_queries, include_verification=False)
    final_providers = provider_counts_by_query_group(final_rows, provider_key="search_provider")
    group_keys = ordered_query_group_keys(query_plan, by_query_group, final_candidates)

    groups = []
    hidden_unexecuted_groups = 0
    for group_id in group_keys:
        stats = by_query_group.get(group_id, {})
        accepted_rows = int(stats.get("accepted_rows", 0) or 0)
        final_count = int(final_candidates.get(group_id, 0) or 0)
        executed_count = int(executed_calls.get(group_id, 0) or 0)
        raw_rows = int(stats.get("raw_rows", 0) or 0)
        quality_rows = int(stats.get("quality_rows", 0) or 0)
        strict_location_rejected = int(stats.get("strict_location_rejected", 0) or 0)
        if not executed_count and not raw_rows and not quality_rows and not accepted_rows and not final_count:
            hidden_unexecuted_groups += 1
            continue
        provider_lift = final_providers.get(group_id, {})
        top_provider = ""
        if provider_lift:
            top_provider = max(provider_lift.items(), key=lambda item: item[1])[0]
        groups.append(
            {
                "query_group_id": group_id,
                "query_group_index": int(stats.get("query_group_index", 0) or 0),
                "query_group_label": stats.get("query_group_label") or group_id,
                "adaptive_wave": int(stats.get("adaptive_wave", 1) or 1),
                "adaptive_wave_label": stats.get("adaptive_wave_label", ""),
                "wave_type": stats.get("wave_type") or DEFAULT_QUERY_WAVE_TYPE,
                "wave_type_label": stats.get("wave_type_label") or query_wave_type_label(stats.get("wave_type")),
                "title_input": stats.get("title_input", ""),
                "skill_input": stats.get("skill_input", ""),
                "location_input": stats.get("location_input", ""),
                "source_site": stats.get("source_site", ""),
                "sample_query": stats.get("sample_query", ""),
                "planned_calls": int(planned_calls.get(group_id, 0) or 0),
                "executed_calls": executed_count,
                "raw_rows": raw_rows,
                "quality_rows": quality_rows,
                "strict_location_rejected": strict_location_rejected,
                "accepted_rows": accepted_rows,
                "final_candidates": final_count,
                "unique_lift": final_count,
                "deduped_or_capped_out": max(accepted_rows - final_count, 0),
                "executed_provider_counts": executed_providers.get(group_id, {}),
                "final_provider_counts": provider_lift,
                "top_provider": top_provider,
            }
        )

    groups.sort(key=lambda item: (item["adaptive_wave"], item["query_group_index"], item["query_group_id"]))
    ranked_groups = sorted(groups, key=lambda item: item["final_candidates"], reverse=True)
    totals = {
        "planned_calls": sum(item["planned_calls"] for item in groups),
        "executed_calls": sum(item["executed_calls"] for item in groups),
        "raw_rows": sum(item["raw_rows"] for item in groups),
        "quality_rows": sum(item["quality_rows"] for item in groups),
        "strict_location_rejected": sum(item["strict_location_rejected"] for item in groups),
        "accepted_rows": sum(item["accepted_rows"] for item in groups),
        "final_candidates": len(final_rows or []),
        "deduped_or_capped_out": sum(item["deduped_or_capped_out"] for item in groups),
        "hidden_unexecuted_groups": hidden_unexecuted_groups,
    }

    return {
        "groups": groups,
        "ranked_groups": ranked_groups[:10],
        "totals": totals,
        "notes": [
            "Query group lift is attributed to the group whose row survived dedupe and result-limit capping.",
            "Use Wave 1 group lift to decide which later semantic groups deserve more calls.",
            "Unexecuted groups with zero rows are hidden from the report to keep benchmarks readable.",
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

    base_queries = annotate_query_groups(build_queries(search_input))
    alternate_base_queries = build_adaptive_alternate_base_queries(
        search_input,
        build_queries,
        start_index=len(base_queries) + 1,
    )
    query_waves = split_queries_into_adaptive_waves(base_queries, requested_count)
    started_at = time.time()
    per_request_limit = min(requested_count, 20)
    query_plan = build_query_plan(providers, query_waves, requested_count, per_request_limit, search_input)
    planned_query_count = len(query_plan)
    planned_call_cap = resolve_search_call_cap(search_input, config, query_plan, requested_count)
    budgeted_query_count = min(planned_query_count, planned_call_cap) if planned_call_cap else planned_query_count
    adaptive_wave_summaries = build_adaptive_wave_summaries(query_waves, query_plan)
    adaptive_wave_map = {item["wave"]: item for item in adaptive_wave_summaries}
    executed_queries = []
    all_rows = []
    stop_reason = "plan_exhausted"
    location_policy = search_input.get("location_policy") or "strict"
    target_locations = search_input.get("display_locations") or search_input.get("locations", [])
    provider_errors = []
    failed_providers = set()
    verification_limit = max(int(config.get("location_verification_limit", 20) or 0), 0)
    diagnostics = build_diagnostics(verification_limit)
    location_metadata = country_metadata_from_target_locations(target_locations)
    dynamic_wave_selection_records = []
    dynamic_wave_selection_applied_waves = set()
    verification_state = {
        "attempts": 0,
        "confirmed": 0,
        "limit": verification_limit,
        "attempted_keys": set(),
        "providers": resolve_location_verification_providers(config),
        "target_providers": resolve_location_verification_target_providers(config),
    }

    plan_index = 0
    while plan_index < len(query_plan):
        if len(dedupe_rows(all_rows)) >= requested_count:
            stop_reason = "target_reached"
            break
        if planned_call_cap and executed_search_call_count(executed_queries) >= planned_call_cap:
            stop_reason = "call_cap_reached"
            break
        query_info = query_plan[plan_index]
        current_wave = int(query_info.get("adaptive_wave", 1) or 1)
        if (
            requested_count >= ADAPTIVE_WAVE_MIN_REQUESTED_COUNT
            and current_wave > 1
            and current_wave not in dynamic_wave_selection_applied_waves
        ):
            dynamic_wave_selection = build_dynamic_wave_selection(
                query_plan,
                plan_index,
                diagnostics,
                all_rows,
                alternate_base_queries=alternate_base_queries,
                current_wave=current_wave,
            )
            if dynamic_wave_selection:
                query_plan = apply_dynamic_wave_selection(
                    query_plan,
                    plan_index,
                    dynamic_wave_selection,
                    diagnostics,
                    all_rows,
                    alternate_base_queries=alternate_base_queries,
                    requested_count=requested_count,
                )
                query_info = query_plan[plan_index]
                dynamic_wave_selection_records.append(dynamic_wave_selection)
            dynamic_wave_selection_applied_waves.add(current_wave)
        if progress_callback:
            progress_total = budgeted_query_count or len(query_plan)
            progress_current = min(plan_index + 1, progress_total)
            progress_callback(progress_current, progress_total, query_info, started_at, len(all_rows))

        query = query_info["query"]
        provider = query_info["provider"]
        wave_number = int(query_info.get("adaptive_wave", 1) or 1)
        wave_summary = adaptive_wave_map.get(wave_number)
        if wave_summary and wave_summary["started_unique_candidates"] is None:
            wave_summary["started_unique_candidates"] = len(dedupe_rows(all_rows))
        if provider in failed_providers:
            plan_index += 1
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
            plan_index += 1
            continue

        for row in rows:
            row["search_provider"] = provider
        rows = attach_query_context(rows, query_info)
        rows = normalize_devpost_rows(rows)
        rows = [annotate_location_match(row, target_locations, location_metadata) for row in rows]
        add_diagnostic(diagnostics, provider, "raw_rows", len(rows))
        add_query_group_diagnostic(diagnostics, query_info, "raw_rows", len(rows))
        if wave_summary:
            wave_summary["raw_rows"] += len(rows)
        quality_rows = [row for row in rows if row_filter(row)]
        add_diagnostic(diagnostics, provider, "quality_rows", len(quality_rows))
        add_query_group_diagnostic(diagnostics, query_info, "quality_rows", len(quality_rows))
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
                add_query_group_diagnostic(diagnostics, query_info, "strict_location_rejected")
        if location_policy == "strict":
            quality_rows = [row for row in quality_rows if row_matches_strict_locations(row, target_locations)]
        add_diagnostic(diagnostics, provider, "accepted_rows", len(quality_rows))
        add_query_group_diagnostic(diagnostics, query_info, "accepted_rows", len(quality_rows))
        all_rows.extend(quality_rows)
        if wave_summary:
            wave_summary["accepted_rows"] += len(quality_rows)
            wave_summary["unique_candidates_after_wave"] = len(dedupe_rows(all_rows))
        plan_index += 1

    rows = dedupe_rows(all_rows)[:requested_count]
    executed_primary_query_count = executed_search_call_count(executed_queries)
    verification_query_count = max(len(executed_queries) - executed_primary_query_count, 0)
    if len(rows) >= requested_count:
        stop_reason = "target_reached"
    elif planned_call_cap and executed_primary_query_count >= planned_call_cap and planned_call_cap < planned_query_count:
        stop_reason = "call_cap_reached"
    else:
        stop_reason = "plan_exhausted"
    adaptive_wave_summaries = finalize_adaptive_wave_summaries(
        adaptive_wave_summaries,
        len(rows),
        requested_count,
        stop_reason=stop_reason,
    )
    search_strategy = summarize_search_strategy(search_input, executed_queries)
    search_depth = str(search_input.get("search_depth") or "extended").strip().lower()
    search_strategy["search_depth"] = search_depth
    search_strategy["search_depth_label"] = SEARCH_DEPTH_LABELS.get(search_depth, "Extended")
    search_strategy["base_query_count"] = len(base_queries)
    search_strategy["adaptive_alternate_group_count"] = len(alternate_base_queries)
    search_strategy["provider_passes"] = int(planned_query_count / max(len(base_queries), 1))
    search_strategy["planned_query_count"] = planned_query_count
    search_strategy["planned_call_cap"] = planned_call_cap
    search_strategy["budgeted_query_count"] = budgeted_query_count
    search_strategy["call_cap_applied"] = bool(planned_call_cap and planned_call_cap < planned_query_count)
    search_strategy["executed_query_count"] = len(executed_queries)
    search_strategy["executed_search_query_count"] = executed_primary_query_count
    search_strategy["verification_query_count"] = verification_query_count
    search_strategy["stop_reason"] = stop_reason
    search_strategy["stop_reason_label"] = search_stop_reason_label(stop_reason)
    search_strategy["provider_errors"] = provider_errors
    search_strategy["adaptive_waves"] = {
        "enabled": len(query_waves) > 1,
        "planned_wave_count": len(query_waves),
        "completed_wave_count": len([item for item in adaptive_wave_summaries if item["executed_calls"]]),
        "stop_reason": stop_reason,
        "stop_reason_label": search_stop_reason_label(stop_reason),
        "planned_call_cap": planned_call_cap,
        "budgeted_query_count": budgeted_query_count,
        "call_cap_applied": bool(planned_call_cap and planned_call_cap < planned_query_count),
        "evidence_expansion": summarize_evidence_expansion(adaptive_wave_summaries, stop_reason),
        "dynamic_selection": summarize_dynamic_wave_selections(dynamic_wave_selection_records),
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
    search_strategy["query_group_contribution_report"] = build_query_group_contribution_report(
        query_plan=query_plan,
        executed_queries=executed_queries,
        diagnostics=diagnostics,
        final_rows=rows,
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
