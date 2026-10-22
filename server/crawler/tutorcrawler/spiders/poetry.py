"""古诗：从 chinese-poetry 开源数据集（GitHub, MIT 许可，古诗本身为公有领域）抓取，
写入知识库(knowledge_points)，并自动生成「补全诗句」填空题。
运行：scrapy crawl poetry  （可 -a source=poetry_xxx 指定 sources.yaml 中别的配置）
"""
import json, re, scrapy
from ..items import QuestionItem, KnowledgeItem
from ..sources import load_sources

class PoetrySpider(scrapy.Spider):
    name = "poetry"

    def __init__(self, source="poetry_tang300", sources_file=None, **kw):
        super().__init__(**kw)
        self.cfg = load_sources(sources_file)["sources"][source]
        self.start_urls = self.cfg["start_urls"]
        self.whitelist = set(self.cfg.get("titles") or [])

    def parse(self, response):
        data = json.loads(response.text)
        if isinstance(data, dict): data = data.get("content") or data.get("data") or [data]
        grade = self.cfg.get("grade", 3)
        for p in data:
            title = p.get("title") or p.get("rhythmic") or ""
            lines = p.get("paragraphs") or []
            if not title or not lines: continue
            if self.whitelist and title not in self.whitelist: continue
            if len("".join(lines)) > self.cfg.get("max_chars", 80): continue  # 小学只要短诗
            author = p.get("author", "")
            yield KnowledgeItem(grade=grade, subject="语文", name=f"{title}·{author}", content="\n".join(lines), source_url=response.url)
            for ln in lines:
                parts = [x for x in re.split(r"[，,。！？；]", ln) if x]
                if len(parts) == 2:
                    yield QuestionItem(grade=grade, subject="语文", knowledge_point="古诗", type="fill",
                                       stem=f"补全诗句（{author}《{title}》）：{parts[0]}，______。", options=[],
                                       answer=parts[1], explanation="\n".join(lines), source_url=response.url)
