from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from beem.instance import shared_steem_instance
from datetime import datetime, timedelta
import json


class ObjectCache(dict):

    def __init__(self, initial_data={}, default_expiration=10):
        super().__init__(initial_data)
        self.default_expiration = default_expiration

    def clear(self):
        """ Clears the whole cache
        """
        dict.__init__(self, dict())

    def __setitem__(self, key, value):
        if key in self:
            del self[key]
        data = {
            "expires": datetime.utcnow() + timedelta(
                seconds=self.default_expiration),
            "data": value
        }
        dict.__setitem__(self, key, data)

    def __getitem__(self, key):
        if key in self:
            value = dict.__getitem__(self, key)
            return value["data"]

    def get(self, key, default):
        if key in self:
            return self[key]
        else:
            return default

    def __contains__(self, key):
        if dict.__contains__(self, key):
            value = dict.__getitem__(self, key)
            if datetime.utcnow() < value["expires"]:
                return True
        return False

    def __str__(self):
        return "ObjectCache(n={}, default_expiration={})".format(
            len(list(self.keys())), self.default_expiration)


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
        steem_instance=None,
        *args,
        **kwargs
    ):
        self.steem = steem_instance or shared_steem_instance()
        self.cached = False
        self.identifier = None

        # We don't read lists, sets, or tuples
        if isinstance(data, (list, set, tuple)):
            raise ValueError(
                "Cannot interpret lists! Please load elements individually!")

        if id_item and isinstance(id_item, str):
            self.id_item = id_item
        else:
            self.id_item = "id"
        if klass and isinstance(data, klass):
            self.identifier = data.get(self.id_item)
            super().__init__(data)
        elif isinstance(data, dict):
            self.identifier = data.get(self.id_item)
            super().__init__(data)
        elif isinstance(data, int):
            # This is only for block number bascially
            self.identifier = data
            if not lazy and not self.cached:
                self.refresh()
            # make sure to store the blocknumber for caching
            self[self.id_item] = str(data)
            # Set identifier again as it is overwritten in super() in refresh()
            self.identifier = data
        elif isinstance(data, str):
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
                super().__init__(self.getcache(data))
            elif not lazy and not self.cached:
                self.refresh()

        if use_cache and not lazy:
            self.cache()
            self.cached = True

    @staticmethod
    def clear_cache():
        if BlockchainObject._cache:
            BlockchainObject._cache.clear()

    def test_valid_objectid(self, i):
        if isinstance(i, str):
            return True
        elif isinstance(i, int):
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

    def iscached(self, id):
        return id in BlockchainObject._cache

    def getcache(self, id):
        return BlockchainObject._cache.get(id, None)

    def __getitem__(self, key):
        if not self.cached:
            self.refresh()
        return super().__getitem__(key)

    def items(self):
        if not self.cached:
            self.refresh()
        return list(super().items())

    def __contains__(self, key):
        if not self.cached:
            self.refresh()
        return super().__contains__(key)

    def __repr__(self):
        return "<%s %s>" % (
            self.__class__.__name__, str(self.identifier))

    def json(self):
        return json.loads(str(json.dumps(self)))
