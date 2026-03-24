"""
Gmail OAuth 2.0 authentication helper.

First run: opens browser for consent, saves token to GMAIL_TOKEN_PATH.
Subsequent runs: loads saved token, refreshes silently if expired.

Prerequisites:
  1. Download credentials.json from Google Cloud Console
  2. Set GMAIL_CREDENTIALS_PATH in .env (defaults to ./credentials.json)
  3. Set GMAIL_TOKEN_PATH in .env (defaults to ./gmail_token.json)
"""
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Read-only scope — never modifies or deletes email
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_credentials(credentials_path: Path, token_path: Path) -> Credentials:
    """
    Returns valid Gmail credentials.
    Triggers browser OAuth flow on first call, then uses saved token.
    """
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        print("[AUTH] Gmail token expired — refreshing silently...")
        creds.refresh(Request())
    else:
        if not credentials_path.exists():
            raise FileNotFoundError(
                f"\n[AUTH ERROR] credentials.json not found at {credentials_path}\n"
                "Download it from: https://console.cloud.google.com/apis/credentials\n"
                "See GMAIL_SETUP.md for step-by-step instructions.\n"
            )
        print("[AUTH] Opening browser for Gmail authorisation...")
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)
        print("[AUTH] Authorisation granted.")

    token_path.write_text(creds.to_json())
    print(f"[AUTH] Token saved to {token_path}")
    return creds
