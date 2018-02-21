from beem.instance import shared_steem_instance
from datetime import datetime, timedelta
from .utils import (
    formatTimeFromNow, formatTime, formatTimeString, assets_from_string)
from .asset import Asset
from .amount import Amount
from .price import Price, Order, FilledOrder
from .account import Account
from beembase import operations


class Market(dict):
    """ This class allows to easily access Markets on the blockchain for trading, etc.

        :param steem.steem.Steem steem_instance: Steem instance
        :param steem.asset.Asset base: Base asset
        :param steem.asset.Asset quote: Quote asset
        :returns: Blockchain Market
        :rtype: dictionary with overloaded methods

        Instances of this class are dictionaries that come with additional
        methods (see below) that allow dealing with a market and it's
        corresponding functions.

        This class tries to identify **two** assets as provided in the
        parameters in one of the following forms:

        * ``base`` and ``quote`` are valid assets (according to :class:`steem.asset.Asset`)
        * ``base:quote`` separated with ``:``
        * ``base/quote`` separated with ``/``
        * ``base-quote`` separated with ``-``

        .. note:: Throughout this library, the ``quote`` symbol will be
                  presented first (e.g. ``USD:BTS`` with ``USD`` being the
                  quote), while the ``base`` only refers to a secondary asset
                  for a trade. This means, if you call
                  :func:`steem.market.Market.sell` or
                  :func:`steem.market.Market.buy`, you will sell/buy **only
                  quote** and obtain/pay **only base**.

    """

    def __init__(
        self,
        *args,
        base=None,
        quote=None,
        steem_instance=None,
        **kwargs
    ):
        self.steem = steem_instance or shared_steem_instance()

        if len(args) == 1 and isinstance(args[0], str):
            quote_symbol, base_symbol = assets_from_string(args[0])
            quote = Asset(quote_symbol, steem_instance=self.steem)
            base = Asset(base_symbol, steem_instance=self.steem)
            super(Market, self).__init__({"base": base, "quote": quote})
        elif len(args) == 0 and base and quote:
            super(Market, self).__init__({"base": base, "quote": quote})
        elif len(args) == 2 and not base and not quote:
            super(Market, self).__init__({"base": args[1], "quote": args[0]})
        else:
            raise ValueError("Unknown Market Format: %s" % str(args))

    def get_string(self, separator=":"):
        """ Return a formated string that identifies the market, e.g. ``USD:BTS``

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

    def ticker(self):
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
        cer = self["quote"]["options"]["core_exchange_rate"]
        data["core_exchange_rate"] = Price(
            cer,
            steem_instance=self.steem
        )
        if cer["base"]["asset_id"] == self["quote"]["id"]:
            data["core_exchange_rate"] = data["core_exchange_rate"].invert()

        ticker = self.steem.rpc.get_ticker(
            self["base"]["id"],
            self["quote"]["id"],
        )
        data["baseVolume"] = Amount(ticker["base_volume"], self["base"], steem_instance=self.steem)
        data["quoteVolume"] = Amount(ticker["quote_volume"], self["quote"], steem_instance=self.steem)
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

    def volume24h(self):
        """ Returns the 24-hour volume for all markets, plus totals for primary currencies.

            Sample output:

            .. code-block:: js

                {
                    "BTS": 361666.63617,
                    "USD": 1087.0
                }

        """
        volume = self.steem.rpc.get_24_volume(
            self["base"]["id"],
            self["quote"]["id"],
        )
        return {
            self["base"]["symbol"]: Amount(volume["base_volume"], self["base"], steem_instance=self.steem),
            self["quote"]["symbol"]: Amount(volume["quote_volume"], self["quote"], steem_instance=self.steem)
        }

    def orderbook(self, limit=25):
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
        orders = self.steem.rpc.get_order_book(
            self["base"]["id"],
            self["quote"]["id"],
            limit
        )
        asks = list(map(lambda x: Order(
            Amount(x["quote"], self["quote"], steem_instance=self.steem),
            Amount(x["base"], self["base"], steem_instance=self.steem),
            steem_instance=self.steem
        ), orders["asks"]))
        bids = list(map(lambda x: Order(
            Amount(x["quote"], self["quote"], steem_instance=self.steem),
            Amount(x["base"], self["base"], steem_instance=self.steem),
            steem_instance=self.steem
        ), orders["bids"]))
        data = {"asks": asks, "bids": bids}
        return data

    def trades(self, limit=25, start=None, stop=None):
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
        orders = self.steem.rpc.get_trade_history(
            self["base"]["symbol"],
            self["quote"]["symbol"],
            formatTime(stop),
            formatTime(start),
            limit)
        return list(map(
            lambda x: FilledOrder(
                x,
                quote=Amount(x["amount"], self["quote"], steem_instance=self.steem),
                base=Amount(float(x["amount"]) * float(x["price"]), self["base"], steem_instance=self.steem),
                steem_instance=self.steem
            ), orders
        ))

    def accounttrades(self, account=None, limit=25):
        """ Returns your trade history for a given market, specified by
            the "currencyPair" parameter. You may also specify "all" to
            get the orderbooks of all markets.

            :param str currencyPair: Return results for a particular market only (default: "all")
            :param int limit: Limit the amount of orders (default: 25)

            Output Parameters:

                - `type`: sell or buy
                - `rate`: price for `quote` denoted in `base` per `quote`
                - `amount`: amount of quote
                - `total`: amount of base at asked price (amount/price)

            .. note:: This call goes through the trade history and
                      searches for your account, if there are no orders
                      within ``limit`` trades, this call will return an
                      empty array.

        """
        if not account:
            if "default_account" in self.steem.config:
                account = self.steem.config["default_account"]
        if not account:
            raise ValueError("You need to provide an account")
        account = Account(account, steem_instance=self.steem)

        filled = self.steem.rpc.get_fill_order_history(
            self["base"]["id"],
            self["quote"]["id"],
            2 * limit,
            api="history"
        )
        trades = []
        for f in filled:
            if f["op"]["account_id"] == account["id"]:
                trades.append(
                    FilledOrder(
                        f,
                        base=self["base"],
                        quote=self["quote"],
                        steem_instance=self.steem
                    ))
        return trades

    def accountopenorders(self, account=None):
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
        orders = account["limit_orders"]
        for o in orders:
            if ((
                o["sell_price"]["base"]["asset_id"] == self["base"]["id"] and
                o["sell_price"]["quote"]["asset_id"] == self["quote"]["id"]
            ) or (
                o["sell_price"]["base"]["asset_id"] == self["quote"]["id"] and
                o["sell_price"]["quote"]["asset_id"] == self["base"]["id"]
            )):
                r.append(Order(
                    o,
                    steem_instance=self.steem
                ))
        return r

    def buy(
        self,
        price,
        amount,
        expiration=None,
        killfill=False,
        account=None,
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
            assert(amount["asset"]["symbol"] == self["quote"]["symbol"]), \
                "Price: {} does not match amount: {}".format(
                    str(price), str(amount))
        else:
            amount = Amount(amount, self["quote"]["symbol"], steem_instance=self.steem)

        order = operations.Limit_order_create(**{
            "fee": {"amount": 0, "asset_id": "1.3.0"},
            "seller": account["id"],
            "amount_to_sell": {
                "amount": int(float(amount) * float(price) * 10 ** self["base"]["precision"]),
                "asset_id": self["base"]["id"]
            },
            "min_to_receive": {
                "amount": int(float(amount) * 10 ** self["quote"]["precision"]),
                "asset_id": self["quote"]["id"]
            },
            "expiration": formatTimeFromNow(expiration),
            "fill_or_kill": killfill,
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
            assert(amount["asset"]["symbol"] == self["quote"]["symbol"]), \
                "Price: {} does not match amount: {}".format(
                    str(price), str(amount))
        else:
            amount = Amount(amount, self["quote"]["symbol"], steem_instance=self.steem)

        order = operations.Limit_order_create(**{
            "fee": {"amount": 0, "asset_id": "1.3.0"},
            "seller": account["id"],
            "amount_to_sell": {
                "amount": int(float(amount) * 10 ** self["quote"]["precision"]),
                "asset_id": self["quote"]["id"]
            },
            "min_to_receive": {
                "amount": int(float(amount) * float(price) * 10 ** self["base"]["precision"]),
                "asset_id": self["base"]["id"]
            },
            "expiration": formatTimeFromNow(expiration),
            "fill_or_kill": killfill,
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

    def cancel(self, orderNumber, account=None):
        """ Cancels an order you have placed in a given market. Requires
            only the "orderNumber". An order number takes the form
            ``1.7.xxx``.

            :param str orderNumber: The Order Object ide of the form ``1.7.xxxx``
        """
        return self.steem.cancel(orderNumber, account=account)

    def core_quote_market(self):
        """ This returns an instance of the market that has the core market of the quote asset.
            It means that quote needs to be a market pegged asset and returns a
            market to it's collateral asset.
        """
        if not self["quote"].is_bitasset:
            raise ValueError("Quote (%s) is not a bitasset!" % self["quote"]["symbol"])
        self["quote"].full = True
        self["quote"].refresh()
        collateral = Asset(
            self["quote"]["bitasset_data"]["options"]["short_backing_asset"],
            steem_instance=self.steem
        )
        return Market(quote=self["quote"], base=collateral)

    def core_base_market(self):
        """ This returns an instance of the market that has the core market of the base asset.
            It means that base needs to be a market pegged asset and returns a
            market to it's collateral asset.
        """
        if not self["base"].is_bitasset:
            raise ValueError("base (%s) is not a bitasset!" % self["base"]["symbol"])
        self["base"].full = True
        self["base"].refresh()
        collateral = Asset(
            self["base"]["bitasset_data"]["options"]["short_backing_asset"],
            steem_instance=self.steem
        )
        return Market(quote=self["base"], base=collateral)
