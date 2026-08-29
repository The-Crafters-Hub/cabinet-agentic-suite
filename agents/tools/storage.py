"""
agents/tools/storage.py
DB read/write for teacher_student_knowledge table.
Also handles embedding generation via gemini-embedding-2.

Public functions:
    generate_embedding(text: str) -> list[float]
    store_knowledge_entry(entry_dict: dict, embedding: list[float]) -> int
    store_qa_pair(question, answer, embedding, confidence_level, sources) -> int
"""

import os
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional

from dotenv import load_dotenv
from google import genai

load_dotenv()

logger = logging.getLogger(__name__)

# ── Gemini client ─────────────────────────────────────────────────────────────
_client: genai.Client | None = None

def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY not set in .env")
        _client = genai.Client(api_key=api_key)
    return _client

EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")
MAX_EMBED_CHARS = 2000  # truncate before embedding to stay within token limits
EMBEDDING_DIM   = 3072  # gemini-embedding-2 actual output dimension


# ── KnowledgeEntry dataclass ──────────────────────────────────────────────────
@dataclass
class KnowledgeEntry:
    """Structured craft knowledge extracted from a video transcript."""
    technique_name:   str
    category:         str                     # e.g. "woodturning", "joinery", "finishing"
    materials:        list[str]               = field(default_factory=list)
    tools:            list[str]               = field(default_factory=list)
    safety_notes:     str                     = ""
    skill_level:      str                     = "beginner"  # beginner|intermediate|advanced
    step_by_step:     list[str]               = field(default_factory=list)
    key_concepts:     list[str]               = field(default_factory=list)
    common_mistakes:  list[str]               = field(default_factory=list)
    raw_content:      str                     = ""
    source_url:       Optional[str]           = None
    source_filename:  Optional[str]           = None

    def validate(self) -> None:
        """Raise ValueError if required fields are empty."""
        if not self.technique_name:
            raise ValueError("technique_name is required")
        if not self.category:
            raise ValueError("category is required")
        if not self.raw_content:
            raise ValueError("raw_content is required")
        valid_levels = {"beginner", "intermediate", "advanced"}
        if self.skill_level not in valid_levels:
            raise ValueError(f"skill_level must be one of {valid_levels}")


# ── Embedding generation ──────────────────────────────────────────────────────
def generate_embedding(text: str) -> list[float]:
    """
    Generate a 3072-dimensional embedding using gemini-embedding-2.

    Args:
        text: Text to embed. Truncated to MAX_EMBED_CHARS before sending.

    Returns:
        List of 3072 floats.
    """
    client = _get_client()
    text_truncated = text[:MAX_EMBED_CHARS]

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text_truncated,
    )

    embedding = response.embeddings[0].values
    if len(embedding) != EMBEDDING_DIM:
        logger.warning(f"Unexpected embedding dimension: {len(embedding)} (expected {EMBEDDING_DIM})")

    return list(embedding)


# ── DB write functions ────────────────────────────────────────────────────────
def store_knowledge_entry(entry: KnowledgeEntry | dict, embedding: list[float]) -> int:
    """
    INSERT a video_extract row into teacher_student_knowledge.

    Args:
        entry:     KnowledgeEntry instance or dict with the same keys.
        embedding: 768-dim embedding vector.

    Returns:
        New row ID.
    """
    import sys, os as _os
    sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))
    from db.connection import get_connection

    if isinstance(entry, dict):
        e = entry
    else:
        entry.validate()
        e = asdict(entry)

    sql = """
        INSERT INTO teacher_student_knowledge (
            content_type, source_url, source_filename,
            technique_name, category, materials, tools,
            safety_notes, skill_level, step_by_step,
            key_concepts, common_mistakes, raw_content, embedding
        ) VALUES (
            'video_extract', %(source_url)s, %(source_filename)s,
            %(technique_name)s, %(category)s, %(materials)s, %(tools)s,
            %(safety_notes)s, %(skill_level)s, %(step_by_step)s,
            %(key_concepts)s, %(common_mistakes)s, %(raw_content)s, %(embedding)s
        )
        ON CONFLICT (source_url)
        WHERE source_url IS NOT NULL AND content_type = 'video_extract'
        DO NOTHING
        RETURNING id
    """

    params = {
        "source_url":       e.get("source_url"),
        "source_filename":  e.get("source_filename"),
        "technique_name":   e.get("technique_name", ""),
        "category":         e.get("category", ""),
        "materials":        e.get("materials", []),
        "tools":            e.get("tools", []),
        "safety_notes":     e.get("safety_notes", ""),
        "skill_level":      e.get("skill_level", "beginner"),
        "step_by_step":     __import__("json").dumps(e.get("step_by_step", [])),
        "key_concepts":     e.get("key_concepts", []),
        "common_mistakes":  e.get("common_mistakes", []),
        "raw_content":      e.get("raw_content", ""),
        "embedding":        embedding,
    }

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            if row is None:
                logger.info(f"Duplicate video_extract skipped (source_url already exists): {e.get('source_url')}")
                return -1
            row_id = row[0]

    logger.info(f"Stored video_extract: id={row_id}, technique={e.get('technique_name')}")
    return row_id


def store_qa_pair(
    question: str,
    answer: str,
    embedding: list[float],
    confidence_level: str = "synthesized",
    sources: list[str] | None = None,
) -> int:
    """
    INSERT a qa_pair row into teacher_student_knowledge.

    Args:
        question:         The question asked.
        answer:           The synthesized answer.
        embedding:        768-dim embedding of the Q&A content.
        confidence_level: 'kb_match' | 'web_source' | 'synthesized'
        sources:          List of source names/URLs used.

    Returns:
        New row ID.
    """
    import sys, os as _os
    sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))
    from db.connection import get_connection

    valid_levels = {"kb_match", "web_source", "synthesized"}
    if confidence_level not in valid_levels:
        confidence_level = "synthesized"

    sources_str = ", ".join(sources) if sources else ""
    raw_content = f"Q: {question}\nA: {answer}\nSources: {sources_str}"

    sql = """
        INSERT INTO teacher_student_knowledge (
            content_type, question, answer,
            confidence_level, raw_content, embedding
        ) VALUES (
            'qa_pair', %(question)s, %(answer)s,
            %(confidence_level)s, %(raw_content)s, %(embedding)s
        )
        ON CONFLICT (question)
        WHERE question IS NOT NULL AND content_type = 'qa_pair'
        DO NOTHING
        RETURNING id
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, {
                "question":         question,
                "answer":           answer,
                "confidence_level": confidence_level,
                "raw_content":      raw_content,
                "embedding":        embedding,
            })
            row = cur.fetchone()
            if row is None:
                logger.info(f"Duplicate qa_pair skipped for question: {question[:60]}")
                return -1
            row_id = row[0]

    logger.info(f"Stored qa_pair: id={row_id}, confidence={confidence_level}")
    return row_id
