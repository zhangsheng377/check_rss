import os

mongodb_host = os.getenv('MONGODB_HOST')
mongodb_port = int(os.getenv('MONGODB_PORT'))

redis_host = os.getenv('REDIS_HOST')
redis_port = int(os.getenv('REDIS_PORT'))
