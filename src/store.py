"""VAF AM Build 01 — SQLite Document Store"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime


class SQLiteDocumentStore:
    def __init__(self, db_path: str = "./data/documents.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                source_type TEXT NOT NULL,
                source_url TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT DEFAULT '',
                metadata TEXT NOT NULL,
                ingested_at TEXT NOT NULL,
                tokens_estimated INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_source_type ON documents(source_type);
            CREATE INDEX IF NOT EXISTS idx_ingested_at ON documents(ingested_at);
        """)
        self.conn.commit()

    async def save(self, doc):
        self.conn.execute(
            "INSERT OR REPLACE INTO documents VALUES (?,?,?,?,?,?,?,?,?)",
            (
                doc.id,
                doc.source_type,
                doc.source_url,
                doc.title,
                doc.content,
                doc.summary,
                json.dumps(doc.metadata),
                doc.ingested_at.isoformat(),
                doc.tokens_estimated,
            )
        )
        self.conn.commit()

    async def export_json(self, output_path: str) -> dict:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        rows = self.conn.execute(
            "SELECT id, source_type, title, summary, ingested_at FROM documents ORDER BY ingested_at DESC"
        ).fetchall()

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "count": len(rows),
            "documents": [
                {
                    "id": r[0],
                    "source_type": r[1],
                    "title": r[2],
                    "summary": r[3],
                    "ingested_at": r[4],
                }
                for r in rows
            ],
        }

        import json
        Path(output_path).write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        return report
