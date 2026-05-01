import argparse
import sys

import requests

from src.search_service import (
    build_search_input_from_args,
    load_config,
    print_console_progress,
    run_search,
    save_csv,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Search profile sources through a search API and save results to CSV."
    )
    parser.add_argument("--title", action="append", default=[], help="Job title")
    parser.add_argument("--skill", action="append", default=[], help="Skill keyword or group")
    parser.add_argument("--location", action="append", default=[], help="Location")
    parser.add_argument("--extra", action="append", default=[], help="Extra keyword")
    parser.add_argument("--with-defaults", action="store_true")
    parser.add_argument("--output", default="output/linkedin_profiles.csv")
    parser.add_argument("--num", type=int, default=None)
    parser.add_argument("--titles-file", default=None)
    parser.add_argument("--skills-file", default=None)
    parser.add_argument("--locations-file", default=None)
    parser.add_argument("--provider", choices=["serpapi", "brave", "tavily"], default=None)
    parser.add_argument(
        "--source-site",
        action="append",
        default=[],
        choices=["linkedin", "facebook", "github", "stackoverflow", "wellfound", "devpost"],
    )
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config()
    search_input = build_search_input_from_args(args)
    search_input["provider"] = args.provider
    search_input["num"] = args.num

    try:
        result = run_search(search_input, progress_callback=print_console_progress, config=config)
    except requests.HTTPError as exc:
        message = exc.response.text if exc.response is not None else str(exc)
        print(f"Provider API error: {message}", file=sys.stderr)
        raise SystemExit(1)
    except requests.RequestException as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        raise SystemExit(1)
    except RuntimeError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        raise SystemExit(1)

    save_csv(result["rows"], args.output)

    print(f"Provider: {result['provider']}")
    print(f"Queries: {len(result['queries'])}")
    print(f"Saved {len(result['rows'])} rows to {args.output}")


if __name__ == "__main__":
    main()
