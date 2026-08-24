"""
agents/ingest_agent.py
Lesson Ingest Agent — ADK 2.7.1
Ingests a YouTube video or local file, extracts craft knowledge with Gemini,
embeds it, and stores it in teacher_student_knowledge.

Usage (from main.py):
    run_ingest_agent(source_url="https://youtube.com/...")
"""

import os
import sys
import logging
import asyncio
import urllib.parse as urlparse

sys.path.insert(0, "D:/TheCraftersHub_DataLab/agent_agentic_hackathon")

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from agents.tools.storage import generate_embedding, store_knowledge_entry, KnowledgeEntry
from youtube_transcript_api import YouTubeTranscriptApi
import requests
import json
from google.cloud import storage

logger = logging.getLogger(__name__)

# Cloud Run endpoint URL (replace with actual deployed URL later, or local for testing)
CLOUD_RUN_URL = os.getenv("CLOUD_RUN_URL", "http://localhost:8080")

# ── Tool functions (plain Python — ADK wraps via FunctionTool) ────────────────

def tool_trigger_cloud_extraction(source: str) -> dict:
    """
    Fetch the YouTube transcript locally (YouTube blocks GCP IPs), then send it
    to the Cloud Run backend for Gemini extraction and GCS storage.

    Args:
        source: YouTube URL (https://youtube.com/...)

    Returns:
        dict with 'gcs_uri' pointing to the extracted JSON on Google Cloud Storage.
    """
    if not source.startswith("http"):
        return {"error": "Only YouTube URLs are supported."}

    # Step 1: Fetch transcript locally — YouTube blocks GCP IP ranges
    try:
        parsed = urlparse.urlparse(source)
        video_id = urlparse.parse_qs(parsed.query).get('v', [None])[0]
        if not video_id:
            return {"error": "Invalid YouTube URL: missing 'v' parameter"}
        api = YouTubeTranscriptApi()
        t_list = api.list(video_id)
        t_obj = t_list.find_transcript(['en'])
        data = t_obj.fetch()
        transcript = " ".join([item.text for item in data])
        logger.info(f"Locally fetched transcript: {len(transcript)} chars for {video_id}")
    except Exception as e:
        return {"error": f"Transcript fetch failed locally: {e}"}

    # Step 2: Send transcript to Cloud Run for Gemini extraction + GCS upload
    cloud_run_url = os.getenv("CLOUD_RUN_URL", "http://localhost:8080")
    logger.info(f"Sending transcript to Cloud Run at {cloud_run_url}/extract")
    try:
        response = requests.post(
            f"{cloud_run_url}/extract",
            json={"source_url": source, "transcript": transcript, "video_id": video_id},
            timeout=120
        )
        response.raise_for_status()
        resp_data = response.json()
        return {"gcs_uri": resp_data.get("gcs_uri")}
    except Exception as e:
        logger.error(f"Cloud Run extraction failed: {e}")
        return {"error": str(e)}

def tool_download_and_store(gcs_uri: str) -> dict:
    """
    Download the extracted JSON from GCS, generate embeddings, and store in PostgreSQL.

    Args:
        gcs_uri: The gs://... URI of the extracted JSON file.

    Returns:
        dict with 'row_id', 'technique_name', 'category', 'steps'.
    """
    if not gcs_uri.startswith("gs://"):
        return {"error": "Invalid GCS URI"}

    # Parse GCS URI
    parts = gcs_uri.replace("gs://", "").split("/", 1)
    bucket_name = parts[0]
    blob_name = parts[1]

    # Download from GCS
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    json_data = blob.download_as_string()
    data = json.loads(json_data)

    # Build KnowledgeEntry
    entry = KnowledgeEntry(
        technique_name  = data.get("technique_name", "Unknown Technique"),
        category        = data.get("category", "woodworking"),
        materials       = data.get("materials", []),
        tools           = data.get("tools", []),
        safety_notes    = data.get("safety_notes", ""),
        skill_level     = data.get("skill_level", "beginner"),
        step_by_step    = data.get("step_by_step", []),
        key_concepts    = data.get("key_concepts", []),
        common_mistakes = data.get("common_mistakes", []),
        raw_content     = data.get("raw_content", ""),
        source_url      = data.get("source_url"),
        source_filename = data.get("source_filename"),
    )

    # Generate embedding
    embed_text = f"{entry.technique_name}. {entry.category}. {' '.join(entry.key_concepts[:5])}. {entry.raw_content[:500]}"
    embedding  = generate_embedding(embed_text)

    # Store in DB
    row_id = store_knowledge_entry(entry, embedding)

    return {
        "row_id":         row_id,
        "technique_name": entry.technique_name,
        "category":       entry.category,
        "skill_level":    entry.skill_level,
        "steps":          len(entry.step_by_step),
        "tools_count":    len(entry.tools),
        "materials_count": len(entry.materials),
    }


# ── ADK Agent definition ──────────────────────────────────────────────────────

INGEST_AGENT = Agent(
    name="lesson_ingest_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
    description=(
        "Ingests woodworking/woodturning lesson content from YouTube videos or local files. "
        "Extracts structured craft knowledge and stores it in The Crafters Hub knowledge base."
    ),
    instruction="""You are the Lesson Ingest Agent for The Crafters Hub — a woodworking school in Cairo, Egypt.

Your job is to ingest a lesson source (YouTube URL) and store its knowledge using our hybrid cloud architecture.

Workflow:
1. Call tool_trigger_cloud_extraction with the YouTube URL. This runs on Google Cloud Run and writes to Cloud Storage (GCS).
2. Take the returned gcs_uri and call tool_download_and_store to embed the data and save it to the local PostgreSQL database.
3. Report the result clearly: technique name, category, skill level, number of steps stored, and the GCS URI as proof of cloud execution.

Always be factual. If a tool fails, report the error clearly — do not make up data.
Do not call any tool twice for the same source.""",
    tools=[
        FunctionTool(tool_trigger_cloud_extraction),
        FunctionTool(tool_download_and_store),
    ],
)


# ── Public runner function ────────────────────────────────────────────────────

def run_ingest_agent(source: str) -> str:
    """
    Run the Lesson Ingest Agent for a given source.

    Args:
        source: YouTube URL or absolute path to a local video.

    Returns:
        Agent's final text response.
    """
    from dotenv import load_dotenv
    load_dotenv("D:/TheCraftersHub_DataLab/.env")

    session_service = InMemorySessionService()
    runner = Runner(
        agent=INGEST_AGENT,
        app_name="tch_ingest",
        session_service=session_service,
    )

    async def _run():
        session = await session_service.create_session(
            app_name="tch_ingest",
            user_id="hosam",
        )
        message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=f"Ingest this lesson source: {source}")]
        )
        final_response = ""
        async for event in runner.run_async(
            user_id="hosam",
            session_id=session.id,
            new_message=message,
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        final_response += part.text
        return final_response

    return asyncio.run(_run())
