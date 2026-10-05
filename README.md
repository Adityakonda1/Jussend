# Jussend

Jussend is an approval-first AI email assistant for Gmail.

## What it does

1. Connects to Gmail with Google OAuth.
2. Scans recent inbox conversations.
3. Identifies messages that likely need a human reply.
4. Generates a contextual reply draft.
5. Lets you edit, approve, reject, or regenerate the draft.
6. Saves approved replies as Gmail drafts.
7. Learns from your approved/edited replies.
8. Can periodically scan in the background.
9. Never sends email automatically.

## Quick start

### 1. Requirements

- Python 3.10+
- Google Cloud project
- Gmail API enabled
- OAuth Desktop App credentials
- OpenAI API key

### 2. Google OAuth

In Google Cloud Console:

- Create/select a project.
- Enable Gmail API.
- Create OAuth credentials.
- Choose Desktop app.
- Download the JSON.
- Rename it to `credentials.json`.
- Put it in the Jussend directory.

The app uses the Gmail `modify` scope because it needs to create drafts.

### 3. Install

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure

Copy `.env.example` to `.env` and set:

```text
OPENAI_API_KEY=...
```

Optional:

```text
OPENAI_MODEL=gpt-5.6-mini
LOOKBACK_DAYS=14
MAX_CANDIDATES=10
MAX_DRAFTS_PER_SCAN=5
SCAN_INTERVAL_MINUTES=60
```

### 5. Run

```bash
python app.py
```

Open:

`http://127.0.0.1:8787`

On the first Gmail connection, your browser opens for Google OAuth.

## First-run workflow

Jussend starts in **approval mode**.

- Scan inbox.
- Select a candidate.
- Review the generated draft.
- Edit if necessary.
- Click "Approve & save draft".
- Jussend records the approved version as a style example.

Do this for several emails before enabling recurring scanning.

## Recurring mode

From the dashboard, enable the scheduler after you are satisfied with draft quality.

The scheduler scans periodically and prepares Gmail drafts. It does not send them.

You can also run:

```bash
python app.py --scan
```

## Security

- Gmail OAuth tokens are stored locally.
- Never commit `.env`, `credentials.json`, or `token.json`.
- Email content is treated as untrusted input.
- Jussend does not follow links or execute instructions contained in email.
- Sending is intentionally not implemented in the automated workflow.
- Draft creation is the only write operation.

## Project structure

```text
Jussend/
  app.py
  config.py
  database.py
  gmail.py
  detector.py
  llm.py
  scheduler.py
  templates/
    index.html
  static/
    app.js
    style.css
  data/
  .env.example
  requirements.txt
```
