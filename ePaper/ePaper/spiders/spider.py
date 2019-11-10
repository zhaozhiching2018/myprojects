# -*- coding: utf-8 -*-
import time
import hashlib
from datetime import datetime

import scrapy
from readability import Document

from ePaper.items import EpaperItem
from ePaper.log_config import logger
from ePaper.urls import old_urls, today, yesterday

# today '%Y-%m-%d'
md5urls = old_urls()


def is_alreadyexist(article_url):
    return hashlib.md5(article_url.encode('utf8')).hexdigest() in md5urls


class _21jjSpider(scrapy.Spider):
    name = '21jj'
    allowed_domains = ['21jingji.com']
    start_urls = ['http://epaper.21jingji.com/html/{}/{}/node_1.htm'.format(today[:7], today[-2:])]

    def parse(self, response):
        url = response.url
        article_urls = response.xpath('//div[@class="news_list"]/ul/li/a/@href').extract()
        part_url = url.split('node')[0]
        for article_url in article_urls:
            real_url = part_url + article_url
            if is_alreadyexist(real_url):
                logger.info(f'{real_url} already exist')
                continue
            yield scrapy.Request(real_url, callback=self.article_parse, dont_filter=True)

    def article_parse(self, response):
        url = response.url
        title = response.xpath('//h1/text()').extract()[0]
        if not is_alreadyexist(url) and title != '广告':
            date = response.url.split('html/')[1].split('/content')[0].replace('/', '-')
            media = '21世纪经济报道'
            media_orig = '21世纪经济报道'
            reporters = response.xpath('//div[@class="news_author"]/text()').extract()
            reporter = ''
            if reporters:
                reporter = reporters[0]
            doc = Document(response.text)
            content = doc.summary()

            item = EpaperItem()
            item['url'] = url
            item['title'] = title
            item['date'] = date
            item['media'] = media
            item['media_orig'] = media_orig
            item['reporter'] = reporter
            item['content'] = content
            yield item


class FzwbSpider(scrapy.Spider):
    name = 'fzwb'
    start_urls = ['http://dzb.fawan.com/html/{}/{}/node_2.htm'.format(yesterday[:-3], yesterday[-2:])]

    def parse(self, response):
        logger.info('now page url is {}'.format(response.url))
        if response.url.split('/')[-1] != 'node_2.htm':
            article_urls = ['http://dzb.fawan.com/html/{}/{}/'.format(yesterday[:-3], yesterday[-2:]) + i for i in response.xpath('//td[@height="25"]/a[@class="mulu"]/@href').extract()]
            for article_url in article_urls:
                if is_alreadyexist(article_url):
                    continue
                yield scrapy.Request(article_url, callback=self.article_parse)

        pages = response.xpath('//a[@class="preart"]/text()').extract()
        if pages and pages[-1] == '下一版':
            next_page_url = 'http://dzb.fawan.com/html/{}/{}/'.format(yesterday[:-3], yesterday[-2:]) + response.xpath('//a[@class="preart"]/@href').extract()[-1]
            logger.info('next page url is {}'.format(next_page_url))
            yield scrapy.Request(next_page_url, callback=self.parse)

    def article_parse(self, response):
        url = response.url
        title = response.xpath('//tr[@valign="top"]/td/strong/text()').extract()[0].strip()
        date = ''.join(yesterday.split('-'))
        media = '法制晚报'
        media_orig = '法制晚报'
        reporter = ''
        text_list = response.xpath('//div[@id="ozoom"]/p/text()').extract()
        if text_list:
            if '（记者' in text_list[0]:
                reporter = text_list[0].split('记者')[1].split('）')[0].strip()
            if '文/' in text_list[-1]:
                reporter = text_list[-1].split('文/')[1].strip()
        doc = Document(response.text)
        content = doc.summary()
        if len(content) < 30:
            content = '\r\n'.join(text_list)

        item = EpaperItem()
        item['url'] = url
        item['title'] = title
        item['date'] = date
        item['media'] = media
        item['media_orig'] = media_orig
        item['reporter'] = reporter
        item['content'] = content
        yield item


class JjckbSpider(scrapy.Spider):
    name = 'jjckb'
    allowed_domains = ['jjckb.cn']
    start_urls = ['http://dz.jjckb.cn/www/pages/webpage2009/html/{}/{}/node_2.htm'.format(today[:-3], today[-2:])]

    def parse(self, response):
        article_urls = response.xpath('//tbody/tr/td/ul/li/a/@href').extract()
        article_urls = ['http://dz.jjckb.cn/www/pages/webpage2009/html/{}/{}/'.format(today[:-3], today[-2:]) + i for i in article_urls]
        for article_url in article_urls:
            if is_alreadyexist(article_url):
                continue
            yield scrapy.Request(article_url, callback=self.article_parse, dont_filter=True)
        pages = response.xpath('//tbody/tr/td/span/a/@href').extract()
        if len(pages) == 4:
            next_page_url = 'http://dz.jjckb.cn/www/pages/webpage2009/html/{}/{}/'.format(today[:-3], today[-2:]) + pages[-1]
            logger.info('fetch next page: {}'.format(next_page_url))
            yield scrapy.Request(article_url, callback=self.parse, dont_filter=True)
        elif len(pages) == 2:
            if pages[0] == 'node_3.htm':
                next_page_url = 'http://dz.jjckb.cn/www/pages/webpage2009/html/{}/{}/node_3.htm'.format(today[:-3], today[-2:])
                logger.info('fetch next page: {}'.format(next_page_url))
                yield scrapy.Request(next_page_url, callback=self.parse, dont_filter=True)

    def article_parse(self, response):
        url = response.url
        title = response.xpath('//td[@class="hei16b"]/text()').extract()[0]
        info = response.xpath('//td[@class="black12"]/text()').extract()[0].split('\r\n ')
        reporter = info[2].strip().strip('□').strip('记者 ')
        reporter = ' '.join([i for i in reporter.split() if '报道' not in i and '实习' not in i])
        date = info[1].strip()
        if '来源：' in info[-1]:
            media = info[-1].strip().strip('来源：')
        else:
            media = ''
        media_orig = '经济参考报'
        doc = Document(response.text)
        content = doc.summary()
        logger.info('{} fetched.'.format(title))

        item = EpaperItem()
        item['url'] = url
        item['title'] = title
        item['date'] = date
        item['media'] = media
        item['media_orig'] = media_orig
        item['reporter'] = reporter
        item['content'] = content
        yield item


class ShzqbSpider(scrapy.Spider):
    name = 'shzqb'
    # allowed_domains = ['paper.cnstock.com']
    start_urls = ['http://paper.cnstock.com/html/{}/{}/node_3.htm'.format(today[:-3], today[-2:])]

    def start_requests(self):
        yield scrapy.Request('http://passport.cnstock.com/PassPortWeb/services/userBase/login?username=GongWL&password=654321&_={}'.format(int(time.time()*1000)), callback=self.parse_main_page)

    def parse_main_page(self, response):
        yield scrapy.Request('http://paper.cnstock.com/html/{}/{}/node_3.htm'.format(today[:-3], today[-2:]), callback=self.parse)

    def parse(self, response):
        if '天后到期' in response.text:
            url = response.xpath('//div[@id="floatBox"]/a/@href').extract()[-1]
            yield scrapy.Request(url, callback=self.parse, dont_filter=True)
        else:
            page_titles = [i for i in response.xpath('//a[@class="list_title"]/text()').extract()]
            page_num = [i.split('：')[0] for i in page_titles]
            page_titles = [i.split('：')[1] for i in page_titles]
            article_urls = []
            for num in page_num:
                url = ['http://paper.cnstock.com/html/{}/{}/'.format(today[:-3], today[-2:]) + i for i in response.xpath('//ul[@id="{}"]/li/a/@href'.format(num+'a')).extract()]
                article_urls.append(url)
            logger.info(article_urls)
            logger.info(response.text)
            for page_title, article_url in zip(page_titles, article_urls):
                if page_title == '信息披露':
                    continue
                for i in article_url:
                    if is_alreadyexist(i):
                        logger.info('{} filter'.format(i))
                        continue
                    yield scrapy.Request(i, callback=self.article_parse)

    def article_parse(self, response):
        url = response.url
        title = ''.join(response.xpath('//div[@id="content_title"]/text()').extract())
        title = title.strip()
        date = today
        media = '上海证券报'
        media_orig = '上海证券报'
        tmp1 = response.xpath('//div[@id="content_article"]//table/tbody/tr/td/text()').extract()
        tmp2 = response.xpath('//founder-content/p/text()').extract()[:5]
        reporter = ''
        if tmp1:
            if '□' in tmp1[-1]:
                reporter = tmp1[-1].split('□')[1]
        for i in tmp2:
            if '记者 ' in i:
                if '○' in i:
                    reporter = i.split('记者 ')[1].split('○')[0]
                else:
                    reporter = i.split('记者 ')[1]
        doc = Document(response.text)
        content = doc.summary()
        if len(content) < 30:
            content = '\r\n'.join(response.xpath('//founder-content/p/text()').extract())

        item = EpaperItem()
        item['url'] = url
        item['title'] = title
        item['date'] = date
        item['media'] = media
        item['media_orig'] = media_orig
        item['reporter'] = reporter
        item['content'] = content
        yield item


class XjbSpider(scrapy.Spider):
    name = 'xjb'
    allowed_domains = ['epaper.bjnews.com.cn']
    start_urls = ['http://epaper.bjnews.com.cn/html/{}/{}/node_1.htm'.format(today[:7], today[-2:])]

    def parse(self, response):
        url = response.url
        article_urls = response.xpath('//ul[@class="jcul"]/li/a/@href').extract()
        for article_url in article_urls:
            real_url = url.split('node')[0] + article_url
            if is_alreadyexist(real_url):
                continue
            logger.info('will request: {}'.format(real_url))
            yield scrapy.Request(real_url, callback=self.article_parse, dont_filter=True)
        # 上一版 下一版
        pages = response.xpath('//div[@class="ltop"]/dl/dt/a[@class="preart"]/@href').extract()
        if len(pages) > 1 or pages[0] == "node_2.htm":
            next_page_url = url.split('node')[0]+pages[-1]
            logger.info('next: {}'.format(next_page_url))
            yield scrapy.Request(next_page_url, callback=self.parse, dont_filter=True)

    def article_parse(self, response):
        url = response.url
        title = response.xpath('//h1/text()').extract()[0]
        date = response.url.split('html/')[1].split('/content')[0].replace('/', '-')
        media = response.xpath('//dl[@class="rdln"]/dd/text()').extract()[0].split(' ')[-1]
        reporter = ''
        logger.info('will insert: {}'.format(title))
        doc = Document(response.text)
        content = doc.summary()
        if len(content) < 30:
            content = '\r\n'.join(response.xpath('//founder-content/p/text()').extract())

        item = EpaperItem()
        item['url'] = url
        item['title'] = title
        item['date'] = date
        item['media'] = media
        item['media_orig'] = '新京报'
        item['reporter'] = reporter
        item['content'] = content
        yield item


class ZgjjbSpider(scrapy.Spider):
    name = 'zgjjb'
    allowed_domains = []
    start_urls = ['http://chinafund.stcn.com/paper/zgjjb/html/epaper/index/index.htm']

    def parse(self, response):
        if datetime.now().weekday() == 0:
            page_titles = response.xpath('//h2/a[1]/text()').extract()
            article_urls = []
            for l, r in enumerate(page_titles):
                url = ['http://chinafund.stcn.com/paper/zgjjb/html/epaper/index/' + i for i in response.xpath('//div[@class="area"][{}]/ul/li/a/@href'.format(l+1)).extract()]
                article_urls.append(url)
            for page_title, article_url in zip(page_titles[1:], article_urls[1:]):
                if page_title[-2:] == '数据':
                    continue
                for i in article_url:
                    if is_alreadyexist(i):
                        logger.info(f'{i} already exist')
                        continue
                    yield scrapy.Request(i, callback=self.article_parse, dont_filter=True)

    def article_parse(self, response):
        url = response.url
        title = response.xpath('//div[@id="mainTiile"]/h2/text()').extract()[0]
        tmp = response.xpath('//div[@class="from"]//text()').extract()
        date = response.xpath('//div[@class="from"]/text()').extract()[0].strip().split()[0]  # 中国基金报7天发1次，最开始必须检查不是星期一不运行
        if date == today:
            media = '中国基金报'
            media_orig = '中国基金报'
            if tmp and '作者：' in tmp[-1]:
                reporter = tmp[-1].split('作者：')[1]
            else:
                reporter = ''
            doc = Document(response.text)
            content = doc.summary()
            if len(content) < 30:
                content = '\r\n'.join(response.xpath('//founder-content/p/text()').extract())
            item = EpaperItem()
            item['url'] = url
            item['title'] = title
            item['date'] = date
            item['media'] = media
            item['media_orig'] = media_orig
            item['reporter'] = reporter
            item['content'] = content
            yield item


class ZgzqbSpider(scrapy.Spider):
    name = 'zgzqb'

    # start_urls = ['http://epaper.cs.com.cn/dnis/TRSIdSSSOProxyServlet']
    no_useful_titles = {'偏股混合型基金', '平衡混合型基金', '偏股混合型基金', '二级债券型基金', '股票型基金', '纯债型基金', '偏债混合型基金', '平衡混合型基金', '一级债券型基金', '一级债券型基金', '说明:'}
    '''
    def start_requests(self):
        login_url = 'http://epaper.cs.com.cn/dnis/TRSIdSSSOProxyServlet'
        yield scrapy.FormRequest(login_url, formdata={'username': 'look2012', 'button': '登　录', 'password': '123456'}, callback=self.parse)
    '''

    def start_requests(self):
        yield scrapy.Request('http://epaper.cs.com.cn/dnis/index.jsp', dont_filter=True, callback=self.parse_main_page)

    def parse_main_page(self, response):
        yield scrapy.FormRequest.from_response(response, formdata={'username': 'zzbmtyy', 'button': '登　录', 'password': '123456'}, callback=self.parse_first_page)

    def parse_first_page(self, response):
        first_page_url = 'http://epaper.cs.com.cn/zgzqb/html/{}/{}/nbs.D110000zgzqb_A01.htm'.format(today[:-3], today[-2:])
        yield scrapy.Request(first_page_url, dont_filter=True, callback=self.parse_useful_pages)

    def parse_useful_pages(self, response):
        page_urls = response.xpath('//a[@id="pageLink"]/@href').extract()
        page_titles = response.xpath('//a[@id="pageLink"]/text()').extract()
        for page_url, page_title in zip(page_urls, page_titles):
            if '信息披露' not in page_title and '信息提示' not in page_title and '数据' not in page_title:
                if page_url.startswith('./'):
                    real_page_url = f'http://epaper.cs.com.cn/zgzqb/html/{today[:-3]}/{today[-2:]}/{page_url[2:]}'
                else:
                    real_page_url = f'http://epaper.cs.com.cn/zgzqb/html/{today[:-3]}/{today[-2:]}/{page_url}'
                yield scrapy.Request(real_page_url, callback=self.parse)

    def parse(self, response):
        article_urls = response.xpath('//li/a/@href').extract()
        article_urls = ['http://epaper.cs.com.cn/zgzqb/html/{}/{}/'.format(today[:-3], today[-2:]) + i for i in article_urls]
        for article_url in article_urls:
            if is_alreadyexist(article_url):
                logger.info('{} already exist.'.format(article_url))
                continue
            yield scrapy.Request(article_url, callback=self.article_parse)

    def article_parse(self, response):
        url = response.url
        titles = response.xpath('//td[@class="font01"]/text()').extract()
        if not titles:
            logger.info(f'{url} is not a news')
        else:
            if titles[0] not in self.no_useful_titles:
                title = titles[0]
                date = today
                media = '中国证券报'
                media_orig = '中国证券报'
                reporter_list = response.xpath('//td[@class="font02"]/text()').extract()
                if reporter_list:
                    reporter = reporter_list[0]
                    if ' ' in reporter:
                        reporter = reporter.split()[1]
                    if len(reporter) > 10:
                        reporter = ''
                else:
                    reporter = ''

                doc = Document(response.text)
                content = doc.summary()
                if len(content) < 30:
                    content = '\r\n'.join(response.xpath('//founder-content/p/text()').extract())
                if len(content) < 30:
                    content = '\r\n'.join(response.xpath('//div[@id="ozoom"]/p/text()').extract())

                item = EpaperItem()
                item['url'] = url
                item['title'] = title
                item['date'] = date
                item['media'] = media
                item['media_orig'] = media_orig
                item['reporter'] = reporter
                item['content'] = content
                yield item


class ZqrbSpider(scrapy.Spider):
    name = 'zqrb'
    start_urls = ['http://epaper.zqrb.cn/html/{}/{}/node_2.htm'.format(today[:7], today[-2:])]

    def parse(self, response):
        useful_page_id_list = []
        for i in response.xpath('//h2/a/text()').extract():
            if i.strip()[-4:] != '信息披露' and i.strip()[-2:] != '广告':
                id_ = []
                for c in i.strip()[1:]:
                    if not c.isdigit():
                        break
                    id_.append(c)
                useful_page_id_list.append(i.strip()[0]+''.join(id_))
        logger.info('useful id: {}'.format(useful_page_id_list))
        for id_ in useful_page_id_list:
            article_urls = response.xpath('//table[@id="{}"]//a/@href'.format(id_)).extract()
            logger.info(article_urls)
            for url in article_urls:
                article_url = 'http://epaper.zqrb.cn/html/{}/{}/'.format(today[:7], today[-2:]) + url
                if is_alreadyexist(article_url):
                    logger.info('{} already exist.'.format(article_url))
                    continue
                yield scrapy.Request(article_url, callback=self.article_parse)

    def article_parse(self, response):
        url = response.url
        title = ' '.join(response.xpath('//h1/text()').extract()).strip()
        # url限定了今日，所以干脆today就行了
        date = today
        media = '证券日报'
        media_orig = '证券日报'
        reporter = ''
        text_list = response.xpath('//div[@id="ozoom"]/p/text()').extract()
        for i in text_list[:2]:
            if '记者 ' in i:
                reporter = i.split('记者 ')[1].strip()
            elif '■' in i:
                reporter = i.split('■')[1].strip()
        doc = Document(response.text)
        content = doc.summary()
        if len(content) < 20:
            content = '\r\n'.join(text_list)
        item = EpaperItem()
        item['url'] = url
        item['title'] = title
        item['date'] = date
        item['media'] = media
        item['media_orig'] = media_orig
        item['reporter'] = reporter
        item['content'] = content
        yield item


class CbtSpider(scrapy.Spider):
    name = 'cbt'
    start_urls = ['http://epaper.cbt.com.cn/epaper/uniflows/html/']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse_realurl)

    def parse_realurl(self, response):
        today_url = self.start_urls[0] + response.text.split("href='")[1].split("'</")[0]
        # 自动重定向时防止周末跳转到周五日报的链接
        if today_url.split('/')[-3] == today[-2:]:
            yield scrapy.Request(today_url, callback=self.parse)

    def parse(self, response):
        url = response.url
        tmp_url = url.split('default.htm')[0]
        article_urls = response.xpath('//table[@class="board_link"]//a/@href').extract()
        article_urls = [tmp_url+i for i in article_urls]
        for article_url in article_urls:
            if is_alreadyexist(article_url):
                logger.info('{} already exist'.format(article_url))
                continue
            yield scrapy.Request(article_url, callback=self.article_parse)
        next_page = response.xpath('//a[contains(., "下一版")]/@href').extract()
        if next_page:
            next_page_url = next_page[0]
            next_page_url = '/'.join(url.split('/')[:-2]) + next_page_url.strip('.')
            yield scrapy.Request(next_page_url, callback=self.parse)

    def article_parse(self, response):
        url = response.url
        title = response.xpath('//h2/text()').extract()[0]
        date = response.xpath('//span[@id="boarddate"]/text()').extract()[0].strip()
        reporter = response.xpath('//td[@class="others"]/text()').extract()[0].split('作者：')[1].split('来源：')[0].strip()
        if '■' in reporter:
            reporter = reporter.split('■')[1]
        doc = Document(response.text)
        content = doc.summary()

        item = EpaperItem()
        item['url'] = url
        item['title'] = title
        item['date'] = date
        item['media'] = '中华工商时报'
        item['media_orig'] = '中华工商时报'
        item['reporter'] = reporter
        item['content'] = content
        yield item


class GjjrbSpider(scrapy.Spider):
    name = 'gjjrb'
    allowed_domains = ['paper.people.com.cn']
    start_urls = ['http://paper.people.com.cn/gjjrb/html/{}/{}/node_645.htm'.format(today[:-3], today[-2:])]

    def start_requests(self):
        if datetime.now().weekday() == 0:
            for url in self.start_urls:
                yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        url = response.url
        part_url = url.split('node_')[0]
        article_urls = [part_url+i for i in response.xpath('//div[@id="titleList"]/ul/li/a/@href').extract()]
        for article_url in article_urls:
            if is_alreadyexist(article_url):
                logger.info(f'{article_url} already exist')
                continue
            yield scrapy.Request(article_url, callback=self.article_parse)
        next_page = response.xpath('//a[contains(., "下一版")]/@href').extract()
        if next_page:
            next_page_url = part_url + next_page[0]
            yield scrapy.Request(next_page_url, callback=self.parse)

    def article_parse(self, response):
        url = response.url
        title = response.xpath('//h1/text()').extract()[0]
        date = today
        media = '国际金融报'
        media_orig = media
        reporters = response.xpath('//div[@class="lai"]/span/text()').extract()
        reporter = ''
        if reporters and '记者' in reporters[0]:
            reporter = reporters[0].strip().split('记者 ')[1]
        doc = Document(response.text)
        content = doc.summary()

        item = EpaperItem()
        item['url'] = url
        item['title'] = title
        item['date'] = date
        item['media'] = media
        item['media_orig'] = media_orig
        item['reporter'] = reporter
        item['content'] = content
        yield item


class ZgjybSpider(scrapy.Spider):
    name = 'zgjyb'
    start_urls = ['http://dianzibao.cb.com.cn/html/{}/{}/node_1.htm'.format(today[:-3], today[-2:])]

    def start_requests(self):
        if datetime.now().weekday() == 0:
            for url in self.start_urls:
                yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        url = response.url
        yield scrapy.Request(url, callback=self.page_parse)
        part_url = url.split('node')[0]
        page_urls = {part_url+i for i in response.xpath('//a[@id="pageLink"]/@href').extract() if not i.startswith('./')}
        for page_url in page_urls:
            yield scrapy.Request(page_url, callback=self.page_parse)

    def page_parse(self, response):
        url = response.url
        part_url = url.split('node')[0]
        article_urls = [part_url+i for i in response.xpath('//span[@class="modbd"]/ul/li/a/@href').extract()]
        for article_url in article_urls:
            if is_alreadyexist(article_url):
                logger.info(f'{article_url} already exist')
                continue
            yield scrapy.Request(article_url, callback=self.article_parse)

    def article_parse(self, response):
        url = response.url
        title = response.xpath('//td[@class="font01"]/text()').extract()[0]
        date = today
        media = '中国经营报'
        reporter = ''
        reporter_info = response.xpath('//founder-content/p[1]/text()').extract()[0]
        if '记者' in reporter_info:
            reporter = reporter_info.split('记者')[1].strip().split()[0]
        doc = Document(response.text)
        content = doc.summary()

        item = EpaperItem()
        item['url'] = url
        item['title'] = title
        item['date'] = date
        item['media'] = media
        item['media_orig'] = media
        item['reporter'] = reporter
        item['content'] = content
        yield item


class XinwenchenbaoSpider(scrapy.Spider):
    name = 'zhoudaosh'
    start_urls = [f'http://epaper.zhoudaosh.com/html/{today[:-3]}/{today[-2:]}/node_942.html']

    def parse(self, response):
        for i in response.xpath('//ul/a[@id="pageLink"]/@href').extract():
            if i.startswith('node'):
                page_url = f'http://epaper.zhoudaosh.com/html/{today[:-3]}/{today[-2:]}/{i}'
                yield scrapy.Request(page_url, callback=self.page_parse)
        for i in response.xpath('//ul[@id="artPList1"]/li/a/@href').extract():
            article_url = f'http://epaper.zhoudaosh.com/html/{today[:-3]}/{today[-2:]}/{i}'
            yield scrapy.Request(article_url, callback=self.article_parse)

    def page_parse(self, response):
        for i in response.xpath('//ul[@id="artPList1"]/li/a/@href').extract():
            article_url = f'http://epaper.zhoudaosh.com/html/{today[:-3]}/{today[-2:]}/{i}'
            yield scrapy.Request(article_url, callback=self.article_parse)

    def article_parse(self, response):
        url = response.url
        title = response.xpath('//p[@class="title1"]/text()').extract()[0]
        date = today.replace('-', '')
        media = '新闻晨报'
        media_orig = media
        info = response.xpath('//td[@class="content_tt"]/p/text()').extract()[0]
        reporter = ''
        if '记者' in info:
            reporter = info.split()[1]
        doc = Document(response.text)
        content = doc.summary()

        item = EpaperItem()
        item['url'] = url
        item['title'] = title
        item['date'] = date
        item['media'] = media
        item['media_orig'] = media_orig
        item['reporter'] = reporter
        item['content'] = content
        yield item


class jrtzSpider(scrapy.Spider):
    name = 'jrtzb'
    custom_settings = {'DOWNLOADER_MIDDLEWARES': {}}
    start_urls = ['http://stocknews.scol.com.cn/shtml/jrtzb/{}/v01.shtml'.format(today.replace('-', ''))]

    def parse(self, response):
        url = response.url
        if url:
            article_urls = [f"http://stocknews.scol.com.cn/shtml/jrtzb/{today.replace('-', '')}/{i}" for i in response.xpath('/html/body/table[2]/tr/td[1]/div[2]/div/div[2]/a/@href').extract()]
            for article_url in article_urls:
                if is_alreadyexist(article_url):
                    logger.info(f'{article_url} already exist')
                    continue
                yield scrapy.Request(article_url, callback=self.article_parse)
            next_page = response.xpath('//span[@class="f-12"]/a[contains(., "下一版")]/@href').extract_first()
            if next_page:
                next_page_url = f"http://stocknews.scol.com.cn/shtml/jrtzb/{today.replace('-', '')}/{next_page}"
                yield scrapy.Request(next_page_url, callback=self.parse)

    def article_parse(self, response):
        url = response.url
        title = response.xpath('//*[@id="DivDisplay"]/div[2]/strong/text()').extract()[0]
        date = today
        media = '金融投资报'
        media_orig = media
        reporters = response.xpath('//*[@id="DivDisplay"]/div[6]/p[1]/font[2]/text()[1]').extract()
        reporter = ''
        if reporters and '记者' in reporters[0]:
            reporter = reporters[0].split('记者')[1]
            if '文/图' in reporter:
                reporter = reporter.strip('文/图')
        doc = Document(response.text)
        content = doc.summary()
        item = EpaperItem()
        item['url'] = url
        item['title'] = title
        item['date'] = date
        item['media'] = media
        item['media_orig'] = media_orig
        item['reporter'] = reporter
        item['content'] = content

        yield item
