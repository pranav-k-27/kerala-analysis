# 🗳️ Kerala War Room 2026
### AI-Powered Political Intelligence System for Kerala Assembly Elections

> **Polling: April 9, 2026 · Results: May 4, 2026 · 140 Seats**

---

## 🧠 What's Inside

This is a complete, production-grade AI political intelligence system built for the **UDF/Congress strategic command** for the 2026 Kerala Assembly Elections.

| Module | Description |
|--------|-------------|
| 🗳️ **War Room Dashboard** | Live intelligence dashboard — seat projections, district map, swing seats, strategies, leaders |
| 🤖 **AI Swing Prediction Engine** | Claude-powered constituency analyzer with 8 intelligence signals |
| ⚙️ **LangGraph Intelligence Pipeline** | Daily automated political intelligence — scraping, NLP, risk detection, action recommendations |

---

## 📁 Project Structure

```
kerala-warroom/
├── frontend/                    ← React + Vite app
│   ├── src/
│   │   ├── App.jsx              ← Master shell with top navigation
│   │   └── components/
│   │       ├── WarRoomDashboard.jsx      ← Live intelligence dashboard
│   │       ├── SwingPredictionEngine.jsx ← AI constituency predictor
│   │       └── PipelineMonitor.jsx       ← Pipeline status + logs
│   ├── package.json
│   └── vite.config.js
├── pipeline/
│   ├── kerala_intelligence_pipeline.py   ← LangGraph 10-node pipeline
│   └── requirements.txt
├── .vscode/
│   └── launch.json              ← VS Code run configs (F5 to launch)
├── .env.example                 ← Copy to .env and fill in keys
└── README.md
```

---

## ⚡ Quick Start (5 minutes)

### Step 1 — Clone & open in VS Code
```bash
# Unzip the downloaded package
cd kerala-warroom
code .
```

### Step 2 — Set up environment variables
```bash
# Copy the example file
cp .env.example .env

# Open .env and add your Anthropic API key
# VITE_ANTHROPIC_API_KEY=sk-ant-your-key-here
# ANTHROPIC_API_KEY=sk-ant-your-key-here
```
> Get your API key from: https://console.anthropic.com/

### Step 3 — Install frontend dependencies
```bash
cd frontend
npm install
```

### Step 4 — Run the frontend
```bash
npm run dev
# Opens at http://localhost:5173
```

### Step 5 — (Optional) Run the Python pipeline
```bash
cd pipeline
pip install -r requirements.txt
python kerala_intelligence_pipeline.py --run-now
```

---

## 🔑 API Key Setup (Important)

The **AI Swing Prediction Engine** calls the Anthropic API directly from your browser.

Create `frontend/.env` (not `.env.example`):
```
VITE_ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
```

Then restart the dev server:
```bash
npm run dev
```

> ⚠️ The `VITE_` prefix is required — Vite only exposes variables with this prefix to the browser.

---

## 🖥️ VS Code Integration

Press **F5** to see the launch menu:
- `🗳️ War Room Frontend (Vite)` — starts the React app
- `⚙️ Intelligence Pipeline (Run Now)` — runs the pipeline once
- `📅 Intelligence Pipeline (Daily Schedule)` — schedules at 06:00 IST
- `🚀 Full War Room` — starts both simultaneously

---

## 🤖 AI Swing Prediction Engine

Select any of 15 swing constituencies and tune 8 intelligence signals:

| Signal | What it measures |
|--------|-----------------|
| Inflation Anger | Local price rise intensity |
| UDF Candidate Strength | Quality of the UDF candidate |
| NDA Spoiler Risk | How much BJP splits anti-LDF vote |
| Minority Consolidation | Muslim/Christian vote solidification |
| LDF Cadre Fatigue | Worker disenchantment level |
| Youth Mobilisation | First-time voter drive effectiveness |
| Anti-Incumbency Wave | Local anti-LDF sentiment |
| Rahul Gandhi Effect | National leader resonance |

Claude returns: Win probability, projected margin, key factors, tactical actions, best/worst scenarios, and an analyst note.

---

## ⚙️ LangGraph Intelligence Pipeline

**10-node async StateGraph:**

```
ingest_news → ingest_social → ingest_field
    → analyze_sentiment → cluster_topics
    → score_constituencies → predict_swings
    → detect_risks → recommend_actions
    → generate_report
```

**Output:** Daily War Brief (Markdown + JSON) saved to `reports/`

**Schedule:**
```bash
python pipeline/kerala_intelligence_pipeline.py --schedule 06:00
```

**Single run:**
```bash
python pipeline/kerala_intelligence_pipeline.py --run-now
```

---

## 📊 Data Sources

- **Surveys**: Poll Mantra (n=26K), Mathrubhumi, Political Vibe, C-Voter, ElectionTracker7
- **News**: Mathrubhumi, Manorama, The Hindu, Deccan Herald, National Herald
- **Historical**: 2021 Assembly, 2024 Lok Sabha, 2025 Local Body results

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite 5 |
| AI Engine | Claude Sonnet 4 (Anthropic) |
| Pipeline | LangGraph + LangChain |
| Vector Store | Qdrant (optional) |
| Scraping | httpx + BeautifulSoup |
| Scheduling | Python `schedule` |

---

## 🔒 Security Notes

- Never commit `.env` to git (already in `.gitignore`)
- The `anthropic-dangerous-direct-browser-access: true` header is required for local dev browser API calls
- For production deployment, route API calls through a backend proxy

---

*Built for Kerala 2026 Assembly Elections · UDF Strategic Intelligence*
*Powered by Claude AI + LangGraph*
