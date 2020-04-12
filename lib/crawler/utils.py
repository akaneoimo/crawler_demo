import datetime
import re
from urllib.parse import urlparse, parse_qs, urlencode

import tldextract


def extract_url(url):
    o = urlparse(url)
    tld = tldextract.extract(o.netloc).registered_domain
    if o.netloc == 'baijiahao.baidu.com':
        query = parse_qs(o.query)
        url = f'{o.scheme}://{o.netloc}{o.path}?{urlencode({"id": query["id"][0]})}'
    return {'tld': tld, 'netloc': o.netloc, 'url': url}


def simplify_url(url, key=None):
    o = urlparse(url)
    query = parse_qs(o.query)
    if key is None:
        return f'{o.scheme}://{o.netloc}{o.path}'
    elif query.get(key):
        return f'{o.scheme}://{o.netloc}{o.path}?{urlencode({f"{key}": query[f"{key}"][0]})}'
    else:
        return url


def clean(text):
    return re.sub('\s+', ' ', re.sub('[\ufeff\u3000\xa0\x7f\n]', ' ', text.strip())).strip()


def strptime(date_string, candidate_formats=[]):
    if isinstance(date_string, int):
        return datetime.datetime.utcfromtimestamp(date_string)
    if isinstance(candidate_formats, str):
        candidate_formats = [candidate_formats]
    for fmt in candidate_formats or ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y年%m月%d日 %H:%M:%S', '%Y.%m.%d %H:%M', '%Y年%m月%d日 %H:%M', '%Y年%m月%d日%H:%M', '%Y/%m/%d %H:%M:%S', '%Y年%m月%d日', '%Y-%m-%d']:
        try:
            return datetime.datetime.strptime(date_string, fmt)
        except:
            pass
    raise ValueError(f"no date format matches '{date_string}'")
