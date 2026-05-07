import os
from pathlib import Path

from dotenv import load_dotenv

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from src.search_storage import ensure_storage, load_run, load_run_index, save_run
from src.search_service import run_search
from src.requirement_agent import analyze_requirement_url
from src.web_search import build_run_record, build_web_search_request

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
    return jsonify(load_run_index(RUNS_DIR, INDEX_FILE))


@app.get("/api/searches/<run_id>")
def get_search(run_id):
    run = load_run(RUNS_DIR, run_id)
    if not run:
        return jsonify({"error": "Search run not found"}), 404
    return jsonify(run)


@app.post("/api/search")
def create_search():
    payload = request.get_json(force=True)
    try:
        search, search_input = build_web_search_request(payload, DEFAULT_SEARCH_RESULTS)
        result = run_search(search_input)
    except RuntimeError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": f"Search failed: {exc}"}), 500

    run_record = build_run_record(search, result)
    save_run(RUNS_DIR, INDEX_FILE, run_record)
    return jsonify(run_record)


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


if __name__ == "__main__":
    ensure_storage(RUNS_DIR, INDEX_FILE)
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes"}
    app.run(debug=debug, host=host, port=port)
