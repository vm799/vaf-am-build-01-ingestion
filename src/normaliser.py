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
