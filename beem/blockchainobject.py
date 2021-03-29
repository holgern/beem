# -*- coding: utf-8 -*-
from beemgraphenebase.py23 import bytes_types, integer_types, string_types, text_type
from beem.instance import shared_blockchain_instance
from datetime import datetime, timedelta
import json
import threading


class ObjectCache(dict):

    def __init__(self, initial_data={}, default_expiration=10, auto_clean=True):
        super(ObjectCache, self).__init__(initial_data)
        self.set_expiration(default_expiration)
        self.auto_clean = auto_clean
        self.lock = threading.RLock()

    def __setitem__(self, key, value):
        data = {
            "expires": datetime.utcnow() + timedelta(
                seconds=self.default_expiration),
            "data": value
        }
        with self.lock:
            if key in self:
                del self[key]
            dict.__setitem__(self, key, data)
        if self.auto_clean:
            self.clear_expired_items()

    def __getitem__(self, key):
        with self.lock:
            if key in self:
                value = dict.__getitem__(self, key)
                if value is not None:
                    return value["data"]

    def get(self, key, default):
        with self.lock:
            if key in self:
                if self[key] is not None:
                    return self[key]
                else:
                    return default
            else:
                return default

    def clear_expired_items(self):
        with self.lock:
            del_list = []
            utc_now = datetime.utcnow()
            for key in self:
                value = dict.__getitem__(self, key)
                if value is None:
                    del_list.append(key)
                    continue
                if utc_now >= value["expires"]:
                    del_list.append(key)
            for key in del_list:
                del self[key]

    def __contains__(self, key):
        with self.lock:
            if dict.__contains__(self, key):
                value = dict.__getitem__(self, key)
                if value is None:
                    return False
                if datetime.utcnow() < value["expires"]:
                    return True
                else:
                    value["data"] = None
            return False

    def __str__(self):
        if self.auto_clean:
            self.clear_expired_items()
        n = 0
        with self.lock:
            n = len(list(self.keys()))
        return "ObjectCache(n={}, default_expiration={})".format(
            n, self.default_expiration)

    def set_expiration(self, expiration):
        """ Set new default expiration time in seconds (default: 10s)
        """
        self.default_expiration = expiration


class BlockchainObject(dict):

    space_id = 1
    type_id = None
    type_ids = []

    _cache = ObjectCache()

    def __init__(
        self,
        data,
        klass=None,
        space_id=1,
        object_id=None,
        lazy=False,
        use_cache=True,
        id_item=None,
        blockchain_instance=None,
        *args,
        **kwargs
    ):
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]      
        self.blockchain = blockchain_instance or shared_blockchain_instance()
        self.cached = False
        self.identifier = None

        # We don't read lists, sets, or tuples
        if isinstance(data, (list, set, tuple)):
            raise ValueError(
                "Cannot interpret lists! Please load elements individually!")

        if id_item and isinstance(id_item, string_types):
            self.id_item = id_item
        else:
            self.id_item = "id"
        if klass and isinstance(data, klass):
            self.identifier = data.get(self.id_item)
            super(BlockchainObject, self).__init__(data)
        elif isinstance(data, dict):
            self.identifier = data.get(self.id_item)
            super(BlockchainObject, self).__init__(data)
        elif isinstance(data, integer_types):
            # This is only for block number basically
            self.identifier = data
            if not lazy and not self.cached:
                self.refresh()
            # make sure to store the blocknumber for caching
            self[self.id_item] = (data)
            # Set identifier again as it is overwritten in super() in refresh()
            self.identifier = data
        elif isinstance(data, string_types):
            self.identifier = data
            if not lazy and not self.cached:
                self.refresh()
            self[self.id_item] = str(data)
            self.identifier = data
        else:
            self.identifier = data
            if self.test_valid_objectid(self.identifier):
                # Here we assume we deal with an id
                self.testid(self.identifier)
            if self.iscached(data):
                super(BlockchainObject, self).__init__(self.getcache(data))
            elif not lazy and not self.cached:
                self.refresh()

        if use_cache and not lazy:
            self.cache()
            self.cached = True

    @staticmethod
    def clear_cache():
        BlockchainObject._cache = ObjectCache()

    def test_valid_objectid(self, i):
        if isinstance(i, string_types):
            return True
        elif isinstance(i, integer_types):
            return True
        else:
            return False

    def testid(self, id):
        if not self.type_id:
            return

        if not self.type_ids:
            self.type_ids = [self.type_id]

    def cache(self):
        # store in cache
        if dict.__contains__(self, self.id_item):
            BlockchainObject._cache[self.get(self.id_item)] = self

    def clear_cache_from_expired_items(self):
        BlockchainObject._cache.clear_expired_items()

    def set_cache_expiration(self, expiration):
        BlockchainObject._cache.default_expiration = expiration

    def set_cache_auto_clean(self, auto_clean):
        BlockchainObject._cache.auto_clean = auto_clean

    def get_cache_expiration(self):
        return BlockchainObject._cache.default_expiration

    def get_cache_auto_clean(self):
        return BlockchainObject._cache.auto_clean

    def iscached(self, id):
        return id in BlockchainObject._cache

    def getcache(self, id):
        return BlockchainObject._cache.get(id, None)

    def __getitem__(self, key):
        if not self.cached:
            self.refresh()
        return super(BlockchainObject, self).__getitem__(key)

    def items(self):
        if not self.cached:
            self.refresh()
        return list(super(BlockchainObject, self).items())

    def __contains__(self, key):
        if not self.cached:
            self.refresh()
        return super(BlockchainObject, self).__contains__(key)

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__, str(self.identifier))

    def json(self):
        return json.loads(str(json.dumps(self)))
