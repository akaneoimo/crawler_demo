import json

from .utils import clean, simplify_url


def qq(soup):
    data = json.loads(soup.text)
    return [{'url': d['vurl'], 'title': d['title'], 'category': d['category_chn'], 'publish_time': d['publish_time']} for d in data['data']]


def sina(soup):
    return [{'url': a.get('href'), 'title': clean(a.text)} for a in soup.select('a') if a.get('href') and a.get('href').endswith('.shtml') and len(clean(a.text)) > 10]


def sohu(soup):
    return [{'url': simplify_url(a.get('href')), 'title': clean(a.text)} for a in soup.select('a') if a.get('href') and a.get('href').startswith('http://www.sohu.com/a/') and len(clean(a.text)) > 10]


def netease(soup):
    return [{'url': a.get('href'), 'title': clean(a.text)} for a in soup.select('a') if a.get('href') and a.get('href').endswith('.html') and len(clean(a.text)) > 10]


def cankaoxiaoxi(soup):
    return [{'url': a.get('href'), 'title': clean(a.text)} for a in soup.select('a') if a.get('href') and a.get('href').endswith('.shtml') and a.get('href').startswith('http://www.cankaoxiaoxi.com/') and len(clean(a.text)) > 10]
