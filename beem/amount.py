# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes, int, str
import six
from beem.instance import shared_steem_instance
from beem.asset import Asset


class Amount(dict):
    """ This class deals with Amounts of any asset to simplify dealing with the tuple::

            (amount, asset)

        :param list args: Allows to deal with different representations of an amount
        :param float amount: Let's create an instance with a specific amount
        :param str asset: Let's you create an instance with a specific asset (symbol)
        :param steem.steem.Steem steem_instance: Steem instance
        :returns: All data required to represent an Amount/Asset
        :rtype: dict
        :raises ValueError: if the data provided is not recognized

        Way to obtain a proper instance:

            * ``args`` can be a string, e.g.:  "1 SBD"
            * ``args`` can be a dictionary containing ``amount`` and ``asset_id``
            * ``args`` can be a dictionary containing ``amount`` and ``asset``
            * ``args`` can be a list of a ``float`` and ``str`` (symbol)
            * ``args`` can be a list of a ``float`` and a :class:`beem.asset.Asset`
            * ``amount`` and ``asset`` are defined manually

        An instance is a dictionary and comes with the following keys:

            * ``amount`` (float)
            * ``symbol`` (str)
            * ``asset`` (instance of :class:`beem.asset.Asset`)

        Instances of this class can be used in regular mathematical expressions
        (``+-*/%``) such as:

        .. code-block:: python

            from beem.amount import Amount
            from beem.asset import Asset
            a = Amount("1 STEEM")
            b = Amount(1, "STEEM")
            c = Amount("20", Asset("STEEM"))
            a + b
            a * 2
            a += b
            a /= 2.0

    """
    def __init__(self, amount, asset=None, steem_instance=None):
        self["asset"] = {}

        self.steem = steem_instance or shared_steem_instance()
        if amount and asset is None and isinstance(amount, Amount):
            # Copy Asset object
            self["amount"] = amount["amount"]
            self["symbol"] = amount["symbol"]
            self["asset"] = amount["asset"]

        elif amount is not None and asset is None and isinstance(amount, six.string_types):
            self["amount"], self["symbol"] = amount.split(" ")
            self["asset"] = Asset(self["symbol"], steem_instance=self.steem)

        elif (amount and asset is None and
                isinstance(amount, dict) and
                "amount" in amount and
                "asset_id" in amount):
            self["asset"] = Asset(amount["asset_id"], steem_instance=self.steem)
            self["symbol"] = self["asset"]["symbol"]
            self["amount"] = int(amount["amount"]) / 10 ** self["asset"]["precision"]

        elif (amount and asset is None and
                isinstance(amount, dict) and
                "amount" in amount and
                "asset" in amount):
            self["asset"] = Asset(amount["asset"], steem_instance=self.steem)
            self["symbol"] = self["asset"]["symbol"]
            self["amount"] = int(amount["amount"]) / 10 ** self["asset"]["precision"]

        elif amount and asset and isinstance(asset, Asset):
            self["amount"] = amount
            self["symbol"] = asset["symbol"]
            self["asset"] = asset

        elif amount and asset and isinstance(asset, six.string_types):
            self["amount"] = amount
            self["asset"] = Asset(asset, steem_instance=self.steem)
            self["symbol"] = self["asset"]["symbol"]
        elif isinstance(amount, (six.integer_types, float)) and asset and isinstance(asset, Asset):
            self["amount"] = amount
            self["asset"] = asset
            self["symbol"] = self["asset"]["symbol"]
        elif isinstance(amount, (six.integer_types, float)) and asset and isinstance(asset, dict):
            self["amount"] = amount
            self["asset"] = asset
            self["symbol"] = self["asset"]["symbol"]
        elif isinstance(amount, (six.integer_types, float)) and asset and isinstance(asset, six.string_types):
            self["amount"] = amount
            self["asset"] = Asset(asset, steem_instance=self.steem)
            self["symbol"] = asset
        else:
            raise ValueError

        # make sure amount is a float
        self["amount"] = float(self["amount"])

    def copy(self):
        """ Copy the instance and make sure not to use a reference
        """
        return Amount(
            amount=self["amount"],
            asset=self["asset"].copy(),
            steem_instance=self.steem)

    @property
    def amount(self):
        """ Returns the amount as float
        """
        return self["amount"]

    @property
    def symbol(self):
        """ Returns the symbol of the asset
        """
        return self["symbol"]

    def tuple(self):
        return float(self), self.symbol

    @property
    def asset(self):
        """ Returns the asset as instance of :class:`steem.asset.Asset`
        """
        if not self["asset"]:
            self["asset"] = Asset(self["symbol"], steem_instance=self.steem)
        return self["asset"]

    def json(self):
        return {
            "amount": int(self),
            "symbol": self["asset"]["symbol"]
        }

    def __str__(self):
        return "{:.{prec}f} {}".format(
            self["amount"],
            self["symbol"],
            prec=self["asset"]["precision"]
        )

    def __float__(self):
        return float(self["amount"])

    def __int__(self):
        return int(self["amount"] * 10 ** self["asset"]["precision"])

    def __add__(self, other):
        a = self.copy()
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            a["amount"] += other["amount"]
        else:
            a["amount"] += float(other)
        return a

    def __sub__(self, other):
        a = self.copy()
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            a["amount"] -= other["amount"]
        else:
            a["amount"] -= float(other)
        return a

    def __mul__(self, other):
        a = self.copy()
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            a["amount"] *= other["amount"]
        else:
            a["amount"] *= other
        return a

    def __floordiv__(self, other):
        a = self.copy()
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            from .price import Price
            return Price(self, other)
        else:
            a["amount"] //= other
        return a

    def __div__(self, other):
        a = self.copy()
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            from .price import Price
            return Price(self, other)
        else:
            a["amount"] /= other
        return a

    def __mod__(self, other):
        a = self.copy()
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            a["amount"] %= other["amount"]
        else:
            a["amount"] %= other
        return a

    def __pow__(self, other):
        a = self.copy()
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            a["amount"] **= other["amount"]
        else:
            a["amount"] **= other
        return a

    def __iadd__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            self["amount"] += other["amount"]
        else:
            self["amount"] += other
        return self

    def __isub__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            self["amount"] -= other["amount"]
        else:
            self["amount"] -= other
        return self

    def __imul__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            self["amount"] *= other["amount"]
        else:
            self["amount"] *= other
        return self

    def __idiv__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] / other["amount"]
        else:
            self["amount"] /= other
            return self

    def __ifloordiv__(self, other):
        if isinstance(other, Amount):
            self["amount"] //= other["amount"]
        else:
            self["amount"] //= other
        return self

    def __imod__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            self["amount"] %= other["amount"]
        else:
            self["amount"] %= other
        return self

    def __ipow__(self, other):
        self["amount"] **= other
        return self

    def __lt__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] < other["amount"]
        else:
            return self["amount"] < float(other or 0)

    def __le__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] <= other["amount"]
        else:
            return self["amount"] <= float(other or 0)

    def __eq__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] == other["amount"]
        else:
            return self["amount"] == float(other or 0)

    def __ne__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] != other["amount"]
        else:
            return self["amount"] != float(other or 0)

    def __ge__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] >= other["amount"]
        else:
            return self["amount"] >= float(other or 0)

    def __gt__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] > other["amount"]
        else:
            return self["amount"] > float(other or 0)

    __repr__ = __str__
    __truediv__ = __div__
    __truemul__ = __mul__
