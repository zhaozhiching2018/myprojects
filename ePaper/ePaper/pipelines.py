# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re
import hashlib
import datetime
import asyncio
from collections import defaultdict

import aiohttp
import MySQLdb
from MySQLdb import cursors
from lxml import etree

from .log_config import logger


class EpaperPipeline(object):
    """
    def __init__(self):
        self.conn = MySQLdb.connect(host='120.26.211.213', user='huanghai', password='huanghai_password', database='news_caiji', charset='utf8mb4', cursorclass=cursors.SSCursor)
        self.cur = self.conn.cursor()

    def process_item(self, item, spider):
        url = item['url']
        date = item['date']
        reporter = item['reporter']
        title = item['title']
        media = item['media']
        media_orig = item['media_orig']
        content = '[ePaper]' + item['content']
        sql = "insert into news1 (media, media_orig, str_date, title, content, content_url, reporter) values (%s, %s, %s, %s, %s, %s, %s)"
        self.cur.execute(sql, (media, media_orig, date, title, content, url, reporter))
        sql = "insert into news_xt (media, media_orig, str_date, title, content, content_url, reporter) values (%s, %s, %s, %s, %s, %s, %s)"
        self.cur.execute(sql, (media, media_orig, date, title, content, url, reporter))
        self.conn.commit()
        return item

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()
    """
    api = 'http://tz4.zhangyupai.net:81/mobile/import_xtnews1.php'

    async def save_one(self, info):
        title, content, summary, media_orig, reporter, content_url, str_date, name = info
        data = {'title': title, 'content': content, 'summary': summary, 'media_orig': media_orig, 'reporter': reporter, 'content_url': content_url, 'str_date': str_date, 'spider_channel': 'scrapy', 'spider': name}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.api, data=data) as resp:
                    text = await resp.text(encoding=None, errors="ignore")
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.exception(f'ERROR: {e}')

    def process_item(self, item, spider):
        url = item['url']
        date = item['date']
        reporter = item['reporter']
        title = item['title']
        media_orig = item['media_orig']
        content = '[xt]' + item['content']

        html = etree.HTML(item['content'])
        text = ''.join(i for i in html.xpath('//text()') if i).strip()
        if len(text) > 80:
            abstract = text[:80]
        else:
            abstract = text[:int(0.5*len(text))]
        if abstract:
            info = (title, content, abstract, media_orig, reporter, url, date, spider.name)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.gather(*[self.save_one(info)]))
        return item


class EpaperPipeline2:
    def __init__(self):
        self.MAX_SUMMARY_LENGTH = 250
        pattern = '\[(.+?)\]'
        self.prog = re.compile(pattern)

        self.conn = MySQLdb.connect(host='120.26.106.222', user='julai01', password='Sh51785136@sh', database='jijin', charset='utf8mb4', cursorclass=cursors.SSCursor)
        self.cur = self.conn.cursor()
        sql = 'select key1, `keys` from config where del_flag=0'
        self.cur.execute(sql)
        self.companies = {}
        for key1, keys in self.cur:
            keys = keys.split()
            self.companies[key1] = [key1]
            self.companies[key1].extend([i.strip('(').strip(')').strip('（').strip('）') for i in keys if key1 not in i])

    def process_item(self, item, spider):
        url = item['url']
        date = item['date']
        reporter = item['reporter']
        title = item['title']
        media = item['media']
        media_orig = item['media_orig']
        content = '[ePaper]' + item['content']
        html = etree.HTML(item['content'])
        text = '\n'.join(i.strip() for i in html.xpath('//text()') if i.strip())
        r_finds = self.prog.findall(text)
        if r_finds:
            fpart, bpart = text.split(f'[{r_finds[-1]}]')
            # 去除开头的空格空行
            text = f'{fpart}[{r_finds[-1]}]{bpart.strip()}'

        abstract = defaultdict(list)
        for sentence in text.split('。'):
            for company, words in self.companies.items():
                for word in words:
                    if word in sentence:
                        abstract[company].append(f'{sentence.strip()}。')

        cx_abstract = text[:80].strip()
        if abstract:
            md5link = hashlib.md5(url.encode('utf8')).hexdigest()
            sql = "insert into cx0308 (key1, title, summary, md5link, link, str_date, media, reporter, content, news_id, parse_media, spider) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            self.cur.execute(sql, ('scrapy', title, cx_abstract, md5link, url, ''.join(date.split('-')), media_orig, reporter, content, 0, reporter, spider.name))
            self.conn.commit()
            sql = "SELECT LAST_INSERT_ID()"
            self.cur.execute(sql)
            post_id = self.cur.fetchone()[0]
            sql = "select id, key1 from hisinfo_cx where post_id=%s"
            self.cur.execute(sql, (post_id,))
            old_keys = {key1: id_ for id_, key1 in self.cur}
            if old_keys:
                sql = "update hisinfo_cx set summary=%s where id=%s"
                for key1, id_ in old_keys.items():
                    self.cur.execute(sql, (''.join(abstract[key1])[:self.MAX_SUMMARY_LENGTH], id_))
            sql = "insert into hisinfo_cx (post_id, summary, post_type, key1, str_date, media, media_channel, reporter, readnum, platform, category, tags, scores, note, action) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s" + ', "", "", 0, "", 0)'
            for key1, sentences in abstract.items():
                if key1 in old_keys:
                    continue
                self.cur.execute(sql, (post_id, ''.join(sentences)[:self.MAX_SUMMARY_LENGTH], 0, key1, ''.join(date.split('-')), media_orig, media, reporter, 0, ''))

            sql = "select distinct media from media_status"
            self.cur.execute(sql)
            self.medias = {i[0] for i in self.cur}
            last_update = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
            if media in self.medias:
                sql = "update media_status set link=%s, last_update=%s where media=%s"
                self.cur.execute(sql, (url, last_update, media))
            else:
                sql = "insert into media_status (media, link, last_update) values (%s, %s, %s)"
                self.cur.execute(sql, (media, url, last_update))

            self.conn.commit()
        return item

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()


class EpaperPipeline3:
    api = 'http://tz5.zhangyupai.net:8080/import_tznews'

    async def save_one(self, info):
        title, content, post_type, summary, media_orig, reporter, content_url, str_date = info
        data = {'title': title, 'content': content, 'post_type': post_type, 'summary': summary, 'media_orig': media_orig, 'reporter': reporter, 'content_url': content_url, 'str_date': str_date, 'target_wordid': 0, 'target_stockid': 0}
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.api, data=data) as resp:
                    # text = await resp.text(encoding=None, errors='ignore')
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.exception(f'ERROR: {e}')

    def process_item(self, item, spider):
        url = item['url']
        date = item['date']
        reporter = item['reporter']
        title = item['title']
        media = item['media']
        media_orig = media
        if 'media_orig' in item:
            media_orig = item['media_orig']
        content = '[ePaper]' + item['content']
        post_type = 31
        if 'post_type' in item:
            post_type = item['post_type']

        html = etree.HTML(item['content'])
        text = ''.join(html.xpath('//text()')).strip()
        if len(text) > 80:
            abstract = text[:80]
        else:
            abstract = text[:int(0.5*len(text))]
        if abstract:
            info = (title, content, post_type, abstract, media_orig, reporter, url, date)
            loop = asyncio.get_event_loop()
            loop.run_until_complete(asyncio.gather(*[self.save_one(info)]))
        return item
