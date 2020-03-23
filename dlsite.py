# -*- coding=utf-8 -*-
from lxml import html
import requests
import time
import os
import sqlite3
import sys
import re

start_time = time.perf_counter()

#proxies = {'http': 'socks5://127.0.0.1:10808', 'https': 'socks5://127.0.0.1:10808'}
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
    'Cookie': 'adultchecked=1; locale=ja-jp'
    }

# 避免ERROR: Max retries exceeded with url
requests.adapters.DEFAULT_RETRIES = 5 # 增加重连次数
s = requests.session()
s.keep_alive = False # 关闭多余连接
# s.get(url) 你需要的网址       

def strdate(string):
    y, m, d, h = string[0:4], string[5:7], string[8:10], string[12:14]
    return y+'-'+m+'-'+d+' '+h

def match_rj(rj_url):
    r = s.get(rj_url, allow_redirects=False, headers=header)  # allow_redirects=False 禁止重定向
    # HTTP状态码==200表示请求成功
    if r.status_code != 200:
        return r.status_code, '','','','','','','','','',''
    # fromstring()在解析xml格式时,将字符串转换为Element对象,解析树的根节点
    # 在python中, 对get请求返回的r.content做fromstring()处理,可以方便进行后续的xpath()定位等
    tree = html.fromstring(r.content)
    title = tree.xpath('string(//a[@itemprop="url"])')
    circle = tree.xpath('string(//span[@itemprop="brand" and @class="maker_name"]/a)')
    saledate = tree.xpath('string(//*[@id="work_outline"]/tr/th[contains(text(), "販売日")]/../td/a)')
    cvlist = tree.xpath('//*[@id="work_outline"]/tr/th[contains(text(), "声優")]/../td/a/text()')
    musiclist = tree.xpath('//*[@id="work_outline"]/tr/th[contains(text(), "音楽")]/../td/a/text()')
    age = tree.xpath('string(//*[@id="work_outline"]/tr/th[contains(text(), "年齢指定")]/../td/div)')
    typelist = tree.xpath('//*[@id="work_outline"]/tr/th[contains(text(), "作品形式")]/../td/div/a/span/text()')
    taglist = tree.xpath('//*[@id="work_outline"]/tr/th[contains(text(), "ジャンル")]/../td/div/a/text()')
    size = tree.xpath('string(//*[@id="work_outline"]/tr/th[contains(text(), "ファイル容量")]/../td/div)')
    origin_text= ''
    for o in range(1,len(tree.xpath('string(//*[@class="work_parts_container"]/div[not(contains(@class,"work_parts type_chobit"))])'))+1):
        origin_text= origin_text+ tree.xpath('string(//*[@class="work_parts_container"]/div[not(contains(@class,"work_parts type_chobit"))][{}])'.format(o))
    origin_text= origin_text.strip()

    return 200, title, circle, saledate, cvlist, musiclist, age, typelist, taglist, size, origin_text

'''   
def match_rt(rt_url):
    r = s.get(rt_url + '.html', allow_redirects=False, headers=header, proxies=proxies)
    if r.status_code != 200:
        #print("    Status code:", r.status_code, "\nurl:", url)
        return r.status_code, "", "", []
        
    tree = html.fromstring(r.content)
    title = tree.xpath('//div[@class="works_summary"]/h3/text()')[0]
    circle = tree.xpath('//a[@class="summary_author"]/text()')[0]
    return 200, title, circle, []
'''
url_dlsite = 'https://www.dlsite.com/maniax/works/voice'
req_voicelist = s.get(url_dlsite, allow_redirects=False, headers=header)
if req_voicelist.status_code != 200:
    print('req_voicelist: ' + req_page.status_code)
    sys.exit()
tree_1 = html.fromstring(req_voicelist.content)
page_max = tree_1.xpath('//td[@class="page_no"]/ul/li/a[contains(text(), "最後へ")]/@data-value')[0]

voice_dict = {}
with open('voice_main.txt','a+',encoding='utf-8') as file1:
    file1.seek(0)
    if file1.read() == '':
        dict1 = {}
    else:
        dict1 = eval(file1.read())
for page in range(1,int(page_max)+1): # int(page_max)+1
    url_dlsite = 'https://www.dlsite.com/maniax/works/voice?page={}'.format(page,)
    req_page = s.get(url_dlsite, allow_redirects=False, headers=header)
    if req_page.status_code != 200:
        print('req_page: ' + req_page.status_code)
        with open('err_page.txt','a+',encoding='utf-8') as errf:
            errf.write(str(page)+'\n')
        continue
    tree_2 = html.fromstring(req_page.content)
    url_list = tree_2.xpath('//ul[@id="search_result_img_box"]/li/dl/dt/a/@href')
    '''
    输出dlsie主页面html源码
    with open("html.txt", "w", encoding="utf-8") as h:
        h.write(req_2.text)
    '''
    for u in url_list:
        rjcode = u[-13:-5]
        img_str = tree_2.xpath('string(//*[@id="_link_{}"]/a/div/img/@*[name()=":src"])'.format(rjcode))
        if img_str:
            img_url = "https:" + img_str[img_str.index("'")+1:img_str.index("'",img_str.index("'")+1,)]
        else:
            img_url = ''
        if rjcode in dict1:
            break
        voice_dict[rjcode] = img_url
    else:
        print('page: '+str(url_dlsite))
        time.sleep(1)
        continue
    break

mid_time = time.perf_counter()

with open('voice_new.txt','w',encoding='utf-8') as file2:
    file2.write(str(voice_dict))

title, circle, saledate, age, size= '','','','',''

con = sqlite3.connect('voice.db')
cur = con.cursor()
con.text_factory = str
cur.execute('CREATE TABLE IF NOT EXISTS dlsitevoice (id INTEGER PRIMARY KEY,rjcode CHAR(8),title VARCHAR(100),circle VARCHAR(30),saledate DATETIME,cvs VARCHAR(100),music VARCHAR(120),age CAHR(5),worktype VARCHAR(20),tags VARCHAR(100),size VARCHAR(12),worktext TEXT,img BLOB)')
con.commit()

for rj in voice_dict.keys():
    url_rj = 'https://www.dlsite.com/maniax/work/=/product_id/{}.html'.format(rj,)
    r_status, title, circle, saledate, cvlist, musiclist, age, typelist, taglist, size, origin_text = match_rj(url_rj)
    if r_status != 200 or title == '':
        print(rj+" match_status: " + r_status)
        with open('err_rj.txt','a+',encoding='utf-8') as errf:
            errf.write(str(rj)+'\n')
        continue
    img_url = voice_dict[rj]
    # 删除title中的.*?
    #title = re.sub(u"/\\.*?", "", title)
    if saledate:
        saledate = strdate(saledate)
    
    cvs,music,worktype,tags, worktext= '','','','',''
    if cvlist: #如果cvList非空
        for cvname in cvlist:
            cvs += cvname + '+'
        cvs = cvs.strip('+')
    if musiclist:
        for mname in musiclist:
            music += mname+'+'
        music=music.strip('+')
    if typelist:
        for tname in typelist:
            worktype += tname+'+'
        worktype=worktype.strip('+')
    if taglist:
        for tagname in taglist:
            tags += tagname + '+'
        tags = tags.strip('+')
    size = size.strip()
    for s in origin_text.splitlines():
        if s.isspace() == True:
            s=''
        worktext= worktext+ s.strip()+ '\n'
    worktext= re.sub("\n\n+","\n\n",worktext)
    
    #获取封面图片字节流
    req_img = b''
    if img_url:
        req_img = s.get(img_url,allow_redirects=False, headers=header, stream=True).content
    #img_stream = BytesIO(req_img.content)    
    cur.execute('insert into dlsitevoice (rjcode,title,circle,saledate,cvs,music,age,worktype,tags,size,worktext,img) values (?,?,?,?,?,?,?,?,?,?,?,?)',(rj,title,circle,saledate,cvs,music,age,worktype,tags,size,worktext,sqlite3.Binary(req_img)))
    con.commit()
    print(rj)
    time.sleep(1)
    
cur.close()
con.close()

end_time = time.perf_counter()
print('mid_cost: '+str(mid_time-start_time))
print('end_cost: '+str(end_time-start_time))

with open('voice_main.txt','a+',encoding='utf-8') as dicf:
    dicf.seek(0)
    if dicf.read() == '':
        newdic = {}
    else:
        dicf.seek(0)
        newdic = eval(dicf.read())
    newdic.update(voice_dict)
    dicf.seek(0)
    dicf.truncate()
    dicf.write(str(newdic))
