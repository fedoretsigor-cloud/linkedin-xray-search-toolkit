import re

from src.text_utils import clean_text


REMOTE_TERMS = {"remote", "remotely", "remote work", "work from home", "wfh"}

LOCATION_ALIASES = {
    "ukraine": {"ukraine", "україна", "kyiv", "kiev", "lviv", "odesa", "odessa", "kharkiv", "dnipro"},
    "poland": {"poland", "warsaw", "krakow", "kraków", "wroclaw", "wrocław", "gdansk", "gdańsk"},
    "united states": {"united states", "usa", "u.s.", "us", "new york", "california", "texas"},
    "usa": {"united states", "usa", "u.s.", "us", "new york", "california", "texas"},
    "germany": {"germany", "berlin", "munich", "münchen", "hamburg"},
    "france": {"france", "paris", "lyon", "marseille", "toulouse", "nice"},
    "romania": {"romania", "bucharest", "cluj"},
    "bulgaria": {"bulgaria", "sofia"},
}


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


def build_location_terms(locations):
    terms = []
    requires_remote = False
    for location in normalize_locations(locations):
        normalized = normalize_for_match(location)
        if not normalized:
            continue
        words = [word for word in normalized.split() if word]
        if any(word in REMOTE_TERMS for word in words) or normalized in REMOTE_TERMS:
            # "Remote + Country/City" means the concrete location is strict and
            # "remote" is only work format. This rule applies to every country/city.
            remainder = " ".join(word for word in words if word not in REMOTE_TERMS)
            if remainder:
                add_location_aliases(terms, remainder)
            else:
                requires_remote = True
            continue
        add_location_aliases(terms, normalized)
    return {
        "terms": dedupe_values(terms),
        "requires_remote": requires_remote,
    }


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


def annotate_location_match(row, target_locations):
    policy = build_location_terms(target_locations)
    evidence = row_location_evidence(row)
    evidence_normalized = normalize_for_match(evidence)
    matched_terms = [
        term for term in policy["terms"] if term_matches(term, evidence_normalized)
    ]
    remote_matched = not policy["requires_remote"] or any(
        term_matches(term, evidence_normalized) for term in REMOTE_TERMS
    )
    has_location_constraint = bool(policy["terms"] or policy["requires_remote"])
    matched = has_location_constraint and remote_matched and (
        bool(matched_terms) or not policy["terms"]
    )

    row["target_locations"] = target_locations or []
    row["location_match"] = {
        "required": has_location_constraint,
        "matched": matched,
        "matched_terms": matched_terms,
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


def add_location_aliases(terms, value):
    normalized = normalize_for_match(value)
    if not normalized:
        return
    terms.append(normalized)
    for key, aliases in LOCATION_ALIASES.items():
        if normalized == key or normalized in aliases:
            terms.extend(aliases)


def term_matches(term, text):
    normalized_term = normalize_for_match(term)
    if not normalized_term:
        return False
    pattern = rf"(?<![a-z0-9]){re.escape(normalized_term)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def normalize_for_match(value):
    return clean_text(value).lower().replace("-", " ").replace("/", " ")


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
