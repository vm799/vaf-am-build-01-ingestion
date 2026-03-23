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
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
]
PDF_PATHS  = ["./data/sample_earnings.txt"]
WEB_URLS   = ["https://www.fca.org.uk/news"]

async def main():
    print("🚀 VAF AM Build 01 — Multi-Source Ingestion Pipeline")
    print("━" * 50)
    print("Built with Claude AI + Anthropic Agents")
    print("━" * 50)

    rss  = RSSIngester(feeds=RSS_FEEDS, max_per_feed=3)
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
