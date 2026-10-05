from __future__ import annotations
import base64
from email.mime.text import MIMEText
from email.utils import parseaddr
from bs4 import BeautifulSoup

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import CREDENTIALS_FILE, TOKEN_FILE, SCOPES, LOOKBACK_DAYS

def service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise RuntimeError("credentials.json is missing.")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)

def header(headers, name):
    for h in headers:
        if h.get("name","").lower() == name.lower():
            return h.get("value","")
    return ""

def decode(data):
    if not data:
        return ""
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")

def html_to_text(value):
    soup = BeautifulSoup(value, "html.parser")
    for tag in soup(["script","style"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)

def payload_text(payload):
    if "parts" in payload:
        plain, html = [], []
        for part in payload["parts"]:
            mime = part.get("mimeType","")
            body = part.get("body",{})
            if body.get("data"):
                value = decode(body["data"])
                if mime == "text/plain":
                    plain.append(value)
                elif mime == "text/html":
                    html.append(html_to_text(value))
            if mime.startswith("multipart/"):
                nested = payload_text(part)
                if nested:
                    plain.append(nested)
        return "\n".join(plain or html)
    body = payload.get("body",{})
    if body.get("data"):
        value = decode(body["data"])
        return html_to_text(value) if payload.get("mimeType") == "text/html" else value
    return ""

def normalize(message):
    headers = message.get("payload",{}).get("headers",[])
    return {
        "id": message["id"],
        "thread_id": message.get("threadId"),
        "from": header(headers,"From"),
        "to": header(headers,"To"),
        "subject": header(headers,"Subject"),
        "date": header(headers,"Date"),
        "message_id": header(headers,"Message-ID"),
        "references": header(headers,"References"),
        "text": payload_text(message.get("payload",{})),
        "labels": message.get("labelIds",[])
    }

def profile_email(svc):
    return svc.users().getProfile(userId="me").execute().get("emailAddress","")

def recent_threads(svc):
    result = svc.users().threads().list(
        userId="me",
        q=f"in:anywhere newer_than:{LOOKBACK_DAYS}d -label:spam -label:trash",
        maxResults=50
    ).execute()
    return result.get("threads",[])

def thread(svc, thread_id):
    data = svc.users().threads().get(
        userId="me", id=thread_id, format="full"
    ).execute()
    return [normalize(x) for x in data.get("messages",[])]

def create_draft(svc, message):
    mime = MIMEText(message["body"], "plain", "utf-8")
    mime["To"] = message["to"]
    mime["Subject"] = message["subject"]
    if message.get("in_reply_to"):
        mime["In-Reply-To"] = message["in_reply_to"]
    if message.get("references"):
        mime["References"] = message["references"]
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    return svc.users().drafts().create(
        userId="me",
        body={"message":{"raw":raw,"threadId":message["thread_id"]}}
    ).execute()

def search_draft_for_thread(svc, thread_id):
    # Used only to avoid duplicate drafts for the same Jussend run.
    data = svc.users().drafts().list(userId="me", maxResults=100).execute()
    for item in data.get("drafts",[]):
        try:
            d = svc.users().drafts().get(
                userId="me", id=item["id"], format="minimal"
            ).execute()
            if d.get("message",{}).get("threadId") == thread_id:
                return d["id"]
        except Exception:
            pass
    return None
