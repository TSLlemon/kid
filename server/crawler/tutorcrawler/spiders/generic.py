"""通用可配置爬虫：在 sources.yaml 里写好 start_urls 和选择器即可，无需写代码。
运行：scrapy crawl generic -a source=<sources.yaml 里的名字>
"""
import scrapy
from ..items import QuestionItem
from ..sources import load_sources

def _sel(node, expr):
    if not expr: return None
    return node.xpath(expr[6:]) if expr.startswith("xpath:") else node.css(expr)

def _text(node, expr):
    s = _sel(node, expr)
    if s is None: return ""
    return " ".join(t.strip() for t in s.getall() if t.strip())

class GenericSpider(scrapy.Spider):
    name = "generic"

    def __init__(self, source=None, sources_file=None, **kw):
        super().__init__(**kw)
        if not source: raise ValueError("请用 -a source=名称 指定 sources.yaml 中的数据源")
        self.cfg = load_sources(sources_file)["sources"][source]
        self.start_urls = self.cfg["start_urls"]
        if self.cfg.get("allowed_domains"): self.allowed_domains = self.cfg["allowed_domains"]
        self.pages = 0

    def parse(self, response):
        c, f = self.cfg, self.cfg["fields"]
        for node in _sel(response, c["item"]):
            opts = [o.strip() for o in _sel(node, f.get("options")).getall() if o.strip()] if f.get("options") else []
            yield QuestionItem(grade=c.get("grade", 0), subject=c["subject"],
                               knowledge_point=_text(node, f.get("knowledge_point")) or c.get("knowledge_point", ""),
                               type="choice" if opts else "fill", stem=_text(node, f["stem"]), options=opts,
                               answer=_text(node, f.get("answer")), explanation=_text(node, f.get("explanation")),
                               source_url=response.url)
        self.pages += 1
        nxt = c.get("next_page")
        if nxt and self.pages < c.get("max_pages", 5):
            href = _sel(response, nxt).get()
            if href: yield response.follow(href, self.parse)
