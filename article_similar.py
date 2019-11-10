# -*- coding: utf-8 -*-
import json
import logging

from jieba import posseg as pseg
import MySQLdb
from MySQLdb import cursors
from lxml import etree
from lxml.html import clean
from gensim import corpora, models, similarities
from flask import Flask, request

'''
import requests

hisinfo_ids = '2136953,2137524,2144155,2144271,2130670,2125421,2125423,2127367,2134686,2138726,2142495'
data = {'hisinfo_ids': hisinfo_ids, 'percentage': 0.95}
url = 'http://IP:PORT/similar'
r = requests.post(url, data=data)
for k, v in r.json().items():
    logging.warning(f'{k}, {v}')
'''
logging.basicConfig(level=logging.WARNING,
                    format='[%(asctime)s][%(filename)s][line:%(lineno)d]%(levelname)s: %(message)s')
del_words = {
    '编辑', '责编', '记者 ', '摘要：', '摘要 ', '风险自担', '风险请自担', '想了解更多关于', '扫码下载', '（原题为', '依法追究', '严正声明', "新浪股民维权平台", "你投诉，我报道", "文字内容参考：",
    '关键词 ', '2018-', '原标题', '原文', '概不承担', '转载自', '来源：', '仅做参考', '仅供参考', '未经授权', '浏览更多', '金融曝光台', '财经讯', '在线投诉', "并不预示其未来业绩表现",
    '禁止转载', '阅后点赞', '研究员：', '本文首发', '微信公众号', '个人观点', '蓝字关注', '微信号：', '欢迎订阅', '点击右上角分享', '加入我们', '二维码转账', '赞赏功能', "投资需谨慎", '黑猫投诉平台',
    '热门搜索', '为您推荐', '更多评论', '文明上网', '来源:', '作者:', '扫描二维码', '在线咨询：', '扫描或点击关注', '中金在线', '长按二维码', 'Scan QR Code via WeChat', '推荐阅读',
}
ending_words = {'长按二维码向我转账', '已推荐到看一看', "风险提示：", "免责声明："}
NUM_TOPICS = 350  # 主题数 200~500之间为宜
cleaner = clean.Cleaner(style=True, javascript=True, scripts=True, page_structure=False, safe_attrs_only=False, kill_tags=['span'])

app = Flask(__name__)


@app.route('/similar', methods=['POST'])
def similar_lst():
    if request.method == 'POST':
        hisinfo_ids = request.form.get('hisinfo_ids')
        hisinfo_ids = [int(i.strip()) for i in hisinfo_ids.split(',') if i.strip().isdigit()]
        if hisinfo_ids:
            logging.warning('jijin input count: {}'.format(len(hisinfo_ids)))
            percentage = float(request.form.get('percentage'))
            contents = get_content(hisinfo_ids)
            if contents:
                dic, corpus = get_dic_corpus(contents)
                try:
                    res = similar(contents, dic, corpus, percentage)
                except AssertionError:
                    corpus = tfidf_model(corpus)
                    res = similar(contents, dic, corpus, percentage)
                logging.warning('jijin output count: {}'.format(len(res)))
                return json.dumps(res)
            else:
                logging.critical('all id no content')
                res = {k: [k] for k in hisinfo_ids}
                return json.dumps(res)
        else:
            logging.critical(f'post no id: {request.form.get("hisinfo_ids")}')
            return json.dumps({'': [""]})
    else:
        logging.critical('NOT GET, SHOULD POST')
        return json.dumps({'': [""]})


@app.route('/xtsimilar', methods=['POST'])
def xtsimilar():
    if request.method == 'POST':
        ids = request.form.get('ids')
        ids = [int(i.strip()) for i in ids.split(',') if i.strip().isdigit()]
        if ids:
            logging.warning('xintuo input count: {}'.format(len(ids)))
            percentage = float(request.form.get('percentage'))
            contents = get_xtcontent(ids)
            if contents:
                dic, corpus = get_dic_corpus(contents)
                try:
                    res = similar(contents, dic, corpus, percentage)
                except AssertionError:
                    corpus = tfidf_model(corpus)
                    res = similar(contents, dic, corpus, percentage)
                logging.warning('xintuo output count: {}'.format(len(res)))
                return json.dumps(res)
            else:
                logging.critical('all id no content')
                res = {k: [k] for k in ids}
                return json.dumps(res)
        else:
            logging.critical(f'post no id: {request.form.get("ids")}')
            return json.dumps({'': [""]})
    else:
        logging.critical('NOT GET, SHOULD POST')
        return json.dumps({'': [""]})


@app.route('/cxsimilar', methods=['POST'])
def cx_similar_lst():
    if request.method == 'POST':
        cx_ids = request.form.get('cx0308_ids')
        cx_ids = [int(i.strip()) for i in cx_ids.split(',') if i.strip().isdigit()]
        if cx_ids:
            logging.warning('jijin input count: {}'.format(len(cx_ids)))
            percentage = float(request.form.get('percentage'))
            contents = get_cxcontent(cx_ids)
            if contents:
                dic, corpus = get_dic_corpus(contents)
                try:
                    res = similar(contents, dic, corpus, percentage)
                except AssertionError:
                    corpus = tfidf_model(corpus)
                    res = similar(contents, dic, corpus, percentage)
                logging.warning('jijin output count: {}'.format(len(res)))
                return json.dumps(res)
            else:
                logging.critical('all id no content')
                res = {k: [k] for k in cx_ids}
                return json.dumps(res)
        else:
            logging.critical(f'post no id: {request.form.get("cx_ids")}')
            return json.dumps({'': [""]})
    else:
        logging.critical('NOT GET, SHOULD POST')
        return json.dumps({'': [""]})


@app.route('/tzsimilar', methods=['POST'])
def tzsimilar_lst():
    if request.method == 'POST':
        ids = request.form.get('ids')
        ids = [int(i.strip()) for i in ids.split(',') if i.strip().isdigit()]
        if ids:
            logging.warning('touzi input count: {}'.format(len(ids)))
            percentage = float(request.form.get('percentage'))
            contents = get_tzcontent(ids)
            if contents:
                dic, corpus = get_dic_corpus(contents)
                try:
                    res = similar(contents, dic, corpus, percentage)
                except AssertionError:
                    corpus = tfidf_model(corpus)
                    res = similar(contents, dic, corpus, percentage)
                logging.warning('touzi output count: {}'.format(len(res)))
                return json.dumps(res)
            else:
                logging.critical('all id no content')
                res = {k: [k] for k in ids}
                return json.dumps(res)
        else:
            logging.critical(f'post no id: {request.form.get("ids")}')
            return json.dumps({'': [""]})
    else:
        logging.critical('NOT GET, SHOULD POST')
        return json.dumps({'': [""]})


@app.route('/tzTitlesimilar', methods=['POST'])
def tzTitlesimilar():
    if request.method == 'POST':
        ids = request.form.get('ids')
        ids = [int(i.strip()) for i in ids.split(',') if i.strip().isdigit()]
        if ids:
            logging.warning('touzi input count: {}'.format(len(ids)))
            percentage = float(request.form.get('percentage'))
            titles = get_tztitle(ids)
            if titles:
                dic, corpus = get_dic_corpus(titles)
                try:
                    res = similar(titles, dic, corpus, percentage)
                except AssertionError:
                    corpus = tfidf_model(corpus)
                    res = similar(titles, dic, corpus, percentage)
                logging.warning('touzi output count: {}'.format(len(res)))
                return json.dumps(res)
            else:
                logging.critical('all id no titlet')
                res = {k: [k] for k in ids}
                return json.dumps(res)
        else:
            logging.critical(f'post no id: {request.form.get("ids")}')
            return json.dumps({'': [""]})
    else:
        logging.critical('NOT GET, SHOULD POST')
        return json.dumps({'': [""]})


def filter_words(sentences):
    '''
    过滤文章中包含无用词的语句
    :sentences list[str]
    :return list[str]
    '''
    text = []
    signal = True
    for sentence in sentences:
        for word in ending_words:
            if word in sentence:
                signal = False
                break
        if not signal:
            break
        if sentence.strip() and not [word for word in del_words if word in sentence]:
            text.append(sentence.strip())
    return text


def tokenization(content):
    '''
    {标点符号、连词、助词、副词、介词、时语素、‘的’、数词、方位词、代词}
    {'x', 'c', 'u', 'd', 'p', 't', 'uj', 'm', 'f', 'r'}
    去除文章中特定词性的词
    :content str
    :return list[str]
    '''
    stop_flags = {'x', 'c', 'u', 'd', 'p', 't', 'uj', 'm', 'f', 'r'}
    stop_words = {'nbsp', '\u3000', '\xa0'}
    words = pseg.cut(content)
    return [word for word, flag in words if flag not in stop_flags and word not in stop_words]


def text_extract(content: str):
    '''
    if '<p' in content or '<P' in content:
        html = etree.HTML(content)
        sentences = [i.xpath('string(.)') for i in html.xpath('//p')]
        text = ' '.join(filter_words(sentences)).strip()
        if len(text) < 10:
            # 可能p标签不用来分段，那么直接提取全部文本，这样做list只有1个元素是整个文本
            # len(sentences) = 1
            sentences = [i.xpath('string(.)') for i in html]
            if sentences:
                text = '。'.join(filter_words(sentences[0].split('。'))).strip()
    # 部分html用div之类的分隔，暂时直接提取全部文本
    elif '</' in content:
        html = etree.HTML(content)
        sentences = html.xpath('string(.)').split('。')
        text = '。'.join(filter_words(sentences)).strip()
    '''
    if '<html>' in content:
        content = cleaner.clean_html(content)
    if '<' in content and '>' in content and '</' in content:
        html = etree.HTML(content)
        sentences = []
        for i in html.xpath('//text()'):
            if i.strip():
                sentences.extend(i.strip().split())

        sentences = ''.join(sentences).split('。')
    else:
        sentences = [''.join(sentence.split()) for sentence in content.split('。')]

    text = ' '.join(filter_words(sentences)).strip()
    if text.startswith('['):
        text = text.split(']', 1)[1].strip()
    return text


def get_content(ids: list):
    '''
    从基金数据库获取id list对应的content list并做初步处理
    :ids list[int]
    :return list[(int, str)]
    '''
    conn = MySQLdb.connect(
        host='120.26.106.222',
        user='julai01',
        password='Sh51785136@sh',
        database='jijin',
        charset='utf8mb4',
        cursorclass=cursors.SSCursor)
    with conn.cursor() as cur:
        sql = ["SELECT a.id, b.content FROM hisinfo_cx a INNER JOIN cx0308 b ON a.post_id=b.id WHERE a.id=%s"]
        for l, r in enumerate(ids):
            if l < 1:
                continue
            sql.append(' or a.id=%s')
        sql = ''.join(sql)
        cur.execute(sql, ids)
        contents = []
        for id_, content in cur:
            text = text_extract(content)
            # 文章内容为<html><body/></html>或者为空的排除掉
            if len(text) > 25:
                contents.append((id_, text))

    return contents


def get_cxcontent(ids: list):
    '''
    从基金数据库获取id list对应的content list并做初步处理
    :ids list[int]
    :return list[(int, str)]
    '''
    conn = MySQLdb.connect(
        host='120.26.106.222',
        user='julai01',
        password='Sh51785136@sh',
        database='jijin',
        charset='utf8mb4',
        cursorclass=cursors.SSCursor)
    with conn.cursor() as cur:
        sql = ["SELECT id, content FROM cx0308 WHERE id=%s"]
        for l, r in enumerate(ids):
            if l < 1:
                continue
            sql.append(' or id=%s')
        sql = ''.join(sql)
        cur.execute(sql, ids)
        contents = []
        for id_, content in cur:
            text = text_extract(content)
            # 文章内容为<html><body/></html>或者为空的排除掉
            if len(text) > 25:
                contents.append((id_, text))
    return contents


def get_xtcontent(ids: list):
    '''
    从信托数据库获取id list对应的content list并做初步处理
    :ids list[int]
    :return list[(int, str)]
    '''
    conn = MySQLdb.connect(host='120.26.95.149', user='julai01', password='Sh51785136@sh', database='xintuo', charset='utf8mb4', cursorclass=cursors.SSCursor)
    with conn.cursor() as cur:
        sql = ["SELECT a.id, b.content FROM xt_hisinfo_cx a INNER JOIN xt_cx0308 b ON a.post_id=b.id WHERE a.id=%s"]
        for l, r in enumerate(ids):
            if l < 1:
                continue
            sql.append(' or a.id=%s')
        sql = ''.join(sql)
        cur.execute(sql, ids)
        contents = []
        for id_, content in cur:
            text = text_extract(content)
            # 文章内容为<html><body/></html>或者为空的排除掉
            if len(text) > 25:
                contents.append((id_, text))

    return contents


def get_tzcontent(ids: list):
    '''
    从投资数据库获取id list对应的content list并做初步处理
    :ids list[int]
    :return list[(int, str)]
    '''
    conn = MySQLdb.connect(
        host='dev2.zhangyupai.net',
        user='julai01',
        password='Sh51785136@sh',
        database='touzi_v2',
        charset='utf8mb4',
        cursorclass=cursors.SSCursor)
    with conn.cursor() as cur:
        sql = ["SELECT a.id, b.content FROM crawl_result a INNER JOIN crawl_content b ON a.id=b.crawl_id WHERE a.id=%s"]
        for l, r in enumerate(ids):
            if l < 1:
                continue
            sql.append(' or a.id=%s')
        sql = ''.join(sql)
        cur.execute(sql, ids)
        contents = []
        for id_, content in cur:
            text = text_extract(content)
            # 文章内容为<html><body/></html>或者为空的排除掉
            if len(text) > 25:
                contents.append((id_, text))
    return contents


def get_tztitle(ids: list):
    '''
    从投资数据库获取id list对应的title list
    :ids list[int]
    :return list[(int, str)]
    '''
    conn = MySQLdb.connect(
        host='dev2.zhangyupai.net',
        user='julai01',
        password='Sh51785136@sh',
        database='touzi_v2',
        charset='utf8mb4',
        cursorclass=cursors.SSCursor)
    with conn.cursor() as cur:
        sql = ["SELECT id, title FROM crawl_result WHERE id=%s"]
        for l, r in enumerate(ids):
            if l < 1:
                continue
            sql.append(' or id=%s')
        sql = ''.join(sql)
        cur.execute(sql, ids)
        titles = [(id_, title) for id_, title in cur if title]
    return titles


def get_dic_corpus(contents):
    texts = [tokenization(r) for id_, r in contents]

    dic = corpora.Dictionary(texts)
    corpus = [dic.doc2bow(text) for text in texts]
    return dic, corpus


def tfidf_model(corpus):
    '''
    使用：会避免一处报错，但是准确率下降
    不使用：偶发报错，但是准确率很高
    '''
    return models.TfidfModel(corpus)[corpus]


def similar(contents, dic, corpus, percentage):
    '''
    判断相似度
    :return dict {int: list}
    '''
    lsi = models.LsiModel(corpus, id2word=dic, num_topics=NUM_TOPICS)
    # index = similarities.MatrixSimilarity(lsi[corpus])

    index = similarities.Similarity('index', lsi[corpus], num_features=lsi.num_topics)
    res = {}
    for l, degrees in enumerate(index):
        # print(contents[l][0], [(contents[i][0], similarity) for i, similarity in enumerate(degrees)])
        res[contents[l][0]] = [contents[i][0] for i, similarity in enumerate(degrees) if similarity >= percentage]
    return res


def main():
    hisinfo_ids = '4434705, 4430763'
    hisinfo_ids = [int(i.strip()) for i in hisinfo_ids.split(',') if i.strip()]
    if hisinfo_ids:
        logging.warning('jijin input count: {}'.format(len(hisinfo_ids)))
        percentage = 0.95
        contents = get_content(hisinfo_ids)
        if contents:
            dic, corpus = get_dic_corpus(contents)
            try:
                res = similar(contents, dic, corpus, percentage)
            except AssertionError:
                corpus = tfidf_model(corpus)
                res = similar(contents, dic, corpus, percentage)
            logging.warning('jijin output count: {}'.format(len(res)))
            print(res)

    '''
    ids = '475303, 475201'  # cx0308表的id
    ids = [int(i.strip()) for i in ids.split(',')]
    if ids:
        percentage = 0.95
        contents = get_xtcontent(ids)
        if contents:
            dic, corpus = get_dic_corpus(contents)
            try:
                res = similar(contents, dic, corpus, percentage)
            except AssertionError:
                corpus = tfidf_model(corpus)
                res = similar(contents, dic, corpus, percentage)
            for k, v in res.items():
                print(k, v)
    '''


if __name__ == '__main__':
    # main()
    app.run(host='127.0.0.1', port=80)  # host='0.0.0.0', port=80
