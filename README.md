# BUILD 01 — Multi-Source Data Ingestion
**VAF AM Series | Day: Monday | Build Time: ~2 hours**
*Built with Claude AI + Anthropic Agents | Tailored for Asset Management*

---

## WHAT THIS BUILDS
A parallel data ingestion pipeline pulling from RSS news feeds, PDFs, and web URLs simultaneously. Every document normalised to a single schema. FCA-grade audit trail. Ready to feed any downstream AI agent.

## AM PAIN POINT SOLVED
Analysts spend 60–70% of their day gathering data before any analysis begins. This pipeline does that gathering in 30 seconds while they drink their coffee.

---

## PRD

### Problem
Asset managers and analysts manually aggregate data from FT, Reuters, earnings transcripts, FCA announcements, and fund documents. This is expensive human time applied to mechanical work.

### What We're Building
A multi-source ingestion pipeline: RSS feeds + PDFs + web URLs → normalised `IngestedDocument` schema → SQLite → ready for AI processing.

### Success Criteria
- [ ] Ingests from 3 source types in one `run.py` call
- [ ] All sources run in parallel (asyncio.gather)
- [ ] Output: structured JSON per document
- [ ] One source failing never halts the pipeline
- [ ] Under 30 seconds for 10 documents
- [ ] Audit log of everything ingested

### Non-Goals (v1)
- Bloomberg Terminal / Refinitiv authentication
- Real-time streaming
- Email ingestion

---

## TECHNICAL DESIGN

### Stack
```
Python 3.11 | anthropic | feedparser | pdfplumber | httpx | beautifulsoup4 | aiosqlite | pydantic
```

### Architecture
```
run.py
  └── asyncio.gather()
        ├── RSSIngester    (feedparser)
        ├── PDFIngester    (pdfplumber)
        └── WebIngester    (httpx + bs4)
              │
              ▼
        DocumentNormaliser
              │
              ▼
        ClaudeSummariser  (3-sentence summary per doc)
              │
              ▼
        SQLiteDocumentStore
              │
              ▼
        reports/ingestion_report.json
```

### File Structure
```
BUILD_01_INGESTION/
├── README.md              ← this file
├── PRD.md                 ← product requirements
├── .env.example
├── pyproject.toml
├── run.py                 ← ENTRYPOINT: python run.py
├── src/
│   ├── ingesters/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── rss.py
│   │   ├── pdf.py
│   │   └── web.py
│   ├── normaliser.py
│   ├── store.py
│   ├── summariser.py
│   └── config.py
├── skills/
│   └── ingestion/SKILL.md
├── data/
│   └── sample_earnings.pdf    ← sample PDF for demo
├── tests/
│   ├── test_rss.py
│   ├── test_pdf.py
│   └── test_web.py
└── press_pack/
    ├── LINKEDIN_POST.md
    ├── VIDEO_SCRIPT.md
    └── THUMBNAIL_BRIEF.md
```

### pyproject.toml
```toml
[project]
name = "vaf-am-build-01"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "anthropic>=0.40.0",
    "feedparser>=6.0.11",
    "pdfplumber>=0.11.0",
    "httpx>=0.28.0",
    "beautifulsoup4>=4.12.0",
    "pydantic>=2.10.0",
    "pydantic-settings>=2.7.0",
    "aiosqlite>=0.20.0",
    "python-dotenv>=1.0.0",
    "tiktoken>=0.8.0",
]
[project.optional-dependencies]
dev = ["pytest>=8.3.0", "pytest-asyncio>=0.24.0"]
```

### run.py
```python
"""
VAF AM Build 01 — Multi-Source Data Ingestion
Built by Vaishali Mehmi using Claude AI + Anthropic Agents
github.com/vm799 | Asset Management Series
"""
import asyncio
from src.ingesters.rss import RSSIngester
from src.ingesters.pdf import PDFIngester
from src.ingesters.web import WebIngester
from src.normaliser import DocumentNormaliser
from src.summariser import ClaudeSummariser
from src.store import SQLiteDocumentStore
from src.config import settings

RSS_FEEDS = [
    "https://www.ft.com/rss/home",
    "https://feeds.reuters.com/reuters/businessNews",
]
PDF_PATHS  = ["./data/sample_earnings.pdf"]
WEB_URLS   = ["https://www.fca.org.uk/news/press-releases"]

async def main():
    print("🚀 VAF AM Build 01 — Multi-Source Ingestion Pipeline")
    print("━" * 50)
    print("Built with Claude AI + Anthropic Agents")
    print("━" * 50)

    rss  = RSSIngester(feeds=RSS_FEEDS, max_per_feed=5)
    pdf  = PDFIngester(paths=PDF_PATHS)
    web  = WebIngester(urls=WEB_URLS)

    print("\n[PIPELINE] Launching 3 sources in parallel...")
    raw = await asyncio.gather(
        rss.ingest(), pdf.ingest(), web.ingest(),
        return_exceptions=True,
    )

    normaliser = DocumentNormaliser()
    summariser = ClaudeSummariser()
    store      = SQLiteDocumentStore(settings.data_dir / "documents.db")

    count = 0
    for batch in raw:
        if isinstance(batch, Exception):
            print(f"[WARN] Source failed: {batch}")
            continue
        for doc in batch:
            n = normaliser.normalise(doc)
            n.summary = await summariser.summarise(n.content)
            await store.save(n)
            print(f"[✓] {n.source_type:6} | {n.title[:55]}")
            count += 1

    await store.export_json(settings.reports_dir / "ingestion_report.json")
    print(f"\n✅ Complete. {count} documents ingested and stored.")
    print(f"📁 Report: {settings.reports_dir}/ingestion_report.json")

if __name__ == "__main__":
    asyncio.run(main())
```

### src/config.py
```python
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    anthropic_api_key: str
    data_dir: Path  = Path("./data")
    reports_dir: Path = Path("./reports")
    claude_model: str = "claude-sonnet-4-5"
    max_content_tokens: int = 8000

    model_config = SettingsConfigDict(env_file=".env")

    def model_post_init(self, _):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

settings = Settings()
```

### src/ingesters/base.py
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

@dataclass
class RawDocument:
    source_type: str    # "rss" | "pdf" | "web"
    source_url: str
    title: str
    content: str
    metadata: dict
    ingested_at: datetime = None

    def __post_init__(self):
        if self.ingested_at is None:
            self.ingested_at = datetime.utcnow()

class BaseIngester(ABC):
    @abstractmethod
    async def ingest(self) -> list[RawDocument]: ...
```

### src/ingesters/rss.py
```python
import feedparser, httpx
from .base import BaseIngester, RawDocument

class RSSIngester(BaseIngester):
    def __init__(self, feeds: list[str], max_per_feed: int = 5):
        self.feeds = feeds
        self.max_per_feed = max_per_feed

    async def ingest(self) -> list[RawDocument]:
        docs = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            for feed_url in self.feeds:
                try:
                    resp = await client.get(feed_url)
                    parsed = feedparser.parse(resp.text)
                    for entry in parsed.entries[:self.max_per_feed]:
                        content = getattr(entry, 'summary', '') or ''
                        if len(content) < 50:
                            continue
                        docs.append(RawDocument(
                            source_type="rss",
                            source_url=getattr(entry, 'link', feed_url),
                            title=getattr(entry, 'title', 'Untitled'),
                            content=content,
                            metadata={
                                "feed": feed_url,
                                "author": getattr(entry, 'author', 'Unknown'),
                                "published": getattr(entry, 'published', ''),
                            },
                        ))
                except Exception as e:
                    print(f"[RSS WARN] {feed_url}: {e}")
        return docs
```

### src/normaliser.py
```python
import uuid, tiktoken
from datetime import datetime
from pydantic import BaseModel
from .ingesters.base import RawDocument

enc = tiktoken.get_encoding("cl100k_base")

class IngestedDocument(BaseModel):
    id: str
    source_type: str
    source_url: str
    title: str
    content: str          # truncated to max_tokens
    summary: str = ""
    metadata: dict
    ingested_at: datetime
    tokens_estimated: int

class DocumentNormaliser:
    MAX_TOKENS = 8000

    def normalise(self, raw: RawDocument) -> IngestedDocument:
        tokens = enc.encode(raw.content)
        if len(tokens) > self.MAX_TOKENS:
            content = enc.decode(tokens[:self.MAX_TOKENS])
        else:
            content = raw.content

        return IngestedDocument(
            id=str(uuid.uuid4()),
            source_type=raw.source_type,
            source_url=raw.source_url,
            title=raw.title,
            content=content,
            metadata=raw.metadata,
            ingested_at=raw.ingested_at,
            tokens_estimated=min(len(tokens), self.MAX_TOKENS),
        )
```

### src/summariser.py
```python
import anthropic
from .config import settings

class ClaudeSummariser:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic()

    async def summarise(self, content: str) -> str:
        resp = await self.client.messages.create(
            model=settings.claude_model,
            max_tokens=150,
            messages=[{
                "role": "user",
                "content": (
                    "Summarise this document in exactly 3 sentences for an asset manager. "
                    "Be specific. Include any numbers, dates, or company names mentioned.\n\n"
                    f"DOCUMENT:\n{content[:3000]}"
                ),
            }],
        )
        return resp.content[0].text.strip()
```

---

## COLOSSUS QA CHECKLIST
- [ ] `asyncio.gather(return_exceptions=True)` — one bad source cannot kill pipeline
- [ ] PDF ingester handles corrupt/password-protected files (try/except + log)
- [ ] Content truncated to 8000 tokens BEFORE Claude API call (cost control)
- [ ] SQLite schema indexed on `source_type` and `ingested_at`
- [ ] No API keys in source code — .env only
- [ ] `.env` in `.gitignore` — verified with `git status` before first commit
- [ ] Reports directory auto-created if missing

## QUICK START
```bash
git clone https://github.com/vm799/vaf-am-build-01
cd vaf-am-build-01
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
uv sync
uv run python run.py
```
