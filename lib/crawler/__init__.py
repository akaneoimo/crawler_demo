import os
import json
import time

from bs4 import BeautifulSoup
import requests
import chardet

from lib.utils import Dict
from .utils import extract_url, simplify_url
from . import parse, search, index

WORK_DIR = os.getcwd()


class Config(Dict):
    default_config = {
        'save': {
            'log': {
                'info': os.path.join(WORK_DIR, 'log', 'crawler.log'),
                'error': os.path.join(WORK_DIR, 'log', 'crawler.err'),
            },
            'tmp': os.path.join(WORK_DIR, 'tmp'),
            'database': {
                'login': {
                    'host': '127.0.0.1',
                    'username': 'root',
                    'password': '',
                    'database': 'newsdb'
                },
            }
        },
        'network': {
            'proxy': {
                'enable': False,
                'settings': {
                    'http': 'http://127.0.0.1:10809',
                    'https': 'http://127.0.0.1:10809'
                }
            },
        },
        'parse': {
            'parser': 'lxml'
        },
        'targets': [
            {'host': 'baijiahao.baidu.com', 'alias': 'baijiahao', 'engine': 'baidu'},
            {'host': 'sina.com.cn', 'alias': 'sina', 'engine': 'baidu'},
            {'host': 'taihainet.com', 'alias': 'taihainet', 'engine': 'baidu'},
            {'host': 'sohu.com', 'alias': 'sohu', 'engine': 'baidu'},
            {'host': '163.com', 'alias': '163', 'engine': 'baidu'},
            {'host': 'qq.com', 'alias': 'qq', 'engine': 'baidu'},
            {'host': 'huanqiu.com', 'alias': 'huanqiu', 'engine': 'baidu'},
            {'host': 'people.com.cn', 'alias': 'people', 'engine': 'baidu'},
            {'host': 'takungpao.com', 'alias': 'takungpao', 'engine': 'baidu'},
            {'host': 'cankaoxiaoxi.com', 'alias': 'cankaoxiaoxi', 'engine': 'baidu'},
            {'host': 'chinanews.com', 'alias': 'chinanews', 'engine': 'baidu'},
            {'host': 'cctv.com', 'alias': 'cctv', 'engine': 'baidu'},
            {'host': '81.cn', 'alias': '81', 'engine': 'baidu'},
            {'host': 'southcn.com', 'alias': 'south', 'engine': 'baidu'},
            {'host': 'china.com', 'alias': 'china', 'engine': 'baidu'},
            {'host': 'thepaper.cn', 'alias': 'thepaper', 'engine': 'baidu'},
            {'host': 'stnn.cc', 'alias': 'stnn', 'engine': 'baidu'},
            {'host': 'xinhuanet.com', 'alias': 'xinhuanet', 'engine': 'baidu'},
            {'host': 'cnr.cn', 'alias': 'cnr', 'engine': 'baidu'},
            {'host': 'cri.cn', 'alias': 'cri', 'engine': 'baidu'},
        ],
    }
    def __init__(self, config_path=None):
        super().__init__(self.default_config)
        if config_path:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.update_deep(config)
        self._create_directory()

    def _create_directory(self):
        def mkdir(path):
            if path:
                os.makedirs(path, exist_ok=True)
        
        if isinstance(self.save.log, dict):
            for _, path in self.save.log.items():
                mkdir(os.path.dirname(path))
        elif isinstance(self.save.log, str):
            mkdir(os.path.dirname(self.save.log))
        else:
            raise TypeError('`save.log` should be a dict or string')

        mkdir(self.save.tmp)


class Requestor:
    fake_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
    headers_map = {
        'www.baidu.com': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,ja;q=0.8,en;q=0.7',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Cookie': 'BIDUPSID=E185CABE347220655AF00C7870FD22A2; PSTM=1583135662; BAIDUID=E185CABE3472206568D8DDF830CFBDEE:FG=1; BD_UPN=12314753; sug=3; sugstore=0; ORIGIN=2; bdime=0; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598; BD_HOME=1; H_PS_PSSID=30968_1461_31120_21121_31187_30823_31164_22160; delPer=0; BD_CK_SAM=1; PSINO=5; H_PS_645EC=7d51A7XLrc%2FefHNSv3R6jnUaClUAyd5tkCB85Puy9YS4wGFHq7J2t5zmLgI',
            'Host': 'www.baidu.com',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        },
        'www.thepaper.cn': {
            'Host': 'www.thepaper.cn',
        },
        'www.xinhuanet.com': {
            'Host': 'www.xinhuanet.com',
        }
    }
    for _, headers in headers_map.items():
        headers.update({'User-Agent': fake_user_agent})

    def __init__(self, config):
        self.config = config

    def __call__(self, url, timeout=5, proxies=None, headers=None, remain_query_key=None, no_headers=False):
        if remain_query_key:
            url = simplify_url(url, remain_query_key)
        
        if no_headers:
            response = requests.get(url)
        else:
            if headers:
                response = requests.get(url, timeout=timeout, proxies=proxies, headers=headers)
            else:
                temp = extract_url(url)
                response = requests.get(temp['url'], timeout=timeout, proxies=proxies, headers=self.headers_map.get(temp['netloc']))
 
        url = extract_url(response.url)
        if url['netloc'] != 'baijiahao.baidu.com':
            url['url'] = simplify_url(url['url'])


        soup = BeautifulSoup(response.text, features=self.config.parse.parser)
        for meta in soup.select('head meta'):
            if meta.get('charset'):
                response.encoding = meta['charset'].lower()
                return BeautifulSoup(response.text, features=self.config.parse.parser), url
        
        charset = chardet.detect(response.content)
        if charset['confidence'] > 0.7:
            response.encoding = charset['encoding']
        else:
            response.encoding = 'utf-8'
        return BeautifulSoup(response.text, features=self.config.parse.parser), url


class Searcher:
    def __init__(self, config=None):
        self.config = config if config else 'baidu'
    
    def construct_query(self, keyword, host=None, page=1, start_time='', end_time='', option='all'):
        if self.config == 'baidu':
            if isinstance(keyword, list):
                if option == 'any':
                    keyword = f'({" | ".join(keyword)})'
                elif option == 'all':
                    keyword = f'({" ".join(keyword)})'
                else:
                    raise ValueError('option must be any or all')
            host_param = f'+site:{host}' if host is not None else ''
            time_span_param = (
                f'&gpc=stf={int(time.mktime(time.strptime(start_time, "%Y-%m-%d %H:%M:%S")))},'
                f'{int(time.mktime(time.strptime(end_time, "%Y-%m-%d %H:%M:%S")))}|stftype=2'
            ) if start_time and end_time else ''

            url = f'https://www.baidu.com/s?ie=utf-8&f=8&rsv_bp=1&rsv_idx=1&tn=baidu&word={keyword}{host_param}&pn={page-1}0{time_span_param}'
        elif self.config == 'cnhubei':
            url = f'http://www.cnhubei.com/s?alias=&wd={" ".join(keyword)}&page={page}'
        elif self.config == 'sina':
            url = f'http://search.sina.com.cn/?q={keyword}&ie=utf-8&c=news&range=title&sort=time&page={page}'
        elif self.config == 'taihainet':
            url = f'http://app.taihainet.com/?app=search&action=search&type=all&wd={keyword}&order=time&page={page}'
        elif self.config == 'xinhuanet':
            url = f'http://so.news.cn/getNews?keyword={keyword}&curPage={page}&sortField=0&searchFields=1&lang=cn'
        elif self.config == 'stnn':
            url = f'http://app.stnn.cc/?app=search&controller=index&action=search&type=all&wd={keyword}&order=rel&page={page}'
        elif self.config == 'bbc':
            url = f'https://www.bbc.co.uk/search/more?page={page}&q={" ".join(keyword)}&filter=news&suggid='
        return url
    
    def parse(self, soup: BeautifulSoup):
        return getattr(search, self.config)(soup)


class Indexer:
    def __init__(self):
        pass

    def url(self, site, page=0):
        if site == 'qq':
            return f'https://pacaio.match.qq.com/irs/rcd?cid=137&token=d0f13d594edfc180f5bf6b845456f3ea&id=&ext=top&page={page}'
        elif site == 'sina':
            return f'https://news.sina.com.cn'
        elif site == 'sohu':
            return f'http://www.sohu.com'
        elif site == '163':
            return f'https://www.163.com'
        elif site == 'cankaoxiaoxi':
            return f'http://www.cankaoxiaoxi.com'
        else:
            raise ValueError(f'{site} is not supported now')
    
    _alias = {
        'qq': 'qq',
        'sina': 'sina',
        'sohu': 'sohu',
        '163': 'netease',
        'cankaoxiaoxi': 'cankaoxiaoxi',
    }
    def parse(self, response, site):
        if site in self._alias:
            return getattr(index, self._alias[site])(response)


class Parser:
    def __init__(self):
        pass

    _alias = {
        'baijiahao.baidu.com': 'baijiahao',
        'sina.com.cn': 'sina',
        'taihainet.com': 'taihainet',
        'sohu.com': 'sohu',
        '163.com': 'netease',
        'qq.com': 'qq',
        'huanqiu.com': 'huanqiu',
        'people.com.cn': 'people',
        'takungpao.com': 'takungpao',
        'cankaoxiaoxi.com': 'cankaoxiaoxi',
        'chinanews.com': 'chinanews',
        'cctv.com': 'cctv',
        '81.cn': '_81',
        'southcn.com': 'southcn',
        'china.com': 'china',
        'thepaper.cn': 'thepaper',
        'stnn.cc': 'stnn',
        'xinhuanet.com': 'xinhuanet',
        'cnr.cn': 'cnr',
        'cri.cn': 'cri',
        'cnhubei.com': 'cnhubei',
        'bbc.com': 'bbc',
        'bbc.co.uk': 'bbc',
    }
    def __call__(self, soup: BeautifulSoup, netloc, tld):
        if netloc in self._alias:
            return getattr(parse, self._alias[netloc])(soup)
        elif tld in self._alias:
            return getattr(parse, self._alias[tld])(soup)
