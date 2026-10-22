import os, sys, sqlite3, scrapy
from scrapy.http import HtmlResponse, TextResponse, Request
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tutorcrawler.spiders.generic import GenericSpider
from tutorcrawler.spiders.poetry import PoetrySpider
from tutorcrawler.spiders.words import WordsSpider
from tutorcrawler.pipelines import SQLitePipeline

FX = os.path.join(os.path.dirname(__file__), "fixtures"); SRC = os.path.join(FX, "sources_test.yaml")
def resp(name, cls=TextResponse, url="https://example.org/"):
    return cls(url=url + name, body=open(os.path.join(FX, name), "rb").read(), encoding="utf-8")

def run(spider, r, db):
    out = list(spider.parse(r)); items = [o for o in out if not isinstance(o, Request)]
    p = SQLitePipeline(db); p.open_spider(spider)
    for i in items: p.process_item(i, spider)
    p.close_spider(spider); return out, items

def test_all(tmp_path):
    db = str(tmp_path / "t.db")
    out, items = run(GenericSpider(source="g", sources_file=SRC), resp("grade2_math.html", HtmlResponse), db)
    assert len(items) == 3 and items[0]["options"] == ["A. 14", "B. 15"] and items[0]["answer"] == "B"
    assert "进一" in items[0]["explanation"] and items[1]["type"] == "fill"
    assert any(isinstance(o, Request) and o.url.endswith("page2.html") for o in out)
    _, pit = run(PoetrySpider(source="p", sources_file=SRC), resp("poems.json"), db)
    assert any(i.get("answer") == "戊己庚辛" for i in pit) and not any("很长" in str(dict(i)) for i in pit)
    _, wit = run(WordsSpider(source="w", sources_file=SRC), resp("words.csv"), db)
    assert len(wit) == 12
    c = sqlite3.connect(db)
    assert c.execute("select count(*) from questions where subject='数学'").fetchone()[0] == 2  # 去重
    assert c.execute("select count(*) from knowledge_points").fetchone()[0] == 5
    # 重复运行不新增
    run(PoetrySpider(source="p", sources_file=SRC), resp("poems.json"), db)
    assert c.execute("select count(*) from knowledge_points").fetchone()[0] == 5
