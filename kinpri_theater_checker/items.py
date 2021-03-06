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
    start_date_4dx = scrapy.Field()
    has_4dx = scrapy.Field()


class Show(scrapy.Item):
    updated = scrapy.Field()
    title = scrapy.Field()
    show_types = scrapy.Field()
    movie_types = scrapy.Field()
    date = scrapy.Field()
    theater = scrapy.Field()
    screen = scrapy.Field()
    start_time = scrapy.Field()
    end_time = scrapy.Field()
    ticket_state = scrapy.Field() # 0: ×, 1: △, 2: ○, 3: ◎
    remaining_seats_num = scrapy.Field()
    total_seats_num = scrapy.Field()
    reserved_seats = scrapy.Field()
    remaining_seats = scrapy.Field()
    schedule_url = scrapy.Field()
    reservation_url = scrapy.Field()
