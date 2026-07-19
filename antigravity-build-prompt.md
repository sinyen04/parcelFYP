# Build Prompt for Google Antigravity

Copy everything below into Antigravity as your task/mission description.

---

## Project Goal

Build a complete, runnable full-stack web application called **"Parcel Condition Detection System"**. It has two pages: a main dashboard and a parcel detail page. Users upload a video of parcels; a backend pipeline processes the video, detects each parcel, classifies it as `damaged` or `undamaged`, and stores the result in a database. The frontend displays live totals and lets the user browse and inspect each detected parcel.

**Important constraint:** I do not have a trained YOLO model yet. Do NOT block the build on this. Write the full inference pipeline using the Ultralytics YOLO API exactly as it would be used in production, but point it at a placeholder weights path (e.g. `backend/ml/weights/best.pt`) that does not need to exist yet. Wrap model loading so that if the weights file is missing, the pipeline falls back to a **mock inference function** that generates plausible fake detections (random bounding boxes, random `damaged`/`undamaged` labels, random confidence scores between 0.5–0.99) so the entire system is testable end-to-end right now. Structure the code so that later, dropping a real `best.pt` file into that path and flipping one config flag (e.g. `USE_MOCK_MODEL = False` in a `.env` or config file) switches the app to real inference with zero other code changes. Clearly comment every place this switch happens.

## Tech Stack (use exactly this)

- **Frontend:** Next.js (App Router), JavaScript, **shadcn/ui** for all UI components (buttons, cards, tables, dialogs, etc.) on top of Tailwind CSS
- **Backend:** Python, FastAPI, Uvicorn
- **ML:** Ultralytics YOLOv8 (`ultralytics` package), with built-in ByteTrack tracking (`model.track(..., persist=True)`), OpenCV for frame extraction
- **Database:** SQLite for local dev (via SQLAlchemy ORM), structured so switching to PostgreSQL later only requires changing the connection string
- **Environment manager:** **venv**. Create a standard Python virtual environment (`python -m venv .venv`) for the backend/ML side and install all Python dependencies (FastAPI, uvicorn, sqlalchemy, ultralytics, opencv-python, python-multipart, pydantic, python-dotenv, torch — CPU build unless told otherwise) into it via `pip install -r requirements.txt`. Provide a `requirements.txt` file in `backend/` that fully reproduces this environment, and use standard venv activation (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on macOS/Linux) in any setup scripts or instructions — no conda anywhere.

## Repository Structure

Create this structure (adjust only if there's a good reason):

```
parcel-detection-system/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                 # FastAPI app, CORS, router includes
│   │   ├── config.py                # settings incl. USE_MOCK_MODEL, MODEL_WEIGHTS_PATH, DB URL
│   │   ├── database.py              # SQLAlchemy engine/session setup
│   │   ├── models.py                # SQLAlchemy models: Video, Parcel, User
│   │   ├── schemas.py                # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── videos.py            # POST /videos/upload, GET /videos/{id}/status
│   │   │   ├── parcels.py           # GET /parcels, GET /parcels/{id}
│   │   │   ├── dashboard.py         # GET /dashboard/summary
│   │   │   └── auth.py              # POST /auth/login, /auth/logout (simple JWT)
│   │   ├── ml/
│   │   │   ├── inference.py          # real YOLO+tracker pipeline (Ultralytics)
│   │   │   ├── mock_inference.py     # fake detection generator, same output shape as inference.py
│   │   │   └── pipeline.py           # orchestrates: pick real or mock, dedupe by track_id, write to DB
│   │   └── worker.py                 # background task runner for processing uploaded videos
│   └── uploads/                      # saved videos + parcel image crops (gitignored)
└── frontend/
    ├── package.json
    ├── components.json               # shadcn/ui config
    ├── app/
    │   ├── layout.jsx
    │   ├── page.jsx                   # Dashboard (route: /)
    │   └── parcels/[id]/page.jsx      # Parcel Detail (route: /parcels/:id)
    ├── components/
    │   ├── ui/                        # shadcn/ui generated components (card, button, table, dialog, etc.)
    │   ├── summary-cards.jsx
    │   ├── upload-panel.jsx
    │   └── parcel-list.jsx
    └── lib/
        └── api-client.js              # fetch wrapper for backend calls
```

## Database Schema (implement exactly)

**`videos`**: `id (PK)`, `filename`, `storage_path`, `status` (`pending`/`processing`/`completed`/`failed`), `uploaded_at`, `processed_at` (nullable)

**`parcels`**: `id (PK)`, `video_id (FK)`, `track_id` (int), `condition` (`damaged`/`undamaged`), `confidence_score` (float), `image_path`, `bbox_x`, `bbox_y`, `bbox_w`, `bbox_h`, `action` (derive: `damaged` → `inspection`, `undamaged` → `normal_line`), `detected_at`, `created_at`. Add a unique constraint on `(video_id, track_id)`.

**`users`**: `id (PK)`, `username`, `password_hash`, `role`

## Backend Behavior

1. `POST /videos/upload` accepts a multipart video file, saves it under `backend/uploads/videos/`, creates a `videos` row with status `pending`, and schedules a background task (FastAPI `BackgroundTasks` is fine — no need for Celery/Redis at this stage) to process it.
2. The background task (`worker.py` → `pipeline.py`):
   - Sets video status to `processing`.
   - Reads the video frame-by-frame with OpenCV.
   - Calls either the real YOLO+tracker pipeline (`inference.py`) or the mock generator (`mock_inference.py`), controlled by `config.USE_MOCK_MODEL`.
   - For each unique `track_id`, keeps only the highest-confidence frame's detection, crops that region and saves it as an image under `backend/uploads/crops/`, and upserts one row into `parcels`.
   - Sets video status to `completed` (or `failed` with a caught exception logged).
3. `GET /videos/{id}/status` returns current status so the frontend can poll.
4. `GET /dashboard/summary` returns `{ total_detected, total_damaged, total_undamaged }` as simple counts over `parcels` (all-time, across all videos).
5. `GET /parcels?condition=damaged|undamaged&limit=&offset=` returns paginated rows for the two list panels.
6. `GET /parcels/{id}` returns the full detail record: condition, confidence_score, detected_at (timestamp), action, image_path.
7. `POST /auth/login` / `POST /auth/logout`: simple JWT issuing/invalidation, one hardcoded or seeded test user is fine for now.
8. Enable permissive CORS for local dev so the Vite frontend (localhost:5173 or similar) can call the FastAPI backend (localhost:8000).

### Mock inference contract
`mock_inference.py` must return the exact same data shape `inference.py` would return — a list of dicts like:
```python
{"track_id": int, "condition": "damaged" | "undamaged", "confidence": float, "bbox": (x, y, w, h), "frame_timestamp": float}
```
so `pipeline.py` never needs to know which one produced the data.

## Frontend Behavior

Use Next.js App Router for routing (`app/page.jsx` = dashboard, `app/parcels/[id]/page.jsx` = detail page). Set up shadcn/ui first (`npx shadcn@latest init`, then add the `card`, `button`, `table`, `badge`, `dialog`, and `input` components at minimum) and build every visible UI element — cards, buttons, list rows, the upload control, the login form — out of shadcn/ui components rather than raw HTML elements, so styling stays consistent.

**Dashboard page (`/`)**
- Three summary `<Card>` components (Total Detected / Total Damaged / Total Undamaged) fetched from `/dashboard/summary`, refreshed every few seconds while any video is `processing`.
- Video upload panel: shadcn `<Input type="file">` + `<Button>`, shows current processing status by polling `/videos/{id}/status` (a shadcn `<Badge>` for status is a nice touch).
- Damaged List and Undamaged List panels: use shadcn `<Table>` (or a scrollable `<Card>` with rows), fetched from `/parcels?condition=...`, each row clickable and navigates to `/parcels/:id`.
- A "LOG OUT" `<Button variant="outline">` top-right that clears the auth token and redirects to a login screen (a basic shadcn form is fine, doesn't need to be elaborate).

**Parcel Detail page (`/parcels/:id`)**
- Fetches `/parcels/{id}` on mount (client component, or a server component with a client-side refresh option — either is fine).
- Shows the cropped parcel image, condition, confidence score, timestamp, and action inside a shadcn `<Card>`.
- An "X" `<Button variant="ghost" size="icon">` that navigates back to the dashboard.

## Setup & Verification Steps (have the agent actually do these)

1. Create `backend/requirements.txt`, then run `python -m venv .venv` inside `backend/`, activate it, and `pip install -r requirements.txt` to build the environment with all backend/ML dependencies.
2. Scaffold the frontend with `npx create-next-app@latest` (JavaScript, App Router, Tailwind enabled), run `npx shadcn@latest init` and add the needed components, then `npm install` any remaining dependencies inside `frontend/`.
3. Start the backend (`uvicorn app.main:app --reload`, inside the activated venv) and the frontend (`npm run dev`), and confirm both boot without errors.
4. Upload a short test video (generate a trivial synthetic one with OpenCV if none is available) through the dashboard UI and confirm: the video reaches `completed` status, the three summary cards update, both lists populate, and clicking a row opens a working detail page with mock data.
5. Write a short `README.md` covering: how to create/activate the venv, how to run backend and frontend, and — clearly — the exact steps to plug in a real trained YOLO model later (where to drop `best.pt`, which config flag to flip).

## Deliverables Checklist

- [ ] Full repo structure as above, all files created
- [ ] `backend/requirements.txt` + venv setup, working and reproducible
- [ ] FastAPI backend running with all 7 endpoints listed above
- [ ] SQLite database auto-created on first run with the 3 tables
- [ ] Mock YOLO pipeline producing believable fake data end-to-end
- [ ] Real YOLO+tracker code path fully written (not stubbed with `pass`), just inactive until a real weights file + config flag are set
- [ ] Next.js frontend using shadcn/ui components throughout, with working Dashboard and Parcel Detail pages, connected to the backend
- [ ] README with setup instructions and the "how to plug in your real model" section
