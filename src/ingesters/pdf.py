"""VAF AM Build 01 — PDF + Text Ingester"""
from pathlib import Path
from .base import BaseIngester, RawDocument


class PDFIngester(BaseIngester):
    def __init__(self, paths: list):
        self.paths = [Path(p) for p in paths]

    async def ingest(self) -> list[RawDocument]:
        docs = []
        for path in self.paths:
            if not path.exists():
                print(f"[PDF WARN] File not found: {path}")
                continue
            try:
                if path.suffix.lower() in (".txt", ".md"):
                    text = path.read_text(encoding="utf-8", errors="replace").strip()
                else:
                    import pdfplumber
                    with pdfplumber.open(path) as pdf:
                        text = "\n".join(
                            page.extract_text() or "" for page in pdf.pages
                        ).strip()

                if len(text) < 20:
                    continue

                docs.append(RawDocument(
                    source_type="pdf",
                    source_url=str(path.absolute()),
                    title=path.stem,
                    content=text,
                    metadata={"filename": path.name, "size_bytes": path.stat().st_size},
                ))
                print(f"[PDF ✓] {path.name} ({len(text)} chars)")
            except Exception as e:
                print(f"[PDF WARN] {path.name}: {e}")
        return docs
