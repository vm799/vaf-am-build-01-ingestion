"""
VAF AM Build 01 — File Share Ingester

Watches a directory for PDF files and ingests any it hasn't processed before.
Designed to mimic SharePoint/OneDrive/S3 "drop zone" behaviour locally,
giving enterprise clients a simple: "drop PDF here → auto-ingested" workflow.

State file: .file_watch_state.json in the watch directory.
  - Tracks which files have been processed by (filename + size + mtime).
  - On next run, only new or changed files are ingested.
  - Set GMAIL_FILE_WATCH_RESET=true in .env to reprocess all files.

Source type produced: "file_share"
"""
import json
from datetime import datetime
from pathlib import Path

import pdfplumber

from .base import BaseIngester, RawDocument

STATE_FILE = ".file_watch_state.json"


def _load_state(watch_dir: Path) -> dict:
    state_path = watch_dir / STATE_FILE
    if state_path.exists():
        try:
            return json.loads(state_path.read_text())
        except Exception:
            return {}
    return {}


def _save_state(watch_dir: Path, state: dict):
    state_path = watch_dir / STATE_FILE
    state_path.write_text(json.dumps(state, indent=2))


def _file_fingerprint(path: Path) -> str:
    """Unique string representing file identity — name + size + modification time."""
    stat = path.stat()
    return f"{path.name}|{stat.st_size}|{stat.st_mtime}"


def _extract_pdf_text(path: Path) -> str:
    if path.suffix.lower() in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="replace").strip()

    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages).strip()


class FileShareIngester(BaseIngester):
    """
    Ingests PDF files from a local directory, tracking previously processed files.

    Args:
        watch_dir:    Path to directory to monitor.
        reset_state:  If True, reprocess all files even if previously seen.
    """

    def __init__(self, watch_dir: str | Path, reset_state: bool = False):
        self.watch_dir = Path(watch_dir)
        self.reset_state = reset_state

    async def ingest(self) -> list[RawDocument]:
        return self._scan_directory()

    def _scan_directory(self) -> list[RawDocument]:
        if not self.watch_dir.exists():
            print(f"[FileWatch WARN] Directory not found: {self.watch_dir}")
            return []

        # Load seen-file state
        state = {} if self.reset_state else _load_state(self.watch_dir)
        docs = []
        new_state = dict(state)

        pdf_files = sorted(
            f for f in self.watch_dir.iterdir()
            if f.is_file() and f.suffix.lower() in (".pdf", ".txt", ".md")
            and not f.name.startswith(".")
        )

        if not pdf_files:
            print(f"[FileWatch] No PDF/text files found in {self.watch_dir}")
            return []

        new_count = 0
        for path in pdf_files:
            fingerprint = _file_fingerprint(path)

            if fingerprint in state:
                print(f"[FileWatch] Already processed — skipping: {path.name}")
                continue

            try:
                text = _extract_pdf_text(path)
                if len(text) < 20:
                    print(f"[FileWatch WARN] Empty file: {path.name}")
                    continue

                docs.append(RawDocument(
                    source_type="file_share",
                    source_url=str(path.absolute()),
                    title=path.stem.replace("_", " ").replace("-", " ").title(),
                    content=text,
                    metadata={
                        "filename":       path.name,
                        "size_bytes":     path.stat().st_size,
                        "watch_dir":      str(self.watch_dir),
                        "file_extension": path.suffix.lower(),
                        "modified_at":    datetime.utcfromtimestamp(
                            path.stat().st_mtime
                        ).isoformat(),
                    },
                    ingested_at=datetime.utcfromtimestamp(path.stat().st_mtime),
                ))

                new_state[fingerprint] = path.name
                new_count += 1
                print(f"[FileWatch ✓] {path.name} ({len(text)} chars)")

            except Exception as e:
                print(f"[FileWatch WARN] {path.name}: {e}")

        _save_state(self.watch_dir, new_state)

        if new_count == 0:
            print(f"[FileWatch] No new files since last run.")
        else:
            print(f"[FileWatch ✓] {new_count} new file(s) ingested from {self.watch_dir}")

        return docs
