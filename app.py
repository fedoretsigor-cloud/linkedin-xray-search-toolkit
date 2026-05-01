import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from src.search_service import clean_text, run_search


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RUNS_DIR = DATA_DIR / "runs"
INDEX_FILE = DATA_DIR / "search_runs.json"
DEFAULT_SEARCH_RESULTS = int(os.getenv("SEARCH_RESULTS_PER_QUERY", "20"))

app = Flask(__name__, template_folder="templates", static_folder="static")


def ensure_storage():
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    if not INDEX_FILE.exists():
        INDEX_FILE.write_text("[]", encoding="utf-8")


def load_run_index():
    ensure_storage()
    return json.loads(INDEX_FILE.read_text(encoding="utf-8"))


def save_run_index(items):
    INDEX_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def get_run_file(run_id):
    return RUNS_DIR / f"{run_id}.json"


def save_run(run_record):
    items = load_run_index()
    summary = {
        "id": run_record["id"],
        "created_at": run_record["created_at"],
        "role": run_record["search"]["role"],
        "locations": run_record["search"]["locations"],
        "sources": run_record["search"]["sources"],
        "candidate_count": len(run_record["candidates"]),
        "strong_matches": len([c for c in run_record["candidates"] if c["score"] >= 85]),
    }
    items.insert(0, summary)
    save_run_index(items)
    get_run_file(run_record["id"]).write_text(
        json.dumps(run_record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_run(run_id):
    run_file = get_run_file(run_id)
    if not run_file.exists():
        return None
    return json.loads(run_file.read_text(encoding="utf-8"))


def extract_location_hint(candidate):
    value = clean_text(candidate.get("location") or candidate.get("search_query"))
    return value


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


def transform_candidates(rows, search):
    candidates = []
    for index, row in enumerate(rows, start=1):
        analysis = score_candidate(row, search)
        candidates.append(
            {
                "id": f"cand-{index}",
                "name": clean_text(row.get("profile_name", "")) or "Unknown candidate",
                "role": clean_text(row.get("role", "")),
                "location": clean_text(row.get("location", "")),
                "stack": clean_text(row.get("technology", "")),
                "source": clean_text(row.get("source_site", "")),
                "status": analysis["status"],
                "score": analysis["score"],
                "profile_url": row.get("profile_url", ""),
                "short_description": clean_text(row.get("short_description", "")),
                "is_linkedin_profile": "Yes" if row.get("is_linkedin_profile") else "No",
                "search_query": clean_text(row.get("search_query", "")),
                "analysis": {
                    "summary": (
                        f"{clean_text(row.get('profile_name', 'Unknown'))}, "
                        f"{clean_text(row.get('role', 'profile result'))}, "
                        f"{extract_location_hint(row)}"
                    ),
                    "reasons": analysis["reasons"],
                    "risks": analysis["risks"],
                    "outreach": build_outreach(row, search),
                },
            }
        )
    return sorted(candidates, key=lambda item: item["score"], reverse=True)


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/searches")
def list_searches():
    return jsonify(load_run_index())


@app.get("/api/searches/<run_id>")
def get_search(run_id):
    run = load_run(run_id)
    if not run:
        return jsonify({"error": "Search run not found"}), 404
    return jsonify(run)


@app.post("/api/search")
def create_search():
    payload = request.get_json(force=True)
    requested_num = payload.get("num", DEFAULT_SEARCH_RESULTS)
    try:
        requested_num = int(requested_num)
    except (TypeError, ValueError):
        return jsonify({"error": "Search results limit must be a number"}), 400

    search = {
        "role": clean_text(payload.get("role", "")),
        "titles": [clean_text(value) for value in payload.get("titles", []) if clean_text(value)],
        "tech_groups": [clean_text(value) for value in payload.get("tech_groups", []) if clean_text(value)],
        "locations": [clean_text(value) for value in payload.get("locations", []) if clean_text(value)],
        "sources": payload.get("sources", ["linkedin"]),
        "experience": clean_text(payload.get("experience", "")),
        "availability": clean_text(payload.get("availability", "")),
        "results_limit": requested_num,
    }

    if not search["titles"] and search["role"]:
        search["titles"] = [search["role"]]
    if not search["titles"]:
        return jsonify({"error": "At least one role/title is required"}), 400

    search_input = {
        "titles": search["titles"],
        "skill_groups": [[part.strip() for part in group.split("|") if part.strip()] for group in search["tech_groups"]] or [[]],
        "locations": search["locations"] or [""],
        "extras": [search["availability"]] if search["availability"] else [],
        "source_sites": search["sources"] or ["linkedin"],
        "num": requested_num,
        "provider": None,
    }

    result = run_search(search_input)
    search["stack_summary"] = ", ".join(search["tech_groups"])
    candidates = transform_candidates(result["rows"], search)
    run_record = {
        "id": uuid.uuid4().hex[:10],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "search": search,
        "queries_count": len(result["queries"]),
        "duration_seconds": round(result["duration_seconds"], 2),
        "candidates": candidates,
    }
    save_run(run_record)
    return jsonify(run_record)


if __name__ == "__main__":
    ensure_storage()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes"}
    app.run(debug=debug, host=host, port=port)
