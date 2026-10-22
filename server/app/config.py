import os

def _b(v): return str(v).lower() in ("1", "true", "yes", "on")

class Settings:
    def __init__(self):
        self.WX_APPID = os.getenv("WX_APPID", "")
        self.WX_SECRET = os.getenv("WX_SECRET", "")
        self.ALLOWED_OPENIDS = [x.strip() for x in os.getenv("ALLOWED_OPENIDS", "").split(",") if x.strip()]
        self.DEV_MODE = _b(os.getenv("DEV_MODE", "false"))
        self.TOKEN_SECRET = os.getenv("TOKEN_SECRET", "change-me-please")
        self.DB_PATH = os.getenv("DB_PATH", "/data/tutor.db")
        self.LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
        self.LLM_API_KEY = os.getenv("LLM_API_KEY", "")
        self.LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
        self.LLM_VISION_MODEL = os.getenv("LLM_VISION_MODEL", "")
        self.RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "20"))
        self.MAX_IMAGE_MB = int(os.getenv("MAX_IMAGE_MB", "5"))

settings = Settings()
