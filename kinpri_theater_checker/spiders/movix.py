# -*- coding: utf-8 -*-
import datetime
import re
import scrapy
from scrapy_splash import SplashRequest
from kinpri_theater_checker.items import Show
from kinpri_theater_checker import utils
from get_mongo_client import get_mongo_client


class MovixSpider(scrapy.Spider):
    name = 'movix'
    custom_settings = {
        'ITEM_PIPELINES': {
            'kinpri_theater_checker.pipelines.ShowPipeline': 300,
        },
    }
    allowed_domains = ['smt-cinema.com']

    # prepare start_urls
    db = get_mongo_client().kinpri_theater_checker.theaters
    script = '''
treat = require("treat")

function get_movie(splash, i)
    local button = splash.execjs(
        "document.querySelectorAll('.scrollDate:not(.nonactive)')[" .. i .. "]")
    button.mouse_click()
    local res = {
        html = splash:html(),
        ok = true,
    }
    return res
end

function main(splash)
    local days = splash:execjs(
        "document.querySelectorAll('.scrollDate:not(.nonactive)').length")
    local movies = treat.as_array({})
    for i = 0, days - 1 do
        movies[i] = get_movie(splash, i)
    end
    return movies
end
'''


    def start_requests(self):
        theater_regex = re.compile('|'.join(self.allowed_domains))
        start_urls = [t['link'] for t in self.db.find({'link': theater_regex})]
        for url in start_urls:
            yield SplashRequest(
                url=url,
                callback=self.parse,
                args={'wait': 0.5},
            )


    def parse(self, response):
        # get theater name
        if 'redirect_urls' in response.request.meta:
            request_url = response.request.meta['redirect_urls'][0]
        else:
            request_url = response.url
        theater = self.db.find_one({'link': request_url}).get('name')

        date = response.css('#Day_schedule h1::text').extract_first()
        movies = response.css('.scheduleBox')
        for movie in movies:
            title = movie.css('h2 ::text').extract_first()
            
            # skip the movie is not kinpri
            if not utils.is_title_kinpri(title):
                continue

            shows = movie.css('.scheduleBox>table>tbody>tr>td')
            for s in shows:
                show = Show()
                show['updated'] = datetime.datetime.now()
                show['theater'] = theater
                show['schedule_url'] = response.url
                show['date'] = date
                show['title'] = title
                show['movie_types'] = utils.get_kinpri_types(title)
                screen = s.css('p::text').re(r'\d+')
                if not screen:
                    break
                show['screen'] = screen[0]
                show['start_time'] = s.css('span::text').extract_first()
                show['end_time'] = s.css('tr>td::text').re(r'\d+:\d+')[0]
                show['ticket_state'] = s.css('img::attr(alt)').extract_first()
                reservation_url = s.css('td[onclick]::attr(onclick)')
                if reservation_url:
                    reservation_url = reservation_url.re(r"'(https://.+?)'")[0]
                    yield scrapy.Request(url=reservation_url,
                                         callback=self.parse_reservation,
                                         meta={'show': show},
                    )
                else: 
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
                id = seat.css('::attr(title)').extract_first()
                reserveds.append(id)
            elif seat.css('img[src*="seat_off"]'):
                id = seat.css('::attr(title)').extract_first()
                remainings.append(id)
        show['remaining_seats_num'] = len(remainings)
        show['total_seats_num'] = len(remainings) + len(reserveds)
        show['reserved_seats'] = reserveds
        show['remaining_seats'] = remainings
        yield show
