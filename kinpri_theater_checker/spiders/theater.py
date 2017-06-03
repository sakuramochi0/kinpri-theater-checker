# -*- coding: utf-8 -*-
import scrapy


class TheaterSpider(scrapy.Spider):
    name = "theater"
    allowed_domains = ["http://kinpri.com/theater"]
    start_urls = ['http://kinpri.com/theater/']

    def parse(self, response):
        theaters = response.css('.area_box tr')
        for t in theaters:
            pref = t.css('td:nth-child(1)::text').extract_first()
            name = t.css('td:nth-child(2) a::text').extract_first()
            link = t.css('td:nth-child(2) a::attr(href)').extract_first()
            start_date = t.css('td:nth-child(3)::text').extract_first()
            preticket = t.css('td:nth-child(4)::text').extract_first()
            preticket = preticket == '○'
            live_viewing_0800 = t.css('td:nth-child(5)::text').extract_first()
            live_viewing_0800 = live_viewing_0800 == '○'
            live_viewing_1020 = t.css('td:nth-child(6)::text').extract_first()
            live_viewing_1020 = live_viewing_1020 == '○'

            if pref == '都道府県':
                continue
            item = dict(
                pref = pref,
                name = name,
                link = link,
                start_date = start_date,
                preticket = preticket,
                live_viewing_0800 = live_viewing_0800,
                live_viewing_1020 = live_viewing_1020,
            )
            yield item
