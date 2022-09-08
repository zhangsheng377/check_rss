import logging
import re
import sched
import time
import threading

import requests

from UTILS.config import LOGGING_LEVEL, VERSION
from UTILS.config_ftqq import ftqq_sendkey
from UTILS.db_sheets import get_rss, get_rsses, update_one_rss
from UTILS.utils import check_rss, parse_rss

logging.getLogger().setLevel(LOGGING_LEVEL)

schdule = sched.scheduler(time.time, time.sleep)

rss_locks = {}


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


def handle_rss(rss_url):
    with rss_locks[rss_url]:
        try:
            rss = parse_rss(rss_url)
            rss_entry = rss.entries[0]
            rss_feed_title = rss.feed.title
            db_rss = get_rss(rss_url)
            if check_rss_update(db_rss, rss_entry):
                if update_rss(rss_url, rss_entry.id, rss_entry.title):
                    logging.info(f'更新成功: {rss_url} {rss_feed_title}\n')

                    old_check_element_value, check_element_value = get_check_element_value(db_rss, rss_entry)

                    msg_title = f"我的监测任务[{rss_feed_title}]"
                    msg_desp = f"{check_element_value} <-- {old_check_element_value}\n\n[详情链接]({rss_entry.link})"
                    r = requests.post(f'https://sctapi.ftqq.com/{ftqq_sendkey}.send',
                                      data={'title': msg_title, 'desp': msg_desp})
                    print(r)
                else:
                    logging.debug(f'更新失败: {rss_url} {rss_feed_title}\n')
            if db_rss and db_rss.get('feed_title', '') != rss_feed_title:
                update_rss(rss_url, rss_entry.id, rss_entry.title)
        except Exception as e:
            logging.warning("handle_rss error.", e)

        schdule.enter(60 * 30, 0, handle_rss, (rss_url,))


def discover_rss():
    try:
        rsses = get_rsses()
        for rss in rsses:
            rss_url = rss['_id']
            # print(rss_url)
            if rss_url not in rss_locks:
                logging.info(f"discover rss: {rss_url}")
                if check_rss(rss_url):
                    rss_locks[rss_url] = threading.Lock()
                    schdule.enter(0, 0, handle_rss, (rss_url,))
                else:
                    logging.warning(f"rss: {rss_url} can not parse!")
    except Exception as e:
        logging.warning("discover_rss error.", e)
    schdule.enter(60, 0, discover_rss, )


if __name__ == '__main__':
    # rss_url = 'http://192.168.10.5:1200/bilibili/user/video/2267573'
    # rss_url = 'http://192.168.10.5:1200/jd/price/10056870227270'
    # print(f"check_rss: {check_rss(rss_url)}")
    # print(f"parse_rss: {parse_rss(rss_url)}")

    # print(f"get_rss: {get_rss(rss_url)}")

    # if insert_rsses(document={'_id': rss_url, 'last_uuid': '', 'last_title': ''}):
    #     print("insert_rsses success")
    # else:
    #     print("insert_rsses false")

    # rss_urls = ['http://192.168.10.5:1200/bilibili/user/video/2267573',
    #             'http://192.168.10.5:1200/jd/price/10056870227270',
    #             ]
    # for rss_url in rss_urls:
    #     if insert_rsses(document={'_id': rss_url, 'last_uuid': '', 'last_title': ''}):
    #         print("insert_rsses success")
    #     else:
    #         print("insert_rsses false")

    logging.info(f"VERSION: {VERSION}")
    schdule.enter(0, 0, discover_rss, )
    schdule.run()
