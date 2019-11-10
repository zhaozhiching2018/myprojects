# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class BjhspiderItem(scrapy.Item):
    # define the fields for your item here like:
    url = scrapy.Field()
    title = scrapy.Field()
    date = scrapy.Field()
    # media = scrapy.Field()     百家号固定
    content = scrapy.Field()
    comment_num=scrapy.Field()
    read_num=scrapy.Field()
    read_id=scrapy.Field()