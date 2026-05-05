from src.text_utils import clean_text


def extract_location_hint(candidate):
    return clean_text(candidate.get("location") or candidate.get("search_query"))


def build_outreach(candidate, search):
    first_name = clean_text(candidate.get("profile_name", "")).split(" ")[0] or "there"
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
            f"{clean_text(candidate.get('profile_name', 'Unknown'))}, "
            f"{clean_text(candidate.get('role', 'profile result'))}, "
            f"{extract_location_hint(candidate)}"
        ),
        "reasons": scoring["reasons"],
        "risks": scoring["risks"],
        "outreach": build_outreach(candidate, search),
    }
