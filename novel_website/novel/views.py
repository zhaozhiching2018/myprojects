from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from django.urls import reverse
from .x23uscom import *
from .spider import Spider
from .dingdian import Novel

def index(request):

    context = {}
    return render(request,'novel/index.html',context)

def search(request):
    s_info = request.POST
    novel_name = s_info['novel_name']

    novel_obj = X23usCom(novel_name)
    novel_info = novel_obj.index()
    if isinstance(novel_info,(dict,)):
        url = novel_info['url']
        chapter = Spider(url)
        info = chapter.info(chapter_url = '<a class="read" href="https://www.x23us.com/html/(.*?)" title=".*?">章节列表</a>',
                            )
        
        arg = info['chapter_url'][0].split('/')
        return HttpResponseRedirect(reverse('novel:book',args = (arg[0],arg[1])))
    else:
        last_info = novel_obj.info()
        context = {'last_info':last_info}
        return render(request,'novel/search.html',context)

def book(request,book_pk,book_id):
    url = 'https://www.x23us.com/html/{}/{}/'.format(book_pk,book_id)

    book_name = '<meta name="og:novel:book_name" content="(.*?)"/>'
    book_author = '<meta name="og:novel:author" content="(.*?)"/> '
    book_info = '<td class="L"><a href="(.*?)">(.*?)</a></td>'

    x = Spider(url = url)
    info_dict = x.info(book_name = book_name,
                       book_author = book_author,
                       book_info = book_info,
                       )
    context = info_dict
    detail_url = 'https://www.x23us.com/book/{}'.format(book_id)
    novel_img = '<img style="padding:7px; border:1px solid #E4E4E4; \
width:120px; height:150px; margin:0 25px 0 15px;" alt=".*?" src="(.*?)"  onerror=".*?"/>'
    novel_detail = '<p>(.*?)<br /></p><p style="display:none" id="sidename">.*?</p>'
    n = Spider(url = detail_url)
    detail_dict = n.info(novel_img = novel_img,
                         )

    context.update(detail_dict)

    return render(request,'novel/book.html',context)

def download(request,book_pk,book_id):
    url = 'https://www.x23us.com/html/{}/{}/'.format(book_pk,book_id)
    x = Novel(url)
    y = x.save_txt()
    return HttpResponse(y)
0

def home(request):
    url = 'https://www.x23us.com'
    img_reg = '<dd><a href=".*?" target="_blank"><img src="(.*?)" alt=".*?"></a><br /><a href=".*?" target="_blank">.*?</a></dd>'
    detail_reg = '<dd><a href=".*?" target="_blank"><img src=".*?" alt=".*?"></a><br /><a href="https://www.x23us.com/html/(.*?)" target="_blank">.*?</a></dd>'
    name_reg = '<dd><a href=".*?" target="_blank"><img src=".*?" alt=".*?"></a><br /><a href=".*?" target="_blank">(.*?)</a></dd>'

    the_html = Spider(url = url)
    the_info = the_html.info(img_reg = img_reg,
                       detail_reg = detail_reg,
                       name_reg = name_reg,
                       )
    last_dict = {}
    for i in range(len(the_info['name_reg'])):
        last_dict[the_info['name_reg'][i]] = {
		'img_url':the_info['img_reg'][i],
		'detail_url':the_info['detail_reg'][i],
                'fenjie_url':the_info['detail_reg'][i].split('/'),
		}
    #print(last_dict)
    ty_reg = '<li><p class="ul1">(.*?)《<a class="poptext" href=".*?" target="_blank">.*?</a>》</p><p class="ul2">\
<a href=".*?" target="_blank">.*?</a></p><p>.*?</p>.*?</li>'
    bknm_reg = '<li><p class="ul1">.*?《<a class="poptext" href=".*?" target="_blank">(.*?)</a>》</p><p class="ul2">\
<a href=".*?" target="_blank">.*?</a></p><p>.*?</p>.*?</li>'
    dt_reg = '<li><p class="ul1">.*?《<a class="poptext" href="https://www.x23us.com/html/(.*?)" target="_blank">.*?</a>》</p><p class="ul2">\
<a href=".*?" target="_blank">.*?</a></p><p>.*?</p>.*?</li>'
    cata_reg = '<li><p class="ul1">.*?《<a class="poptext" href=".*?" target="_blank">.*?</a>》</p><p class="ul2">\
<a href=".*?" target="_blank">(.*?)</a></p><p>.*?</p>.*?</li>'
    au_reg = '<li><p class="ul1">.*?《<a class="poptext" href=".*?" target="_blank">.*?</a>》</p><p class="ul2">\
<a href=".*?" target="_blank">.*?</a></p><p>(.*?)</p>.*?</li>'
    tm_reg = '<li><p class="ul1">.*?《<a class="poptext" href=".*?" target="_blank">.*?</a>》</p><p class="ul2">\
<a href=".*?" target="_blank">.*?</a></p><p>.*?</p>(.*?)</li>'
    zxzj_reg = '<li><p class="ul1">.*?《<a class="poptext" href=".*?" target="_blank">.*?</a>》</p><p class="ul2">\
<a href="https://www.x23us.com/html/(.*?)" target="_blank">.*?</a></p><p>.*?</p>.*?</li>'

    zx_info = the_html.info(ty_reg = ty_reg,
                            bknm_reg = bknm_reg,
                            dt_reg = dt_reg,
                            cata_reg = cata_reg,
                            au_reg = au_reg,
                            tm_reg = tm_reg,
                            zxzj_reg = zxzj_reg,
                            )
    zx_dict = {}
    for x in range(12):
        zx_dict[zx_info['bknm_reg'][x]] = {
            'ty_reg':zx_info['ty_reg'][x],
            'dt_reg':zx_info['dt_reg'][x],
            'cata_reg':zx_info['cata_reg'][x],
            'au_reg':zx_info['au_reg'][x],
            'tm_reg':zx_info['tm_reg'][x],
            'fenj_url':zx_info['dt_reg'][x].split('/'),
            'zxzj_reg':zx_info['zxzj_reg'][x],
            }
    context = {'last_dict':last_dict,'zx_dict':zx_dict}
    return render(request,'novel/home.html',context)
     
def chapter(request,book_pk,book_id,chapter_id):
    url = 'https://www.x23us.com/html/{}/{}/{}.html'.format(book_pk,book_id,chapter_id)

    chapter_title = '<title>(.*?)</title>'
    chapter_content = '<dd id="contents">(.*)'

    previous_page = '<dd id="footlink"><a href="/html/(.*?)">上一页</a>\
<a href="/html/(.*?)" title=".*?">返回章节列表</a>\
<a href="/html/(.*?)">下一页</a></dd>'

    x = Spider(url = url)
    info_list = x.info(chapter_title = chapter_title,
                       chapter_content = chapter_content,
                       previous_page = previous_page,
                       )
    return render(request,'novel/chapter.html',context = info_list)

    
    
    
