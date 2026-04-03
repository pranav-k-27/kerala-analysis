# Kerala War Room 2026 — Deployment Guide
## Render + GitHub

---

## STEP 1 — Prepare Local Files

Make sure these files are in your project root:
```
KERALA-WARROOM/
├── .gitignore        ← from this guide
├── render.yaml       ← from this guide
├── frontend/
│   └── .env          ← VITE_API_URL=http://localhost:8000 (local)
└── pipeline/
    └── .env          ← OPENAI_API_KEY=sk-...
```

---

## STEP 2 — One Important Code Change

In `frontend/src/components/` — find every file that has:
```javascript
const API = "http://localhost:8000";
```

Replace with:
```javascript
const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
```

Files to check:
- WarRoomDashboard.jsx
- PipelineMonitor.jsx
- KeralaCMap.jsx (or KeralaCMap_dynamic.jsx)
- SwingPredictionEngine.jsx
- MalayalamNewsFeed.jsx

---

## STEP 3 — Push to GitHub

```bash
# Navigate to your project root
cd C:\Users\Pranav\Downloads\INC\Kerala\kerala-warroom-2026_working_full\kerala-warroom

# Initialize git (if not already done)
git init

# Add remote — create a NEW private repo on github.com first
# then copy the URL and run:
git remote add origin https://github.com/YOUR_USERNAME/kerala-warroom-2026.git

# Stage all files
git add .

# Verify what's being committed (check .env is NOT listed)
git status

# Commit
git commit -m "Kerala War Room 2026 — AI Intelligence System v3"

# Push
git push -u origin main
```

---

## STEP 4 — Deploy on Render

### 4a. Deploy Backend (FastAPI)
1. Go to https://render.com → New → Web Service
2. Connect your GitHub repo
3. Settings:
   - **Name:** `kerala-warroom-api`
   - **Root Directory:** `pipeline`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn api:app --host 0.0.0.0 --port $PORT`
4. Environment Variables → Add:
   - `OPENAI_API_KEY` = your key
5. Click **Create Web Service**
6. Wait for deploy → copy the URL (e.g. `https://kerala-warroom-api.onrender.com`)

### 4b. Deploy Frontend (React)
1. Render → New → Static Site
2. Connect same GitHub repo
3. Settings:
   - **Name:** `kerala-warroom-frontend`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist`
4. Environment Variables → Add:
   - `VITE_API_URL` = your backend URL from step 4a
5. Click **Create Static Site**

### 4c. Setup Pipeline Cron (Daily Auto-Run)
1. Render → New → Cron Job
2. Settings:
   - **Name:** `kerala-warroom-pipeline`
   - **Root Directory:** `pipeline`
   - **Build Command:** `pip install -r requirements.txt`
   - **Command:** `python kerala_intelligence_pipeline.py --run-now`
   - **Schedule:** `30 0 * * *` (6 AM IST = 12:30 AM UTC)
3. Environment Variables → Add:
   - `OPENAI_API_KEY` = your key
4. Create Cron Job

---

## STEP 5 — Verify Deployment

1. Open your frontend URL
2. Check the green "LIVE — AI Pipeline Connected" indicator
3. If it shows "API Offline" → check backend URL in frontend env vars
4. Manually trigger pipeline: Render dashboard → Cron Job → Run Now

---

## STEP 6 — Share Access

Your public URLs will be:
```
Frontend:  https://kerala-warroom-frontend.onrender.com
API:       https://kerala-warroom-api.onrender.com
```

Share the frontend URL with the war room team and sponsors.

---

## Cost on Render

| Service | Plan | Cost |
|---------|------|------|
| Backend API | Free tier (spins down after 15min inactivity) | ₹0 |
| Frontend | Free (static sites are always free) | ₹0 |
| Cron Job | Free (limited minutes/month) | ₹0 |
| **Total** | | **₹0** |

For always-on backend (no spin-down): Starter plan = $7/month (~₹580)
Recommended for war room use — spin-down causes 30-second cold starts.

---

## Troubleshooting

**"API Offline" on frontend:**
→ Check VITE_API_URL env var matches your actual backend URL exactly

**Pipeline not running:**  
→ Check OPENAI_API_KEY is set in cron job env vars

**CORS error in browser:**
→ Add your frontend URL to api.py CORS origins:
```python
allow_origins=[
    "http://localhost:5173",
    "https://kerala-warroom-frontend.onrender.com",
]
```

**Reports not persisting between runs:**
→ Add a Render Disk to the backend service (pipeline config shows this)
