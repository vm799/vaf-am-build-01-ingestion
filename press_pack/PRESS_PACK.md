# BUILD 01 — PRESS PACK
**VAF AM Series | Multi-Source Data Ingestion**
*Built with Claude AI + Anthropic Agents | Asset Management*

---

## LINKEDIN POST

**HOOK (first 2 lines — must stop the scroll):**

> Asset managers spend 60% of analyst time gathering data before any analysis.
> I built the pipeline that does it in 30 seconds. Here's how. 🧵

---

**FULL POST:**

---

I'm a finance professional who taught herself to build AI agents.

This week I'm sharing 9 atomic AI builds — each one solving a real problem in asset management.

**Day 1: Multi-Source Data Ingestion**

Every morning, analysts manually check:
— FT headlines
— Reuters feeds
— Earnings transcripts
— FCA announcements
— Fund documents

Before making a single investment decision.

That's 60–90 minutes of mechanical work applied to expensive human time.

I built a pipeline that does all of it in 30 seconds.

Here's the architecture:

**3 sources. 1 pipeline. Running in parallel.**

```
RSS feeds    → feedparser
PDF docs     → pdfplumber  
Web URLs     → httpx
    │
    ▼
All run simultaneously via asyncio.gather()
    │
    ▼
Claude API → 3-sentence summary per document
    │
    ▼
SQLite store → structured JSON report
```

What I used:
→ Python (asyncio for parallelism)
→ Claude API (Anthropic) for summarisation
→ pdfplumber for PDF extraction
→ feedparser for RSS
→ SQLite for local storage

The key principle: **one source failing never halts the pipeline.**

If Reuters is down, the FT feed and the PDF still run. Return exceptions, don't raise them.

This is Build 01 of 9 this week.

Each build = 2 hours to ship + a demo video.

Each one solves a specific asset management problem.

Tomorrow: giving AI a memory. RAG for fund documents and DDQs.

Follow for daily builds all week. 👇

---

**#AssetManagement #AIinFinance #BuildInPublic #ClaudeAI #AnthropicAI #FinanceAI #AgenticAI #Python**

---

**POST NOTES:**
- Post time: Monday 07:00 GMT
- Image: terminal screenshot showing 3 sources ingesting in parallel
- Tag: @Anthropic in the post
- Add architecture diagram as first comment

---

## VIDEO SCRIPT

**Title:** "I Built the Data Pipeline That Saves AM Analysts 90 Minutes Every Morning"
**Length:** 3–4 minutes
**Format:** Screen recording + talking head overlay (or just screen)
**Platform:** LinkedIn native video + YouTube Shorts cut

---

### [00:00–00:20] HOOK

*Face to camera or voice-over terminal*

"Asset managers and analysts spend 60% of their morning gathering data before they can make a single investment decision. Today I'm showing you how I built the pipeline that changes that — in about 2 hours — using Claude AI and Python."

---

### [00:20–01:00] THE PROBLEM

*Show terminal or slides*

"Here's the problem. Every morning, someone is manually checking FT, Reuters, earnings transcripts, FCA releases. That's mechanical work. It doesn't require a senior analyst. But it's taking up their morning.

The solution: an ingestion pipeline that pulls from multiple sources simultaneously. Not one after another — at the same time. Parallel execution."

---

### [01:00–02:30] THE BUILD — LIVE DEMO

*Terminal recording*

"Let me show you what I built. This is the entrypoint — `run.py`. When I call this, three ingesters launch simultaneously using Python's asyncio.gather.

*[type: `uv run python run.py`]*

Watch the terminal — you can see RSS, PDF, and web ingestion all running at the same time. That's the key. One source failing doesn't stop the others — I'm using `return_exceptions=True`.

Now each document gets summarised by Claude API — three sentences, written for an asset manager. Specific. With numbers and dates.

*[show output appearing]*

And here's the output — structured JSON. Every document has a source type, title, summary, and metadata. Ready for the next agent to process."

---

### [02:30–03:30] THE AM ANGLE

"Why does this matter for asset management? Because this is the foundation layer. You can't have AI research agents, compliance checkers, or morning briefings without reliable data ingestion. This is the infrastructure that everything else runs on.

Built with Claude AI and Anthropic's agent patterns. Local-first — no data leaves your infrastructure. Audit log of everything ingested. One source failing never halts the pipeline."

---

### [03:30–04:00] CLOSE + CTA

"This is Build 01 of 9 this week. Tomorrow: RAG — giving AI a memory from your fund documents and DDQs so it can answer any question from your internal document corpus.

Follow for daily builds. Link to the full code in the comments. Built using Claude AI — the architecture pattern that's powering the most sophisticated personal AI systems in the world right now."

---

## THUMBNAIL BRIEF

**Visual concept:** Split screen
- LEFT: Messy desk with multiple browser tabs, papers, coffee cup (the problem)
- RIGHT: Clean terminal with green checkmarks running (the solution)

**Text overlay:** "90 min → 30 seconds" in bold

**Brand elements:** VAF logo + "Built with Claude AI"

**Colour palette:** Dark background, green terminal text, white type

---

## RECORDING CHECKLIST

Before you hit record:
- [ ] Terminal font size: 18pt minimum (readable on mobile)
- [ ] Dark terminal theme (looks professional on video)
- [ ] `.env` file closed / not visible during recording
- [ ] Test run `python run.py` once so you know it works before filming
- [ ] Add "Built with Claude AI + Anthropic" watermark to screen
- [ ] Record in 1080p minimum

After recording:
- [ ] Add intro text card: "VAF AM Series | Build 01 of 9"
- [ ] Add end card: "Follow for daily builds"
- [ ] Caption the video (LinkedIn auto-captions or Descript)
- [ ] Export: LinkedIn native + YouTube Shorts cut (60s highlight)

---

*VAF AM Series | Vaishali Mehmi | github.com/vm799*
*Built with Claude AI + Anthropic Agents*
