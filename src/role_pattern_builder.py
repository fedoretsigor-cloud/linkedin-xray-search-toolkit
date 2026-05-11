from src.text_utils import clean_text
from src.xray_search import build_title_pattern


ROLE_FAMILIES = [
    {
        "family": "Energy / ETRM Business Analyst",
        "triggers": [
            "etrm",
            "ctrm",
            "front office",
            "power trading",
            "energy trading",
            "commodity trading",
            "commodities",
            "orchestrade",
            "endur",
            "rightangle",
            "allegro",
            "openlink",
        ],
        "core_terms": ["Business Analyst"],
        "role_terms": [],
        "query_strategy": "grouped_anchors",
        "fixed_anchors": ["Front Office"],
        "domain_terms": ["Power Trading", "Energy Trading", "ETRM"],
        "tool_terms": ["Orchestrade", "Endur"],
    },
    {
        "family": "Business Analysis",
        "triggers": [
            "business analyst",
            "systems analyst",
            "system analyst",
            "requirements analyst",
            "functional analyst",
            "functional consultant",
            "business systems analyst",
            "technical business analyst",
        ],
        "core_terms": ["Business"],
        "role_terms": ["Analyst", "Systems Analyst", "Requirements Analyst", "Functional Analyst"],
    },
    {
        "family": "QA Automation",
        "triggers": ["qa", "quality assurance", "test automation", "automation test", "automated test", "sdet", "tester"],
        "core_terms": ["Automation"],
        "role_terms": ["Engineer", "QA", "Tester", "Test Engineer", "SDET"],
    },
    {
        "family": "Java Backend",
        "triggers": ["java backend", "backend java", "java developer", "java engineer"],
        "core_terms": ["Java"],
        "role_terms": ["Backend", "Back End", "Engineer", "Developer", "Software Engineer"],
    },
    {
        "family": "Frontend",
        "triggers": ["frontend", "front end", "react", "angular", "vue"],
        "core_terms": ["Frontend", "Front End"],
        "role_terms": ["Engineer", "Developer", "Software Engineer"],
    },
    {
        "family": "Fullstack",
        "triggers": ["fullstack", "full stack"],
        "core_terms": ["Fullstack", "Full Stack"],
        "role_terms": ["Engineer", "Developer", "Software Engineer"],
    },
    {
        "family": "iOS",
        "triggers": ["ios", "swift", "iphone"],
        "core_terms": ["iOS", "Swift"],
        "role_terms": ["Engineer", "Developer", "Mobile Engineer", "Mobile Developer"],
    },
    {
        "family": "Android",
        "triggers": ["android", "kotlin"],
        "core_terms": ["Android", "Kotlin"],
        "role_terms": ["Engineer", "Developer", "Mobile Engineer", "Mobile Developer"],
    },
    {
        "family": "DevOps / SRE",
        "triggers": ["devops", "sre", "site reliability", "platform engineer", "infrastructure"],
        "core_terms": ["DevOps", "SRE", "Site Reliability"],
        "role_terms": ["Engineer", "Platform Engineer", "Infrastructure Engineer"],
    },
    {
        "family": "Data Engineer",
        "triggers": ["data engineer", "etl", "pipeline engineer", "analytics engineer"],
        "core_terms": ["Data"],
        "role_terms": ["Engineer", "ETL", "Pipeline Engineer", "Analytics Engineer"],
    },
    {
        "family": "Data / BI Analytics",
        "triggers": [
            "data analyst",
            "bi analyst",
            "business intelligence",
            "reporting analyst",
            "analytics analyst",
            "product analyst",
            "growth analyst",
        ],
        "core_terms": ["Data", "BI", "Analytics"],
        "role_terms": ["Analyst", "Business Intelligence Analyst", "Reporting Analyst", "Product Analyst"],
    },
    {
        "family": "ML / AI Engineer",
        "triggers": ["machine learning", "ml engineer", "ai engineer", "applied scientist"],
        "core_terms": ["Machine Learning", "ML", "AI"],
        "role_terms": ["Engineer", "Applied Scientist", "Research Engineer"],
    },
    {
        "family": "Product Management",
        "triggers": ["product manager", "product owner", "technical product manager", "product lead", "product management"],
        "core_terms": ["Product"],
        "role_terms": ["Manager", "Owner", "Product Lead", "Technical Product Manager"],
    },
    {
        "family": "Project / Delivery Management",
        "triggers": [
            "project manager",
            "program manager",
            "delivery manager",
            "scrum master",
            "agile coach",
            "technical project manager",
            "engagement manager",
        ],
        "core_terms": ["Project", "Program", "Delivery"],
        "role_terms": ["Manager", "Scrum Master", "Agile Coach"],
    },
    {
        "family": "Architecture / Leadership",
        "triggers": [
            "solution architect",
            "software architect",
            "technical architect",
            "enterprise architect",
            "engineering manager",
            "development manager",
            "technical manager",
            "tech lead",
            "technical lead",
            "lead software engineer",
        ],
        "core_terms": ["Solution", "Software", "Technical", "Engineering"],
        "role_terms": ["Architect", "Manager", "Tech Lead", "Technical Lead"],
    },
    {
        "family": "UX / Product Design",
        "triggers": [
            "product designer",
            "ux designer",
            "ui designer",
            "ui/ux",
            "ux/ui",
            "interaction designer",
            "ux researcher",
            "user researcher",
        ],
        "core_terms": ["Product", "UX", "UI"],
        "role_terms": ["Designer", "Researcher", "Interaction Designer"],
    },
    {
        "family": "Embedded",
        "triggers": ["embedded", "firmware"],
        "core_terms": ["Embedded"],
        "role_terms": ["Engineer", "Software Engineer", "Firmware Engineer"],
    },
]


def build_role_pattern(role, role_variants=None, context=None):
    role = clean_text(role)
    role_variants = [clean_text(value) for value in role_variants or [] if clean_text(value)]
    title_text = normalize_for_match(" ".join([role, *role_variants]))
    context_text = normalize_for_match(" ".join(flatten_context_values(context)))

    family = choose_family(title_text, context_text)
    if family:
        title_pattern = build_title_pattern_group(family["core_terms"], family["role_terms"])
        return {
            "family": family["family"],
            "mode": "semantic",
            "confidence": family.get("confidence", "medium"),
            "core_terms": family["core_terms"],
            "role_terms": family["role_terms"],
            "query_strategy": family.get("query_strategy", "skill_groups"),
            "fixed_anchors": family.get("fixed_anchors", []),
            "domain_terms": family.get("domain_terms", []),
            "tool_terms": family.get("tool_terms", []),
            "title_pattern": title_pattern,
            "fallback_role": role,
            "fallback_role_variants": role_variants,
            "matched_triggers": family.get("matched_triggers", []),
        }

    return {
        "family": "Custom role",
        "mode": "fallback",
        "confidence": "low",
        "core_terms": [role] if role else [],
        "role_terms": role_variants,
        "query_strategy": "skill_groups",
        "fixed_anchors": [],
        "domain_terms": [],
        "tool_terms": [],
        "title_pattern": build_title_pattern(role, role_variants),
        "fallback_role": role,
        "fallback_role_variants": role_variants,
        "matched_triggers": [],
    }


def choose_family(title_text, context_text):
    title_matches = []
    context_matches = []
    for family in ROLE_FAMILIES:
        title_hits = [trigger for trigger in family["triggers"] if trigger in title_text]
        context_hits = [trigger for trigger in family["triggers"] if trigger in context_text]
        if title_hits:
            title_matches.append(
                {
                    **family,
                    "score": len(title_hits),
                    "confidence": "high",
                    "matched_triggers": dedupe_values(title_hits),
                }
            )
        elif context_hits:
            context_matches.append(
                {
                    **family,
                    "score": len(context_hits),
                    "confidence": "medium",
                    "matched_triggers": dedupe_values(context_hits),
                }
            )

    if title_matches:
        return max(title_matches, key=lambda item: item["score"])
    if context_matches:
        return max(context_matches, key=lambda item: item["score"])
    return None


def flatten_context_values(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values = []
        for item in value.values():
            values.extend(flatten_context_values(item))
        return values
    if isinstance(value, (list, tuple, set)):
        values = []
        for item in value:
            values.extend(flatten_context_values(item))
        return values
    return [str(value)]


def build_title_pattern_group(core_terms, role_terms):
    core = build_or_group(core_terms)
    roles = build_or_group(role_terms)
    return " ".join(part for part in [core, roles] if part)


def build_or_group(values):
    cleaned = dedupe_values(values)
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return f"\"{cleaned[0]}\""
    return "(" + " OR ".join(f"\"{value}\"" for value in cleaned) + ")"


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
