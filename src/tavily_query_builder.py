def clean_text(value):
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


def tavily_query_count_for_target_count(target_count):
    try:
        target_count = int(target_count)
    except (TypeError, ValueError):
        target_count = 20

    if target_count <= 20:
        return 1
    if target_count <= 40:
        return 2
    if target_count <= 60:
        return 3
    if target_count <= 100:
        return 5
    return 10


def build_tavily_query_variants(query, target_count):
    normalized_query = clean_text(query)
    variants = [normalized_query]
    boosters = [
        '"profile"',
        '"resume"',
        '"cv"',
        '"open to work"',
        '"engineer"',
        '"developer"',
        '"software engineer"',
        '"backend"',
        '"frontend"',
        '"remote"',
        '"candidate"',
        '"talent"',
    ]
    needed_queries = tavily_query_count_for_target_count(target_count)
    for booster in boosters:
        if len(variants) >= needed_queries:
            break
        variants.append(f"{normalized_query} {booster}".strip())
    return variants[:needed_queries]
