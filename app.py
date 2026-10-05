from flask import Flask, render_template, request, jsonify
from config import APP_HOST, APP_PORT, MAX_CANDIDATES, MAX_DRAFTS_PER_SCAN
from database import (
    init_db, add_draft, get_draft, update_draft, add_example,
    list_drafts, set_setting, get_setting
)
from gmail import service, profile_email, recent_threads, thread, create_draft, search_draft_for_thread
from detector import find_candidates
from llm import generate
from scheduler import start_scheduler, is_running

app = Flask(__name__)
init_db()

def scan():
    svc = service()
    mine = profile_email(svc)
    threads = []
    for item in recent_threads(svc):
        try:
            threads.append(thread(svc, item["id"]))
        except Exception:
            continue

    candidates = find_candidates(threads, mine)[:MAX_CANDIDATES]
    created = 0

    for c in candidates:
        if created >= MAX_DRAFTS_PER_SCAN:
            break

        messages = c["messages"]
        last = messages[-1]

        # Avoid repeatedly generating Jussend drafts for the same thread.
        existing = search_draft_for_thread(svc, last["thread_id"])
        if existing:
            continue

        try:
            draft = generate(messages)
            draft_id = add_draft({
                "gmail_thread_id": last["thread_id"],
                "sender": last["from"],
                "subject": last["subject"],
                "original": last["text"],
                "generated": draft,
                "status": "generated",
                "score": c["score"],
                "reason": c["reason"]
            })
            created += 1
        except Exception as exc:
            add_draft({
                "gmail_thread_id": last["thread_id"],
                "sender": last["from"],
                "subject": last["subject"],
                "original": last["text"],
                "generated": "",
                "status": "error",
                "score": c["score"],
                "reason": str(exc)
            })

    set_setting("last_scan", __import__("datetime").datetime.now().isoformat())
    return created

@app.route("/")
def index():
    return render_template(
        "index.html",
        drafts=list_drafts(),
        scheduler=is_running(),
        connected=bool(get_setting("connected"))
    )

@app.post("/api/connect")
def connect():
    try:
        svc = service()
        email = profile_email(svc)
        set_setting("connected","1")
        return jsonify({"ok":True,"email":email})
    except Exception as exc:
        return jsonify({"ok":False,"error":str(exc)}),400

@app.post("/api/scan")
def api_scan():
    try:
        count = scan()
        return jsonify({"ok":True,"created":count})
    except Exception as exc:
        return jsonify({"ok":False,"error":str(exc)}),400

@app.get("/api/drafts")
def api_drafts():
    return jsonify(list_drafts())

@app.post("/api/drafts/<int:draft_id>/approve")
def approve(draft_id):
    data = request.get_json(force=True) or {}
    draft = get_draft(draft_id)
    if not draft:
        return jsonify({"ok":False,"error":"Draft not found"}),404

    body = data.get("body", draft["generated"]).strip()
    svc = service()

    try:
        messages = {
            "to": draft["sender"],
            "subject": draft["subject"] if draft["subject"].lower().startswith("re:") else "Re: " + draft["subject"],
            "body": body,
            "thread_id": draft["gmail_thread_id"]
        }
        # Retrieve the latest message for threading headers.
        msgs = thread(svc, draft["gmail_thread_id"])
        last = msgs[-1]
        messages["in_reply_to"] = last.get("message_id")
        messages["references"] = (last.get("references","") + " " + last.get("message_id","")).strip()

        result = create_draft(svc, messages)
        update_draft(draft_id, approved=body, status="approved", gmail_draft_id=result.get("id"))
        add_example(draft["original"], draft["generated"], body)
        return jsonify({"ok":True,"gmail_draft_id":result.get("id")})
    except Exception as exc:
        return jsonify({"ok":False,"error":str(exc)}),400

@app.post("/api/drafts/<int:draft_id>/reject")
def reject(draft_id):
    update_draft(draft_id,status="rejected")
    return jsonify({"ok":True})

@app.post("/api/drafts/<int:draft_id>/regenerate")
def regenerate(draft_id):
    draft = get_draft(draft_id)
    if not draft:
        return jsonify({"ok":False,"error":"Draft not found"}),404
    try:
        svc = service()
        messages = thread(svc, draft["gmail_thread_id"])
        body = generate(messages)
        update_draft(draft_id,generated=body,status="generated")
        return jsonify({"ok":True,"body":body})
    except Exception as exc:
        return jsonify({"ok":False,"error":str(exc)}),400

@app.post("/api/scheduler")
def scheduler_toggle():
    data=request.get_json(force=True) or {}
    enabled=bool(data.get("enabled"))
    if enabled:
        start_scheduler(scan)
        set_setting("scheduler","1")
    else:
        set_setting("scheduler","0")
    return jsonify({"ok":True,"enabled":is_running()})

if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--scan",action="store_true")
    args=parser.parse_args()
    if args.scan:
        print(f"Created {scan()} draft(s).")
    else:
        app.run(host=APP_HOST,port=APP_PORT,debug=False)
