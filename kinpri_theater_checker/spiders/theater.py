# -*- coding: utf-8 -*-
import scrapy
import datetime
from kinpri_theater_checker.items import Theater


class TheaterSpider(scrapy.Spider):
    name = "theater"
    custom_settings = {
        'ITEM_PIPELINES': {
            'kinpri_theater_checker.pipelines.TheaterPipeline': 300,
        }
    }
    allowed_domains = ["http://kinpri.com/theater"]
    start_urls = ['http://kinpri.com/theater/']

    def parse(self, response):
        trs = response.css('.area_box tr')
        for tr in trs:
            t = Theater()
            t['last_updated'] = datetime.datetime.now()
            pref = tr.css('td:nth-child(1)::text').extract_first()
            # skip headers
            if pref == '都道府県':
                continue
            t['pref'] = pref
            t['name'] = tr.css('td:nth-child(2) a::text').extract_first()
            t['link'] = tr.css('td:nth-child(2) a::attr(href)').extract_first()
            t['start_date'] = tr.css('td:nth-child(3)::text').extract_first()
            yield t
