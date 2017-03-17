#!/bin/bash

scrapy crawl simu 1> ./sfDataCrawl/runningLog/output/$(date +%Y-%m-%d_%H:%M:%S)_error.log 2>./sfDataCrawl/runningLog/output/$(date +%Y-%m-%d_%H:%M:%S)_info.log