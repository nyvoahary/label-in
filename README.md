# Label-in

A lightweight, local Label-Studio-style web app for transcribing audio clips. Point it at a folder of datasets — each subfolder is its own project with its own progress.

## Features

- **Multi-project** — every subfolder of the root containing a `*.label_studio.json` is auto-discovered as a project. Switch between them from a dropdown in the sidebar; the last-used project is remembered.
- **Sidebar task list** with done/pending status dots, click-to-jump, and filter (All / Pending / Done).
- **Live progress bar** per project (`<done> / <total>`).
- **Audio player** with variable playback speed (0.5× – 1.5×), loop regions, and keyboard controls.
- **Multiple predictions shown side by side** — one card per model, each showing the model name and confidence score.
- **Click-to-insert words** — click any word in a prediction card to replace the word at your cursor in the annotation textarea. Select multiple words in a card then click to insert the whole selection.
- **Per-card Copy ↓** — copies that model's full prediction into the textarea.
- **Atomic JSON persistence** — annotations saved to `annotations.json` inside each project folder; the original `*.label_studio.json` is never modified.
- **Label-Studio-compatible export** at `/api/projects/<name>/export` (merges edits into the original task structure as `annotations`).
- **Auto-resume** — on switching projects, jumps to the first pending task.
- **Backup to NAS** — one-click backup of `annotations.json` to a network share (SMB/CIFS).
- **Sync from NAS** — per-task merge of NAS annotations into local; newer `updated_at` wins per task, so work done on two machines on different tasks is safely combined. A `.bak` of the local file is saved before any overwrite.

## Project layout

```
label-in/
├── app.py                       # Flask backend
├── templates/
│   └── index.html               # Single-page UI
├── requirements.txt
├── datasets/
│   ├── speaker_one/             # Project 1
│   │   ├── *.wav
│   │   ├── speaker_one.label_studio.json
│   │   └── annotations.json     # Created on first save
│   └── speaker_two/             # Project 2
│       ├── *.wav
│       ├── speaker_two.label_studio.json
│       └── annotations.json
```

To add a new project, drop a new subfolder with audio files and a `*.label_studio.json` next to the existing ones — refresh the page and it appears in the dropdown.

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
python3 -m venv .venv
source .venv/bin/activate    # Linux/macOS
# or
.venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

## Run

```bash
python app.py                    # uses datasets/ directory as the root
python app.py path/to/root       # or point at another root folder
```

Then open <http://127.0.0.1:5000>.

## Input format

Each task in `*.label_studio.json` supports multiple predictions, one per model:

```json
{
  "data": {
    "audio": "clip_00000.wav",
    "start": 0.0,
    "end": 3.75,
    "confidence": 0.937
  },
  "predictions": [
    {
      "model_version": "BadRex/w2v-bert-2.0-malagasy-asr",
      "score": 0.937,
      "result": [
        {
          "from_name": "transcription",
          "to_name": "audio",
          "type": "textarea",
          "value": { "text": ["vao enina ambin'ny folo taona"] }
        }
      ]
    },
    {
      "model_version": "whisper-large-v3",
      "score": 0.147,
      "result": [
        {
          "from_name": "transcription",
          "to_name": "audio",
          "type": "textarea",
          "value": { "text": ["Po enambe o furtona bolache"] }
        }
      ]
    }
  ]
}
```

All predictions are shown side by side. If no `predictions` array is present, `data.text` is used as a fallback.

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
| `R` | Restart from beginning (when not typing) |
| `[` / `]` | Set loop start / end at playhead |
| `L` | Toggle loop |
| `\` | Clear loop region |
| `Ctrl` + `D` | Copy first prediction into the textarea |

**Prediction word insertion:** click any word in a prediction card to replace the word at your cursor in the annotation box. To insert multiple words, select them in the prediction card first, then click.

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | UI |
| `GET` | `/api/projects` | List all projects with done/total counts |
| `GET` | `/api/projects/<name>/tasks` | List tasks, merged with annotations |
| `POST` | `/api/projects/<name>/tasks/<idx>` | Save annotation `{ text, status? }` |
| `GET` | `/api/projects/<name>/export` | Tasks + annotations in Label Studio format |
| `POST` | `/api/projects/<name>/backup` | Copy `annotations.json` to NAS |
| `POST` | `/api/projects/<name>/sync` | Merge NAS annotations into local (per-task, newer wins) |
| `GET` | `/audio/<name>/<filename>` | Serves audio from the project folder |

## NAS backup & sync

The app can back up and sync `annotations.json` to a network share. Set `BACKUP_ROOT` in `app.py` to your mount point:

```python
BACKUP_ROOT = Path("/run/user/1000/gvfs/smb-share:server=192.168.88.26,share=transcription")
```

The share must already be mounted before starting the app. On Linux, GNOME auto-mounts SMB shares under `/run/user/<uid>/gvfs/` when you connect via Files (Nautilus).

**Backup** copies the current `annotations.json` to `<BACKUP_ROOT>/<project>/annotations.json`.

**Sync** performs a per-task merge:
- Task only on NAS → pulled into local
- Task on both → the one with the newer `updated_at` timestamp wins
- Task only local → kept as-is
- Before writing, the current local file is saved as `annotations.json.bak`

This makes it safe to work on the same project from two machines: split tasks between them, back up from each, then sync on either machine to get the combined result.

## Notes

- Server binds to `127.0.0.1:5000` only (local-only by design).
- Saves are atomic (`annotations.json.tmp` → rename) so a crash mid-save won't corrupt the file.
- An empty annotation auto-marks a task as `pending`; non-empty marks it `done`. Use **Mark Pending** to keep text but flag for review.
- Each project has independent state — annotations, progress, and current task selection do not leak between projects.
