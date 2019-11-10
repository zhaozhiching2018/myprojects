# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import requests
from sqlalchemy import or_

from .models import User, UserData, News, NewsContent, toutiaoSession


class ToutiaoPipeline(object):

    def __init__(self):
        self.session = toutiaoSession()

    def process_item(self, item, spider):
        user_id = item['user_id']
        user_name = item['user_name']
        if 'user_followers_count' in item:
            # item 是 user
            user_followers_count = item['user_followers_count']
            user_digg_count = item['user_digg_count']
            user_publish_count = item['user_publish_count']

            user = User(user_id=user_id, user_name=user_name)
            user_data = UserData(user_id=user_id, publish_count=user_publish_count, followers_count=user_followers_count, digg_count=user_digg_count)
            user_is_exist = self.session.query(User).filter_by(user_id=user_id).all()
            # 如果已经存在，更新user_data
            if user_is_exist:
                self.session.query(UserData).filter_by(user_id=user_id).update({'publish_count': user_publish_count, 'followers_count': user_followers_count, 'digg_count': user_digg_count})
            else:
                self.session.add(user)
                self.session.add(user_data)
            self.session.commit()
        elif 'url' in item:
            # item 是 news
            url = item['url']
            uniform_url = item['uniform_url']
            title = item['title']
            abstract = ''
            if 'abstract' in item:
                abstract = item['abstract']
            content = item['content']

            media_orig = ''
            if 'media_orig' in item:
                media_orig = item['media_orig']
            reporter = ''
            if 'reporter' in item:
                reporter = item['reporter']  # 事实上头条号没法抓reporter

            date = item['date']
            datestamp = item['datestamp']
            digg_count = item['digg_count']  # 点赞数
            comment_count = item['comment_count']  # 评论数
            forward_count = item['forward_count']  # 转发数
            read_count = 0
            if 'read_count' in item:
                read_count = item['read_count']
            post_type = item['post_type']

            news_is_exist = self.session.query(News).filter(or_(News.url == url, News.uniform_url == uniform_url)).all()

            if not news_is_exist:
                # post https://tower.im/teams/538577/documents/8453/
                meta_info = '{"digg_count": %s, "comment_count": %s, "forward_count": %s}' % (digg_count, comment_count, forward_count)
                data = {'title': title, 'content': content, 'post_type': 6, 'summary': abstract, 'media_orig': media_orig, 'reporter': reporter, 'content_url': url, 'str_date': date, 'username': user_name, 'is_orig': 1, 'meta_info': meta_info, 'spider': 'tth_m'}
                post_url = 'http://tz4.zhangyupai.net:81/mobile/import_ttnews1.php'
                if '请保持关注' not in title and '金融界' not in user_name:
                    response = requests.post(post_url, data=data)
                    print(response.text)
                    # insert into
                    if post_type == 1:
                        # 视频
                        video_watch_count = item['video_watch_count']  # 视频播放量
                        news = News(post_type=post_type, url=url, uniform_url=uniform_url, title=title, abstract=abstract, user_id=user_id, user_name=user_name, media_orig=media_orig, str_date=date, datestamp=datestamp, read_count=read_count, digg_count=digg_count, comment_count=comment_count, forward_count=forward_count, video_watch_count=video_watch_count)
                    else:
                        news = News(post_type=post_type, url=url, uniform_url=uniform_url, title=title, abstract=abstract, user_id=user_id, user_name=user_name, media_orig=media_orig, str_date=date, datestamp=datestamp, read_count=read_count, digg_count=digg_count, comment_count=comment_count, forward_count=forward_count)
                    self.session.add(news)
                    self.session.commit()
                    if news.id:
                        newsContent = NewsContent(news_id=news.id, content=content)
                        self.session.add(newsContent)
                        self.session.commit()
            else:
                update_info = {'uniform_url': uniform_url, 'read_count': read_count, 'digg_count': digg_count, 'comment_count': comment_count, 'forward_count': forward_count}
                self.session.query(News).filter_by(url=url).update(update_info)
                self.session.commit()
        elif 'read_count' in item:
            # 根据uniform_url更新阅读数
            # 注意if的判断顺序，目前暂且这样
            uniform_url = item['uniform_url']
            str_date = item['date']
            read_count = item['read_count']
            update_info = {'read_count': read_count}
            data = self.session.query(News).filter_by(uniform_url=uniform_url, str_date=str_date).update(update_info)
            if not data and 'title' in item:
                title = item['title']
                update_info['uniform_url'] = uniform_url
                self.session.query(News).filter_by(user_id=user_id, title=title, str_date=str_date).update(update_info)
            self.session.commit()
            pass

        return item
