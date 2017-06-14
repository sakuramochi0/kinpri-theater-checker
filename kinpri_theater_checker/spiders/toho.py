# -*- coding: utf-8 -*-
import datetime
import re
import scrapy
from scrapy_splash import SplashRequest
from kinpri_theater_checker.items import Show
from kinpri_theater_checker import utils
from get_mongo_client import get_mongo_client


class TohoSpider(scrapy.Spider):
    name = 'toho'
    custom_settings = {
        'ITEM_PIPELINES': {
            'kinpri_theater_checker.pipelines.ShowPipeline': 300,
        },
        'CONCURRENT_REQUESTS': 2,
    }
    allowed_domains = ['tohotheater.jp']

    # prepare start_urls
    db = get_mongo_client().kinpri_theater_checker.theaters


    def start_requests(self):
        theater_regex = re.compile('|'.join(self.allowed_domains))
        start_urls = [t['link'] for t in self.db.find({'link': theater_regex})]
        for url in start_urls:
            yield SplashRequest(
                url=url,
                callback=self.parse,
                args={'wait': 3},
            )


    def parse(self, response):
        # get theater name
        if 'redirect_urls' in response.request.meta:
            request_url = response.request.meta['redirect_urls'][0]
        else:
            request_url = response.url
        theater = self.db.find_one({'link': request_url}).get('name')

        date = response.css('.schedule-body-day::text').extract_first()
        movies = response.css('.schedule-body-section-item')
        for movie in movies:
            title = movie.css('.schedule-body-title::text').extract_first()
            
            # skip the movie is not kinpri
            if not utils.is_title_kinpri(title):
                continue

            screens = movie.css('.schedule-screen')
            for s in screens:
                screen = s.css('.schedule-screen-title::text').extract_first()

                shows = s.css('.schedule-item')
                for s in shows:
                    show = Show()
                    show['updated'] = datetime.datetime.now()
                    show['theater'] = theater
                    show['schedule_url'] = response.url
                    show['date'] = date
                    show['title'] = title
                    show['movie_types'] = utils.get_kinpri_types(title)
                    show['screen'] = screen
                    show['start_time'] = s.css('.time .start::text').extract_first()
                    show['end_time'] = s.css('.time .end::text').extract_first()
                    show['ticket_state'] = s.css('.status::attr(class)').extract_first()
                    reservation_url = s.css('a')
                    # if reservation_url:
                    #     reservation_url = 
                    #     yield scrapy.Request(url=reservation_url,
                    #                          callback=self.parse_reservation,
                    #                          meta={'show': show},
                    #     )
                    # else: 
                    show['remaining_seats_num'] = 0
                    show['total_seats_num'] = None
                    show['reserved_seats'] = None
                    show['remaining_seats'] = []
                    show['reservation_url'] = None
                    yield show


    def parse_reservation(self, response):
        show = response.meta['show']
        seats = response.css('#choice td a.tip')
        remainings = []
        reserveds = []
        for seat in seats:
            if seat.css('img[src*="seat_no"]'):
                id = eat.css('::attr(title)').extract_first()
                reserveds.append(id)
            elif seat.css('img[src*="seat_off"]'):
                id = eat.css('::attr(title)').extract_first()
                remainings.append(id)
        show['remaining_seats_num'] = len(remainings)
        show['total_seats_num'] = len(remainings) + len(reserveds)
        show['reserved_seats'] = reserveds
        show['remaining_seats'] = remainings
        yield show
