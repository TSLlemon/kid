import yaml
from scrapy.utils.project import get_project_settings

def load_sources(path=None):
    path = path or get_project_settings().get("SOURCES_FILE")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
