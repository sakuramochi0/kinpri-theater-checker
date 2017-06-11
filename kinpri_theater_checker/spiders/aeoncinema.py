# -*- coding: utf-8 -*-
import datetime
import re
import scrapy
from kinpri_theater_checker.items import Show
from kinpri_theater_checker import utils
from get_mongo_client import get_mongo_client


class AeoncinemaSpider(scrapy.Spider):
    name = "aeoncinema"
    custom_settings = {
        'ITEM_PIPELINES': {
            'kinpri_theater_checker.pipelines.ShowPipeline': 300,
        }
    }
    allowed_domains = ["aeoncinema.com"]

    # prepare start_urls
    db = get_mongo_client().kinpri_theater_checker.theaters
    aeoncinema_regex = re.compile(r'aeoncinema.com')
    start_urls = [t['link'] for t in db.find({'link': aeoncinema_regex})]


    def parse(self, response):
        # get theater name
        if 'redirect_urls' in response.request.meta:
            request_url = response.request.meta['redirect_urls'][0]
        else:
            request_url = response.url
        theater = self.db.find_one({'link': request_url}).get('name')

        url = response.css('li.schedule a::attr(href)').extract_first()
        yield scrapy.Request(url=url, callback=self.parse_schedule,
                             meta={'theater': theater})


    def parse_schedule(self, response):

        date = response.css('.today::text').extract_first()
        movies = response.css('.movielist')
        for movie in movies:
            title = movie.css('.main a::text').extract_first().strip()
            
            # skip not kinpri
            if not utils.regex_kinpri.search(title):
                continue

            shows = movie.css('.timetbl [class^="tbl"]')[1:]
            for s in shows:
                show = Show()

                show['updated'] = datetime.datetime.now()
                show['title'] = title
                show['movie_types'] = utils.get_kinpri_types(title)
                show['date'] = date
                show['theater'] = response.meta['theater']
                show['schedule_url'] = response.url

                start_time, end_time = s.css('.time ::text').extract()
                show['start_time'] = ':'.join(re.findall(r'(\d{1,2})', start_time))
                show['end_time'] = ':'.join(re.findall(r'(\d{1,2})', end_time))
                show['screen'] = s.css('.screen ::text').extract_first()
                state = s.css('.icon_kuuseki ::text').extract_first()
                show['ticket_state'] = state

                # TODO: run javascript via splash
                reservation_url = None
                if reservation_url:
                    show['reservation_url'] = reservation_url
                    yield scrapy.Request(url=reservation_url,
                                         callback=self.parse_reservation,
                                         meta={'show': show})
                else:
                    yield show


    # TODO: 
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
