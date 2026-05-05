from src.text_utils import clean_text


def score_candidate(candidate, search):
    score = 35
    reasons = []
    risks = []
    source_site = candidate.get("source_site", "")
    description = clean_text(candidate.get("short_description", "")).lower()
    role = clean_text(candidate.get("role", ""))
    technology = clean_text(candidate.get("technology", ""))
    location = clean_text(candidate.get("location", ""))

    if role:
        score += 15
        reasons.append(f"Matches requested role: {role}")
    if technology:
        tech_parts = [part.strip() for part in technology.split("|") if part.strip()]
        matched = [part for part in tech_parts if part.lower() in description]
        if matched:
            score += min(25, 8 * len(matched))
            reasons.append(f"Mentions stack keywords: {', '.join(matched)}")
        else:
            risks.append("Tech stack is not clearly visible in indexed text")
    if location:
        score += 10
        reasons.append(f"Search location matched: {location}")

    if source_site == "linkedin":
        score += 15
        reasons.append("LinkedIn profile result is usually higher confidence")
    elif source_site == "facebook":
        score += 5
        reasons.append("Facebook result passed open-to-work filter")
        if "open to work" in description or "currently looking" in description:
            score += 5

    if candidate.get("is_linkedin_profile"):
        score += 5
    else:
        risks.append("Profile URL may not be a direct LinkedIn profile")

    if not candidate.get("short_description"):
        risks.append("Very little indexed context is available")

    status = "Need review"
    if score >= 90:
        status = "Strong match"
    elif score >= 75:
        status = "Good match"
    elif score < 50:
        status = "Weak match"

    return {
        "score": min(score, 99),
        "status": status,
        "reasons": reasons or ["Relevant source result matched the search inputs"],
        "risks": risks or ["Need manual validation before outreach"],
    }
