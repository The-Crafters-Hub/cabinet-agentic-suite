"""
sentinel_server.py — Lightweight FastAPI server for the Finance Sentinel Agent.
Runs on host machine (port 8200). Proxied by Control Panel nginx at /api/sentinel/.

Start with:
    uvicorn sentinel_server:app --host 0.0.0.0 --port 8200 --reload

Endpoints:
    POST /run         { days_back: int }  → runs sentinel, returns full result
    GET  /health      → { status: "ok" }
"""

import sys
import os
import time
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncio

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sentinel_server")

app = FastAPI(title="TCH Finance Sentinel API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory job store (single-server, sufficient for this use case) ─────────
jobs: dict[str, dict] = {}


class RunRequest(BaseModel):
    days_back: int = Field(default=7, ge=1, le=365, description="Days to scan back")


class RunResponse(BaseModel):
    job_id: str
    status: str
    summary: str | None = None
    scanned: int | None = None
    sent_for_approval: int | None = None
    skipped: int | None = None
    duration_seconds: float | None = None
    error: str | None = None


def _parse_summary(text: str) -> dict:
    """Extract key numbers from the agent's summary text."""
    import re
    scanned = sent = skipped = None
    m = re.search(r"Unmatched.*?(\d+)", text, re.IGNORECASE)
    if m: scanned = int(m.group(1))
    m = re.search(r"Sent.*?Approval.*?(\d+)", text, re.IGNORECASE)
    if m: sent = int(m.group(1))
    m = re.search(r"Skipped.*?(\d+)", text, re.IGNORECASE)
    if m: skipped = int(m.group(1))
    return {"scanned": scanned, "sent_for_approval": sent, "skipped": skipped}


@app.get("/health")
def health():
    return {"status": "ok", "service": "Finance Sentinel API"}


@app.post("/run", response_model=RunResponse)
async def run_sentinel(req: RunRequest):
    """
    Run the Finance Sentinel agent synchronously.
    Returns when the agent completes (typically 20–40 seconds).
    """
    import uuid
    job_id = str(uuid.uuid4())[:8].upper()
    logger.info(f"[{job_id}] Sentinel run started — days_back={req.days_back}")

    start = time.time()
    try:
        # Run in thread pool so we don't block the event loop
        loop = asyncio.get_event_loop()
        from agents.sentinel_agent import run_sentinel_agent
        summary_text = await loop.run_in_executor(
            None, lambda: run_sentinel_agent(days_back=req.days_back)
        )
        duration = round(time.time() - start, 1)
        parsed = _parse_summary(summary_text)
        logger.info(f"[{job_id}] Completed in {duration}s — {parsed}")
        return RunResponse(
            job_id=job_id,
            status="complete",
            summary=summary_text,
            duration_seconds=duration,
            **parsed,
        )
    except Exception as e:
        duration = round(time.time() - start, 1)
        logger.error(f"[{job_id}] Failed after {duration}s: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
def status():
    """Check if the sentinel server is reachable and the DB is connected."""
    try:
        from agents.sentinel_agent import tool_scan_unmatched_transactions
        # Dry-run with 0 days just to test DB connectivity
        result = tool_scan_unmatched_transactions(days_back=1)
        db_ok = "error" not in result
    except Exception as e:
        db_ok = False

    return {
        "server": "ok",
        "db": "ok" if db_ok else "error",
        "whatsapp_recipient": os.getenv("HOSAM_ALERT_PHONE", "not set"),
    }
