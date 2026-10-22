"""英语单词：读取开放许可的词表（CSV: word,meaning[,grade] 或 JSON 数组），
写入知识库并生成「看中文写英文」「看英文选中文」题目。
自带词表优先用 server/scripts/import_words.py 导入（无需网络）；
换更大的远端词表时再用爬虫：
  scrapy crawl words -a source=words_remote
"""
import csv, io, json, random, scrapy
from ..items import QuestionItem, KnowledgeItem
from ..sources import load_sources

class WordsSpider(scrapy.Spider):
    name = "words"

    def __init__(self, source="words_remote", sources_file=None, **kw):
        super().__init__(**kw)
        self.cfg = load_sources(sources_file)["sources"][source]
        self.start_urls = self.cfg["start_urls"]

    def parse(self, response):
        t = response.text.strip()
        rows = json.loads(t) if t.startswith("[") else list(csv.DictReader(io.StringIO(t)))
        rows = [r for r in rows if r.get("word") and r.get("meaning")]
        rnd = random.Random(42)
        for r in rows:
            g = int(r.get("grade") or self.cfg.get("grade", 3))
            yield KnowledgeItem(grade=g, subject="英语", name=r["word"], content=r["meaning"], source_url=response.url)
            yield QuestionItem(grade=g, subject="英语", knowledge_point="单词", type="fill",
                               stem=f"写出英文单词：{r['meaning']}", options=[], answer=r["word"], explanation="", source_url=response.url)
            others = [x["meaning"] for x in rows if x is not r]
            if len(others) >= 3:
                ch = rnd.sample(others, 3) + [r["meaning"]]; rnd.shuffle(ch)
                opts = [f"{'ABCD'[i]}. {m}" for i, m in enumerate(ch)]
                yield QuestionItem(grade=g, subject="英语", knowledge_point="单词", type="choice",
                                   stem=f"“{r['word']}” 是什么意思？", options=opts,
                                   answer="ABCD"[ch.index(r["meaning"])], explanation=f"{r['word']}：{r['meaning']}", source_url=response.url)
