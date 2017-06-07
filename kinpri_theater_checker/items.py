# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class KinpriTheaterCheckerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class Theater(scrapy.Item):
    last_updated = scrapy.Field()
    pref = scrapy.Field()
    name = scrapy.Field()
    link = scrapy.Field()
    start_date = scrapy.Field()
    preticket = scrapy.Field()
    live_viewing_20170610_0800 = scrapy.Field()
    live_viewing_20170610_1020 = scrapy.Field()
