# -*- coding: utf-8 -*-
import logging
from scrapy import signals
from scrapy.exceptions import NotConfigured
import json
import MySQLdb
from sfDataCrawl import settings
import math
import time

logger = logging.getLogger(__name__)

class DataSyncExtension(object):
    product_db_conn = ''
    product_db_cursor = ''
    def __init__(self, ):
        self.product_db_conn = ''
        self.product_db_cursor = ''
        self.conn = MySQLdb.connect(settings.MYSQL_HOST, settings.MYSQL_USER,
                                    settings.MYSQL_PWD,settings.MYSQL_DB, charset='utf8',use_unicode=True)
        self.cursor = self.conn.cursor()
    @classmethod
    def from_crawler(cls, crawler):
        # instantiate the extension object
        ext = cls()
        # connect the extension object to signals
        crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)

        # return the extension object
        return ext

    def spider_opened(self, spider):
        logger.info("open spider %s start", spider.name)
        if spider.name == 'simu':
            crawl_db_conn = spider.conn
            crawl_db_cursor = spider.cursor
            self.product_db_conn = MySQLdb.connect(settings.PRODUCT_MYSQL_HOST, settings.PRODUCT_MYSQL_USER,
                                                   settings.PRODUCT_MYSQL_PWD,settings.PRODUCT_MYSQL_DB,
                                                   charset='utf8',use_unicode=True)
            self.product_db_cursor = self.product_db_conn.cursor()
            # sync the data from product system to sf_crawl database
            if not settings.SKIP_IMPORTING:
                try:
                    self._import_company_data(self.product_db_cursor, crawl_db_conn, crawl_db_cursor)
                    print 'import _import_company_data data'
                    self._import_manager_data(self.product_db_cursor, crawl_db_conn, crawl_db_cursor)
                    print 'import _import_manager_data data'
                    self._import_product_data(self.product_db_conn, self.product_db_cursor, crawl_db_conn, crawl_db_cursor)
                    print 'import _import_product_data data'
                    self._import_manager_product_data(self.product_db_conn, self.product_db_cursor, crawl_db_conn, crawl_db_cursor)
                    print 'import _import_manager_product_data data'
                    self._import_hs_index(self.product_db_conn, self.product_db_cursor, crawl_db_conn, crawl_db_cursor)
                    print 'import _import_hs_index data'
                    self._import_product_nav(self.product_db_conn, self.product_db_cursor, crawl_db_conn, crawl_db_cursor)
                    print 'import _import_product_nav data'
                    self._import_dividend_split(self.product_db_conn, self.product_db_cursor, crawl_db_conn, crawl_db_cursor)
                    print 'import _import_dividend_split data'
                    self._import_return_drawdown(self.product_db_conn, self.product_db_cursor, crawl_db_conn, crawl_db_cursor)
                    print 'import _import_return_drawdown data'
                    self._import_statistics(self.product_db_conn, self.product_db_cursor, crawl_db_conn, crawl_db_cursor)
                    print 'import _import_statistics data'
                    pass
                except MySQLdb.Error,e:
                    spider.spider_log.info('import data Error' + str(e))
                    raise
                pass
            pass
        logger.info("open spider %s done", spider.name)

    def spider_closed(self, spider):
        logger.info("close spider %s start", spider.name)
        if spider.name == 'simu':
            crawl_db_conn = spider.conn
            crawl_db_cursor = spider.cursor
            self.product_db_conn = MySQLdb.connect(settings.PRODUCT_MYSQL_HOST, settings.PRODUCT_MYSQL_USER,
                                                   settings.PRODUCT_MYSQL_PWD,settings.PRODUCT_MYSQL_DB,
                                                   charset='utf8',use_unicode=True)
            self.product_db_cursor = self.product_db_conn.cursor()
            # sync the data from product system to sf_crawl database
            if not settings.SKIP_EXPORTING:
                try:
                    self.update_data(crawl_db_cursor,crawl_db_conn)
                    self._export_company_data(crawl_db_conn, crawl_db_cursor, self.product_db_conn,self.product_db_cursor)
                    print 'export company data'
                    self._export_manager_data(crawl_db_conn, crawl_db_cursor, self.product_db_conn,self.product_db_cursor)
                    print 'export manager data'
                    self._export_product_data(crawl_db_conn, crawl_db_cursor, self.product_db_conn, self.product_db_cursor)
                    print 'export product data'
                    self._export_manager_product_data(crawl_db_conn, crawl_db_cursor, self.product_db_conn, self.product_db_cursor)
                    print 'export manager product data'
                    self._export_hs_index(crawl_db_conn, crawl_db_cursor, self.product_db_conn, self.product_db_cursor)
                    print 'export _export_hs_index data'
                    self._export_product_nav(crawl_db_conn, crawl_db_cursor, self.product_db_conn, self.product_db_cursor)
                    print 'export _export_product_nav data'
                    self._export_dividend_split(crawl_db_conn, crawl_db_cursor, self.product_db_conn, self.product_db_cursor)
                    print 'export _export_dividend_split data'
                    self._export_return_drawdown(crawl_db_conn, crawl_db_cursor, self.product_db_conn, self.product_db_cursor)
                    print 'export _export_return_drawdown data'
                    self._export_statistics(crawl_db_conn, crawl_db_cursor, self.product_db_conn, self.product_db_cursor)
                    print 'export _export_statistics data'
                except MySQLdb.Error,e:
                    spider.spider_log.info('export data Error' + str(e))
                    #print self.product_db_cursor._last_executed
                pass
            pass
        logger.info("close spider %s done", spider.name)

    def item_scraped(self, item, spider):
        pass

    # 数据更新
    def update_data(self,cursor,conn):
        # 清理数据
        self._flush_data(cursor, conn)
        self._update_company_in_entity(cursor,conn)
        #update sf_manager_product table
        self._update_sfmanagerproduct()
        self._update_rep_product_in_company(cursor,conn)
        update_sql_list = list()
        # update field product_count in sf_company table
        update_sf_company_sql = 'UPDATE sf_company comT LEFT JOIN ( SELECT COUNT(*) AS proNum, company_id AS companyId FROM sf_product WHERE STATUS = 0 \
                                 GROUP BY company_id ) proT ON comT.id = proT.companyId SET comT.product_count = proT.proNum'
        #update field manage_product_num in sf_manager table
        update_sf_manager_sql = 'UPDATE sf_manager sfmanager LEFT JOIN (SELECT COUNT(1) AS repproductNum,manager_id AS managerId FROM  sf_manager_product GROUP BY manager_id)sfmp \
                                ON sfmanager.id =sfmp.managerId  SET sfmanager.manage_product_num  = sfmp.repproductNum'
        update_sql_list.append(update_sf_company_sql)
        update_sql_list.append(update_sf_manager_sql)
        #更新统计数据
        self._update_statistics_data(cursor,conn)
        try:
           for update_sql in update_sql_list:
                self.cursor.execute(update_sql)
           self.conn.commit()
        except MySQLdb.Error, e:
            print "ERROR"
        pass
    def _import_product_data(self, product_conn, product_cursor, crawl_conn, crawl_cursor):
        #获取crawl数据中最大的产品Id，将线上环境中大于该Id的insert进来，剩余更新进来
        product_items = ['id','name','full_name','start_date','end_date','init_nav','issuing_scale','trustee_bank',
                         'access_role','status','product_status','purchase_status','product_type','list_order',
                         'latest_nav','nav_date','added_nav','company_id','company_name','manager_list',
                         'return_recent_month1','return_recent_month3','return_recent_month6',
                         'return_recent_year1','return_recent_year2','return_recent_year3','return_recent_year4',
                         'return_recent_year5','return_year1','return_year2','return_year3','return_year4',
                         'return_year5','grade','nav_trustworthy','appraise','tag_type','min_purchase_amount',
                         'min_append_amount','structured','update_time','create_time']
        self._sync_entity_data(product_cursor, crawl_cursor, crawl_conn, 'sf_product', items=product_items)
        #upsert the companydata part
        product_data_items = ['id', 'description', 'orientation', 'investment_idea', 'investment_restriction',
                              'investment_target', 'investment_strategy','investment_range','asset_allocation',
                              'comparison_datum', 'remark', 'subscription_fee', 'fixed_management_fee', 'ransom_fee',
                              'commission', 'attachment_url', 'raise_ratio', 'rebate_type', 'rebate', 'account_number',
                              'account_name', 'account_bank', 'account_remark','expected_return', 'expected_return_desc',
                              'open_date', 'locked_time','locked_time_desc', 'duration', 'redemption_status',
                              'nav_data_freq', 'precautious_line','precautious_line_desc', 'stop_loss_line',
                              'stop_loss_line_desc', 'expected_guaranteed_return','risk_income_character',
                              'income_distribution','create_time', 'update_time']
        self._sync_entity_data(product_cursor, crawl_cursor, crawl_conn, 'sf_product_data', items=product_data_items)
    def _import_manager_data(self, product_cursor, crawl_conn, crawl_cursor):
        # 获取crawl数据中最大的经理Id，将线上环境中大于该Id的insert进来，剩余更新进来
        max_crawl_entity_id = ''
        max_crawl_update_time = ''
        max_product_entity_id = ''
        max_product_update_time = ''
        number_per_round = 1000
        insert_entities_list = list()
        insert_entities_data_list = list()
        max_crawl_sql = 'SELECT MAX(id) as maxId, MAX(update_time) as maxUpdateTime from sf_manager'
        max_crawl_info = self._get_max_info(crawl_cursor,max_crawl_sql)
        max_crawl_entity_id = max_crawl_info[0]
        max_crawl_update_time = max_crawl_info[1]
        max_product_sql = "SELECT MAX(id) as maxId, Max(update_time) as maxUpdateTime from sf_manager"
        product_max_info = self._get_max_info(product_cursor,max_product_sql)
        max_product_entity_id = product_max_info[0]
        max_product_update_time = product_max_info[1]
        if max_product_entity_id > max_crawl_entity_id:
            max_insert_sql = 'SELECT MAX(update_time) as maxUpdateTime from sf_manager WHERE id <= %s'
            max_insert_param = [max_crawl_entity_id]
            max_product_info = self._get_max_info(product_cursor, max_insert_sql,max_insert_param)
            max_product_update_time = max_product_info[0]
            page_sql = 'SELECT count(1) as toInsertNum from sf_manager where id > %s'
            page_param = [max_crawl_entity_id]
            insert_page = self._get_page_total_number(product_cursor, page_sql, page_param, number_per_round)
            for insert_index in range(0, insert_page):
                select_sql = 'SELECT id,name,name_en,nick_initial,sex,education,company_id, company_name, \
                profile, background, avatar, status, invest_year, list_order, appraise, typical_product_id, \
                manage_product_num, create_time, update_time FROM sf_manager WHERE id > %s ORDER BY id  LIMIT '+ \
                                 str(number_per_round) + ' OFFSET %s'
                select_param = [max_crawl_entity_id, insert_index * number_per_round]
                insert_sql = 'INSERT INTO sf_manager (id,name,name_en,nick_initial,sex,education,company_id, \
                  company_name,profile, background, avatar, status, invest_year, list_order, appraise, \
                  typical_product_id,manage_product_num, create_time, update_time) VALUES(%s,%s,%s,%s,%s,%s,%s,%s, \
                  %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
                #insert manager table data
                self._insert_data(product_cursor,crawl_cursor,crawl_conn,select_sql,select_param,insert_sql)
        if max_product_update_time > max_crawl_update_time :
            page_sql = 'SELECT COUNT(1) from sf_manager where update_time > %s'
            page_param = [max_crawl_update_time]
            total_page = self._get_page_total_number(product_cursor,page_sql,page_param,number_per_round)
            for update_index in range(0,total_page):
                select_sql = 'SELECT name,name_en,nick_initial,sex,education,company_id, company_name, \
                                profile, background, avatar, status, invest_year, list_order, appraise, typical_product_id, \
                                manage_product_num, create_time, update_time,id FROM sf_manager WHERE update_time > %s ORDER BY id  LIMIT '+ \
                                 str(number_per_round) + ' OFFSET %s'
                select_param = [max_crawl_update_time, update_index * number_per_round]

                update_sql = 'UPDATE sf_manager SET name = %s, name_en = %s, nick_initial = %s, sex = %s, education = %s,\
                          company_id = %s, company_name = %s, profile = %s, background = %s, avatar = %s, status = %s, \
                          invest_year = %s, list_order = %s, appraise = %s, typical_product_id = %s, manage_product_num = %s,\
                          create_time = %s, update_time = %s WHERE id = %s'
                self._update_data_by_id(product_cursor,crawl_cursor,crawl_conn,select_sql,select_param,update_sql)
                pass
            pass
        pass
    def _import_company_data(self, product_cursor, crawl_conn, crawl_cursor):
        #获取crawl数据中最大的公司Id，将线上环境中大于该Id的insert进来，剩余更新进来
        #暂时使用company和company_data分开处理两张表，为了代码书写方便。如果后期性能受到影响，合并读取
        max_crawl_company_id = ''
        max_crawl_update_time = ''
        max_product_company_id = ''
        max_product_update_time = ''
        insert_per_round = 1000
        inserted_line_number = 0
        max_sql = 'SELECT MAX(id) as maxId, MAX(update_time) as maxUpdateTime  FROM sf_company'
        max_info = self._get_max_info(crawl_cursor,max_sql)
        max_crawl_company_id = max_info[0]
        max_crawl_update_time = max_info[1]
        product_max_sql = 'SELECT MAX(id) as maxId, MAX(update_time) as maxUpdateTime  FROM sf_company'
        product_max_info = self._get_max_info(product_cursor, product_max_sql)
        max_product_company_id = product_max_info[0]
        max_product_update_time = product_max_info[1]
        if max_product_company_id > max_crawl_company_id :
            max_insert_sql = 'SELECT MAX(update_time) as maxUpdateTime from sf_company WHERE id <= %s'
            max_param = [max_crawl_company_id]
            max_insert_info = self._get_max_info(product_cursor, max_insert_sql, max_param)
            max_product_update_time = max_insert_info[0]
            product_cursor.execute('SELECT count(1)  FROM sf_company WHERE id > %s',[max_crawl_company_id])
            inserted_number_info = product_cursor.fetchall()
            for temp_info in inserted_number_info:
                inserted_line_number = temp_info[0]
            temp_page_number = (inserted_line_number)/insert_per_round
            if divmod(inserted_line_number, insert_per_round) > 0 :
                page_number = int(math.floor(temp_page_number) + 1)
            else:
                page_number = int(temp_page_number)
            for i in range(0,page_number):
                product_cursor.execute('SELECT id, name, full_name, nick_initial, core_manager_id, \
                                     core_manager_name, rep_product, website_addr, icp, \
                                     establishment_date, registered_capital, country, \
                                     province, city, asset_mgmt_scale, logo, list_order, \
                                     status, product_count, create_time, update_time from sf_company WHERE id > %s  ORDER BY \
                                     id  LIMIT '+ str(insert_per_round) + ' OFFSET %s', [max_crawl_company_id, i*insert_per_round]
                                       )
                companies = product_cursor.fetchall()
                inserted_company = list()
                for company in companies:
                    inserted_company.append(company)
                print 'import the sf_company data and page number is ' + str(i)
                try:
                    crawl_cursor.executemany('INSERT INTO sf_company (id, name, full_name, nick_initial, core_manager_id, \
                                             core_manager_name,rep_product, website_addr, icp, establishment_date, registered_capital, country, \
                                             province, city, asset_mgmt_scale, logo, list_order, status, product_count,  \
                                             create_time, update_time) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, %s,\
                                             %s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',inserted_company)
                    crawl_conn.commit()
                except Exception as exp:
                    print 'insert for sf_company in importing failed'
                    print exp
                product_cursor.execute('SELECT id, team, investment_idea, description, short_profile from sf_company_data \
                                  WHERE id > %s  ORDER BY id DESC LIMIT '+ str(insert_per_round) + ' OFFSET %s', [max_crawl_company_id, i * insert_per_round])
                companies_data = product_cursor.fetchall()
                inserted_company_data = list()
                for company in companies_data:
                    inserted_company_data.append(company)
                print 'import the sf_company_data data and page number is ' + str(i)
                try:
                    crawl_cursor.executemany('INSERT INTO sf_company_data (id, team, investment_idea, description, short_profile) \
                                    VALUES (%s,%s,%s,%s,%s)',inserted_company_data)
                    crawl_conn.commit()
                except Exception as exp:
                    print 'insert for sf_company_data in importing failed'
                    print exp
        if max_product_update_time > max_crawl_update_time:
            to_update_number = 0
            product_cursor.execute('SELECT COUNT(1) as toUpdateNum FROM sf_company WHERE update_time > %s',[max_crawl_update_time])
            to_update_info = product_cursor.fetchall()
            for update_line in to_update_info:
                to_update_number = update_line[0]
            if divmod(to_update_number,insert_per_round)[1] > 0:
                to_update_total_page = int(math.floor(to_update_number/insert_per_round) + 1)
            else:
                to_update_total_page = int(math.floor(to_update_number/insert_per_round))
            for update_index in range(0,to_update_total_page):
                product_cursor.execute('SELECT id, name, full_name, nick_initial, core_manager_id, \
                                     core_manager_name, rep_product, website_addr, icp, \
                                     establishment_date, registered_capital, country, \
                                     province, city, asset_mgmt_scale, logo, list_order, \
                                     status, product_count, create_time, update_time from sf_company WHERE update_time > %s  ORDER BY \
                                     id LIMIT '+ str(insert_per_round) + ' OFFSET %s', [max_crawl_update_time, update_index*insert_per_round]
                                       )
                update_companies = product_cursor.fetchall()
                updated_companies = list()
                for update_company in update_companies:
                    updated_companies.append(update_company)
                for company in updated_companies:
                    #for now update the info one by one
                    company_id = company[0]
                    company = company + (company_id,)
                    try:
                        crawl_cursor.execute('UPDATE sf_company SET name = %s, full_name = %s, nick_initial = %s,\
                                             core_manager_id = %s, core_manager_name = %s, rep_product = %s, website_addr = %s, icp = %s,\
                                             establishment_date = %s, registered_capital = %s, country = %s, \
                                             province = %s, city = %s, asset_mgmt_scale = %s, logo = %s, list_order = %s, \
                                             status = %s, product_count = %s, create_time = %s, update_time = %s WHERE id = %s',
                                             [company[1],company[2],company[3],company[4],company[5],company[6],company[7],
                                              company[8], company[9], company[10], company[11], company[12], company[13], company[14],
                                              company[15], company[16], company[17], company[18], company[19],company[20],company[0]
                                              ])
                        crawl_conn.commit()
                    except Exception as exp:
                        print 'update for sf_company in importing failed'
                        print exp
            pass
    def _import_manager_product_data(self, product_conn, product_cursor, crawl_conn, crawl_cursor):
        #use create_time to do the insert and update_time to do the update
        table_items = ['manager_id','product_id','begin_date','end_date','is_current','create_time','update_time']
        key_items = ['manager_id','product_id']
        self._sync_table_data(product_cursor,crawl_cursor,crawl_conn,'sf_manager_product',table_items,key_items)
        pass
    def _import_product_nav(self, product_conn, product_cursor, crawl_conn, crawl_cursor):
        #use create_time to do the insert and update_time to do the update
        table_items = ['product_id','nav_date','nav','added_nav','growth_rate','create_time','update_time']
        key_items = ['product_id','nav_date']
        self._sync_table_data(product_cursor,crawl_cursor,crawl_conn,'sf_nav',table_items,key_items)
        pass
    def _import_hs_index(self, product_conn, product_cursor, crawl_conn, crawl_cursor):
        # use create_time to do the insert and update_time to do the update
        table_items = ['index_type', 'index_date', 'hs_index', 'growth_rate', 'total_growth_rate', 'create_time', 'update_time']
        key_items = ['index_type', 'index_date']
        self._sync_table_data(product_cursor, crawl_cursor, crawl_conn, 'sf_hs_index', table_items, key_items)
        pass
    def _import_dividend_split(self, product_conn, product_cursor, crawl_conn, crawl_cursor):
        # use create_time to do the insert and update_time to do the update
        table_items = ['product_id', 'type', 'date', 'value', 'create_time', 'update_time']
        key_items = ['product_id', 'type','date']
        self._sync_table_data(product_cursor, crawl_cursor, crawl_conn, 'sf_dividend_split', table_items, key_items)
        pass
    def _import_return_drawdown(self, product_conn, product_cursor, crawl_conn, crawl_cursor):
        # use create_time to do the insert and update_time to do the update
        table_items = ['product_id', 'type', '`year_month`', 'nav', 'added_nav', 'value','hs300','create_time', 'update_time']
        key_items = ['product_id', 'type','`year_month`']
        self._sync_table_data(product_cursor, crawl_cursor, crawl_conn, 'sf_return_drawdown', table_items, key_items)
        pass
    def _import_statistics(self, product_conn, product_cursor, crawl_conn, crawl_cursor):
        # use create_time to do the insert and update_time to do the update
        table_items = ['product_id', 'time_type', 'type_average_net', 'four_bit_rank', 'hs300', 'annualized_wave',
                       'annualized_net','retrace','sharp','calmar','sortino','month_win','type_average_rank',
                       'create_time','update_time']
        key_items = ['product_id', 'time_type']
        self._sync_table_data(product_cursor, crawl_cursor, crawl_conn, 'sf_statistic', table_items, key_items)
        pass

    def _export_product_data(self,source_conn, source_curosr, target_conn, target_cursor):
        # 获取crawl数据中最大的产品Id，将线上环境中大于该Id的insert进来，剩余更新进来
        product_items = ['id', 'name', 'full_name', 'start_date', 'end_date', 'init_nav', 'issuing_scale',
                         'trustee_bank','access_role', 'status', 'product_status', 'purchase_status',
                         'product_type', 'list_order','latest_nav', 'nav_date', 'added_nav', 'company_id',
                         'company_name', 'manager_list','return_recent_month1', 'return_recent_month3',
                         'return_recent_month6','return_recent_year1', 'return_recent_year2', 'return_recent_year3',
                         'return_recent_year4','return_recent_year5', 'return_year1', 'return_year2',
                         'return_year3', 'return_year4','return_year5', 'grade', 'nav_trustworthy',
                         'appraise', 'tag_type', 'min_purchase_amount','min_append_amount', 'structured',
                         'update_time', 'create_time']
        self._sync_entity_data(source_cursor=source_curosr, target_cursor=target_cursor, target_conn=target_conn,
                            table_name='sf_product', items=product_items, restrictions=' company_id is not NULL ')
        # upsert the companydata part
        product_data_items = ['id', 'description', 'orientation', 'investment_idea', 'investment_restriction',
                              'investment_target', 'investment_strategy', 'investment_range', 'asset_allocation',
                              'comparison_datum', 'remark', 'subscription_fee', 'fixed_management_fee', 'ransom_fee',
                              'commission', 'attachment_url', 'raise_ratio', 'rebate_type', 'rebate', 'account_number',
                              'account_name', 'account_bank', 'account_remark', 'expected_return',
                              'expected_return_desc',
                              'open_date', 'locked_time', 'locked_time_desc', 'duration', 'redemption_status',
                              'nav_data_freq', 'precautious_line', 'precautious_line_desc', 'stop_loss_line',
                              'stop_loss_line_desc', 'expected_guaranteed_return', 'risk_income_character',
                              'income_distribution', 'create_time', 'update_time']
        self._sync_entity_data(source_cursor=source_curosr, target_cursor=target_cursor, target_conn=target_conn,
                            table_name='sf_product_data', items=product_data_items)
        pass
    def _export_manager_data(self,source_conn, source_curosr, target_conn, target_cursor):
        # 获取crawl数据中最大的经理Id，将线上环境中大于该Id的insert进来，剩余更新进来
        product_items = ['id', 'name', 'name_en', 'nick_initial', 'sex', 'education', 'company_id','company_name',
                         'profile', 'background', 'avatar', 'status', 'invest_year', 'list_order',
                         'appraise', 'typical_product_id', 'manage_product_num', 'create_time', 'update_time']
        self._sync_entity_data(source_cursor=source_curosr, target_cursor=target_cursor, target_conn=target_conn,
                            table_name='sf_manager', items=product_items, restrictions=' company_id is not NULL and company_name is not NULL ')
        pass
    def _export_company_data(self,source_conn, source_curosr, target_conn, target_cursor):
        # 获取crawl数据中最大的产品Id，将线上环境中大于该Id的insert进来，剩余更新进来
        product_items = ['id', 'name', 'full_name', 'nick_initial', 'core_manager_id', 'core_manager_name',
                         'rep_product','website_addr','icp', 'establishment_date', 'registered_capital',
                         'country', 'province', 'city','region', 'asset_mgmt_scale', 'logo', 'list_order',
                         'appraise', 'status','product_count', 'create_time', 'update_time']
        self._sync_entity_data(source_cursor=source_curosr, target_cursor=target_cursor, target_conn=target_conn,
                            table_name='sf_company', items=product_items, restrictions=' name is not NULL ')
        # upsert the companydata part
        product_data_items = ['id', 'team', 'investment_idea', 'description', 'short_profile', 'create_time', 'update_time']
        self._sync_entity_data(source_cursor=source_curosr, target_cursor=target_cursor, target_conn=target_conn,
                            table_name='sf_company_data', items=product_data_items)
        pass
    def _export_manager_product_data(self, source_conn, source_curosr, target_conn, target_cursor):
        # use create_time to do the insert and update_time to do the update
        table_items = ['manager_id', 'product_id', 'begin_date', 'end_date', 'is_current', 'create_time', 'update_time']
        key_items = ['manager_id', 'product_id']
        self._sync_table_data(source_curosr, target_cursor, target_conn, 'sf_manager_product', table_items, key_items)
        pass
    def _export_product_nav(self, source_conn, source_curosr, target_conn, target_cursor):
        # use create_time to do the insert and update_time to do the update
        table_items = ['product_id', 'nav_date', 'nav', 'added_nav', 'growth_rate', 'create_time', 'update_time']
        key_items = ['product_id', 'nav_date']
        self._sync_table_data(source_curosr, target_cursor, target_conn, 'sf_nav', table_items, key_items)
        pass
    def _export_hs_index(self, source_conn, source_curosr, target_conn, target_cursor):
        # use create_time to do the insert and update_time to do the update
        table_items = ['index_type', 'index_date', 'hs_index', 'growth_rate', 'total_growth_rate', 'create_time',
                       'update_time']
        key_items = ['index_type', 'index_date']
        self._sync_table_data(source_curosr, target_cursor, target_conn, 'sf_hs_index', table_items, key_items)
        pass
    def _export_dividend_split(self, source_conn, source_curosr, target_conn, target_cursor):
        # use create_time to do the insert and update_time to do the update
        table_items = ['product_id', 'type', 'date', 'value', 'create_time', 'update_time']
        key_items = ['product_id', 'type', 'date']
        self._sync_table_data(source_curosr, target_cursor, target_conn, 'sf_dividend_split', table_items, key_items)
        pass
    def _export_return_drawdown(self, source_conn, source_curosr, target_conn, target_cursor):
        # use create_time to do the insert and update_time to do the update
        table_items = ['product_id', 'type', '`year_month`', 'nav', 'added_nav', 'value', 'hs300', 'create_time',
                       'update_time']
        key_items = ['product_id', 'type', '`year_month`']
        self._sync_table_data(source_curosr, target_cursor, target_conn, 'sf_return_drawdown', table_items, key_items)
        pass
    def _export_statistics(self, source_conn, source_curosr, target_conn, target_cursor):
        # use create_time to do the insert and update_time to do the update
        table_items = ['product_id', 'time_type', 'type_average_net', 'four_bit_rank', 'hs300', 'annualized_wave',
                       'annualized_net', 'retrace', 'sharp', 'calmar', 'sortino', 'month_win', 'type_average_rank',
                       'create_time', 'update_time']
        key_items = ['product_id', 'time_type']
        self._sync_table_data(source_curosr, target_cursor, target_conn, 'sf_statistic', table_items, key_items)
        pass

    def _move_first_to_last_for_tuple(self,tuple_data):
        if len(tuple_data) < 2:
            return tuple_data
        list_data = list()
        first_element = ''
        for i in range(len(tuple_data)):
            if i == 0:
                first_element = tuple_data[i]
            else:
                list_data.append(tuple_data[i])
        list_data.append(first_element)
        return_tuple = tuple(list_data)
        return return_tuple
    def _insert_data(self,source_cursor, target_cursor, target_conn, select_sql, select_param,insert_sql):
        insert_entities_list = list()
        source_cursor.execute(select_sql,select_param)
        insert_entities = source_cursor.fetchall()
        for insert_entity in insert_entities:
            insert_entities_list.append(insert_entity)
        print 'insert data batch' + insert_sql
        target_cursor.executemany(insert_sql, insert_entities_list)
        target_conn.commit()
        pass
    def _update_data_by_id(self, source_cursor, target_cursor, target_conn, select_sql, select_param, update_sql):
        source_cursor.execute(select_sql,select_param)
        update_info = source_cursor.fetchall()
        print 'update data by id' + update_sql
        for update_line in update_info:
            # update_tuple = self._move_first_to_last_for_tuple(update_line)
            target_cursor.execute(update_sql,list(update_line))
        target_conn.commit()
    def _get_page_total_number(self,source_cursor,sql,param,round_number = 1000):
        if len(param) > 0:
            source_cursor.execute(sql,param)
        else:
            source_cursor.execute(sql)
        page_info = source_cursor.fetchall()
        for line in page_info:
            item_number = line[0]
        if divmod(item_number, round_number)[1] > 0:
            total_page_number = int(math.floor(divmod(item_number,round_number)[0]) + 1)
        else:
            total_page_number = int(math.floor(divmod(item_number, round_number)[0]))
        return total_page_number
    def _get_max_info(self,source_cursor,select_sql, select_param=None):
        if select_param is None:
            source_cursor.execute(select_sql)
        else:
            source_cursor.execute(select_sql,select_param)
        max_info = source_cursor.fetchall()
        for max_line in max_info:
            return max_line
    def _sync_entity_data(self,source_cursor,target_cursor,target_conn,table_name,items=[],restrictions=''):
        number_per_round = 1000
        insert_entities_list = list()
        insert_entities_data_list = list()
        max_target_sql = 'SELECT MAX(id) as maxId, MAX(update_time) as maxUpdateTime from ' + table_name
        max_target_info = self._get_max_info(target_cursor, max_target_sql)
        max_target_entity_id = max_target_info[0]
        max_target_update_time = max_target_info[1]
        max_source_sql = 'SELECT MAX(id) as maxId, Max(update_time) as maxUpdateTime from ' + table_name
        if len(restrictions) > 0:
            max_target_sql = max_target_sql + 'WHERE '+ restrictions
        source_max_info = self._get_max_info(source_cursor, max_source_sql)
        max_source_entity_id = source_max_info[0]
        max_source_update_time = source_max_info[1]
        print 'max_product_entity_id', max_source_entity_id, max_target_entity_id
        if max_source_entity_id > max_target_entity_id:
            print '_sync_entity_data', table_name
            max_insert_sql = 'SELECT MAX(update_time) as maxUpdateTime from ' + table_name + ' WHERE id <= %s'
            if len(restrictions) > 0:
                max_target_sql +=' AND ' + restrictions
            max_insert_param = [max_target_entity_id]
            max_source_info = self._get_max_info(source_cursor, max_insert_sql, max_insert_param)
            max_source_update_time = max_source_info[0]
            page_sql = 'SELECT count(1) as toInsertNum from ' + table_name + ' where id > %s'
            if len(restrictions) > 0:
                page_sql = page_sql + ' AND ' + restrictions
            page_param = [max_target_entity_id]
            insert_page = self._get_page_total_number(source_cursor, page_sql, page_param, number_per_round)
            print 'insert page for table' + str(table_name) + ' and page number is ' + str(insert_page)
            for insert_index in range(0, insert_page):
                select_sql = 'SELECT '
                i_counter = 0
                for item_name in items:
                    if i_counter != 0:
                        select_sql = select_sql + ',' + item_name
                    else:
                        select_sql = select_sql + item_name
                    i_counter += 1
                select_sql = select_sql + ' FROM ' + table_name + ' WHERE id > %s '
                if len(restrictions) > 0:
                    select_sql += ' AND ' + restrictions
                select_sql = select_sql + ' ORDER BY id LIMIT ' + str(number_per_round) + ' OFFSET %s'
                select_param = [max_target_entity_id, insert_index * number_per_round]
                insert_sql = 'INSERT INTO  ' + table_name + '  ('
                i_counter = 0
                for item_name in items:
                    if i_counter != 0:
                        insert_sql = insert_sql + ',' + item_name
                    else:
                        insert_sql = insert_sql + item_name
                    i_counter += 1
                insert_sql = insert_sql + ') VALUES('
                item_length = len(items);
                for i in range(0, item_length):
                    if i != 0:
                        insert_sql = insert_sql + ',%s'
                    else:
                        insert_sql = insert_sql + '%s'
                insert_sql = insert_sql + ')'
                # insert manager table data
                try:
                    self._insert_data(source_cursor, target_cursor, target_conn, select_sql, select_param, insert_sql)
                except Exception as exp:
                    print 'exception when sync the table' + str(table_name)
                    print exp
        if max_source_update_time is None or max_target_update_time is None or max_source_update_time > max_target_update_time:
            if max_target_update_time is not None:
                page_sql = 'SELECT COUNT(1) from  ' + table_name + '  where update_time > %s'
                if len(restrictions) > 0:
                    page_sql += ' AND ' + restrictions
                page_param = [max_target_update_time]
            else:
                page_sql = 'SELECT COUNT(1) from  ' + table_name
                if len(restrictions) > 0:
                    page_sql += ' WHERE ' + restrictions
                page_param = []
            total_page = self._get_page_total_number(source_cursor, page_sql, page_param, number_per_round)
            for update_index in range(0, total_page):
                select_sql = 'SELECT '
                item_index = 0
                for item_name in items:
                    if item_index != 0 :
                        if item_index == 1:
                            select_sql += item_name
                        else:
                            select_sql += ',' + item_name
                    item_index += 1
                if max_target_update_time is  not None:
                    select_sql = select_sql + ',' + items[0] + ' FROM  ' + table_name + ' WHERE update_time > %s '
                    if len(restrictions) > 0:
                        select_sql += ' AND ' + restrictions
                    select_sql += ' ORDER BY id LIMIT '+ str(number_per_round) + ' OFFSET %s'
                    select_param = [max_target_update_time, update_index * number_per_round]
                else:
                    select_sql = select_sql + ',' + items[
                        0] + ' FROM  ' + table_name
                    if len(restrictions) > 0:
                        select_sql += ' WHERE ' + restrictions
                    select_sql += ' ORDER BY id LIMIT ' + str(number_per_round) + ' OFFSET %s'
                    select_param = [update_index * number_per_round]
                update_sql = 'UPDATE ' + table_name + ' SET '
                for i in range(0, len(items)):
                    if i > 0 :
                        if i != 1:
                            update_sql += ',' + items[i] + ' = %s'
                        else:
                            update_sql += items[i] + '=%s'
                update_sql += ' WHERE '+ items[0] + ' =%s'
                try:
                    self._update_data_by_id(source_cursor, target_cursor, target_conn, select_sql, select_param, update_sql)
                except Exception as exp:
                    print 'exception when sync the table' + str(table_name)
                    print 'update sql ' + update_sql
                    print exp
                pass
            pass
        pass

    #更新sf_manager_product
    def _update_sfmanagerproduct(self):
        #sf_manager表中根据create_time取managers
        crawl_managers_sql = 'SELECT id,crawl_id,name FROM sf_manager WHERE create_time > date_sub(curdate(),interval 1 day)'
        self.cursor.execute(crawl_managers_sql)
        crawl_managers = self.cursor.fetchall()
        for manager in crawl_managers:
            sfmanager_id = manager[0]
            sfmanager_crawl_id = manager[1]
            sfmanager_name = manager[2]
            crawl_manager_list_string = sfmanager_crawl_id+','+sfmanager_name+';'
            crawl_products_sql = 'SELECT id,manager_list,start_date,end_date  FROM sf_product WHERE crawl_managers_list LIKE "%'+crawl_manager_list_string+'%"'
            self.cursor.execute(crawl_products_sql)
            sfproducts = self.cursor.fetchall()
            for sfproduct in sfproducts:
                sfproduct_id = sfproduct[0]
                sfproduct_managerlist = sfproduct[1]
                sfproduct_start_date = sfproduct[2]
                sfproduct_end_date = sfproduct[3]
                if sfproduct_start_date == '':
                    #因为sf_manager_product中的begin_date是不能为空值的，下面要向sf_manager_product中插入新的产品，用到此字段
                    sfproduct_start_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                new_managerlist_string = str(sfmanager_id) + ',' + sfmanager_name + ';'
                if new_managerlist_string not in sfproduct_managerlist:
                    if sfproduct_managerlist != ';':
                        if crawl_manager_list_string in sfproduct_managerlist:
                            new_managerlist_string = sfproduct_managerlist.replace(crawl_manager_list_string,new_managerlist_string)
                        else:
                            new_managerlist_string = sfproduct_managerlist + new_managerlist_string

                    update_sfproduct_managerlist_sql = 'UPDATE sf_product SET manager_list = %s WHERE id= %s'
                    self.cursor.execute(update_sfproduct_managerlist_sql,[new_managerlist_string,sfproduct_id])
                    self.conn.commit()

                create_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                update_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                is_newproduct_exist_sql = 'SELECT * FROM sf_manager_product WHERE manager_id = %s AND product_id = %s AND begin_date = %s'
                self.cursor.execute(is_newproduct_exist_sql,[sfmanager_id, sfproduct_id, sfproduct_start_date])
                queryResult = self.cursor.fetchone()
                if queryResult is None:
                    insert_newproduct_sql = 'INSERT INTO sf_manager_product(manager_id,product_id,is_current,begin_date,end_date,create_time,update_time)\
                                              VALUES(%s,%s,1,%s,%s,%s,%s)'
                    self.cursor.execute(insert_newproduct_sql,[sfmanager_id,sfproduct_id,sfproduct_start_date,sfproduct_end_date,create_time,update_time])
                    self.conn.commit()
            pass
    #跟新表中的company_id 和company_name
    def _update_company_in_entity(self,cursor,conn):
        update_manager_sql = 'UPDATE sf_manager managerT LEFT JOIN sf_company companyT \
            ON managerT.crawl_company_id = companyT.crawl_id \
            SET managerT.company_id = companyT.id, managerT.company_name = companyT.name \
            WHERE managerT.company_id is NULL'
        cursor.execute(update_manager_sql)
        conn.commit()
        update_product_sql = 'UPDATE sf_product productT LEFT JOIN sf_company companyT \
        ON productT.crawl_company_id = companyT.crawl_id \
        SET productT.company_id = companyT.id, productT.company_name = companyT.name \
        WHERE productT.company_id is NULL'
        cursor.execute(update_product_sql)
        conn.commit()

    def _update_rep_product_in_company(self,cursor,conn):
        # update sf_company rep_product
        update_rep_product_sql = 'UPDATE sf_company comT LEFT JOIN sf_product proT ON comT.rep_product_name = proT.name \
                             SET rep_product = proT.id WHERE proT.status = 0 and comT.rep_product is NULL '
        cursor.execute(update_rep_product_sql)
        conn.commit()
    def _update_statistics_data(self,cursor,conn):
        for time_type in range(1,16):
            # calculation 1: calculate type_average_net
            avgNet_info_sql = 'SELECT productT.product_type,AVG(annualized_net) AS avgNet,time_type FROM `sf_statistic` statisticT INNER JOIN sf_product productT ON \
                            productT.id = statisticT.product_id  WHERE productT.`status` =0 AND statisticT.time_type = %s GROUP BY productT.product_type'
            cursor.execute(avgNet_info_sql,[time_type])
            avg_info = cursor.fetchall()
            for info in avg_info:
                if info[1] is not None:
                    type_average_net = round(float(info[1]),4)
                else:
                    type_average_net = None
                update_type_avg_sql = 'UPDATE sf_statistic staT INNER JOIN sf_product proT ON staT.product_id = proT.id SET staT.type_average_net = %s WHERE proT.`status`=0 AND proT.product_type =%s and staT.time_type = %s '
                cursor.execute(update_type_avg_sql,[type_average_net,info[0],time_type])
                conn.commit()

            # calculation 2: calculate type_average_rank
            products_same_type_sql = 'SELECT product_type AS pTypes,count(1) AS pSum  FROM `sf_product` where `status`=0 GROUP BY product_type ORDER BY product_type ; '
            cursor.execute(products_same_type_sql)
            productsInfo = cursor.fetchall()
            for pInfo in productsInfo:
                pType = pInfo[0]
                pSum = pInfo[1]
                update_average_rank_sql = 'UPDATE sf_statistic s1 RIGHT JOIN (SELECT product_id, time_type, annualized_net, NAME, \
                          @ranknum := @ranknum + 1 AS rank FROM (SELECT @ranknum :=0) tempT, (SELECT staT.product_id, staT.time_type \
                          FROM sf_statistic staT LEFT JOIN sf_product proT ON staT.product_id = proT.id WHERE proT.status = 0  \
                          AND proT.product_type = %s AND staT.time_type = %s ORDER BY staT.annualized_net DESC) t1) t2 \
                          ON s1.`product_id` = t2.product_id AND s1.`time_type` = s2.time_type \
                          SET type_average_rank = CONCAT(t2.rank, "/%s") '
                cursor.execute(update_average_rank_sql,[pType,time_type,pSum])
                conn.commit()

            #calculation3: calculate four_bit_rank
            sfproduct_net_statistics_sql = 'SELECT  maxNet,minNet,(maxNet-minNet) AS minusNet FROM(SELECT max(statisticT.annualized_net) AS maxNet,' \
                       'min(statisticT.annualized_net) AS minNet FROM `sf_product` productT LEFT JOIN sf_statistic statisticT ON statisticT.product_id = productT.id' \
                       ' WHERE statisticT.time_type =%s AND productT.status =0 )Temp '
            cursor.execute(sfproduct_net_statistics_sql, [time_type])
            sfproduct_net_info = cursor.fetchall()
            # 四分卫各节点
            if sfproduct_net_info is not None:
                # minNet~ onefourth; onefourth~twofourths ;twofourths~threefourths ; threefourths~maxNet
                maxNet = sfproduct_net_info[0]
                minNet = sfproduct_net_info[1]
                minusNet = sfproduct_net_info[2]
                onefourth = minNet + minusNet / 4  # 四分之一节点
                twofourths = minNet + minusNet / 2
                threefourths = minNet + 3 * minusNet / 4
                update_fourbitrank_statistic_sql1 = ' UPDATE sf_statistic SET four_bit_rank = "1.0000"	WHERE  time_type=%s AND annualized_net is not NULL AND annualized_net <%s '
                cursor.execute(update_fourbitrank_statistic_sql1, [time_type, onefourth])
                update_fourbitrank_statistic_sql2 = ' UPDATE sf_statistic SET four_bit_rank = "2.0000"	WHERE  time_type=%s AND annualized_net is not NULL AND annualized_net>%s AND annualized_net <=%s '
                cursor.execute(update_fourbitrank_statistic_sql2, [time_type, onefourth, twofourths])
                update_fourbitrank_statistic_sql3 = ' UPDATE sf_statistic SET four_bit_rank = "3.0000"	WHERE  time_type=%s AND annualized_net is not NULL AND  annualized_net>%s AND annualized_net <=%s '
                cursor.execute(update_fourbitrank_statistic_sql3, [time_type, twofourths, threefourths])
                update_fourbitrank_statistic_sql4 = ' UPDATE sf_statistic SET four_bit_rank = "4.0000"	WHERE  time_type=%s AND annualized_net is not NULL AND annualized_net>%s AND annualized_net <=%s '
                cursor.execute(update_fourbitrank_statistic_sql4, [time_type, threefourths, maxNet])
                conn.commit()

        pass

    def _sync_table_data(self,source_cursor,target_cursor,target_conn,table_name,items=[], key_items=[]):
        #use create_time to insert and update_time to update items
        number_per_round = 1000
        insert_entities_list = list()
        insert_entities_data_list = list()
        max_target_sql = 'SELECT MAX(create_time) as maxCreateTime,MAX(update_time) as maxUpdateTime from ' + table_name
        max_target_info = self._get_max_info(target_cursor, max_target_sql)
        max_target_create_time = max_target_info[0]
        max_target_update_time =  max_target_info[1]
        max_source_sql = 'SELECT MAX(create_time) as maxCreateTime,MAX(update_time) as maxUpdateTime from ' + table_name
        source_max_info = self._get_max_info(source_cursor, max_source_sql)
        max_source_create_time = source_max_info[0]
        max_source_update_time = source_max_info[1]
        if max_target_create_time is None or max_source_create_time is None or max_source_create_time > max_target_create_time:
            print '_sync_table_data', table_name
            if max_target_create_time is not None:
                max_insert_sql = 'SELECT MAX(update_time) as maxUpdateTime from ' + table_name + ' WHERE create_time <= %s'
                max_insert_param = [max_target_create_time]
            else:
                max_insert_sql = 'SELECT MAX(update_time) as maxUpdateTime from ' + table_name
                max_insert_param = []
            max_source_info = self._get_max_info(source_cursor, max_insert_sql, max_insert_param)
            max_source_update_time = max_source_info[0]
            if max_target_create_time is not None:
                page_sql = 'SELECT count(1) as toInsertNum from ' + table_name + ' where create_time > %s'
                page_param = [max_target_create_time]
            else:
                page_sql = 'SELECT count(1) as toInsertNum from ' + table_name
                page_param = []
            print 'insert page', page_sql, max_target_create_time
            insert_page = self._get_page_total_number(source_cursor, page_sql, page_param, number_per_round)
            print 'insert page',insert_page
            for insert_index in range(0, insert_page):
                select_sql = 'SELECT '
                i_counter = 0
                for item_name in items:
                    if i_counter != 0:
                        select_sql = select_sql + ',' + item_name
                    else:
                        select_sql = select_sql + item_name
                    i_counter += 1
                order_key = ''
                i_counter = 0
                for item_name in items:
                    if i_counter != 0:
                        order_key += ',' + item_name
                    else:
                        order_key += item_name
                    i_counter += 1
                if max_target_create_time is not None:
                    select_sql = select_sql + ' FROM ' + table_name + ' WHERE create_time > %s ORDER BY ' +  \
                                 order_key+' LIMIT '+ str(number_per_round) +' OFFSET %s'
                    select_param = [max_target_create_time, insert_index * number_per_round]
                else:
                    select_sql = select_sql + ' FROM ' + table_name + ' ORDER BY '+order_key + ' LIMIT '+ \
                                 str(number_per_round) + ' OFFSET %s'
                    select_param = [insert_index * number_per_round]
                insert_sql = 'INSERT INTO  ' + table_name + '  ('
                i_counter = 0
                for item_name in items:
                    if i_counter != 0:
                        insert_sql = insert_sql + ',' + item_name
                    else:
                        insert_sql = insert_sql + item_name
                    i_counter += 1
                insert_sql = insert_sql + ') VALUES('
                item_length = len(items);
                for i in range(0, item_length):
                    if i != 0:
                        insert_sql = insert_sql + ',%s'
                    else:
                        insert_sql = insert_sql + '%s'
                insert_sql = insert_sql + ')'
                # insert manager table data
                print '_sync_table_data', table_name,insert_sql
                try:
                    self._insert_data(source_cursor, target_cursor, target_conn, select_sql, select_param, insert_sql)
                except Exception as exp:
                    print 'exception when sync the table' + str(table_name)
                    print exp
        if max_target_update_time is not None and max_source_update_time > max_target_update_time:
            if max_target_update_time is not None:
                page_sql = 'SELECT COUNT(1) from  ' + table_name + '  where update_time > %s'
                page_param = [max_target_update_time]
            else:
                page_sql = 'SELECT COUNT(1) from  ' + table_name
                page_param = []
            total_page = self._get_page_total_number(source_cursor, page_sql, page_param, number_per_round)
            item_key_dic = {}
            for item_key in key_items:
                item_key_dic[item_key] = 1
            for update_index in range(0, total_page):
                item_index = 0
                select_sql = 'SELECT '
                for item_name in items:
                    if item_name not in item_key_dic:
                        if item_index == 0:
                            select_sql += item_name
                        else:
                            select_sql += ',' + item_name
                        item_index += 1
                for item_key in key_items:
                    select_sql += ',' + item_key
                if max_target_update_time is None:
                    select_sql = select_sql + ' FROM  ' + table_name + ' WHERE update_time > %s ORDER BY update_time LIMIT '+ \
                                 str(number_per_round) + ' OFFSET %s'
                    select_param = [max_target_update_time, update_index * number_per_round]
                else:
                    select_sql = select_sql + ' FROM  ' + table_name + ' ORDER BY update_time LIMIT '+ \
                                 str(number_per_round) + ' OFFSET %s'
                    select_param = [update_index * number_per_round]
                update_sql = 'UPDATE ' + table_name + ' SET '
                item_index = 0
                for i in range(0, len(items)):
                    item_name =items[i]
                    if item_name not in item_key_dic:
                        if item_index != 0:
                            update_sql += ',' + items[i] + ' = %s'
                        else:
                            update_sql += items[i] + '=%s'
                        item_index += 1
                update_sql += ' WHERE '
                item_index = 0
                update_param = []
                for item_key in key_items:
                    if item_index == 0:
                        update_sql += item_key + ' =%s'
                    else:
                        update_sql += ' AND ' + item_key + ' =%s'
                    update_param.append(item_key)
                    item_index += 1
                try:
                    self._update_data_by_id(source_cursor, target_cursor, target_conn, select_sql, select_param, update_sql)
                except Exception as exp:
                    print 'exception when sync the table' + str(table_name)
                    print 'update sql ' + update_sql
                    print exp
                pass
            pass

    # 数据清理
    def _flush_data(self, cursor, conn):
        # flush sf_product table
        flush_sfproduct_sql = 'DELETE FROM sf_product WHERE company_id is NULL'
        cursor.execute(flush_sfproduct_sql)
        conn.commit()
        # flush sf_manager table
        flush_sfmanager_sql = 'DELETE FROM sf_manager WHERE company_id is NULL'
        cursor.execute(flush_sfmanager_sql)
        conn.commit()
        pass

