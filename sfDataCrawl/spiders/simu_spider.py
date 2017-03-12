# -*- coding: utf-8 -*-
import scrapy
from sfDataCrawl.items import TestItem
from sfDataCrawl.items import ProductItem
from sfDataCrawl.items import CompanyItem
from sfDataCrawl.items import ManagerItem
from scrapy.http import FormRequest
import json
import logging
import datetime
import MySQLdb
import re
from os import path
from sfDataCrawl import settings
import time
from sfDataCrawl.items import NavItem
from scrapy.loader import ItemLoader
from sfDataCrawl.items import MonthItem
from sfDataCrawl.items import HsReturnItem

NOT_EXISTED_COMPANY_ID = None

class SimuSpider(scrapy.Spider):
    name = "simu"
    total_page = 0
    current_page = 1
    spider_log = ''
    conn = ''
    cusor = ''
    # 当前已经存在的产品
    product_dict = dict()
    # 当前已经抓取的howbuy产品
    howbuy_product_dict = dict()
    # 当前已经存在的公司
    company_dict = dict()
    # 当前已经抓取的hobuy公司
    howbuy_company_dict = dict()
    # 当前已经存在的经理
    manager_dict = dict()
    # 当前已经抓取的hobuy经理
    howbuy_manager_dict = dict()
    # sql查询的最新数据
    nav_dict = dict()
    # 抓取的最新数据
    crawl_data = {}
    # sql查询月份的最新数据
    reutrn_dict = dict()
    hs300_dict = dict()
    #之前几天抓取的公司不再抓取
    crawl_day = 2
    #产品类型
    product_type_dict = {'股票型':0,'管理期货':2,'市场中性':4,'多空仓型':4,'套利型':3,'定向增发':1,'多策略':7,'组合型':6,'债券型':5,'货币型':8,'宏观策略':8,'其他':8}
    def __init__(self):
        current_path = path.abspath('.')
        # file_name = 'spider_warning'+ datetime.date.today().strftime('%Y-%m-%d') + '.log'
        file_name = current_path + '/sfDataCrawl/runningLog/spider_warning'+ datetime.date.today().strftime('%Y-%m-%d') + '.log'
        
        logging.getLogger('scrapy').setLevel(logging.ERROR)

        warning_file_hanlder = logging.FileHandler(file_name)
        warning_file_hanlder.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        self.spider_log = logging.getLogger('spider_log')
        self.spider_log.addHandler(warning_file_hanlder)
        try:
            self.conn = MySQLdb.connect(settings.MYSQL_HOST, settings.MYSQL_USER, settings.MYSQL_PWD, settings.MYSQL_DB, charset='utf8',use_unicode=True)
            self.cursor = self.conn.cursor()
            self.cursor.execute('SELECT id,name,status,crawl_id,crawl_update_time FROM sf_product')
            products = self.cursor.fetchall()
            for product in products:
                id = product[0]
                name = product[1]
                status = product[2]
                howbuy_id = product[3]
                howbuy_update_time = product[4]
                product_info = {
                    'id' : id,
                    'name' : name,
                    'status' : status,
                    'howbuy_id' : howbuy_id,
                    'howbuy_update_time' : howbuy_update_time
                }
                self.product_dict[name] = product_info
                self.howbuy_product_dict[howbuy_id] = product_info
            # 公司字典
            self.cursor.execute('SELECT id,name,status,crawl_id,crawl_update_time FROM sf_company')
            companies = self.cursor.fetchall()
            for company in companies:
                id = company[0]
                name = company[1]
                status = company[2]
                crawl_id = company[3]
                crawl_update_time = company[4]
                company_info = {
                    'id' : id,
                    'name' : name,
                    'status' : status,
                    'howbuy_id' : crawl_id,
                    'howbuy_update_time' : crawl_update_time
                }
                self.company_dict[name] = company_info
                self.howbuy_company_dict[crawl_id] = company_info
            #经理字典
            self.cursor.execute('SELECT id,name,status,crawl_id,crawl_update_time,company_name FROM sf_manager')
            managers = self.cursor.fetchall()
            for manager in managers:
                id = manager[0]
                name = manager[1]
                status = manager[2]
                crawl_id = manager[3]
                crawl_update_time = manager[4]
                company_name = manager[5]
                manager_info = {
                    'id' : id,
                    'name' : name,
                    'status' : status,
                    'howbuy_id' : crawl_id,
                    'howbuy_update_time' : crawl_update_time,
                    'company_name' : company_name
                }
                self.manager_dict[name+'-'+company_name] = manager_info
                self.howbuy_manager_dict[crawl_id] = manager_info
            #hs300字典
            self.get_hs_dict()
            # sql查询最新的数据
            self.cursor.execute('SELECT product_id, MAX(nav_date) FROM sf_nav GROUP BY product_id')
            navs = self.cursor.fetchall()
            for nav in navs:
                product_id = nav[0]
                date = nav[1]
                nav_data = {
                    'date': str(date),
                }
                # 把最新时间放入字典比对抓取时间
                self.nav_dict[product_id] = nav_data
        except MySQLdb.Error,e:
            print 'initial error'
            print str(e)
        pass
    def get_hs_dict(self):
        cursor = self.cursor
        select_sql = 'SELECT index_type, index_date, hs_index, growth_rate FROM sf_hs_index ORDER BY index_date DESC'
        cursor.execute(select_sql)
        hs_info = cursor.fetchall()
        counter = 0
        for hs_line in hs_info:
            index_date = hs_line[1].strftime('%Y-%m-%d')
            self.hs300_dict[index_date] = {
                'index_date': index_date,
                'hs_index': hs_line[2],
            }
    def start_requests(self):
        urls = [
            'https://simu.howbuy.com/mlboard.htm'
        ]
        board_url = "https://simu.howbuy.com/mlboard.htm"
        #board_url = "https://simu.howbuy.com/shenhaishitouzi/"
        self.spider_log.info(board_url)
        page_data = {
            "orderType": "Desc",
            "sortField": "jzrq",
            "ejfl": "",
            "jgxs": "",
            "gzkxd": '1',
            "skey": "",
            "page": '1',
            "perPage": '100'
        }
        yield FormRequest(board_url, callback=self.parse, formdata=page_data)
        #yield scrapy.Request('https://simu.howbuy.com/manager/30043518.html',self.parse_manager)
        #yield scrapy.Request('https://simu.howbuy.com/zixi/S80358/', callback=self.parse_product)
        # for url in urls:
        #     yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        #沪深300
        hs_url = "http://quotes.money.163.com/trade/lsjysj_zhishu_000300.html"
        yield scrapy.Request(hs_url,self.get_hs)
        temp_total_page = response.xpath('//*[@id="allPage"]/@value').extract_first()
        # #TODO for testing
        temp_total_page = 1
        if self.total_page < 1 and temp_total_page is not None:
            self.total_page = temp_total_page
        #循环获取1-20的tr  注意当获取的每页的条数发生变化  这里要跟着变化
        per_page_line = 100
        for i in range(1,per_page_line+1):
            product = response.xpath('//*[@id="spreadDetails"]/tr['+str(i)+']/td[3]/a/@href').extract_first()
            product_name = response.xpath(u'//*[@id="spreadDetails"]/tr['+str(i)+']/td[3]/a/text()').extract_first()
            if product_name in self.product_dict:
                if self.product_dict[product_name]['status'] == 0:
                    self.spider_log.info('product URL: ' + product)
                    if '/--/' not in product:
                        #公司不存在的产品不抓取
                        yield scrapy.Request(product,self.parse_product)
            else:
                self.spider_log.info('product URL: ' + product)
                yield scrapy.Request(product,self.parse_product)
        if self.current_page < self.total_page :
            self.current_page += 1
            next_page_data = {
                "orderType": "Desc",
                "sortField": "jzrq",
                "ejfl": "",
                "gzkxd": '1',
                "skey": "",
                "page": str(self.current_page),
                "perPage": '100'
            }
            board_url = "https://simu.howbuy.com/mlboard.htm"
            self.spider_log.info('product list URL: ' + board_url)
            yield FormRequest(board_url,callback=self.parse,formdata=next_page_data)


    def parse_product(self,response):
        product_name = response.xpath("//div[contains(@class, 'trade_fund_top_dotted')]//h1/text()").extract_first()
        item = ProductItem()
        product_url = response.url
        item['crawl_product_id'] = product_url.split("/")[-2]
        item['crawl_product_name'] = product_name
        if(product_name in self.product_dict):
            if(self.product_dict[product_name]['howbuy_update_time'] is None):
                howbuy_update_time = '1980-01-01 00:00:00'
            else:
                howbuy_update_time = str(self.product_dict[product_name]['howbuy_update_time'])
        else:
            howbuy_update_time = '1980-01-01 00:00:00'
        if(self._no_crawl(howbuy_update_time) == 1):
            item['crawl_product_full_name'] = response.xpath('//div[contains(@class,"part_a")]//tr[1]/td[2]/text()').extract_first()
            item['start_date'] = response.xpath('//div[contains(@class,"part_a")]//tr[9]/td[2]/text()').extract_first()
            item['trustee_bank'] = response.xpath('//div[contains(@class,"part_a")]//tr[4]/td[2]/text()').extract_first()
            item['status'] = response.xpath('//div[contains(@class,"part_a")]//tr[12]/td[2]/text()').extract_first()
            #item['product_type'] = 0 response.xpath('//div[contains(@class,"part_a")]//tr[2]/td[2]/text()').extract_first()
            product_type_data = response.xpath('//div[contains(@class,"part_a")]//tr[2]/td[2]/text()').extract_first()
            item['product_type'] = self.product_type_dict[product_type_data.encode("utf-8") ]
            item['company_name'] = response.xpath('//div[contains(@class,"trade_fund_top_dotted_bott")]//p[3]/a/text()').extract_first()
            item['min_purchase_amount'] = response.xpath('//div[contains(@class,"instruction_box")]//tr[1]/td[2]/text()').re_first(r'\d+')
            item['min_append_amount'] = response.xpath('//div[contains(@class,"instruction_box")]//tr[7]/td[2]/text()').extract_first()
            if item['min_append_amount'] == '--':
                item['min_append_amount'] = None
            structured = response.xpath('//div[contains(@class,"part_a")]//tr[10]/td[2]/text()').extract_first()
            if structured == "非结构化".decode('utf-8') :
                item['structured'] = 0
            else :
                item['structured'] = 1
            item['purchase_status'] = 2 #默认停售
            item['nav_date'] = response.xpath("//div[contains(@class, 'net_value')]//div[contains(@class,'tb_chart')]//tr[2]/td[1]/text()").extract_first()
            item['crawl_url'] = response.url
            item['crawl_company_id'] = response.xpath('//div[contains(@class,"trade_fund_top_dotted_bott")]//p[3]/a/@href').re_first(r'https://simu.howbuy.com/(.+)/$')
            item['crawl_managers_id'] = response.xpath('//div[contains(@class,"fund_class")]/div[contains(@class,"fund_tabs")]//span/@code').extract_first()
            item['crawl_managers_name'] = response.xpath('//div[contains(@class,"fund_class")]/div[contains(@class,"fund_tabs")]//span/text()').extract_first()
            item['now_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            #fubiao
            item['locked_time'] = response.xpath("//div[contains(@class,'part_a')]//tr[7]/td[2]/text()").extract_first()
            item['open_date'] = response.xpath("//div[contains(@class,'part_a')]//tr[5]/td[2]/text()").extract_first()
            item['commission'] = response.xpath("//div[contains(@class,'instruction_box')]//tr[5]/td[5]/text()").extract_first()
            item['ransom_fee'] = response.xpath("//div[contains(@class,'instruction_box')]//tr[6]/td[4]/text()").extract_first()
            item['fixed_management_fee'] = response.xpath("//div[contains(@class,'instruction_box')]//tr[4]/td[3]/text()").extract_first()
            item['subscription_fee'] = response.xpath("//div[contains(@class,'instruction_box')]//tr[3]/td[2]/text()").extract_first()
            item['dividend_date'] = list();
            trs = response.xpath("//div[contains(@class,'part_c')]//div[1]//table//tr")
            if len(trs)>2:
                for i in range(3,len(trs)+1):
                    dividend_date = response.xpath("//div[contains(@class,'part_c')]//div[1]//table/tr["+str(i)+"]/td[2]/text()").extract_first()
                    item['dividend_date'].append(dividend_date)
            company_url = response.xpath("//div[contains(@class, 'trade_fund_top_dotted_bott')]//p[contains(@class,'p3')]//a/@href").extract_first()
            if company_url is not None:
                skip_company = False
                if item['company_name'] in self.company_dict:
                    company_howbuy_update_time = self.company_dict[item['company_name']]['howbuy_update_time']
                    if company_howbuy_update_time is not None:
                        need_crawl = self._no_crawl(str(company_howbuy_update_time))
                        if need_crawl == 1:
                            skip_company = True

                if skip_company != True:
                    self.spider_log.info('-------company url---------:'+company_url)
                    yield scrapy.Request(company_url, callback=self.parse_company)
            else:
                print 'no company',item['crawl_product_id']
                #没有公司的产品直接跳过
                return
            #maager url
            manager_url = response.xpath("//div[contains(@class, 'trade_fund_top_dotted')]/div[2]/p[3]/span/a/@href").extract_first()
            if manager_url is not None :
                skip_manager = False
                if item['crawl_managers_id'] in self.howbuy_manager_dict:
                    manager_howbuy_udpate_time = self.howbuy_manager_dict[item['crawl_managers_id']]['howbuy_update_time']
                    if manager_howbuy_udpate_time is not None:
                        need_crawl = self._no_crawl(str(manager_howbuy_udpate_time))
                        if need_crawl == 1:
                            skip_manager = True
                # self.howbuy_manager_dict[crawl_id]
                if skip_manager != True:
                   self.spider_log.info('--------manage URL----------: ' + manager_url)
                   yield scrapy.Request(manager_url,callback=self.parse_manager)
            #fubiao jieshu
            crawl_manager_id = item['crawl_managers_id']
            if item['crawl_managers_id'] is not None :
                if crawl_manager_id in self.howbuy_manager_dict:
                    oManager = self.howbuy_manager_dict[crawl_manager_id]
                    item['manager_list'] = str(oManager['id']) + ',' + oManager['name']
                else:
                    item['manager_list'] = item['crawl_managers_id'] + ',' + item['crawl_managers_name']+';'
            else :
                item['manager_list'] = ';'
            crawl_company_id = item['crawl_company_id']
            if crawl_company_id in self.howbuy_company_dict:
                item['company_id'] = self.howbuy_company_dict[crawl_company_id]['id']
            else:
                item['company_id'] = NOT_EXISTED_COMPANY_ID
            yield item
            #抓取净值
            script = response.xpath('/html/body/script[13]/@src')
            srcipt_url = script.extract_first()
            self.spider_log.info('js URL: ' + srcipt_url)
            yield scrapy.Request(srcipt_url, callback=self.get_script)
        else:
            return
    def parse_company(self,response):
        item = CompanyItem()
        item['crawl_url'] = response.url
        item['crawl_id'] = response.url.split('com/')[1].split('/')[0]
        item['name'] = response.xpath("//div[contains(@class,'con_left')]//h2/text()").extract_first()
        if (item['name'] in self.company_dict):
            if (self.company_dict[item['name']]['howbuy_update_time'] is not None):
                howbuy_update_time = str(self.company_dict[item['name']]['howbuy_update_time'])
            else:
                howbuy_update_time = '1980-01-01 00:00:00'
        else:
            howbuy_update_time = '1980-01-01 00:00:00'
        if (self._no_crawl(howbuy_update_time) == 1):
            item['core_manager_name'] = response.xpath("//div[contains(@class,'company_detail')]//ul[contains(@class,'fund_about')]//li[0]/text()").extract_first()
            rep_product = response.xpath("//*[@id='nTab7_Con1']/div[contains(@class,'contrast_left')]/@jjdm").extract_first()
            item['icp'] = response.xpath("//div[contains(@class,'company_detail')]//ul[contains(@class,'company_about')]//li[1]//span/text()").extract_first()
            item['establishment_date']  = response.xpath("//div[contains(@class,'company_detail')]//ul[contains(@class,'company_about')]//li[3]//span/text()").extract_first()
            registered_capital_selector = response.xpath("//div[contains(@class,'company_detail')]//ul[contains(@class,'fund_about')]//li[3]//span/text()")
            registered_capital = registered_capital_selector.extract_first()
            if registered_capital == '--':
                item['registered_capital'] = None
            elif registered_capital is None:
                item['registered_capital'] = None
            else:
                item['registered_capital'] = float(registered_capital_selector.re_first(r'\d+'))*10000
            item['region'] = response.xpath("//div[contains(@class,'company_detail')]//ul[contains(@class,'company_about')]//li[2]//span/text()").extract_first()
            item['asset_mgmt_scale'] = response.xpath("//div[contains(@class,'company_detail')]//ul[contains(@class,'fund_about')]//li[3]//span/text()").extract_first()
            item['full_name'] = item['name']
            item['rep_product_name'] = response.xpath("//div[contains(@class,'contrast_right')]//p[1]/a/text()").extract_first()
            current_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            item['crawl_update_time'] = current_date
            item['crawl_create_time'] = current_date
            item['update_time'] = current_date
            item['create_time'] = current_date
            if item['name'] is None:
                return
            else:
                yield item
        else:
            pass

    def parse_empty(self,response):
        pass

    def parse_empty(self, response):
        pass
    #抓取js
    def get_script(self, response):
        # 读取URL从url中获取抓取id
        url = response.url
        crawl_id = url.split("_")[-2]
        body = response.body
        data_arr = body.split(';')[0]
        data = data_arr.split('=')[-1]
        # 加上单引号变成json字符串
        string = data.replace("'", '"')
        string = string.replace("u", "")
        pat = '\"\\1\"'
        rep_str = re.sub("([a-zA-Z]+)", pat, string)
        navs = {}
        if (crawl_id in self.howbuy_product_dict):
            product_id = self.howbuy_product_dict[crawl_id]['id']
            dic = json.loads(rep_str)
            return_data = self.chkData(dic,product_id)
            # 循环迭代加入
            l = ItemLoader(item=NavItem(), response=response)
            items = []
            current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            if product_id not in self.nav_dict:
                self.nav_dict[product_id] = {
                    'date':'1980-01-01'
                }
            max_date = self.nav_dict[product_id]['date']
            for next_data in return_data:
                nav_date = []
                nav_date.append(product_id)
                nav_date.append(str(crawl_id))
                nav_date.append(next_data['nav_date'])
                nav_date.append(round(float(next_data['added_nav']),4))
                nav_date.append(round(float(next_data['nav']),4))
                growth_rate = round(float(next_data['growth_rate']),4)
                nav_date.append(growth_rate)
                nav_date.append(current_time)
                nav_date.append(current_time)
                nav_date.append(current_time)
                nav_date.append(url)
                if (product_id in self.nav_dict.keys() and str(self.nav_dict[product_id]['date']) >= str(next_data['nav_date'])):
                    pass
                else:
                    items.append(tuple(nav_date))
                if next_data['nav_date'] > max_date:
                    max_date = next_data['nav_date']
                self.nav_dict[product_id]['date'] = max_date
            l.add_value('nav_item_date', items)
            l.add_value('product_id', product_id)
            yield l.load_item();
        else:
            pass

    # 处理json的数据
    def chkData(self, dic,product_id):
        for list in dic[u'navList']:
            item = {}
            arr = list.split(',')
            if arr[3] == 0:
                arr[3] = 12
            # 净值日期
            item['nav_date'] = arr[2] + '-' + arr[3] + '-' + arr[4]
            # 累计净值
            item['added_nav'] = arr[6]
            # 净值
            item['nav'] = arr[5]
            # 增长率
            # item['growth_rate'] = '1.00'
            #最新的净值日期
            # d = datetime.datetime.strptime(item['nav_date'], '%Y-%m-%d')
            # oneday = datetime.timedelta(days=1)
            # day = d - oneday
            # yesterday = datetime.date(day.year, day.month, day.day)
            # str_date = yesterday.strftime('%Y-%m-%d')
            # sql = "select nav,nav_date from sf_nav where product_id = %s ORDER BY nav_date ASC  limit 1"
            # param = [str(product_id)]
            # self.cursor.execute(sql,param)
            # results_first = self.cursor.fetchone()#查询最早一条净值记录
            # if results_first is None:
            #     item['growth_rate'] = 0.00
            # else:
                # growth_rate = (float(arr[5])-float(results_first[0]))/float(results_first[0])
            item['growth_rate'] = float(arr[6]) - 1
                # item['growth_rate'] = float('%.4f' % growth_rate)
            item['create_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            item['update_time'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            yield item
    #处理经理
    def parse_manager(self,response):
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        item = ManagerItem()
        item['manager_name'] = response.xpath('//div[contains(@class,"currentPath")]/span/text()').extract_first()

        manager_url = response.url
        item['crawl_id'] = manager_url.split('/')[-1].split('.')[-2]

        crawl_company_id = response.xpath('//*[@id="szgs"]/@href').re_first(r'https://simu.howbuy.com/(.+)/$')
        if crawl_company_id in self.howbuy_company_dict:
            item['company_id'] = self.howbuy_company_dict[crawl_company_id]['id']
        else:
            item['company_id'] = NOT_EXISTED_COMPANY_ID
            #如果经理所在公司不存在，则抓取公司
            company_url = response.xpath('//*[@id="szgs"]/@href').extract_first()
            if company_url is not None:
                yield scrapy.Request(company_url, self.parse_company)
        item['crawl_company_id'] = crawl_company_id
        item['company_name'] = response.xpath('//*[@id="szgs"]/text()').extract_first()
        name = item['manager_name']+'-'+item['company_name']
        if (name in self.manager_dict):
            if (self.manager_dict[name]['howbuy_update_time'] is not None):
                howbuy_update_time = str(self.manager_dict[name]['howbuy_update_time'])
            else:
                howbuy_update_time = '1980-01-01 00:00:00'
        else:
            howbuy_update_time = '1980-01-01 00:00:00'
        if (self._no_crawl(howbuy_update_time) == 1):
            item['profile'] = response.xpath('//div[contains(@class,"manager_des_content")]/div[1]/div/text()').extract_first()
            item['background'] = 1#response.xpath('//*[@id="experience"]/div[3]/div[2]//tr[2]/td[2]/text()').extract_first()
            item['invest_year'] = response.xpath('//*[@id="experience"]/div[3]/div[2]//tr[1]/td[2]/text()').re_first(r'\d+')
            item['crawl_product_id'] = response.xpath('//*[@id="dbjj"]/@href').re_first(r'https://simu.howbuy.com/.+/(\w+)/$')
            item['manage_product_num'] = response.xpath('//*[@id="experience"]/div[3]/div[2]//tr[3]/td[4]/text()').re_first(r'\d+')
            item['now_time'] = current_time
            item['create_time'] = current_time
            item['update_time'] = current_time

            yield item
        else:
            pass
    #沪深300
    def get_hs(self,response):
        items = []
        # sql查询最新沪深时间
        self.cursor.execute('SELECT index_date FROM sf_hs_index order by index_date desc limit 1')
        hs_new_date = self.cursor.fetchone()
        # 循环迭代加入
        l = ItemLoader(item=HsReturnItem(), response=response)
        # product_id = self.howbuy_product_dict[crawl_id]['id']
        items = []
        item = []
        date_time_arr = response.xpath("/html/body/div[2]/div[3]/table/tr/td[1]/text()").extract()
        hs_arr = response.xpath("/html/body/div[2]/div[3]/table/tr/td[5]/text()").extract()
        rate_arr = response.xpath("/html/body/div[2]/div[3]/table/tr/td[6]/text()").extract()
        for index in range(len(date_time_arr)):
            date_time_arr[index]
            hs_arr[index]
            rate_arr[index]
            t_str = date_time_arr[index]
            d = time.strptime(t_str, '%Y%m%d')
            formatTime = time.strftime("%Y-%m-%d", d)
            nav_date = []
            if(formatTime > str(hs_new_date[0])):
                now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                nav_date.append(0)
                nav_date.append(date_time_arr[index])
                index_data = hs_arr[index].replace(',', '')
                nav_date.append(index_data)
                nav_date.append(rate_arr[index])
                nav_date.append(0)
                nav_date.append(now_time)
                nav_date.append(now_time)
                items.append(tuple(nav_date))
            else:
                pass
        l.add_value('hs_return', items)
        yield l.load_item();
    def _no_crawl(self,crawl_product_day):
        crawl_date = datetime.datetime.strptime(crawl_product_day, "%Y-%m-%d %H:%M:%S").date()
        current_date = datetime.datetime.now().date()
        if((current_date - crawl_date).days > self.crawl_day):
            return 1
        else:
            return
