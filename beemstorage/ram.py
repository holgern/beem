# -*- coding: utf-8 -*-
# Inspired by https://raw.githubusercontent.com/xeroc/python-graphenelib/master/graphenestorage/ram.py
from .interfaces import StoreInterface


# StoreInterface is done first, then dict which overwrites the interface
# methods
class InRamStore(StoreInterface):
    """ The InRamStore inherits
        :class:`beemstorage.interfaces.StoreInterface` and extends it by two
        further calls for wipe and delete.

        The store is syntactically equivalent to a regular dictionary.

        .. warning:: If you are trying to obtain a value for a key that does
            **not** exist in the store, the library will **NOT** raise but
            return a ``None`` value. This represents the biggest difference to
            a regular ``dict`` class.
    """

    # Specific for this library
    def delete(self, key):
        """ Delete a key from the store
        """
        self.pop(key, None)

    def wipe(self):
        """ Wipe the store
        """
        keys = list(self.keys()).copy()
        for key in keys:
            self.delete(key)
