from src.text_utils import clean_text


def extract_location_hint(candidate):
    return clean_text(candidate.get("location") or candidate.get("search_query"))


def build_outreach(candidate, search):
    first_name = clean_text(candidate.get("profile_name", "")).split(" ")[0] or "there"
    role = search["role"] or "this role"
    stack = search["stack_summary"] or "the requested stack"
    location = ", ".join(search["locations"]) or "the target market"
    project_title = clean_text(candidate.get("project_title", ""))
    if candidate.get("source_site") == "devpost" and project_title:
        return (
            f"Hi {first_name}, I found your Devpost project {project_title} while searching for "
            f"{role} talent in {location}. The project looks relevant for {stack}, and I would "
            f"love to share a role that may fit. If you are open to hearing about opportunities, "
            f"I can send more details."
        )
    return (
        f"Hi {first_name}, I found your profile while searching for {role} talent in {location}. "
        f"Your background looks relevant for {stack}, and I would love to share a role that may fit. "
        f"If you are open to hearing about opportunities, I can send more details."
    )


def build_candidate_analysis(candidate, search, scoring):
    project_title = clean_text(candidate.get("project_title", ""))
    if candidate.get("source_site") == "devpost" and project_title:
        summary = (
            f"{clean_text(candidate.get('profile_name', 'Unknown'))}, "
            f"maker on Devpost project {project_title}, "
            f"{extract_location_hint(candidate)}"
        )
    else:
        role = clean_text(candidate.get("display_role") or candidate.get("role") or "profile result")
        summary = (
            f"{clean_text(candidate.get('profile_name', 'Unknown'))}, "
            f"{role}, "
            f"{extract_location_hint(candidate)}"
        )
    return {
        "summary": summary,
        "reasons": scoring["reasons"],
        "risks": scoring["risks"],
        "outreach": build_outreach(candidate, search),
    }
