# -*- coding: utf-8 -*-
import datetime
import re
import scrapy
from kinpri_theater_checker.items import Show
from kinpri_theater_checker import utils
from get_mongo_client import get_mongo_client


class CinecittaSpider(scrapy.Spider):
    name = "cinecitta"
    custom_settings = {
        'ITEM_PIPELINES': {
            'kinpri_theater_checker.pipelines.ShowPipeline': 300,
        },
    }
    allowed_domains = ['cinecitta.co.jp', 'cinecitta.jp']

    # prepare start_urls
    db = get_mongo_client().kinpri_theater_checker.theaters
    theater_regex = re.compile(r'cinecitta.co.jp')
    start_urls = [t['link'] for t in db.find({'link': theater_regex})]

    def parse(self, response):
        # get theater name
        if 'redirect_urls' in response.request.meta:
            request_url = response.request.meta['redirect_urls'][0]
        else:
            request_url = response.url
        theater = self.db.find_one({'link': request_url}).get('name')

        calendar_url = response.urljoin(response.css('iframe::attr(src)').extract_first())
        yield scrapy.Request(url=calendar_url,
                             callback=self.parse_calendar,
                             meta={'theater': theater})


    def parse_calendar(self, response):
        urls_dates = zip(
            response.css('a::attr(href)').extract(),
            response.css('a::text').extract())
        for url, date in urls_dates:
            response.meta['date'] = date
            yield response.request.replace(url=url,
                                           callback=self.parse_schedule_iframe,
                                           meta=response.meta)


    def parse_schedule_iframe(self, response):
        url = response.urljoin(response.css('#ifrParent::attr(src)').extract_first())
        yield response.request.replace(url=url, callback=self.parse_schedule)


    def parse_schedule(self, response):
        movies = response.css('table.movietitle')
        for movie in movies:
            title = movie.css('.item1 ::text').extract_first()
            
            # skip the movie is not kinpri
            if not utils.is_title_kinpri(title):
                continue

            screen = movie.css('a.theaterlink::text').re(r'\d+')[0]
            shows = movie.css('.time1, .time2')
            for s in shows:
                show = Show()
                show['updated'] = datetime.datetime.now()
                show['theater'] = response.meta['theater']
                show['schedule_url'] = response.url
                show['date'] = response.meta['date']
                show['title'] = title
                show['screen'] = screen
                show['movie_types'] = utils.get_kinpri_types(title)
                times = s.css('span::text').re(r'\d+:\d+')
                if not times:
                    break
                show['start_time'] = times[0]
                show['end_time'] = times[1]
                show['ticket_state'] = s.css('img::attr(src)').extract()[-1]
                show['reservation_url'] = s.css('a::attr(href)').extract_first()
                # TODO: check seats
                # if reservation_url:
                #     
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
