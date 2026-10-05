import sqlite3
from datetime import datetime, timezone
from config import DB_FILE

def connect():
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = connect()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS examples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original TEXT NOT NULL,
        draft TEXT NOT NULL,
        approved TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gmail_thread_id TEXT NOT NULL,
        gmail_draft_id TEXT,
        sender TEXT,
        subject TEXT,
        original TEXT,
        generated TEXT,
        approved TEXT,
        status TEXT NOT NULL,
        score INTEGER DEFAULT 0,
        reason TEXT,
        created_at TEXT NOT NULL
    );
    """)
    con.commit()
    con.close()

def set_setting(key, value):
    con = connect()
    con.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))
    con.commit()
    con.close()

def get_setting(key, default=None):
    con = connect()
    row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    con.close()
    return row["value"] if row else default

def add_example(original, draft, approved):
    con = connect()
    con.execute(
        "INSERT INTO examples(original,draft,approved,created_at) VALUES(?,?,?,?)",
        (original, draft, approved, datetime.now(timezone.utc).isoformat())
    )
    con.commit()
    con.close()

def get_examples(limit=5):
    con = connect()
    rows = con.execute(
        "SELECT * FROM examples ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    con.close()
    return [dict(x) for x in rows]

def add_draft(data):
    con = connect()
    cur = con.execute("""
      INSERT INTO drafts(
        gmail_thread_id,gmail_draft_id,sender,subject,original,generated,
        approved,status,score,reason,created_at
      ) VALUES(?,?,?,?,?,?,?,?,?,?,?)
    """, (
        data.get("gmail_thread_id"), data.get("gmail_draft_id"),
        data.get("sender"), data.get("subject"), data.get("original"),
        data.get("generated"), data.get("approved"), data.get("status","generated"),
        data.get("score",0), data.get("reason",""),
        datetime.now(timezone.utc).isoformat()
    ))
    con.commit()
    draft_id = cur.lastrowid
    con.close()
    return draft_id

def update_draft(draft_id, **fields):
    if not fields:
        return
    con = connect()
    assignments = ", ".join(f"{k}=?" for k in fields)
    values = list(fields.values()) + [draft_id]
    con.execute(f"UPDATE drafts SET {assignments} WHERE id=?", values)
    con.commit()
    con.close()

def get_draft(draft_id):
    con = connect()
    row = con.execute("SELECT * FROM drafts WHERE id=?", (draft_id,)).fetchone()
    con.close()
    return dict(row) if row else None

def list_drafts(status=None, limit=100):
    con = connect()
    if status:
        rows = con.execute(
            "SELECT * FROM drafts WHERE status=? ORDER BY id DESC LIMIT ?",
            (status, limit)
        ).fetchall()
    else:
        rows = con.execute(
            "SELECT * FROM drafts ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    con.close()
    return [dict(x) for x in rows]
