import datetime
import traceback
import MySQLdb
from MySQLdb import cursors
from ePaper.log_config import logger

today = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')
yesterday = datetime.datetime.strftime(datetime.datetime.now()+datetime.timedelta(-1), '%Y-%m-%d')


def old_urls() ->set:
    '''
    获取数据库昨天和今天的所有[ePaper]开头的新闻url
    :return set()
    '''
    conn = MySQLdb.connect(host='120.26.106.222', user='julai01', password='Sh51785136@sh', database='jijin', charset='utf8mb4', cursorclass=cursors.SSCursor)
    try:
        with conn.cursor() as cur:
            sql = "select str_date, md5link from cx0308 WHERE (str_date=%s or str_date=%s) and content like %s and id>1600000"
            cur.execute(sql, (''.join(today.split('-')), ''.join(yesterday.split('-')), '[ePaper]%'))  # 注意格式
            urls = set(url for str_date, url in cur)
    except:
        logger.exception('select old urls error')
        traceback.print_exc()
    finally:
        conn.close()
    return urls
