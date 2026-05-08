import re

from src.text_utils import clean_text


PROFILE_CONTEXT_MARKERS = {
    "experience",
    "about",
    "education",
    "connections",
    "followers",
    "developer",
    "engineer",
    "consultant",
    "architect",
}


def _tokenize(value):
    return [
        token
        for token in re.split(r"[^a-z0-9+#.]+", clean_text(value).lower())
        if token
    ]


def _split_stack(technology):
    parts = []
    for group in clean_text(technology).split("|"):
        for item in group.split(","):
            value = clean_text(item)
            if value:
                parts.append(value)
    return parts


def _contains_phrase(text, phrase):
    phrase = clean_text(phrase).lower()
    if not phrase:
        return False
    return phrase in text


def score_candidate(candidate, search):
    score = 25
    reasons = []
    risks = []
    source_site = clean_text(candidate.get("source_site", ""))
    candidate_type = clean_text(candidate.get("candidate_type", ""))
    description = clean_text(candidate.get("short_description", ""))
    description_lower = description.lower()
    role = clean_text(candidate.get("role", ""))
    technology = clean_text(candidate.get("technology", ""))
    location = clean_text(candidate.get("location", ""))
    location_match = candidate.get("location_match", {}) or {}
    target_location = clean_text(candidate.get("target_location", ""))
    profile_name = clean_text(candidate.get("profile_name", ""))

    if source_site == "linkedin" and candidate.get("is_linkedin_profile"):
        score += 18
        reasons.append("Direct LinkedIn profile URL")
    elif source_site == "linkedin":
        risks.append("LinkedIn result is not a direct /in/ profile")
    elif source_site == "facebook":
        score += 8
        reasons.append("Facebook result passed open-to-work filter")
    elif source_site == "devpost":
        if candidate_type == "project_maker":
            score += 10
            reasons.append("Devpost maker evidence found")
        else:
            score -= 20
            risks.append("Devpost project has no visible maker candidate")

    if profile_name:
        score += 5
    else:
        risks.append("Candidate name is missing")

    if role:
        role_tokens = _tokenize(role)
        matched_role_tokens = [token for token in role_tokens if token in description_lower]
        if _contains_phrase(description_lower, role):
            score += 20
            reasons.append(f"Description mentions requested role: {role}")
        elif matched_role_tokens:
            score += min(14, 5 * len(matched_role_tokens))
            reasons.append(f"Description matches role keywords: {', '.join(matched_role_tokens)}")
        else:
            score += 6
            risks.append("Requested role is not clearly visible in indexed text")

    stack_parts = _split_stack(technology)
    if stack_parts:
        matched_stack = [part for part in stack_parts if _contains_phrase(description_lower, part)]
        if matched_stack:
            score += min(26, 9 * len(matched_stack))
            reasons.append(f"Mentions stack keywords: {', '.join(matched_stack)}")
        else:
            risks.append("Tech stack is not clearly visible in indexed text")
    else:
        risks.append("No stack keywords were provided for scoring")

    if target_location:
        if location_match.get("matched"):
            score += 14
            matched_terms = ", ".join(location_match.get("matched_terms") or [location or target_location])
            reasons.append(f"Indexed text matches strict location: {matched_terms}")
        elif _contains_phrase(description_lower, target_location):
            score += 14
            reasons.append(f"Description mentions target location: {target_location}")
        else:
            risks.append("Target location is not clearly visible in indexed profile text")

    context_hits = [marker for marker in PROFILE_CONTEXT_MARKERS if marker in description_lower]
    if len(description) >= 80:
        score += 6
        reasons.append("Profile snippet has enough context for review")
    elif description:
        score += 2
        risks.append("Profile snippet is short")
    else:
        risks.append("Very little indexed context is available")

    if context_hits:
        score += min(8, 2 * len(context_hits))

    if source_site == "facebook" and ("open to work" in description_lower or "currently looking" in description_lower):
        score += 6
        reasons.append("Open-to-work signal is visible")

    status = "Need review"
    if source_site == "devpost" and candidate_type != "project_maker":
        status = "Weak match"
        score = min(score, 45)
    if score >= 88:
        status = "Strong match"
    elif score >= 74:
        status = "Good match"
    elif score < 52:
        status = "Weak match"

    return {
        "score": min(score, 99),
        "status": status,
        "reasons": reasons or ["Relevant source result matched the search inputs"],
        "risks": risks or ["Need manual validation before outreach"],
    }
