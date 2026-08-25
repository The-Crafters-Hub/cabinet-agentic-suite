# Demo Video Script — The Cabinet Agentic Suite
> Duration: 3 minutes | Record: Aug 29, 2026 | Tools: OBS Studio or Win+G
> Use this EXACT script. No ad-libbing. One take if possible.

---

## Pre-recording Setup Checklist

- [ ] Terminal open in `D:\TheCraftersHub_DataLab\agent_agentic_hackathon\`
- [ ] Font size: 16pt minimum (legible on 1080p)
- [ ] `python main.py test-db` run once beforehand (confirm green)
- [ ] WhatsApp open on phone (to show notification arriving)
- [ ] VS Code open with `demo\sample_output.md` in preview mode
- [ ] Dark terminal background (Windows Terminal, Dark theme)
- [ ] Record at 1920x1080

---

## Scene-by-Scene Script

### Scene 1 — Title Card (0:00–0:25)
**[No voiceover. Title card on screen.]**

```
"When a master craftsman can't answer every question —
 who does?"

The Cabinet Agentic Suite
Built for The Crafters Hub, Cairo, Egypt
```

*Hold for 10 seconds. Fade to terminal.*

---

### Scene 2 — Ingest Agent (0:25–1:05)
**[Switch to terminal. Type slowly — let viewers read.]**

**Narrate:**
> "Our Lesson Ingest Agent fetches a Stuart Batty YouTube video, extracts structured knowledge using Gemini, and stores it — in under 90 seconds."

**Type:**
```bash
python main.py ingest --source "https://www.youtube.com/watch?v=c0ij507DEzU"
```

**[Let it run. Show the log lines appearing:]**
- `Fetching transcript for video ID...`
- `Transcript fetched: 5487 characters`
- `Extraction complete: 'Bench Grinder Sharpening Platform Setup'`
- `Stored video_extract: id=2`

**[Panel appears:]**
```
Technique: Bench Grinder Sharpening Platform Setup
Category: Woodturning | Skill Level: Beginner
Steps: 6 | Tools: 4
Database Row ID: 2
```

**Narrate:**
> "90 seconds. Stuart Batty's knowledge is now in our database."

---

### Scene 3 — Lesson Guide (1:05–1:40)
**[Switch to VS Code with `demo/sample_output.md` in preview.]**

**Narrate:**
> "Every ingested video becomes a structured lesson guide. Technique, materials, tools, step-by-step instructions, and safety warnings — extracted automatically."

**[Scroll slowly through the sample output, pausing on:]**
- The step-by-step section (6 numbered steps)
- The Safety callout box (highlighted in red)
- The Common Mistakes section

**Narrate:**
> "This is what Mostafa's students get — without Mostafa having to write a single word."

---

### Scene 4 — Research Agent (1:40–2:15)
**[Back to terminal.]**

**Narrate:**
> "The Research Agent answers craft questions — searching OUR knowledge base first, then trusted web sources, then synthesizing with Gemini. Every answer is stored back, growing the knowledge base automatically."

**Type:**
```bash
python main.py research --question "What platform system does Stuart Batty recommend for sharpening on a bench grinder?"
```

**[Show key log lines:]**
- `teacher_knowledge search: 2 results`
- `Stored qa_pair: id=3, confidence=kb_match`

**[Show the answer panel — highlight:]**
- "Source: The Crafters Hub Knowledge Base" ← point to this line
- The safety warning section

**Narrate:**
> "It found the answer in OUR database — not Gemini's general knowledge. The flywheel is working."

---

### Scene 5 — Finance Sentinel (2:15–2:40)
**[Terminal. Run sentinel. Have phone ready.] **

**Narrate:**
> "The Finance Sentinel scans unmatched payments and asks for Hosam's approval via WhatsApp — it never modifies the database without a human reply."

**Type:**
```bash
python main.py sentinel --days 7
```

**[Show phone receiving WhatsApp:]**
> "Finance Sentinel Alert — Reply APPROVE-{id} or REJECT-{id}"

**Narrate:**
> "Read-only scan. Human in the loop. Nothing is written without Hosam's explicit reply."

---

### Scene 5b — Cloud Run Proof (2:40–3:00)
**[Switch to browser. Open: https://console.cloud.google.com/run — show the `tch-ingest-backend` service.]**

**Narrate:**
> "The extraction backend runs on Google Cloud Run — fully serverless. Here is the live service. You can see the request count from the video we just ingested."

**[Scroll to show:]**
- Service name: `tch-ingest-backend`
- Region: `us-central1`
- Status: `READY`
- At least 1 recent request in the metrics chart

**Narrate:**
> "Every transcript extraction hits this endpoint. The result is stored in Google Cloud Storage, then pulled to the on-premise database."

---

### Scene 6 — Flywheel Proof + Closing (3:00–3:20)
**[Terminal. Quick DB query.]**

**Type:**
```bash
python main.py test-db
```

**[Show output:]**
```
[DB] teacher_student_knowledge rows: 3
[DB] knowledge_base rows: 553
```

**Narrate:**
> "Started at zero this morning. Three entries in the flywheel. Every question makes it smarter."

**[Fade to closing card:]**
```
Built by Hosam Elshanawany and HAMADA.
For Mostafa. For the community. For the craft.

The Crafters Hub — El Shorouk City, Cairo, Egypt
https://the-crafters-hub.com
```

---

## Post-Recording

1. Upload to YouTube as **PUBLIC** (not Unlisted — Devpost will reject unlisted videos)
2. Copy the URL
3. Add the URL to both:
   - `demo/submission_all_things_agentic.md` (Demo Video field)
   - `demo/submission_devnetwork.md` (Demo Video field)
4. You're ready to submit.
