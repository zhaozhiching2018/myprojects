# -*- coding: utf-8 -*-
import json
import time
import datetime

import scrapy

from ..items import ToutiaoItem
from ..models import mediaSession, Media
from ..log_config import logger

today = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d')
weekago = datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(-8), '%Y%m%d')

'''
class Toutiaohao_pcSpider(scrapy.Spider):
    name = 'toutiaohao_pc'
    max_behot_time = "0"
    users_id = [56930773555, ]

    def get_js(self, param):
        with open('toutiao-TAC.sign.js', 'r', encoding='utf8') as f:
            line = f.readline()
            htmlstr = ""
            while line:
                htmlstr = htmlstr + line
                line = f.readline()
            ctx = execjs.compile(htmlstr)
            return ctx.call("get_as_cp_signature", param)

    def start_requests(self):
        for user_id in self.users_id:
            headers = {'referer': f'https://www.toutiao.com/c/user/{user_id}/'}
            max_behot_time = 0
            data = self.get_js(max_behot_time)
            honey = json.loads(data)
            eas, ecp, esign = honey['as'], honey['cp'], honey['_signature']
            datas_url = f'https://www.toutiao.com/c/user/article/?page_type=1&user_id={user_id}&max_behot_time={max_behot_time}&count=20&as={eas}&cp={ecp}&_signature={esign}'
            yield scrapy.Request(datas_url, headers=headers, callback=self.parse)
            time.sleep(1+random.random()*2)

    def parse(self, response):
        datas = json.loads(response.text)
        print(datas)
'''


class Toutiaohao_mSpider(scrapy.Spider):
    name = 'tth_m'

    def __init__(self, id_=''):
        self.users_id = {
            56930773555: '嘉实基金',
            50832472687: '嘉实财富',
            5197909475: '金贝塔',
        }
        if id_:
            self.users_id[id_] = ''
        for media, user_id in self.get_medias():
            self.users_id[user_id] = media

    def get_medias(self):
        session = mediaSession()
        # 头条渠道整体的post_type是6
        for media in session.query(Media).filter_by(post_type=6).all():
            user_id = media.link.strip()
            if user_id.isdigit():
                yield media.media, int(user_id)

    def timestamp2time(self, timestamp):
        timeArray = time.localtime(timestamp)
        return time.strftime("%Y%m%d", timeArray)

    def get_news_date(self, news):
        if 'publish_time' in news:
            date = self.timestamp2time(news['publish_time'])
        elif 'create_time' in news:
            date = self.timestamp2time(news['create_time'])
        elif 'raw_data' in news:
            raw_data = news['raw_data']
            if 'content' in raw_data and 'answer' in raw_data['content']:
                date = self.timestamp2time(raw_data['content']['answer']['create_time'])
            elif 'comment_base' in raw_data:
                if 'create_time' in raw_data:
                    date = self.timestamp2time(raw_data['create_time'])
                elif 'create_time' in raw_data['comment_base']:
                    date = self.timestamp2time(raw_data['comment_base']['create_time'])
        return date

    def start_requests(self):
        for user_id, user_name in self.users_id.items():
            start_url = f'https://lf.snssdk.com/api/feed/profile/v1/?category=profile_all&visited_uid={user_id}&count=20&offset=0'
            yield scrapy.Request(start_url, meta={'user_id': user_id, 'user_name': user_name}, callback=self.parse)
            user_info_url = f'https://lf.snssdk.com/user/profile/homepage/v7/?user_id={user_id}'
            yield scrapy.Request(user_info_url, meta={'user_id': user_id}, callback=self.user_info_parse)

    def parse(self, response):
        user_id = response.meta['user_id']
        user_name = response.meta['user_name']
        results = json.loads(response.text)
        datas, has_more, offset = results['data'], results['has_more'], results['offset']

        if datas:
            oldest_news = json.loads(datas[-1]['content'])
            oldest_date = self.get_news_date(oldest_news)

            for data in datas:
                news = json.loads(data['content'])
                item = ToutiaoItem()
                item['user_id'] = user_id
                item['user_name'] = user_name
                item['date'] = self.get_news_date(news)
                if item['date'] >= weekago:
                    has_video = news['has_video']
                    if has_video:
                        # 视频
                        video_id = news['group_id']
                        item['title'] = news['title']
                        item['url'] = news['display_url']
                        item['uniform_url'] = f'https://www.toutiao.com/a{video_id}'
                        item['datestamp'] = news['publish_time']
                        item['comment_count'] = news['comment_count']  # 评论数
                        item['forward_count'] = news['forward_info']['forward_count']  # 转发数
                        item['post_type'] = 1
                        video_info_url = f'https://a3.pstatp.com/article/full/22/1/{video_id}/{video_id}/0/0/0/0'
                        yield scrapy.Request(video_info_url, meta={'item': item}, callback=self.video_parse)
                    elif 'publish_time' in news:
                        # 文章
                        article_id = news['group_id']  # 文章id
                        item['title'] = news['title']
                        item['url'] = news['display_url']
                        item['uniform_url'] = f'https://www.toutiao.com/a{article_id}'
                        if 'Abstract' in news:
                            item['abstract'] = news['Abstract']
                        item['datestamp'] = news['publish_time']
                        item['user_name'] = news['user_info']['name']
                        item['comment_count'] = news['comment_count']  # 评论数
                        item['forward_count'] = news['forward_info']['forward_count']  # 转发数
                        item['post_type'] = 2
                        article_info_url = f'https://a3.pstatp.com/article/full/22/1/{article_id}/{article_id}/0/0/0/0'
                        yield scrapy.Request(article_info_url, meta={'item': item}, callback=self.article_parse)
                    elif 'create_time' in news:
                        # 头条
                        thread_id = news['thread_id']
                        item['title'] = news['title']
                        item['url'] = news['share_url'].split('?')[0]
                        item['uniform_url'] = f'https://www.toutiao.com/a{thread_id}'
                        item['content'] = news['content']
                        item['datestamp'] = news['create_time']
                        item['user_name'] = news['user']['name']
                        item['comment_count'] = news['comment_count']  # 评论数
                        item['forward_count'] = news['forward_info']['forward_count']  # 转发数
                        item['digg_count'] = news['digg_count']
                        item['post_type'] = 3
                        yield item
                    elif 'raw_data' in news:
                        raw_data = news['raw_data']
                        if 'content' in raw_data and 'answer' in raw_data['content']:
                            # 问答
                            item['title'] = raw_data['content']['question']['title']
                            item['url'] = f"https://m.zjurl.cn/answer/{raw_data['content']['answer']['ansid']}/"
                            item['uniform_url'] = f"https://www.toutiao.com/a{raw_data['content']['answer']['ansid']}"
                            item['datestamp'] = raw_data['content']['answer']['create_time']
                            item['content'] = raw_data['content']['answer']['abstract_text']  # 完整纯文本，不是摘要
                            item['comment_count'] = raw_data['content']['answer']['comment_count']  # 评论数
                            item['digg_count'] = raw_data['content']['answer']['digg_count']  # 点赞数
                            item['forward_count'] = raw_data['content']['answer']['forward_count']  # 转发数
                            item['user_name'] = raw_data['content']['user']['uname']
                            # item['follow_count'] = raw_data['content']['follow_count'] 问题关注数？
                            # item['nice_ans_count'] = raw_data['content']['nice_ans_count'] # 问题收藏数？
                            item['post_type'] = 4
                            yield item
                        elif 'comment_base' in raw_data:
                            # 转发
                            item['url'] = f'https://lf.snssdk.com/ugc/comment/repost_detail/v2/info/?comment_id={raw_data["id"]}'
                            item['uniform_url'] = f'https://www.toutiao.com/a{raw_data["id"]}'
                            item['title'] = ''
                            if 'create_time' in raw_data:
                                item['datestamp'] = raw_data['create_time']
                            elif 'create_time' in raw_data['comment_base']:
                                item['datestamp'] = raw_data['comment_base']['create_time']
                            article_id = raw_data['origin_common_content']['group_id']
                            item['content'] = '\n'.join([raw_data['content'], raw_data['origin_common_content']['title'], f'https://a3.pstatp.com/article/full/22/1/{article_id}/{article_id}/0/0/0/0'])
                            item['forward_count'] = raw_data['comment_base']['action']['forward_count']
                            item['digg_count'] = raw_data['comment_base']['action']['digg_count']
                            item['comment_count'] = raw_data['comment_base']['action']['comment_count']
                            item['user_name'] = raw_data['user']['info']['name']
                            item['media_orig'] = raw_data['origin_common_content']['title'].split('：')[0]
                            item['post_type'] = 5
                            yield item
                else:
                    logger.info('is old')
            # 如果oldest_date是在weekago以前的，不翻页
            if has_more and oldest_date >= weekago:
                next_page_url = f"https://lf.snssdk.com/api/feed/profile/v1/?category=profile_all&visited_uid={user_id}&count=20&offset={offset}"
                yield scrapy.Request(next_page_url, meta={'user_id': user_id, 'user_name': user_name}, callback=self.parse)
        else:
            logger.warning(f'result count: {len(datas)}')

    def article_parse(self, response):
        news = json.loads(response.text)['data']
        item = response.meta['item']
        item['content'] = news['content']
        # item['url'] = news['url']
        item['digg_count'] = news['digg_count']  # 点赞数
        yield item

    def video_parse(self, response):
        news = json.loads(response.text)['data']
        item = response.meta['item']
        item['url'] = news['url']
        item['content'] = news['content']
        item['video_watch_count'] = news['video_detail_info']['video_watch_count']
        item['digg_count'] = news['digg_count']  # 点赞数
        yield item

    def user_info_parse(self, response):
        """
        头条号的个人信息页
        """
        data = json.loads(response.text)['data']
        item = ToutiaoItem()
        item['user_id'] = response.meta['user_id']
        item['user_name'] = data['name']
        item['user_followers_count'] = data['followers_count']
        item['user_digg_count'] = data['digg_count']
        item['user_publish_count'] = data['publish_count']
        yield item


class Toutiaohao_mwebSpider(scrapy.Spider):
    name = 'tth_m_web'

    def __init__(self, id_=''):
        self.users_id = {
            56930773555: '嘉实基金',
            50832472687: '嘉实财富',
            5197909475: '金贝塔',
        }
        if id_:
            self.users_id[id_] = ''
        for media, user_id in self.get_medias():
            self.users_id[user_id] = media

    def get_medias(self):
        session = mediaSession()
        # 头条渠道整体的post_type是6
        for media in session.query(Media).filter_by(post_type=6).all():
            user_id = media.link.strip()
            if user_id.isdigit():
                yield media.media, int(user_id)

    def timestamp2time(self, timestamp):
        timeArray = time.localtime(timestamp)
        return time.strftime("%Y%m%d", timeArray)

    def get_news_date(self, news):
        if 'publish_time' in news:
            date = self.timestamp2time(news['publish_time'])
        elif 'create_time' in news:
            date = self.timestamp2time(news['create_time'])
        elif 'raw_data' in news:
            raw_data = news['raw_data']
            if 'content' in raw_data and 'answer' in raw_data['content']:
                date = self.timestamp2time(raw_data['content']['answer']['create_time'])
            elif 'comment_base' in raw_data:
                date = self.timestamp2time(raw_data['create_time'])
        return date

    def start_requests(self):
        for user_id, user_name in self.users_id.items():
            m_web_url = f"http://i.snssdk.com/dongtai/list/v9/?user_id={user_id}&max_cursor=0&callback="
            yield scrapy.Request(m_web_url, meta={'user_id': user_id, 'user_name': user_name}, callback=self.m_web_parse)

    def m_web_parse(self, response):
        """
        通过uniform_url, title, user_id, str_date更新阅读数，补丁作用
        """
        user_id = response.meta['user_id']
        user_name = response.meta['user_name']
        datas = json.loads(response.text)['data']

        for data in datas['data']:
            item = ToutiaoItem()
            item['user_id'] = user_id
            item['user_name'] = user_name
            item_id_str = data['id_str']
            item['date'] = self.get_news_date(data)
            item['uniform_url'] = f"https://www.toutiao.com/a{item_id_str}"
            if 'group' in data and 'title' in data['group']:
                item['title'] = data['group']['title']
            item['read_count'] = data['read_count']
            yield item
        if datas['data']:
            oldest_date = self.get_news_date(datas['data'][-1])
            if oldest_date >= weekago and datas['has_more']:
                max_cursor = datas['max_cursor']
                next_page_url = f"http://i.snssdk.com/dongtai/list/v9/?user_id={user_id}&max_cursor={max_cursor}&callback="
                yield scrapy.Request(next_page_url, meta={'user_id': user_id, 'user_name': user_name}, callback=self.m_web_parse)
