"""
agents/tools/search.py
Semantic search over:
  1. teacher_student_knowledge (our new hackathon table)
  2. knowledge_base (Cabinet production table — READ ONLY)

Public functions:
    search_teacher_knowledge(query_embedding, top_k=5) -> list[dict]
    search_cabinet_kb(query_embedding, top_k=5) -> list[dict]
    search_combined(query_embedding, top_k=5) -> list[dict]
"""

import logging
import sys

sys.path.insert(0, "D:/TheCraftersHub_DataLab/agent_agentic_hackathon")

logger = logging.getLogger(__name__)


def search_teacher_knowledge(query_embedding: list[float], top_k: int = 5) -> list[dict]:
    """
    Semantic search on teacher_student_knowledge using cosine similarity.

    Args:
        query_embedding: 768-dim query vector.
        top_k:           Number of results to return.

    Returns:
        List of dicts: {id, content_type, technique_name, question, raw_content, score}
    """
    from db.connection import get_connection

    sql = """
        SELECT
            id,
            content_type,
            technique_name,
            question,
            raw_content,
            1 - (embedding <=> %s::vector) AS score
        FROM teacher_student_knowledge
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """

    results = []
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (query_embedding, query_embedding, top_k))
                rows = cur.fetchall()
                for row in rows:
                    results.append({
                        "id":             row[0],
                        "content_type":   row[1],
                        "technique_name": row[2],
                        "question":       row[3],
                        "raw_content":    row[4][:800] if row[4] else "",  # truncate for context
                        "score":          float(row[5]) if row[5] else 0.0,
                        "source":         "teacher_student_knowledge",
                    })
    except Exception as e:
        logger.error(f"search_teacher_knowledge failed: {e}")

    logger.info(f"teacher_knowledge search: {len(results)} results")
    return results


def search_cabinet_kb(query_embedding: list[float], top_k: int = 5, query_text: str = "") -> list[dict]:
    """
    Text search on the Cabinet's knowledge_base table (553 entries).
    knowledge_base has no embedding column — uses ILIKE full-text search.
    query_text is used for matching; query_embedding is kept for API compatibility.

    Args:
        query_embedding: Ignored (no embedding in this table). Kept for API compat.
        top_k:           Number of results to return.
        query_text:      Search text (used for ILIKE matching).

    Returns:
        List of dicts: {id, title, content, category, score, source}
    """
    from db.connection import get_connection

    if not query_text:
        return []

    # Use ILIKE for keyword matching across title + content
    sql = """
        SELECT
            id,
            title,
            content,
            category,
            -- Simple relevance: title match scores higher
            CASE WHEN title ILIKE %(pattern)s THEN 0.85 ELSE 0.65 END AS score
        FROM knowledge_base
        WHERE
            is_active = TRUE
            AND (title ILIKE %(pattern)s OR content ILIKE %(pattern)s)
        ORDER BY score DESC
        LIMIT %(top_k)s
    """

    pattern = f"%{query_text}%"
    results = []
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, {"pattern": pattern, "top_k": top_k})
                rows = cur.fetchall()
                for row in rows:
                    results.append({
                        "id":       row[0],
                        "question": row[1],  # use title as question
                        "answer":   row[2][:600] if row[2] else "",
                        "category": row[3],
                        "score":    float(row[4]) if row[4] else 0.0,
                        "source":   "cabinet_knowledge_base",
                    })
    except Exception as e:
        logger.error(f"search_cabinet_kb failed: {e}")

    logger.info(f"cabinet_kb text search '{query_text}': {len(results)} results")
    return results



def search_combined(query_embedding: list[float], top_k: int = 5, query_text: str = "") -> list[dict]:
    """
    Search both tables and return top_k merged results ranked by score.

    Args:
        query_embedding: 3072-dim vector (for teacher_student_knowledge).
        top_k:           Total results to return (across both tables).
        query_text:      Raw question text (for knowledge_base ILIKE search).

    Returns:
        List of dicts sorted by score descending.
    """
    teacher_results = search_teacher_knowledge(query_embedding, top_k=top_k)
    kb_results      = search_cabinet_kb(query_embedding, top_k=top_k, query_text=query_text)

    combined = teacher_results + kb_results
    combined.sort(key=lambda x: x["score"], reverse=True)

    return combined[:top_k]
