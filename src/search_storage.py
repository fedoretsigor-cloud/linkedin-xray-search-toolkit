import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def ensure_storage(runs_dir, index_file):
    runs_dir.mkdir(parents=True, exist_ok=True)
    if not index_file.exists():
        index_file.write_text("[]", encoding="utf-8")


def load_run_index(runs_dir, index_file):
    ensure_storage(runs_dir, index_file)
    return json.loads(index_file.read_text(encoding="utf-8"))


def save_run_index(index_file, items):
    index_file.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def get_run_file(runs_dir, run_id):
    return Path(runs_dir) / f"{run_id}.json"


def save_run(runs_dir, index_file, run_record):
    items = load_run_index(runs_dir, index_file)
    summary = {
        "id": run_record["id"],
        "project_id": run_record.get("project_id", ""),
        "created_at": run_record["created_at"],
        "role": run_record["search"]["role"],
        "locations": run_record["search"]["locations"],
        "sources": run_record["search"]["sources"],
        "candidate_count": len(run_record["candidates"]),
        "strong_matches": len([c for c in run_record["candidates"] if c["score"] >= 85]),
    }
    items.insert(0, summary)
    save_run_index(index_file, items)
    get_run_file(runs_dir, run_record["id"]).write_text(
        json.dumps(run_record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_run(runs_dir, run_id):
    run_file = get_run_file(runs_dir, run_id)
    if not run_file.exists():
        return None
    return json.loads(run_file.read_text(encoding="utf-8"))


def ensure_project_storage(projects_dir, project_index_file):
    projects_dir.mkdir(parents=True, exist_ok=True)
    if not project_index_file.exists():
        project_index_file.write_text("[]", encoding="utf-8")


def get_project_file(projects_dir, project_id):
    return Path(projects_dir) / f"{project_id}.json"


def load_project_index(projects_dir, project_index_file):
    ensure_project_storage(projects_dir, project_index_file)
    return json.loads(project_index_file.read_text(encoding="utf-8"))


def save_project_index(project_index_file, items):
    project_index_file.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def load_project(projects_dir, project_id):
    project_file = get_project_file(projects_dir, project_id)
    if not project_file.exists():
        return None
    return json.loads(project_file.read_text(encoding="utf-8"))


def save_project(projects_dir, project_index_file, project):
    ensure_project_storage(projects_dir, project_index_file)
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    get_project_file(projects_dir, project["id"]).write_text(
        json.dumps(project, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    items = load_project_index(projects_dir, project_index_file)
    summary = build_project_summary(project)
    items = [item for item in items if item["id"] != project["id"]]
    items.insert(0, summary)
    save_project_index(project_index_file, items)


def build_project_summary(project):
    return {
        "id": project["id"],
        "created_at": project["created_at"],
        "updated_at": project["updated_at"],
        "role": project.get("confirmed_brief", {}).get("role") or project.get("requirement_brief", {}).get("role") or "Untitled project",
        "requirement_url": project.get("requirement_url", ""),
        "run_count": len(project.get("search_runs", [])),
        "candidate_count": project.get("candidate_count", 0),
    }


def create_or_update_project(projects_dir, project_index_file, run_record):
    project_id = run_record.get("project_id") or uuid.uuid4().hex[:10]
    now = datetime.now(timezone.utc).isoformat()
    project = load_project(projects_dir, project_id) or {
        "id": project_id,
        "created_at": now,
        "search_runs": [],
        "candidate_reviews": [],
        "communication_events": [],
    }

    project["requirement_url"] = run_record.get("requirement_url", "")
    project["requirement_brief"] = run_record.get("requirement_brief")
    project["confirmed_brief"] = run_record.get("confirmed_brief")
    project["search_strategy"] = run_record.get("search_strategy", {})
    project["candidate_count"] = len(run_record.get("candidates", []))

    run_summary = {
        "id": run_record["id"],
        "created_at": run_record["created_at"],
        "candidate_count": len(run_record.get("candidates", [])),
        "queries_count": run_record.get("queries_count", 0),
    }
    project["search_runs"] = [item for item in project.get("search_runs", []) if item["id"] != run_record["id"]]
    project["search_runs"].insert(0, run_summary)

    save_project(projects_dir, project_index_file, project)
    return project
