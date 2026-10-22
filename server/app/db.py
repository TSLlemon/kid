import sqlite3, os, threading
from .config import settings

_lock = threading.Lock()
SCHEMA = """
CREATE TABLE IF NOT EXISTS users(openid TEXT PRIMARY KEY, nickname TEXT, grade INTEGER DEFAULT 3, created_at TEXT DEFAULT CURRENT_TIMESTAMP, username TEXT, password_hash TEXT);
CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY AUTOINCREMENT, openid TEXT, kind TEXT, subject TEXT, grade INTEGER, question TEXT, answer TEXT, correct INTEGER, created_at TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS mistakes(id INTEGER PRIMARY KEY AUTOINCREMENT, openid TEXT, subject TEXT, grade INTEGER, question TEXT, my_answer TEXT, correct_answer TEXT, explanation TEXT, mastered INTEGER DEFAULT 0, created_at TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS checkins(openid TEXT, day TEXT, created_at TEXT DEFAULT (datetime('now','localtime')), PRIMARY KEY(openid, day));
CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY AUTOINCREMENT, grade INTEGER, subject TEXT, knowledge_point TEXT, type TEXT, stem TEXT, options TEXT, answer TEXT, explanation TEXT, source_url TEXT, hash TEXT UNIQUE, created_at TEXT DEFAULT (datetime('now','localtime')));
CREATE INDEX IF NOT EXISTS idx_q_gs ON questions(grade, subject);
CREATE TABLE IF NOT EXISTS knowledge_points(id INTEGER PRIMARY KEY AUTOINCREMENT, grade INTEGER, subject TEXT, name TEXT, content TEXT, source_url TEXT, hash TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS stories(id INTEGER PRIMARY KEY AUTOINCREMENT, grade INTEGER, subject TEXT, title TEXT, sentences TEXT, hash TEXT UNIQUE);
CREATE INDEX IF NOT EXISTS idx_s_gs ON stories(grade, subject);
CREATE TABLE IF NOT EXISTS vocab(id INTEGER PRIMARY KEY AUTOINCREMENT, word TEXT UNIQUE, meaning TEXT, phonetic TEXT, pinyin TEXT, grade INTEGER);
CREATE INDEX IF NOT EXISTS idx_v_g ON vocab(grade);
"""

def connect():
    d = os.path.dirname(settings.DB_PATH)
    if d: os.makedirs(d, exist_ok=True)
    c = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with _lock:
        c = connect()
        try:
            c.executescript(SCHEMA)
            # 兼容旧库；重复启动不会重复添加字段，也不吞掉其他 SQL 错误。
            user_columns = {row["name"] for row in c.execute("PRAGMA table_info(users)")}
            for column in ("username", "password_hash"):
                if column not in user_columns:
                    c.execute(f"ALTER TABLE users ADD COLUMN {column} TEXT")
            question_columns = {row["name"] for row in c.execute("PRAGMA table_info(questions)")}
            if "story_id" not in question_columns:
                c.execute("ALTER TABLE questions ADD COLUMN story_id INTEGER")
            c.commit()
        finally:
            c.close()

def q(sql, args=(), one=False, commit=False):
    with _lock:
        c = connect()
        try:
            cur = c.execute(sql, args)
            if commit:
                c.commit(); return cur.lastrowid
            rows = [dict(r) for r in cur.fetchall()]
            return (rows[0] if rows else None) if one else rows
        finally:
            c.close()
