import json
import os

from openai import OpenAI

from src.requirement_fetcher import fetch_requirement_text
from src.text_utils import clean_text


REQUIREMENT_BRIEF_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "role": {"type": "string"},
        "seniority": {"type": "string"},
        "location": {"type": "string"},
        "remote_policy": {"type": "string"},
        "domain": {"type": "string"},
        "must_have_skills": {"type": "array", "items": {"type": "string"}},
        "nice_to_have_skills": {"type": "array", "items": {"type": "string"}},
        "role_variants": {"type": "array", "items": {"type": "string"}},
        "search_keywords": {"type": "array", "items": {"type": "string"}},
        "exclusions": {"type": "array", "items": {"type": "string"}},
        "open_questions": {"type": "array", "items": {"type": "string"}},
        "human_summary": {"type": "string"},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": [
        "role",
        "seniority",
        "location",
        "remote_policy",
        "domain",
        "must_have_skills",
        "nice_to_have_skills",
        "role_variants",
        "search_keywords",
        "exclusions",
        "open_questions",
        "human_summary",
        "confidence",
    ],
}


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in .env")
    return OpenAI(api_key=api_key)


def analyze_requirement_url(url):
    page = fetch_requirement_text(url)
    brief = analyze_requirement_text(page["text"], source_url=page["url"], page_title=page["title"])
    return {
        "source_url": page["url"],
        "page_title": page["title"],
        "truncated": page["truncated"],
        "brief": brief,
    }


def analyze_requirement_text(text, *, source_url="", page_title=""):
    client = get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    prompt = build_requirement_prompt(text, source_url=source_url, page_title=page_title)

    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a sourcing requirement analyst. Extract hiring requirements "
                        "into strict JSON. Be conservative: if evidence is missing, add an "
                        "open question instead of guessing."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "requirement_brief",
                    "schema": REQUIREMENT_BRIEF_SCHEMA,
                    "strict": True,
                }
            },
        )
        return normalize_brief(json.loads(response.output_text))
    except TypeError:
        return analyze_requirement_text_chat(client, model, prompt)


def analyze_requirement_text_chat(client, model, prompt):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a sourcing requirement analyst. Return only valid JSON matching "
                    "the requested schema. Be conservative and do not guess missing evidence."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    return normalize_brief(json.loads(response.choices[0].message.content))


def build_requirement_prompt(text, *, source_url="", page_title=""):
    return f"""
Analyze this public hiring requirement page and extract a sourcing brief.

Source URL: {source_url or "unknown"}
Page title: {page_title or "unknown"}

Return JSON with exactly these fields:
- role
- seniority
- location
- remote_policy
- domain
- must_have_skills
- nice_to_have_skills
- role_variants
- search_keywords
- exclusions
- open_questions
- human_summary
- confidence: low, medium, or high

Guidelines:
- Use English.
- Keep role concise and searchable.
- role_variants should be useful search titles, not generic noise.
- must_have_skills should include only clearly required skills.
- search_keywords can include domain keywords and evidence terms.
- open_questions should contain practical questions for the human to confirm.
- human_summary should start with "I understood the task as:".

Requirement text:
---
{text}
---
""".strip()


def normalize_brief(brief):
    return {
        "role": clean_text(brief.get("role", "")),
        "seniority": clean_text(brief.get("seniority", "")),
        "location": clean_text(brief.get("location", "")),
        "remote_policy": clean_text(brief.get("remote_policy", "")),
        "domain": clean_text(brief.get("domain", "")),
        "must_have_skills": clean_list(brief.get("must_have_skills", [])),
        "nice_to_have_skills": clean_list(brief.get("nice_to_have_skills", [])),
        "role_variants": clean_list(brief.get("role_variants", [])),
        "search_keywords": clean_list(brief.get("search_keywords", [])),
        "exclusions": clean_list(brief.get("exclusions", [])),
        "open_questions": clean_list(brief.get("open_questions", [])),
        "human_summary": clean_text(brief.get("human_summary", "")),
        "confidence": clean_text(brief.get("confidence", "low")).lower() or "low",
    }


def clean_list(values):
    if not isinstance(values, list):
        return []
    cleaned = []
    seen = set()
    for value in values:
        item = clean_text(value)
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            cleaned.append(item)
    return cleaned
