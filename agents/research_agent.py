"""
agents/research_agent.py
Research & Answer Agent — ADK 2.7.1
Answers craft questions by searching the knowledge base, then falling back
to trusted web sources. Stores every Q&A as a qa_pair for the flywheel.

Usage (from main.py):
    run_research_agent(question="How do I sharpen a bowl gouge?")
"""

import os
import sys
import logging
import asyncio

sys.path.insert(0, "D:/TheCraftersHub_DataLab/agent_agentic_hackathon")

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from agents.tools.storage import generate_embedding, store_qa_pair
from agents.tools.search import search_combined
from agents.tools.web_search import search_trusted_sources

logger = logging.getLogger(__name__)


# ── Tool functions ─────────────────────────────────────────────────────────────

def tool_search_knowledge_base(question: str) -> dict:
    """
    Search The Crafters Hub knowledge base and lesson library for relevant answers.
    Searches both teacher_student_knowledge (lessons) and knowledge_base (curated Q&A).

    Args:
        question: The woodworking question to search for.

    Returns:
        dict with 'results' (list of matches with score and snippet) and 'count' (int).
    """
    embedding = generate_embedding(question)
    results   = search_combined(embedding, top_k=5, query_text=question)

    # Filter to only relevant results (score > 0.6)
    relevant = [r for r in results if r.get("score", 0) > 0.60]

    return {
        "results": relevant,
        "count":   len(relevant),
        "searched": "teacher_student_knowledge + knowledge_base",
    }


def tool_search_trusted_web(question: str) -> dict:
    """
    Search pre-approved woodworking websites for additional information.
    Only queries: AAW, Popular Woodworking, Woodcraft Magazine.
    Never queries the open internet.

    Args:
        question: The woodworking question to search for.

    Returns:
        dict with 'results' (list of web snippets) and 'count' (int).
    """
    results = search_trusted_sources(question, top_n=3)
    return {
        "results": results,
        "count":   len(results),
        "sources": [r["source_name"] for r in results],
    }


def tool_store_qa_answer(question: str, answer: str, confidence: str, sources: list) -> dict:
    """
    Store a verified Q&A pair in the knowledge base to grow the flywheel.

    Args:
        question:   The question that was answered.
        answer:     The complete, verified answer.
        confidence: 'kb_match' (from our DB), 'web_source' (from trusted web), or 'synthesized'.
        sources:    List of source names used.

    Returns:
        dict with 'row_id' (int) confirming storage.
    """
    embed_text = f"Q: {question} A: {answer}"
    embedding  = generate_embedding(embed_text)
    row_id     = store_qa_pair(
        question=question,
        answer=answer,
        embedding=embedding,
        confidence_level=confidence,
        sources=sources,
    )
    return {"row_id": row_id, "stored": True}


# ── ADK Agent definition ───────────────────────────────────────────────────────

RESEARCH_AGENT = Agent(
    name="craft_research_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
    description=(
        "Answers woodworking and woodturning questions by searching The Crafters Hub "
        "knowledge base and trusted web sources. Stores all Q&A pairs to grow the knowledge flywheel."
    ),
    instruction="""You are the Craft Research Agent for The Crafters Hub — a woodworking school in Cairo, Egypt.

Answer woodworking and woodturning questions accurately, using only trusted sources.

Workflow (STRICTLY follow this order):
1. Call tool_search_knowledge_base with the question.
   - If count > 0 and best score > 0.75: USE that answer. Set confidence='kb_match'.
   - If count > 0 but score 0.60-0.75: Use as partial context, also check web.
   - If count = 0: Proceed to web search.

2. If needed, call tool_search_trusted_web with the question.
   - Synthesize the web snippets into a clear, practical answer.
   - Set confidence='web_source'.

3. If both return nothing useful: Synthesize from your own woodworking knowledge.
   - Set confidence='synthesized'. Be clear you are drawing on general knowledge.

4. Always call tool_store_qa_answer with the final answer BEFORE responding to the user.
   This is mandatory — it grows the knowledge flywheel.

5. Respond to the user with:
   - A clear, practical answer (3-8 sentences for simple questions, step-by-step for techniques)
   - Source credit (e.g. "Source: Cabinet Knowledge Base" or "Source: AAW, Popular Woodworking")
   - Safety warnings if relevant

Rules:
- Never invent tool or material names
- Always include safety information for turning/cutting operations
- Answer in English unless the question is in Arabic
- Do NOT call tool_store_qa_answer more than once per question""",
    tools=[
        FunctionTool(tool_search_knowledge_base),
        FunctionTool(tool_search_trusted_web),
        FunctionTool(tool_store_qa_answer),
    ],
)


# ── Public runner function ─────────────────────────────────────────────────────

def run_research_agent(question: str) -> str:
    """
    Run the Research Agent for a given question.

    Args:
        question: Woodworking question in English or Arabic.

    Returns:
        Agent's final answer as a string.
    """
    from dotenv import load_dotenv
    load_dotenv("D:/TheCraftersHub_DataLab/.env")

    session_service = InMemorySessionService()
    runner = Runner(
        agent=RESEARCH_AGENT,
        app_name="tch_research",
        session_service=session_service,
    )

    async def _run():
        session = await session_service.create_session(
            app_name="tch_research",
            user_id="student",
        )
        message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=question)]
        )
        final_response = ""
        async for event in runner.run_async(
            user_id="student",
            session_id=session.id,
            new_message=message,
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        final_response += part.text
        return final_response

    return asyncio.run(_run())
