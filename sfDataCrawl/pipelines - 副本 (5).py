# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import MySQLdb
import datetime
import time
import calendar
import numpy as np
from sfDataCrawl import settings
import numpy as np
from decimal import *

def get_date_by_interval(source_date, interval_type=1):
    o_source_date =datetime.datetime.strptime(source_date, '%Y-%m-%d').date()
    source_year = o_source_date.year
    source_month = o_source_date.month
    source_date = o_source_date.day
    result_date = source_date
    target_year = ''
    target_month = ''
    target_day = ''
    if interval_type == 1 or interval_type == 2 or interval_type == 3:
        #近几月
        month_type = {1: 1, 2: 3, 3: 6}
        interval_value = month_type[interval_type]
        if source_month < interval_value :
            target_year = source_year - 1
        else:
            target_year = source_year
        target_month = divmod(source_month + 12 - interval_value, 12)[1]
        if target_month == 0 :
            target_month = 12
            target_year -= 1
        count_day = calendar.monthrange(target_year,target_month)[1]
        if count_day < source_date:
            target_day = count_day
        else:
            target_day = source_date
        result_date = datetime.date(target_year, target_month, target_day)
    elif interval_type == 4:
        #今年以来
        target_year = source_year
        result_date = datetime.date(target_year, 1, 1)
        pass
    elif interval_type == 5 or interval_type == 6 or interval_type == 7 or interval_type == 8 or interval_type == 9:
        #近几年
        year_type = {5 : 1, 6 : 2, 7 : 3, 8 : 4, 9 : 5}
        interval_value = year_type[interval_type]
        target_year = source_year - interval_value
        target_month = source_month
        count_day = calendar.monthrange(target_year, target_month)[1]
        if count_day < source_date:
            target_day = count_day
        else:
            target_day = source_date
        result_date = datetime.date(target_year, target_month, target_day)
        pass
    elif interval_type == 10 or interval_type == 11 or interval_type == 12 or interval_type == 13 or interval_type == 14:
        year_type = {10 : 1, 11 : 2, 12 : 3, 13 : 4, 14 : 5}
        interval_value = year_type[interval_type]
        target_year = source_year - interval_value
        target_month = 1
        target_day = 1
        result_date = datetime.date(target_year, target_month, target_day)
    return result_date

def get_day_interval(source_date,target_date):
    o_source_date = datetime.datetime.strptime(source_date, '%Y-%m-%d').date()
    o_target_date = datetime.datetime.strptime(target_date, '%Y-%m-%d').date()
    return (o_target_date - o_source_date).days

class SfDataCrawlPipeline(object):
    host = '192.168.83.31'
    user_name = 'root'
    password = 'Jrcs@15F'
    db_name = 'sf_crawl'
    cursor = ''
    conn = ''
    def __init__(self):
        try:
            self.conn = MySQLdb.connect(self.host, self.user_name, self.password, self.db_name, charset='utf8',use_unicode=True)
            self.cursor = self.conn.cursor()
        except MySQLdb.Error,e:
            print 'initial error'
            print str(e)

    def process_item(self, item, spider):
        #test db in the localhost
        # if 'name1' in item:
        #     try:
        #         self.cursor.execute('INSERT INTO test(name) VALUES(%s)', [item['name1']])
        #         self.conn.commit()
        #     except MySQLdb.Error, e:
        #         print "ERROR"
        return item

class SfProductPipeline(object):
    def process_item(self,item,spider):
        # return item
        if 'crawl_product_id' in item and 'crawl_product_name' in item:
            conn = spider.conn
            cursor = spider.cursor
            product_dict = spider.product_dict
            howbuy_product_dict = spider.howbuy_product_dict
            product_name = item['crawl_product_name']
            howbuy_id = item['crawl_product_id']
            if howbuy_id not in howbuy_product_dict:
                if product_name not in product_dict:
                    #新产品，从未采集过
                    try:
                        cursor.execute(
                            'INSERT INTO sf_product(crawl_id,name,full_name,nav_date,company_id,manager_list,start_date,trustee_bank,product_type,\
                            company_name,min_purchase_amount,min_append_amount,structured,crawl_url,crawl_company_id,crawl_managers_list,crawl_create_time,crawl_update_time,create_time,update_time)\
                             VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                            [item['crawl_product_id'], item['crawl_product_name'], item['crawl_product_full_name'], item['nav_date'], item['company_id']
                            , item['manager_list'],item['start_date'],item['trustee_bank'],item['product_type'],item['company_name']
                            ,item['min_purchase_amount'],item['min_append_amount'],item['structured'],item['crawl_url'],item['crawl_company_id'],item['manager_list'],item['now_time'],item['now_time'],item['now_time'],item['now_time']])
                        new_product_id = cursor.lastrowid
                        cursor.execute('INSERT INTO sf_product_data(id,crawl_id,subscription_fee,fixed_management_fee,ransom_fee,commission,open_date,locked_time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',
                            [int(conn.insert_id()),item['crawl_product_id'],item['subscription_fee'],item['fixed_management_fee'], item['ransom_fee'],item['commission'], item['open_date'], item['locked_time']])
                        conn.commit()
                        spider.spider_log.info('-----crawl sf_product_data success-----')
                        spider.product_dict[product_name] = {'id':new_product_id,'name':product_name,'status':0,
                                                             'howbuy_id':howbuy_id,'howbuy_update_time': item['now_time']}
                        spider.howbuy_product_dict[howbuy_id] = {'id':new_product_id,'name':item['crawl_product_name'],
                                                                 'status':0,'howbuy_id':howbuy_id,'howbuy_update_time': item['now_time']}
                        spider.nav_dict[new_product_id] = {'date':'1980-01-01'}

                        #插入sf_dividend_split操作
                        if item['dividend_date'] is not None:
                            length = len(item['dividend_date'])
                            insertString = list()
                            for i in range(0, length):
                                create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                                update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                                insertString.append( '(' + new_product_id + '，' + 1 + '，' + item['dividend_date'][length - i - 1]+ ',' +None+','+ create_time + ',' + update_time + ')')
                            insert_sfdividendsplit_sql = ' INSERT INTO `sf_dividend_split`(product_id, `type`, `date`,`value`, create_time, update_time)VALUES( %s, %s, %s, %s, %s, %s,%s)'
                            cursor.executemany(insert_sfdividendsplit_sql, [insertString])
                            conn.commit()

                    #             spider.spider_log.info('-----crawl sf_dividend_split success-----')
                    # except MySQLdb.Error, e:
                    #     print str(e)
                    except Exception, e:
                        # spider.spider_log.error('-----sql_error-----:' + str(e))
                        spider.spider_log.error('-----insert sf_product fail-----:' + str(e) + ',insert howbuy_id' + str(howbuy_id) +  ',insert product_name' + str(product_name))
                else:
                    product_info = product_dict[product_name]
                    product_id = product_info['id']
                    try:
                        #该产品已经存在，可能为手工录入，可能是第一次采集，故无匹配关系
                        cursor.execute('UPDATE sf_product set crawl_id = %s,nav_date = %s,manager_list = %s,start_date = %s,trustee_bank = %s,product_type = %s\
                         ,min_purchase_amount = %s,structured = %s,crawl_url = %s,crawl_company_id = %s,crawl_managers_list = %s,\
                         update_time = %s, crawl_update_time = %s where id = %s',
                         [howbuy_id,item['nav_date'],item['manager_list'],item['start_date'],item['trustee_bank'],item['product_type'],
                         item['min_purchase_amount'],item['structured'],item['crawl_url'],item['crawl_company_id'],
                          item['manager_list'],item['now_time'],item['now_time'],product_id])
                        conn.commit()
                        spider.product_dict[product_name] = {'id': product_id,'name': product_name,'status': 0,
                                                             'howbuy_id': howbuy_id,'howbuy_update_time': item['now_time']}
                        spider.howbuy_product_dict[howbuy_id] = {'id': product_id,'name': product_name,'status': 0,
                                                                 'howbuy_id': howbuy_id,'howbuy_update_time': item['now_time']}

                        # 插入sf_dividend_split操作
                        if item['dividend_date'] is not None:
                            length = len(item['dividend_date'])
                            for i in range(0, length):
                                query_date = item['dividend_date'][length - i - 1]
                                is_sfdividend_split_exist_sql = 'SELECT * FROM `sf_dividend_split` WHERE`date` =%s and product_id = %s'
                                cursor.execute(is_sfdividend_split_exist_sql, [query_date, product_id])
                                queryResult = cursor.fetchone()
                                if queryResult is None:
                                    insert_sfdividendsplit_sql = ' INSERT INTO `sf_dividend_split` (product_id, `type`, `date`,`value`, create_time, update_time)VALUES( %s,%s,%s, %s,%s,%s)'
                                    create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                                    update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                                    cursor.execute(insert_sfdividendsplit_sql, [product_id, 1, item['dividend_date'][length - i- 1],None, create_time,update_time])
                                    conn.commit()

                #                 spider.spider_log.info('-----insert sf_dividend_split success-----:')
                    # except MySQLdb.Error, e:
                    #     print '**************', e
                    except MySQLdb.Error, e:
                        spider.spider_log.error('-----update sf_product fail-----:' + str(e) + ',更新失败的howbuy_id' + str(howbuy_id) + ',更新失败的product_name' + str(product_name)+ ',更新失败的product_id' +product_id)
                pass
            else:
                if product_name not in product_dict:
                    #采集过，但是产品名字修改
                    #TODO 需讨论
                    pass
                else:
                    #完全匹配
                    product_info = product_dict[product_name]
                    product_id = product_info['id']
                    try:
                        #该产品已经存在，可能为手工录入，可能是第一次采集，故无匹配关系
                        cursor.execute('UPDATE sf_product set crawl_id = %s,nav_date = %s,manager_list = %s,start_date = %s,trustee_bank = %s,product_type = %s\
                        ,min_purchase_amount = %s,structured = %s,crawl_url = %s,crawl_company_id = %s,crawl_managers_list = %s,crawl_update_time = %s,update_time= %s where id = %s',
                        [howbuy_id,item['nav_date'],item['manager_list'],item['start_date'],item['trustee_bank'],item['product_type'],
                        item['min_purchase_amount'],item['structured'],item['crawl_url'],item['crawl_company_id'],item['manager_list'],item['now_time'],item['now_time'],product_id])
                        conn.commit()

                        # 插入sf_dividend_split操作
                        if item['dividend_date'] is not None:
                            length = len(item['dividend_date'])
                            for i in range(0, length):
                                query_date = item['dividend_date'][length - i - 1]
                                is_sfdividend_split_exist_sql = 'SELECT * FROM `sf_dividend_split` WHERE`date` =%s and product_id = %s'
                                cursor.execute(is_sfdividend_split_exist_sql, [query_date, product_id])
                                queryResult = cursor.fetchone()                               
                                if queryResult is None:
                                    insert_sfdividendsplit_sql = ' INSERT INTO `sf_dividend_split` (product_id, `type`, `date`, `value`,create_time, update_time)VALUES( %s, %s, %s, %s, %s,%s)'
                                    create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                                    update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                                    cursor.execute(insert_sfdividendsplit_sql, [product_id, 1, item['dividend_date'][length - i - 1],None,create_time,update_time])
                                    conn.commit()

                    # except MySQLdb.Error, e:
                    #     print '**************', e
                    except MySQLdb.Error, e:
                        # spider.spider_log.error('-----sql_error-----:' + str(e))
                        spider.spider_log.error('-----update sf_product fail-----:' + str(e) + ',更新失败的product_info' + str(product_info))
                    pass
                pass
                pass
        return item

class SfCompanyPipeline(object):
    def process_item(self,item,spider):
        if 'core_manager_name' in item and 'registered_capital' in item:
            conn = spider.conn
            cursor = spider.cursor
            company_dict = spider.company_dict
            howbuy_company_dict = spider.howbuy_company_dict
            company_name = item['name']
            howbuy_id = item['crawl_id']
            if howbuy_id not in howbuy_company_dict:
                if company_name not in company_dict:
                    #新公司，从未采集过
                    try:
                        cursor.execute(
                            'INSERT INTO sf_company(crawl_url,crawl_create_time,crawl_update_time,crawl_id,full_name,name,core_manager_name,rep_product_name,\
                            icp,establishment_date,registered_capital,region,update_time,create_time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                            [item['crawl_url'],item['crawl_create_time'],item['crawl_update_time'],item['crawl_id'],item['full_name'],
                            item['name'], item['core_manager_name'], item['rep_product_name'],item['icp'],item['establishment_date'],
                            item['registered_capital'],item['region'],item['update_time'],item['create_time']])
                        lastid = int(cursor.lastrowid)
                        cursor.execute('INSERT INTO sf_company_data(id) VALUES(%s)',[lastid])
                        #update company dict
                        update_company_info = {
                            'id': lastid,
                            'name': item['name'],
                            'status': 0,
                            'howbuy_id': howbuy_id,
                            'howbuy_update_time': item['crawl_update_time']
                        }
                        conn.commit()
                        spider.spider_log.info('-----SfCompanyPipeline insert sf_company success-----:company_id:' + str(lastid) + 'crawl_company_id:' + str(howbuy_id))
                        spider.company_dict[company_name] = update_company_info
                        spider.howbuy_company_dict[howbuy_id] = update_company_info
                        #update sf_product companye_id
                        update_product_sql = 'UPDATE sf_product set company_id = %s, update_time=%s where crawl_company_id = %s AND company_id = %s '
                        cursor.execute(update_product_sql,[lastid,item['update_time'],howbuy_id, None])
                        conn.commit()
                        spider.spider_log.info('-----SfCompanyPipeline update sf_product success-----:company_id' + str(lastid) + 'crawl_company_id' + str(howbuy_id))
                        # update sf_manager companye_id
                        update_manager_sql = 'UPDATE sf_manager set company_id = %s, update_time = %s WHERE crawl_company_id = %s AND company_id = %s'
                        cursor.execute(update_manager_sql, [lastid, item['update_time'], howbuy_id, None])
                        conn.commit()
                        spider.spider_log.info('-----SfCompanyPipeline update sf_manager success-----:company_id' + str(lastid) + 'crawl_company_id' + str(howbuy_id))
                    # except MySQLdb.Error, e:
                    #     print '**************', e

                    except MySQLdb.Error, e:
                        # spider.spider_log.error('-----SfCompanyPipeline sql_error-----:' + str(e))
                        spider.spider_log.error('-----SfCompanyPipeline sql fail-----:' + str(e) + ',更新失败：' + str(item))
                else:
                    company_info = company_dict[company_name]
                    company_id = company_info['id']
                    sql = 'UPDATE sf_company set crawl_id=%s,full_name=%s,crawl_update_time =%s, crawl_url=%s, core_manager_name=%s,\
                        rep_product_name=%s, icp=%s, establishment_date=%s, registered_capital=%s, region=%s ,update_time=%s where id = %s'
                    param = [howbuy_id ,
                        item['full_name'],item['crawl_update_time'],item['crawl_url'],item['core_manager_name'],item['rep_product_name'],item['icp'],
                        item['establishment_date'],item['registered_capital'],item['region'],item['update_time'],company_id]
                    try:
                        #该公司已经存在，可能为手工录入，可能是第一次采集，故无匹配关系
                        cursor.execute(sql,param)
                        conn.commit()
                        spider.spider_log.info('-----UPDATE SfCompanyPipeline sf_company success-----:crawl_id' + str(howbuy_id) +', company_id' + str(company_id))
                        # update company dict
                        update_company_info = {
                            'id': company_id,
                            'name': item['name'],
                            'status': 0,
                            'howbuy_id': howbuy_id,
                            'howbuy_update_time': item['crawl_update_time']
                        }
                        spider.company_dict[company_name] = update_company_info
                        spider.howbuy_company_dict[howbuy_id] = update_company_info
                    # except MySQLdb.Error, e:
                    #     print '**************', e
                    except MySQLdb.Error, e:
                        # spider.spider_log.error('-----sql_error-----:' + str(e))
                        spider.spider_log.error('-----SfCompanyPipeline sql fail-----:' + str(e) + ',update fail sql：' + sql + ',update fail data：'+str(param))
                pass
            else:
                if company_name not in company_dict:
                    #采集过，但是产品名字修改
                    #TODO 需讨论
                    pass
                else:
                    #完全匹配
                    company_info = company_dict[company_name]
                    company_id = company_info['id']
                    sql = 'UPDATE sf_company set crawl_id = %s,update_time=%s where id = %s'
                    param = [howbuy_id ,item['update_time'], company_id]
                    try:
                        #该产品已经存在，可能为手工录入，可能是第一次采集，故无匹配关系
                        cursor.execute(sql,param)
                        conn.commit()
                        spider.spider_log.info('-----UPDATE SfCompanyPipeline sf_company success-----:crawl_id' + str(howbuy_id) +', company_id' + str(company_id))
                    # except MySQLdb.Error, e:
                    #     print '**************', e
                    except MySQLdb.Error, e:
                        spider.spider_log.error('-----SfCompanyPipeline update sf_company sql fail-----:' + str(e) + ',update fail sql：' + sql + ',update param：' + str(param))
                    pass
        return item


class NavPipeline(object):
    def cmp_func(self,a,b):
        max_date_1 = a['max'][0]
        max_date_2 = b['max'][0]
        if max_date_1 > max_date_2:
            return 1
        else:
            return -1
        pass
    def process_item(self, item, spider):
        cursor = spider.cursor
        conn = spider.conn
        if 'nav_item_date' in item:
            cursor = spider.cursor
            conn = spider.conn
            max_month = 0
            if len(item['nav_item_date']) == 0:
                return item
            sql = 'insert into sf_nav(product_id,crawl_id,nav_date,added_nav,nav,growth_rate,create_time,update_time,crawl_time,crawl_url) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            try:
                cursor.executemany(sql, item['nav_item_date'])
                conn.commit()
                spider.spider_log.info('-----NavPipeline insert sf_nav success -----')
            except Exception, e:
                spider.spider_log.error('-----NavPipeline insert sf_nav fail-----:' + str(e)+",insert fail sql "+ sql + "，insert fail data：" +str(item['nav_item_date']))
            #提取净值
            product_id = item['product_id'][0]
            cursor.execute('SELECT nav_date,nav,added_nav FROM sf_nav where product_id = %s Order By `nav_date` DESC',
                           [product_id])
            product_all_navs = cursor.fetchall()
            hs300_dict = spider.hs300_dict
            self._return_drawdown(item['product_id'][0], cursor, spider, conn, product_all_navs, hs300_dict)
            #月回撤
            # cursor.execute('SELECT `year_month`,added_nav,hs300 FROM sf_return_drawdown where type = %s AND product_id = %s order by `year_month` DESC limit 2',[2,item['product_id'][0]])
            # #self.cursor.execute('SELECT MAX(year_month) FROM sf_return_drawdown')
            # navs = cursor.fetchall()
            # #print navs
            # product_navs = []
            # if len(navs) == 0:
            #     product_navs = product_all_navs
            # else:
            #     max_month = navs[0][0]
            #     max_day = navs[0][0]+'-01'
            #     end_time = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            #     for nav_line in product_all_navs:
            #         nav_line_date = nav_line[0].strftime('%Y-%m-%d')
            #         if nav_line_date >= max_day and nav_line_date <= end_time:
            #             product_navs.append(nav_line)
            #     # cursor.execute('SELECT nav_date,nav,added_nav FROM sf_nav where product_id = %s AND `nav_date` >= %s and `nav_date` <= %s Order By `nav_date`',[item['product_id'][0],max_day,end_time])
            #     # product_navs = cursor.fetchall()
            # return_navs = {}
            # list_navs = []
            # list_data = []
            # results = {}
            # result = {}
            # hs_data = []
            # hs_value = {}
            # hs_list = {}
            # hs_result = {}
            # hs300_dict = spider.hs300_dict
            # hs300_list = sorted(spider.hs300_dict.keys(),reverse=True)
            # current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            # current_month = time.strftime('%Y-%m', time.localtime(time.time()))
            # if not all(product_navs[0]):
            #     print "此产品暂时无数据"
            # else:
            #     for product_nav in product_navs:
            #         data = product_nav[0]
            #         month = str(data)[0:7]
            #         if month not in return_navs:
            #             return_navs[month] = {'max':product_nav,'min':product_nav}
            #         else:
            #             if return_navs[month]['max'][0] < data:
            #                 return_navs[month]['max'] = product_nav
            #             if return_navs[month]['min'][0] > data:
            #                 return_navs[month]['min'] = product_nav
            #     for k in return_navs:
            #         list_navs.append(return_navs[k])
            #     for j in sorted(list_navs,cmp=self.cmp_func):
            #         list_data.append(j)
            #     for i in range(0, len(list_data)):
            #         sMax = str(list_data[i]['max'][0])
            #         sMonth = str(list_data[i]['max'][0])[0:7]
            #         if str(current_month) != sMonth:
            #             hs_max = sMax
            #             if hs_max not in hs300_dict:
            #                 for hs_i_index in range(0,len(hs300_list)):
            #                     #向前寻找
            #                     if hs300_list[hs_i_index] <= hs_max:
            #                         hs_max = hs300_list[hs_i_index]
            #                         break
            #             if i+1 == len(list_data):
            #                 results[sMonth] = list_data[i]['max']
            #                 hs_list[sMonth] = hs300_dict[hs_max]['hs_index']
            #             else:
            #                 sNextMin = str(list_data[i+1]['min'][0])
            #                 hs_next_min = sNextMin
            #                 if hs_next_min not in hs300_dict:
            #                     for hs_i_index in range(0, len(hs300_list)):
            #                         # 像前寻找
            #                         if hs300_list[hs_i_index] <= hs_next_min:
            #                             hs_next_min = hs300_list[hs_i_index]
            #                             break
            #                 sFirst = str(list_data[i+1]['min'][0])[0:7]+'-01'
            #                 timefArray = time.strptime(sFirst,"%Y-%m-%d")
            #                 timeaArray = time.strptime(sMax,"%Y-%m-%d")
            #                 timeiArray = time.strptime(sNextMin,"%Y-%m-%d")
            #                 timeFtamp = int(time.mktime(timefArray))
            #                 timeAtemp = int(time.mktime(timeaArray))
            #                 timeItemp = int(time.mktime(timeiArray))
            #                 if abs(timeAtemp - timeFtamp) > abs(timeItemp - timeFtamp):
            #                     results[sMonth] = list_data[i+1]['min']
            #                     hs_list[sMonth] = hs300_dict[hs_next_min]['hs_index']
            #                 else:
            #                     results[sMonth] = list_data[i]['max']
            #                     hs_list[sMonth] = hs300_dict[hs_max]['hs_index']
            #     keys = results.keys()
            #     keys.sort()
            #     for key in range(0,len(keys)):
            #         k = keys[key]
            #         result[k] = {}
            #         hs_result[k] = {}
            #         if key == 0:
            #             result[k]['value'] = 0
            #             hs_result[k]['value'] = 0
            #         else:
            #             last_key = keys[key-1]
            #             result[k]['value'] = round((results[k][2] - results[last_key][2])/results[k][2],4)
            #             hs_result[k]['value'] = round((hs_list[k] - hs_list[last_key])/hs_list[k],4)
            #             if result[k]['value'] > 0:
            #                 result[k]['value'] = 0
            #             if hs_result[k]['value'] > 0:
            #                 hs_result[k]['value'] = 0
            #     for key in results:
            #         if max_month != 0 and key == max_month:
            #             if len(navs) == 2:
            #                 max_month_value = round((results[key][2] - navs[1][1])/results[key][2],4)
            #                 max_hs300 = round((hs_list[key] - navs[1][2])/hs_list[k],4)
            #             else:
            #                 max_month_value = round((results[key][2] - navs[0][1])/results[key][2],4)
            #                 max_hs300 = round((hs_list[key] - navs[0][2])/hs_list[k],4)
            #             if max_month_value > 0:
            #                 max_month_value = 0
            #             if max_hs300 >0:
            #                 max_hs300 = 0
            #             try:
            #                 sql = 'UPDATE sf_return_drawdown SET nav = %s,added_nav = %s,value=%s,hs300=%s,update_time=%s where product_id = %s and `year_month`=%s'
            #                 param = [results[key][1],results[key][2],max_month_value,max_hs300,current_time,item['product_id'][0],max_month]
            #                 cursor.execute(sql,param)
            #             except Exception, e:
            #                 spider.spider_log.error('-----NavPipeline update sf_return_drawdown fail-----:' + str(e) + ",update fail sql " + sql + "，update fail data：" + str(param))
            #         else:
            #             try:
            #                 return_value = result[key]['value']
            #                 hs_return_value = hs_result[key]['value']
            #                 if return_value > 0:
            #                     return_value = 0
            #                 if hs_return_value > 0:
            #                     hs_return_value = 0
            #                 sql = 'INSERT INTO sf_return_drawdown(product_id,type,`year_month`,nav,added_nav,value,hs300,create_time,update_time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            #                 param = [item['product_id'][0],2,key,results[key][1],results[key][2],return_value,hs_return_value,current_time,current_time]
            #                 cursor.execute(sql,param)
            #                 conn.commit()
            #                 spider.spider_log.info('-----NavPipeline insert sf_return_drawdown success -----')
            #             except Exception, e:
            #                 spider.spider_log.error('-----NavPipeline INSERT sf_return_drawdown fail-----:' + str(e) + ",INSERT fail sql " + sql + "，INSERT fail data：" + str(param))
            #         #计算统计数据
            #         self._calculate_statistics(item['product_id'][0],cursor,spider,conn,product_all_navs,hs300_dict)
                    #计算月回报
                    # self._return_drawdown(item['product_id'][0],cursor,spider,conn,product_all_navs,hs300_dict)

                # 更新sf_dividend_split 的value
                # product_nav_dict = {}
                # for nav_line in product_all_navs:
                #     nav_date = str(nav_line[1])
                #     product_nav_dict [nav_date] = {
                #         'nav_date' : nav_date,
                #         'nav' : nav_line[1],
                #         'added_nav':nav_line[2]
                #     }
                # product_nav_dates = sorted(product_nav_dict.keys())
                # nav_dividend_sql = 'SELECT `date`,`value` FROM `sf_dividend_split` WHERE product_id = %s ORDER BY `date`'
                # cursor.execute(nav_dividend_sql, [item['product_id'][0]])
                # sf_dividend_info = cursor.fetchall()
                # previous_dividend = 0
                # if len(sf_dividend_info) > 0:
                #     for dividend_line in sf_dividend_info:
                #         dividend_date = str(dividend_line[0])
                #         dividend_value = dividend_line[1]
                #         if dividend_value is not None:
                #             previous_dividend += dividend_value
                #         else:
                #             match_nav_date = None
                #             for nav_date in product_nav_dates:
                #                 if nav_date > dividend_date:
                #                     match_nav_date = nav_date
                #                     break;
                #             #如果分红之后无净值数据，该分红信息忽略
                #             if match_nav_date is not None:
                #                 nav_delta = product_nav_dict[match_nav_date]['added_nav'] - product_nav_dict[match_nav_date]['nav']
                #                 dividend_value = nav_delta - previous_dividend
                #                 update_dividend_sql = ' UPDATE `sf_dividend_split` SET `value`=%s, update_time = %s where date=%s AND product_id =%s'
                #                 current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                #                 cursor.execute(update_dividend_sql, [dividend_value,current_time, dividend_date, product_id])
                #                 conn.commit()
                #                 previous_dividend += nav_delta
            # except MySQLdb.Error, e:
            #     spider.spider_log.error(cursor._last_executed)
            #     #spider.spider_log.error('插入失败的produt_id: '+str(item))
            #     pass
            pass

        return item
    def _calculate_statistics(self,product_id,cursor,spider,conn,product_navs,hs300_dict):
        #无风险利率
        unrisk_rate = 0.026
        sf_navs = product_navs
        need_insert = False
        statistic_select_sql = 'SELECT count(1) FROM sf_statistic WHERE product_id = %s'
        cursor.execute(statistic_select_sql,[product_id])
        statistic_info = cursor.fetchall()
        for statistic_line in statistic_info:
            if statistic_line[0] == 0 :
                need_insert = True
        sf_nav_dict = {}
        sf_latest_date = ''
        sf_first_date = ''
        if len(sf_navs) > 0:
            current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            result = {}
            net_result = {}
            for i in range(1,16):
                result[i] = {
                    'product_id': product_id,
                    'time_type': i,
                    'type_average_net': None,
                    'four_bit_rank': None,
                    'hs300': None,
                    'annualized_wave': None,
                    'annualized_net': None,
                    'retrace': None,
                    'sharp': None,
                    'calmar': None,
                    'sortino': None,
                    'month_win': None,
                    'type_average_rank': None,
                    'update_time': current_time
                }
                net_result[i] = None
            date_index = 0
            sf_latest_date = str(sf_navs[0][0])
            target_date = {}
            o_latest_date = datetime.datetime.strptime(sf_latest_date, '%Y-%m-%d').date()
            for i in range(1,15):
                target_day = get_date_by_interval(sf_latest_date,i)
                target_date[i] = {
                    'target_date' : target_day,
                    'target_nav_date' : sf_latest_date,
                    'offset' : abs((o_latest_date - target_day).days),
                    'dates' : [], #绝对区间内的数据
                    'nav_datas': []  # 绝对区间内的净值
                }
            create_data = []
            for nav_info in sf_navs:
                nav_date = str(nav_info[0])
                nav = nav_info[1]
                added_nav = nav_info[2]
                sf_nav_dict[nav_date] = {'nav_date':nav_date,'nav':nav,'added_nav':added_nav}
                create_data.append(nav)
                o_nav_date = datetime.datetime.strptime(nav_date, '%Y-%m-%d').date()
                for i in range(1,15):
                    target_day = target_date[i]['target_date']
                    temp_offset = (o_nav_date - target_day).days
                    offset = abs(temp_offset)
                    if offset < target_date[i]['offset']:
                        target_date[i]['target_nav_date'] = nav_date
                        target_date[i]['offset'] = offset
                    if i < 10 or i == 15:
                        if temp_offset >= 0:
                            target_date[i]['dates'].append(nav_date)
                            target_date[i]['nav_datas'].append(nav)
                    else:
                        o_return_last_day = datetime.date(target_day.year,12,31)
                        right_offset = (o_return_last_day - o_nav_date).days
                        if temp_offset >=0 and right_offset >=0:
                            target_date[i]['dates'].append(nav_date)
                            target_date[i]['nav_datas'].append(nav)
            #补全逐年中年初的摇摆值
            for time_index in range(10, 14):
                nav_dates = target_date[time_index]['dates']
                target_nav_date = target_date[time_index]['target_nav_date']
                date_length = len(nav_dates)
                if date_length > 0 and nav_dates[date_length - 1] != target_nav_date:
                    target_date[time_index]['dates'].append(target_nav_date)
                    nav = sf_nav_dict[target_nav_date]['nav']
                    target_date[time_index]['nav_datas'].append(nav)
                    pass
            sf_first_date = min(sf_nav_dict.keys())
            o_sf_first_date = datetime.datetime.strptime(sf_first_date, '%Y-%m-%d').date()
            max_offset = (o_latest_date - o_sf_first_date).days
            target_date[15] = {
                'target_date': o_sf_first_date,
                'target_nav_date': sf_first_date,
                'offset': max_offset,
                'dates': sorted(sf_nav_dict.keys(),reverse=True),  # 绝对区间内的数据
                'nav_datas':create_data
            }
            for i in range(1,16):
                o_target_info = target_date[i]
                if o_target_info['offset'] <= max_offset:
                    #标准差
                    standard_deviation = 0
                    #和值
                    sum_net = 0
                    #时间差
                    delta_day = 0
                    #净值list
                    nets = o_target_info['nav_datas']
                    target_nav_date = o_target_info['target_nav_date']
                    #系数
                    #标准差
                    if(len(target_date[i]['nav_datas']) > 1):
                        std_num = np.std(target_date[i]['nav_datas'])
                        if(i == 1 or i ==2 or i ==3 or i ==4):
                            start = datetime.datetime.strptime(target_date[i]['dates'][0],'%Y-%m-%d')
                            end = datetime.datetime.strptime(target_date[i]['dates'][len(target_date[i]['dates'])-1],'%Y-%m-%d')
                            dayNum = (start - end).days
                            year_wave = std_num/dayNum*365
                        elif (i == 6):
                            year_wave = std_num/2
                        elif (i == 7):
                            year_wave = std_num/3
                        elif (i == 8):
                            year_wave = std_num/4
                        elif (i == 9):
                            year_wave = std_num/5
                        elif (i == 10 or i == 11 or i == 12 or i == 13 or i == 14 or i == 5):
                            year_wave = std_num
                        elif (i == 15):
                            if target_date[15]['offset'] == 0:
                                year_wave = None
                            else:
                                year_wave = std_num/target_date[15]['offset']*365
                        if year_wave:
                            result[i]['year_wave'] = '%.4f' % year_wave
                        else:
                            result[i]['year_wave'] = 0
                    else:
                        result[i]['year_wave'] = 0
                    net_value = 0
                    begin_day_info = sf_nav_dict[target_nav_date]
                    date_info = o_target_info['dates']
                    date_length = len(date_info)
                    last_day = sf_latest_date
                    begin_day = target_nav_date
                    if date_length > 1:
                        if i > 9 and i < 15:
                            #逐年
                            last_day = date_info[0]
                            begin_day = date_info[date_length-1]

                        delta_day = get_day_interval(begin_day, last_day)

                        standard_deviation = np.std(nets)

                        begin_day_info = sf_nav_dict[begin_day]
                        end_day_info = sf_nav_dict[last_day]
                        if(i<15):
                            net_value = (end_day_info['nav'] - begin_day_info['nav']) / begin_day_info['nav']
                        else:
                            net_value = end_day_info['added_nav'] - 1
                        net_result[i] = net_value
                        hs300_dates = sorted(hs300_dict.keys(),reverse=True)
                        hs_last_day = last_day
                        hs_begin_day = begin_day
                        if last_day not in hs300_dict or begin_day not in hs300_dict:
                            hs_last_day_found = False
                            hs_begin_day_found = False
                            for hs_i_index in range(0, len(hs300_dates)):
                                if not hs_last_day_found:
                                    if hs300_dates[hs_i_index] < hs_last_day:
                                        hs_last_day_found = True
                                        hs_last_day = hs300_dates[hs_i_index]
                                if not hs_begin_day_found:
                                    if hs300_dates[hs_i_index] < hs_begin_day:
                                        hs_begin_day = hs300_dates[hs_i_index]
                                        hs_begin_day_found = True
                                if hs_last_day_found and hs_begin_day_found:
                                    break

                        hs_net_value = round(hs300_dict[hs_last_day]['hs_index']/hs300_dict[hs_begin_day]['hs_index'] - 1, 4)
                        result[i]['hs300'] = round(hs_net_value,4)
                        if standard_deviation is not None and standard_deviation != 0:
                            sharp_value = round((net_value - Decimal(unrisk_rate))/standard_deviation,4)
                            result[i]['sharp'] = round(sharp_value,4)
                        #年化收益率
                        if i <= 4 or i == 15:
                            ratio = Decimal(365.0 / delta_day)
                            result[i]['annualized_net'] = round((float(net_value)/delta_day)*365,4)
                        elif i >= 5 and i <= 9:
                            #近n年
                            ratio = Decimal(1.0 / (i - 4))
                            result[i]['annualized_net'] = round(float(net_value)/(i-4),4)
                        else:
                            # 逐年
                            ratio = 1
                            result[i]['annualized_net'] = round(net_value,4)
                        #年化波动率：
                        result[i]['annualized_wave'] = round(standard_deviation * ratio, 4)
                        #最大回撤
                        result[i]['retrace'] = max(nets) - min(nets)
                        #索提诺比率
                        if i > 4:
                            if result[i]['annualized_net'] is not None and result[i]['retrace'] is not None and result[i]['retrace'] != 0:
                                result[i]['sortino'] = round((float(result[i]['annualized_net']) - 0.026)/float(result[i]['retrace']),4)
                    elif date_length == 1:
                        #孤立值
                        pass
                    pass
            product_update = 'UPDATE sf_product set latest_nav = %s, added_nav = %s, return_recent_month1 = %s,return_recent_month3 = %s,\
                  return_recent_month6=%s, return_recent_year1 = %s, return_recent_year2 = %s, return_recent_year3 = %s,\
                  return_recent_year4 = %s, return_recent_year5 = %s, return_year1 = %s, return_year2 = %s, return_year3 = %s, \
                  return_year4 = %s, return_year5 = %s ,update_time = %s WHERE id = %s'
            cursor.execute(product_update,
                           [ sf_nav_dict[sf_latest_date]['nav'], sf_nav_dict[sf_latest_date]['added_nav'],
                             net_result[1], net_result[2], net_result[3], net_result[5], net_result[6], net_result[7],
                             net_result[8], net_result[9], net_result[10], net_result[11], net_result[12],
                             net_result[13], net_result[14], current_time,product_id
                             ])
            conn.commit()
            spider.spider_log.info('-----update sf_product success-----:product_id:' + str(product_id))
            from_start_date = sf_first_date
            if result[i]['annualized_net'] is not None and result[i]['annualized_net'] != 0 :
                result[i]['calmer_value'] = round(round(result[i]['retrace'],4)/result[i]['annualized_net'],4)     
            result_value = []

            if need_insert is False:
                try:
                    for i in range(1, 16):
                        update_static = 'UPDATE sf_statistic set type_average_net = %s,four_bit_rank = %s,hs300 = %s,annualized_wave = %s,annualized_net = %s,\
                                            retrace = %s,sharp = %s,calmar = %s,sortino = %s,month_win = %s,type_average_rank = %s,update_time = %s WHERE product_id = %s AND time_type = %s'
                        cursor.execute(update_static,[result[i]['type_average_net'],result[i]['four_bit_rank'],result[i]['hs300'],result[i]['annualized_wave'],result[i]['annualized_net'],result[i]['retrace'],
                            result[i]['sharp'],result[i]['calmar'],result[i]['sortino'],result[i]['month_win'],result[i]['type_average_rank'],current_time,product_id,result[i]['time_type']])
                    conn.commit()
                    spider.spider_log.info('-----update sf_statistic success-----:product_id:' + str(product_id))
                except MySQLdb.Error, e:
                    spider.spider_log.error('-----update sf_statistic fail-----:' + str(e)+',更新的sql'+update_static+',数据：'+str(result)+',更新失败id'+str(product_id))

            else:
                for i in range(1, 16):
                    static_nav = []
                    static_nav.append(result[i]['product_id'])
                    static_nav.append(result[i]['time_type'])
                    static_nav.append(result[i]['type_average_net'])
                    static_nav.append(result[i]['four_bit_rank'])
                    static_nav.append(result[i]['hs300'])
                    static_nav.append(result[i]['annualized_wave'])
                    static_nav.append(result[i]['annualized_net'])
                    static_nav.append(result[i]['retrace'])
                    static_nav.append(result[i]['sharp'])
                    static_nav.append(result[i]['calmar'])
                    static_nav.append(result[i]['sortino'])
                    static_nav.append(result[i]['month_win'])
                    static_nav.append(result[i]['type_average_rank'])
                    static_nav.append(current_time)
                    static_nav.append(current_time)
                    result_value.append(tuple(static_nav))
                insert_static = 'INSERT INTO sf_statistic(product_id,time_type,type_average_net,four_bit_rank,hs300,annualized_wave,annualized_net,\
                retrace,sharp,calmar,sortino,month_win,type_average_rank,create_time,update_time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
                try:
                    cursor.executemany(insert_static, result_value)
                    conn.commit()
                    spider.spider_log.info('-----insert sf_statistic success-----')
                except MySQLdb.Error, e:
                    spider.spider_log.error('-----insert sf_statistic fail-----:' + str(e) + ',insert sql' + insert_static + ',data：' + str(result_value))
        pass

    def _return_drawdown(self, product_id, cursor, spider, conn,product_navs,hs300_dict):
        with open("t.txt", 'a') as f:
            f.write('-------product_navs-----------'+str(product_navs)+','+'-------hs300_dict-----------'+str(hs300_dict)+"\r\n")

            return_navs = {}
            list_navs = []
            list_data = []
            results = {}
            result = {}
            hs_data = []
            hs_value = {}
            hs_list = {}
            hs_result = {}
            hs300_list = sorted(hs300_dict.keys(),reverse=True)
            current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
            current_month = time.strftime('%Y-%m', time.localtime(time.time()))
            if product_navs is None:
                pass
            else:
                print 55555555555
                print product_navs
                i=0
                for product_nav in product_navs:
                    i = i+1
                    data = product_nav[0]
                    month = str(data)[0:7]
                    if month not in return_navs:
                        return_navs[month] = {'max':product_nav,'min':product_nav}
                    else:
                        if return_navs[month]['max'][0] < data:
                            return_navs[month]['max'] = product_nav
                        if return_navs[month]['min'][0] > data:
                            return_navs[month]['min'] = product_nav
                        if(return_navs[month]['min'][0] is None):
                            day = return_navs[month]['min'] + '-01'
                            i = 0
                            for nav_i_index in range(0, len(product_navs)):
                                i = i+1
                                # 向前寻找
                                if product_navs[nav_i_index] <= day or i < 15:
                                    return_navs[month]['min'] = product_navs[nav_i_index]
                                    break
                for k in return_navs:
                    list_navs.append(return_navs[k])
                for j in sorted(list_navs,cmp=self.cmp_func):
                    list_data.append(j)
                for i in range(0, len(list_data)):
                    sMax = str(list_data[i]['max'][0])
                    sMonth = str(list_data[i]['max'][0])[0:7]
                    if str(current_month) != sMonth:
                        hs_max = sMax
                        print 33333333333
                        print hs_max
                        if hs_max not in hs300_dict:
                            for hs_i_index in range(0,len(hs300_list)):
                                #向前寻找
                                if hs300_list[hs_i_index] <= hs_max:
                                    print 1111111111
                                    print hs_i_index
                                    print hs300_list[hs_i_index]
                                    hs_max = hs300_list[hs_i_index]
                                    break
                        if i+1 == len(list_data):
                            results[sMonth] = list_data[i]['max']
                            hs_list[sMonth] = hs300_dict[hs_max]['hs_index']
                        else:
                            sNextMin = str(list_data[i+1]['min'][0])
                            hs_next_min = sNextMin
                            print 44444444444
                            print hs_next_min
                            if hs_next_min not in hs300_dict:
                                for hs_i_index in range(0, len(hs300_list)):
                                    # 像前寻找
                                    if hs300_list[hs_i_index] <= hs_next_min:
                                        print 222222222222
                                        print hs_i_index
                                        print hs300_list[hs_i_index]
                                        hs_next_min = hs300_list[hs_i_index]
                                        break
                            sFirst = str(list_data[i+1]['min'][0])[0:7]+'-01'
                            timefArray = time.strptime(sFirst,"%Y-%m-%d")
                            timeaArray = time.strptime(sMax,"%Y-%m-%d")
                            timeiArray = time.strptime(sNextMin,"%Y-%m-%d")
                            timeFtamp = int(time.mktime(timefArray))
                            timeAtemp = int(time.mktime(timeaArray))
                            timeItemp = int(time.mktime(timeiArray))
                            if abs(timeAtemp - timeFtamp) > abs(timeItemp - timeFtamp):
                                results[sMonth] = list_data[i+1]['min']
                                hs_list[sMonth] = hs300_dict[hs_next_min]['hs_index']
                            else:
                                results[sMonth] = list_data[i]['max']
                                hs_list[sMonth] = hs300_dict[hs_max]['hs_index']
                keys = results.keys()
                keys.sort()
                for key in range(0,len(keys)):
                    k = keys[key]
                    result[k] = {}
                    hs_result[k] = {}
                    if key == 0:
                        result[k]['value'] = 0
                        hs_result[k]['value'] = 0
                    else:
                        last_key = keys[key-1]
                        result[k]['value'] = round((results[k][2] - results[last_key][2])/results[k][2],4)
                        hs_result[k]['value'] = round((hs_list[k] - hs_list[last_key])/hs_list[k],4)
                        if result[k]['value'] > 0:
                            result[k]['value'] = 0
                        if hs_result[k]['value'] > 0:
                            hs_result[k]['value'] = 0

            pass


            for key in results:
                if max_month != 0 and key == max_month:
                    if len(navs) == 2:
                        max_month_value = round((results[key][2] - navs[1][1])/results[key][2],4)
                        max_hs300 = round((hs_list[key] - navs[1][2])/hs_list[k],4)
                    else:
                        max_month_value = round((results[key][2] - navs[0][1])/results[key][2],4)
                        max_hs300 = round((hs_list[key] - navs[0][2])/hs_list[k],4)
                    if max_month_value > 0:
                        max_month_value = 0
                    if max_hs300 >0:
                        max_hs300 = 0
                    try:
                        sql = 'UPDATE sf_return_drawdown SET nav = %s,added_nav = %s,value=%s,hs300=%s,update_time=%s where product_id = %s and `year_month`=%s'
                        param = [results[key][1],results[key][2],max_month_value,max_hs300,current_time,item['product_id'][0],max_month]
                        cursor.execute(sql,param)
                    except Exception, e:
                        spider.spider_log.error('-----NavPipeline update sf_return_drawdown fail-----:' + str(e) + ",update fail sql " + sql + "，update fail data：" + str(param))
                else:
                    try:
                        return_value = result[key]['value']
                        hs_return_value = hs_result[key]['value']
                        if return_value > 0:
                            return_value = 0
                        if hs_return_value > 0:
                            hs_return_value = 0
                        sql = 'INSERT INTO sf_return_drawdown(product_id,type,`year_month`,nav,added_nav,value,hs300,create_time,update_time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)'
                        param = [item['product_id'][0],2,key,results[key][1],results[key][2],return_value,hs_return_value,current_time,current_time]
                        cursor.execute(sql,param)
                        conn.commit()
                        spider.spider_log.info('-----NavPipeline insert sf_return_drawdown success -----')
                    except Exception, e:
                        spider.spider_log.error('-----NavPipeline INSERT sf_return_drawdown fail-----:' + str(e) + ",INSERT fail sql " + sql + "，INSERT fail data：" + str(param))
                #计算统计数据
                self._calculate_statistics(item['product_id'][0],cursor,spider,conn,product_all_navs)
                #计算月回报
                self._return_drawdown(item['product_id'][0],cursor,spider,conn,product_all_navs,hs300_dict)

            # 更新sf_dividend_split 的value
            product_nav_dict = {}
            for nav_line in product_all_navs:
                product_nav_dict [nav_line[0]] = {
                    'nav_date' : nav_line[0],
                    'nav' : nav_line[1],
                    'added_nav':nav_line[2]
                }
            nav_date_sql = 'SELECT date FROM `sf_dividend_split` WHERE product_id = %s'
            cursor.execute(nav_date_sql, [item['product_id'][0]])
            navDates = cursor.fetchall()
            nav_value_sum = 0
            if navDates is not None:
                for navDate in navDates:
                    nav_data_sql = 'SELECT  nav,added_nav FROM sf_nav WHERE nav_date >= %s and product_id = %s ORDER BY nav_date LIMIT 1'
                    cursor.execute(nav_data_sql, [navDate, item['product_id'][0]])
                    nav_data = cursor.fetchone()
                    if nav_data is not None:
                        nav_value = nav_data[1] - nav_data[0] - nav_value_sum
                        nav_value_sum += nav_value
                        update_sfdividendsplit_sql = ' UPDATE `sf_dividend_split` SET `value`=%s where date=%s AND product_id =%s'
                        cursor.execute(update_sfdividendsplit_sql, [nav_value, navDate, item['product_id'][0]])







        #产品有净值的月数
        # sql = "SELECT DISTINCT(DATE_FORMAT(nav_date,'%%Y-%%m')) FROM sf_nav WHERE  product_id =%s ORDER BY nav_date DESC"
        # cursor.execute(sql, [product_id])
        # product_month = cursor.fetchall()
        # month_list = []
        # # 每个月的月初和月末净值
        # end_sql = "SELECT product_id,nav_date,nav,added_nav,growth_rate FROM sf_nav WHERE DATE_FORMAT(nav_date,'%%Y-%%m') = %s AND product_id =%s ORDER BY nav_date DESC limit 1"
        # start_sql = "SELECT product_id,nav_date,nav,added_nav,growth_rate FROM sf_nav WHERE DATE_FORMAT(nav_date,'%%Y-%%m') = %s AND product_id =%s ORDER BY nav_date ASC limit 1"
        # # 沪深300的月回报
        # hs_end_sql = "SELECT hs_index FROM `sf_hs_index` where index_date = %s limit 1"
        # now_month = time.strftime('%Y-%m', time.localtime(time.time()))
        # sf_return_drawdown = []
        # now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        # month_already = {}
        # hs_date_list = sorted(hs300_dict.keys(),reverse=True)
        # with open("hs_date_list.txt", 'a') as f:
        #     f.write('-------hs_date_list-----------'+str(hs_date_list)+"\r\n")
        # sql = "SELECT product_id FROM sf_return_drawdown WHERE  product_id =%s and `year_month`=%s limit 1"
        # for month in product_month:
        #     #月末的最后一条数据
        #     cursor.execute(sql, [product_id,month[0]])
        #     have_data = cursor.fetchone()
        #     if have_data is None:
        #         if (now_month != month[0]):
        #             # 月末的最后一条数据
        #             cursor.execute(end_sql, (month[0], product_id))
        #             end_month = cursor.fetchone()
        #
        #             # 沪深300这个月末的净值
        #             cursor.execute(hs_end_sql, [end_month[1]])
        #             hs_end_month = cursor.fetchone()
        #             # 月初的第一条数据
        #             cursor.execute(start_sql, [month[0], product_id])
        #             start_month = cursor.fetchone()
        #             # 沪深300这个月初的净值
        #             cursor.execute(hs_end_sql, [start_month[1]])
        #             hs_start_month = cursor.fetchone()
        #             # 如果是一个值往前推15天
        #             if (end_month[1] == start_month[1]):
        #                 yes_time = start_month[1] + datetime.timedelta(days=-15)
        #                 helf_month = yes_time.strftime('%Y-%m-%d')
        #                 sql = "SELECT product_id,nav_date,nav,added_nav,growth_rate FROM sf_nav WHERE  product_id =%s and  nav_date between  %s and %s ORDER BY nav_date DESC limit 1"
        #                 cursor.execute(sql, [product_id, helf_month, start_month[1]])
        #                 start_month = cursor.fetchone()
        #                 # 沪深300这个月初的净值
        #                 cursor.execute(hs_end_sql, [start_month[1]])
        #                 hs_start_month = cursor.fetchone()
        #             # 涨跌幅
        #             if(start_month[3] != 0 and start_month[3] is not None):
        #                 value = (end_month[3] - start_month[3]) / start_month[3]
        #                 value = '%.4f' % value
        #             else:
        #                 value = None
        #             # 沪深300
        #             hs300 = (hs_end_month[0] - hs_start_month[0]) / hs_start_month[0]
        #             hs300 = '%.4f' % hs300
        #             create_time = now_time
        #             update_time = now_time
        #             return_list = (str(product_id), 0, str(month[0]), str(end_month[2]), str(end_month[3]), str(value), str(hs300), str(create_time), str(update_time))
        #             sf_return_drawdown.append(return_list)
        # sql = 'insert into sf_return_drawdown(`product_id`,`type`,`year_month`,`nav`,`added_nav`,`value`,`hs300`,`create_time`,`update_time`) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        # if sf_return_drawdown is not None:
        #     try:
        #         cursor.executemany(sql, sf_return_drawdown)
        #         conn.commit()
        #         spider.spider_log.info('-----navpipelines insert sf_return_drawdown-----')
        #     except MySQLdb.Error, e:
        #         spider.spider_log.error('-----insert sf_return_drawdown fail-----:' + str(e) + ',insert sql' + sql + ',data：' + str(sf_return_drawdown))


class SfManagerPipeline(object):
    def process_item(self,item,spider):        
        if 'invest_year' in item:
            conn = spider.conn
            cursor = spider.cursor
            manager_dict = spider.manager_dict
            howbuy_manager_dict = spider.howbuy_manager_dict
            manager_name = item['manager_name']
            company_name = item['company_name']
            manager_company = item['manager_name']+'-'+item['company_name']
            howbuy_id = item['crawl_id']
            if manager_company not in manager_dict:
                #新经理，从未采集过
                sql = 'INSERT INTO sf_manager(name,company_id,company_name,profile,background,invest_year,manage_product_num,\
                        crawl_id,crawl_company_id,crawl_product_id,\
                        crawl_create_time, create_time, update_time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
                param = [item['manager_name'],item['company_id'],item['company_name'],item['profile'],item['background'],item['invest_year'], item['manage_product_num'], item['crawl_id'], item['crawl_company_id'],item['crawl_product_id'],item['now_time'], item['create_time'], item['update_time']]
                try:
                    cursor.execute(sql,param)
                    new_manager_id = cursor.lastrowid
                    conn.commit()
                    spider.howbuy_manager_dict[howbuy_id] = {
                        'id' : new_manager_id,
                        'name': manager_name,
                        'status': 0,
                        'howbuy_id': howbuy_id,
                        'howbuy_update_time': item['update_time'],
                        'company_name': company_name
                    }
                    spider.howbuy_manager_dict[manager_name+'-'+company_name] ={
                        'id' : new_manager_id,
                        'name': manager_name,
                        'status': 0,
                        'howbuy_id': howbuy_id,
                        'howbuy_update_time': item['update_time'],
                        'company_name': company_name
                    }
                    spider.spider_log.info('----update sf_manager success-----')
                except MySQLdb.Error, e:
                    # spider.spider_log.error('-----sql_error-----:' + str(e))
                    spider.spider_log.error('-----insert sf_return_drawdown fail-----:' + str(e) + ',insert sql' + sql + ',data：' + str(param))
            else:
                manager_info = manager_dict[manager_company]
                manager_id = manager_info['id']
                company_name = manager_info['company_name']
                sql = 'UPDATE sf_manager set profile=%s, background =%s, invest_year=%s, manage_product_num=%s,\
                    crawl_id=%s, crawl_company_id=%s, crawl_product_id=%s, crawl_update_time=%s, update_time = %s \
                    where id = %s and company_name = %s'
                param = [item['profile'],item['background'],item['invest_year'],
                                                          item['manage_product_num'], item['crawl_id'], item['crawl_company_id'],
                                                          item['crawl_product_id'],item['now_time'],item['update_time'],
                                                          manager_id,company_name]
                try:
                    #该经理已经存在，可能为手工录入，可能是第一次采集，故无匹配关系
                    cursor.execute(sql,param)
                    conn.commit()
                    spider.spider_log.info('-----update sf_manager success-----')
                    spider.howbuy_manager_dict[howbuy_id] = {
                        'id' : manager_id,
                        'name': manager_name,
                        'status': 0,
                        'howbuy_id': howbuy_id,
                        'howbuy_update_time': item['update_time'],
                        'company_name': company_name
                    }
                    spider.howbuy_manager_dict[manager_company] ={
                        'id' : manager_id,
                        'name': manager_name,
                        'status': 0,
                        'howbuy_id': howbuy_id,
                        'howbuy_update_time': item['update_time'],
                        'company_name': company_name
                    }
                except MySQLdb.Error, e:
                    spider.spider_log.error('-----update sf_manager fail-----:' + str(e) + ',insert sql' + sql + ',data：' + str(param))
        return item
class MonthPipeline(object):
    def process_item(self, item, spider):
        if 'month_return' in item:
            conn = spider.conn
            cursor = spider.cursor
            sql = 'insert into sf_return_drawdown(`product_id`,`type`,`year_month`,`nav`,`added_nav`,`value`,`hs300`,`create_time`,`update_time`) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            try:
                cursor.executemany(sql, item['month_return'])
                conn.commit()
                spider.spider_log.info('-----insert sf_return_drawdown success-----: ')
            # except MySQLdb.Error, e:
            #     spider.spider_log.info('插入失败的produt_id: ' + str(item['month_return']))
            except MySQLdb.Error, e:
                # spider.spider_log.error('-----sql_error-----:' + str(e))
                spider.spider_log.error('-----insert sf_return_drawdown fail-----:' + str(e) + ',insert sql' + sql + ',data：' + str(item['month_return']))
            pass
        return item
#沪深300
class HsPipeline(object):
    def process_item(self, item, spider):
        if 'hs_return' in item:
            conn = spider.conn
            cursor = spider.cursor
            sql = 'insert into sf_hs_index(`index_type`,`index_date`,`hs_index`,`growth_rate`,`total_growth_rate`,`create_time`,`update_time`) values(%s,%s,%s,%s,%s,%s,%s)'
            try:
                cursor.executemany(sql, item['hs_return'])
                conn.commit()
                spider.spider_log.warning('-----insert sf_hs_index success-----:')
            except MySQLdb.Error, e:
                spider.spider_log.error('-----insert sf_return_drawdown fail-----:' + str(e) + ',insert sql' + sql + ',data：' + str(item['hs_return']))
            pass
            spider.get_hs_dict()
        return item