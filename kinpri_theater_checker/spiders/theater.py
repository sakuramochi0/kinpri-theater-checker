# -*- coding: utf-8 -*-
import scrapy
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
            pref = tr.css('td:nth-child(1)::text').extract_first()
            name = tr.css('td:nth-child(2) a::text').extract_first()
            link = tr.css('td:nth-child(2) a::attr(href)').extract_first()
            start_date = tr.css('td:nth-child(3)::text').extract_first()
            preticket = tr.css('td:nth-child(4)::text').extract_first()
            live_viewing_20170610_0800 = tr.css('td:nth-child(5)::text').extract_first()
            live_viewing_20170610_1020 = tr.css('td:nth-child(6)::text').extract_first()

            # skip headers
            if pref == '都道府県':
                continue

            # construct theater object
            t['pref'] = pref
            t['name'] = name
            t['link'] = link
            t['start_date'] = start_date
            t['preticket'] = preticket
            t['live_viewing_20170610_0800'] = live_viewing_20170610_0800
            t['live_viewing_20170610_1020'] = live_viewing_20170610_1020
            yield t
