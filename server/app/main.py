import base64, datetime, hashlib, json, os, re, secrets, shutil, subprocess
import re
from typing import Optional
import httpx
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from .config import settings
from . import db, llm, prompts, ratelimit, mathgen, ocr
from .auth import make_token, current_user

app = FastAPI(title="小学学习辅导")
SUBJECTS = ("语文", "数学", "英语", "名著")

@app.on_event("startup")
def _startup(): db.init_db()

@app.exception_handler(llm.LLMError)
async def _llm_err(_, e): return JSONResponse(status_code=502, content={"detail": str(e)})

def chk(subject, grade):
    if subject not in SUBJECTS: raise HTTPException(400, "科目只能是 语文/数学/英语")
    if not 1 <= int(grade) <= 6: raise HTTPException(400, "年级应为 1-6")

def log(oid, kind, subject, grade, question, answer="", correct=None):
    db.q("INSERT INTO records(openid,kind,subject,grade,question,answer,correct) VALUES(?,?,?,?,?,?,?)",
         (oid, kind, subject, grade, str(question)[:2000], str(answer)[:4000], correct), commit=True)

@app.get("/api/health")
def health(): return {"ok": True}

@app.get("/", include_in_schema=False)
def index():
    from fastapi.responses import HTMLResponse
    return HTMLResponse(
        "<html><head><meta charset='utf-8'><title>kid-tutor</title></head>"
        "<body style='font-family:sans-serif;max-width:640px;margin:40px auto;padding:0 16px'>"
        "<h2>\U0001f4da kid-tutor 学习辅导服务运行中</h2>"
        "<p>这是后端 API 服务，各端这样用：</p><ul>"
        "<li>安卓 App：填写你部署的后端地址</li>"
        "<li>微信小程序：需配置备案域名（见《部署说明》）</li>"
        "<li><a href='/docs'>接口文档</a> · <a href='/api/health'>健康检查</a></li>"
        "</ul><p style='color:#888;font-size:13px'>AI 讲题需在 .env 里配置大模型 Key 才会可用。</p>"
        "</body></html>")


def _hash_pw(pw: str) -> str:
    salt = secrets.token_hex(8)
    return f"{salt}${hashlib.sha256((salt + pw).encode()).hexdigest()}"

def _verify_pw(pw: str, stored: str) -> bool:
    try:
        salt, h = stored.split("$", 1)
        return hashlib.sha256((salt + pw).encode()).hexdigest() == h
    except Exception:
        return False

class LoginIn(BaseModel):
    code: str = ""
    nickname: Optional[str] = ""
    username: Optional[str] = None
    password: Optional[str] = None

@app.post("/api/login")
async def login(body: LoginIn):
    # 用户名+密码登录
    if body.username and body.password:
        un = body.username.strip().lower()
        rows = db.q("SELECT openid, password_hash, nickname FROM users WHERE username=?", (un,))
        if not rows or not rows[0].get("password_hash") or not _verify_pw(body.password, rows[0]["password_hash"]):
            raise HTTPException(401, "用户名或密码错误")
        openid = rows[0]["openid"]
        return {"token": make_token(openid), "openid": openid, "nickname": rows[0].get("nickname") or un}
    if settings.DEV_MODE and (body.code.startswith("dev") or not settings.WX_SECRET):
        openid = "dev-" + (body.code[3:] or "user")
    else:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get("https://api.weixin.qq.com/sns/jscode2session", params={
                "appid": settings.WX_APPID, "secret": settings.WX_SECRET, "js_code": body.code, "grant_type": "authorization_code"})
        d = r.json()
        openid = d.get("openid")
        if not openid: raise HTTPException(400, f"微信登录失败: {d.get('errmsg', '')}")
    if settings.ALLOWED_OPENIDS and openid not in settings.ALLOWED_OPENIDS and not settings.DEV_MODE:
        # 返回 openid 方便家长加入白名单
        raise HTTPException(403, f"不在家庭白名单内，请把这个 openid 加到 ALLOWED_OPENIDS：{openid}")
    db.q("INSERT OR IGNORE INTO users(openid,nickname) VALUES(?,?)", (openid, body.nickname), commit=True)
    return {"token": make_token(openid), "openid": openid}

class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=64)
    nickname: str = ""
    grade: int = 3

@app.post("/api/register")
async def register(body: RegisterIn):
    un = body.username.strip().lower()
    if not re.match(r"^[a-z0-9_]+$", un):
        raise HTTPException(400, "用户名只能用字母、数字、下划线")
    openid = "u_" + un
    rows = db.q("SELECT openid FROM users WHERE openid=? OR username=?", (openid, un))
    if rows:
        raise HTTPException(400, "用户名已存在")
    nick = body.nickname.strip() or un
    grade = max(1, min(6, int(body.grade or 3)))
    db.q("INSERT INTO users(openid, nickname, grade, username, password_hash) VALUES(?,?,?,?,?)",
         (openid, nick, grade, un, _hash_pw(body.password)), commit=True)
    return {"token": make_token(openid), "openid": openid, "nickname": nick}

class ExplainIn(BaseModel):
    subject: str
    grade: int
    question: str = Field(min_length=1, max_length=2000)

@app.post("/api/explain")
async def explain(body: ExplainIn, oid: str = Depends(current_user)):
    chk(body.subject, body.grade); ratelimit.check(oid)
    res = await llm.chat_json(prompts.explain_system(body.subject, body.grade), body.question)
    log(oid, "explain", body.subject, body.grade, body.question, res.get("answer", ""))
    return res

@app.post("/api/explain_image")
async def explain_image(subject: str = Form(...), grade: int = Form(...), note: str = Form(""),
                        file: UploadFile = File(...), oid: str = Depends(current_user)):
    chk(subject, grade); ratelimit.check(oid)
    data = await file.read()
    if len(data) > settings.MAX_IMAGE_MB * 1024 * 1024: raise HTTPException(413, "图片太大了")
    mime = file.content_type if (file.content_type or "").startswith("image/") else "image/jpeg"
    url = f"data:{mime};base64,{base64.b64encode(data).decode()}"
    content = [{"type": "text", "text": "请识别图片中的题目并讲解。" + (note or "")},
               {"type": "image_url", "image_url": {"url": url}}]
    res = await llm.chat_json(prompts.explain_system(subject, grade), content, vision=True)
    log(oid, "explain", subject, grade, res.get("question", "[图片题目]"), res.get("answer", ""))
    return res
@app.post("/api/ocr")
async def ocr_image(file: UploadFile = File(...), oid: str = Depends(current_user)):
    data = await file.read()
    if len(data) > settings.MAX_IMAGE_MB * 1024 * 1024:
        raise HTTPException(413, "image too large")
    try:
        text = ocr.ocr_image(data)
    except Exception as e:
        raise HTTPException(500, "OCR failed: " + str(e))
    return {"text": text}

class PracticeIn(BaseModel):
    subject: str
    grade: int
    topic: str = ""
    count: int = Field(default=5, ge=1, le=10)

@app.post("/api/practice")
async def practice(body: PracticeIn, oid: str = Depends(current_user)):
    chk(body.subject, body.grade); ratelimit.check(oid)
    # 数学：优先用本地生成器（无限题量、零 AI 成本）；topic 对不上任何知识点时回退到题库/AI
    if body.subject == "数学":
        gen = mathgen.generate(body.grade, body.count, body.topic or "")
        if gen:
            return {"source": "generator", "questions": gen}
    bank = db.q("SELECT * FROM questions WHERE grade=? AND subject=?" + (" AND (knowledge_point LIKE ? OR stem LIKE ?)" if body.topic else "")
                + " ORDER BY RANDOM() LIMIT ?", (body.grade, body.subject) + ((f"%{body.topic}%",) * 2 if body.topic else ()) + (body.count,))
    if len(bank) >= body.count:
        return {"source": "bank", "questions": [{"question": b["stem"], "type": b["type"] or "fill",
                "options": json.loads(b["options"] or "[]"), "answer": b["answer"], "explanation": b["explanation"] or ""} for b in bank]}
    ask = f"请出 {body.count} 道小学{body.grade}年级{body.subject}练习题。" + (f"主题/类似题目：{body.topic}" if body.topic else "")
    res = await llm.chat_json(prompts.practice_system(body.subject, body.grade), ask)
    return {"source": "ai", "questions": res.get("questions", [])[:body.count]} if "questions" in res else res

class GradeIn(BaseModel):
    subject: str
    grade: int
    question: str
    answer: str
    reference: str = ""
    explanation: str = ""
    attempt: int = 1

def _norm(s): return str(s).strip().lower().replace("（", "(").replace("）", ")").replace(" ", "").rstrip(".。")

@app.post("/api/grade")
async def grade(body: GradeIn, oid: str = Depends(current_user)):
    chk(body.subject, body.grade)
    attempt = min(max(int(body.attempt or 1), 1), 3)
    if body.reference and _norm(body.reference) == _norm(body.answer):
        res = {"correct": True, "feedback": "答对啦，真棒！🎉", "correct_answer": body.reference, "hint_level": 0}
    else:
        ratelimit.check(oid)
        res = await llm.chat_json(prompts.grade_system(body.subject, body.grade, attempt),
                                  f"题目：{body.question}\n参考答案：{body.reference or '无'}\n孩子的答案：{body.answer}")
        res["hint_level"] = attempt
        if attempt < 3 and not res.get("correct"):
            # 前两次只给提示，不返回答案
            res.pop("correct_answer", None)
            res.pop("explanation", None)
    ok = bool(res.get("correct"))
    log(oid, "practice", body.subject, body.grade, body.question, body.answer, int(ok))
    if not ok and attempt >= 3:
        # 用完3次机会才记入错题本
        db.q("INSERT INTO mistakes(openid,subject,grade,question,my_answer,correct_answer,explanation) VALUES(?,?,?,?,?,?,?)",
             (oid, body.subject, body.grade, body.question, body.answer, res.get("correct_answer", body.reference),
              res.get("explanation", "") or body.explanation or res.get("feedback", "")), commit=True)
    return res

class MistakeIn(BaseModel):
    subject: str
    grade: int
    question: str
    my_answer: str = ""
    correct_answer: str = ""
    explanation: str = ""

@app.get("/api/mistakes")
def list_mistakes(subject: str = "", mastered: int = 0, oid: str = Depends(current_user)):
    sql, a = "SELECT * FROM mistakes WHERE openid=? AND mastered=?", [oid, mastered]
    if subject: sql += " AND subject=?"; a.append(subject)
    return db.q(sql + " ORDER BY id DESC LIMIT 200", a)

@app.post("/api/mistakes")
def add_mistake(m: MistakeIn, oid: str = Depends(current_user)):
    chk(m.subject, m.grade)
    i = db.q("INSERT INTO mistakes(openid,subject,grade,question,my_answer,correct_answer,explanation) VALUES(?,?,?,?,?,?,?)",
             (oid, m.subject, m.grade, m.question, m.my_answer, m.correct_answer, m.explanation), commit=True)
    return {"id": i}

class MistakePatch(BaseModel):
    mastered: int

@app.patch("/api/mistakes/{mid}")
def patch_mistake(mid: int, p: MistakePatch, oid: str = Depends(current_user)):
    db.q("UPDATE mistakes SET mastered=? WHERE id=? AND openid=?", (p.mastered, mid, oid), commit=True)
    return {"ok": True}

@app.delete("/api/mistakes/{mid}")
def del_mistake(mid: int, oid: str = Depends(current_user)):
    db.q("DELETE FROM mistakes WHERE id=? AND openid=?", (mid, oid), commit=True)
    return {"ok": True}

def _today(): return datetime.date.today().isoformat()

def _streak(oid):
    days = {r["day"] for r in db.q("SELECT day FROM checkins WHERE openid=?", (oid,))}
    d, n = datetime.date.today(), 0
    if d.isoformat() not in days: d -= datetime.timedelta(days=1)
    while d.isoformat() in days: n += 1; d -= datetime.timedelta(days=1)
    return n

@app.post("/api/checkin")
def checkin(oid: str = Depends(current_user)):
    db.q("INSERT OR IGNORE INTO checkins(openid,day) VALUES(?,?)", (oid, _today()), commit=True)
    return {"checked": True, "streak": _streak(oid)}

@app.get("/api/checkin")
def checkin_status(oid: str = Depends(current_user)):
    c = db.q("SELECT 1 FROM checkins WHERE openid=? AND day=?", (oid, _today()), one=True)
    return {"checked": bool(c), "streak": _streak(oid)}

@app.get("/api/records")
def records(limit: int = 50, oid: str = Depends(current_user)):
    return db.q("SELECT * FROM records WHERE openid=? ORDER BY id DESC LIMIT ?", (oid, min(limit, 200)))

@app.get("/api/stats")
def stats(oid: str = Depends(current_user)):
    by = db.q("SELECT subject, COUNT(*) total, SUM(CASE WHEN correct=1 THEN 1 ELSE 0 END) right_cnt FROM records "
              "WHERE openid=? AND kind='practice' GROUP BY subject", (oid,))
    ex = db.q("SELECT COUNT(*) n FROM records WHERE openid=? AND kind='explain'", (oid,), one=True)["n"]
    week = db.q("SELECT substr(created_at,1,10) day, COUNT(*) n FROM records WHERE openid=? AND created_at>=date('now','-6 day') GROUP BY day ORDER BY day", (oid,))
    mk = db.q("SELECT COUNT(*) n FROM mistakes WHERE openid=? AND mastered=0", (oid,), one=True)["n"]
    cd = db.q("SELECT COUNT(*) n FROM checkins WHERE openid=?", (oid,), one=True)["n"]
    for b in by: b["accuracy"] = round((b["right_cnt"] or 0) * 100 / b["total"]) if b["total"] else 0
    return {"by_subject": by, "explain_count": ex, "week": week, "open_mistakes": mk, "checkin_days": cd, "streak": _streak(oid)}

# ---------- 课外阅读 / 知识讲解 / 配音 ----------
_AUDIO_DIR = os.getenv("AUDIO_DIR", "/data/audio")
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")

@app.get("/api/stories")
def list_stories(subject: str, grade: int, oid: str = Depends(current_user)):
    chk(subject, grade); ratelimit.check(oid)
    rows = db.q("SELECT id,title,grade,subject,sentences FROM stories WHERE subject=? AND grade=? ORDER BY id",
                (subject, grade))
    return {"stories": [{"id": r["id"], "title": r["title"], "grade": r["grade"], "subject": r["subject"],
                         "sentence_count": len(json.loads(r["sentences"] or "[]"))} for r in rows]}

@app.get("/api/stories/{sid}")
def story_detail(sid: int, oid: str = Depends(current_user)):
    ratelimit.check(oid)
    r = db.q("SELECT * FROM stories WHERE id=?", (sid,), one=True)
    if not r: raise HTTPException(404, "故事不存在")
    sentences = json.loads(r["sentences"] or "[]")
    qs = db.q("SELECT type,stem AS question,options,answer,explanation FROM questions WHERE story_id=? ORDER BY id",
              (sid,))
    return {"id": r["id"], "title": r["title"], "grade": r["grade"], "subject": r["subject"],
            "sentences": sentences,
            "audios": [hashlib.sha1(((s["text"] if isinstance(s, dict) else s).encode("utf-8"))).hexdigest() for s in sentences],
            "questions": [{"type": q["type"], "question": q["question"],
                           "options": json.loads(q["options"] or "[]"),
                           "answer": q["answer"], "explanation": q["explanation"] or ""} for q in qs]}

@app.get("/api/knowledge")
def list_knowledge(subject: str, grade: int, oid: str = Depends(current_user)):
    chk(subject, grade); ratelimit.check(oid)
    rows = db.q("SELECT id,name,content FROM knowledge_points WHERE subject=? AND grade=? ORDER BY id",
                (subject, grade))
    return {"items": [{"id": r["id"], "name": r["name"], "content": r["content"],
                       "audio": hashlib.sha1((r["content"] or "").encode("utf-8")).hexdigest()} for r in rows]}

def _audio_path(sha1, ext):
    return os.path.join(_AUDIO_DIR, sha1[:2], sha1 + ext)

@app.get("/api/audio/{sha1}")
def get_audio(sha1: str, format: str = "opus"):
    # 公开访问：小程序 InnerAudioContext / 安卓 MediaPlayer 发不出 Authorization header；
    # 内容只是 TTS 朗读音频，sha1 格式校验防路径穿越
    if not _SHA1_RE.match(sha1 or ""): raise HTTPException(404, "音频不存在")
    if format == "opus":
        p = _audio_path(sha1, ".opus")
        if not os.path.isfile(p): raise HTTPException(404, "音频不存在")
        return FileResponse(p, media_type="audio/ogg")
    if format == "mp3":
        src = _audio_path(sha1, ".opus")
        if not os.path.isfile(src): raise HTTPException(404, "音频不存在")
        dst = os.path.join(_AUDIO_DIR + "_mp3", sha1[:2], sha1 + ".mp3")
        if not os.path.isfile(dst):
            if not shutil.which("ffmpeg"): raise HTTPException(404, "音频不存在")
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src,
                                "-codec:a", "libmp3lame", "-q:a", "4", dst],
                               timeout=60, capture_output=True)
            if r.returncode != 0 or not os.path.isfile(dst):
                raise HTTPException(404, "音频不存在")
        return FileResponse(dst, media_type="audio/mpeg")
    raise HTTPException(400, "format 只能是 opus 或 mp3")

_WORD_RE = re.compile(r"^[a-zA-Z\-']{1,32}$")
_WORD_AUDIO_DIR = os.path.join(os.path.dirname(settings.DB_PATH), "word_audio")

@app.get("/api/vocab")
def get_vocab(grade: int = 1, oid: str = Depends(current_user)):
    chk("英语", grade)
    rows = db.q("SELECT word, meaning, phonetic, pinyin, grade FROM vocab WHERE grade=? ORDER BY id", (grade,))
    return {"words": rows}

@app.get("/api/word_audio/{word}")
def get_word_audio(word: str, lang: str = "en"):
    # 公开访问：发音按钮直接播，无需登录；word 严格校验防路径穿越
    if not _WORD_RE.match(word or ""): raise HTTPException(404, "音频不存在")
    if lang not in ("en", "zh"): raise HTTPException(400, "lang 只能是 en 或 zh")
    p = os.path.join(_WORD_AUDIO_DIR, f"{word.lower()}_{lang}.mp3")
    if not os.path.isfile(p): raise HTTPException(404, "音频不存在")
    return FileResponse(p, media_type="audio/mpeg")


class LearningVideoIn(BaseModel):
    subject: str
    grade: int = Field(ge=1, le=6)
    knowledge: str = Field(default="", max_length=200)

@app.post("/api/learning_videos")
def learning_video_recommendations(body: LearningVideoIn, oid: str = Depends(current_user)):
    chk(body.subject, body.grade)
    ratelimit.check(oid)
    from .learning_videos import recommend
    return recommend(body.subject, body.grade, body.knowledge)


@app.get("/api/books")
def books_list(oid: str = Depends(current_user)):
    from .books import list_books
    return {"books":list_books()}

@app.get("/api/books/{book_id}")
def book_contents(book_id: str, oid: str = Depends(current_user)):
    from .books import load_book,metadata
    b=load_book(book_id)
    return metadata(b) | {"chapters":[{"index":i,"title":c["title"]} for i,c in enumerate(b["chapters"])]}

@app.get("/api/books/{book_id}/chapters/{index}")
def book_chapter(book_id: str,index: int,oid: str = Depends(current_user)):
    from .books import chapter
    return chapter(book_id,index)

@app.post("/api/books/{book_id}/chapters/{index}/audio/{segment}")
async def book_chapter_audio(book_id:str,index:int,segment:int,oid:str=Depends(current_user)):
    from .books import prepare_audio
    ratelimit.check(oid)
    return await prepare_audio(book_id,index,segment)

@app.get("/api/book_audio/{filename}")
def book_audio_file(filename:str):
    if not re.fullmatch(r"[a-f0-9]{64}\.mp3",filename):raise HTTPException(404,"音频不存在")
    p=os.path.join("/data/book_audio",filename)
    if not os.path.isfile(p):raise HTTPException(404,"音频尚未生成")
    return FileResponse(p,media_type="audio/mpeg")

@app.get("/api/book_image/{filename}")
def book_image_file(filename:str):
    if not re.fullmatch(r"[a-f0-9]{64}\.(?:jpg|png)",filename):raise HTTPException(404,"插图不存在")
    p=os.path.join("/data/book_images",filename)
    if not os.path.isfile(p):raise HTTPException(404,"插图不存在")
    return FileResponse(p,media_type="image/png" if filename.endswith("png") else "image/jpeg")


@app.get("/api/learning_word_audio/{word}")
def learning_word_audio(word: str, lang: str = "en"):
    import re
    if not re.fullmatch(r"[a-zA-Z][a-zA-Z_-]{0,60}",word) or lang not in ("en","zh","example_en","example_zh"):
        raise HTTPException(404,"音频不存在")
    p=os.path.join(os.path.dirname(settings.DB_PATH),"learning_audio",word.lower()+"_"+lang+".mp3")
    if not os.path.isfile(p):raise HTTPException(404,"音频不存在")
    return FileResponse(p,media_type="audio/mpeg")
