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

    # Gmail integration (optional — only required if ENABLE_GMAIL=true)
    enable_gmail: bool = False
    gmail_credentials_path: Path = Path("./credentials.json")
    gmail_token_path: Path = Path("./gmail_token.json")
    gmail_label: str = "INBOX"
    gmail_max_emails: int = 10

    # File share watch directory (optional — only required if ENABLE_FILE_WATCH=true)
    enable_file_watch: bool = False
    file_watch_dir: Path = Path("./data/file_watch")
    file_watch_reset: bool = False   # set true to reprocess all files

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    def model_post_init(self, _context):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        if self.enable_file_watch:
            self.file_watch_dir.mkdir(parents=True, exist_ok=True)

settings = Settings()
