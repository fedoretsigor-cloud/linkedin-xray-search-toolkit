import re

from src.text_utils import clean_text


GENERIC_SEARCH_PHRASES = {
    "ability",
    "ability to",
    "experience",
    "experience with",
    "proven experience",
    "proven experience developing",
    "strong communication skills",
    "technical documentation",
    "requirements",
    "development",
    "testing",
}

CANONICAL_TERMS = [
    ("robot framework", "Robot Framework", "language"),
    ("python", "Python", "language"),
    ("pytest", "pytest", "language"),
    ("automotive", "automotive", "domain"),
    ("embedded", "embedded", "domain"),
    ("multi-ecu", "multi-ECU", "domain"),
    ("multi ecu", "multi-ECU", "domain"),
    ("ecu", "ECU", "domain"),
    ("adas", "ADAS", "domain"),
    ("hil", "HiL", "domain"),
    ("hardware-in-the-loop", "HiL", "domain"),
    ("sil", "SIL", "domain"),
    ("software-in-the-loop", "SIL", "domain"),
    ("can", "CAN", "domain"),
    ("lin", "LIN", "domain"),
    ("ethernet", "Ethernet", "domain"),
    ("git", "Git", "tooling"),
    ("jfrog", "JFrog", "tooling"),
    ("artifactory", "Artifactory", "tooling"),
    ("virtual environment", "virtual environments", "tooling"),
    ("virtual environments", "virtual environments", "tooling"),
    ("dependency", "dependencies", "tooling"),
    ("dependencies", "dependencies", "tooling"),
    ("log analysis", "log analysis", "tooling"),
    ("analyze logs", "log analysis", "tooling"),
    ("logs", "logs", "tooling"),
    ("bdd", "BDD", "methodology"),
    ("gherkin", "Gherkin", "methodology"),
    ("keyword-driven", "keyword-driven testing", "methodology"),
    ("selenium", "Selenium", "language"),
    ("cypress", "Cypress", "language"),
    ("playwright", "Playwright", "language"),
    ("puppeteer", "Puppeteer", "language"),
    ("typescript", "TypeScript", "language"),
    ("javascript", "JavaScript", "language"),
    ("java", "Java", "language"),
    ("spring boot", "Spring Boot", "tooling"),
    ("spring", "Spring", "tooling"),
    ("kafka", "Kafka", "tooling"),
    ("aws", "AWS", "tooling"),
]


def build_search_intent(brief):
    brief = brief or {}
    original = brief.get("original_brief") if isinstance(brief.get("original_brief"), dict) else {}
    source = {**original, **brief}
    terms_by_kind = {"language": [], "domain": [], "tooling": [], "methodology": [], "other": []}

    for value in collect_source_phrases(source):
        for kind, term in extract_terms(value):
            add_unique(terms_by_kind.setdefault(kind, []), term)

    search_keywords = [
        clean_search_keyword(value)
        for value in source.get("search_keywords", [])
        if clean_search_keyword(value)
    ]
    for keyword in search_keywords:
        if is_generic_phrase(keyword):
            continue
        if extract_terms(keyword):
            continue
        kind = classify_term(keyword)
        add_unique(terms_by_kind.setdefault(kind, []), keyword)

    skill_groups = build_skill_groups(terms_by_kind)
    return {
        "role_titles": dedupe_values([source.get("role", ""), *source.get("role_variants", [])])[:5],
        "must_have_keywords": dedupe_values(terms_by_kind.get("language", []) + terms_by_kind.get("domain", [])),
        "domain_keywords": dedupe_values(terms_by_kind.get("domain", [])),
        "tool_keywords": dedupe_values(terms_by_kind.get("tooling", []) + terms_by_kind.get("methodology", [])),
        "optional_keywords": dedupe_values(terms_by_kind.get("other", [])),
        "skill_groups": skill_groups,
    }


def collect_source_phrases(source):
    values = []
    for key in ("search_keywords", "must_have_skills", "nice_to_have_skills"):
        values.extend(source.get(key, []) if isinstance(source.get(key), list) else [])
    values.extend([source.get("domain", ""), source.get("role", "")])
    return values


def extract_terms(value):
    text = clean_text(value)
    normalized = normalize_for_match(text)
    matches = []
    for needle, label, kind in CANONICAL_TERMS:
        if term_matches(needle, normalized):
            matches.append((kind, label))
    if matches:
        return matches
    keyword = clean_search_keyword(text)
    if keyword and not is_generic_phrase(keyword):
        return [(classify_term(keyword), keyword)]
    return []


def term_matches(needle, normalized):
    pattern = rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])"
    return re.search(pattern, normalized) is not None


def normalize_for_match(value):
    return clean_text(value).lower().replace("/", " ").replace("-", " ")


def clean_search_keyword(value):
    text = clean_text(value).strip(" ,;:()[]{}-")
    text = re.sub(r"\s+", " ", text)
    if not text or len(text) > 35:
        return ""
    if len(text.split()) > 4:
        return ""
    return text


def classify_term(value):
    normalized = normalize_for_match(value)
    for needle, _label, kind in CANONICAL_TERMS:
        if term_matches(needle, normalized):
            return kind
    return "other"


def is_generic_phrase(value):
    normalized = normalize_for_match(value)
    return normalized in GENERIC_SEARCH_PHRASES


def build_skill_groups(terms_by_kind):
    groups = []
    primary = dedupe_values(terms_by_kind.get("language", []))[:3]
    domain = dedupe_values(terms_by_kind.get("domain", []))[:6]
    tooling = dedupe_values(terms_by_kind.get("tooling", []) + terms_by_kind.get("methodology", []))[:6]
    other = dedupe_values(terms_by_kind.get("other", []))[:3]

    if primary:
        groups.append(primary)
    if domain:
        groups.extend(chunk(domain, 3))
    if tooling:
        groups.extend(chunk(tooling, 3))
    if other and len(groups) < 4:
        groups.append(other)
    return groups or [[]]


def chunk(values, size):
    return [values[index : index + size] for index in range(0, len(values), size)]


def dedupe_values(values):
    result = []
    for value in values:
        add_unique(result, value)
    return result


def add_unique(values, value):
    text = clean_text(value)
    key = text.lower()
    if text and key not in {item.lower() for item in values}:
        values.append(text)
