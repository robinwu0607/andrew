import redis as r
import pickle
import time

POOL = r.ConnectionPool(host='localhost', port=6379, db=0)


class Broker(object):
    def __init__(self, name: str):
        self.name = name
        self.db = r.StrictRedis(connection_pool=POOL)
        return

    def push(self, value: str):
        self.db.rpush(self.name, value)
        return

    def pop(self):
        value = self.db.lpop(self.name)
        return value.decode('utf-8') if value else ""

    def append(self, key: str, value: str):
        self.db.append(key=":".join([self.name, key]), value=value)
        return

    def set(self, key: str, value, expire=None):
        while not self.db.setnx(self.name + '______redis', 'LOCK'):
            time.sleep(0.1)
        self.db.set(name=":".join([self.name, key]), value=pickle.dumps(value), ex=expire)
        del self.db[self.name + '______redis']

    def get_str(self, key: str):
        value = self.db.get(name=":".join([self.name, key]))
        return pickle.loads(value) if value else ""

    def get_list(self, key: str):
        value = self.db.get(name=":".join([self.name, key]))
        return pickle.loads(value) if value else []

    def get_dict(self, key: str):
        value = self.db.get(name=":".join([self.name, key]))
        return pickle.loads(value) if value else {}

    def get_keys(self):
        return self.db.keys()

    def delete(self, key: str):
        del self.db[":".join([self.name, key])]
        return

    def flush(self):
        return self.db.flushall()
