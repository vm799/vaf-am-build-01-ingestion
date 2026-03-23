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
