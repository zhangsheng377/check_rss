import json
import re
from datetime import datetime

import redis

from DATABASE import database_factory
from UTILS.config_port import redis_host, redis_port


def get_db_sheet(database_name, sheet_name):
    return database_factory(database_name=database_name, sheet_name=sheet_name, model="pymongo")


def _get_data(key: str, get_db_func):
    data_redis = db_redis.get(key)
    if data_redis is None:
        data = get_db_func()
        db_redis.set(key, json.dumps(data))
    else:
        data = json.loads(data_redis)
    return data


def get_db_rsses():
    rss_db_sheet = get_db_sheet(database_name="rss", sheet_name="rss")
    return rss_db_sheet.find()


def get_rsses():
    return _get_data('rss', get_db_rsses)


def get_rss(rss_url):
    rsses = get_rsses()
    for rss in rsses:
        if rss_url == rss['_id']:
            return rss
    return None


def update_redis_rsses_from_db():
    data = get_db_rsses()
    db_redis.set('rss', json.dumps(data))


def insert_rsses(document):
    rss_db_sheet = get_db_sheet(database_name="rss", sheet_name="rss")
    if rss_db_sheet.insert(document=document):
        update_redis_rsses_from_db()
        return True
    return False


def update_one_rss(filter, update):
    rss_db_sheet = get_db_sheet(database_name="rss", sheet_name="rss")
    result = rss_db_sheet.update_one(filter=filter, update=update)
    update_redis_rsses_from_db()
    return result


db_redis = redis.Redis(host=redis_host, port=redis_port, db=0)

if __name__ == '__main__':
    rsses = get_rsses()
    print(rsses)
    print(type(rsses), type(rsses[0]))

