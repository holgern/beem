# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import random
from datetime import datetime, timedelta
from beem.instance import shared_steem_instance
from .utils import (
    formatTimeFromNow, formatTime, formatTimeString, assets_from_string, parse_time)
from .asset import Asset
from .amount import Amount
from .price import Price, Order, FilledOrder
from .account import Account
from beembase import operations


class Market(dict):
    """ This class allows to easily access Markets on the blockchain for trading, etc.

        :param beem.steem.Steem steem_instance: Steem instance
        :param beem.asset.Asset base: Base asset
        :param beem.asset.Asset quote: Quote asset
        :returns: Blockchain Market
        :rtype: dictionary with overloaded methods

        Instances of this class are dictionaries that come with additional
        methods (see below) that allow dealing with a market and it's
        corresponding functions.

        This class tries to identify **two** assets as provided in the
        parameters in one of the following forms:

        * ``base`` and ``quote`` are valid assets (according to :class:`beem.asset.Asset`)
        * ``base:quote`` separated with ``:``
        * ``base/quote`` separated with ``/``
        * ``base-quote`` separated with ``-``

        .. note:: Throughout this library, the ``quote`` symbol will be
                  presented first (e.g. ``STEEM:SBD`` with ``STEEM`` being the
                  quote), while the ``base`` only refers to a secondary asset
                  for a trade. This means, if you call
                  :func:`beem.market.Market.sell` or
                  :func:`beem.market.Market.buy`, you will sell/buy **only
                  quote** and obtain/pay **only base**.

    """

    def __init__(
        self,
        base=None,
        quote=None,
        steem_instance=None,
    ):
        """
        Init Market

            :param beem.steem.Steem steem_instance: Steem instance
            :param beem.asset.Asset base: Base asset
            :param beem.asset.Asset quote: Quote asset
        """
        self.steem = steem_instance or shared_steem_instance()

        if quote is None and isinstance(base, str):
            quote_symbol, base_symbol = assets_from_string(base)
            quote = Asset(quote_symbol, steem_instance=self.steem)
            base = Asset(base_symbol, steem_instance=self.steem)
            super(Market, self).__init__({"base": base, "quote": quote})
        elif base and quote:
            quote = Asset(quote, steem_instance=self.steem)
            base = Asset(base, steem_instance=self.steem)
            super(Market, self).__init__({"base": base, "quote": quote})
        elif base is None and quote is None:
            quote = Asset("SBD", steem_instance=self.steem)
            base = Asset("STEEM", steem_instance=self.steem)
            super(Market, self).__init__({"base": base, "quote": quote})
        else:
            raise ValueError("Unknown Market config")

    def get_string(self, separator=":"):
        """ Return a formated string that identifies the market, e.g. ``STEEM:SBD``

            :param str separator: The separator of the assets (defaults to ``:``)
        """
        return "%s%s%s" % (self["quote"]["symbol"], separator, self["base"]["symbol"])

    def __eq__(self, other):
        if isinstance(other, str):
            quote_symbol, base_symbol = assets_from_string(other)
            return (
                self["quote"]["symbol"] == quote_symbol and
                self["base"]["symbol"] == base_symbol
            ) or (
                self["quote"]["symbol"] == base_symbol and
                self["base"]["symbol"] == quote_symbol
            )
        elif isinstance(other, Market):
            return (
                self["quote"]["symbol"] == other["quote"]["symbol"] and
                self["base"]["symbol"] == other["base"]["symbol"]
            )

    def ticker(self, raw_data=False):
        """ Returns the ticker for all markets.

            Output Parameters:

            * ``last``: Price of the order last filled
            * ``lowestAsk``: Price of the lowest ask
            * ``highestBid``: Price of the highest bid
            * ``baseVolume``: Volume of the base asset
            * ``quoteVolume``: Volume of the quote asset
            * ``percentChange``: 24h change percentage (in %)
            * ``settlement_price``: Settlement Price for borrow/settlement
            * ``core_exchange_rate``: Core exchange rate for payment of fee in non-BTS asset
            * ``price24h``: the price 24h ago

            Sample Output:

            .. code-block:: js

                {
                    {
                        "quoteVolume": 48328.73333,
                        "quoteSettlement_price": 332.3344827586207,
                        "lowestAsk": 340.0,
                        "baseVolume": 144.1862,
                        "percentChange": -1.9607843231354893,
                        "highestBid": 334.20000000000005,
                        "latest": 333.33333330133934,
                    }
                }

        """
        data = {}
        # Core Exchange rate
        self.steem.rpc.set_next_node_on_empty_reply(True)
        ticker = self.steem.rpc.get_ticker(api="market_history")

        if raw_data:
            return ticker

        data["sbdVolume"] = Amount(ticker["sbd_volume"], steem_instance=self.steem)
        data["steemVolume"] = Amount(ticker["steem_volume"], steem_instance=self.steem)
        data["lowestAsk"] = Price(
            ticker["lowest_ask"],
            base=self["base"],
            quote=self["quote"],
            steem_instance=self.steem
        )
        data["highestBid"] = Price(
            ticker["highest_bid"],
            base=self["base"],
            quote=self["quote"],
            steem_instance=self.steem
        )
        data["latest"] = Price(
            ticker["latest"],
            quote=self["quote"],
            base=self["base"],
            steem_instance=self.steem
        )
        data["percentChange"] = float(ticker["percent_change"])

        return data

    def volume24h(self, raw_data=False):
        """ Returns the 24-hour volume for all markets, plus totals for primary currencies.

            Sample output:

            .. code-block:: js

                {
                    "BTS": 361666.63617,
                    "USD": 1087.0
                }

        """
        self.steem.rpc.set_next_node_on_empty_reply(True)
        volume = self.steem.rpc.get_volume(api="market_history")
        if raw_data:
            return volume
        return {
            self["base"]["symbol"]: Amount(volume["sbd_volume"], steem_instance=self.steem),
            self["quote"]["symbol"]: Amount(volume["steem_volume"], steem_instance=self.steem)
        }

    def orderbook(self, limit=25, raw_data=False):
        """ Returns the order book for a given market. You may also
            specify "all" to get the orderbooks of all markets.
            :param int limit: Limit the amount of orders (default: 25)
            Sample output:
            .. code-block:: js
                {'bids': [0.003679 USD/BTS (1.9103 USD|519.29602 BTS),
                0.003676 USD/BTS (299.9997 USD|81606.16394 BTS),
                0.003665 USD/BTS (288.4618 USD|78706.21881 BTS),
                0.003665 USD/BTS (3.5285 USD|962.74409 BTS),
                0.003665 USD/BTS (72.5474 USD|19794.41299 BTS)],
                'asks': [0.003738 USD/BTS (36.4715 USD|9756.17339 BTS),
                0.003738 USD/BTS (18.6915 USD|5000.00000 BTS),
                0.003742 USD/BTS (182.6881 USD|48820.22081 BTS),
                0.003772 USD/BTS (4.5200 USD|1198.14798 BTS),
                0.003799 USD/BTS (148.4975 USD|39086.59741 BTS)]}
            .. note:: Each bid is an instance of
                class:`steem.price.Order` and thus carries the keys
                ``base``, ``quote`` and ``price``. From those you can
                obtain the actual amounts for sale
        """
        self.steem.rpc.set_next_node_on_empty_reply(True)
        if self.steem.rpc.get_use_appbase():
            orders = self.steem.rpc.get_order_book({'limit': limit}, api="market_history")
        else:
            orders = self.steem.rpc.get_order_book(limit, api='database_api')
        if raw_data:
            return orders
        asks = list([Order(
            Amount(x["order_price"]["quote"], steem_instance=self.steem),
            Amount(x["order_price"]["base"], steem_instance=self.steem),
            steem_instance=self.steem) for x in orders["asks"]])
        bids = list([Order(
            Amount(x["order_price"]["quote"], steem_instance=self.steem),
            Amount(x["order_price"]["base"], steem_instance=self.steem),
            steem_instance=self.steem).invert() for x in orders["bids"]])
        asks_date = list([formatTimeString(x["created"]) for x in orders["asks"]])
        bids_date = list([formatTimeString(x["created"]) for x in orders["bids"]])
        data = {"asks": asks, "bids": bids, "asks_date": asks_date, "bids_date": bids_date}
        return data

    def recent_trades(self, limit=25, raw_data=False):
        """ Returns the order book for a given market. You may also
            specify "all" to get the orderbooks of all markets.

            :param int limit: Limit the amount of orders (default: 25)

            Sample output:

            .. code-block:: js

                {'bids': [0.003679 USD/BTS (1.9103 USD|519.29602 BTS),
                0.003676 USD/BTS (299.9997 USD|81606.16394 BTS),
                0.003665 USD/BTS (288.4618 USD|78706.21881 BTS),
                0.003665 USD/BTS (3.5285 USD|962.74409 BTS),
                0.003665 USD/BTS (72.5474 USD|19794.41299 BTS)],
                'asks': [0.003738 USD/BTS (36.4715 USD|9756.17339 BTS),
                0.003738 USD/BTS (18.6915 USD|5000.00000 BTS),
                0.003742 USD/BTS (182.6881 USD|48820.22081 BTS),
                0.003772 USD/BTS (4.5200 USD|1198.14798 BTS),
                0.003799 USD/BTS (148.4975 USD|39086.59741 BTS)]}


            .. note:: Each bid is an instance of
                class:`steem.price.Order` and thus carries the keys
                ``base``, ``quote`` and ``price``. From those you can
                obtain the actual amounts for sale

        """
        self.steem.rpc.set_next_node_on_empty_reply(limit > 0)
        if self.steem.rpc.get_use_appbase():
            orders = self.steem.rpc.get_recent_trades({'limit': limit}, api="market_history")['trades']
        else:
            orders = self.steem.rpc.get_recent_trades(limit, api="market_history")
        if raw_data:
            return orders
        filled_order = list([FilledOrder(x, steem_instance=self.steem) for x in orders])
        return filled_order

    def trades(self, limit=25, start=None, stop=None, raw_data=False):
        """ Returns your trade history for a given market.

            :param int limit: Limit the amount of orders (default: 25)
            :param datetime start: start time
            :param datetime stop: stop time

        """
        # FIXME, this call should also return whether it was a buy or
        # sell
        if not stop:
            stop = datetime.now()
        if not start:
            start = stop - timedelta(hours=24)
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            orders = self.steem.rpc.get_trade_history({'start': formatTimeString(start),
                                                       'end': formatTimeString(stop),
                                                       'limit': limit}, api="market_history")['trades']
        else:
            orders = self.steem.rpc.get_trade_history(
                formatTimeString(start),
                formatTimeString(stop),
                limit, api="market_history")
        if raw_data:
            return orders
        filled_order = list([FilledOrder(x, steem_instance=self.steem) for x in orders])
        return filled_order

    def market_history_buckets(self):
        self.steem.rpc.set_next_node_on_empty_reply(True)
        ret = self.steem.rpc.get_market_history_buckets(api="market_history")
        if self.steem.rpc.get_use_appbase():
            return ret['bucket_sizes']
        else:
            return ret

    def market_history(self, bucket_seconds=300, start_age=3600, end_age=0):
        buckets = self.market_history_buckets()
        if bucket_seconds < 5 and bucket_seconds >= 0:
            bucket_seconds = buckets[bucket_seconds]
        else:
            if bucket_seconds not in buckets:
                raise ValueError("You need select the bucket_seconds from " + str(buckets))
        self.steem.rpc.set_next_node_on_empty_reply(False)
        if self.steem.rpc.get_use_appbase():
            history = self.steem.rpc.get_market_history({'bucket_seconds': bucket_seconds,
                                                         'start': formatTimeFromNow(-start_age - end_age),
                                                         'end': formatTimeFromNow(-end_age)}, api="market_history")['buckets']
        else:
            history = self.steem.rpc.get_market_history(
                bucket_seconds,
                formatTimeFromNow(-start_age - end_age),
                formatTimeFromNow(-end_age),
                api="market_history")
        return history

    def accountopenorders(self, account=None, raw_data=False):
        """ Returns open Orders

            :param steem.account.Account account: Account name or instance of Account to show orders for in this market
        """
        if not account:
            if "default_account" in self.steem.config:
                account = self.steem.config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, full=True, steem_instance=self.steem)

        r = []
        # orders = account["limit_orders"]
        if self.steem.rpc.get_use_appbase():
            orders = self.steem.rpc.find_limit_orders({'account': account["name"]}, api="database")['orders']
        else:
            orders = self.steem.rpc.get_open_orders(account["name"])
        if raw_data:
            return orders
        for o in orders:
            order = {}
            order["order"] = Order(
                Amount(o["sell_price"]["base"], steem_instance=self.steem),
                Amount(o["sell_price"]["quote"], steem_instance=self.steem),
                steem_instance=self.steem
            )
            order["orderid"] = o["orderid"]
            order["created"] = formatTimeString(o["created"])
            r.append(order)
        return r

    def buy(
        self,
        price,
        amount,
        expiration=None,
        killfill=False,
        account=None,
        orderid=None,
        returnOrderId=False
    ):
        """ Places a buy order in a given market

            :param float price: price denoted in ``base``/``quote``
            :param number amount: Amount of ``quote`` to buy
            :param number expiration: (optional) expiration time of the order in seconds (defaults to 7 days)
            :param bool killfill: flag that indicates if the order shall be killed if it is not filled (defaults to False)
            :param string account: Account name that executes that order
            :param string returnOrderId: If set to "head" or "irreversible" the call will wait for the tx to appear in
                                        the head/irreversible block and add the key "orderid" to the tx output

            Prices/Rates are denoted in 'base', i.e. the USD_BTS market
            is priced in BTS per USD.

            **Example:** in the USD_BTS market, a price of 300 means
            a USD is worth 300 BTS

            .. note::

                All prices returned are in the **reversed** orientation as the
                market. I.e. in the BTC/BTS market, prices are BTS per BTC.
                That way you can multiply prices with `1.05` to get a +5%.

            .. warning::

                Since buy orders are placed as
                limit-sell orders for the base asset,
                you may end up obtaining more of the
                buy asset than you placed the order
                for. Example:

                    * You place and order to buy 10 USD for 100 BTS/USD
                    * This means that you actually place a sell order for 1000 BTS in order to obtain **at least** 10 USD
                    * If an order on the market exists that sells USD for cheaper, you will end up with more than 10 USD
        """
        if not expiration:
            expiration = self.steem.config["order-expiration"]
        if not account:
            if "default_account" in self.steem.config:
                account = self.steem.config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self.steem)

        if isinstance(price, Price):
            price = price.as_base(self["base"]["symbol"])

        if isinstance(amount, Amount):
            amount = Amount(amount, steem_instance=self.steem)
            if not amount["asset"]["symbol"] == self["quote"]["symbol"]:
                raise AssertionError("Price: {} does not match amount: {}".format(
                    str(price), str(amount)))
        elif isinstance(amount, str):
            amount = Amount(amount, steem_instance=self.steem)
        else:
            amount = Amount(amount, self["quote"]["symbol"], steem_instance=self.steem)

        order = operations.Limit_order_create(**{
            "owner": account["name"],
            "orderid": orderid or random.getrandbits(32),
            "amount_to_sell": Amount(
                float(amount) * float(price),
                self["base"]["symbol"],
                steem_instance=self.steem
            ),
            "min_to_receive": Amount(
                float(amount),
                self["quote"]["symbol"],
                steem_instance=self.steem
            ),
            "expiration": formatTimeFromNow(expiration),
            "fill_or_kill": killfill,
            "prefix": self.steem.prefix,
        })

        if returnOrderId:
            # Make blocking broadcasts
            prevblocking = self.steem.blocking
            self.steem.blocking = returnOrderId

        tx = self.steem.finalizeOp(order, account["name"], "active")

        if returnOrderId:
            tx["orderid"] = tx["operation_results"][0][1]
            self.steem.blocking = prevblocking

        return tx

    def sell(
        self,
        price,
        amount,
        expiration=None,
        killfill=False,
        account=None,
        orderid=None,
        returnOrderId=False
    ):
        """ Places a sell order in a given market

            :param float price: price denoted in ``base``/``quote``
            :param number amount: Amount of ``quote`` to sell
            :param number expiration: (optional) expiration time of the order in seconds (defaults to 7 days)
            :param bool killfill: flag that indicates if the order shall be killed if it is not filled (defaults to False)
            :param string account: Account name that executes that order
            :param string returnOrderId: If set to "head" or "irreversible" the call will wait for the tx to appear in
                                        the head/irreversible block and add the key "orderid" to the tx output

            Prices/Rates are denoted in 'base', i.e. the USD_BTS market
            is priced in BTS per USD.

            **Example:** in the USD_BTS market, a price of 300 means
            a USD is worth 300 BTS

            .. note::

                All prices returned are in the **reversed** orientation as the
                market. I.e. in the BTC/BTS market, prices are BTS per BTC.
                That way you can multiply prices with `1.05` to get a +5%.
        """
        if not expiration:
            expiration = self.steem.config["order-expiration"]
        if not account:
            if "default_account" in self.steem.config:
                account = self.steem.config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self.steem)
        if isinstance(price, Price):
            price = price.as_base(self["base"]["symbol"])

        if isinstance(amount, Amount):
            amount = Amount(amount, steem_instance=self.steem)
            if not amount["asset"]["symbol"] == self["quote"]["symbol"]:
                raise AssertionError("Price: {} does not match amount: {}".format(
                    str(price), str(amount)))
        elif isinstance(amount, str):
            amount = Amount(amount, steem_instance=self.steem)
        else:
            amount = Amount(amount, self["quote"]["symbol"], steem_instance=self.steem)

        order = operations.Limit_order_create(**{
            "owner": account["name"],
            "orderid": orderid or random.getrandbits(32),
            "amount_to_sell": Amount(
                float(amount),
                self["quote"]["symbol"],
                steem_instance=self.steem
            ),
            "min_to_receive": Amount(
                float(amount) * float(price),
                self["base"]["symbol"],
                steem_instance=self.steem
            ),
            "expiration": formatTimeFromNow(expiration),
            "fill_or_kill": killfill,
            "prefix": self.steem.prefix,
        })
        if returnOrderId:
            # Make blocking broadcasts
            prevblocking = self.steem.blocking
            self.steem.blocking = returnOrderId

        tx = self.steem.finalizeOp(order, account["name"], "active")

        if returnOrderId:
            tx["orderid"] = tx["operation_results"][0][1]
            self.steem.blocking = prevblocking

        return tx

    def cancel(self, orderNumbers, account=None, **kwargs):
        """ Cancels an order you have placed in a given market. Requires
            only the "orderNumbers". An order number takes the form
            ``1.7.xxx``.
            :param str orderNumbers: The Order Object ide of the form ``1.7.xxxx``
        """
        if not account:
            if "default_account" in self.steem.config:
                account = self.steem.config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, full=False, steem_instance=self.steem)

        if not isinstance(orderNumbers, (list, set, tuple)):
            orderNumbers = {orderNumbers}

        op = []
        for order in orderNumbers:
            op.append(
                operations.Limit_order_cancel(**{
                    "owner": account["name"],
                    "orderid": order,
                    "prefix": self.steem.prefix}))
        return self.steem.finalizeOp(op, account["name"], "active", **kwargs)
