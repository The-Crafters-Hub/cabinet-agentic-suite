"""
agents_server.py — Unified FastAPI gateway for ALL TCH agentic tools.
Runs on host machine (port 8200). Proxied by Control Panel nginx at /api/agents/.

Start with:
    uvicorn agents_server:app --host 0.0.0.0 --port 8200 --reload

Endpoints:
    GET  /health                  → { status: "ok" }
    POST /sentinel/run            → { days_back: int }
    POST /ingest/run              → { source_url: str }
    POST /research/run            → { question: str }  (ready for future use)
"""

import sys, os, time, logging, re, asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("agents_server")

app = FastAPI(title="TCH Agents API", version="2.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


# ─── Shared utilities ─────────────────────────────────────────────────────────

async def _run_in_thread(fn):
    """Run a blocking function in a threadpool so we don't block the event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, fn)


# ─── /health ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "TCH Agents API", "version": "2.0.0"}


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER: /sentinel
# ═══════════════════════════════════════════════════════════════════════════════

sentinel_router = APIRouter(prefix="/sentinel", tags=["Finance Sentinel"])


class SentinelRunRequest(BaseModel):
    days_back: int = Field(default=7, ge=1, le=365)


class SentinelRunResponse(BaseModel):
    status: str
    summary: str | None = None
    scanned: int | None = None
    sent_for_approval: int | None = None
    skipped: int | None = None
    duration_seconds: float | None = None
    error: str | None = None


def _parse_sentinel_summary(text: str) -> dict:
    scanned = sent = skipped = None
    m = re.search(r"Unmatched.*?(\d+)", text, re.IGNORECASE)
    if m: scanned = int(m.group(1))
    m = re.search(r"Sent.*?Approval.*?(\d+)", text, re.IGNORECASE)
    if m: sent = int(m.group(1))
    m = re.search(r"Skipped.*?(\d+)", text, re.IGNORECASE)
    if m: skipped = int(m.group(1))
    return {"scanned": scanned, "sent_for_approval": sent, "skipped": skipped}


@sentinel_router.post("/run", response_model=SentinelRunResponse)
async def run_sentinel(req: SentinelRunRequest):
    from agents.sentinel_agent import run_sentinel_agent
    logger.info(f"[Sentinel] Starting — days_back={req.days_back}")
    start = time.time()
    try:
        text = await _run_in_thread(lambda: run_sentinel_agent(days_back=req.days_back))
        return SentinelRunResponse(
            status="complete",
            summary=text,
            duration_seconds=round(time.time() - start, 1),
            **_parse_sentinel_summary(text),
        )
    except Exception as e:
        logger.error(f"[Sentinel] Error: {e}")
        return SentinelRunResponse(status="error", error=str(e), duration_seconds=round(time.time() - start, 1))


app.include_router(sentinel_router)


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER: /ingest
# ═══════════════════════════════════════════════════════════════════════════════

ingest_router = APIRouter(prefix="/ingest", tags=["Ingest Agent"])


class IngestRunRequest(BaseModel):
    source_url: str = Field(..., description="YouTube URL to ingest")


class IngestRunResponse(BaseModel):
    status: str
    summary: str | None = None
    technique_name: str | None = None
    category: str | None = None
    skill_level: str | None = None
    steps: int | None = None
    tools_count: int | None = None
    materials_count: int | None = None
    duration_seconds: float | None = None
    error: str | None = None


def _parse_ingest_summary(text: str) -> dict:
    result = {}
    m = re.search(r"Technique[:\s]+(.+)", text, re.IGNORECASE)
    if m: result["technique_name"] = m.group(1).strip().rstrip(".")
    m = re.search(r"Category[:\s]+(.+)", text, re.IGNORECASE)
    if m: result["category"] = m.group(1).strip().rstrip(".")
    m = re.search(r"Skill[_ ]?Level[:\s]+(.+)", text, re.IGNORECASE)
    if m: result["skill_level"] = m.group(1).strip().rstrip(".")
    m = re.search(r"(?:Steps|Number of steps)[:\s]+(\d+)", text, re.IGNORECASE)
    if m: result["steps"] = int(m.group(1))
    m = re.search(r"Tools[:\s]+(\d+)", text, re.IGNORECASE)
    if m: result["tools_count"] = int(m.group(1))
    m = re.search(r"Materials[:\s]+(\d+)", text, re.IGNORECASE)
    if m: result["materials_count"] = int(m.group(1))
    return result


@ingest_router.post("/run", response_model=IngestRunResponse)
async def run_ingest(req: IngestRunRequest):
    from agents.ingest_agent import run_ingest_agent
    logger.info(f"[Ingest] Starting — url={req.source_url}")
    start = time.time()
    try:
        text = await _run_in_thread(lambda: run_ingest_agent(source=req.source_url))
        return IngestRunResponse(
            status="complete",
            summary=text,
            duration_seconds=round(time.time() - start, 1),
            **_parse_ingest_summary(text),
        )
    except Exception as e:
        logger.error(f"[Ingest] Error: {e}")
        return IngestRunResponse(status="error", error=str(e), duration_seconds=round(time.time() - start, 1))


app.include_router(ingest_router)


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTER: /research  (shell — ready for future wiring)
# ═══════════════════════════════════════════════════════════════════════════════

research_router = APIRouter(prefix="/research", tags=["Research Agent"])


class ResearchRunRequest(BaseModel):
    question: str = Field(..., min_length=5)


class ResearchRunResponse(BaseModel):
    status: str
    answer: str | None = None
    source: str | None = None
    duration_seconds: float | None = None
    error: str | None = None


@research_router.post("/run", response_model=ResearchRunResponse)
async def run_research(req: ResearchRunRequest):
    from agents.research_agent import run_research_agent
    logger.info(f"[Research] Starting — question={req.question[:80]}")
    start = time.time()
    try:
        text = await _run_in_thread(lambda: run_research_agent(question=req.question))
        return ResearchRunResponse(
            status="complete",
            answer=text,
            duration_seconds=round(time.time() - start, 1),
        )
    except Exception as e:
        logger.error(f"[Research] Error: {e}")
        return ResearchRunResponse(status="error", error=str(e), duration_seconds=round(time.time() - start, 1))


app.include_router(research_router)
