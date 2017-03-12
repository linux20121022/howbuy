ALTER TABLE `zgcf`.`sf_company_data` ADD COLUMN `update_time` DATETIME NULL COMMENT '更新时间' AFTER `short_profile`, ADD COLUMN `create_time` DATETIME NULL COMMENT '创建时间' AFTER `update_time`;

ALTER TABLE `sf_crawl`.`sf_product` CHANGE `company_id` `company_id` INT(11) NULL COMMENT '发行机构ID';
ALTER TABLE `sf_crawl`.`sf_company` ADD COLUMN `crawl_update_time` DATETIME NULL COMMENT '抓取内容更新时间' AFTER `update_time`, ADD COLUMN `crawl_id` VARCHAR(50) NULL COMMENT '抓取方公司的id' AFTER `crawl_update_time`, ADD COLUMN `crawl_url` VARCHAR(200) NULL COMMENT '抓取的url' AFTER `crawl_id`, ADD COLUMN `crawl_create_time` DATETIME NULL COMMENT '抓取内容创建时间' AFTER `crawl_url`;
ALTER TABLE `sf_crawl`.`sf_company` ADD COLUMN `rep_product_name` VARCHAR(50) NULL COMMENT '代表产品名称' AFTER `update_time`
ALTER TABLE `sf_crawl`.`sf_company_data` ADD COLUMN `update_time` DATETIME NULL COMMENT '更新时间' AFTER `short_profile`, ADD COLUMN `create_time` DATETIME NULL COMMENT '创建时间' AFTER `update_time`;

ALTER TABLE `sf_crawl`.`sf_manager` ADD COLUMN `crawl_id` VARCHAR(50) NULL COMMENT '抓取方经理ID' AFTER `update_time`, ADD COLUMN `crawl_company_id` VARCHAR(50) NULL COMMENT '抓取经理所属的公司id' AFTER `crawl_id`, ADD COLUMN `crawl_product_id` VARCHAR(50) NULL COMMENT '抓取产品id' AFTER `crawl_company_id`, ADD COLUMN `crawl_update_time` DATETIME NULL COMMENT '抓取更新时间' AFTER `crawl_product_id`, ADD COLUMN `crawl_create_time` DATETIME NULL COMMENT '抓取创建时间' AFTER `crawl_update_time`;

ALTER TABLE `sf_crawl`.`sf_nav` ADD COLUMN `crawl_url` VARCHAR(200) NULL COMMENT '抓取净值URL' AFTER `update_time`, ADD COLUMN `crawl_time` DATETIME NULL COMMENT '抓取净值时间' AFTER `crawl_url`, ADD COLUMN `crawl_id` VARCHAR(20) NULL COMMENT '抓取的id' AFTER `crawl_time`;


ALTER TABLE `sf_crawl`.`sf_product` ADD COLUMN `crawl_id` VARCHAR(50) NULL COMMENT '抓取方Id' AFTER `create_time`, ADD COLUMN `crawl_url` VARCHAR(200) NULL COMMENT '抓取方url' AFTER `crawl_id`, ADD COLUMN `crawl_company_id` VARCHAR(50) NULL COMMENT '抓取方公司Id' AFTER `crawl_url`, ADD COLUMN `crawl_managers_list` VARCHAR(100) NULL COMMENT '抓取方基金经理信息(格式: id,name;id,name;.....)' AFTER `crawl_company_id`, ADD COLUMN `crawl_create_time` DATETIME NULL COMMENT '抓去创建时间' AFTER `crawl_managers_list`, ADD COLUMN `crawl_update_time` DATETIME NULL COMMENT '抓去更新时间' AFTER `crawl_create_time`;

ALTER TABLE `sf_crawl`.`sf_product_data` ADD COLUMN `crawl_id` VARCHAR(50) NULL COMMENT '抓取方ID' AFTER `update_time`, ADD COLUMN `crawl_create_time` DATETIME NULL COMMENT '抓取创建时间' AFTER `crawl_id`, ADD COLUMN `crawl_update_time` DATETIME NULL COMMENT '抓取更新时间' AFTER `crawl_create_time`;
;
ALTER TABLE `sf_crawl`.`sf_dividend_split` CHANGE `value` `value` DECIMAL(15,4) NULL COMMENT '拆分比例/分红额';


ALTER TABLE `sf_crawl`.`sf_dividend_split` DROP FOREIGN KEY `sfDividend_product`;
ALTER TABLE `sf_crawl`.`sf_dividend_split` ADD CONSTRAINT `sfDividend_product` FOREIGN KEY (`product_id`) REFERENCES `sf_crawl`.`sf_product`(`id`) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE `sf_crawl`.`sf_manager` DROP FOREIGN KEY `sfManager_company`;
ALTER TABLE `sf_crawl`.`sf_manager` ADD CONSTRAINT `sfManager_company` FOREIGN KEY (`company_id`) REFERENCES `sf_crawl`.`sf_company`(`id`) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE `sf_crawl`.`sf_manager_product` DROP FOREIGN KEY `sfManager_product`;
ALTER TABLE `sf_crawl`.`sf_manager_product` ADD CONSTRAINT `sfManager_product` FOREIGN KEY (`manager_id`) REFERENCES `sf_crawl`.`sf_manager`(`id`) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE `sf_crawl`.`sf_manager_product` DROP FOREIGN KEY `sfProduct_manager`;
ALTER TABLE `sf_crawl`.`sf_manager_product` ADD CONSTRAINT `sfProduct_manager` FOREIGN KEY (`product_id`) REFERENCES `sf_crawl`.`sf_product`(`id`) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE `sf_crawl`.`sf_nav` DROP FOREIGN KEY `sfNav_product`;
ALTER TABLE `sf_crawl`.`sf_nav` ADD CONSTRAINT `sfNav_product` FOREIGN KEY (`product_id`) REFERENCES `sf_crawl`.`sf_product`(`id`) ON UPDATE CASCADE ON DELETE CASCADE;
ALTER TABLE `sf_crawl`.`sf_return_drawdown` DROP FOREIGN KEY `sfReturn_product`;
ALTER TABLE `sf_crawl`.`sf_return_drawdown` ADD CONSTRAINT `sfReturn_product` FOREIGN KEY (`product_id`) REFERENCES `sf_crawl`.`sf_product`(`id`) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE `sf_crawl`.`sf_statistic` DROP FOREIGN KEY `sfStatistic_product`;
ALTER TABLE `sf_crawl`.`sf_statistic` ADD CONSTRAINT `sfStatistic_product` FOREIGN KEY (`product_id`) REFERENCES `sf_crawl`.`sf_product`(`id`) ON UPDATE CASCADE ON DELETE CASCADE;

UPDATE sf_company SET update_time = '2017-03-01 12:00:00' WHERE update_time IS NULL;
UPDATE sf_company SET create_time = '2017-03-01 12:00:00' WHERE create_time IS NULL;
UPDATE sf_company_data SET update_time = '2017-03-01 12:00:00' WHERE update_time IS NULL;
UPDATE sf_company_data SET create_time = '2017-03-01 12:00:00' WHERE create_time IS NULL;

UPDATE sf_product SET update_time = '2017-03-01 12:00:00' WHERE update_time IS NULL;
UPDATE sf_product SET create_time = '2017-03-01 12:00:00' WHERE create_time IS NULL;
UPDATE sf_product_data SET update_time = '2017-03-01 12:00:00' WHERE update_time IS NULL;
UPDATE sf_product_data SET create_time = '2017-03-01 12:00:00' WHERE create_time IS NULL;

UPDATE sf_manager SET update_time = '2017-03-01 12:00:00' WHERE update_time IS NULL;
UPDATE sf_manager SET create_time = '2017-03-01 12:00:00' WHERE create_time IS NULL;

UPDATE sf_manager_product SET update_time = '2017-03-01 12:00:00' WHERE update_time IS NULL;
UPDATE sf_manager_product SET create_time = '2017-03-01 12:00:00' WHERE create_time IS NULL;

UPDATE sf_dividend_split SET update_time = '2017-03-01 12:00:00' WHERE update_time IS NULL;
UPDATE sf_dividend_split SET create_time = '2017-03-01 12:00:00' WHERE create_time IS NULL;

UPDATE sf_hs_index SET update_time = '2017-03-01 12:00:00' WHERE update_time IS NULL;
UPDATE sf_hs_index SET create_time = '2017-03-01 12:00:00' WHERE create_time IS NULL;

UPDATE sf_nav SET update_time = '2017-03-01 12:00:00' WHERE update_time IS NULL;
UPDATE sf_nav SET create_time = '2017-03-01 12:00:00' WHERE create_time IS NULL;
UPDATE sf_return_drawdown SET update_time = '2017-03-01 12:00:00' WHERE update_time IS NULL;
UPDATE sf_return_drawdown SET create_time = '2017-03-01 12:00:00' WHERE create_time IS NULL;

UPDATE sf_statistic SET update_time = '2017-03-01 12:00:00' WHERE update_time IS NULL;
UPDATE sf_statistic SET create_time = '2017-03-01 12:00:00' WHERE create_time IS NULL;
