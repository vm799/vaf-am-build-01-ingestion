# Gmail Integration — Setup Guide

Get real emails from your Gmail inbox into the VAF AM ingestion pipeline in ~10 minutes.

---

## Step 1 — Create a Google Cloud Project

1. Go to **https://console.cloud.google.com**
2. Click the project dropdown (top-left) → **New Project**
3. Name it: `VAF AM Intelligence`
4. Click **Create**

---

## Step 2 — Enable the Gmail API

1. In your new project, go to **APIs & Services → Library**
2. Search: `Gmail API`
3. Click it → click **Enable**

---

## Step 3 — Create OAuth 2.0 Credentials

1. Go to **APIs & Services → Credentials**
2. Click **+ Create Credentials → OAuth client ID**
3. If prompted, configure the OAuth consent screen first:
   - User type: **External**
   - App name: `VAF AM Intelligence`
   - Support email: your email
   - Scroll to bottom → **Save and Continue** (skip scopes, skip test users for now)
   - Back at credentials page — try again
4. Application type: **Desktop app**
5. Name: `VAF AM CLI`
6. Click **Create**
7. Click **Download JSON** (the download icon on the right)
8. Rename the file to `credentials.json`
9. Move it into the repo root: `vaf-am-build-01-ingestion/credentials.json`

---

## Step 4 — Add Yourself as a Test User

While the app is in "testing" mode (which it is by default), only listed accounts can authenticate.

1. Go to **APIs & Services → OAuth consent screen**
2. Scroll to **Test users** section
3. Click **+ Add Users**
4. Enter your Gmail address
5. Click **Save**

---

## Step 5 — Configure Your .env

Open `.env` (copy from `.env.example` if it doesn't exist) and set:

```
ENABLE_GMAIL=true
GMAIL_CREDENTIALS_PATH=./credentials.json
GMAIL_TOKEN_PATH=./gmail_token.json
GMAIL_LABEL=INBOX
GMAIL_MAX_EMAILS=10
```

**Tip — create a dedicated Gmail label:**

Rather than reading your entire inbox, create a label like `VAF-Ingestion` in Gmail and filter emails into it. Then set `GMAIL_LABEL=VAF-Ingestion`. This gives you precise control over what gets ingested.

To create a label in Gmail: Settings → Labels → Create new label.

---

## Step 6 — First Run (OAuth consent)

```bash
cd vaf-am-build-01-ingestion
uv run python run.py
```

On first run, a browser window will open asking you to:
1. Choose your Google account
2. Allow `VAF AM Intelligence` to read your Gmail
3. Click **Allow**

The token is saved to `gmail_token.json`. Subsequent runs are silent — no browser needed.

---

## Step 7 — Demo Flow

```bash
# Send 3 test emails to yourself:
#   Email 1: Subject "FCA Enforcement Notice Q1 2026" — text body only
#   Email 2: Subject "HSBC Q1 2026 Earnings" — with PDF attached (any earnings PDF)
#   Email 3: Subject "Reuters Market Briefing" — text body only

# Drop 2 PDFs into the file watch folder:
mkdir -p data/file_watch
cp your_report.pdf data/file_watch/
cp your_factsheet.pdf data/file_watch/

# Set both enabled in .env:
# ENABLE_GMAIL=true
# ENABLE_FILE_WATCH=true

# Run the pipeline:
uv run python run.py
```

**What you'll see:**
- Gmail: 3 emails fetched
  - Email 1: `[HIGH]` flagged due to "FCA" keyword → email body summarised
  - Email 2: email body + PDF attachment → 2 documents produced, both summarised
  - Email 3: `[MEDIUM]` market briefing → email body summarised
- File watch: 2 new PDFs detected → both ingested
- All processed by Claude AI → summaries in report

---

## Security Notes

- `credentials.json` and `gmail_token.json` are in `.gitignore` — **never commit these**
- The app only has `gmail.readonly` scope — it cannot send, delete or modify any email
- Token refreshes silently — no re-auth needed after initial consent
- To revoke access: Google Account → Security → Third-party apps → Remove VAF AM Intelligence

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `credentials.json not found` | File missing from repo root | Download from Google Cloud Console → Step 3 |
| `Access blocked: App not verified` | You're not a test user | Add your email in OAuth consent screen → Step 4 |
| `Token has been expired or revoked` | Token file corrupted | Delete `gmail_token.json` and re-run |
| `Quota exceeded` | Too many API calls | Reduce `GMAIL_MAX_EMAILS` in .env |
| `Label not found` | Label name typo | Check exact label name in Gmail settings |
