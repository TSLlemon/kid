import hmac, hashlib, base64, time, json
from fastapi import Header, HTTPException
from .config import settings

def make_token(openid: str, days=30) -> str:
    body = base64.urlsafe_b64encode(json.dumps({"o": openid, "e": int(time.time()) + days * 86400}).encode()).decode()
    sig = hmac.new(settings.TOKEN_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"

def parse_token(tok: str):
    try:
        body, sig = tok.split(".")
        if not hmac.compare_digest(sig, hmac.new(settings.TOKEN_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()):
            return None
        d = json.loads(base64.urlsafe_b64decode(body))
        return d["o"] if d["e"] > time.time() else None
    except Exception:
        return None

def current_user(authorization: str = Header(default="")) -> str:
    tok = authorization.replace("Bearer ", "").strip()
    oid = parse_token(tok) if tok else None
    if not oid:
        raise HTTPException(401, "请先登录")
    if settings.ALLOWED_OPENIDS and oid not in settings.ALLOWED_OPENIDS and not settings.DEV_MODE:
        raise HTTPException(403, "不在家庭白名单内")
    return oid
