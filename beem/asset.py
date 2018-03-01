# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import json
from .exceptions import AssetDoesNotExistsException
from .blockchainobject import BlockchainObject


class Asset(BlockchainObject):
    """ Deals with Assets of the network.

        :param str Asset: Symbol name or object id of an asset
        :param bool lazy: Lazy loading
        :param bool full: Also obtain bitasset-data and dynamic asset dat
        :param beem.steem.Steem steem_instance: Steem
            instance
        :returns: All data of an asset
        :rtype: dict

        .. note:: This class comes with its own caching function to reduce the
                  load on the API server. Instances of this class can be
                  refreshed with ``Asset.refresh()``.
    """
    type_id = 3

    def __init__(
        self,
        asset,
        lazy=False,
        full=False,
        steem_instance=None
    ):
        self.full = full
        super(Asset, self).__init__(
            asset,
            lazy=lazy,
            full=full,
            steem_instance=steem_instance
        )
        self.refresh()

    def refresh(self):
        """ Refresh the data from the API server
        """
        self.chain_params = self.steem.chain_params
        if self.identifier == "sbd_symbol" or self.identifier == self.chain_params["sbd_symbol"] or self.identifier == 0:
            self["asset"] = "sbd_symbol"
            self["precision"] = 3
            self["id"] = 0
            self["symbol"] = self.chain_params["sbd_symbol"]
        elif self.identifier == "steem_symbol" or self.identifier == self.chain_params["steem_symbol"] or self.identifier == 1:
            self["asset"] = "steem_symbol"
            self["precision"] = 3
            self["id"] = 1
            self["symbol"] = self.chain_params["steem_symbol"]
        elif self.identifier == "vests_symbol" or self.identifier == self.chain_params["vests_symbol"] or self.identifier == 2:
            self["asset"] = "vests_symbol"
            self["precision"] = 6
            self["id"] = 2
            self["symbol"] = self.chain_params["vests_symbol"]
        else:
            raise AssetDoesNotExistsException(self.identifier)

    @property
    def symbol(self):
        return self["symbol"]

    @property
    def precision(self):
        return self["precision"]
