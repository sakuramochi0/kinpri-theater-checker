# -*- coding: utf-8 -*-
import datetime
import re
import scrapy
from kinpri_theater_checker.items import Show
from kinpri_theater_checker import utils
from get_mongo_client import get_mongo_client


class KinezoSpider(scrapy.Spider):
    name = "unitedcinemas"
    custom_settings = {
        'ITEM_PIPELINES': {
            'kinpri_theater_checker.pipelines.ShowPipeline': 300,
        },
    }
    allowed_domains = ["unitedcinemas.jp"]

    # prepare start_urls
    db = get_mongo_client().kinpri_theater_checker.theaters
    theater_regex = re.compile(r'unitedcinemas.jp')
    start_urls = [t['link'] for t in db.find({'link': theater_regex})]

    def parse(self, response):
        # TODO: create start_requests() and get theater & url in it

        # get theater name
        if 'redirect_urls' in response.request.meta:
            request_url = response.request.meta['redirect_urls'][0]
        else:
            request_url = response.url
        theater = self.db.find_one({'link': request_url}).get('name')

        urls = response.css('#carouselCalendar li a::attr(href)').extract()
        for url in urls:
            next_url = response.urljoin(url)
            yield scrapy.Request(url=next_url,
                                 callback=self.parse_schedule,
                                 meta={'theater': theater})


    def parse_schedule(self, response):
        date = response.url
        movies = response.css('#dailyList>li')
        for movie in movies:
            title = movie.css('.movieTitle a::text').extract_first()
            
            # skip the movie is not kinpri
            if not utils.regex_kinpri.search(title):
                continue
            
            shows_rows = movie.css('.tl>li')
            for shows_row in shows_rows:
                screen = shows_row.css('.screenNumber img::attr(alt)').re(r'(\d+)')[0]
                shows = shows_row.css('div')
                for s in shows:
                    show = Show()
                    show['updated'] = datetime.datetime.now()
                    show['theater'] = response.meta['theater']
                    show['schedule_url'] = response.url
                    show['date'] = date
                    show['title'] = title
                    show['screen'] = screen
                    show['movie_types'] = utils.get_kinpri_types(title)
                    show['start_time'] = s.css('.startTime::text').extract_first()
                    show['end_time'] = s.css('.endTime::text').extract_first()
                    state = s.css('.tl .uolIcon .scheduleIcon::attr(alt)').re(r'\[(.)\]')
                    if state:
                        show['ticket_state'] = state[0]
                    else:
                        show['ticket_state'] = None
                    reservation_url = movie.css('.uolIcon a::attr(href)').extract_first()
                    if reservation_url:
                        show['reservation_url'] = reservation_url
                        yield scrapy.Request(url=reservation_url,
                                             callback=self.parse_check_continue,
                                             meta={'show': show},
                                             dont_filter=True,
                        )
                    else: 
                        show['remaining_seats_num'] = 0
                        show['total_seats_num'] = None
                        show['reserved_seats'] = None
                        show['remaining_seats'] = []
                        show['reservation_url'] = None
                        yield show


    def parse_check_continue(self, response):
        if '購入途中' in response.css('h2::text').extract_first():
            url = response.urljoin(response.css('form::attr(action)').extract()[-1])
            yield response.request.replace(url=url,
                                           callback=self.parse_reservation,
                                           method='POST',
                                           body='rm=start')
        yield response.request.replace(callback=self.parse_reservation)


    def parse_reservation(self, response):
        show = response.meta['show']
        remainings = [s.css('::attr(id)').extract_first()
                     for s in response.css('#view_seat td[value="0"]')]
        reserveds = [s.css('::attr(id)').extract_first()
                     for s in response.css('#view_seat td[value="1"]')]
        show['remaining_seats_num'] = len(remainings)
        show['total_seats_num'] = len(remainings) + len(reserveds)
        show['reserved_seats'] = reserveds
        show['remaining_seats'] = remainings
        yield show
