# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import random
import pytz
import logging
from datetime import datetime, timedelta
from beem.instance import shared_steem_instance
from .utils import (
    formatTimeFromNow, formatTime, formatTimeString, assets_from_string, parse_time, addTzInfo)
from .asset import Asset
from .amount import Amount
from .price import Price, Order, FilledOrder
from .account import Account
from beembase import operations
REQUEST_MODULE = None
if not REQUEST_MODULE:
    try:
        import requests
        REQUEST_MODULE = "requests"
    except ImportError:
        REQUEST_MODULE = None
log = logging.getLogger(__name__)


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

            * ``latest``: Price of the order last filled
            * ``lowest_ask``: Price of the lowest ask
            * ``highest_bid``: Price of the highest bid
            * ``sbd_volume``: Volume of SBD
            * ``steem_volume``: Volume of STEEM
            * ``percent_change``: 24h change percentage (in %)

            .. note::
                Market is STEEM:SBD and prices are SBD per STEEM!

            Sample Output:

            .. code-block:: js

                 {
                    'highest_bid': 0.30100226633322913,
                    'latest': 0.0,
                    'lowest_ask': 0.3249636958897082,
                    'percent_change': 0.0,
                    'sbd_volume': 108329611.0,
                    'steem_volume': 355094043.0
                }

        """
        data = {}
        # Core Exchange rate
        self.steem.rpc.set_next_node_on_empty_reply(True)
        ticker = self.steem.rpc.get_ticker(api="market_history")

        if raw_data:
            return ticker

        data["highest_bid"] = Price(
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
        data["lowest_ask"] = Price(
            ticker["lowest_ask"],
            base=self["base"],
            quote=self["quote"],
            steem_instance=self.steem
        )
        data["percent_change"] = float(ticker["percent_change"])
        data["sbd_volume"] = Amount(ticker["sbd_volume"], steem_instance=self.steem)
        data["steem_volume"] = Amount(ticker["steem_volume"], steem_instance=self.steem)

        return data

    def volume24h(self, raw_data=False):
        """ Returns the 24-hour volume for all markets, plus totals for primary currencies.

            Sample output:

            .. code-block:: js

                {
                    "STEEM": 361666.63617,
                    "SBD": 1087.0
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
        """ Returns the order book for SBD/STEEM market.
            :param int limit: Limit the amount of orders (default: 25)

            Sample output (raw_data=False):
                .. code-block:: js

                    {
                        'asks': [
                            380.510 STEEM 460.291 SBD @ 1.209669 SBD/STEEM,
                            53.785 STEEM 65.063 SBD @ 1.209687 SBD/STEEM
                        ],
                        'bids': [
                            0.292 STEEM 0.353 SBD @ 1.208904 SBD/STEEM,
                            8.498 STEEM 10.262 SBD @ 1.207578 SBD/STEEM
                        ],
                        'asks_date': [
                            datetime.datetime(2018, 4, 30, 21, 7, 24, tzinfo=<UTC>),
                            datetime.datetime(2018, 4, 30, 18, 12, 18, tzinfo=<UTC>)
                        ],
                        'bids_date': [
                            datetime.datetime(2018, 4, 30, 21, 1, 21, tzinfo=<UTC>),
                            datetime.datetime(2018, 4, 30, 20, 38, 21, tzinfo=<UTC>)
                        ]
                    }

            Sample output (raw_data=True):
                .. code-block:: js

                    {
                        'asks': [
                            {
                                'order_price': {'base': '8.000 STEEM', 'quote': '9.618 SBD'},
                                'real_price': '1.20225000000000004',
                                'steem': 4565,
                                'sbd': 5488,
                                'created': '2018-04-30T21:12:45'
                            }
                        ],
                        'bids': [
                            {
                                'order_price': {'base': '10.000 SBD', 'quote': '8.333 STEEM'},
                                'real_price': '1.20004800192007677',
                                'steem': 8333,
                                'sbd': 10000,
                                'created': '2018-04-30T20:29:33'
                            }
                        ]
                    }

            .. note:: Each bid is an instance of
                class:`beem.price.Order` and thus carries the keys
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
            :param bool raw_data: when False, FilledOrder objects will be
                returned

            Sample output (raw_data=False):

                .. code-block:: js

                    [
                        (2018-04-30 21:00:54+00:00) 0.267 STEEM 0.323 SBD @ 1.209738 SBD/STEEM,
                        (2018-04-30 20:59:30+00:00) 0.131 STEEM 0.159 SBD @ 1.213740 SBD/STEEM,
                        (2018-04-30 20:55:45+00:00) 0.093 STEEM 0.113 SBD @ 1.215054 SBD/STEEM,
                        (2018-04-30 20:55:30+00:00) 26.501 STEEM 32.058 SBD @ 1.209690 SBD/STEEM,
                        (2018-04-30 20:55:18+00:00) 2.108 STEEM 2.550 SBD @ 1.209677 SBD/STEEM,
                    ]

            Sample output (raw_data=True):

                .. code-block:: js

                    [
                        {'date': '2018-04-30T21:02:45', 'current_pays': '0.235 SBD', 'open_pays': '0.194 STEEM'},
                        {'date': '2018-04-30T21:02:03', 'current_pays': '24.494 SBD', 'open_pays': '20.248 STEEM'},
                        {'date': '2018-04-30T20:48:30', 'current_pays': '175.464 STEEM', 'open_pays': '211.955 SBD'},
                        {'date': '2018-04-30T20:48:30', 'current_pays': '0.999 STEEM', 'open_pays': '1.207 SBD'},
                        {'date': '2018-04-30T20:47:54', 'current_pays': '0.273 SBD', 'open_pays': '0.225 STEEM'},
                    ]

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

    def trade_history(self, start=None, stop=None, intervall=None, limit=25, raw_data=False):
        """ Returns the trade history for the internal market

            This function allows to fetch a fixed number of trades at fixed
            intervall times to reduce the call duration time. E.g. it is possible to
            receive the trades from the last 7 days, by fetching 100 trades each 6 hours.

            When intervall is set to None, all trades are recieved between start and stop.
            This can take a while.

            :param datetime start: Start date
            :param datetime stop: Stop date
            :param timedelta intervall: Defines the intervall
            :param int limit: Defines how many trades are fetched at each intervall point
            :param bool raw_data: when True, the raw data are returned
        """
        utc = pytz.timezone('UTC')
        if not stop:
            stop = utc.localize(datetime.utcnow())
        if not start:
            start = stop - timedelta(hours=1)
        start = addTzInfo(start)
        stop = addTzInfo(stop)
        current_start = start
        filled_order = []
        fo = self.trades(start=current_start, stop=stop, limit=limit, raw_data=raw_data)
        if intervall is None and len(fo) > 0:
            current_start = fo[-1]["date"]
            filled_order += fo
        elif intervall is not None:
            current_start += intervall
            filled_order += [fo]
        last_date = fo[-1]["date"]
        while (len(fo) > 0 and last_date < stop):
            fo = self.trades(start=current_start, stop=stop, limit=limit, raw_data=raw_data)
            if len(fo) == 0 or fo[-1]["date"] == last_date:
                break
            last_date = fo[-1]["date"]
            if intervall is None:
                current_start = last_date
                filled_order += fo
            else:
                current_start += intervall
                filled_order += [fo]
        return filled_order

    def trades(self, limit=100, start=None, stop=None, raw_data=False):
        """ Returns your trade history for a given market.

            :param int limit: Limit the amount of orders (default: 100)
            :param datetime start: start time
            :param datetime stop: stop time

        """
        # FIXME, this call should also return whether it was a buy or
        # sell
        utc = pytz.timezone('UTC')
        if not stop:
            stop = utc.localize(datetime.utcnow())
        if not start:
            start = stop - timedelta(hours=24)
        start = addTzInfo(start)
        stop = addTzInfo(stop)
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
        """ Return the market history (filled orders).

            :param int bucket_seconds: Bucket size in seconds (see
                `returnMarketHistoryBuckets()`)
            :param int start_age: Age (in seconds) of the start of the
                window (default: 1h/3600)
            :param int end_age: Age (in seconds) of the end of the window
                (default: now/0)

            Example:
                .. code-block:: js

                    {
                        'close_sbd': 2493387,
                        'close_steem': 7743431,
                        'high_sbd': 1943872,
                        'high_steem': 5999610,
                        'id': '7.1.5252',
                        'low_sbd': 534928,
                        'low_steem': 1661266,
                        'open': '2016-07-08T11:25:00',
                        'open_sbd': 534928,
                        'open_steem': 1661266,
                        'sbd_volume': 9714435,
                        'seconds': 300,
                        'steem_volume': 30088443
                    }

        """
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
        if not self.steem.is_connected():
            return None
        self.steem.rpc.set_next_node_on_empty_reply(False)
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

            Prices/Rates are denoted in 'base', i.e. the SBD_STEEM market
            is priced in STEEM per SBD.

            **Example:** in the SBD_STEEM market, a price of 300 means
            a SBD is worth 300 STEEM

            .. note::

                All prices returned are in the **reversed** orientation as the
                market. I.e. in the STEEM/SBD market, prices are SBD per STEEM.
                That way you can multiply prices with `1.05` to get a +5%.

            .. warning::

                Since buy orders are placed as
                limit-sell orders for the base asset,
                you may end up obtaining more of the
                buy asset than you placed the order
                for. Example:

                    * You place and order to buy 10 SBD for 100 STEEM/SBD
                    * This means that you actually place a sell order for 1000 STEEM in order to obtain **at least** 10 SBD
                    * If an order on the market exists that sells SBD for cheaper, you will end up with more than 10 SBD
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

            Prices/Rates are denoted in 'base', i.e. the SBD_STEEM market
            is priced in STEEM per SBD.

            **Example:** in the SBD_STEEM market, a price of 300 means
            a SBD is worth 300 STEEM

            .. note::

                All prices returned are in the **reversed** orientation as the
                market. I.e. in the STEEM/SBD market, prices are SBD per STEEM.
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
            only the "orderNumbers".

            :param int/list orderNumbers: A single order number or a list of order numbers
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

    @staticmethod
    def _weighted_average(values, weights):
        """ Calculates a weighted average
        """
        if not (len(values) == len(weights) and len(weights) > 0):
            raise AssertionError("Length of both array must be the same and greater than zero!")
        return sum(x * y for x, y in zip(values, weights)) / sum(weights)

    @staticmethod
    def btc_usd_ticker(verbose=False):
        """ Returns the BTC/USD price from bitfinex, gdax, kraken, okcoin and bitstamp. The mean price is
            weighted by the exchange volume.
        """
        prices = {}
        urls = [
            "https://api.bitfinex.com/v1/pubticker/BTCUSD",
            "https://api.gdax.com/products/BTC-USD/ticker",
            "https://api.kraken.com/0/public/Ticker?pair=XBTUSD",
            "https://www.okcoin.com/api/v1/ticker.do?symbol=btc_usd",
            "https://www.bitstamp.net/api/v2/ticker/btcusd/",
        ]
        responses = list(requests.get(u, timeout=30) for u in urls)

        for r in [x for x in responses
                  if hasattr(x, "status_code") and x.status_code == 200 and x.json()]:
            try:
                if "bitfinex" in r.url:
                    data = r.json()
                    prices['bitfinex'] = {
                        'price': float(data['last_price']),
                        'volume': float(data['volume'])}
                elif "gdax" in r.url:
                    data = r.json()
                    prices['gdax'] = {
                        'price': float(data['price']),
                        'volume': float(data['volume'])}
                elif "kraken" in r.url:
                    data = r.json()['result']['XXBTZUSD']['p']
                    prices['kraken'] = {
                        'price': float(data[0]),
                        'volume': float(data[1])}
                elif "okcoin" in r.url:
                    data = r.json()["ticker"]
                    prices['okcoin'] = {
                        'price': float(data['last']),
                        'volume': float(data['vol'])}
                elif "bitstamp" in r.url:
                    data = r.json()
                    prices['bitstamp'] = {
                        'price': float(data['last']),
                        'volume': float(data['volume'])}
            except KeyError as e:
                log.info(str(e))

        if verbose:
            print(prices)

        if len(prices) == 0:
            raise RuntimeError("Obtaining BTC/USD prices has failed from all sources.")

        # vwap
        return Market._weighted_average(
            [x['price'] for x in prices.values()],
            [x['volume'] for x in prices.values()])

    @staticmethod
    def steem_btc_ticker():
        """ Returns the STEEM/BTC price from bittrex, binance, huobi and upbit. The mean price is
            weighted by the exchange volume.
        """
        prices = {}
        urls = [
            # "https://poloniex.com/public?command=returnTicker",
            "https://bittrex.com/api/v1.1/public/getmarketsummary?market=BTC-STEEM",
            "https://api.binance.com/api/v1/ticker/24hr",
            "https://api.huobi.pro/market/history/kline?period=1day&size=1&symbol=steembtc",
            "https://crix-api.upbit.com/v1/crix/trades/ticks?code=CRIX.UPBIT.BTC-STEEM&count=1",
        ]
        headers = {'Content-type': 'application/x-www-form-urlencoded',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36'}
        responses = list(requests.get(u, headers=headers, timeout=30) for u in urls)

        for r in [x for x in responses
                  if hasattr(x, "status_code") and x.status_code == 200 and x.json()]:
            try:
                if "poloniex" in r.url:
                    data = r.json()["BTC_STEEM"]
                    prices['poloniex'] = {
                        'price': float(data['last']),
                        'volume': float(data['baseVolume'])}
                elif "bittrex" in r.url:
                    data = r.json()["result"][0]
                    price = (data['Bid'] + data['Ask']) / 2
                    prices['bittrex'] = {'price': price, 'volume': data['BaseVolume']}
                elif "binance" in r.url:
                    data = [x for x in r.json() if x['symbol'] == 'STEEMBTC'][0]
                    prices['binance'] = {
                        'price': float(data['lastPrice']),
                        'volume': float(data['quoteVolume'])}
                elif "huobi" in r.url:
                    data = r.json()["data"][-1]
                    prices['huobi'] = {
                        'price': float(data['close']),
                        'volume': float(data['vol'])}
                elif "upbit" in r.url:
                    data = r.json()[-1]
                    prices['upbit'] = {
                        'price': float(data['tradePrice']),
                        'volume': float(data['tradeVolume'])}
            except KeyError as e:
                log.info(str(e))

        if len(prices) == 0:
            raise RuntimeError("Obtaining STEEM/BTC prices has failed from all sources.")

        return Market._weighted_average(
            [x['price'] for x in prices.values()],
            [x['volume'] for x in prices.values()])

    def steem_usd_implied(self):
        """Returns the current STEEM/USD market price"""
        return self.steem_btc_ticker() * self.btc_usd_ticker()
