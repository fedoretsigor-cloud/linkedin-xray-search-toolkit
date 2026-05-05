def _clean_text(value):
    if not value:
        return ""
    return (
        str(value)
        .replace("ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ", "-")
        .replace("ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“", "-")
        .replace("ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\xa0", " ")
        .strip()
    )


def extract_location_hint(candidate):
    return _clean_text(candidate.get("location") or candidate.get("search_query"))


def build_outreach(candidate, search):
    first_name = _clean_text(candidate.get("profile_name", "")).split(" ")[0] or "there"
    role = search["role"] or "this role"
    stack = search["stack_summary"] or "the requested stack"
    location = ", ".join(search["locations"]) or "the target market"
    return (
        f"Hi {first_name}, I found your profile while searching for {role} talent in {location}. "
        f"Your background looks relevant for {stack}, and I would love to share a role that may fit. "
        f"If you are open to hearing about opportunities, I can send more details."
    )


def build_candidate_analysis(candidate, search, scoring):
    return {
        "summary": (
            f"{_clean_text(candidate.get('profile_name', 'Unknown'))}, "
            f"{_clean_text(candidate.get('role', 'profile result'))}, "
            f"{extract_location_hint(candidate)}"
        ),
        "reasons": scoring["reasons"],
        "risks": scoring["risks"],
        "outreach": build_outreach(candidate, search),
    }
