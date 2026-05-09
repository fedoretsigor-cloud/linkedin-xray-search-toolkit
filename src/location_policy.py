import re
from urllib.parse import urlparse

from src.text_utils import clean_text


REMOTE_TERMS = {"remote", "remotely", "remote work", "work from home", "wfh"}
PROFILE_SEGMENT_SEPARATOR = re.compile(r"\s+(?:-|\u2013|\u2014)\s+")
SOCIAL_COUNT_MARKERS = ("connection", "contact", "follower", "kontakt")


def normalize_locations(locations):
    normalized = []
    for value in locations or []:
        text = clean_text(value)
        if not text:
            continue
        parts = re.split(r"[,;/\n]+|\bor\b", text, flags=re.IGNORECASE)
        for part in parts:
            item = clean_text(part)
            if item:
                normalized.append(item)
    return dedupe_values(normalized)


def effective_locations(locations):
    normalized = normalize_locations(locations)
    has_concrete_location = any(
        strip_remote_marker(normalize_for_match(location)) for location in normalized
    )
    if not has_concrete_location:
        return normalized
    return [
        location
        for location in normalized
        if strip_remote_marker(normalize_for_match(location))
    ]


def build_location_terms(locations):
    terms = []
    requires_remote = False
    for location in locations or []:
        raw = clean_text(location)
        if not raw:
            continue
        concrete_parts = []
        remote_seen = False
        for part in [clean_text(item) for item in re.split(r"[,;/\n]+", raw) if clean_text(item)]:
            normalized = normalize_for_match(part)
            if has_remote_marker(normalized):
                remote_seen = True
                remainder = strip_remote_marker(normalized)
                if remainder:
                    concrete_parts.append(remainder)
                continue
            concrete_parts.append(part)

        if concrete_parts:
            # If the user writes "City, Country", the city is the strict
            # constraint. If the user writes only a country, match that
            # country literally instead of broadening to city aliases.
            add_location_terms(terms, concrete_parts[0])
        elif remote_seen:
            requires_remote = True
    return {
        "terms": dedupe_values(terms),
        "requires_remote": requires_remote,
    }


def build_location_query_values(locations):
    values = []
    for location in locations or []:
        normalized = normalize_for_match(extract_primary_query_location(location))
        if not normalized:
            continue
        if has_remote_marker(normalized):
            remainder = strip_remote_marker(normalized)
            values.append(remainder or "remote")
        else:
            values.append(normalized)
    return dedupe_values(values)


def extract_primary_query_location(location):
    raw = clean_text(location)
    if not raw:
        return ""
    parts = [clean_text(part) for part in re.split(r"[,;/\n]+", raw) if clean_text(part)]
    if not parts:
        return ""

    primary = parts[0]
    normalized_primary = normalize_for_match(primary)
    if has_remote_marker(normalized_primary):
        remainder = strip_remote_marker(normalized_primary)
        return remainder or "remote"

    # General rule:
    # if user specifies "City, State/Country", search query uses only the first
    # concrete place token, while strict filtering still validates the full location.
    return primary


def row_location_evidence(row):
    return clean_text(
        " ".join(
            [
                row.get("result_title", ""),
                row.get("short_description", ""),
                row.get("profile_name", ""),
            ]
        )
    )


def explicit_profile_location(row):
    location = clean_text(row.get("location", ""))
    if normalize_for_match(location) in {"", "-", "unknown", "n/a", "none"}:
        return ""
    return location


def linkedin_country_subdomain_location(row, location_metadata=None):
    metadata = location_metadata or {}
    if metadata.get("location_type") != "Country":
        return ""
    country_iso = clean_text(metadata.get("country_iso_code", "")).lower()
    location_name = clean_text(metadata.get("location_name", ""))
    if not country_iso or not location_name:
        return ""

    host = urlparse(row.get("profile_url", "") or "").netloc.lower()
    labels = [label for label in host.split(".") if label]
    if len(labels) >= 3 and labels[-2:] == ["linkedin", "com"] and labels[0] == country_iso:
        return location_name
    return ""


def has_social_count_marker(value):
    normalized = normalize_for_match(value)
    return any(char.isdigit() for char in normalized) and any(
        marker in normalized for marker in SOCIAL_COUNT_MARKERS
    )


def field_value(segment):
    text = clean_text(segment)
    if ":" not in text:
        return text
    label, value = text.rsplit(":", 1)
    if len(label) > 45:
        return text
    return clean_text(value)


def is_structured_location_candidate(value):
    text = clean_text(value)
    normalized = normalize_for_match(text)
    if not text or len(text) > 80:
        return False
    if any(char.isdigit() for char in text):
        return False
    if any(separator in text for separator in ("|", "@", "://")):
        return False
    if normalized in {"about", "experience", "education", "connections", "followers"}:
        return False
    return True


def structured_location_fragments(text):
    fragments = []
    for line in clean_text(text).splitlines():
        line = clean_text(line)
        if not line:
            continue
        fragments.append(line)
        fragments.extend(
            clean_text(segment)
            for segment in PROFILE_SEGMENT_SEPARATOR.split(line)
            if clean_text(segment) and clean_text(segment) != line
        )
    return fragments


def infer_current_location_from_target_context(row, policy_terms):
    if not policy_terms:
        return ""
    fragments = structured_location_fragments(row_location_evidence(row))
    for index, fragment in enumerate(fragments[:-1]):
        if not has_social_count_marker(fragments[index + 1]):
            continue
        candidate = field_value(fragment)
        candidate_normalized = normalize_for_match(candidate)
        if not is_structured_location_candidate(candidate):
            continue
        if any(term_matches(term, candidate_normalized) for term in policy_terms):
            return candidate
    return ""


def annotate_location_match(row, target_locations, location_metadata=None):
    policy = build_location_terms(target_locations)
    evidence = row_location_evidence(row)
    evidence_normalized = normalize_for_match(evidence)
    evidence_matched_terms = [
        term for term in policy["terms"] if term_matches(term, evidence_normalized)
    ]
    explicit_location = explicit_profile_location(row)
    inferred_location = infer_current_location_from_target_context(row, policy["terms"])
    subdomain_location = linkedin_country_subdomain_location(row, location_metadata)
    subdomain_normalized = normalize_for_match(subdomain_location)
    subdomain_matched_terms = [
        term for term in policy["terms"] if term_matches(term, subdomain_normalized)
    ]
    current_location = explicit_location or inferred_location or subdomain_location
    current_location_source = "profile_header_or_snippet"
    if subdomain_location and subdomain_matched_terms:
        current_normalized = normalize_for_match(current_location)
        current_matches_target = any(term_matches(term, current_normalized) for term in policy["terms"])
        if not current_location or not current_matches_target:
            current_location = subdomain_location
            current_location_source = "linkedin_country_subdomain"
        elif not explicit_location and not inferred_location:
            current_location_source = "linkedin_country_subdomain"
    if current_location and (
        not clean_text(row.get("location", ""))
        or current_location_source == "linkedin_country_subdomain"
    ):
        row["location"] = current_location
    current_location_normalized = normalize_for_match(current_location)
    current_location_matched_terms = [
        term for term in policy["terms"] if term_matches(term, current_location_normalized)
    ]
    remote_matched = not policy["requires_remote"] or any(
        term_matches(term, evidence_normalized) for term in REMOTE_TERMS
    )
    has_location_constraint = bool(policy["terms"] or policy["requires_remote"])
    current_location_conflict = bool(
        current_location and policy["terms"] and not current_location_matched_terms
    )
    current_location_required = bool(policy["terms"])
    current_location_missing = current_location_required and not current_location
    matched_terms = current_location_matched_terms
    matched = (
        has_location_constraint
        and remote_matched
        and not current_location_missing
        and not current_location_conflict
        and (bool(current_location_matched_terms) or not policy["terms"])
    )

    row["target_locations"] = target_locations or []
    row["location_match"] = {
        "required": has_location_constraint,
        "matched": matched,
        "matched_terms": matched_terms,
        "evidence_matched_terms": evidence_matched_terms,
        "current_location": current_location,
        "current_location_source": current_location_source,
        "subdomain_location": subdomain_location,
        "current_location_required": current_location_required,
        "current_location_missing": current_location_missing,
        "current_location_matched_terms": current_location_matched_terms,
        "current_location_conflict": current_location_conflict,
        "free_text_location_only": bool(evidence_matched_terms and current_location_missing),
        "requires_remote": policy["requires_remote"],
        "remote_matched": remote_matched,
    }
    return row


def row_matches_strict_locations(row, target_locations):
    if not target_locations:
        return True
    match = row.get("location_match") or annotate_location_match(row, target_locations).get("location_match", {})
    if not match.get("required"):
        return True
    return bool(match.get("matched"))


def add_location_terms(terms, value):
    normalized = normalize_for_match(value)
    if normalized:
        terms.append(normalized)


def term_matches(term, text):
    normalized_term = normalize_for_match(term)
    if not normalized_term:
        return False
    pattern = rf"(?<![a-z0-9]){re.escape(normalized_term)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def normalize_for_match(value):
    return clean_text(value).lower().replace("-", " ").replace("/", " ")


def has_remote_marker(value):
    normalized = normalize_for_match(value)
    return any(term_matches(term, normalized) for term in REMOTE_TERMS)


def strip_remote_marker(value):
    stripped = normalize_for_match(value)
    for term in sorted(REMOTE_TERMS, key=len, reverse=True):
        stripped = re.sub(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", " ", stripped)
    return clean_text(stripped)


def dedupe_values(values):
    deduped = []
    seen = set()
    for value in values:
        text = clean_text(value)
        key = text.lower()
        if text and key not in seen:
            seen.add(key)
            deduped.append(text)
    return deduped
