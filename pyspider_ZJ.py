from pyspider.libs.base_handler import *
from my import My
from bs4 import BeautifulSoup
import re
from urllib.parse import urlencode

'''湛江'''

class Handler(My):
    name = "ZJ"
    
    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('http://www.zjgh.gov.cn/ysszgs.aspx?classid=21&1', 
            callback=self.index_page, save={'page':1, 'type':self.table_name[0]})
        self.crawl('http://www.zjgh.gov.cn/ysszgs.aspx?classid=21&1', 
            callback=self.index_page, save={'page':1, 'type':self.table_name[1]})
        self.crawl('http://www.zjgh.gov.cn/ysszgs.aspx?classid=21&1', 
            callback=self.index_page, save={'page':1, 'type':self.table_name[2]})
        self.crawl('http://www.zjgh.gov.cn/ysszgs.aspx?classid=21&1', 
            callback=self.index_page, save={'page':1, 'type':self.table_name[3]})

    def index_page(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')

        lists = soup('a', {'target':'_blank'})[:-3]
        print(len(lists))
        domain = 'http://www.zjgh.gov.cn/'
        for i in lists:
            crawl_link = domain + i['href'] 
            self.crawl(crawl_link, callback=self.content_page, save=response.save)
        
        last_page = int(soup('a', {'href': re.compile(r'javascript:__doPostBack')})[-1]['href'].split(',')[1].split('\'')[1])
        if last_page != response.save['page']:
            parmas = {'__EVENTTARGET': 'ywgslist$AspNetPager1'}
            parmas['__EVENTARGUMENT'] = str(response.save['page'] + 1)
            parmas['__VIEWSTATE'] = soup.find('input', {'name':'__VIEWSTATE'})['value']
            parmas['__EVENTVALIDATION'] = soup.find('input', {'name': '__EVENTVALIDATION'})['value']
            parmas['search$SearchStr'] = '请输入关键字'.encode('gb2312')
            parmas['search$ColumnIDDDL'] = soup.find('select', {'name': 'search$ColumnIDDDL'}).find('option', {'selected':'selected'})['value']
            parmas['ywgslist$AspNetPager1_input'] = str(response.save['page'])

            data = urlencode(parmas)
            print(response.orig_url)
            temp = response.orig_url.split('&')
            url = temp[0]
            for i in temp[1:-1]:
                url += '&' + i
            print(url)
            url = url + '&' + str(response.save['page'] + 1)
            response.save['page'] = response.save['page'] + 1
            self.crawl(url, method='POST', data=data, callback=self.index_page, save=response.save)

        