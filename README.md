# Label-in

A lightweight, local Label-Studio-style web app for transcribing audio clips. Point it at a folder of datasets — each subfolder is its own project with its own progress.

## Features

- **Multi-project** — every subfolder of the root containing a `*.label_studio.json` is auto-discovered as a project. Switch between them from a dropdown in the sidebar; the last-used project is remembered.
- **Sidebar task list** with done/pending status dots, click-to-jump, and filter (All / Pending / Done).
- **Live progress bar** per project (`<done> / <total>`).
- **Audio player** with variable playback speed (0.5× – 1.5×).
- **Prediction shown read-only** above an editable textarea pre-filled with the model's text — edit and save.
- **Atomic JSON persistence** — annotations saved to `annotations.json` *inside each project's folder*; the original `*.label_studio.json` is never modified.
- **Label-Studio-compatible export** at `/api/projects/<name>/export` (merges your edits into the original task structure as `annotations`).
- **Auto-resume** — on switching projects, jumps to the first pending task.

## Project layout

```
label-in/
├── app.py                       # Flask backend
├── templates/
│   └── index.html               # Single-page UI
├── requirements.txt
├── storytown_bolo/              # Project 1
│   ├── *.wav
│   ├── storytown_bolo.label_studio.json
│   └── annotations.json         # Created on first save
└── another_dataset/             # Project 2 — drop more folders like this
    ├── *.wav
    ├── another_dataset.label_studio.json
    └── annotations.json
```

To add a new project, just drop a new subfolder containing audio files and a `*.label_studio.json` next to the existing ones — refresh the page and it appears in the dropdown.

## Setup

### Quick start (recommended)

**Linux / macOS:**
```bash
chmod +x run.sh
./run.sh
```

**Windows:**
```cmd
run.bat
```

The scripts automatically create a virtual environment, install dependencies, and launch the app. Pass arguments to set a custom root folder (e.g. `./run.sh path/to/root`).

### Manual setup

```bash
# Create a virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate    # Linux/macOS
# or
.venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt
```

## Run

```bash
python app.py                    # uses datasets/ directory as the root
python app.py path/to/root       # or point at another root folder
```

Then open <http://127.0.0.1:5000>.

Each subfolder under the root that contains a `*.label_studio.json` is treated as a project.

## Input format

Each task in `*.label_studio.json` looks like:

```json
{
  "data": {
    "audio": "clip_00000.wav",
    "start": 5.12,
    "end": 8.7,
    "text": "predicted transcription",
    "confidence": 0.215
  },
  "predictions": [
    {
      "model_version": "large-v3",
      "score": 0.215,
      "result": [
        {
          "from_name": "transcription",
          "to_name": "audio",
          "type": "textarea",
          "value": { "text": ["predicted transcription"] }
        }
      ]
    }
  ]
}
```

## Output format

Each project's `annotations.json` is keyed by audio filename:

```json
{
  "clip_00000.wav": {
    "index": 0,
    "audio": "clip_00000.wav",
    "text": "your corrected transcription",
    "status": "done",
    "updated_at": "2026-04-29T12:34:56+00:00"
  }
}
```

`GET /api/projects/<name>/export` returns the original tasks with your edits merged in as Label-Studio-format `annotations`, suitable for re-importing into Label Studio or downstream training pipelines.

## Keyboard shortcuts

| Key | Action |
|---|---|
| `Ctrl` + `Enter` | Save and advance to next task |
| `Tab` / `Shift` + `Tab` | Next / previous task |
| `Space` | Play / pause (when not typing) |
| `R` | Replay from start (when not typing) |
| `Ctrl` + `D` | Copy prediction into the textarea |

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | UI |
| `GET` | `/api/projects` | List all projects with done/total counts |
| `GET` | `/api/projects/<name>/tasks` | List tasks for a project, merged with annotations |
| `POST` | `/api/projects/<name>/tasks/<idx>` | Save annotation `{ text, status? }` |
| `GET` | `/api/projects/<name>/export` | Tasks + annotations in Label Studio format |
| `GET` | `/audio/<name>/<filename>` | Serves audio from the project's folder |

## Notes

- Server binds to `127.0.0.1:5000` only (local-only by design).
- Saves are atomic (`annotations.json.tmp` → rename) so a crash mid-save won't corrupt the file.
- An empty annotation auto-marks a task as `pending`; non-empty marks it `done`. Use **Mark Pending** to keep text but flag for review.
- Each project has independent state — annotations, progress, and current task selection do not leak between projects.
