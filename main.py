import logging
import sched
import subprocess
import time
import threading

import PyRSS2Gen

from UTILS.config import LOGGING_LEVEL, VERSION
from UTILS.db_sheets import get_rss, get_rsses
from UTILS.utils import check_rss, parse_rss, update_rss, update_rss_feed_title, check_rss_update, need_download, \
    send_notice, save_rss_items

logging.getLogger().setLevel(LOGGING_LEVEL)

schdule = sched.scheduler(time.time, time.sleep)

rss_locks = {}

my_rss_items = []


def handle_rss(rss_url):
    with rss_locks[rss_url]:
        try:
            rss = parse_rss(rss_url)
            if not rss or len(rss.entries) <= 0:
                logging.warning(f"rss parse failed. rss: {rss}")
            else:
                rss_entry = rss.entries[0]
                rss_feed_title = rss.feed.title
                db_rss = get_rss(rss_url)
                if db_rss and db_rss.get('feed_title', '') != rss_feed_title:
                    if rss_feed_title and rss_feed_title != 'undefined 的 bilibili 空间':
                        update_rss_feed_title(rss_url, rss_feed_title)
                    else:
                        rss_feed_title = db_rss.get('feed_title', rss_feed_title)
                if check_rss_update(db_rss, rss_entry):
                    if update_rss(rss_url, rss_entry.id, rss_entry.title):
                        logging.info(f'更新成功: {rss_url} {rss_feed_title} {rss_entry}\n')
                        logging.info(f'更新成功1: {rss}\n')

                        send_notice(rss_entry=rss_entry, rss_feed_title=rss_feed_title, last_title=db_rss['last_title'])

                        update_rss_item(rss_entry, rss_feed_title)

                        save_rss_items(rss_items=my_rss_items)

                        if need_download(db_rss):
                            command = f"you-get -o /mnt/nfs/download/bilibili --no-caption {rss_entry.link}"
                            subprocess.Popen(command, shell=True)

                    else:
                        logging.debug(f'更新失败: {rss_url} {rss_feed_title}\n')
        except Exception as e:
            logging.warning("handle_rss error.", e)

        schdule.enter(60 * 30, 0, handle_rss, (rss_url,))


def update_rss_item(rss_entry, rss_feed_title):
    rss_item = PyRSS2Gen.RSSItem(
        title=rss_entry.title,
        link=rss_entry.link,
        description=rss_entry.summary,
        pubDate=rss_entry.published,
        categories=[rss_feed_title],
        source=PyRSS2Gen.Source(name=rss_feed_title, url='')
    )
    my_rss_items.insert(0, rss_item)


def discover_rss():
    try:
        rsses = get_rsses()
        for rss in rsses:
            rss_url = rss['_id']
            # print(rss_url)
            if rss_url not in rss_locks:
                logging.debug(f"discover rss: {rss_url}")
                if check_rss(rss_url):
                    rss_locks[rss_url] = threading.Lock()
                    schdule.enter(0, 0, handle_rss, (rss_url,))
                else:
                    logging.debug(f"rss: {rss_url} can not parse!")
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
