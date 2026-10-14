
"""Local Label-Studio-style audio transcription app.

Each subfolder of the root that contains a `*.label_studio.json` is treated
as its own project, with its own `annotations.json`.

Run:
    pip install flask
    python app.py [root_folder]

Defaults to the directory containing this file. Open http://127.0.0.1:5000
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_file, send_from_directory, abort, render_template
from werkzeug.security import check_password_hash

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


# --- Login -----------------------------------------------------------------------
# HTTP Basic auth against AUTH_FILE ({"username": "<werkzeug password hash>"}),
# managed with manage_users.py. With no users the app stays open (local use).

AUTH_FILE = Path(os.environ.get("AUTH_FILE", DATA_ROOT / "users.json"))
_auth_cache: dict = {"mtime": None, "users": {}, "verified": set()}


def _auth_users() -> dict[str, str]:
    try:
        mtime = AUTH_FILE.stat().st_mtime
    except FileNotFoundError:
        return {}
    if mtime != _auth_cache["mtime"]:
        _auth_cache.update(mtime=mtime, users=json.loads(AUTH_FILE.read_text("utf-8")), verified=set())
    return _auth_cache["users"]


@app.before_request
def require_login():
    users = _auth_users()
    if not users:
        return None
    auth = request.authorization
    if auth and auth.type == "basic" and auth.username in users:
        # Password hashing is deliberately slow; remember credentials already checked.
        key = (auth.username, hashlib.sha256((auth.password or "").encode()).hexdigest())
        if key in _auth_cache["verified"]:
            return None
        if check_password_hash(users[auth.username], auth.password or ""):
            _auth_cache["verified"].add(key)
            return None
    return Response("Login required", 401, {"WWW-Authenticate": 'Basic realm="label-in"'})


def discover_projects() -> list[dict]:
    """Find every subfolder of DATA_ROOT that contains a *.label_studio.json."""
    projects = []
    # Hidden folders (e.g. .uploads staging) are never projects.
    for sub in sorted(p for p in DATA_ROOT.iterdir() if p.is_dir() and not p.name.startswith(".")):
        ls = find_tasks_file(sub)
        if ls is None:
            continue
        projects.append({
            "name": sub.name,
            "dir": sub,
            "tasks_file": ls,
            "annotations_file": sub / "annotations.json",
        })
    return projects


def find_tasks_file(folder: Path) -> Path | None:
    ls = next(folder.glob("*.label_studio.json"), None)
    if ls is None:
        # fall back to any .json so users with other names still work
        others = sorted(p for p in folder.glob("*.json") if p.name not in ("annotations.json", "learned_words.json"))
        ls = others[0] if others else None
    return ls


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
        return jsonify({"nas_configured": BACKUP_ROOT is not None, "nas_accessible": False, "projects": {}})
    out = {}
    for p in discover_projects():
        name = p["name"]
        nas_dir = BACKUP_ROOT / name
        if not nas_dir.is_dir() or not (nas_dir / "annotations.json").exists():
            local = json.loads(p["annotations_file"].read_text()) if p["annotations_file"].exists() else {}
            out[name] = {
                "on_nas": False,
                "local_ahead": bool(local),
                "nas_ahead": False,
                "in_sync": False,
            }
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
    return jsonify({"nas_configured": True, "nas_accessible": True, "projects": out})


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


# --- Upload a project folder from the browser ---------------------------------
# Files are sent one per request into DATA_ROOT/.uploads/<name>/, then "finish"
# validates the folder and moves it into place (or merges into an existing project).

UPLOADS_DIR = DATA_ROOT / ".uploads"
PROJECT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.\-]{0,99}$")
UPLOAD_EXTS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".json"}


def _staging_dir(name: str) -> Path:
    if not PROJECT_NAME_RE.match(name):
        abort(400, f"Invalid project name: {name}")
    return UPLOADS_DIR / name


def _check_upload_filename(filename: str) -> None:
    if (Path(filename).name != filename or filename.startswith(".")
            or Path(filename).suffix.lower() not in UPLOAD_EXTS):
        abort(400, f"File not allowed: {filename}")


def _missing_audio(tasks_file: Path, *folders: Path) -> list[str]:
    with tasks_file.open("r", encoding="utf-8") as f:
        tasks = json.load(f)
    wanted = {task_audio(t) for t in tasks if task_audio(t)}
    return sorted(a for a in wanted if not any((d / a).is_file() for d in folders))


@app.route("/api/uploads/<name>")
def api_upload_status(name: str):
    """Files already staged for this upload, so an interrupted upload can resume."""
    staging = _staging_dir(name)
    files = {p.name: p.stat().st_size for p in staging.iterdir() if p.is_file()} if staging.is_dir() else {}
    return jsonify({"files": files, "exists": (DATA_ROOT / name).exists()})


@app.route("/api/uploads/<name>/files/<filename>", methods=["PUT"])
def api_upload_file(name: str, filename: str):
    staging = _staging_dir(name)
    _check_upload_filename(filename)
    staging.mkdir(parents=True, exist_ok=True)
    dest = staging / filename
    tmp = staging / f".{filename}.part"
    with tmp.open("wb") as f:
        shutil.copyfileobj(request.stream, f, 1024 * 1024)
    tmp.replace(dest)
    return jsonify({"ok": True, "size": dest.stat().st_size})


@app.route("/api/uploads/<name>", methods=["DELETE"])
def api_upload_cancel(name: str):
    shutil.rmtree(_staging_dir(name), ignore_errors=True)
    return jsonify({"ok": True})


@app.route("/api/uploads/<name>/finish", methods=["POST"])
def api_upload_finish(name: str):
    staging = _staging_dir(name)
    if not staging.is_dir():
        return jsonify({"error": "Nothing uploaded for this project"}), 404
    mode = (request.json or {}).get("mode", "new")
    target = DATA_ROOT / name

    if mode == "new":
        if target.exists():
            return jsonify({"error": f"Project '{name}' already exists", "exists": True}), 409
        tasks_file = find_tasks_file(staging)
        if tasks_file is None:
            return jsonify({"error": "No *.label_studio.json in the uploaded folder"}), 400
        missing = _missing_audio(tasks_file, staging)
        if missing:
            return jsonify({"error": f"{len(missing)} audio file(s) missing", "missing": missing[:50]}), 400
        for leftover in staging.glob(".*.part"):
            leftover.unlink()
        staging.replace(target)
        seed_learned_words()
        return jsonify({"action": "created", "name": name})

    if mode != "merge":
        return jsonify({"error": f"Unknown mode: {mode}"}), 400
    if not target.is_dir():
        return jsonify({"error": f"Project '{name}' does not exist"}), 404

    # The server's tasks file is kept; the uploaded one is only used if the server has none.
    tasks_file = find_tasks_file(target) or find_tasks_file(staging)
    if tasks_file is None:
        return jsonify({"error": "No *.label_studio.json on the server or in the upload"}), 400
    missing = _missing_audio(tasks_file, target, staging)
    if missing:
        return jsonify({"error": f"{len(missing)} audio file(s) missing", "missing": missing[:50]}), 400

    added_files = 0
    for src in staging.iterdir():
        if not src.is_file() or src.name.startswith(".") or src.name == "annotations.json":
            continue
        dst = target / src.name
        if not dst.exists():
            shutil.move(str(src), dst)
            added_files += 1

    pulled = kept = 0
    uploaded_ann = staging / "annotations.json"
    if uploaded_ann.exists():
        project = get_project(name)
        local = load_annotations(project)
        merged, pulled, kept = _merge_annotations(local, json.loads(uploaded_ann.read_text("utf-8")))
        if pulled:
            if project["annotations_file"].exists():
                shutil.copyfile(project["annotations_file"], str(project["annotations_file"]) + ".bak")
            save_annotations(project, merged)

    shutil.rmtree(staging, ignore_errors=True)
    if pulled:
        seed_learned_words()
    return jsonify({"action": "merged", "name": name, "added_files": added_files,
                    "annotations_updated": pulled, "annotations_kept": kept})


# --- Download a project as a zip -----------------------------------------------

@app.route("/api/projects/<name>/download")
def api_download(name: str):
    """?audio=1 → full project folder; otherwise annotations + tasks file only."""
    project = get_project(name)
    full = request.args.get("audio") == "1"
    if full:
        files = sorted(p for p in project["dir"].iterdir()
                       if p.is_file() and not p.name.endswith((".tmp", ".part")))
    else:
        files = [p for p in (project["tasks_file"], project["annotations_file"]) if p.exists()]
    buf = tempfile.TemporaryFile()
    with zipfile.ZipFile(buf, "w") as zf:
        for p in files:
            # Audio is already compressed or not worth the CPU; only deflate JSON.
            method = zipfile.ZIP_DEFLATED if p.suffix == ".json" else zipfile.ZIP_STORED
            zf.write(p, f"{name}/{p.name}", compress_type=method)
    buf.seek(0)
    suffix = "" if full else "_annotations"
    return send_file(buf, mimetype="application/zip", as_attachment=True,
                     download_name=f"{name}{suffix}.zip")


# Override with LEARNED_WORDS_FILE to keep the list on persistent storage (e.g. in Docker).
LEARNED_WORDS_FILE = Path(os.environ.get("LEARNED_WORDS_FILE", ROOT / "static" / "learned_words.json"))

@app.route("/api/learned-words", methods=["GET"])
def get_learned_words():
    if LEARNED_WORDS_FILE.exists():
        return jsonify(json.loads(LEARNED_WORDS_FILE.read_text("utf-8")))
    return jsonify([])

@app.route("/api/learned-words", methods=["POST"])
def add_learned_words():
    new_words = request.json.get("words", [])
    if not new_words:
        return jsonify({"added": 0})
    existing = set(json.loads(LEARNED_WORDS_FILE.read_text("utf-8")) if LEARNED_WORDS_FILE.exists() else [])
    added = [w for w in new_words if w not in existing]
    if added:
        existing.update(added)
        LEARNED_WORDS_FILE.write_text(json.dumps(sorted(existing), ensure_ascii=False), "utf-8")
    return jsonify({"added": len(added), "total": len(existing)})


@app.route("/audio/<name>/<path:filename>")
def serve_audio(name: str, filename: str):
    project = get_project(name)
    return send_from_directory(str(project["dir"]), filename)


def seed_learned_words():
    """Merge all annotation words into learned_words.json on every startup."""
    import re
    existing = set(json.loads(LEARNED_WORDS_FILE.read_text("utf-8")) if LEARNED_WORDS_FILE.exists() else [])
    before = len(existing)
    for project in discover_projects():
        ann_file = project["dir"] / "annotations.json"
        if not ann_file.exists():
            continue
        data = json.loads(ann_file.read_text("utf-8"))
        for task in data.values():
            if not isinstance(task, dict) or task.get("status") != "done":
                continue
            text = task.get("text", "")
            if not text:
                continue
            for w in text.split():
                clean = re.sub(r"[\"\"''.,!?;:()\[\]{}\-–—]", "", w).lower()
                if len(clean) > 1:
                    existing.add(clean)
    LEARNED_WORDS_FILE.write_text(json.dumps(sorted(existing), ensure_ascii=False), "utf-8")
    print(f"learned_words.json: {len(existing)} words (+{len(existing) - before} new from annotations).")


if __name__ == "__main__":
    print(f"Root:        {DATA_ROOT}")
    projects = discover_projects()
    print(f"Projects:    {len(projects)}")
    for p in projects:
        print(f"  - {p['name']}  ({p['tasks_file'].name})")
    if not projects:
        print("  (none found — each project must be a subfolder containing a *.label_studio.json)")
    seed_learned_words()
    app.run(host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "5000")), debug=False)
