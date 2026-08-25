# The Cabinet — Agentic Suite

> *Built for The Crafters Hub — a woodworking and woodturning school in El Shorouk City, Cairo, Egypt.*

## The Problem

The Crafters Hub was co-founded by Hosam Elshanawany and Mostafa Fahmy. Mostafa is the woodworking master — the cornerstone of the workshop, the person who made the craft culture real. He is currently in a severe coma and unable to teach. The workshop's physical operations are paused.

The knowledge built together over years — in lessons, in conversations, in hours of answering students' WhatsApp questions — lives in The Cabinet's knowledge base. This project keeps that knowledge alive, growing, and reachable for the students who still need it.

## What We Built

**The Cabinet Agentic Suite** is a three-agent system powered by Google ADK 2.7.1 and Gemini 3.6 Flash, running entirely on-premise at The Crafters Hub.

| Agent | What It Does |
|---|---|
| **Lesson Ingest Agent** | Fetches a YouTube transcript or transcribes a local video, extracts structured craft knowledge using Gemini's structured output API, embeds it with gemini-embedding-2, and stores it in PostgreSQL. |
| **Research & Answer Agent** | Answers woodworking questions by searching the knowledge base first, falling back to pre-approved trusted websites, synthesizing a sourced answer — and storing every Q&A back in the DB (the Knowledge Flywheel). |
| **Finance Sentinel Agent** | Scans unmatched income transactions, finds the best student match, and sends a WhatsApp approval request to Hosam. Never auto-modifies finance data. |

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system diagram and data flow.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/The-Crafters-Hub/cabinet-agentic-suite
cd cabinet-agentic-suite

# 2. Install
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env — add GEMINI_API_KEY, PostgreSQL credentials, Meta WhatsApp token

# 4. Run DB migration
python db/run_migration.py

# 5. Ingest a lesson (Stuart Batty YouTube)
python main.py ingest --source "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"

# 6. Ask a craft question
python main.py research --question "What wood is best for beginner bowl turning?"

# 7. Run Finance Sentinel
python main.py sentinel --days 7

# 8. Verify DB
python main.py test-db
```

## Tech Stack

| Component | Technology |
|---|---|
| Agent Framework | Google ADK 2.7.1 |
| LLM / Extraction | Gemini 3.6 Flash (`gemini-3.6-flash`) |
| Embeddings | `gemini-embedding-2` (3072-dim) |
| Database | PostgreSQL 16 + pgvector |
| Transcription | YouTube Transcript API + Faster-Whisper (local) |
| Notifications | Meta WhatsApp Cloud API v20.0 |
| Runtime | Python 3.13.7 |

## The Knowledge Flywheel

Every question answered by the Research Agent is stored back in the database as a `qa_pair`. The next time a similar question is asked, it retrieves the stored answer instead of calling Gemini again — reducing cost and improving response time. Over time, the system gets smarter from its own usage.

```
YouTube Video → Transcript → Gemini Extraction → PostgreSQL
                                                      ↓
Student Question → Embedding Search → Stored Answer (if exists)
                                    → Gemini + Web (if new) → Store Answer
```

## Finance Sentinel — Human in the Loop

The Sentinel never auto-approves or auto-modifies any financial record. Its complete loop:

1. Reads `finance_transactions` (READ ONLY)
2. Finds the best student match by amount delta
3. Sends WhatsApp message to Hosam: *"Reply APPROVE-{id} or REJECT-{id}"*
4. Hosam replies manually
5. Nothing is written until Hosam approves

## Live Results (as of Aug 24, 2026)

- 553 existing knowledge base entries (built over 2 years)
- First Q&A pair stored by the Research Agent: `id=1`
- DB now has 5 lesson entries in `teacher_student_knowledge` after ingesting real woodturning videos
- Finance Sentinel configured and tested against production finance DB (487 rows)
- All three agents importing and running cleanly on Python 3.13.7
- GCS caching layer active — re-submitting a known video takes <2 seconds at $0 cost

## About

Built by **Hosam Elshanawany** and **HAMADA** — for Mostafa, for the community, for the craft.  
Co-founders: Hosam Elshanawany & Mostafa Fahmy  
Website: [the-crafters-hub.com](https://the-crafters-hub.com)  
Phone: +20 111 377 6666

## License

MIT
