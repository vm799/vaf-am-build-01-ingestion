"""VAF AM Build 01 — Web Ingester"""
import httpx
from bs4 import BeautifulSoup
from .base import BaseIngester, RawDocument


class WebIngester(BaseIngester):
    def __init__(self, urls: list):
        self.urls = urls

    async def ingest(self) -> list[RawDocument]:
        docs = []
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            for url in self.urls:
                try:
                    resp = await client.get(
                        url,
                        headers={"User-Agent": "VAF-AM-Research-Bot/1.0"},
                    )
                    resp.raise_for_status()

                    soup = BeautifulSoup(resp.text, "html.parser")

                    # Remove noise elements
                    for tag in soup(["script", "style", "nav", "footer", "header"]):
                        tag.decompose()

                    # Try to get article content first, fall back to body
                    article = soup.find("article") or soup.find("main") or soup.body
                    text = article.get_text(separator=" ", strip=True) if article else ""
                    text = " ".join(text.split())  # normalise whitespace

                    title = ""
                    if soup.title:
                        title = soup.title.string or ""
                    if not title:
                        h1 = soup.find("h1")
                        title = h1.get_text(strip=True) if h1 else url

                    if len(text) < 50:
                        continue

                    docs.append(RawDocument(
                        source_type="web",
                        source_url=url,
                        title=title[:120],
                        content=text,
                        metadata={
                            "domain": url.split("/")[2],
                            "status_code": resp.status_code,
                            "content_length": len(text),
                        },
                    ))
                    print(f"[WEB ✓] {url[:60]}")
                except Exception as e:
                    print(f"[WEB WARN] {url[:60]}: {e}")
        return docs
