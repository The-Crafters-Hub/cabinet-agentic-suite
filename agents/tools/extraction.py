"""
agents/tools/extraction.py
Extract structured craft knowledge from a video transcript using Gemini 3.6 Flash.
Uses structured output (response_schema) — no regex, no hallucination risk.

Public function:
    extract_craft_knowledge(transcript: str, source_url=None, source_filename=None)
        -> KnowledgeEntry
"""

import os
import json
import logging
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Import KnowledgeEntry from storage (single definition)
import sys
sys.path.insert(0, "D:/TheCraftersHub_DataLab/agent_agentic_hackathon")
from agents.tools.storage import KnowledgeEntry

load_dotenv("D:/TheCraftersHub_DataLab/.env")
logger = logging.getLogger(__name__)

_client: genai.Client | None = None

def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not set in .env")
        _client = genai.Client(api_key=api_key)
    return _client

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

_SYSTEM_INSTRUCTION = """You are an expert woodcraft knowledge extractor for The Crafters Hub, 
a woodworking and woodturning school in Cairo, Egypt. We teach both traditional hand tool
woodworking AND lathe-based woodturning.

Your job is to read a video transcript and extract structured, practical teaching knowledge.
Be specific, accurate, and focus on information that a woodworking teacher or student can use directly.
If information is not mentioned in the transcript, leave the field empty — do NOT invent details.
Always identify safety information clearly."""

_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "technique_name": {
            "type": "string",
            "description": "The main woodworking or woodturning technique demonstrated (e.g. 'Bowl Turning with Spindle Gouge')"
        },
        "category": {
            "type": "string",
            "description": "Category: woodturning, woodworking, joinery, carving, finishing, hand_tools, power_tools, furniture, safety, design"
        },
        "materials": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Materials used (e.g. ['green oak', 'walnut blank', 'danish oil'])"
        },
        "tools": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Tools used (e.g. ['spindle gouge', 'bowl gouge', '10-inch lathe'])"
        },
        "safety_notes": {
            "type": "string",
            "description": "All safety warnings, precautions, and PPE requirements mentioned"
        },
        "skill_level": {
            "type": "string",
            "enum": ["beginner", "intermediate", "advanced"],
            "description": "Required skill level for this technique"
        },
        "step_by_step": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Ordered steps of the technique, each step as a clear sentence"
        },
        "key_concepts": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Core concepts and principles the learner must understand"
        },
        "common_mistakes": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Common mistakes beginners make with this technique"
        }
    },
    "required": ["technique_name", "category", "skill_level"]
}


def extract_craft_knowledge(
    transcript: str,
    source_url: Optional[str] = None,
    source_filename: Optional[str] = None,
) -> KnowledgeEntry:
    """
    Extract structured craft knowledge from a video transcript using Gemini 3.6 Flash.

    Args:
        transcript:       Full transcript text from YouTube or Whisper.
        source_url:       YouTube URL (if from YouTube).
        source_filename:  Local filename (if from Whisper).

    Returns:
        KnowledgeEntry dataclass with all extracted fields.

    Raises:
        ValueError: If Gemini returns an unusable response.
    """
    client = _get_client()

    # Truncate transcript to keep within context limits (~30,000 chars is safe)
    transcript_safe = transcript[:30_000]

    prompt = f"""Extract structured woodworking/woodturning knowledge from this transcript.

TRANSCRIPT:
{transcript_safe}

Return a JSON object following the schema exactly."""

    logger.info(f"Extracting knowledge from transcript ({len(transcript_safe)} chars)...")

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_INSTRUCTION,
            temperature=0.1,  # deterministic extraction
            response_mime_type="application/json",
            response_schema=_EXTRACTION_SCHEMA,
        ),
    )

    raw_json = response.text
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {e}\nRaw: {raw_json[:500]}")

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
        raw_content     = transcript_safe,
        source_url      = source_url,
        source_filename = source_filename,
    )

    entry.validate()

    logger.info(
        f"Extraction complete: '{entry.technique_name}' "
        f"({entry.category}, {entry.skill_level}), "
        f"{len(entry.step_by_step)} steps"
    )
    return entry
