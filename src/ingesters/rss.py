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
