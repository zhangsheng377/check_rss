import json
import logging
import re
from xml.dom import minidom

import PyRSS2Gen
import feedparser
import requests

from UTILS.config import bz_chan_addr
from UTILS.config_ftqq import ftqq_sendkey, bz_sendkey

from UTILS.db_sheets import update_one_rss


def parse_rss(url):
    return feedparser.parse(url)


def check_rss(url):
    result = None
    try:
        result = parse_rss(url)
    except Exception as e:
        print(e)
    if not result:
        return False
    if result.status != 200:
        logging.debug(f"rss: {url} can not parse! status: {result.status}")
        return False
    return True


def update_rss(rss_url, uuid, title):
    _filter = {'_id': rss_url}
    _update = {'$set': {'last_uuid': uuid,
                        'last_title': title}}
    result = update_one_rss(filter=_filter, update=_update)
    if result is not None and result.modified_count > 0:
        return True
    return False


def update_rss_feed_title(rss_url, feed_title):
    _filter = {'_id': rss_url}
    _update = {'$set': {'feed_title': feed_title}}
    result = update_one_rss(filter=_filter, update=_update)
    if result is not None and result.modified_count > 0:
        return True
    return False


def get_check_element_value(db_rss, rss_entry):
    check_element = db_rss.get('check_element', 'uuid')
    if check_element == 'uuid':
        return db_rss['last_uuid'], rss_entry.id
    elif check_element == 'title':
        return db_rss['last_title'], rss_entry.title
    return None, None


def check_rss_update(db_rss, rss_entry):
    if not db_rss:
        return True
    old_check_element_value, check_element_value = get_check_element_value(db_rss, rss_entry)
    return old_check_element_value != check_element_value


def need_download(db_rss):
    need_download_str = db_rss.get('need_download', 'not_download')
    return need_download_str == 'need_download'


def send_notice(rss_entry, rss_feed_title, last_title):
    header = {"Content-Type": "application/json"}
    proxies = {}
    msg_title = f"我的监测任务[{rss_feed_title}]"
    msg_desp = f"{rss_entry.title} <-- {last_title}\n\n[详情链接]({rss_entry.link})"
    message = {
        "msgtype": "markdown",
        "title": msg_title,
        "desp": msg_desp
    }
    # r = requests.post(f'https://sctapi.ftqq.com/{ftqq_sendkey}.send',
    #                   data={'title': msg_title, 'desp': msg_desp})
    message_json = json.dumps(message)
    r = requests.post(f'http://{bz_chan_addr}/{ftqq_sendkey}.send',
                      data=message_json, headers=header, proxies=proxies)
    logging.info(r)
    webhook = f"http://{bz_chan_addr}/{bz_sendkey}.send"
    image_url = None
    try:
        pattern = re.compile("""<img[^>]+src=["']([^'"<>]+)["'][^<>]+/?>""")
        summary = rss_entry.summary
        image_urls = pattern.findall(summary)
        if len(image_urls) > 0:
            image_url = image_urls[0]
    except Exception as e:
        print(e)
    message = {
        "msgtype": "news",
        "articles": [
            {
                "title": rss_entry.title,
                "description": f" <-- {last_title}\n\n【{rss_feed_title}】",
                "url": rss_entry.link,
                "picurl": image_url
            }
        ]
    }
    message_json = json.dumps(message)
    r = requests.post(url=webhook, data=message_json, headers=header, proxies=proxies)
    logging.info(r)


def save_rss_items(rss_items):
    with open('/mnt/nfs/download/myrss/myrss.xml', "w", encoding='utf-8') as rss_file:
        rss_file.write(f"<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<rss version=\"2.0\">")
        for feed_title in rss_items:
            channel_xml = make_rss_channel_xml(feed_title, rss_items[feed_title])

            rss_file.write(f"\n{channel_xml}")
        rss_file.write(f"\n</rss>")
    # rss2gen.write_xml(open('/mnt/nfs/download/myrss/myrss.xml', "w", encoding='utf-8'),
    #                   encoding='utf-8')


def make_rss_channel_xml(feed_title, items):
    rss2gen = PyRSS2Gen.RSS2(title=feed_title, link='', description='', items=items)
    rss_xml = rss2gen.to_xml(encoding='utf-8')
    dom = minidom.parseString(rss_xml)
    elem = dom.documentElement
    channel = elem.getElementsByTagName('channel')[0]
    channel_xml = channel.toxml()
    return channel_xml
