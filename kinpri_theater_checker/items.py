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


class Show(scrapy.Item):
    updated = scrapy.Field()
    theater = scrapy.Field()
    screen = scrapy.Field()
    title = scrapy.Field()
    date = scrapy.Field()
    start_time = scrapy.Field()
    end_time = scrapy.Field()
    ticket_state = scrapy.Field() # 0: ×, 1: △, 2: ○, 3: ◎
    remaining_seats_num = scrapy.Field()
    total_seats_num = scrapy.Field()
    reserved_seats = scrapy.Field()
    remaining_seats = scrapy.Field()
