import os
import json
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
from google import genai
from google.genai import types
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TCH Ingest Backend")

# Initialize clients
try:
    # On Cloud Run, GEMINI_API_KEY should be passed as an env var
    _genai_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    # GCS uses Application Default Credentials
    _storage_client = storage.Client()
    GCS_BUCKET = "tch-knowledge-base-2026"
    MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
except Exception as e:
    logger.error(f"Failed to initialize clients: {e}")

class IngestRequest(BaseModel):
    source_url: str
    transcript: str  # Transcript text pre-fetched locally (YouTube blocks GCP IPs)
    video_id: str

_SYSTEM_INSTRUCTION = """You are an expert woodcraft knowledge extractor for The Crafters Hub, 
a woodworking and woodturning school in Cairo, Egypt.

Your job is to read a video transcript and extract structured, practical teaching knowledge.
Be specific, accurate, and focus on information that a woodworking teacher or student can use directly.
If information is not mentioned in the transcript, leave the field empty — do NOT invent details.
Always identify safety information clearly."""

_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "technique_name": {
            "type": "string",
            "description": "The main woodworking or woodturning technique demonstrated"
        },
        "category": {
            "type": "string",
            "description": "Category: woodturning, joinery, carving, finishing, hand_tools, power_tools, safety, design"
        },
        "materials": {
            "type": "array",
            "items": {"type": "string"},
        },
        "tools": {
            "type": "array",
            "items": {"type": "string"},
        },
        "safety_notes": {
            "type": "string",
        },
        "skill_level": {
            "type": "string",
            "enum": ["beginner", "intermediate", "advanced"],
        },
        "step_by_step": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Ordered steps of the technique, each step as a clear sentence"
        },
        "key_concepts": {
            "type": "array",
            "items": {"type": "string"},
        },
        "common_mistakes": {
            "type": "array",
            "items": {"type": "string"},
        }
    },
    "required": ["technique_name", "category", "skill_level"]
}

def fetch_youtube_transcript(url: str) -> str:
    """Fetch transcript using v1.2.4 instance API."""
    import urllib.parse as urlparse
    parsed = urlparse.urlparse(url)
    video_id = urlparse.parse_qs(parsed.query).get('v')
    if not video_id:
        raise ValueError("Invalid YouTube URL: missing 'v' parameter")
    video_id = video_id[0]
    
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        transcript_obj = transcript_list.find_transcript(['en'])
        data = transcript_obj.fetch()
        text = " ".join([item.text for item in data])
        return text, video_id
    except Exception as e:
        raise ValueError(f"Transcript fetch failed: {e}")

@app.post("/extract")
def extract_knowledge(req: IngestRequest):
    logger.info(f"Received extract request for: {req.source_url} (video_id={req.video_id})")
    
    video_id = req.video_id
    transcript = req.transcript
    logger.info(f"Transcript length: {len(transcript)} chars")
        
    # 2. Extract knowledge using Gemini
    transcript_safe = transcript[:30_000]
    prompt = f"Extract structured woodworking/woodturning knowledge from this transcript.\n\nTRANSCRIPT:\n{transcript_safe}\n\nReturn a JSON object following the schema exactly."
    
    try:
        response = _genai_client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_INSTRUCTION,
                temperature=0.1,
                response_mime_type="application/json",
                response_schema=_EXTRACTION_SCHEMA,
            ),
        )
        raw_json = response.text
        data = json.loads(raw_json)
        
        # Add original context to the output
        data['raw_content'] = transcript_safe
        data['source_url'] = req.source_url
        data['source_filename'] = None
        
    except Exception as e:
        logger.error(f"Gemini extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")
        
    # 3. Save to GCS
    try:
        bucket = _storage_client.bucket(GCS_BUCKET)
        gcs_filename = f"extracts/{video_id}.json"
        blob = bucket.blob(gcs_filename)
        blob.upload_from_string(json.dumps(data, indent=2), content_type="application/json")
        gcs_uri = f"gs://{GCS_BUCKET}/{gcs_filename}"
        logger.info(f"Saved to GCS: {gcs_uri}")
    except Exception as e:
        logger.error(f"GCS upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"GCS upload failed: {e}")

    return {
        "status": "success",
        "video_id": video_id,
        "gcs_uri": gcs_uri,
        "data": data
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "TCH Ingest Backend", "model": MODEL, "gcs_bucket": GCS_BUCKET}

@app.get("/")
def root():
    return {
        "service": "The Cabinet Agentic Suite — Cloud Run Ingest Backend",
        "status": "ok",
        "endpoints": {
            "health": "GET /health",
            "extract": "POST /extract  — body: {source_url, transcript, video_id}"
        },
        "model": MODEL,
        "built_for": "All Things Agentic Hackathon — Google x Devpost 2026"
    }

