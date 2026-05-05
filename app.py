import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from flask import Flask, jsonify, redirect, render_template, request, session, url_for


from src.scoring import score_candidate
from src.search_service import clean_text, run_search

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RUNS_DIR = DATA_DIR / "runs"
INDEX_FILE = DATA_DIR / "search_runs.json"
DEFAULT_SEARCH_RESULTS = int(os.getenv("SEARCH_RESULTS_PER_QUERY", "20"))
ACCESS_CODE = os.getenv("APP_ACCESS_CODE", "").strip()
SESSION_SECRET = os.getenv("SESSION_SECRET") or os.getenv("SECRET_KEY") or "local-dev-session-secret"


app = Flask(__name__, template_folder="templates", static_folder="static")

app.secret_key = SESSION_SECRET
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "0").lower() in {"1", "true", "yes"}
app.config["PERMANENT_SESSION_LIFETIME"] = int(os.getenv("SESSION_LIFETIME_SECONDS", "43200"))

EXEMPT_ENDPOINTS = {"login", "login_submit", "static"}


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


def contains_cyrillic(values):
    import re

    pattern = re.compile(r"[\u0400-\u04FF]")
    for value in values:
        if value and pattern.search(str(value)):
            return True
    return False



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

def auth_enabled():
    return bool(ACCESS_CODE)


def is_authenticated():
    return session.get("is_authenticated") is True


@app.before_request
def require_access_code():
    if not auth_enabled():
        return None
    if request.endpoint in EXEMPT_ENDPOINTS:
        return None
    if is_authenticated():
        return None
    if request.path.startswith("/api/"):
        return jsonify({"error": "Authentication required", "login_url": url_for("login")}), 401
    next_path = request.full_path if request.query_string else request.path
    return redirect(url_for("login", next=next_path))


@app.get("/login")
def login():
    next_path = request.args.get("next", "/")
    error = request.args.get("error")
    return render_template(
        "login.html",
        next_path=next_path if next_path.startswith("/") else "/",
        error=error,
        access_configured=auth_enabled(),
    )


@app.post("/login")
def login_submit():
    next_path = request.form.get("next", "/")
    entered_code = request.form.get("access_code", "").strip()

    if not auth_enabled():
        return render_template(
            "login.html",
            next_path="/",
            error="Access code is not configured yet. Add APP_ACCESS_CODE in environment variables.",
            access_configured=False,
        ), 503

    if entered_code != ACCESS_CODE:
        return render_template(
            "login.html",
            next_path=next_path if next_path.startswith("/") else "/",
            error="Invalid access code. Please try again.",
            access_configured=True,
        ), 401

    session.permanent = False
    session["is_authenticated"] = True
    safe_next = next_path if next_path.startswith("/") else "/"
    response = redirect(safe_next)
    response.set_cookie(
        "engineer_search_tab_access",
        "1",
        max_age=30,
        httponly=False,
        samesite="Lax",
        secure=app.config["SESSION_COOKIE_SECURE"],
    )
    return response


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



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

    validation_values = [
        search["role"],
        *search["titles"],
        *search["tech_groups"],
        *search["locations"],
        search["experience"],
        search["availability"],
    ]

    if contains_cyrillic(validation_values):
        return jsonify({"error": "Please use English only."}), 400

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

    try:
        result = run_search(search_input)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 400

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
