# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

from collections import defaultdict

import requests
from scrapy import signals
from twisted.web._newclient import ResponseFailed

from .log_config import logger


class EpaperSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ProxyMiddleware:

    # 遇到这些类型的错误直接当做代理不可用处理掉, 不再传给retrymiddleware
    DONT_RETRY_ERRORS = (TimeoutError, ConnectionRefusedError, ValueError, ResponseFailed)

    def __init__(self):
        # 代理无效的次数，切换太多次大概率本身是错误url
        self.url_proxy_change_count = defaultdict(int)
        # 同一url代理无效的阈值，超过这个值抛弃url
        self.max_proxy_valid = 8

        # 代理服务器的地址
        self.base_url = 'http://tz5.zhangyupai.net:5000'
        self.ban_code = {404, 403, 408, 502, 503, 500, 504}

    def set_invalid(self, request):
        '''
        处理无效代理
        '''
        if 'proxy' in request.meta.keys():

            invalid_proxy = request.meta['proxy'].split('//')[1]

            logger.info(f'{invalid_proxy} invalid: {request.meta["proxy"]}')
            requests.get(f'{self.base_url}/decrease/{invalid_proxy}')

    def set_proxy(self, request):
        '''
        设置代理
        '''
        proxy = 'http://' + requests.get(f'{self.base_url}/get_one').text

        request.meta['proxy'] = proxy
        logger.info(f'request proxy change to {proxy}')

    def process_request(self, request, spider):
        """
        将request设置为使用代理
        """
        # 防止部分代理重定向跳转到莫名其妙的网页, 由于腾讯不少新闻链接本身就需要跳转，所以注释掉
        # request.meta["dont_redirect"] = True

        # spider发现parse error, 要求更换代理
        if "change_proxy" in request.meta.keys() and request.meta["change_proxy"]:
            self.set_invalid(request)
            self.set_proxy(request)
            request.meta['change_proxy'] = False

    def process_response(self, request, response, spider):
        """
        检查response.status, 根据status是否在允许的状态码中决定是否切换proxy, 或者禁用proxy
        """
        if response.status in self.ban_code:
            if '找不到文件或目录' in response.text:
                return response
            self.url_proxy_change_count[response.url] += 1
            if self.url_proxy_change_count[response.url] >= self.max_proxy_valid:
                logger.info(f'{response.url} is invalid')
                return response
            logger.info(f"{response.url} status: {response.status}")
            self.set_invalid(request)
            self.set_proxy(request)
            new_request = request.copy()
            new_request.dont_filter = True
            return new_request
        else:
            return response

    def process_exception(self, request, exception, spider):
        """
        处理由于使用代理导致的连接异常
        """
        if isinstance(exception, self.DONT_RETRY_ERRORS):
            self.set_invalid(request)
            self.set_proxy(request)
            new_request = request.copy()
            new_request.dont_filter = True
            return new_request
