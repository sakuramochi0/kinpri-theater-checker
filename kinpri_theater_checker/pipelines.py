# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import re
import zenhan
from dateutil.parser import parse
from get_mongo_client import get_mongo_client


def normalize(text):
    return zenhan.z2h(text, mode=zenhan.DIGIT)


def parse_date(text):
    date_regex = re.compile(r'(\d{1,2})月(\d{1,2})日')
    m = date_regex.search(text)
    date_text = '/'.join(m.groups())
    date = parse(date_text)
    return date


class KinpriTheaterCheckerPipeline(object):
    pass


class TheaterPipeline(object):

    collection_name = 'theaters'

    def __init__(self, mongo_db):
        self.mongo_db = mongo_db


    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )


    def open_spider(self, spider):
        self.client = get_mongo_client()
        self.db = self.client[self.mongo_db]


    def close_spider(self, spider):
        self.client.close()


    def process_item(self, item, spider):
        item['preticket'] = '○' in item['preticket']
        item['live_viewing_20170610_0800'] = '○' in item['live_viewing_20170610_0800']
        item['live_viewing_20170610_1020'] = '○' in item['live_viewing_20170610_1020']

        m = re.search(r'(\d{1,2}.\d{1,2})', item['start_date'])
        if m:
            # match like this: '6.10 (sat)'
            date_str = m.group(1).replace('.', '/')
            item['start_date'] = parse(date_str)
        else:
            item['start_date'] = None

        item = dict(item)
        self.db[self.collection_name].update_one(
            {'name': item['name']}, {'$set': item}, upsert=True)
        return item


class ShowPipeline(object):

    collection_name = 'shows'

    def __init__(self, mongo_db):
        self.mongo_db = mongo_db


    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )


    def open_spider(self, spider):
        self.client = get_mongo_client()
        self.db = self.client[self.mongo_db]


    def close_spider(self, spider):
        self.client.close()


    def process_item(self, item, spider):
        if spider.name == 'kinezo':
            item['screen'] = normalize(item['screen'])
            item['date'] = parse(item['date'])
            state = re.search(r'sec0(\d)', item['ticket_state']).group(1)
            if state == '5': # ×
                item['ticket_state'] = 1
            elif state == '3': # △
                item['ticket_state'] = 2
            elif state == '2': # ○
                item['ticket_state'] = 3
            elif state == '1': # ◎
                item['ticket_state'] = 4
            elif state == '4': # -
                item['ticket_state'] = 0
        elif spider.name == 'aeoncinema':
            item['date'] = parse_date(item['date'])
            state = item['ticket_state']
            if state == '×': # ×
                item['ticket_state'] = 1
            elif state == '△': # △
                item['ticket_state'] = 2
            elif state == '○': # ○
                item['ticket_state'] = 3
            elif state == '◎': # ◎
                item['ticket_state'] = 4
            else:
                item['ticket_state'] = 0
                
        self.db[self.collection_name].insert(dict(item))

        # update latest shows
        self.db.shows_latest.update_one({
            'date': item['date'],
            'theater': item['theater'],
            'screen': item['screen'],
            'start_time': item['start_time'],
        }, {'$set': dict(item)},
            upsert=True,
        )

        return item

