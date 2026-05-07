import json
import os

from openai import OpenAI

from src.text_utils import clean_text


RESUME_REVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "decision": {
            "type": "string",
            "enum": ["strong_fit", "possible_fit", "not_fit", "unclear"],
        },
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "summary": {"type": "string"},
        "resume_evidence": {"type": "array", "items": {"type": "string"}},
        "profile_alignment": {"type": "array", "items": {"type": "string"}},
        "contradictions": {"type": "array", "items": {"type": "string"}},
        "missing_info": {"type": "array", "items": {"type": "string"}},
        "questions_to_ask": {"type": "array", "items": {"type": "string"}},
        "recommended_next_action": {"type": "string"},
    },
    "required": [
        "decision",
        "score",
        "summary",
        "resume_evidence",
        "profile_alignment",
        "contradictions",
        "missing_info",
        "questions_to_ask",
        "recommended_next_action",
    ],
}


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in .env")
    return OpenAI(api_key=api_key)


def analyze_resume_text(*, confirmed_brief, candidate, profile_review, resume_text):
    text = clean_text(resume_text)
    if len(text) < 80:
        raise RuntimeError("Paste or upload more resume text before analysis")

    client = get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    prompt = build_resume_review_prompt(
        confirmed_brief=confirmed_brief or {},
        candidate=candidate or {},
        profile_review=profile_review or {},
        resume_text=text[:24000],
    )

    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful technical recruiter reviewing a candidate resume. "
                        "Compare the resume against the confirmed hiring brief and previous "
                        "profile review. Be conservative and do not invent experience."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "resume_review",
                    "schema": RESUME_REVIEW_SCHEMA,
                    "strict": True,
                }
            },
        )
        return normalize_resume_review(json.loads(response.output_text))
    except TypeError:
        return analyze_resume_text_chat(client, model, prompt)


def analyze_resume_text_chat(client, model, prompt):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful technical recruiter. Return only valid JSON. "
                    "Use only evidence visible in the provided resume, profile review, and brief."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
    )
    return normalize_resume_review(json.loads(response.choices[0].message.content))


def build_resume_review_prompt(*, confirmed_brief, candidate, profile_review, resume_text):
    return f"""
Review this candidate resume against the confirmed hiring brief and previous profile review.

Confirmed brief:
{json.dumps(confirmed_brief, ensure_ascii=False, indent=2)}

Candidate search result:
{json.dumps(candidate, ensure_ascii=False, indent=2)}

Previous profile review:
{json.dumps(profile_review, ensure_ascii=False, indent=2)}

Resume text:
---
{resume_text}
---

Return JSON with:
- decision: strong_fit, possible_fit, not_fit, or unclear
- score: 0-100
- summary
- resume_evidence: concrete evidence found in the resume
- profile_alignment: where resume confirms or supports the previous profile/search evidence
- contradictions: contradictions or suspicious mismatches between resume, profile review, and brief
- missing_info
- questions_to_ask
- recommended_next_action

Rules:
- Use only visible evidence.
- If the resume does not prove must-have skills, lower the score and list missing_info.
- Questions should be practical recruiter follow-ups.
- recommended_next_action should be one short human-controlled action, not an automated send.
""".strip()


def normalize_resume_review(review):
    return {
        "decision": clean_text(review.get("decision", "unclear")) or "unclear",
        "score": normalize_score(review.get("score", 0)),
        "summary": clean_text(review.get("summary", "")),
        "resume_evidence": clean_list(review.get("resume_evidence", [])),
        "profile_alignment": clean_list(review.get("profile_alignment", [])),
        "contradictions": clean_list(review.get("contradictions", [])),
        "missing_info": clean_list(review.get("missing_info", [])),
        "questions_to_ask": clean_list(review.get("questions_to_ask", [])),
        "recommended_next_action": clean_text(review.get("recommended_next_action", "")),
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
