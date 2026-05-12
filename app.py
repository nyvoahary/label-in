"""Local Label-Studio-style audio transcription app.

Each subfolder of the root that contains a `*.label_studio.json` is treated
as its own project, with its own `annotations.json`.

Run:
    pip install flask
    python app.py [root_folder]

Defaults to the directory containing this file. Open http://127.0.0.1:5000
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory, abort, render_template

ROOT = Path(__file__).parent.resolve()
if len(sys.argv) > 1:
    DATA_ROOT = (ROOT / sys.argv[1]).resolve()
elif (ROOT / "datasets").is_dir():
    DATA_ROOT = (ROOT / "datasets").resolve()
else:
    DATA_ROOT = ROOT

BACKUP_ROOT = Path(os.environ["BACKUP_ROOT"]) if "BACKUP_ROOT" in os.environ else None

if not DATA_ROOT.exists():
    raise SystemExit(f"Root folder not found: {DATA_ROOT}")

app = Flask(__name__, template_folder=str(ROOT / "templates"))


def discover_projects() -> list[dict]:
    """Find every subfolder of DATA_ROOT that contains a *.label_studio.json."""
    projects = []
    for sub in sorted(p for p in DATA_ROOT.iterdir() if p.is_dir()):
        ls = next(sub.glob("*.label_studio.json"), None)
        if ls is None:
            # fall back to any .json so users with other names still work
            others = [p for p in sub.glob("*.json") if p.name != "annotations.json"]
            if not others:
                continue
            ls = others[0]
        projects.append({
            "name": sub.name,
            "dir": sub,
            "tasks_file": ls,
            "annotations_file": sub / "annotations.json",
        })
    return projects


def get_project(name: str) -> dict:
    for p in discover_projects():
        if p["name"] == name:
            return p
    abort(404, f"Project not found: {name}")


def load_tasks(project: dict) -> list[dict]:
    with project["tasks_file"].open("r", encoding="utf-8") as f:
        return json.load(f)


def load_annotations(project: dict) -> dict[str, dict]:
    path = project["annotations_file"]
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_annotations(project: dict, data: dict[str, dict]) -> None:
    path = project["annotations_file"]
    tmp = path.with_suffix(".json.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def task_audio(task: dict) -> str:
    return task.get("data", {}).get("audio", "")


def all_predictions(task: dict) -> list[dict]:
    """Return [{model, score, text}, ...] for every prediction in the task."""
    preds = task.get("predictions") or []
    out = []
    for p in preds:
        model = p.get("model_version") or "unknown"
        score = p.get("score")
        text = ""
        for r in (p.get("result") or []):
            texts = (r.get("value") or {}).get("text") or []
            if texts:
                text = texts[0]
                break
        if text:
            out.append({"model": model, "score": score, "text": text})
    if not out:
        fallback = task.get("data", {}).get("text", "") or ""
        if fallback:
            out.append({"model": "default", "score": None, "text": fallback})
    return out


@app.route("/")
def index():
    return render_template("dashboard.html", root=DATA_ROOT.name)


@app.route("/projects")
def labeling():
    return render_template("index.html", root=DATA_ROOT.name)


@app.route("/api/projects")
def api_projects():
    out = []
    for p in discover_projects():
        tasks = load_tasks(p)
        annos = load_annotations(p)
        done = sum(1 for a in annos.values() if a.get("status") == "done")
        review = sum(1 for a in annos.values() if a.get("status") in ("review", "autosave"))
        out.append({
            "name": p["name"],
            "total": len(tasks),
            "done": done,
            "review": review,
            "tasks_file": p["tasks_file"].name,
        })
    return jsonify({"projects": out, "root": str(DATA_ROOT)})


@app.route("/api/projects/<name>/tasks")
def api_tasks(name: str):
    project = get_project(name)
    tasks = load_tasks(project)
    annos = load_annotations(project)
    out = []
    for i, t in enumerate(tasks):
        d = t.get("data", {})
        audio = d.get("audio", "")
        anno = annos.get(audio)
        preds = all_predictions(t)
        out.append({
            "index": i,
            "audio": audio,
            "start": d.get("start"),
            "end": d.get("end"),
            "duration": (d.get("end") or 0) - (d.get("start") or 0),
            "predictions": preds,
            "prediction": preds[0]["text"] if preds else "",  # sidebar preview
            "confidence": d.get("confidence"),
            "annotation": (anno or {}).get("text", ""),
            "status": (anno or {}).get("status", "pending"),
            "updated_at": (anno or {}).get("updated_at"),
        })
    return jsonify({"project": name, "tasks": out, "count": len(out)})


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", root=DATA_ROOT.name)


@app.route("/api/dashboard")
def api_dashboard():
    projects = []
    total_tasks = 0
    total_done = 0
    total_pending = 0
    total_review = 0
    total_autosave = 0
    for p in discover_projects():
        tasks = load_tasks(p)
        annos = load_annotations(p)
        done = sum(1 for a in annos.values() if a.get("status") == "done")
        review = sum(1 for a in annos.values() if a.get("status") == "review")
        autosave = sum(1 for a in annos.values() if a.get("status") == "autosave")
        pending = len(tasks) - done - review - autosave
        total_tasks += len(tasks)
        total_done += done
        total_review += review
        total_autosave += autosave
        total_pending += pending
        completion = (done / len(tasks) * 100) if tasks else 0
        projects.append({
            "name": p["name"],
            "total": len(tasks),
            "done": done,
            "pending": pending,
            "review": review,
            "autosave": autosave,
            "completion": round(completion, 1),
        })
    overall_completion = (total_done / total_tasks * 100) if total_tasks else 0
    return jsonify({
        "overall": {
            "projects": len(projects),
            "tasks": total_tasks,
            "done": total_done,
            "pending": total_pending,
            "review": total_review,
            "autosave": total_autosave,
            "completion": round(overall_completion, 1),
        },
        "projects": projects,
    })


@app.route("/api/projects/<name>/tasks/<int:idx>", methods=["POST"])
def api_save(name: str, idx: int):
    project = get_project(name)
    tasks = load_tasks(project)
    if idx < 0 or idx >= len(tasks):
        abort(404)
    payload = request.get_json(force=True) or {}
    text = (payload.get("text") or "").strip()
    status = payload.get("status")
    if status not in ("done", "pending", "review", "autosave"):
        status = "done" if text else "pending"

    audio = task_audio(tasks[idx])
    annos = load_annotations(project)

    existing = annos.get(audio, {})
    if status == "autosave" and existing.get("status") in ("done", "review"):
        status = existing["status"]

    annos[audio] = {
        "index": idx,
        "audio": audio,
        "text": text,
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    save_annotations(project, annos)
    return jsonify({"ok": True, "annotation": annos[audio]})


@app.route("/api/projects/<name>/export")
def api_export(name: str):
    project = get_project(name)
    tasks = load_tasks(project)
    annos = load_annotations(project)
    now = datetime.now(timezone.utc).isoformat()
    out = []
    for t in tasks:
        audio = task_audio(t)
        anno = annos.get(audio)
        merged = json.loads(json.dumps(t))
        if anno and anno.get("text"):
            merged["annotations"] = [{
                "created_at": anno.get("updated_at", now),
                "result": [{
                    "from_name": "transcription",
                    "to_name": "audio",
                    "type": "textarea",
                    "value": {"text": [anno["text"]]},
                }],
            }]
        out.append(merged)
    return jsonify(out)


@app.route("/api/projects/<name>/backup", methods=["POST"])
def api_backup(name: str):
    project = get_project(name)
    src = project["annotations_file"]
    if not src.exists():
        return jsonify({"error": "No annotations file found"}), 404
    if BACKUP_ROOT is None:
        return jsonify({"error": "BACKUP_ROOT not configured"}), 503
    if not BACKUP_ROOT.exists():
        return jsonify({"error": "Backup destination not accessible"}), 503
    dest_dir = BACKUP_ROOT / name
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "annotations.json"
    with open(src, "rb") as fsrc, open(dest, "wb") as fdst:
        shutil.copyfileobj(fsrc, fdst)
    return jsonify({"ok": True, "dest": str(dest)})


def _merge_annotations(local: dict, remote: dict) -> tuple[dict, int, int]:
    """Merge two annotation dicts. Per-task: prefer the one with newer updated_at.
    Returns (merged, pulled_count, kept_count)."""
    merged = dict(local)
    pulled = 0
    kept = 0
    for key, remote_task in remote.items():
        local_task = local.get(key)
        if local_task is None:
            # task only exists on remote
            merged[key] = remote_task
            pulled += 1
        else:
            remote_ts = remote_task.get("updated_at", "")
            local_ts = local_task.get("updated_at", "")
            if remote_ts > local_ts:
                merged[key] = remote_task
                pulled += 1
            else:
                kept += 1
    return merged, pulled, kept


@app.route("/api/projects/<name>/sync", methods=["POST"])
def api_sync(name: str):
    project = get_project(name)
    local_path = project["annotations_file"]
    if BACKUP_ROOT is None:
        return jsonify({"error": "BACKUP_ROOT not configured"}), 503
    if not BACKUP_ROOT.exists():
        return jsonify({"error": "NAS not accessible"}), 503
    nas_path = BACKUP_ROOT / name / "annotations.json"
    if not nas_path.exists():
        return jsonify({"error": "No backup found on NAS for this project"}), 404

    local = json.loads(local_path.read_text()) if local_path.exists() else {}
    remote = json.loads(nas_path.read_text())

    merged, pulled, kept = _merge_annotations(local, remote)

    if pulled == 0:
        return jsonify({"action": "skipped", "reason": "local_up_to_date", "pulled": 0, "kept": kept})

    # safety backup before overwriting
    if local_path.exists():
        with open(local_path, "rb") as fsrc, open(str(local_path) + ".bak", "wb") as fdst:
            shutil.copyfileobj(fsrc, fdst)

    local_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2))
    return jsonify({"action": "merged", "pulled": pulled, "kept": kept})


@app.route("/api/sync-status")
def api_sync_status():
    if BACKUP_ROOT is None or not BACKUP_ROOT.exists():
        return jsonify({"nas_accessible": False, "projects": {}})
    out = {}
    for p in discover_projects():
        name = p["name"]
        nas_dir = BACKUP_ROOT / name
        if not nas_dir.is_dir() or not (nas_dir / "annotations.json").exists():
            out[name] = {"on_nas": False}
            continue
        nas_path = nas_dir / "annotations.json"
        local = json.loads(p["annotations_file"].read_text()) if p["annotations_file"].exists() else {}
        remote = json.loads(nas_path.read_text())
        local_max = max((v.get("updated_at", "") for v in local.values()), default="")
        remote_max = max((v.get("updated_at", "") for v in remote.values()), default="")
        out[name] = {
            "on_nas": True,
            "local_ahead": local_max > remote_max,
            "nas_ahead": remote_max > local_max,
            "in_sync": local_max == remote_max and bool(local_max),
        }
    return jsonify({"nas_accessible": True, "projects": out})


@app.route("/api/nas/projects")
def api_nas_projects():
    if BACKUP_ROOT is None:
        return jsonify({"error": "BACKUP_ROOT not configured"}), 503
    if not BACKUP_ROOT.exists():
        return jsonify({"error": "NAS not accessible"}), 503
    local_names = {p["name"] for p in discover_projects()}
    out = []
    for sub in sorted(p for p in BACKUP_ROOT.iterdir() if p.is_dir()):
        ls = next(sub.glob("*.label_studio.json"), None)
        if ls is None:
            others = [p for p in sub.glob("*.json") if p.name != "annotations.json"]
            if not others:
                continue
        out.append({"name": sub.name, "exists_locally": sub.name in local_names})
    return jsonify({"projects": out})


@app.route("/api/nas/projects/<name>/pull", methods=["POST"])
def api_nas_pull(name: str):
    if BACKUP_ROOT is None:
        return jsonify({"error": "BACKUP_ROOT not configured"}), 503
    if not BACKUP_ROOT.exists():
        return jsonify({"error": "NAS not accessible"}), 503
    src = BACKUP_ROOT / name
    if not src.is_dir():
        return jsonify({"error": "Project not found on NAS"}), 404
    dest = DATA_ROOT / name
    if dest.exists():
        return jsonify({"error": "Project already exists locally"}), 409
    shutil.copytree(src, dest)
    return jsonify({"ok": True, "name": name, "dest": str(dest)})


@app.route("/api/nas/projects/<name>/pull-stream")
def api_nas_pull_stream(name: str):
    if BACKUP_ROOT is None or not BACKUP_ROOT.exists():
        return jsonify({"error": "NAS not accessible"}), 503
    src = BACKUP_ROOT / name
    if not src.is_dir():
        return jsonify({"error": "Project not found on NAS"}), 404
    dest = DATA_ROOT / name
    if dest.exists():
        return jsonify({"error": "Project already exists locally"}), 409

    def sse(obj: dict) -> str:
        return f"data: {json.dumps(obj)}\n\n"

    def generate():
        try:
            files: list[tuple[Path, int]] = []
            total_bytes = 0
            for root, _, names in os.walk(src):
                for n in names:
                    fp = Path(root) / n
                    sz = fp.stat().st_size
                    files.append((fp, sz))
                    total_bytes += sz
            yield sse({"type": "start", "files": len(files), "bytes": total_bytes})

            dest.mkdir(parents=True, exist_ok=False)
            copied_bytes = 0
            CHUNK = 1024 * 1024
            for fp, _ in files:
                rel = fp.relative_to(src)
                dst = dest / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                with open(fp, "rb") as fsrc, open(dst, "wb") as fdst:
                    while True:
                        buf = fsrc.read(CHUNK)
                        if not buf:
                            break
                        fdst.write(buf)
                        copied_bytes += len(buf)
                        yield sse({
                            "type": "progress",
                            "copied": copied_bytes,
                            "total": total_bytes,
                            "file": str(rel),
                        })
            yield sse({"type": "done"})
        except Exception as e:
            if dest.exists():
                shutil.rmtree(dest, ignore_errors=True)
            yield sse({"type": "error", "error": str(e)})

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/audio/<name>/<path:filename>")
def serve_audio(name: str, filename: str):
    project = get_project(name)
    return send_from_directory(str(project["dir"]), filename)


if __name__ == "__main__":
    print(f"Root:        {DATA_ROOT}")
    projects = discover_projects()
    print(f"Projects:    {len(projects)}")
    for p in projects:
        print(f"  - {p['name']}  ({p['tasks_file'].name})")
    if not projects:
        print("  (none found — each project must be a subfolder containing a *.label_studio.json)")
    app.run(host="127.0.0.1", port=5000, debug=False)
