import os
import sys
import pickle
import json
import datetime
import time
import random
from queue import Queue

from lib.crawler import Config, Parser, Searcher, Requestor
from lib.crawler.component import BaseUrlFetcher, TargetedCrawler
from lib.utils import Logger, Dict
from lib.utils.mysql import DataBase


class SearchEngineUrlFetcher(BaseUrlFetcher):
    def __init__(self, request: Requestor, searcher: Searcher, queries, current_info, hosts: list, topics: list, pages: list, queue_dict):
        super().__init__(request)
        self.searcher = searcher

        self.queries = queries
        self.current_info = current_info

        self.hosts = hosts
        self.topics = topics
        self.pages = pages

        self.queue_dict = queue_dict

        self._init_queries()

    def _init_queries(self, page_order=True):
        temp = {host: {topic['name']: {'pages': [page for page in self.pages], 'keywords': topic['keywords']} for topic in self.topics} for host in self.hosts}
        while temp:
            random_host = random.choice(list(temp.keys()))
            random_host_topics = temp[random_host]
            random_topic = random.choice(list(random_host_topics.keys()))
            random_keyword_pages = random_host_topics[random_topic]
            page = random_keyword_pages['pages'].pop(0)
            self.queries.put({'url': self.searcher.construct_query(random_keyword_pages['keywords'], random_host, page), 'host': random_host, 'topic': random_topic})
            if not random_keyword_pages['pages']:
                random_host_topics.pop(random_topic)
            if not random_host_topics:
                temp.pop(random_host)
    
    def dispatch(self, urls, host, topic):
        for url in urls:
            self.queue_dict[host].put({'url': url, 'topic': topic})

    def run(self):
        while not self.queries.empty():
            self.current_info.query = self.queries.get()
            query = self.current_info.query
            soup, _ = self.request(query['url'], headers=self.request.headers_map['www.baidu.com'])
            urls = self.searcher.parse(soup)
            self.dispatch(urls, query['host'], query['topic'])
            self.current_info.pop('query')
            time.sleep(random.uniform(2, 3))


class TopicalCrawler:
    def __init__(self, name, config, topics, pages):
        self.name = name
        self.config = config
        self.topics = topics
        self.site_alias = {target['host']: target.get('alias', '') for target in self.config.targets}
        
        self.url_queries = Queue()
        self.current_info = Dict()
        self.queue_dict = {target['host']: Queue() for target in self.config.targets}
        self.current_info_dict = {target['host']: Dict() for target in self.config.targets}
        self.save_breakpoint_path = os.path.join(self.config.save.tmp, f'{self.name}.breakpoint')

        if os.path.isfile(self.save_breakpoint_path):
            self._load_breakpoint()

        self.request = Requestor(self.config)
        # self.searcher = Searcher(self.config)
        self.searcher = Searcher('baidu')
        self.parser = Parser()
        
        self.database = DataBase(**self.config.save.database.login)

        # self.reset_database()
        self.table = 'news'
        self.logger = Logger(filename=self.config.save.log)
        
        self.url_fetcher = SearchEngineUrlFetcher(
            request=self.request,
            searcher=self.searcher,

            queries=self.url_queries,
            current_info=self.current_info,
            hosts=[target['host'] for target in self.config.targets],
            topics=self.topics,
            pages=pages,
            
            queue_dict=self.queue_dict,
        )

        # one thread for one host
        self.threads = [TargetedCrawler(
            self.request,
            self.parser,
            self.url_fetcher,
            self.database,
            self.table,
            self.logger,
            target,
            self.queue_dict[target['host']],
            self.current_info_dict[target['host']],
        ) for target in config.targets]

    def __call__(self, string, option='url'):
        if option == 'url':
            self.parse(string)
        elif option == 'keyword':
            urls = self.search(string)
            data = []
            for url in urls:
                soup, url, host = self.request(url)
                data.append(self.parse(soup, host))
            return data
        else:
            raise ValueError("option should be 'url' or 'keyword'")
    
    def test_search(self, keyword, host=None, page=1):
        query = self.searcher.construct_query(keyword, host, page)
        soup, _ = self.request(query)
        urls = self.searcher.parse(soup)
        return urls

    def test_parse(self, url, remain_query_key=None):
        soup, url = self.request(url, remain_query_key=remain_query_key, no_headers=True)
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
        return {**data, 'url': url['url'], 'site': self.site_alias.get(url['tld']) or self.site_alias.get(url['netloc'], '')}
        
    def _load_breakpoint(self):
        with open(self.save_breakpoint_path, 'rb') as f:
            temp = pickle.load(f)
        
        for q in temp['url_queries']:
            self.url_queries.put(q)

        for host, queue_ in temp['queue_dict'].items():
            for q in queue_:
                self.queue_dict[host].put(q)

    def _save_breakpoint(self):
        temp = {
            'url_queries': ([self.current_info.query] if self.current_info.get('query') else []) + [self.url_queries.get() for _ in range(self.url_queries.qsize())],
            'queue_dict': {target: ([self.current_info_dict[target].query] if self.current_info_dict[target].get('query') else []) + [queue_.get() for _ in range(queue_.qsize())] for target, queue_ in self.queue_dict.items()}
        }
        with open(self.save_breakpoint_path, 'wb') as f:
            pickle.dump(temp, f)

    def _cleanup(self):
        try:
            self.database.close()
        except:
            pass

    def run(self):
        self._init_topics()
        self.url_fetcher.start()
        for t in self.threads:
            t.start()
        try:
            while True:
                time.sleep(1)
                if self.url_fetcher.is_alive():
                    continue
                for t in self.threads:
                    if t.is_alive():
                        break
                else:
                    break
        except KeyboardInterrupt:
            self.logger.info('keyboard interrupt by user')
            self._save_breakpoint()
            self._cleanup()
        except:
            self.logger.error(exc_info=sys.exc_info())
            self._save_breakpoint()
            self._cleanup()

    def _init_topics(self):
        for topic in self.topics:
            if not isinstance(topic['keywords'], list):
                topic['keywords'] = [topic['keywords']]
            temp_keywords_str = json.dumps(topic['keywords'])
            if not self.database.select('topic', name=topic['name']):
                self.database.insert('topic',
                    name        =topic['name'],
                    keywords    =temp_keywords_str,
                    entry_time  =datetime.datetime.now(),
                    remark      =topic.get('remark', '')
                )
            else:
                self.database.update({'table': 'topic', 'constraints': {'name': topic['name']}}, remark=topic.get('remark', ''), keywords=temp_keywords_str)

if __name__ == '__main__':
    config = Config('config.json')
    topics = [
        # 示例, 该列表的每一个元素代表一个主题，name 字段为主题名称/标识, keywords字段为该主题的关键词
        # {'name': '主题名称', 'keywords': ['关键词1', '关键词2']}
        {'name': '九合一选举', 'keywords': ['台湾', '九合一']},
    ]
    pages = list(range(1, 21))  # 百度搜索的页码
    
    topic_crawler = TopicalCrawler('topic_crawler', config, topics, pages)
    topic_crawler.run()
    