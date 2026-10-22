import json, re, httpx
from .config import settings

class LLMError(Exception): pass

async def chat(messages, vision=False, temperature=0.5) -> str:
    if not settings.LLM_API_KEY:
        raise LLMError("服务器未配置 LLM_API_KEY")
    model = (settings.LLM_VISION_MODEL or settings.LLM_MODEL) if vision else settings.LLM_MODEL
    async with httpx.AsyncClient(timeout=90) as c:
        r = await c.post(f"{settings.LLM_BASE_URL}/chat/completions",
                         headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
                         json={"model": model, "messages": messages, "temperature": temperature})
    if r.status_code != 200:
        raise LLMError(f"AI 服务出错({r.status_code})")
    return r.json()["choices"][0]["message"]["content"]

def parse_json(text: str):
    t = text.strip()
    t = re.sub(r"^```(?:json)?|```$", "", t, flags=re.M).strip()
    try:
        return json.loads(t)
    except Exception:
        m = re.search(r"\{.*\}", t, re.S)
        if m:
            try: return json.loads(m.group(0))
            except Exception: pass
    return None

async def chat_json(system, user_content, vision=False):
    txt = await chat([{"role": "system", "content": system}, {"role": "user", "content": user_content}], vision=vision)
    data = parse_json(txt)
    return data if data is not None else {"raw": txt}
