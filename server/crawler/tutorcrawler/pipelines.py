import hashlib, json, os, sqlite3
from scrapy.exceptions import DropItem
from .items import QuestionItem

SCHEMA = """
CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY AUTOINCREMENT, grade INTEGER, subject TEXT, knowledge_point TEXT, type TEXT, stem TEXT, options TEXT, answer TEXT, explanation TEXT, source_url TEXT, hash TEXT UNIQUE, created_at TEXT DEFAULT (datetime('now','localtime')));
CREATE TABLE IF NOT EXISTS knowledge_points(id INTEGER PRIMARY KEY AUTOINCREMENT, grade INTEGER, subject TEXT, name TEXT, content TEXT, source_url TEXT, hash TEXT UNIQUE);
"""

class SQLitePipeline:
    """写入与后端共用的 SQLite；按内容哈希去重。"""
    def __init__(self, db_path): self.db_path = db_path
    @classmethod
    def from_crawler(cls, crawler): return cls(crawler.settings.get("DB_PATH"))
    def open_spider(self, spider):
        d = os.path.dirname(self.db_path)
        if d: os.makedirs(d, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path); self.conn.executescript(SCHEMA); self.added = 0
    def close_spider(self, spider):
        self.conn.commit(); self.conn.close(); spider.logger.info(f"新增 {self.added} 条")
    def process_item(self, item, spider):
        d = dict(item)
        if not d.get("subject") or not (d.get("stem") or d.get("name")): raise DropItem("缺少必要字段")
        if isinstance(item, QuestionItem):
            opts = json.dumps(d.get("options") or [], ensure_ascii=False)
            h = hashlib.md5(f"{d['subject']}|{d['stem'].strip()}|{d.get('answer','')}".encode()).hexdigest()
            cur = self.conn.execute("INSERT OR IGNORE INTO questions(grade,subject,knowledge_point,type,stem,options,answer,explanation,source_url,hash) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (int(d.get("grade") or 0), d["subject"], d.get("knowledge_point", ""), d.get("type", "fill"), d["stem"].strip(), opts,
                 d.get("answer", ""), d.get("explanation", ""), d.get("source_url", ""), h))
        else:
            h = hashlib.md5(f"{d['subject']}|{d['name']}|{d.get('content','')[:200]}".encode()).hexdigest()
            cur = self.conn.execute("INSERT OR IGNORE INTO knowledge_points(grade,subject,name,content,source_url,hash) VALUES(?,?,?,?,?,?)",
                (int(d.get("grade") or 0), d["subject"], d["name"], d.get("content", ""), d.get("source_url", ""), h))
        self.added += cur.rowcount
        return item
