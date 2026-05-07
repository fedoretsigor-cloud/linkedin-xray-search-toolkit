import json
import os

from openai import OpenAI

from src.text_utils import clean_text


PROFILE_REVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "decision": {
            "type": "string",
            "enum": ["strong_fit", "possible_fit", "not_fit", "unclear"],
        },
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "summary": {"type": "string"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "risks": {"type": "array", "items": {"type": "string"}},
        "missing_info": {"type": "array", "items": {"type": "string"}},
        "questions_to_ask": {"type": "array", "items": {"type": "string"}},
        "outreach_message": {"type": "string"},
    },
    "required": [
        "decision",
        "score",
        "summary",
        "evidence",
        "risks",
        "missing_info",
        "questions_to_ask",
        "outreach_message",
    ],
}


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in .env")
    return OpenAI(api_key=api_key)


def analyze_profile_text(*, confirmed_brief, candidate, profile_text):
    text = clean_text(profile_text)
    if len(text) < 80:
        raise RuntimeError("Paste more profile text before analysis")

    client = get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    prompt = build_profile_review_prompt(
        confirmed_brief=confirmed_brief or {},
        candidate=candidate or {},
        profile_text=text[:18000],
    )

    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful technical sourcing reviewer. Compare pasted profile "
                        "text against the confirmed hiring brief. Be conservative and cite only "
                        "evidence visible in the pasted text or candidate search snippet."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "profile_review",
                    "schema": PROFILE_REVIEW_SCHEMA,
                    "strict": True,
                }
            },
        )
        return normalize_review(json.loads(response.output_text))
    except TypeError:
        return analyze_profile_text_chat(client, model, prompt)


def analyze_profile_text_chat(client, model, prompt):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful technical sourcing reviewer. Return only valid JSON. "
                    "Be conservative and do not invent candidate experience."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    return normalize_review(json.loads(response.choices[0].message.content))


def build_profile_review_prompt(*, confirmed_brief, candidate, profile_text):
    return f"""
Review this pasted candidate profile against the confirmed hiring brief.

Confirmed brief:
{json.dumps(confirmed_brief, ensure_ascii=False, indent=2)}

Candidate search result:
{json.dumps(candidate, ensure_ascii=False, indent=2)}

Pasted profile text:
---
{profile_text}
---

Return JSON with:
- decision: strong_fit, possible_fit, not_fit, or unclear
- score: 0-100
- summary
- evidence
- risks
- missing_info
- questions_to_ask
- outreach_message

Rules:
- Use only evidence from pasted profile text and candidate search result.
- If must-have evidence is missing, lower the score and add missing_info.
- Questions should be practical questions a recruiter can ask the candidate.
- Outreach should be concise and human-controlled, not automatically sent.
""".strip()


def normalize_review(review):
    return {
        "decision": clean_text(review.get("decision", "unclear")) or "unclear",
        "score": normalize_score(review.get("score", 0)),
        "summary": clean_text(review.get("summary", "")),
        "evidence": clean_list(review.get("evidence", [])),
        "risks": clean_list(review.get("risks", [])),
        "missing_info": clean_list(review.get("missing_info", [])),
        "questions_to_ask": clean_list(review.get("questions_to_ask", [])),
        "outreach_message": clean_text(review.get("outreach_message", "")),
    }


def normalize_score(value):
    try:
        return max(0, min(100, int(value)))
    except (TypeError, ValueError):
        return 0


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
