import requests
import re

class X23usCom:

    def __init__(self,key_word = '大主宰'):
        self.key_word = key_word
    
    def index(self):
        
        key_word = self.key_word.encode('gb2312')
        url = 'https://www.x23us.com/modules/article/search.php'
        params = {
            'searchtype':'keywords',
            'searchkey':key_word,
            }

        res = requests.get(url,params = params)
        if res.history:
            print('res.url',res.url)# res.url https://www.x23us.com/book/66656
            return {'url':res.url} #{'url': 'https://www.x23us.com/book/66656'}
        else:
            return res
        
    def info(self):
        html = self.index().text
        
        book_name = '<td class="odd"><a href=".*?">(.*?)</a></td>'
        book_url = '<td class="even"><a href="https://www.x23us.com/html/(.*?)" target="_blank">.*?</a></td>'
        book_author = '<td class="odd">\w*?([^a]*?)</td>'
        book_statu = '<td class="even" align="center">(.*?)</td>'
        #小说链接
        book_detail_url = '<td class="odd"><a href="(.*?)">.*?</a></td>'
        #最新章节
        latest_chapter = '<td class="even"><a href=".*?" target="_blank">(.*?)</a></td>'

        book_name = re.findall(book_name,html)
        book_url = re.findall(book_url,html)
        book_author = re.findall(book_author,html)
        book_statu = re.findall(book_statu,html)
               
        book_detail_url = re.findall(book_detail_url,html)
        latest_chapter = re.findall(latest_chapter,html)

        novel_img = '<img style="padding:7px; border:1px solid #E4E4E4; width:120px; height:150px; margin:0 25px 0 15px;" alt=".*?" src="(.*?)"  onerror=".*?"/>'
        novel_detail = '<p>(.*?)</p><p style="display:none" id="sidename">.*?</p>'

        
        info_dict = {}
        for i in range(len(book_name)):
            
            info_dict[book_name[i].replace('<b style="color:red">','').replace('</b>','')] \
                                               = {'author':book_author[i].replace('<b style="color:red">','').replace('</b>',''),
                                                  'url':book_url[i],
                                                  'statu':book_statu[i],
                                                  'latest_chapter':latest_chapter[i],
                                                  'detail_url':book_detail_url[i],
                                                  'fenjie_url':book_url[i].split('/'),
                                                  }

        return info_dict

if __name__ == '__main__':
    
    x = X23usCom(key_word = '圣墟')
    y = x.index()
    print(y)

