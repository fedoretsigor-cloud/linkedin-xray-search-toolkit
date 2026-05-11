import re

from src.text_utils import clean_text


N_A = "N/A"

GLOBAL_STACK_TERMS = [
    ".NET",
    "A/B testing",
    "ADAS",
    "Agile",
    "Airflow",
    "Allegro",
    "Android",
    "Angular",
    "API",
    "Appium",
    "AWS",
    "Azure",
    "BDD",
    "BigQuery",
    "BPMN",
    "C#",
    "C++",
    "CI/CD",
    "cloud",
    "Commodity Trading",
    "commodity risk",
    "commodities",
    "Compose",
    "Confluence",
    "Core Data",
    "crude oil",
    "CTRM",
    "Cypress",
    "DAX",
    "dbt",
    "Django",
    "Docker",
    "Endur",
    "energy risk",
    "Energy Trading",
    "ETL",
    "ETRM",
    "FastAPI",
    "Figma",
    "Front Office",
    "Git",
    "GitLab",
    "GCP",
    "GraphQL",
    "Hibernate",
    "HiL",
    "HTML",
    "iOS",
    "JPA",
    "Java",
    "JavaScript",
    "Jenkins",
    "Jetpack",
    "Jira",
    "Kafka",
    "Kotlin",
    "Kubernetes",
    "LLM",
    "Looker",
    "MLOps",
    "Middle Office",
    "microservices",
    "MongoDB",
    "natural gas",
    "Next.js",
    "NLP",
    "Node.js",
    "NoSQL",
    "Openlink",
    "Oracle",
    "Orchestrade",
    "Playwright",
    "PostgreSQL",
    "Power BI",
    "Power Trading",
    "PnL",
    "Puppeteer",
    "pytest",
    "Python",
    "PyTorch",
    "RabbitMQ",
    "React",
    "Redis",
    "Redux",
    "REST",
    "Right Angle",
    "RightAngle",
    "risk management",
    "Robot Framework",
    "scheduling",
    "Scrum",
    "Selenium",
    "settlements",
    "SIL",
    "Snowflake",
    "Spark",
    "Spring",
    "Spring Boot",
    "SQL",
    "Swift",
    "SwiftUI",
    "Tableau",
    "TensorFlow",
    "Terraform",
    "trade capture",
    "trading systems",
    "TypeScript",
    "UAT",
    "UIKit",
    "UML",
    "Vue",
]

NON_STACK_TERMS = {
    "analyst",
    "architect",
    "business analyst",
    "developer",
    "engineer",
    "manager",
    "owner",
    "profile",
    "software engineer",
}

ROLE_HEADLINE_TERMS = (
    "administrator",
    "analyst",
    "architect",
    "consultant",
    "cto",
    "data",
    "designer",
    "developer",
    "devops",
    "director",
    "engineer",
    "etrm",
    "functional",
    "head",
    "lead",
    "manager",
    "owner",
    "president",
    "principal",
    "product",
    "professional",
    "program",
    "project",
    "qa",
    "recruiter",
    "scientist",
    "sdet",
    "senior",
    "sme",
    "software",
    "specialist",
    "sre",
    "technical",
    "tester",
    "trader",
    "vp",
)

ROLE_TERMS_RE = re.compile(
    r"\b(?:analyst|architect|consultant|developer|engineer|lead|manager|owner|professional|specialist|sme)\b",
    re.IGNORECASE,
)
BIO_ROLE_RE = re.compile(
    r"^(?:i['`’]?m|i am)\s+(?:an?\s+)?(.+?)(?:\s+who\b|,|\.|;|\s+-\s+|\s+with\b|$)",
    re.IGNORECASE,
)
AS_ROLE_RE = re.compile(
    r"\bas\s+(?:an?\s+)?((?:[A-Za-z0-9+#/&-]+\s+){0,7}"
    r"(?:Analyst|Architect|Consultant|Developer|Engineer|Lead|Manager|Owner|Professional|Specialist|SME))\b",
    re.IGNORECASE,
)
HEADLINE_STOP_MARKERS = (
    " - Experience:",
    " - Education:",
    " - Location:",
    " Experience:",
    " Education:",
    " Location:",
    " About ",
    " Experience ",
    " Education ",
    " Contact info",
)

SOCIAL_MARKER_RE = re.compile(r"\b\d[\d,.]*\+?\s+(?:connections?|followers?|contacts?)\b", re.IGNORECASE)


def evidence_text(row):
    return clean_text(" ".join([row.get("result_title", ""), row.get("short_description", "")]))


def split_title_parts(value):
    return [clean_text(part) for part in re.split(r"\s+-\s+", clean_text(value)) if clean_text(part)]


def strip_linkedin_suffix(value):
    text = clean_text(value)
    text = re.sub(r"\s+[-|]\s*LinkedIn(?:\s.*)?$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^LinkedIn\s*[-|]\s*", "", text, flags=re.IGNORECASE)
    return clean_text(text)


def strip_markdown(value):
    text = clean_text(value)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"https?://\S+", "", text, flags=re.IGNORECASE)
    return clean_text(text)


def strip_name_prefix(value, name):
    text = clean_text(value)
    profile_name = clean_text(name)
    if not text or not profile_name:
        return text
    pattern = re.compile(rf"^{re.escape(profile_name)}\b\s*[-|,:]?\s*", re.IGNORECASE)
    return clean_text(pattern.sub("", text))


def strip_after_markers(value):
    text = clean_text(value)
    for marker in HEADLINE_STOP_MARKERS:
        section_marker = marker.strip().lower() in {"about", "experience", "education", "location", "contact info"}
        index = text.find(marker) if section_marker and ":" not in marker else text.lower().find(marker.lower())
        if index >= 0:
            text = text[:index]
    return clean_text(text)


def strip_location_tail(value, row):
    text = clean_text(value)
    location = clean_text(row.get("location", ""))
    if location and location.lower() in text.lower():
        index = text.lower().find(location.lower())
        if index > 0:
            text = text[:index]
    text = SOCIAL_MARKER_RE.split(text, 1)[0]
    return clean_text(text)


def has_role_cue(value):
    text = clean_text(value).lower()
    return any(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) for term in ROLE_HEADLINE_TERMS)


def is_profile_noise_line(value, row):
    text = clean_text(value).strip(" -|,")
    if not text:
        return True
    lowered = text.lower()
    blocked = {
        clean_text(row.get("profile_name", "")).lower(),
        clean_text(row.get("location", "")).lower(),
        "about",
        "experience",
        "education",
        "contact info",
        "linkedin",
    }
    if lowered in blocked:
        return True
    if re.match(r"^(?:about|experience|education|contact info)(?:[:\s]|$)", lowered):
        return True
    if SOCIAL_MARKER_RE.search(text):
        return True
    if lowered.startswith(("connections", "followers", "reactions", "posts")):
        return True
    return False


def role_phrase_from_bio_sentence(value):
    text = clean_text(value).strip(" -|,")
    match = BIO_ROLE_RE.search(text)
    if match:
        phrase = clean_text(match.group(1)).strip(" -|,")
        if has_role_cue(phrase):
            return phrase

    match = AS_ROLE_RE.search(text)
    if match:
        phrase = clean_text(match.group(1)).strip(" -|,")
        if has_role_cue(phrase):
            return phrase

    if re.match(r"^experienced\s+", text, re.IGNORECASE) and ROLE_TERMS_RE.search(text):
        phrase = re.split(r"\s+with\b|,|\.|;", text, 1, flags=re.IGNORECASE)[0]
        return clean_text(phrase).strip(" -|,")

    return ""


def normalize_description_headline(value, row):
    text = strip_markdown(value)
    text = strip_name_prefix(text, row.get("profile_name", ""))
    text = strip_after_markers(text)
    text = strip_location_tail(text, row)
    text = re.sub(r"\s*\.\.\.$", "", text).strip(" -|,")
    if not text or is_profile_noise_line(text, row):
        return ""

    bio_phrase = role_phrase_from_bio_sentence(text)
    if bio_phrase:
        return bio_phrase

    sentence_like = bool(re.search(r"\b(?:i|we|my|our|years?|worked|helps?|building|driving)\b", text, re.IGNORECASE))
    has_title_separator = any(separator in text for separator in ("|", "/", " - ", "•"))
    if sentence_like and not has_title_separator:
        return ""

    if not has_role_cue(text):
        return ""
    return text


def valid_headline(value, row):
    headline = clean_text(value).strip(" -|,")
    if not headline or headline.lower() == N_A.lower():
        return ""
    blocked = {
        clean_text(row.get("profile_name", "")).lower(),
        clean_text(row.get("location", "")).lower(),
        "linkedin",
        "profile",
    }
    if headline.lower() in blocked:
        return ""
    if len(headline) > 180:
        headline = clean_text(headline[:180].rsplit(" ", 1)[0])
    if any(marker.lower().strip() == headline.lower() for marker in ("Experience", "Education", "Location")):
        return ""
    if not re.search(r"[A-Za-z]", headline):
        return ""
    return headline


def extract_role_from_title(row):
    title = strip_linkedin_suffix(row.get("result_title", ""))
    name = clean_text(row.get("profile_name", ""))
    if not title:
        return ""

    parts = split_title_parts(title)
    if len(parts) > 1 and name and parts[0].lower() == name.lower():
        for part in parts[1:]:
            candidate = valid_headline(strip_after_markers(part), row)
            if candidate:
                return candidate

    if "|" in title and name and title.lower().startswith(name.lower()):
        candidate = strip_name_prefix(title, name)
        candidate = strip_after_markers(strip_linkedin_suffix(candidate))
        candidate = valid_headline(candidate, row)
        if candidate:
            return candidate

    candidate = strip_name_prefix(title, name)
    candidate = strip_after_markers(candidate)
    return valid_headline(candidate, row)


def extract_role_from_description(row):
    description = clean_text(row.get("short_description", ""))
    if not description:
        return ""
    candidates = []
    for line in description.splitlines()[:10]:
        candidate = normalize_description_headline(line, row)
        if candidate:
            candidates.append(candidate)
    if not candidates:
        for fragment in re.split(r"\s+-\s+|\s{2,}", description)[:8]:
            candidate = normalize_description_headline(fragment, row)
            if candidate:
                candidates.append(candidate)
    for candidate in candidates:
        headline = valid_headline(candidate, row)
        if headline:
            return headline
    return ""


def extract_profile_role(row):
    return extract_role_from_title(row) or extract_role_from_description(row)


def flatten_values(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values = []
        for item in value.values():
            values.extend(flatten_values(item))
        return values
    if isinstance(value, (list, tuple, set)):
        values = []
        for item in value:
            values.extend(flatten_values(item))
        return values
    return [str(value)]


def split_terms(value):
    terms = []
    for item in flatten_values(value):
        for part in re.split(r"[|,;/]+", clean_text(item)):
            term = clean_text(part)
            if term:
                terms.append(term)
    return terms


def candidate_stack_terms(row, search):
    role_pattern = (search or {}).get("role_pattern") or {}
    search_intent = (search or {}).get("search_intent") or {}
    terms = []
    terms.extend(split_terms(row.get("technology", "")))
    terms.extend(split_terms(row.get("query_technology", "")))
    terms.extend(split_terms((search or {}).get("tech_groups", [])))
    terms.extend(split_terms(search_intent.get("must_have_keywords", [])))
    terms.extend(split_terms(search_intent.get("domain_keywords", [])))
    terms.extend(split_terms(search_intent.get("tool_keywords", [])))
    terms.extend(split_terms(role_pattern.get("fixed_anchors", [])))
    terms.extend(split_terms(role_pattern.get("domain_terms", [])))
    terms.extend(split_terms(role_pattern.get("tool_terms", [])))
    terms.extend(split_terms(role_pattern.get("grouped_anchor_alternates", [])))
    terms.extend(GLOBAL_STACK_TERMS)
    return dedupe_terms(terms)


def dedupe_terms(terms):
    deduped = []
    seen = set()
    for term in terms:
        text = clean_text(term)
        key = text.lower()
        if not text or key in seen or key in NON_STACK_TERMS:
            continue
        seen.add(key)
        deduped.append(text)
    return deduped


def contains_term(text, term):
    normalized = clean_text(term).lower()
    if not normalized:
        return False
    if re.search(r"[^a-z0-9\s]", normalized):
        return normalized in text
    if " " in normalized:
        return normalized in text
    return re.search(rf"(?<![a-z0-9]){re.escape(normalized)}(?![a-z0-9])", text) is not None


def extract_profile_stack(row, search=None, max_terms=8):
    text = evidence_text(row).lower()
    if not text:
        return ""
    matches = [term for term in candidate_stack_terms(row, search or {}) if contains_term(text, term)]
    return " | ".join(matches[:max_terms])
