import logging

import feedparser


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
        logging.warning(f"rss: {url} can not parse! status: {result.status}")
        return False
    return True
