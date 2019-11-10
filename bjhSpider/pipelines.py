# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql


class BjhspiderPipeline(object):
    def __init__(self):
        self.id = 1;
        #链接数据库
        self.db = pymysql.connect("127.0.0.1", "root", "root", "test", charset='utf8')
        #获取游标
        self.cursor = self.db.cursor()

    def process_item(self, item, spider):
        dictitem = dict(item)
        title = dictitem['title']
        url = dictitem['url']
        date = dictitem['date']
        content=dictitem['content']
        read_num=dictitem['read_num']
        comment_num=dictitem['comment_num']
        sql = "INSERT INTO baijiahao(`title`,`url`,`date`,`content`,`read_num`,`comment_num`)  VALUES ('%s', '%s', '%s','%s','%s','%s',)"
        self.cursor.execute(sql, (title, url, date,content,read_num,comment_num))
        last_id = self.cursor.lastrowid  # 获取最后一次插入的主键id
        print("--------------------------- process_item sql ----------------------------")
        print(sql)
        print(last_id)
        self.db.commit()
        return item