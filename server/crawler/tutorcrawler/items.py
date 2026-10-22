import scrapy

class QuestionItem(scrapy.Item):
    grade = scrapy.Field(); subject = scrapy.Field(); knowledge_point = scrapy.Field(); type = scrapy.Field()
    stem = scrapy.Field(); options = scrapy.Field(); answer = scrapy.Field(); explanation = scrapy.Field(); source_url = scrapy.Field()

class KnowledgeItem(scrapy.Item):
    grade = scrapy.Field(); subject = scrapy.Field(); name = scrapy.Field(); content = scrapy.Field(); source_url = scrapy.Field()
