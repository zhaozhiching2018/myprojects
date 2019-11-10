import requests
import re
import os

class Novel:
    '''
    实现功能：输入书名详细链接，可以爬取整本小说
    必传参数为：小说详细链接，（编码格式），
    可选参数为：需要获取部分的正则表达式，编码格式，作者正则，书名正则         
    '''
    def __init__(self,catalog_url,           #catalog目录
                 regular_catalog ='<td class="L"><a href="(.*?)">(.*?)</a></td>',
                 the_encoding = 'gbk',
                 book_author = '<meta name="og:novel:author" content="(.*?)"/>',
                 book_name = '<meta name="og:novel:book_name" content="(.*?)"/> ',
                 arg1 = None,
                 arg2 = None,
                 ):
        self.catalog_url = catalog_url
        self.regular_catalog = regular_catalog #章节目录
        self.encoding = the_encoding
        self.book_author = book_author
        self.book_name = book_name
        if arg1 != None:
            self.arg1 = arg1
        if arg2 != None:
            self.arg2 = arg2
            
        self.catalog_html = self.catalog_html()
    def catalog_html(self,):
        try:
            res = requests.get(self.catalog_url,timeout = 10)
            res.raise_for_status()
        except requests.exceptions.ConnectionError:
            return '请查看网络链接是否畅通！'
        else:
            if res.status_code == requests.codes.ok:
                res.encoding = self.encoding
                catalog_h5 = res.text
                book_author = re.search(self.book_author,catalog_h5).group(1)
                book_name = re.search(self.book_name,catalog_h5).group(1)
                h5_list = re.findall(self.regular_catalog,catalog_h5)[:10]
                try:
                    with open('error--书名：{}--作者：{}.txt'.format(book_name,book_author),'r') as r:
                        last_info = r.readlines()[-1]
                        print(last_info)
                    last_info = eval(last_info) 
                except OSError: 
                    return book_name,book_author,h5_list
                else:
                    last_location = h5_list.index(last_info)
                    return book_name,book_author,h5_list[last_location:]
    
    def save_txt(self,detail_regular='<dd id="contents">(.*?)</dd>',\
                 detail_encoding='gbk'):
        chapter_info = self.catalog_html
        last_str = ''
        for i in chapter_info[2]:
            chapter_url = self.catalog_url+i[0]
            print(i)
            try:
                chapter_html = requests.get(chapter_url)
                chapter_html.encoding = detail_encoding
                chapter_html = chapter_html.text
                chapter_content = re.search(detail_regular,chapter_html,re.S)
                chapter_content = chapter_content.group(1).replace('&nbsp;','').\
                                  replace('<br />','\n')
            except requests.exceptions.ConnectionError:
                with open('error--书名：{}--作者：{}.txt'.format(chapter_info[0],chapter_info[1]),'a') as f:
                    f.write('\n \n')
                    f.write('执行任务时，网络链接中断，链接：\n{}'.format(i))
                    a = '执行任务时，网络链接中断，链接：\n{}'.format(i)
                    print(a)
                    return a
            else:
                
                last_str += i[1]+'\n \n'+ chapter_content+'\n \n'
                
        book_name = '书名：{}--作者：{}.txt'.format(chapter_info[0],chapter_info[1])
        the_path = os.getcwd()
        last_path = the_path + '\\{}'.format(book_name)
        print(last_path)
        return last_str
                                
if __name__ == '__main__':
    
    catalog_url = 'https://www.x23us.com/html/70/70883/'
    x = Novel(catalog_url = catalog_url)
    x.save_txt()
                    
                    





        
        
