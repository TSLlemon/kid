import sqlite3

from fastapi.testclient import TestClient

from app import db, main


def test_fresh_database_registration_and_password_login(tmp_path, monkeypatch):
    monkeypatch.setattr(db.settings, "DB_PATH", str(tmp_path / "fresh.db"))
    monkeypatch.setattr(db.settings, "DEV_MODE", False)
    with TestClient(main.app) as client:
        body = {"username": "sample_user", "password": "test-only-password", "nickname": "样例"}
        response = client.post("/api/register", json=body)
        assert response.status_code == 200
        token = response.json()["token"]
        assert client.get("/api/stats", headers={"Authorization": "Bearer " + token}).status_code == 200
        assert client.post("/api/register", json={**body, "username": "SAMPLE_USER"}).status_code == 400
        assert client.post("/api/login", json={"username": body["username"], "password": "wrong"}).status_code == 401
        response = client.post("/api/login", json={"username": body["username"], "password": body["password"]})
        assert response.status_code == 200 and response.json()["openid"] == "u_sample_user"


def test_legacy_database_migration_preserves_users_and_is_idempotent(tmp_path, monkeypatch):
    path = tmp_path / "legacy.db"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE users(openid TEXT PRIMARY KEY, nickname TEXT, grade INTEGER DEFAULT 3, created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        connection.execute("INSERT INTO users(openid,nickname) VALUES(?,?)", ("sample-legacy", "样例"))
    monkeypatch.setattr(db.settings, "DB_PATH", str(path))
    db.init_db()
    db.init_db()
    with sqlite3.connect(path) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(users)")}
        assert {"username", "password_hash"}.issubset(columns)
        assert connection.execute("SELECT nickname FROM users WHERE openid='sample-legacy'").fetchone() == ("样例",)
        assert connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
        assert "story_id" in {row[1] for row in connection.execute("PRAGMA table_info(questions)")}


def test_nonempty_vocabulary_and_grade_filter(tmp_path, monkeypatch):
    monkeypatch.setattr(db.settings, "DB_PATH", str(tmp_path / "vocab.db"))
    with TestClient(main.app) as client:
        from app.auth import make_token
        client.headers["Authorization"] = "Bearer " + make_token("sample-only")
        assert client.get("/api/vocab?grade=1").json() == {"words": []}
        db.q("INSERT INTO vocab(word,meaning,phonetic,pinyin,grade) VALUES(?,?,?,?,?)", ("cat", "猫", None, None, 1), commit=True)
        db.q("INSERT INTO vocab(word,meaning,grade) VALUES(?,?,?)", ("book", "书", 2), commit=True)
        response = client.get("/api/vocab?grade=1")
        assert response.status_code == 200
        assert response.json() == {"words": [{"word": "cat", "meaning": "猫", "phonetic": None, "pinyin": None, "grade": 1}]}
