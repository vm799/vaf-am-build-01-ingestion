"""
VAF AM Build 01 — Multi-Source Data Ingestion
Built by Vaishali Mehmi using Claude AI + Anthropic Agents
github.com/vm799 | Asset Management Series

Sources (activated via .env flags):
  Always on:  RSS feeds, PDF files, web scraping
  Optional:   Gmail inbox (ENABLE_GMAIL=true)
  Optional:   File share watch directory (ENABLE_FILE_WATCH=true)
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


def _build_gmail_ingester():
    """Returns GmailIngester if ENABLE_GMAIL=true and credentials exist."""
    from src.auth.gmail_auth import get_gmail_credentials
    from src.ingesters.gmail import GmailIngester

    creds = get_gmail_credentials(
        credentials_path=settings.gmail_credentials_path,
        token_path=settings.gmail_token_path,
    )
    return GmailIngester(
        credentials=creds,
        label=settings.gmail_label,
        max_emails=settings.gmail_max_emails,
    )


async def main():
    print("🚀 VAF AM Build 01 — Multi-Source Ingestion Pipeline")
    print("━" * 50)
    print("Built with Claude AI + Anthropic Agents")
    print("━" * 50)

    # --- Core ingesters (always on) ---
    ingesters = [
        ("rss",  RSSIngester(feeds=RSS_FEEDS, max_per_feed=3)),
        ("pdf",  PDFIngester(paths=PDF_PATHS)),
        ("web",  WebIngester(urls=WEB_URLS)),
    ]

    # --- Optional: Gmail ---
    if settings.enable_gmail:
        print("\n[PIPELINE] Gmail ingestion enabled")
        try:
            gmail_ingester = _build_gmail_ingester()
            ingesters.append(("gmail", gmail_ingester))
        except FileNotFoundError as e:
            print(str(e))
            print("[PIPELINE] Skipping Gmail — see GMAIL_SETUP.md to configure.\n")

    # --- Optional: File share ---
    if settings.enable_file_watch:
        from src.ingesters.file_watch import FileShareIngester
        print(f"[PIPELINE] File watch enabled: {settings.file_watch_dir}")
        ingesters.append((
            "file_watch",
            FileShareIngester(
                watch_dir=settings.file_watch_dir,
                reset_state=settings.file_watch_reset,
            ),
        ))

    # --- Run all ingesters in parallel ---
    labels   = [label for label, _ in ingesters]
    tasks    = [ingester.ingest() for _, ingester in ingesters]

    print(f"\n[PIPELINE] Launching {len(ingesters)} source(s) in parallel: {', '.join(labels)}")
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # --- Normalise → Summarise → Store ---
    normaliser = DocumentNormaliser()
    summariser = ClaudeSummariser()
    store      = SQLiteDocumentStore(settings.data_dir / "documents.db")

    count = 0
    for label, batch in zip(labels, results):
        if isinstance(batch, Exception):
            print(f"[WARN] {label} source failed: {batch}")
            continue
        for doc in batch:
            n = normaliser.normalise(doc)
            n.summary = await summariser.summarise(n.content)
            await store.save(n)
            print(f"[✓] {n.source_type:18} | {n.title[:50]}")
            count += 1

    report_path = settings.reports_dir / "ingestion_report.json"
    await store.export_json(report_path)

    # Auto-sync to portfolio so Results tab updates immediately
    import shutil, pathlib
    portfolio_data = pathlib.Path(__file__).parent.parent / "portfolio" / "data"
    if portfolio_data.exists():
        shutil.copy(report_path, portfolio_data / "build_01.json")
        print(f"📊 Portfolio synced → portfolio/data/build_01.json")

    print(f"\n✅ Complete. {count} documents ingested and stored.")
    print(f"📁 Report: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())
