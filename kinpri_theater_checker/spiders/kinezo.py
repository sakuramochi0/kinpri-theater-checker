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
    db = get_mongo_client().kinpri_theater_checker.theaters
    kinezo_regex = re.compile(r'kinezo.jp|tjoy.net')
    start_urls = [t['link'] for t in db.find({'link': kinezo_regex})]
    print('start_urls:', start_urls)

    def parse(self, response):
        # get theater name
        if 'redirect_urls' in response.request.meta:
            request_url = response.request.meta['redirect_urls'][0]
        else:
            request_url = response.url
        theater = self.db.find_one({'link': request_url}).get('name')

        event_url = list(
            filter(lambda x: '/event_list' in x,
                   response.css('#headerMenuData a::attr(href)').extract()))[0]
        self.logger.info('event_url: ' + event_url)

        # parse normal list
        movies = response.css('a[name="movieItem"]')
        for movie in movies:
            title = ' '.join(movie.css('span::text').extract())
            if utils.regex_kinpri.search(title):
                url = movie.css('::attr(href)').extract_first()
                self.logger.info('title: ' + title)
                self.logger.info('url: ' + url)
                yield scrapy.Request(url=url, callback=self.parse_schedule,
                                     meta={'theater': theater})


    def parse_schedule(self, response):
        
        schedule_days = response.css('#schedule p[id^="day_"]')
        schedule_list = response.css('.schedule_list ul')
        # self.logger.info('schedule_days: ' + schedule_days.extract_first())
        for day, ul in zip(schedule_days, schedule_list):
            date = day.css('span::text').extract_first()
            for li in ul.css('li'):
                show = Show()
     
                # skip no schedule day
                state = li.css('::attr(class)').extract_first()
                if not state or state == 'noSchedule':
                    continue
     
                show['updated'] = datetime.datetime.now()
                title = ' '.join(response.css('.text span::text').extract())
                show['title'] = title
                show['movie_types'] = utils.get_kinpri_types(title)
                show['date'] = date
                show['ticket_state'] = state
                show['theater'] = response.meta['theater']
                show['screen'], time = li.css('::text').extract()
                show['start_time'], show['end_time'] = time.split(' - ')
                show['schedule_url'] = response.url

                reservation_url = li.css('a::attr(href)').extract_first()
                if state == 'sec05': # soldout
                    show['remaining_seats_num'] = 0
                    show['total_seats_num'] = None
                    show['reserved_seats'] = None
                    show['remaining_seats'] = []
                    show['reservation_url'] = None
                    yield show
                else: 
                    show['reservation_url'] = reservation_url
                    yield scrapy.Request(url=reservation_url,
                                         callback=self.parse_reservation,
                                         meta={'show': show})


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
