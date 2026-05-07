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
import sys
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, abort, render_template

ROOT = Path(__file__).parent.resolve()
if len(sys.argv) > 1:
    DATA_ROOT = (ROOT / sys.argv[1]).resolve()
elif (ROOT / "datasets").is_dir():
    DATA_ROOT = (ROOT / "datasets").resolve()
else:
    DATA_ROOT = ROOT

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


@app.route("/api/projects/<name>/tasks/<int:idx>", methods=["POST"])
def api_save(name: str, idx: int):
    project = get_project(name)
    tasks = load_tasks(project)
    if idx < 0 or idx >= len(tasks):
        abort(404)
    payload = request.get_json(force=True) or {}
    text = (payload.get("text") or "").strip()
    status = payload.get("status") or ("done" if text else "pending")

    audio = task_audio(tasks[idx])
    annos = load_annotations(project)
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
