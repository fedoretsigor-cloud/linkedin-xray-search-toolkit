import argparse


def build_or_group(values):
    cleaned = [value.strip() for value in values if value and value.strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return f"\"{cleaned[0]}\""
    joined = " OR ".join(f"\"{value}\"" for value in cleaned)
    return f"({joined})"


def build_query(titles, skills, locations, extras):
    parts = ["site:linkedin.com/in/"]

    title_group = build_or_group(titles)
    skill_group = build_or_group(skills)
    location_group = build_or_group(locations)

    for group in (title_group, skill_group, location_group):
        if group:
            parts.append(group)

    for extra in extras:
        extra = extra.strip()
        if extra:
            parts.append(f"\"{extra}\"")

    return " ".join(parts)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate LinkedIn X-Ray search queries for Google."
    )
    parser.add_argument("--title", action="append", default=[], help="Job title")
    parser.add_argument("--skill", action="append", default=[], help="Skill keyword")
    parser.add_argument("--location", action="append", default=[], help="Location")
    parser.add_argument("--extra", action="append", default=[], help="Extra keyword")
    parser.add_argument(
        "--with-defaults",
        action="store_true",
        help="Add common IT title synonyms automatically",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    titles = list(args.title)
    if args.with_defaults:
        defaults = ["software engineer", "developer", "programmer"]
        for item in defaults:
            if item not in titles:
                titles.append(item)

    query = build_query(
        titles=titles,
        skills=args.skill,
        locations=args.location,
        extras=args.extra,
    )
    print(query)


if __name__ == "__main__":
    main()
