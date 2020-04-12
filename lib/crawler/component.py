import sys
import datetime
import time
import random
import threading
from queue import Queue

from lib.utils import Logger, Dict
from lib.utils.mysql import DataBase
from . import Parser, Searcher, Requestor

thread_lock = threading.Lock()


def lock(thread_func):
    def wrapper(obj, *args, **kwargs):
        thread_lock.acquire()
        try:
            return thread_func(obj, *args, **kwargs)
        except Exception as e:
            raise e
        finally:
            thread_lock.release()
    return wrapper


class BaseUrlFetcher(threading.Thread):
    def __init__(self, request: Requestor):
        threading.Thread.__init__(self, daemon=True)
        self.request = request


class BaseCrawler(threading.Thread):
    def __init__(self, request: Requestor, parser: Parser, url_fetcher: BaseUrlFetcher):
        threading.Thread.__init__(self, daemon=True)
        self.request = request
        self.parser = parser
        self.url_fetcher = url_fetcher


class TargetedCrawler(BaseCrawler):
    def __init__(self, request: Requestor, parser: Parser, url_fetcher: BaseUrlFetcher, database: DataBase, table: str, logger: Logger, target: dict, queue: Queue, current_info: Dict, proxies=None):
        super().__init__(request, parser, url_fetcher)

        self.database = database
        self.table = table
        self.logger = logger

        self.target = target    # {'alias': '', 'host': ''}
        self.queue = queue
        self.current_info = current_info

        self.proxies = proxies
        self.crawled_urls = set([r['url'] for r in self.database.select(self.table, 'url', site=self.target['alias'])])
        
    def run(self):
        while self.url_fetcher.is_alive() or self.queue.qsize():
            if not self.queue.empty():
                try:
                    self.current_info.query = self.queue.get()
                    query = self.current_info.query
                    topic = query.get('topic', '')
                    soup, url = self.request(query['url'], no_headers=True)
                    if url['url'] not in self.crawled_urls:
                        data = self.parser(soup, url['netloc'], url['tld'])
                        next_page_url = data.pop('next', None)
                        while next_page_url:
                            try:
                                _soup, _url = self.request(next_page_url)
                                _data = self.parser(_soup, _url['netloc'], _url['tld'])
                                data['text'] += _data['text']
                                next_page_url = _data.pop('next', None)
                            except:
                                break
                        # data = {'publish_time': datetime.datetime.now(), 'source': random_str(4), 'title': random_str(8), 'text': random_str(16)}
                        self.save(**data, url=url['url'], site=self.target['alias'], entry_time=datetime.datetime.now(), topic=topic)
                        self.logger.info(f'parse and save (url:{url["url"]}, topic:{topic}, title:{data["title"]}) successfully')
                        self.crawled_urls.add(url['url'])
                    else:
                        self.logger.info(f'{url["url"]} is in database already')
                    self.current_info.pop('query')
                except:
                    self.logger.error(exc_info=sys.exc_info(), message=f'parse and save (url:{url["url"]}, topic:{topic})')
            else:
                time.sleep(2)

    @lock
    def save(self, **data):
        topic = data.pop('topic')
        last_row_id = self.database.insert(self.table, **data)
        self.database.insert(f'{self.table}_topic', news_id=last_row_id, topic_name=topic)
