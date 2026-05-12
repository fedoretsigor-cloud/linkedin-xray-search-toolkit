import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock, Thread

from dotenv import load_dotenv

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from src.search_storage import (
    add_candidate_review,
    add_resume_review,
    create_or_update_project,
    ensure_project_storage,
    ensure_storage,
    load_project,
    load_project_index,
    load_run,
    load_run_index,
    save_run,
)
from src.search_service import run_search
from src.requirement_agent import analyze_requirement_url
from src.profile_review_agent import analyze_profile_text
from src.resume_review_agent import analyze_resume_text
from src.resume_text_extractor import extract_resume_text
from src.web_search import build_run_record, build_web_search_request, hydrate_run_candidate_evidence

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RUNS_DIR = DATA_DIR / "runs"
PROJECTS_DIR = DATA_DIR / "projects"
INDEX_FILE = DATA_DIR / "search_runs.json"
PROJECT_INDEX_FILE = DATA_DIR / "sourcing_projects.json"
DEFAULT_SEARCH_RESULTS = int(os.getenv("SEARCH_RESULTS_PER_QUERY", "20"))
ACCESS_CODE = os.getenv("APP_ACCESS_CODE", "").strip()
SESSION_SECRET = os.getenv("SESSION_SECRET") or os.getenv("SECRET_KEY") or "local-dev-session-secret"


app = Flask(__name__, template_folder="templates", static_folder="static")

app.secret_key = SESSION_SECRET
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "0").lower() in {"1", "true", "yes"}
app.config["PERMANENT_SESSION_LIFETIME"] = int(os.getenv("SESSION_LIFETIME_SECONDS", "43200"))
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

EXEMPT_ENDPOINTS = {"login", "login_submit", "static"}
SEARCH_JOBS = {}
SEARCH_JOBS_LOCK = Lock()
MAX_SEARCH_JOBS = 25


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


def benchmark_provider_lift(run):
    report = run.get("provider_contribution_report") or run.get("search_strategy", {}).get("provider_contribution_report") or {}
    providers = report.get("providers") if isinstance(report, dict) else []
    return [
        {
            "provider": item.get("provider", ""),
            "final_candidates": int(item.get("final_candidates", 0) or 0),
            "accepted_rows": int(item.get("accepted_rows", 0) or 0),
            "executed_calls": int(item.get("executed_calls", 0) or 0),
        }
        for item in providers or []
        if int(item.get("final_candidates", 0) or 0) > 0
    ]


def benchmark_top_query_groups(run, limit=3):
    report = run.get("query_group_contribution_report") or run.get("search_strategy", {}).get("query_group_contribution_report") or {}
    groups = report.get("ranked_groups") if isinstance(report, dict) else []
    if not groups:
        groups = report.get("groups", []) if isinstance(report, dict) else []
    ranked = sorted(
        [item for item in groups or [] if int(item.get("final_candidates", 0) or 0) > 0],
        key=lambda item: int(item.get("final_candidates", 0) or 0),
        reverse=True,
    )
    return [
        {
            "label": item.get("query_group_label") or item.get("skill_input") or item.get("query_group_id", ""),
            "final_candidates": int(item.get("final_candidates", 0) or 0),
            "executed_calls": int(item.get("executed_calls", 0) or 0),
        }
        for item in ranked[:limit]
    ]


def build_benchmark_summary(run):
    search_strategy = run.get("search_strategy", {}) if isinstance(run.get("search_strategy"), dict) else {}
    search = run.get("search", {}) if isinstance(run.get("search"), dict) else {}
    adaptive_waves = search_strategy.get("adaptive_waves", {}) if isinstance(search_strategy.get("adaptive_waves"), dict) else {}
    dynamic_selection = adaptive_waves.get("dynamic_selection", {}) if isinstance(adaptive_waves.get("dynamic_selection"), dict) else {}
    return {
        "id": run.get("id", ""),
        "created_at": run.get("created_at", ""),
        "project_id": run.get("project_id", ""),
        "role": search.get("role") or search_strategy.get("primary_role") or "Untitled search",
        "role_family": search_strategy.get("role_pattern_family", ""),
        "locations": search_strategy.get("locations") or search.get("locations", []),
        "search_depth": search_strategy.get("search_depth") or search.get("search_depth", ""),
        "candidate_count": len(run.get("candidates", []) or []),
        "duration_seconds": float(run.get("duration_seconds", 0) or 0),
        "executed_query_count": int(
            search_strategy.get("executed_search_query_count")
            or search_strategy.get("executed_query_count")
            or run.get("queries_count", 0)
            or 0
        ),
        "planned_query_count": int(search_strategy.get("planned_query_count", 0) or 0),
        "planned_call_cap": int(search_strategy.get("planned_call_cap", 0) or 0),
        "call_cap_applied": bool(search_strategy.get("call_cap_applied")),
        "stop_reason": search_strategy.get("stop_reason", ""),
        "base_query_count": int(search_strategy.get("base_query_count", 0) or 0),
        "completed_wave_count": int(adaptive_waves.get("completed_wave_count", 0) or 0),
        "dynamic_action": dynamic_selection.get("action", ""),
        "provider_lift": benchmark_provider_lift(run),
        "top_query_groups": benchmark_top_query_groups(run),
    }


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def prune_search_jobs_locked():
    if len(SEARCH_JOBS) <= MAX_SEARCH_JOBS:
        return
    ordered = sorted(SEARCH_JOBS.values(), key=lambda item: item.get("created_at", ""))
    for job in ordered[: max(len(SEARCH_JOBS) - MAX_SEARCH_JOBS, 0)]:
        SEARCH_JOBS.pop(job["id"], None)


def update_search_job(job_id, **updates):
    with SEARCH_JOBS_LOCK:
        job = SEARCH_JOBS.get(job_id)
        if not job:
            return
        job.update(updates)
        job["updated_at"] = utc_now_iso()


def public_search_job(job):
    return {
        key: value
        for key, value in job.items()
        if key != "thread"
    }


def progress_payload(current, total, query_info, started_at, row_count):
    query_info = query_info or {}
    total = int(total or 0)
    current = int(current or 0)
    return {
        "current": current,
        "total": total,
        "percent": round((current / total) * 100, 1) if total else 0,
        "provider": query_info.get("provider", ""),
        "query_group_label": query_info.get("query_group_label") or query_info.get("skill_input") or "",
        "wave_type": query_info.get("wave_type", ""),
        "wave_type_label": query_info.get("wave_type_label", ""),
        "adaptive_wave": query_info.get("adaptive_wave", ""),
        "adaptive_wave_label": query_info.get("adaptive_wave_label", ""),
        "candidates_seen": int(row_count or 0),
        "elapsed_seconds": round(time.time() - started_at, 1),
    }


def execute_search_run(search, search_input, progress_callback=None):
    result = run_search(search_input, progress_callback=progress_callback)
    run_record = build_run_record(search, result)
    project = create_or_update_project(PROJECTS_DIR, PROJECT_INDEX_FILE, run_record)
    run_record["project_id"] = project["id"]
    save_run(RUNS_DIR, INDEX_FILE, run_record)
    return run_record


def run_search_job(job_id, search, search_input):
    update_search_job(job_id, status="running", started_at=utc_now_iso())
    try:
        def progress_callback(current, total, query_info, started_at, row_count):
            update_search_job(
                job_id,
                progress=progress_payload(current, total, query_info, started_at, row_count),
            )

        run_record = execute_search_run(search, search_input, progress_callback=progress_callback)
        with SEARCH_JOBS_LOCK:
            latest_progress = dict(SEARCH_JOBS.get(job_id, {}).get("progress", {}))
        update_search_job(
            job_id,
            status="succeeded",
            finished_at=utc_now_iso(),
            run_id=run_record["id"],
            progress={
                **latest_progress,
                "current": int(run_record.get("search_strategy", {}).get("executed_search_query_count") or run_record.get("queries_count") or 0),
                "candidates_seen": len(run_record.get("candidates", []) or []),
                "percent": 100,
            },
        )
    except RuntimeError as exc:
        update_search_job(
            job_id,
            status="failed",
            finished_at=utc_now_iso(),
            error=str(exc),
            error_status=400,
        )
    except Exception as exc:
        update_search_job(
            job_id,
            status="failed",
            finished_at=utc_now_iso(),
            error=f"Search failed: {exc}",
            error_status=500,
        )


@app.get("/api/searches")
def list_searches():
    return jsonify(load_run_index(RUNS_DIR, INDEX_FILE))


@app.get("/api/benchmarks")
def list_benchmarks():
    try:
        limit = min(max(int(request.args.get("limit", "10")), 1), 50)
    except ValueError:
        limit = 10
    summaries = []
    for item in load_run_index(RUNS_DIR, INDEX_FILE):
        run_id = item.get("id")
        if not run_id:
            continue
        run = load_run(RUNS_DIR, run_id)
        if not run:
            continue
        summaries.append(build_benchmark_summary(run))
        if len(summaries) >= limit:
            break
    return jsonify({"runs": summaries})


@app.get("/api/projects")
def list_projects():
    return jsonify(load_project_index(PROJECTS_DIR, PROJECT_INDEX_FILE))


@app.get("/api/projects/<project_id>")
def get_project(project_id):
    project = load_project(PROJECTS_DIR, project_id)
    if not project:
        return jsonify({"error": "Sourcing project not found"}), 404
    return jsonify(project)


@app.get("/api/searches/<run_id>")
def get_search(run_id):
    run = load_run(RUNS_DIR, run_id)
    if not run:
        return jsonify({"error": "Search run not found"}), 404
    return jsonify(hydrate_run_candidate_evidence(run))


@app.post("/api/search")
def create_search():
    payload = request.get_json(force=True)
    try:
        search, search_input = build_web_search_request(payload, DEFAULT_SEARCH_RESULTS)
        run_record = execute_search_run(search, search_input)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Search failed: {exc}"}), 500

    return jsonify(run_record)


@app.post("/api/search-jobs")
def create_search_job():
    payload = request.get_json(force=True)
    try:
        search, search_input = build_web_search_request(payload, DEFAULT_SEARCH_RESULTS)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Search failed: {exc}"}), 500

    job_id = uuid.uuid4().hex[:10]
    job = {
        "id": job_id,
        "status": "queued",
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
        "progress": {
            "current": 0,
            "total": 0,
            "percent": 0,
            "candidates_seen": 0,
        },
    }
    with SEARCH_JOBS_LOCK:
        SEARCH_JOBS[job_id] = job
        prune_search_jobs_locked()

    thread = Thread(target=run_search_job, args=(job_id, search, search_input), daemon=True)
    with SEARCH_JOBS_LOCK:
        if job_id in SEARCH_JOBS:
            SEARCH_JOBS[job_id]["thread"] = thread
    thread.start()
    return jsonify(public_search_job(job)), 202


@app.get("/api/search-jobs/<job_id>")
def get_search_job(job_id):
    with SEARCH_JOBS_LOCK:
        job = SEARCH_JOBS.get(job_id)
        if not job:
            return jsonify({"error": "Search job not found"}), 404
        payload = public_search_job(dict(job))

    if payload.get("status") == "succeeded" and payload.get("run_id"):
        run = load_run(RUNS_DIR, payload["run_id"])
        if run:
            payload["run"] = hydrate_run_candidate_evidence(run)
    return jsonify(payload)


@app.post("/api/requirements/analyze")
def analyze_requirement():
    payload = request.get_json(force=True)
    url = (payload.get("url") or "").strip()
    try:
        result = analyze_requirement_url(url)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Requirement analysis failed: {exc}"}), 400
    return jsonify(result)


@app.post("/api/projects/<project_id>/candidate-reviews")
def create_candidate_review(project_id):
    payload = request.get_json(force=True)
    project = load_project(PROJECTS_DIR, project_id)
    if not project:
        return jsonify({"error": "Sourcing project not found"}), 404

    profile_text = payload.get("profile_text", "")
    candidate = payload.get("candidate", {})
    try:
        analysis = analyze_profile_text(
            confirmed_brief=project.get("confirmed_brief") or {},
            candidate=candidate,
            profile_text=profile_text,
        )
        review = add_candidate_review(
            PROJECTS_DIR,
            PROJECT_INDEX_FILE,
            project_id,
            {
                "project_id": project_id,
                "candidate_id": payload.get("candidate_id", ""),
                "candidate_name": payload.get("candidate_name", ""),
                "candidate_url": payload.get("candidate_url", ""),
                "profile_text": profile_text,
                "analysis": analysis,
            },
        )
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Profile review failed: {exc}"}), 400
    return jsonify(review)


@app.post("/api/projects/<project_id>/resume-reviews")
def create_resume_review(project_id):
    project = load_project(PROJECTS_DIR, project_id)
    if not project:
        return jsonify({"error": "Sourcing project not found"}), 404

    candidate = parse_json_form_field("candidate", {})
    profile_review = parse_json_form_field("profile_review", None)
    candidate_id = request.form.get("candidate_id", "")
    candidate_url = request.form.get("candidate_url", "")
    resume_text = request.form.get("resume_text", "")
    resume_filename = ""

    upload = request.files.get("resume_file")
    try:
        if upload and upload.filename:
            extracted = extract_resume_text(upload)
            resume_text = extracted["text"]
            resume_filename = extracted["filename"]
        if profile_review is None:
            profile_review = find_latest_candidate_review(project, candidate_id, candidate_url)
        analysis = analyze_resume_text(
            confirmed_brief=project.get("confirmed_brief") or {},
            candidate=candidate,
            profile_review=profile_review or {},
            resume_text=resume_text,
        )
        review = add_resume_review(
            PROJECTS_DIR,
            PROJECT_INDEX_FILE,
            project_id,
            {
                "project_id": project_id,
                "candidate_id": candidate_id,
                "candidate_name": request.form.get("candidate_name", ""),
                "candidate_url": candidate_url,
                "resume_filename": resume_filename,
                "resume_text": resume_text,
                "profile_review": profile_review,
                "analysis": analysis,
            },
        )
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Resume review failed: {exc}"}), 400
    return jsonify(review)


def parse_json_form_field(name, default):
    value = request.form.get(name)
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def find_latest_candidate_review(project, candidate_id, candidate_url):
    for review in project.get("candidate_reviews", []):
        if candidate_url and review.get("candidate_url") == candidate_url:
            return review.get("analysis") or review
        if candidate_id and review.get("candidate_id") == candidate_id:
            return review.get("analysis") or review
    return {}


if __name__ == "__main__":
    ensure_storage(RUNS_DIR, INDEX_FILE)
    ensure_project_storage(PROJECTS_DIR, PROJECT_INDEX_FILE)
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes"}
    app.run(debug=debug, host=host, port=port)
