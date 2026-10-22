import time
from collections import defaultdict, deque
from fastapi import HTTPException
from .config import settings

_hits = defaultdict(deque)

def check(key: str, limit: int | None = None):
    limit = limit or settings.RATE_LIMIT_PER_MIN
    now = time.time(); dq = _hits[key]
    while dq and now - dq[0] > 60: dq.popleft()
    if len(dq) >= limit:
        raise HTTPException(429, "休息一下吧，请一分钟后再试～")
    dq.append(now)
