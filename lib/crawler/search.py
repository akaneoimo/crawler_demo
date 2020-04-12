def baidu(soup):
    return [div.h3.a.get('href') for div in soup.select('#content_left div.result')]


def search_sina(soup):
    result_list = soup.find_all('div', class_='box-result clearfix')
    url_list = [result.find('a').get('href') for result in result_list]
    return url_list


def search_taihainet(soup):
    result_list = soup.find('dl', class_='search-list').find_all('dd')
    url_list = [result.find('div', class_='article title').find('a').get('href') for result in result_list]
    return url_list


def search_xinhuanet(soup):
    return [result['url'] for result in json.loads(soup.text)['content']['results']]


def search_stnn(soup):
    return [li.h3.a.get('href') for li in soup.select('div.search-result-list li')]


def cnhubei(soup):
    return [box.h2.a.get('href') for box in soup.select('#mainContent div.search_res')]


def bbc(soup):
    return [box.select_one('h1 a').get('href') for box in soup.select('ol.search-results li')]
