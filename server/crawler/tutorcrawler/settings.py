import os
BOT_NAME = "tutorcrawler"
SPIDER_MODULES = ["tutorcrawler.spiders"]
ROBOTSTXT_OBEY = True                 # 遵守 robots.txt
DOWNLOAD_DELAY = float(os.getenv("CRAWL_DELAY", "2"))   # 礼貌延迟
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS_PER_DOMAIN = 1
AUTOTHROTTLE_ENABLED = True
HTTPCACHE_ENABLED = True              # 本地缓存，重复运行不重复请求
USER_AGENT = "KidTutorFamilyBot/1.0 (personal family use; contact: your-email@example.com)"
ITEM_PIPELINES = {"tutorcrawler.pipelines.SQLitePipeline": 300}
DB_PATH = os.getenv("DB_PATH", "/data/tutor.db")
SOURCES_FILE = os.getenv("SOURCES_FILE", os.path.join(os.path.dirname(os.path.dirname(__file__)), "sources.yaml"))
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"
