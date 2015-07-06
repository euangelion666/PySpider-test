#!/usr/bin/env python
from pyspider.libs.base_handler import *
from pyquery import PyQuery as pq
from bs4 import BeautifulSoup
from itertools import repeat
import md5
import re
import urllib2
import os
from cStringIO import StringIO
import Image
import urlparse
from multiprocessing.dummy import Pool as ThreadPool 
'''广州市国土资源和规划委员会'''

class Handler(BaseHandler):
    height = 250
    width = 250
    thread_num = 14
    headers= {
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding":"gzip, deflate, sdch",
        "Accept-Language":"zh-CN,zh;q=0.8",
        "Cache-Control":"max-age=0",
        "Connection":"keep-alive",
        "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36"
    }
    crawl_config = {
        "headers" : headers,
        "timeout" : 100
    }

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('http://www.upo.gov.cn/WebApi/GsApi.aspx?do=phlist&lb=null&area=null&page=1', 
            fetch_type='js', callback=self.index_page)

    # @config(age=10 * 24 * 60 * 60)
    @config(age = 1)
    def index_page(self, response):
        r = BeautifulSoup(response.text)
        json = r.body.text
        response_json = eval(json)
        json_list = response_json['list']
        domain = 'http://www.upo.gov.cn'
        content_list = [domain + i['Url'] for i in json_list]
        page_count = response_json['pagecount']
        page_count = int(page_count)

        for each in content_list:
            self.crawl(each, callback=self.content_page)

        ajax_url = response.url[:-1]
        # page_count = 10
        for i in range(2, page_count + 1):
            next_page = ajax_url + str(i)
            self.crawl(next_page, fetch_type='js', callback=self.next_list)

    @config(priority=2)
    def next_list(self, response):
        r = BeautifulSoup(response.text)
        json = r.body.text
        response_json = eval(json)
        json_list = response_json['list']
        domain = 'http://www.upo.gov.cn'
        content_list = [domain + i['Url'] for i in json_list]

        for each in content_list:
            self.crawl(each, callback=self.content_page)

    @config(priority=2)
    def content_page(self, response):
        attachment = response.doc('a[href$="doc"]') + response.doc('a[href$="pdf"]') + response.doc('a[href$=".jpg"]')
        images = response.doc('img')

        url = response.url
        m = md5.new()
        m.update(url)
        web_name = m.hexdigest()
        # path = 'D:/web/' + web_name + '/'
        path = '/home/teer/web/' + web_name + '/'
        if not os.path.exists(path):
            os.makedirs(path)           

        attachment_list = []
        if attachment is not None:
            for each in attachment.items():
                attachment_list.append(each.attr.href)
            pool = ThreadPool(self.thread_num)
            pool.map(self.download_attachment, zip(attachment_list, repeat(path)))
            pool.close()

        image_list = []
        if images is not None:
            for each in images.items():
                image_url = urlparse.urljoin(url, each.attr.src)
                image_list.append(image_url)
            pool = ThreadPool(self.thread_num)
            pool.map(self.download_image, zip(image_list, repeat(path)))
            pool.close()

        return {
            "url": response.url,
            "html": response.text,
        }
    
    def on_result(self, result):
        if result is not None: 
            m = md5.new()
            m.update(result['url'])
            web_name = m.hexdigest()
            # path = 'D:/web/' + web_name + '/'
            path = '/home/teer/web/' + web_name + '/'
            if not os.path.exists(path):
                os.makedirs(path)           

            page_path = path + 'page.txt'
            f = open(page_path, 'wb')
            f.write(result['html'].encode('utf-8'))
            f.close()
            content_path = path + 'content.txt'
            f = open(content_path, 'wb')
            soup = BeautifulSoup(result['html'])
            for i in soup('style') + soup('script'):
                i.extract()
            f.write(soup.get_text(strip=True).encode('utf-8'))
            f.close()
            url_path = path + 'url.txt'
            f = open(url_path, 'wb')
            f.write(result['url'].encode('utf-8'))
            f.close()
        super(Handler, self).on_result(result)

    def download_attachment(self, (url, path)):
        f = urllib2.urlopen(url)
        attachment_path = path + os.path.basename(url)
        with open(attachment_path, 'wb') as code:
            code.write(f.read())

    def download_image(self, (url, path)):
        f = urllib2.urlopen(url)
        
        if self.height * self.width == 0:
            image_path = path + os.path.basename(url)
            with open(image_path, 'wb') as code:
                code.write(f.read())
        else:
            i = Image.open(StringIO(f.read()))
            temp_width, temp_height = i.size
            if temp_width >= self.width and temp_height >= self.height:
                image_path = path + os.path.basename(url)
                i.save(image_path)
