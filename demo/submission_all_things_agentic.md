# Devpost Submission — All Things Agentic Hackathon
> Filed in exact form order. Character counts shown per field.
> Submit at: https://all-things-agentic.devpost.com

---

## STEP 1 — Project Overview

---

### * Project name
> Limit: 60 characters

```
The Cabinet Agentic Suite
```
✅ 25 characters

---

### * Elevator pitch
> Limit: 200 characters

```
Three autonomous agents that keep a woodworking school's knowledge alive and its books clean — one ingests lessons, one answers questions, one guards the finances.
```
✅ 165 characters

---

## STEP 2 — Project Details

---

### * About the project
> Markdown. Sections: Inspiration, What it does, How we built it, Challenges, Accomplishments, What we learned, What's next.

```markdown
## Inspiration

The Crafters Hub is a woodworking and woodturning school in El Shorouk City, Cairo, Egypt — co-founded by Hosam Elshanawany and Mostafa Fahmy. Mostafa is the woodworking master, the cornerstone of the workshop, the person who made the craft culture real. He is currently in a severe coma and unable to teach. The workshop's physical operations are paused.

The knowledge built together over years — in lessons, in conversations, in hours of answering students' WhatsApp questions — lives in The Cabinet's knowledge base: 553 entries, live in PostgreSQL. This project keeps that knowledge alive, growing, and reachable for the students who still need it.

## What it does

The Cabinet Agentic Suite is a three-agent system built with Google ADK 2.7.1:

**Agent 1 — Lesson Ingest Agent (Hybrid Cloud):** Fetches a YouTube transcript via our Google Cloud Run microservice in under 2 seconds. The Cloud Run service sends it to Gemini 3.6 Flash with a structured output schema, extracts the knowledge (technique, tools, safety, steps), and stores the JSON payload directly into a Google Cloud Storage (GCS) bucket. The local agent then reads the GCS bucket, generates a 3072-dim vector with gemini-embedding-2, and stores it in the on-premise PostgreSQL database.

**Agent 2 — Research & Answer Agent:** Answers woodworking questions from teachers and students. It searches the ingested knowledge base first (pgvector cosine similarity), falls back to pre-approved trusted websites (AAW, Popular Woodworking), then synthesizes using Gemini. Every answer is stored back in the database as a Q&A pair — this is the Knowledge Flywheel. The second time a similar question arrives, it is answered from local storage in milliseconds at zero API cost.

**Agent 3 — Finance Sentinel:** Scans the school's production finance database (READ ONLY) for unmatched income transactions and matches them to student enrollment records by amount delta. When confidence exceeds 60%, it sends a WhatsApp message to Hosam via Meta's Cloud API: "Reply APPROVE-{id} or REJECT-{id}." It never auto-modifies a single financial record. Human approval is required for every write.

## How we built it

- **Google Cloud Run** — Serverless hosting for the AI extraction backend (FastAPI)
- **Google Cloud Storage** — Bridge storage between the cloud extraction service and the on-premise database
- **Google ADK 2.7.1** — `Agent` class + `@tool` decorator + `Runner.run_async()` for orchestration
- **Gemini 3.6 Flash** — structured knowledge extraction (JSON schema output) + answer synthesis
- **gemini-embedding-2** — 3072-dim vectors for semantic similarity search
- **PostgreSQL + pgvector** — on-premise vector store, zero hosting cost
- **YouTube Transcript API 1.2.4** — transcript fetching without a browser or scraping
- **Faster-Whisper** — local video transcription at $0 (runs on school's Quadro P1000 GPU)
- **Meta WhatsApp Cloud API v20.0** — human-in-the-loop approval channel for Finance Sentinel
- **Python 3.13.7 / psycopg2 / Rich CLI**

The system uses a true Hybrid Cloud architecture: heavy AI workloads run on Google Cloud Run and GCS, while the vector database stays on the school's own on-premise server.

## Challenges we ran into

- **pgvector index dimension cap:** Both `ivfflat` and `hnsw` index types cap at 2000 dimensions in our pgvector version. `gemini-embedding-2` outputs 3072 dimensions. Solution: drop the index and use sequential cosine scan (fast enough at <10K rows for the demo window; index can be added post-competition after a pgvector upgrade).
- **youtube-transcript-api v1.2.4 API change:** The library moved from a static class API (`YouTubeTranscriptApi.get_transcript()`) to an instance-based API (`YouTubeTranscriptApi().list(video_id).find_transcript(...).fetch()`). Discovered and fixed during E2E testing.
- **Windows console encoding:** Python's `rich` library on a Windows cp1256 console raises `UnicodeEncodeError` on emoji. Replaced all emoji with ASCII tags throughout the CLI.

## Accomplishments that we're proud of

- First YouTube video ingested end-to-end in **90 seconds** (transcript → Gemini extraction → embedding → PostgreSQL)
- First research query after ingestion returned **`kb_match` confidence** — answered from OUR database, not Gemini general knowledge, on the very first try
- The Knowledge Flywheel reached **3 Q&A pairs** in the first two hours of live operation
- Finance Sentinel is scanning the school's **real production finance table** (487 rows) in read-only mode — no test data

## What we learned

- ADK 2.7.1's `@tool` decorator with typed Python functions produces clean, Gemini-compatible JSON schema with minimal boilerplate
- `gemini-embedding-2` is significantly more capable than `text-embedding-004` but emits 3072-dim vectors — any system assuming 768 dimensions will silently corrupt its vector store
- The human-in-the-loop pattern via WhatsApp is more practical for a small school than any dashboard approval UI — Hosam is always on his phone, never always at a computer

## What's next

- Ingest the full Stuart Batty YouTube back-catalogue (~200 videos) to build a comprehensive woodturning knowledge base
- Add a WhatsApp-facing research endpoint so students can ask questions directly in WhatsApp and get sourced answers
- Add the Finance Sentinel approval handler (the write side of the loop — currently only the read + alert side is built)
- Open-source the agent templates as a starter kit for other artisan schools in MENA
```

---

### * Built with
> Up to 25 tags — enter each as a separate tag

```
Google ADK
Gemini 3.6 Flash
gemini-embedding-2
Google Cloud Run
Google Cloud Storage
google-genai
pgvector
PostgreSQL
Python
YouTube Transcript API
Faster-Whisper
Meta WhatsApp Cloud API
psycopg2
Rich
```
✅ 14 tags

---

### "Try it out" links

```
https://github.com/The-Crafters-Hub/cabinet-agentic-suite
```

---

### * Video demo link
> YouTube, Facebook Video, Vimeo or Youku URL

```
[Add after recording Aug 29 — upload as PUBLIC, not unlisted. ~3 min.]
```

---

## STEP 3 — Additional Info

---

### Sponsor / Special Prizes
```
[ ] Startup Excellence  ← skip unless Hosam opts in with corporate email
```

---

### * Submitter Type
```
Individual
```
*(or "Organization" if opting in for Startup Prize)*

---

### * Submitter country of residence
```
Egypt
```

---

### * Which Category are you submitting to?
> Check the current category list on the form — select the one matching multi-agent / agentic systems

```
Fortified Enterprise Fleet
```

---

### * If submitting on behalf of an Organization, what is the Organization name?
```
The Crafters Hub
```

---

### * What date did you start this project?
> Format: MM-DD-YY | Must be within submission period

```
08-18-26
```
*(August 18, 2026 — started immediately after submitting the Gemini API XPrize)*

---

### * URL to your public or private code repo
> If private, share with testing@devpost.com and cloudhackathons@google.com

```
https://github.com/The-Crafters-Hub/cabinet-agentic-suite
```

---

### * Did you add Reproducible Testing instructions to your README?
```
Yes
```

---

### Hosted project URL (optional)
```
[Leave blank — system runs on-premise, not publicly hosted]
```

---

### Testing instructions (judges only, not public)
```
See README.md.
1. git clone repo & cd cabinet-agentic-suite
2. pip install -r requirements.txt
3. cp .env.example .env & add GEMINI_API_KEY and DATABASE_URL
4. python main.py test-db
5. python main.py research -q "wood glue"
```

---

### * Which Google SDK did you use?
```
[x] Agent Development Kit (ADK)
[x] Google GenAI SDK (google-genai)
```

---

### * Which Google Cloud Service(s) did you use?
> ⚠️ REQUIRED: At least one. 

```
[x] Cloud Run
```
*(Our extraction backend runs on Cloud Run and uses Cloud Storage)*

---

```
ARCHITECTURE.png (rendered from Mermaid — file in repo root. Upload this file directly to the Devpost form.)
```

---

### * Which Google AI Models did you use?
> Gemini 3.5 or newer is REQUIRED

```
gemini-3.6-flash (generation + structured output + synthesis)
gemini-embedding-2 (3072-dim semantic embeddings)
```

---

### OPTIONAL — Bonus Points: Content piece
```
[Leave blank unless Hosam writes a blog post about the project]
```

---

### OPTIONAL — Bonus Points: Social media post
> Must include #AllThingsAgenticHackathon

```
[Optional: post on X or LinkedIn with #AllThingsAgenticHackathon before submitting]
```

---

## ⚠️ Pre-Submit Checklist (from Devpost's own final reminder)

- [ ] Gemini 3.5 or newer ✅ (`gemini-3.6-flash`)
- [ ] A Google agent framework ✅ (ADK 2.7.1)
- [ ] At least one Google Cloud service ✅ (Gemini API / Generative Language API)
- [ ] Category selected on form
- [ ] Text description filled (About the project)
- [ ] Code repo link is public (or shared with testing@devpost.com)
- [ ] README has spin-up instructions
- [ ] Architecture diagram uploaded as PNG/PDF
- [ ] Demo video is PUBLIC on YouTube (~3 min), shows agent working
- [ ] Start date entered as 08-18-26
- [ ] All team members have ACCEPTED their invite (not just added)
- [ ] Prior work disclosed in About section ✅ (XPRIZE infrastructure vs. new agents)
