# Parcel Condition Detection System

An AI-powered full-stack web application for detecting and classifying parcel conditions (damaged/undamaged) from video footage. Upload a video of parcels, and the system processes it frame-by-frame using a YOLOv8 model with ByteTrack tracking to identify and classify each unique parcel.

## Tech Stack

| Layer     | Technology                                      |
|-----------|------------------------------------------------|
| Frontend  | Next.js (App Router), JavaScript, shadcn/ui, Tailwind CSS |
| Backend   | Python, FastAPI, Uvicorn                        |
| ML        | Ultralytics YOLOv8, ByteTrack, OpenCV           |
| Database  | SQLite (SQLAlchemy ORM)                          |
| Auth      | JWT (python-jose, passlib + bcrypt)              |

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend runs at **http://localhost:8000**. A SQLite database (`parcel_detection.db`) is auto-created on first startup, along with a test user:
- **Username:** `admin`
- **Password:** `admin123`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend runs at **http://localhost:3000**.

### 3. Using the System

1. Open http://localhost:3000 in your browser
2. Log in with `admin` / `admin123`
3. Upload a video file using the upload panel
4. Watch the status badge change from `PENDING` → `PROCESSING` → `COMPLETED`
5. Summary cards and parcel lists will auto-populate with detection results
6. Click any parcel row to view its detailed information

## API Endpoints

| Method | Endpoint                  | Description                                |
|--------|---------------------------|--------------------------------------------|
| POST   | `/auth/login`             | Authenticate and get JWT token             |
| POST   | `/auth/logout`            | Invalidate current token                   |
| POST   | `/videos/upload`          | Upload a video for processing              |
| GET    | `/videos/{id}/status`     | Poll processing status                     |
| GET    | `/dashboard/summary`      | Get total/damaged/undamaged counts         |
| GET    | `/parcels`                | List parcels (filter by `?condition=`)     |
| GET    | `/parcels/{id}`           | Get full parcel detail                     |
| GET    | `/health`                 | Health check                               |

## How to Plug In Your Real YOLO Model

The system ships with a **mock inference mode** that generates realistic fake detections for end-to-end testing. When you have a trained YOLOv8 model, follow these steps to switch to real inference:

### Step 1: Place your model weights

Copy your trained `best.pt` (or whatever your weights file is named) to:

```
backend/ml/weights/best.pt
```

Create the `ml/weights/` directory if it doesn't exist:

```bash
mkdir -p backend/ml/weights
cp /path/to/your/best.pt backend/ml/weights/best.pt
```

### Step 2: Update the config

Edit `backend/.env` and change:

```env
# BEFORE (mock mode):
USE_MOCK_MODEL=True

# AFTER (real model):
USE_MOCK_MODEL=False
```

### Step 3: Restart the backend

```bash
# (from backend/ with venv activated)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

That's it! **Zero code changes required.** The pipeline will now use your real YOLO model with ByteTrack tracking instead of generating mock data.

### Model Requirements

Your YOLOv8 model should:
- Be trained with the Ultralytics framework
- Have two classes: `damaged` (class 0) and `undamaged` (class 1)
- If your class mapping differs, update the mapping in `backend/app/ml/inference.py`

## Project Structure

```
parcelproject/
├── README.md
├── backend/
│   ├── .env                          # Config: USE_MOCK_MODEL, DB URL, JWT secret
│   ├── requirements.txt              # Python dependencies
│   ├── app/
│   │   ├── main.py                   # FastAPI app, CORS, router includes
│   │   ├── config.py                 # Settings (USE_MOCK_MODEL toggle here)
│   │   ├── database.py               # SQLAlchemy engine/session
│   │   ├── models.py                 # ORM models: Video, Parcel, User
│   │   ├── schemas.py                # Pydantic schemas
│   │   ├── worker.py                 # Background video processor
│   │   ├── routers/
│   │   │   ├── auth.py               # JWT login/logout
│   │   │   ├── videos.py             # Upload + status
│   │   │   ├── parcels.py            # List + detail
│   │   │   └── dashboard.py          # Summary stats
│   │   └── ml/
│   │       ├── inference.py          # Real YOLO pipeline (Ultralytics)
│   │       ├── mock_inference.py     # Mock detection generator
│   │       └── pipeline.py           # Orchestrator (picks real/mock)
│   └── uploads/                      # Videos + crop images (gitignored)
└── frontend/
    ├── package.json
    ├── components.json               # shadcn/ui config
    ├── app/
    │   ├── layout.js                 # Root layout (dark mode)
    │   ├── page.js                   # Dashboard
    │   └── parcels/[id]/page.js      # Parcel detail
    ├── components/
    │   ├── ui/                       # shadcn/ui components
    │   ├── summary-cards.js          # Metric cards
    │   ├── upload-panel.js           # Video upload + status
    │   ├── parcel-list.js            # Parcel table
    │   └── login-form.js             # Login form
    └── lib/
        ├── api-client.js             # Backend API wrapper
        └── utils.js                  # Utility functions
```

## Database Schema

- **`videos`**: id, filename, storage_path, status, uploaded_at, processed_at
- **`parcels`**: id, video_id (FK), track_id, condition, confidence_score, image_path, bbox_x/y/w/h, action, detected_at, created_at — with unique constraint on (video_id, track_id)
- **`users`**: id, username, password_hash, role
