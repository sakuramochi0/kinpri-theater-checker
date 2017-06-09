# -*- coding: utf-8 -*-
import datetime
import re
import scrapy
from kinpri_theater_checker.items import Show
from kinpri_theater_checker import utils
from get_mongo_client import get_mongo_client


class KinezoSpider(scrapy.Spider):
    name = "kinezo"
    custom_settings = {
        'ITEM_PIPELINES': {
            'kinpri_theater_checker.pipelines.ShowPipeline': 300,
        }
    }
    allowed_domains = ["kinezo.jp"]

    # prepare start_urls
    kinezo_regex = re.compile(r'kinezo.jp|tjoy.net')
    db = get_mongo_client().kinpri_theater_checker.theater
    start_urls = [t['link'] for t in db.find({'link': kinezo_regex})][:1]

    def parse(self, response):
        # get theater name
        if 'redirect_urls' in response.request.meta:
            request_url = response.request.meta['redirect_urls'][0]
        else:
            request_url = response.url
        theater_name = self.db.find_one({'link': request_url}).get('name')

        event_url = list(
            filter(lambda x: '/event_list' in x,
                   response.css('#headerMenuData a::attr(href)').extract()))[0]
        self.logger.info('event_url: ' + event_url)

        # parse event list
        # yield scrapy.Request(url=event_url, callback=self.parse_event,
        #                      meta={'theater': theater_name})

        # parse normal list
        movies = response.css('a[name="movieItem"]')
        for movie in movies:
            title = ' '.join(movie.css('span::text').extract())
            if REGEX_KINPRI.search(title):
                url = movie.css('::attr(href)').extract_first()
                self.logger.info('title: ' + title)
                self.logger.info('url: ' + url)
                yield scrapy.Request(url=url, callback=self.parse_schedule)


    def parse_schedule(self, response):
        lis = response.css('.eventScheduleList li')
        for li in lis:
            show = Show()
            show['updated'] = datetime.datetime.now()
            show['theater'] = response.meta['theater']
            show['screen'] = li.css('.screen_name::text').extract_first()
            title = li.css('.title::text').extract_first()
            if not REGEX_KINPRI.search(title):
                continue
            show['title'] = title
            show['date'] = li.css('.date::text').extract_first()
            show['start_time'] = li.css('.start::text').extract_first()
            show['end_time'] = li.css('.end::text').extract_first()
            show['ticket_state'] = li.css('.ticket_state::attr(class)').extract_first()
        
            reservation_url = response.urljoin(li.css('a::attr(href)').extract_first())
            if reservation_url:
                yield scrapy.Request(url=reservation_url, callback=self.parse_reservation,
                                     meta={'show': show})
            else:
                show['remaining_seats_num'] = 0
                show['total_seats_num'] = None
                show['reserved_seats'] = None
                show['remaining_seats'] = []
                yield show


    def parse_reservation(self, response):
        show = response.meta['show']
        remaining = [s.css('::attr(title)').extract_first()
                     for s in response.css('li.seatSell.seatOn')]
        reserved = [s.css('::attr(title)').extract_first()
                    for s in response.css('li.seatSell.seatOff')]
        show['remaining_seats_num'] = len(remaining)
        show['total_seats_num'] = len(remaining) + len(reserved)
        show['reserved_seats'] = reserved
        show['remaining_seats'] = remaining
        yield show
