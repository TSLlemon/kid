import os, sys, json, tempfile
_test_dir = tempfile.TemporaryDirectory(prefix="kidtutor-api-test-")
os.environ.update(DEV_MODE="true", DB_PATH=os.path.join(_test_dir.name, "test.db"), LLM_API_KEY="x", RATE_LIMIT_PER_MIN="100")
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pytest
from fastapi.testclient import TestClient
from app import main, llm

async def fake_chat(messages, vision=False, temperature=0.5):
    sys_p = messages[0]["content"]
    if "批改" in sys_p: return json.dumps({"correct": False, "feedback": "再想想", "hint": "先想想加法", "correct_answer": "4", "explanation": "2加2等于4"})
    if "请出符合" in sys_p: return "```json\n" + json.dumps({"questions": [{"question": "2+2=?", "type": "fill", "options": [], "answer": "4", "explanation": "2加2"}]}) + "\n```"
    return json.dumps({"question": "图片题" if vision else messages[1]["content"], "hint": "想想", "steps": ["a"], "answer": "4", "encourage": "加油"})

llm.chat = fake_chat

@pytest.fixture(scope="module")
def c():
    with TestClient(main.app) as cl:
        t = cl.post("/api/login", json={"code": "devkid"}).json()["token"]
        cl.headers["Authorization"] = "Bearer " + t
        yield cl

def test_auth_required():
    with TestClient(main.app) as cl:
        assert cl.get("/api/stats").status_code == 401

def test_explain(c):
    r = c.post("/api/explain", json={"subject": "数学", "grade": 2, "question": "2+2=?"})
    assert r.status_code == 200 and r.json()["answer"] == "4"
    assert c.post("/api/explain", json={"subject": "物理", "grade": 2, "question": "x"}).status_code == 400

def test_explain_image(c):
    r = c.post("/api/explain_image", data={"subject": "英语", "grade": 4}, files={"file": ("a.jpg", b"\xff\xd8xx", "image/jpeg")})
    assert r.status_code == 200 and r.json()["question"] == "图片题"

def test_practice_math_generator(c):
    # 数学走本地生成器：无限题量，不调 AI
    r = c.post("/api/practice", json={"subject": "数学", "grade": 1, "count": 5}).json()
    assert r["source"] == "generator" and len(r["questions"]) == 5
    for q in r["questions"]:
        assert q["question"] and q["answer"] and q["explanation"] and q["knowledge_point"]
        assert q["type"] in ("fill", "choice")
        if q["type"] == "choice":
            assert q["answer"] in "ABCD" and len(q["options"]) == 4
    # topic 能对应知识点时也走生成器
    r = c.post("/api/practice", json={"subject": "数学", "grade": 3, "topic": "两位数乘法", "count": 3}).json()
    assert r["source"] == "generator"
    assert all(q["knowledge_point"] == "两位数乘法" for q in r["questions"])
    # topic 对不上任何知识点时回退到 AI（空题库）
    r = c.post("/api/practice", json={"subject": "数学", "grade": 1, "topic": "鸡兔同笼", "count": 2}).json()
    assert r["questions"][0]["answer"] == "4"

def test_practice_grade_mistakes(c):
    assert c.post("/api/grade", json={"subject": "数学", "grade": 1, "question": "2+2", "answer": " 4 ", "reference": "4"}).json()["correct"]
    wrong = {"subject": "数学", "grade": 1, "question": "2+2", "answer": "5", "reference": "4"}
    for attempt in (1, 2):
        response = c.post("/api/grade", json={**wrong, "attempt": attempt})
        assert response.status_code == 200
        result = response.json()
        assert not result["correct"] and result["hint_level"] == attempt
        assert result["hint"] and "correct_answer" not in result and "explanation" not in result
        assert c.get("/api/mistakes").json() == []
    response = c.post("/api/grade", json={**wrong, "attempt": 3})
    assert response.status_code == 200
    result = response.json()
    assert not result["correct"] and result["hint_level"] == 3
    assert result["correct_answer"] == "4" and result["explanation"]
    ms = c.get("/api/mistakes").json(); assert len(ms) == 1
    assert ms[0]["my_answer"] == "5" and ms[0]["correct_answer"] == "4"
    assert c.patch(f"/api/mistakes/{ms[0]['id']}", json={"mastered": 1}).status_code == 200
    assert c.get("/api/mistakes").json() == []
    i = c.post("/api/mistakes", json={"subject": "语文", "grade": 3, "question": "q"}).json()["id"]
    c.delete(f"/api/mistakes/{i}")
    assert c.get("/api/mistakes").json() == []

def test_checkin_stats(c):
    assert c.post("/api/checkin").json()["streak"] == 1
    assert c.get("/api/checkin").json()["checked"]
    s = c.get("/api/stats").json()
    assert s["explain_count"] == 2 and s["by_subject"][0]["accuracy"] == 25
    assert len(c.get("/api/records").json()) >= 6

def test_rate_limit():
    from app import ratelimit
    for _ in range(3): ratelimit.check("k", 3)
    with pytest.raises(Exception): ratelimit.check("k", 3)

def test_practice_prefers_bank(c):
    from app import db
    for i in range(3):
        db.q("INSERT INTO questions(grade,subject,knowledge_point,type,stem,options,answer,hash) VALUES(3,'语文','古诗','fill',?, '[]','a',?)", (f"题{i}", f"h{i}"), commit=True)
    r = c.post("/api/practice", json={"subject": "语文", "grade": 3, "count": 3}).json()
    assert r["source"] == "bank" and len(r["questions"]) == 3
    assert c.post("/api/practice", json={"subject": "语文", "grade": 3, "count": 5}).json()["source"] == "ai"
