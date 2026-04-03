"""
╔══════════════════════════════════════════════════════════════╗
║   KERALA WAR ROOM 2026 — FastAPI Bridge Server              ║
║   Serves pipeline reports to the React dashboard            ║
║   Run: uvicorn api:app --reload --port 8000                 ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import glob
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

# ── App setup ────────────────────────────────────────────────
app = FastAPI(
    title="Kerala War Room API",
    description="Bridge between LangGraph pipeline and React dashboard",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

# ── Pipeline run state (in-memory) ───────────────────────────
pipeline_state = {
    "status":     "idle",      # idle | running | complete | error
    "run_id":     None,
    "started_at": None,
    "completed_at": None,
    "log":        [],
    "error":      None,
}


# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {
        "service": "Kerala War Room API",
        "status":  "online",
        "time":    datetime.now().isoformat(),
        "reports": len(list(REPORTS_DIR.glob("report_*.json"))),
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ═══════════════════════════════════════════════════════════════
# REPORTS — List & Fetch
# ═══════════════════════════════════════════════════════════════

@app.get("/api/reports")
def list_reports():
    """Return list of all saved pipeline reports."""
    files = sorted(
        REPORTS_DIR.glob("report_*.json"),
        key=lambda f: f.stat().st_mtime,  # sort by actual file write time
        reverse=True
    )
    reports = []
    for f in files:
        stat = f.stat()
        reports.append({
            "filename":   f.name,
            "run_id":     f.stem.split("_")[-1],
            "date":       f.stem.split("_")[1] if len(f.stem.split("_")) > 1 else "",
            "size_kb":    round(stat.st_size / 1024, 1),
            "created_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return {"count": len(reports), "reports": reports}


@app.get("/api/latest-report")
def get_latest_report():
    """Return the most recent pipeline report."""
    files = sorted(
        REPORTS_DIR.glob("report_*.json"),
        key=lambda f: f.stat().st_mtime,  # sort by actual file write time
        reverse=True
    )
    if not files:
        raise HTTPException(
            status_code=404,
            detail="No reports found. Run the pipeline first: python kerala_intelligence_pipeline.py --run-now"
        )
    with open(files[0], encoding="utf-8") as f:
        data = json.load(f)
    data["_meta"] = {
        "filename":    files[0].name,
        "loaded_at":   datetime.now().isoformat(),
        "total_reports": len(files),
    }
    return JSONResponse(content=data)


@app.get("/api/report/{run_id}")
def get_report_by_id(run_id: str):
    """Return a specific report by run ID."""
    matches = list(REPORTS_DIR.glob(f"report_*_{run_id}.json"))
    if not matches:
        raise HTTPException(status_code=404, detail=f"Report {run_id} not found")
    with open(matches[0], encoding="utf-8") as f:
        return JSONResponse(content=json.load(f))


@app.get("/api/brief/{run_id}")
def get_brief_by_id(run_id: str):
    """Return the markdown brief for a specific run."""
    matches = list(REPORTS_DIR.glob(f"brief_*_{run_id}.md"))
    if not matches:
        raise HTTPException(status_code=404, detail=f"Brief {run_id} not found")
    return FileResponse(matches[0], media_type="text/plain")


# ═══════════════════════════════════════════════════════════════
# PIPELINE — Trigger & Status
# ═══════════════════════════════════════════════════════════════

@app.get("/api/pipeline/status")
def pipeline_status():
    """Return current pipeline run status."""
    return pipeline_state


@app.post("/api/pipeline/run")
async def trigger_pipeline(background_tasks: BackgroundTasks):
    """Trigger a pipeline run from the dashboard."""
    if pipeline_state["status"] == "running":
        return {"message": "Pipeline already running", "run_id": pipeline_state["run_id"]}

    pipeline_state.update({
        "status":     "running",
        "started_at": datetime.now().isoformat(),
        "completed_at": None,
        "log":        ["Pipeline triggered from dashboard..."],
        "error":      None,
    })

    background_tasks.add_task(_run_pipeline_subprocess)
    return {"message": "Pipeline started", "run_id": pipeline_state["run_id"]}


async def _run_pipeline_subprocess():
    """Run the pipeline as a subprocess and stream logs."""
    try:
        pipeline_state["log"].append("Starting LangGraph pipeline...")
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "kerala_intelligence_pipeline.py",
            "--run-now",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=Path(__file__).parent,
        )
        async for line in proc.stdout:
            decoded = line.decode("utf-8", errors="replace").strip()
            if decoded:
                pipeline_state["log"].append(decoded)
                # Cap log at 200 lines
                if len(pipeline_state["log"]) > 200:
                    pipeline_state["log"] = pipeline_state["log"][-200:]

        await proc.wait()
        if proc.returncode == 0:
            pipeline_state["status"] = "complete"
            pipeline_state["completed_at"] = datetime.now().isoformat()
            pipeline_state["log"].append("✅ Pipeline completed successfully!")
        else:
            pipeline_state["status"] = "error"
            pipeline_state["error"] = f"Process exited with code {proc.returncode}"

    except Exception as e:
        pipeline_state["status"] = "error"
        pipeline_state["error"] = str(e)
        pipeline_state["log"].append(f"❌ Error: {str(e)}")



@app.get("/api/malayalam/latest")
def get_latest_malayalam():
    summ_dir = Path("summaries")
    if not summ_dir.exists():
        raise HTTPException(status_code=404, detail="No Malayalam summaries yet. Run: python malayalam_rss.py --fetch")
    files = sorted(
        summ_dir.glob("malayalam_news_*.json"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    if not files:
        raise HTTPException(status_code=404, detail="No Malayalam summaries yet. Run: python malayalam_rss.py --fetch")
    with open(files[0], encoding="utf-8") as f:
        data = json.load(f)
    data["_meta"] = {"filename": files[0].name, "loaded_at": datetime.now().isoformat()}
    return JSONResponse(content=data)


@app.post("/api/malayalam/fetch")
async def trigger_malayalam_fetch(background_tasks: BackgroundTasks):
    background_tasks.add_task(_run_malayalam_fetch)
    return {"message": "Malayalam RSS fetch started"}


async def _run_malayalam_fetch():
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "malayalam_rss.py", "--fetch",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=Path(__file__).parent,
        )
        await proc.wait()
    except Exception as e:
        print(f"Malayalam fetch error: {e}")




# ═══════════════════════════════════════════════════════════════
# SUMMARY — Quick stats endpoint
# ═══════════════════════════════════════════════════════════════



@app.get("/api/summary")
def get_summary():
    """Return quick summary stats from latest report."""
    files = sorted(
        REPORTS_DIR.glob("report_*.json"),
        key=lambda f: f.stat().st_mtime,  # sort by actual file write time
        reverse=True
    )
    if not files:
        return {
            "has_data":   False,
            "message":    "Run the pipeline to generate data",
        }
    with open(files[0], encoding="utf-8") as f:
        report = json.load(f)

    return {
        "has_data":           True,
        "run_id":             report.get("run_id"),
        "date":               report.get("date"),
        "generated_at":       report.get("generated_at"),
        "overall_status":     report.get("overall_status"),
        "majority_confidence": report.get("majority_confidence"),
        "seat_projection":    report.get("seat_projection"),
        "top_risks":          len(report.get("top_risks", [])),
        "constituencies_scored": len(report.get("constituency_scores", [])),
        "topic_clusters":     len(report.get("topic_clusters", [])),
        "swing_summary":      report.get("action_playbook", {}).get("priority_message_of_day", ""),
        "total_reports":      len(files),
    }

@app.get("/api/constituencies")
def get_constituencies():
    files = sorted(
        REPORTS_DIR.glob("report_*.json"),
        key=lambda f: f.stat().st_mtime,  # sort by actual file write time
        reverse=True
    )
    if not files:
        raise HTTPException(status_code=404, detail="Run pipeline first")
    with open(files[0], encoding="utf-8") as f:
        report = json.load(f)
    seats = report.get("constituency_scores", [])
    udf=sum(1 for s in seats if s.get("lean")=="UDF")
    ldf=sum(1 for s in seats if s.get("lean")=="LDF")
    nda=sum(1 for s in seats if s.get("lean")=="NDA")
    swing=sum(1 for s in seats if s.get("lean")=="SWING")
    return JSONResponse(content={
        "seats": seats, "total": len(seats),
        "summary": {"udf_leading":udf,"ldf_leading":ldf,"nda_leading":nda,
                    "swing":swing,"majority_needed":71},
        "run_id": report.get("run_id"),
        "date": report.get("date"),
    })

allow_origins=[
    "http://localhost:5173",
    "https://kerala-warroom-frontend.onrender.com",  # ← add this
]