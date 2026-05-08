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


def build_tavily_query_variants(query, target_count):
    return [clean_text(query)]
