# -*- coding: utf-8 -*-
import datetime
import re
import scrapy
from kinpri_theater_checker.items import Show
from kinpri_theater_checker import utils
from get_mongo_client import get_mongo_client


class TtcgSpider(scrapy.Spider):
    name = "ttcg"
    custom_settings = {
        'ITEM_PIPELINES': {
            'kinpri_theater_checker.pipelines.ShowPipeline': 300,
        }
    }
    allowed_domains = ['ttcg.jp']

    # prepare start_urls
    db = get_mongo_client().kinpri_theater_checker.theaters
    start_urls = [t['link'] for t in db.find({'link': re.compile(r'ttcg.jp')})]


    def parse(self, response):
        # get theater name
        if 'redirect_urls' in response.request.meta:
            request_url = response.request.meta['redirect_urls'][0]
        else:
            request_url = response.url
        theater = self.db.find_one({'link': request_url}).get('name')

        url = response.css('#navschedule a::attr(href)').extract_first()
        yield scrapy.Request(url=url, callback=self.parse_schedule,
                             meta={'theater': theater})


    def parse_schedule(self, response):
        date = response.css('.today::text').extract_first()
        movies = response.css('.timeschedule')
        for movie in movies:
            title = movie.css('.mtitle span.fontm::text').extract_first().strip()
            
            # skip not kinpri
            if not utils.is_title_kinpri(title):
                continue

            shows = movie.css('td')
            for s in shows:
                show = Show()

                show['updated'] = datetime.datetime.now()
                show['title'] = title
                show['movie_types'] = utils.get_kinpri_types(title)
                show['date'] = date
                show['theater'] = response.meta['theater']
                show['schedule_url'] = response.url
                show['start_time'] = s.css('.start ::text').extract_first()
                if not show['start_time']:
                    break
                show['end_time'] = s.css('.end ::text').extract_first()
                show['screen'] = None
                state = s.css('.icon_kuuseki ::text').extract_first()
                show['ticket_state'] = state

                reservation_url = None
                if reservation_url:
                    show['reservation_url'] = reservation_url
                    yield scrapy.Request(url=reservation_url,
                                         callback=self.parse_reservation,
                                         meta={'show': show})
                else:
                    yield show

        next_day_url = response.css('.schehead .b-next a::attr(href)') \
                               .extract_first()
        if not next_day_url == response.url:
            print(next_day_url)
            yield response.request.replace(url=next_day_url)


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
