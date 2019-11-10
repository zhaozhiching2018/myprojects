import scrapy
import re
from bjhSpider.items import BjhspiderItem
from readability import Document
import time

from ..log_config import logger

a=time.time()
b=int(a*1000)

class bjhSpider(scrapy.Spider):
    name = 'bjh'
    start_url = 'https://baijiahao.baidu.com/builder/author/register/index'
    start_urls = ['https://author.baidu.com/list?type=article&tab=2&uk=D0hHfmuMEVka02HZelKA7g&num=3']

    #得到cookie
    def start_requests(self):
        yield scrapy.Request(self.start_url, callback=self.func)

    def func(self, response):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        url = response.url
        html = response.text
        title_list = re.findall(r'"title":(.+?),', html)
        url_list = re.findall(r'"url":(.+?),', html)
        date_list = re.findall(r'"updatedAt":(.+?),', html)
        create_list = re.findall(r'"created_at":(.+?),', html)
        publish_list = re.findall(r'"publish_at":(.+?),', html)  # 发布时间转化为最后的时间
        news_id_list = re.findall(r'"id":"news_(.+?)",', html)
        asyncData = re.findall(r'"asyncData":{(.+?)}', html)
        # print(html)
        readjson = 'https://mbd.baidu.com/webpage?type=homepage&action=interact&format=jsonp&params=%5B%7B%22'
        for i in range(len(title_list)):
            user_type = re.findall(r'"user_type":"(.+?)",', asyncData[i])[0]
            dynamic_id = re.findall(r'"dynamic_id":"(.+?)",', asyncData[i])[0]
            dynamic_type = re.findall(r'"dynamic_type":"(.+?)",', asyncData[i])[0]
            dynamic_sub_type = re.findall(r'"dynamic_sub_type":"(.+?)",', asyncData[i])[0]
            thread_id = re.findall(r'"thread_id":"(.+?)",', asyncData[i])[0]
            feed_id = re.findall(r'"feed_id":"(.+?)"', asyncData[i])[0]
            title=title_list[i]
            url=url_list[i]
            date=date_list[i]
            publish=publish_list[i]
            news_id=news_id_list[i]
            last_publish=publish_list[len(title_list)-1]
            last_date=int(last_publish)-60
            last_datetime=str(last_date)
            time_local = time.localtime(int(publish))
            atime = time.strftime("%Y%m%d %H:%M:%S", time_local)   #发布时间，因date为相对时间，所以用publish时间戳转化代替
            # print(title, url, atime)   #标题，url，发布时间
            if i < len(title_list) - 1:
                readjson += 'user_type%22%3A%22' + user_type + '%22%2C%22' \
                            + 'dynamic_id%22%3A%22' + dynamic_id + '%22%2C%22' \
                            + 'dynamic_type%22%3A%22' + dynamic_type + '%22%2C%22' \
                            + 'dynamic_sub_type%22%3A%22' + dynamic_sub_type + '%22%2C%22' \
                            + 'thread_id%22%3A%22' + thread_id + '%22%2C%22' \
                            + 'feed_id%22%3A%22' + feed_id + '%22%7D%2C%7B%22'
            else:
                readjson += 'user_type%22%3A%22' + user_type + '%22%2C%22' \
                            + 'dynamic_id%22%3A%22' + dynamic_id + '%22%2C%22' \
                            + 'dynamic_type%22%3A%22' + dynamic_type + '%22%2C%22' \
                            + 'dynamic_sub_type%22%3A%22' + dynamic_sub_type + '%22%2C%22' \
                            + 'thread_id%22%3A%22' + thread_id + '%22%2C%22' \
                            + 'feed_id%22%3A%22' + feed_id + '%22%7D%5D'
            url = url.strip('"')
            yield scrapy.Request(
                url,
                meta={'title': title,
                        'url': url,
                       'date': atime,
                    'news_id':news_id,
                          },
                callback=self.article_parse)
        readjson += '&uk=D0hHfmuMEVka02HZelKA7g&_=' + str(b)

        yield scrapy.Request(readjson, callback=self.read_parse)
        if int(last_datetime) >int(a-(3600*24)):  #循环24个小时
            # print(last_datetime)
            yield scrapy.Request('https://author.baidu.com/list?type=article&tab=2&uk=D0hHfmuMEVka02HZelKA7g&ctime={}&num=3'.format(last_datetime), callback=self.parse)   #利用最后一个create_time代替最开始时间戳进行下一个循环抓取

    # 阅读数，评论数(此网页需不断重复更新爬取）
    def read_parse(self, response):
        url = response.url
        logger.info(url)
        html = response.text
        logger.info(html)
        comment_num_list = re.findall(r'"comment_num":"(.+?)",', html)
        read_num_list = re.findall(r'"read_num":(.+?),', html)
        read_id_list = re.findall(r'"3_2001_(.+?)"', html)
        for i in range(len(comment_num_list)):
            comment_num = comment_num_list[i]
            read_num = read_num_list[i]
            read_id = read_id_list[i]
            print(comment_num, read_num)
            item = BjhspiderItem()
            item['comment_num'] = comment_num  # 阅读数
            item['read_num'] = read_num  # 评论数
            item['read_id'] = read_id  # 阅读json数据id    等于  文章json数据id
            yield item

            # yield scrapy.Request(
            #     meta={'comment_num': comment_num,
            #           'read_num': read_num,
            #           'read_id': read_id,
            #           },
            #     callback=self.article_parse)



            # 内容数据
    def article_parse(self, response):
        url = response.url
        title = response.meta['title']
        date = response.meta['date']
        news_id=response.meta['news_id']
        # comment_num=response.mata['comment_num']
        # read_num=response.meta['read_num']
        # read_id=response.meta['read_id']
        doc = Document(response.text)
        content = doc.summary()
        # print(content)
        # 写入item
        item = BjhspiderItem()
        item['url'] = url    #文章链接
        item['title'] = title   #标题
        item['date'] = date    #时间
        item['content'] = content   #标题
        # item['news_id'] = news_id  #文章json数据id 最后可根据此id进行阅读数检验
        yield item
