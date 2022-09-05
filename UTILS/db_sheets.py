from UTILS.cache_redis import CacheRedis
from UTILS.database_factory import DatabaseFactory
from UTILS.config_port import redis_host, redis_port, mongodb_host, mongodb_port


def get_db_sheet(database_name, sheet_name):
    database_factory = DatabaseFactory(host=mongodb_host, port=mongodb_port, model='pymongo')
    return database_factory.get(database_name=database_name, sheet_name=sheet_name)


cache_redis = CacheRedis(host=redis_host, port=redis_port, db=0)


def get_db_rsses():
    rss_db_sheet = get_db_sheet(database_name="rss", sheet_name="rss")
    return rss_db_sheet.find()


def get_rsses():
    return cache_redis.get_cache_from_db('rss', get_db_rsses)


def get_rss(rss_url):
    rsses = get_rsses()
    for rss in rsses:
        if rss_url == rss['_id']:
            return rss
    return None


def update_redis_rsses_from_db():
    data = get_db_rsses()
    cache_redis.set('rss', data)


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


if __name__ == '__main__':
    rsses = get_rsses()
    print(rsses)
    print(type(rsses), type(rsses[0]))
