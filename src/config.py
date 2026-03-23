from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class Settings(BaseSettings):
    anthropic_api_key: str
    data_dir: Path = Path("./data")
    reports_dir: Path = Path("./reports")
    claude_model: str = "claude-haiku-4-5"
    max_content_tokens: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    def model_post_init(self, _context):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

settings = Settings()
