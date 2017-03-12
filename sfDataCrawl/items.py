# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Item,Field

class SfdatacrawlItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class TestItem(scrapy.Item):
    name1 = Field()
    pass
class ProductItem(scrapy.Item):
    crawl_product_id = Field()
    crawl_product_name = Field()
    nav_date = Field()
    crawl_product_full_name = Field()
    start_date = Field()
    trustee_bank = Field()
    status = Field()
    product_type = Field()
    company_id = Field()
    company_name = Field()
    min_purchase_amount = Field()
    min_append_amount = Field()
    structured = Field()
    crawl_url = Field()
    crawl_company_id = Field()
    crawl_managers_id = Field()
    crawl_managers_name = Field()
    manager_list = Field()
    now_time = Field()
    locked_time = Field()
    open_date = Field()
    commission = Field()
    ransom_fee = Field()
    fixed_management_fee = Field()
    subscription_fee = Field()
    crawl_create_time = Field()
    dividend_date = Field()
    purchase_status = Field()
    pass

class CompanyItem(scrapy.Item):
    crawl_id = Field()
    rep_product_name = Field()
    crawl_update_time = Field()
    crawl_create_time = Field()
    crawl_url = Field()
    name = Field()
    full_name = Field()
    nick_initial = Field()
    core_manager_id = Field()
    core_manager_name = Field()
    rep_product = Field()
    website_addr = Field()
    icp = Field()
    establishment_date  = Field()
    registered_capital = Field()
    country = Field()
    province = Field()
    city = Field()
    region = Field()
    asset_mgmt_scale = Field()
    logo = Field()
    list_order = Field()
    appraise = Field()
    status = Field()
    product_count = Field()
    create_time = Field()
    update_time = Field()
    team = Field()
    investment_idea= Field()
    description= Field()
    short_profile = Field()
    pass
class CompanydataItem(scrapy.Item):
    team = Field()
    investment_idea= Field()
    description= Field()
    short_profile = Field()
    locked_time = Field()
    open_date = Field()
    commission = Field()
    ransom_fee = Field()
    fixed_management_fee = Field()
    subscription_fee = Field()
    crawl_create_time = Field()
    pass

class NavItem(scrapy.Item):
    nav_item_date = scrapy.Field()
    product_id = scrapy.Field()
    pass

class ManagerItem(scrapy.Item):
    name = Field()
    manager_name = Field()
    crawl_id = Field()
    company_id = Field()
    company_name = Field()
    profile = Field()
    background = Field()
    invest_year = Field()
    typical_product_id = Field()
    manage_product_num = Field()
    now_time = Field()
    create_time = Field()
    update_time = Field()
    crawl_company_id = Field()
    crawl_product_id = Field()
    pass

class MonthItem(scrapy.Item):
    month_return = Field()

class HsReturnItem(scrapy.Item):
    hs_return = Field()