# Devpost Submission — DevNetwork API+Cloud+AI
> Copy-paste ready. Submit at https://api-cloud-ai-hackathon-2026.devpost.com before **Sep 3, 2026 EOD**
> FRAMING: Lead with API stitching — not agents. This audience judges on API integration depth.

---

## Project Name
**The Cabinet Knowledge API — Stitching 7 APIs into a Self-Reinforcing Craft Intelligence Platform**

---

## Tagline
One codebase. 7 APIs. Zero new cloud costs. A woodworking school's YouTube lessons become searchable knowledge in 90 seconds — and every answer stores itself back for the next student.

---

## About the Project

### The API Integration Story

The Cabinet Knowledge API connects 7 distinct APIs into a single, production-grade intelligence pipeline for The Crafters Hub — a woodworking school in Cairo, Egypt. No new cloud infrastructure was provisioned. Every API is stitched onto the school's existing on-premise server via a Cloudflare Tunnel.

**The 8-API chain:**

```
YouTube Transcript API
        ↓
  Google Cloud Run (backend)
        ↓
  Gemini 3.6 Flash (generation)
        ↓
  Google Cloud Storage (bridge)
        ↓
  gemini-embedding-2 (embeddings)
        ↓
  PostgreSQL + pgvector (vector store)
        ↓
  Meta WhatsApp Cloud API v20.0 (notifications)
        ↓
  Google ADK 2.7.1 (orchestration)
```

**How each API is used:**

| API | How we use it | Why it matters |
|---|---|---|
| **Google Cloud Run** | Hosts the FastAPI extraction backend | Serverless, scales to zero, runs heavy AI workloads off-premise |
| **Google Cloud Storage** | Bridge storage for the extracted JSON payload | Secure handoff between the cloud and the on-premise database |
| **YouTube Transcript API** | Fetches captions from any YouTube video in <2 sec — no browser, no scraping | Zero-cost content ingestion from world-class instructors |
| **Gemini 3.6 Flash** | Structured output extraction of craft knowledge + answer synthesis | $0.001/request for a full lesson extraction |
| **gemini-embedding-2** | 3072-dim vectors for semantic similarity search | Finds the right answer even when the exact words don't match |
| **PostgreSQL pgvector** | Cosine similarity search on `teacher_student_knowledge` table | On-premise, zero latency, zero hosting cost |
| **Meta WhatsApp Cloud API** | Finance Sentinel sends approval requests; student answers delivered via WhatsApp | The school already runs on WhatsApp — zero adoption friction |
| **Google ADK 2.7.1** | Orchestrates 3 autonomous agents with FunctionTool registration and async streaming | Replaces brittle LangChain-style chains with a production-ready agent framework |

### Hybrid Cloud + Edge Architecture

The system makes a deliberate, optimized split between cloud and edge:

**Cloud (Google Cloud Run + GCS + Gemini API):** Knowledge extraction, answer synthesis, embedding generation. A Cloud Run FastAPI service handles the heavy lifting, dumping the structured JSON to Google Cloud Storage.

**Edge (on-premise server):** PostgreSQL + pgvector, Faster-Whisper local transcription, WhatsApp webhook receiver. The local ADK agent reads from GCS and stores it securely locally. Everything that needs persistence runs on the school's own hardware.

**Why this matters:** A school in Cairo cannot absorb $200/month in cloud database costs. Running pgvector on-premise means the entire vector search layer costs $0 in hosting. Faster-Whisper runs on a Quadro P1000 GPU at 5 tokens/second — local video workshops are transcribed for free.

### The Self-Reinforcing Loop

The most important API interaction is the feedback loop between Gemini's generation and pgvector's retrieval:

1. Student asks a question → `gemini-embedding-2` embeds the question (3072 dims)
2. pgvector searches existing answers → returns top matches by cosine similarity
3. If score > 0.75: return stored answer. **No Gemini generation call.** Zero cost.
4. If score < 0.75: Gemini synthesizes answer → `gemini-embedding-2` embeds it → stored back
5. Next identical question: instant retrieval, zero API cost

**Measured result:** The first Stuart Batty video ingested produced a KB hit on the very next research query at `kb_match` confidence — sourced from our database, not Gemini general knowledge.

### Finance Sentinel — WhatsApp as an Approval API

The Finance Sentinel demonstrates a non-standard use of the WhatsApp API: as a **human-in-the-loop approval channel.** When the Sentinel finds an unmatched payment that matches a student enrollment by amount delta (≥60% confidence), it sends:

> *"Reply APPROVE-{id} or REJECT-{id}"*

No database record is modified until Hosam replies. This replaces a spreadsheet review process that previously took 2-3 hours per week.

### Live Results (August 24, 2026)
- 553 production KB entries searchable via pgvector
- First YouTube video ingested in 90 seconds end-to-end (transcript → Gemini → embed → DB)
- First Q&A flywheel loop completed — `kb_match` on second query
- Finance Sentinel scanning production `finance_transactions` table (READ ONLY, 487 rows)

---

## Technologies Used

- Google Agent Development Kit (ADK) 2.7.1
- Google Cloud Run
- Google Cloud Storage
- Gemini 3.6 Flash (`gemini-3.6-flash`)
- Gemini Embedding 2 (`gemini-embedding-2`, 3072-dim)
- PostgreSQL 16 + pgvector
- YouTube Transcript API 1.2.4
- Faster-Whisper ≥1.0.0 (local GPU transcription)
- Meta WhatsApp Cloud API v20.0
- Python 3.13.7
- psycopg2-binary 2.9.11
- Rich 13.9.4

---

## Prior Work Disclosure

The Cabinet infrastructure — 16 Docker containers, PostgreSQL "Iron Vault" database, n8n automation platform, Cloudflare tunnel, and the 553-entry knowledge base — was built for the Build with Gemini XPRIZE hackathon (May–August 2026). That project is documented and submitted separately.

**The three ADK agents** (Lesson Ingest Agent, Research & Answer Agent, Finance Sentinel), the `teacher_student_knowledge` database table, all tool modules (`transcript.py`, `extraction.py`, `storage.py`, `search.py`, `web_search.py`, `whatsapp.py`), and the `main.py` CLI were built **exclusively during this hackathon's August 4–31 window.** The agents read from but do not modify the pre-existing Cabinet infrastructure.

---

## Demo Video
[Add YouTube URL after recording on Aug 29]

---

## GitHub Repository
https://github.com/The-Crafters-Hub/the-cabinet/tree/main/agent_agentic_hackathon

---

## Team Members
- Hosam Elshanawany — Co-founder, The Crafters Hub
- HAMADA (AI Agent) — Built with Antigravity + Gemini
