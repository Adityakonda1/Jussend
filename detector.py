import re
from email.utils import parseaddr

BULK_RE = re.compile(
    r"(no[-_ ]?reply|do[-_ ]?not[-_ ]?reply|noreply|mailer-daemon|newsletter|notifications?@)",
    re.I
)

BULK_SUBJECTS = [
    "unsubscribe", "weekly digest", "daily digest", "receipt",
    "invoice", "shipping update", "verification code", "security alert"
]

def email_address(value):
    return parseaddr(value)[1].lower()

def bulk(sender, subject):
    e = email_address(sender)
    return bool(BULK_RE.search(e)) or any(x in subject.lower() for x in BULK_SUBJECTS)

def candidate(messages, mine):
    if not messages:
        return False, 0, "empty thread"
    last = messages[-1]
    sender = email_address(last["from"])

    if sender == mine.lower():
        return False, 0, "latest message is from you"

    if bulk(last["from"], last["subject"]):
        return False, 0, "automated/bulk email"

    score = 50
    reasons = ["latest message is from another person"]

    text = last["text"]
    lower = text.lower()
    subject = last["subject"].lower()

    if "?" in text:
        score += 20
        reasons.append("asks a question")
    if any(p in lower for p in [
        "could you", "can you", "would you", "please", "let me know",
        "are you available", "when can", "what do you think"
    ]):
        score += 15
        reasons.append("contains a request")
    if any(p in subject for p in [
        "interview", "opportunity", "application", "meeting",
        "follow up", "follow-up", "recruiter"
    ]):
        score += 10
        reasons.append("work/career conversation")
    if len(text) > 100:
        score += 5

    return True, min(score,100), "; ".join(reasons)

def find_candidates(all_threads, mine):
    result = []
    for messages in all_threads:
        ok, score, reason = candidate(messages,mine)
        if ok:
            result.append({
                "messages":messages,
                "score":score,
                "reason":reason
            })
    return sorted(result,key=lambda x:x["score"],reverse=True)
