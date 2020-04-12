import re
import json
from urllib.parse import urlparse
import time
from datetime import timedelta

import requests
from bs4 import BeautifulSoup, NavigableString
import chardet

from .utils import clean, strptime


def baijiahao(soup):
    time_ = strptime(soup.select_one('meta[itemprop=dateUpdate]').get('content').strip())
    title = soup.select_one('div.article-title').text
    source = (soup.select_one('p.source-name') or soup.select_one('p.author-name')).text
    text = ''.join([clean(p.text) for p in soup.find('div', class_='article-content').find_all('p')])
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text)}


def sina(soup):
    try:
        [s.extract() for s in soup(['script', 'style'])]
        title = (soup.select_one('h1.main-title') or soup.select_one('h1#main_title')).text.strip()
        date_source = soup.select_one('.date-source') or soup.select_one('.time-source')
        time_ = strptime((date_source.select_one('span.date') or date_source.select_one('span.titer')).text)
        source = (date_source.select_one('span.source a') or date_source.select_one('a') or date_source.select_one('span.source')).text
        content_box = soup.select_one('#article') or soup.select_one('#artibody')
        text = ''.join([clean(p.text) for p in content_box.select('p:not(.article-notice)')])
    except:
        [s.extract() for s in soup(['script', 'style'])]
        title = soup.select_one('h1#artibodyTitle').text.strip()
        date_source = soup.select_one('.date-source') or soup.select_one('.time-source')
        try:
            time_ = strptime(date_source.contents[0].strip())
            source = date_source.contents[1].text.strip()
        except:
            try:
                time_ = strptime(soup.select_one('#pub_date').text)
            except:
                time_ = strptime(soup.select_one('#pub_date').text)
            source = (soup.select_one('#media_name') or soup.select_one('span.linkRed02')).text.strip()
        content_box = soup.select_one('#article') or soup.select_one('#artibody')
        text = ''.join([clean(p.text) for p in content_box.select('p:not(.article-notice)')])
    # fields:media,source,labels_show,commentid,comment_count,title,ltitle,url,info,thumbs,thumb,ctime,reason,category,video_id,hotTag,img_count,gif,live_stime,live_etime,media_id,summary,orgUrl,show,intro,docid,playtimes,video_height,video_width,time_length,user_icon,uid
    # api = f'https://cre.mix.sina.com.cn/api/v3/get?callback=data&cateid=sina_all&cre=tianyi&mod=pcpager_inter&merge=3&statics=1&this_page=1&length=40&up=0&down=0&pageurl={url}&imp_type=2&action=0&fields=url&tm=1566786743&offset=0&_={int(round(time.time() * 1000))}'
    # try:
    #     related_urls = [d['url'] for d in json.loads(requests.get(api).content.decode('utf-8')[6:-3])['data']]
    # except:
    #     related_urls = []
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text)}


def sohu(soup):
    [s.extract() for s in soup(['script', 'style'])]
    try:
        title = (soup.select_one('div.text-title h1') or soup.select_one('h1.title')).text.strip()
        try:
            time_ = strptime(int(soup.select_one('#news-time').get('data-val')) // 1000)
        except:
            time_ = strptime(soup.select_one('span.datetime').text)
        source = (soup.select_one('[data-role=original-link] a') or soup.select_one('span.source')).text.strip()
        try:
            text = soup.select_one('#mp-editor').text
        except:
            text = ''.join([clean(p.text) for p in soup.select('#mp-editor p') or soup.select('div.content p')])
    except:
        title = (soup.select_one('h1[itemprop=headline]') or soup.select_one('div.title h1') or soup.select_one('h1')).text.strip()
        try:
            time_ = strptime(soup.select_one('#pubtime_baidu').text)
        except:
            time_ = strptime((soup.select_one('.time') or soup.select_one('.sourceTime .r')).text)
        try:
            source = soup.select_one('#media_span').text.strip()
        except:
            source = ''
        text = soup.select_one('#contentText').text
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text)}


def qq(soup):
    try:
        time_ = strptime((re.search(r'"pubtime":(\s)?"(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})"', soup.text) or re.search(r"pubtime:(\s)?'(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})'", soup.text)).group(2))
        source = re.search(r'"media":(\s)?"([^"]+)"', soup.text).group(2)
        title = soup.select_one('div.LEFT h1').text.strip()
        text = ''.join([clean(p.text) for p in soup.select('div.content-article p')])
    except:
        try:
            time_ = strptime(re.search(r'"pub_time":(\s)?"(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})"', soup.text).group(2))
            source = re.search(r'"source":(\s)?"([^"]+)"', soup.text).group(2).encode('utf-8').decode('unicode_escape')
            title = re.search(r'"longtitle":(\s)?"([^"]+)"', soup.text).group(2).encode('utf-8').decode('unicode_escape')
            soup = BeautifulSoup(re.search(r'"cnt_html":(\s)?"([^"]+)"', soup.text).group(2), config.parser)
            text = clean(soup.text.encode('utf-8').decode('unicode_escape'))
        except:
            [s.extract() for s in soup(['script', 'style'])]
            soup.select_one('div.rv-js-root') and soup.select_one('div.rv-js-root').extract()
            try:
                time_ = strptime((soup.select_one('.a_time') or soup.select_one('.article-time') or soup.select_one('.pubTime')).text)
            except:
                time_ = strptime(soup.select_one('.info').contents[0])
            source = (soup.select_one('.a_source') or soup.select_one('span[bosszone=jgname] a') or soup.select_one('span[bosszone=jgname]') or soup.select_one('.where')).text
            title = soup.select_one('h1').text
            text = soup.select_one('#Cnt-Main-Article-QQ').text
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text)}


def netease(soup):
    [s.extract() for s in soup(['script', 'style'])]
    title = (soup.select_one('#epContentLeft h1') or soup.select_one('.article_title h2')).text.strip()
    try:
        date_source = soup.select_one('div.post_time_source')
        time_ = strptime(re.search(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}', date_source.text.strip()).group())
        source = date_source.select_one('#ne_article_source').text
    except:
        time_ = strptime(soup.select_one('#contain').get('data-ptime'))
        source = soup.select_one('.time span:nth-child(3)').text
    text = ''.join([clean(p.text) for p in soup.select('#endText p') or soup.select('#content p')])
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text)}


def taihainet(soup):
    title = (soup.select_one('hgroup.wrapper') or soup.select_one('h1.topic')).text.strip()
    try:
        time_ = strptime((soup.select_one('publish_time') or soup.select_one('#pubtime_baidu') or soup.select_one('time')).text.strip())
        source = (soup.select_one('span.source_baidu a') or soup.select_one('span.source_baidu')).text.strip()
    except:
        time_source = find_time_source_by_regex(soup.select_one('.page-info').text)
        time_ = strptime(time_source[0])
        source = time_source[1]
    content_box = soup.select_one('div.article-content')
    text = ''.join([clean(p.text) for p in content_box.select('p')])
    pages = soup.select_one('div.article-page')
    next_page_url = None
    if pages is not None:
        link = pages.select_one('td:nth-last-child(2)').find('a')
        if link.text == '下一页' and link.get('class') != ['disable']:
            next_page_url = link.get('href')
    related_urls = [link.a.get('href') for link in soup.select('div.relative-news header')]
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text), 'next': next_page_url}


def huanqiu(soup):
    scripts = ''.join([s.extract().text for s in soup('script')])
    title = (soup.select_one('h1.tle') or soup.select_one('.t-container-title h3') or soup.select_one('.container-title h3')).text.strip()
    try:
        time_ = strptime((soup.select_one('span.la_t_a') or soup.select_one('.time')).text.strip())
    except:
        time_ = strptime(int(re.search(r'ctime(\s)?:(\s)?"(\d+)"', scripts).group(3)) // 1000) + timedelta(hours=8)
    try:
        source = (soup.select_one('span.la_t_b') or soup.select_one('span.source span') or soup.select_one('span.source a')).text.strip()
    except:
        source = re.search(r'source(\s)?:(\s)?\{"name":(\s)?"([^"]+)"', scripts).group(4)
    text = ''.join([clean(p.text) for p in (soup.select('div.la_con p') or soup.select('article p'))if p.get('style') != 'text-align: center;'])
    related_urls = [li.a.get('href') for li in (soup.select('div.la_xiangguan_news li') or soup.select('div.l-aboutNews li'))]
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text)}

def people(soup):
    [s.extract() for s in soup(['script', 'style'])]
    try:
        title = soup.select_one('h1').text.strip()
        try: 
            time_ = strptime(re.search(r'\d{4}年\d{2}月\d{2}日\d{2}:\d{2}', (soup.select_one('div.box01 div.fl') or soup.select_one('p.p1') or soup.select_one('p.sou')).text).group())
        except:
            time_ = strptime(soup.select_one('#p_publishtime').text)
        source = (soup.select_one('div.box01 div.fl a') or soup.select_one('p.p1 a') or soup.select_one('p.sou a') or soup.select_one('#p_origin a')).text.strip()
        [s.extract() for s in soup.select('div[align=center]')]
        [s.extract() for s in soup.select('#p_content title')]
        [s.extract() for s in soup(['center', 'u'])]
        text = ''.join([clean(p.text) for p in soup.select('div#rwb_zw p') or soup.select('div.show_text p') or soup.select('div.box_con p') or soup.select('#p_content')])
    except:
        title = soup.select_one('h1').text.strip()
        regex_obj = re.search(r'《\s*(.+)\s*》\s*（\s*(\d{4}年\d{2}月\d{2}日)', soup.select_one('div.lai').text)
        time_ = strptime(regex_obj.group(2))
        source = regex_obj.group(1).strip()
        text = soup.select_one('#ozoom').text
    related_urls = [li.a.get('href') for li in soup.select('#rwb_xgxw li')]
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text)}


def takungpao(soup):
    [s.extract() for s in soup('script')]
    next_page_url = None
    try:
        try:
            title = (soup.select_one('h2.tkp_con_title') or soup.select_one('h1.tpk_con_tle')).text.strip()
            date_source = soup.select_one('div.tkp_con_author') or soup.select_one('h1.article_info_l')
            time_ = strptime(date_source.select_one('span:first-child').text.strip())
            source = date_source.select_one('span:last-child').text.strip()
            text = ''.join([clean(p.text) for p in soup.select('div.tkp_content p')])
        except:
            title = (soup.select_one('h2.tkp_con_title') or soup.select_one('h1.tpk_con_tle')).text.strip()
            time_ = strptime(soup.select_one('.article_info_l .fl_dib:nth-child(1)').contents[0])
            source = soup.select_one('.article_info_l .fl_dib:nth-child(2)').text.lstrip('来源：').rstrip('|')
            text = ''.join([clean(p.text) for p in soup.select('div.tpk_text p')])
    except:
        try:
            title = soup.select_one('div.article h1').text.strip()
            time_ = strptime((soup.select_one('#pubtime_baidu') or soup.select_one('span.time')).text.strip())
            source = (soup.select_one('#source_baidu') or soup.select_one('div.articleInforL span:nth-child(2)')).text.lstrip('来源：')
            text = ''.join([clean(p.text) for p in soup.select('div.text p')])
            pages = soup.select_one('div.filpBox')
            if pages and [c for c in pages.contents if c != '\n']:
                link = pages.select_one(':nth-last-child(1)')
                if link.text == '下一页' and link.get('class') != ['disable']:
                    next_page_url = link.get('href')
        except Exception as e:
            title = soup.select_one('#title_tex').text
            regex_obj = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s*来源：(.+)', soup.select_one('#time_tex').text.strip())
            time_ = strptime(regex_obj.group(1))
            source = regex_obj.group(2)
            text = ''.join([clean(p.text) for p in soup.select('#details-con p')])
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text), 'next': next_page_url}


def cankaoxiaoxi(soup):
    [s.extract() for s in soup('script')]
    next_page_url = None
    title = (soup.select_one('h1.articleHead') or soup.select_one('.bg-content h1') or soup.select_one('h2.YH') or soup.select_one('h2')).text.strip()
    try:
        time_ = strptime((soup.select_one('#pubtime_baidu') or soup.select_one('span.__BAIDUNEWS__tm')).text.strip())
        source = re.search(r'来源：(\S+)', (soup.select_one('#source_baidu') or soup.select_one('span.__BAIDUNEWS__source')).text.strip()).group(1)
    except:
        regex_obj = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s*来源：(\S+)\s*', soup.select_one('span.cor666').text)
        time_ = strptime(regex_obj.group(1))
        source = regex_obj.group(2)
    text_box = soup.select_one('div.articleText') or soup.select_one('#ctrlfscont') or soup.select_one('div.__BAIDUNEWS__content')
    [a.extract() for a in text_box(['a', 'strong'])]
    text = text_box.text
    pages = soup.select_one('div.page')
    if pages and [c for c in pages.contents if c != '\n']:
        link = pages.select_one('li:nth-last-child(1) a')
        if link.text == '下一页':
            next_page_url = link.get('href')
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text), 'next': next_page_url}


def chinanews(soup):
    [s.extract() for s in soup('script')]
    next_page_url = None
    try:
        title = (soup.select_one('#cont_1_1_2 h1') or soup.select_one('#text h1.left_bt')).text.strip()
        obj = re.search(r'(\d{4}年\d{2}月\d{2}日\s+\d{2}:\d{2})\s+来源：(\S+)', (soup.select_one('div.left-t') or soup.select_one('div.left_time')).text.strip())
        time_ = strptime(obj.group(1))
        source = obj.group(2)
        text = ''.join([clean(p.text) for p in soup.select('div.left_zw p')])
    except:
        title = (soup.select_one('#cont_1_1_2 h1') or soup.select_one('#text h1.left_bt') or soup.select_one('.left_bt h1')  or soup.select_one('.left_bt ul')).text.strip()
        obj = re.search(r'(\d{4}年\d{2}月\d{2}日\s+\d{2}:\d{2})\s+来源：(\S+)', (soup.select_one('div.left-t') or soup.select_one('div.left_time')).text.strip())
        time_ = strptime(obj.group(1))
        source = obj.group(2)
        text = ''.join([clean(p.text) for p in soup.select('div.left_zw p')])
        pages = soup.select_one('#function_code_page')
        if pages and [c for c in pages.contents if c != '\n']:
            link = pages.select_one('a:nth-last-child(1)')
            if link and link.text == '下一页':
                next_page_url = link.get('href')
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text), 'next': next_page_url}

def cctv(soup):
    [s.extract() for s in soup('script')]
    title = (soup.select_one('div.cnt_bd h1') or soup.select_one('div.bd h1')).text.strip()
    try:
        obj = re.search(r'来源：(\S+)\s+(\d{4}年\d{2}月\d{2}日\s+\d{2}:\d{2})', soup.select_one('span.info i').text.strip())
        time_ = strptime(obj.group(2))
        source = obj.group(1)
    except:
        obj = re.search(r'(\d{4}年\d{2}月\d{2}日)\s+来源：(\S+)', soup.select_one('.date_left_yswp').text.strip())
        time_ = strptime(obj.group(1))
        source = obj.group(2)
    text = ''.join([clean(p.text) for p in soup.select('div.cnt_bd p:not([align=center])') or soup.select('#page_body div.col_650 div.bd p:not([align=center])')])
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text)}


def _81(soup):
    [s.extract() for s in soup('script')]
    try:
        title = (soup.select_one('div.article-header h1') or soup.select_one('div.title h1')).text.strip()
        time_ = strptime((soup.select_one('i.time_') or soup.select_one('i.time') or soup.select_one('span.last')).text.strip())
        source = re.search(r'来源：(\S+)', soup.select_one('div.info span:first-child').text.strip()).group(1)
        text = ''.join([clean(p.text) for p in soup.select('#article-content p') or soup.select('#content p')])
        pages = soup.select_one('#displaypagenum')
        if pages and [c for c in pages.contents if c != '\n']:
            link = pages.select_one('a:nth-last-child(2)')
            if link and link.text == '下一页':
                try:
                    prefix = '/'.join(o.path.strip('/').split('/')[:-1])
                    text += parse_81(f"{o.scheme}://{o.netloc}/{prefix}/{link.get('href')}")['text']
                except:
                    pass
    except:
        title = ' '.join([t for t in soup.select_one('#APP-Title') if isinstance(t, NavigableString)])
        time_ = strptime(re.search(r'\d{4}年\d{1,2}月\d{1,2}日', soup.select_one('.nav-site').text).group())
        source = soup.select_one('.nav-site .hidden-md-down').text.strip()
        text = ''.join([clean(p.text) for p in soup.select('#APP-Content p')])
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text)}


def southcn(soup):
    [s.extract() for s in soup('script')]
    title = (soup.select_one('#article_title') or soup.select_one('#articleTitle') or soup.select_one('#article h1') or soup.select_one('#ScDetailTitle')).text.strip()
    try:
        try:
            time_ = strptime((soup.select_one('#pubtime_baidu') or soup.select_one('span.time')).text.strip())
        except:
            time_ = strptime(soup.select_one('.pubtime').get('data-time'))
        try:
            source = re.search(r'来源[：:]\s*(\S+)', (soup.select_one('#source_baidu') or soup.select_one('span.source')).text.strip()).group(1)
        except:
            try:
                source = (soup.select_one('.nfhname') or soup.select_one('#source_baidu')).text.strip()
            except:
                source = ''
    except :
        regex_obj = re.search(r'(\S+)\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', soup.select_one('.p-information').text)
        time_ = strptime(regex_obj.group(2))
        source = regex_obj.group(1)
    text = ''.join([clean(p.text) for p in soup.select('#content p') or soup.select('.article p') or soup.select('#ScDetailContent p')])
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text)}


def china(soup):
    title = (soup.select_one('#chan_newsTitle') or soup.select_one('h1.article-main-title') or soup.select_one('h1')).text.strip()
    try:
        time_ = strptime(soup.select_one('span.time').text.strip())
        source = soup.select_one('span.source').text.strip()
    except:
        try:
            time_ = strptime(soup.select_one('#chan_newsInfo').contents[2].strip())
            soup.select_one('#chan_newsInfo span.chan_newsInfo_comment') and soup.select_one('#chan_newsInfo span.chan_newsInfo_comment').extract()
            try:
                source = soup.select_one('#chan_newsInfo').contents[3].text
            except:
                source = ''
        except:
            regex_obj = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*(\S+)', soup.select_one('#chan_newsInfo').contents[2].strip())
            time_ = strptime(regex_obj.group(1))
            source = regex_obj.group(2)
    text = ''.join([clean(p.text) for p in soup.select('#chan_newsDetail p')])
    # pages = soup.select_one('#chan_multipageNumN')
    # if pages and [c for c in pages.contents if c != '\n']:
    #     link = pages.select_one('a:nth-last-child(1)')
    #     if link and link.text == '下一页':
    #         try:
    #             prefix = '/'.join(o.path.strip('/').split('/')[:-1])
    #             next_page_url = f"{o.scheme}://{o.netloc}/{prefix}/{link.get('href')}"
    #         except:
    #             pass
    related_urls = [h3.a.get('href') for h3 in soup.select('#chan_xgxw h3.tit')]
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text)}


def thepaper(soup):
    [s.extract() for s in soup('script')]
    title = soup.select_one('h1.news_title').text.strip()
    regex = re.compile(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})(\s+来源：(\S+))?')
    try:
        obj = regex.search(clean(soup.select_one('div.news_about p:nth-child(2)').text))
        time_ = strptime(obj.group(1))
        source = obj.group(3)
    except:
        obj = regex.search(clean(soup.select_one('div.news_about p:nth-child(1)').text))
        time_ = strptime(obj.group(1))
        source = obj.group(3)
    if not source:
        source = soup.select_one('div.news_about p:nth-child(1)').text
    text = soup.select_one('div.news_txt').text
    # newsid = re.search(r'newsDetail_forward_(\d+)', url)
    # if newsid:
    #     newsid = newsid.group(1)
    #     api = 'https://www.thepaper.cn/async_recommend.jsp?contid=%s' % newsid
    #     res = BeautifulSoup(requests.get(api).content.decode('utf-8'), config.parser)
    #     related_urls = [f"https://www.thepaper.cn/{div.a.get('href')}" for div in res.select('div.ctread_name')]
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text)}


def stnn(soup):
    [s.extract() for s in soup('script')]
    title = (soup.select_one('h1.article-title') or soup.select_one('h1.ui-article-title')).text.strip()
    time_ = strptime((soup.select_one('span.date') or soup.select_one('publish_time') or soup.select_one('time')).text.strip())
    try:
        source = soup.select_one('span.source').text.strip()
    except:
        source = ''
    text = (soup.select_one('div.article-content') or soup.select_one('#content-show')).text
    # related_urls = [li.a.get('href') for li in soup.select('div.rel-news li')]
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text)}


def xinhuanet(soup):
    [s.extract() for s in soup('script')]
    next_page_url = None
    title = soup.select_one('div.h-title')
    if title:
        title = title.text.strip()
        time_ = strptime((soup.select_one('span.h-time_') or soup.select_one('span.h-time')).text.strip())
        try:
            source = (soup.select_one('span.aticle-src') or soup.select_one('#source')).text.strip()
        except:
            source = '新华网'
        text = ''.join([p.text for p in soup.select('#p-detail p:not([align=left]):not([align=center])') if not p.select_one('font')])
    else:
        title = (soup.select_one('#title') or  soup.select_one('#Title')).text.strip()
        try:
            time_ = strptime((soup.select_one('span.time_') or soup.select_one('span.time') or soup.select_one('#pubtime')).text.strip())
            temp_source = (soup.select_one('#source') or soup.select_one('#from')).text.strip()
            regex_obj = re.search(r'来源[：:]\s*(\S+)', temp_source)
            source = regex_obj.group(1) if regex_obj else temp_source
        except:
            time_source = soup.select_one('body > table:nth-child(2) > tr:nth-child(1) > td:nth-child(2) > table:nth-child(1) > tr:nth-child(2) > td').text.strip()
            regex_obj = re.search(r'(\d{4}年\d{2}月\d{2}日 \d{2}:\d{2}:\d{2})\s*来源[：:]\s*(\S+)', time_source)
            time_ = strptime(regex_obj.group(1))
            source = regex_obj.group(2)
        pages = soup.select_one('#div_currpage') and soup.select_one('#div_currpage').extract()
        soup.select_one('#div_page_roll1') and soup.select_one('#div_page_roll1').extract()
        text = ''.join([p.text for p in soup.select('div.article p:not([align=left]):not([align=center])') if not p.select_one('font')]) or ''.join([p.text for p in soup.select('#content') or soup.select('#Content')])
        if pages and [c for c in pages.contents if c != '\n']:
            link = pages.select_one('a:nth-last-child(1)')
            if link and link.text == '下一页':
                next_page_url = link.get('href')
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text), 'next': next_page_url}


def cnr(soup):
    [s.extract() for s in soup('script')]
    try:
        title = (soup.select_one('article h2') or soup.select_one('div.article h2') or soup.select_one('div.wh635 h1') or soup.select_one('div.article h1') or soup.select_one('.wh645 p.lh30') or soup.select_one('p.lh40') or soup.select_one('h2.lh26') or soup.select_one('div.f24')).text
        try:
            try:
                time_ = strptime((soup.select_one('#pubtime_baidu') or soup.select_one('publish_time')).text.strip())
                source = (soup.select_one('#source_baidu a') or soup.select_one('span.source')).text.strip()
            except:
                try:
                    regex_obj = re.search(r'(\d{4}\.\d{2}\.\d{2} \d{2}:\d{2})\s*来源[:：](\S+)', soup.select_one('.author').text)
                    time_ = strptime(regex_obj.group(1))
                    source = regex_obj.group(2)
                except:
                    temp = (soup.select_one('p.lh30.left') or soup.select_one('p.lh20.left') or soup.select_one('span.lh20') or soup.select_one('p.lh26') or soup.select_one('div.lh26')).text
                    regex_obj = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*来源[:：]\s*(\S+)', temp) or re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\s*来源[:：]\s*(\S+)', temp)
                    time_ = strptime(regex_obj.group(1))
                    source = regex_obj.group(2)
            text = ''.join([p.text for p in soup.select('div.TRS_Editor p') or soup.select('div.contentText') or soup.select('div.sanji_left_text_3') if not p.select_one('font') and not p.get('align') == 'center'])
        except:
            time_ = strptime(soup.select_one('div.source span:nth-child(1)').text.strip())
            source = re.search(r'来源[:：]\s*(\S+)', soup.select_one('div.source span:nth-child(2)').text.strip()).group(1)
            text = ''.join([p.text if not p.select_one('font') else p.contents[0] for p in soup.select('div.TRS_Editor p') or soup.select('div.contentText')])
        related_urls = [h2.a.get('href') for h2 in soup.select('div.aboutLinks h2')]
    except:
        try:
            title = soup.select_one('#Title').text.strip()
            time_source = soup.select_one('#Time').text.strip()
            obj = re.search(r'(.+)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', time_source)
            time_ = strptime(obj.group(2))
            source = obj.group(1)
            text = soup.select_one('#Content').text
        except:
            title = soup.select_one('.bt').text.strip()
            regex_obj = re.search(r'(\S+)\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2})', soup.select_one('.ly').text)
            time_ = strptime(regex_obj.group(2))
            source = regex_obj.group(1)
            text = ''.join([p.text for p in soup.select('div.TRS_Editor p')])
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text)}


def cri(soup):
    [s.extract() for s in soup('script')]
    title = (soup.select_one('#goTop') or soup.select_one('#atitle') or soup.select_one('.news_ts_tit') or soup.select_one('#ctitle')).text.strip()
    try:
        try:
            time_ = strptime((soup.select_one('#acreatedtime') or soup.select_one('#pubtime_baidu')).text.strip())
        except:
            time_ = strptime(re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', soup.select_one('#acreatedtime').text).group())
        try:
            source = re.search(r'[来來]源[:：]\s*(\S+)', soup.select_one('#asource').text.strip()).group(1)
        except:
            source = soup.select_one('#source_baidu a').text.strip()
    except:
        try:
            regex_obj = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*\|?\s*来源[:：]\s*(\S+)\s*', (soup.select_one('div.news_ts_ly') or soup.select_one('div.signdate')).text)
            time_ = strptime(regex_obj.group(1))
            source = regex_obj.group(2)
        except:
            title = (soup.select_one('#goTop') or soup.select_one('#atitle') or soup.select_one('.news_ts_tit') or soup.select_one('#ctitle')).text.strip()
            regex_obj = re.search(r'(\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?)\s*\|?\s*來源[:：]\s*(\S+)\s*', (soup.select_one('div.news_ts_ly') or soup.select_one('div.signdate')  or soup.select_one('.article-info')).text)
            time_ = strptime(regex_obj.group(1))
            source = regex_obj.group(3)
    text = ''.join([p.text for p in soup.select('#abody p') or soup.select('#ccontent p')])
    return {'publish_time': time_, 'source': clean(source), 'title': clean(title), 'text': clean(text)}


def cnhubei(soup):
    time_ = strptime(re.search(r'发布时间：(\d{4}年\d{2}月\d{2}日\d{2}:\d{2})', soup.select_one('#lmy_information01 span:nth-child(1)').text).group(1))
    source = soup.select_one('#lmy_information01 div.information_box a:nth-child(3)').text
    title = soup.select_one('#lmy h1').text
    text = ''.join([p.text for p in soup.select('div.article_w p')])
    return {'publish_time': time_, 'source': source, 'title': clean(title), 'text': clean(text)}


def bbc(soup):
    time_ = strptime(int(soup.select_one('div.date.date--v2').get('data-seconds')))
    source = 'bbc'
    title = (soup.select_one('div.story-body h1') or soup.select_one('div.story-body h2.unit__title')).text
    text = ''.join([p.text for p in soup.select('div.story-body__inner p')])
    return {'publish_time': time_, 'source': source, 'title': clean(title), 'text': clean(text)}


def find_by_regex(string, regex, index):
    obj = re.search(regex, string)
    if obj:
        return {key: obj.group(value) for key, value in index.items()}
    else:
        return {}

source_regex = re.compile(r'[来來]源[:：]\s*(\S+)\s*')
def find_source_by_regex(string):
    regex_obj = source_regex.search(string)
    return regex_obj.group(1)


time_regex = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?)\s*')
def find_time_by_regex(string):
    regex_obj = time_regex.search(string)
    return regex_obj.group(1)


time_source_regex = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?)\s*[来來]源[:：]\s*(\S+)\s*')
def find_time_source_by_regex(string):
    regex_obj = time_source_regex.search(string)
    return regex_obj.group(1), regex_obj.group(3)
