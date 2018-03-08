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
        if "asset" not in self or self["asset"] is None or len(self["asset"]) == 0:
            raise AssetDoesNotExistsException(self.identifier+" "+self.steem.chain_params["chain_assets"])

    def refresh(self):
        """ Refresh the data from the API server
        """
        self.chain_params = self.steem.chain_params
        self["asset"] = ""
        for asset in self.chain_params["chain_assets"]:
            if self.identifier in [asset["symbol"], asset["asset"], asset["id"]]:
                self["asset"] = asset["asset"]
                self["precision"] = asset["precision"]
                self["id"] = asset["id"]
                self["symbol"] = asset["symbol"]
                break

    @property
    def symbol(self):
        return self["symbol"]

    @property
    def asset(self):
        return self["asset"]

    @property
    def precision(self):
        return self["precision"]
