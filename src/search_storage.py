import json
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
