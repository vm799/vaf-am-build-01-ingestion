import anthropic
from .config import settings

class ClaudeSummariser:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic()

    async def summarise(self, content: str) -> str:
        resp = await self.client.messages.create(
            model=settings.claude_model,
            max_tokens=80,
            system="You are a concise financial analyst. Summarize documents in exactly 3 sentences.",
            messages=[{
                "role": "user",
                "content": f"{content[:2000]}",
            }],
        )
        return resp.content[0].text.strip()
