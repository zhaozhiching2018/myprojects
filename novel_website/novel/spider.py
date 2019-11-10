import requests
import re

class Spider:

    def __init__(self,
                 url = 'https://www.x23us.com/html/28/28373/',
                 charset = 'gbk',
                 json = None,
                 ):
        self.url = url
        self.json = json
        self.charset = charset
        self.html = self.html()
        
    def html(self):

        res = requests.get(self.url)
        res.encoding = self.charset

        if self.json != None:
            return res.json()
        return res.text

    def info(self,**regex):
        
        info_dict = {}
        for key,value in regex.items():
            info_dict[key] = re.findall(value,self.html)

        return info_dict

if __name__ == '__main__':
    x = Spider(url = 'https://www.x23us.com')
    y = x.info(img_reg = '<dd><a href=".*?" target="_blank"><img src="(.*?)" alt=".*?"></a><br /><a href=".*?" target="_blank">.*?</a></dd>',
               detail_reg = '<dd><a href=".*?" target="_blank"><img src=".*?" alt=".*?"></a><br /><a href="(.*?)" target="_blank">.*?</a></dd>',
               name_reg = '<dd><a href=".*?" target="_blank"><img src=".*?" alt=".*?"></a><br /><a href=".*?" target="_blank">(.*?)</a></dd>',
               )
    print(y)
