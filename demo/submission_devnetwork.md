# Devpost Submission — DevNetwork API+Cloud+AI
> Copy-paste ready. Submit at https://api-cloud-ai-hackathon-2026.devpost.com before **Sep 3, 2026 EOD**
> FRAMING: Lead with API stitching — not agents. This audience judges on API integration depth.

---

## Project Name
**The Cabinet Knowledge API — Stitching 8 APIs into a Self-Reinforcing Craft Intelligence Platform**

---

## Tagline
One codebase. 8 APIs. Zero new cloud costs. A woodworking school's YouTube lessons become searchable knowledge in 90 seconds — and every answer stores itself back for the next student.

---

## About the Project

### Inspiration

We run a woodworking and woodturning school in Cairo. Between managing bookings, tracking finances, and answering student questions on WhatsApp, we were spending less time at the workbench and more time on admin. We had already built *The Cabinet* — an on-premise operations platform — as our internal backbone. But we needed it to think.

Then life dealt us a harder blow. My co-founder Mostafa Fahmy suffered a severe accident and is currently in a coma. Keeping the school running, keeping his craft alive, and giving him something to come back to — that became the fuel for this project.

### What it does

The Cabinet Knowledge API connects 8 distinct APIs into a single, self-reinforcing intelligence pipeline. A woodworking instructor's YouTube lesson becomes structured, searchable knowledge in 90 seconds — and every question a student asks teaches the system to answer faster the next time.

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

**The self-reinforcing loop:**

1. Student asks a question → `gemini-embedding-2` embeds it (3072 dims)
2. pgvector searches `teacher_student_knowledge` → returns top match by cosine similarity
3. If score > 0.75: return stored answer. **No Gemini generation call. Zero cost.**
4. If score < 0.75: Gemini synthesizes answer → embeds it → stored back to the table
5. Next identical question: instant retrieval, zero API cost

**Finance Sentinel — WhatsApp as a human-in-the-loop approval API:**

When the Sentinel finds an unmatched payment that aligns with a student enrollment (≥60% confidence), it sends:

> *"Reply APPROVE-{id} or REJECT-{id}"*

No database record is modified until Hosam replies. This replaces a spreadsheet review that previously took 2–3 hours per week.

### How we built it

The architecture makes a deliberate split between cloud and edge:

**Cloud (Google Cloud Run + GCS + Gemini API):** Knowledge extraction, answer synthesis, embedding generation. A Cloud Run FastAPI service handles the heavy lifting, dumping the structured JSON to Google Cloud Storage.

**Edge (on-premise server at the workshop):** PostgreSQL + pgvector, Faster-Whisper local transcription, WhatsApp webhook receiver. The local ADK agent reads from GCS and stores it securely on the school's own hardware.

A school in Cairo cannot absorb $200/month in cloud database costs. Running pgvector on-premise means the entire vector search layer costs $0 in hosting. Faster-Whisper runs on a Quadro P1000 GPU at 5 tokens/second — local video workshops are transcribed for free.

### Challenges we ran into

- **Hybrid cloud/edge coordination:** Getting the Cloud Run service to hand off to a local agent via GCS without a persistent cloud socket required careful state management.
- **pgvector schema alignment:** Ensuring the 3072-dim `gemini-embedding-2` vectors matched the live `teacher_student_knowledge` column definition exactly — a mismatch would silently corrupt all similarity scores.
- **WhatsApp as an approval channel:** Meta's Cloud API doesn't have a native "awaiting reply" state — we built the approval handshake entirely in the Finance Sentinel agent logic.

### Accomplishments that we're proud of

- 8 APIs stitched into one coherent pipeline with zero new recurring cloud costs
- First YouTube video ingested end-to-end in **90 seconds** (transcript → Gemini → embed → DB)
- Self-reinforcing flywheel verified: `kb_match` on the second research query
- Finance Sentinel scanning production `finance_transactions` table (READ ONLY, 487 rows) with human approval gate live on WhatsApp
- 553 production KB entries in the school's pre-existing knowledge base, now queryable by the same agent

### What we learned

The biggest lesson: **the most important API call is the one you don't make.** Building the pgvector retrieval layer as the first gate — before any Gemini call — means the system gets cheaper every day it runs.

### What's next

- **Mass Ingestion of Internal Archives:** Use the Google Cloud credit to run a one-time mass ingestion of our own 3-year backlog of recorded workshop footage and authorized curriculum — permanently embedding hundreds of hours of domain knowledge on our local server at zero recurring cost.
- **Human-in-the-loop WhatsApp Research:** Wire the Research Agent into our WhatsApp pipeline as a "co-pilot" for instructors. When a student asks a complex question, the Agent will silently draft a fully researched, perfectly formatted response based on the Knowledge Base, allowing the human instructor to review, edit, and send it with one tap.
- Package The Cabinet as a licensable SaaS for other craft schools in MENA.

### Live Results (August 24, 2026)
- 553 production KB entries in `knowledge_base`
- `teacher_student_knowledge` table live with 3072-dim pgvector embeddings (hackathon flywheel)
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
https://github.com/The-Crafters-Hub/cabinet-agentic-suite

---

## Team Members
- Hosam Elshanawany — Co-founder, The Crafters Hub
- HAMADA (AI Agent) — Built with Antigravity + Gemini
