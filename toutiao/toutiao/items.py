# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ToutiaoItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    user_id = scrapy.Field()  # 头条用户id
    user_name = scrapy.Field()
    user_type = scrapy.Field()  # 头条号类型：机构，媒体，大V（自媒体）
    user_followers_count = scrapy.Field()  # 头条号粉丝数
    user_digg_count = scrapy.Field()  # 头条号获赞总数
    user_publish_count = scrapy.Field()  # 头条号的创作总数
    url = scrapy.Field()
    uniform_url = scrapy.Field()
    title = scrapy.Field()
    abstract = scrapy.Field()  # 摘要
    content = scrapy.Field()  # 内容

    media_orig = scrapy.Field()
    reporter = scrapy.Field()
    date = scrapy.Field()  # 发布日期
    datestamp = scrapy.Field()  # 发布时间戳
    read_count = scrapy.Field()  # 阅读数
    digg_count = scrapy.Field()  # 点赞数
    comment_count = scrapy.Field()  # 评论数
    forward_count = scrapy.Field()  # 转发数
    video_watch_count = scrapy.Field()  # 视频播放量
    post_type = scrapy.Field()  # 内容类别：视频/文章/问答/转发/微头条
