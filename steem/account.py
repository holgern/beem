from steem.instance import shared_steem_instance
from .exceptions import AccountDoesNotExistsException
from .blockchainobject import BlockchainObject

import json

class Account(BlockchainObject):
    """ This class allows to easily access Account data

        :param str account_name: Name of the account
        :param steem.steem.Steem steem_instance: Steem
               instance
        :param bool lazy: Use lazy loading
        :param bool full: Obtain all account data including orders, positions,
               etc.
        :returns: Account data
        :rtype: dictionary
        :raises steem.exceptions.AccountDoesNotExistsException: if account
                does not exist

        Instances of this class are dictionaries that come with additional
        methods (see below) that allow dealing with an account and it's
        corresponding functions.

        .. code-block:: python

            from steem.account import Account
            account = Account("test")
            print(account)

        .. note:: This class comes with its own caching function to reduce the
                  load on the API server. Instances of this class can be
                  refreshed with ``Account.refresh()``.

    """

    type_id = 2

    def __init__(
        self,
        account,
        id_item ="name",
        full=False,
        lazy=False,
        steem_instance=None
    ):
        self.full = full
        super().__init__(
            account,
            lazy=lazy,
            full=full,
            id_item = "name",
            steem_instance=steem_instance
        )

    def refresh(self):
        """ Refresh/Obtain an account's data from the API server
        """
        if self.full:
            account = self.steem.rpc.get_accounts(
                [self.identifier])
        else:
            account = self.steem.rpc.lookup_account_names(
                    [self.identifier])
        if not account:
            raise AccountDoesNotExistsException(self.identifier)
        else:
            account = account[0]
        if not account:
            raise AccountDoesNotExistsException(self.identifier)        
        # self.identifier = account["id"]

        super(Account, self).__init__(account,id_item="name")

    def getSimilarAccountNames(self,limit=5):
        """ Returns limit similar accounts with name as array
        """
        return self.steem.rpc.lookup_accounts(self.name,limit)

    @property
    def name(self):
        return self["name"]

    @property
    def profile(self):
        """ Returns the account profile
        """
        return json.loads(self["json_metadata"])["profile"]

    @property
    def sp(self):
        """ Returns the accounts Steem Power
        """
        vests = self["vesting_shares"]

    @property
    def available_balances(self):
        """ List balances of an account. This call returns instances of
            :class:`steem.amount.Amount`.
        """
        from .amount import Amount
        available_str = [self["balance"], self["sbd_balance"], self["vesting_shares"]]
        return [
            Amount(b, steem_instance=self.steem)
            for b in available_str # if int(b["amount"]) > 0
        ]

    @property
    def saving_balances(self):
        from .amount import Amount
        savings_str = [self["savings_balance"], self["savings_sbd_balance"]]
        return [
            Amount(b, steem_instance=self.steem)
            for b in savings_str # if int(b["amount"]) > 0
        ]

    @property
    def reward_balances(self):
        from .amount import Amount
        rewards_str = [self["reward_steem_balance"], self["reward_sbd_balance"], self["reward_vesting_balance"]]
        return [
            Amount(b, steem_instance=self.steem)
            for b in rewards_str # if int(b["amount"]) > 0
        ]

    @property
    def total_balances(self):

        return [ self.balance(self.available_balances, "STEEM") + self.balance(self.saving_balances, "STEEM") + 
                        self.balance(self.reward_balances, "STEEM"),
                 self.balance(self.available_balances, "SBD") + self.balance(self.saving_balances, "SBD") +
                      self.balance(self.reward_balances, "SBD"),
                 self.balance(self.available_balances, "VESTS") + self.balance(self.reward_balances, "VESTS"),
        ]

    @property
    def get_balances(self):

        return {
            'available': self.available_balances,
            'savings': self.saving_balances,
            'rewards': self.reward_balances,
            'total': self.total_balances,
        }

    def balance(self, balances, symbol):
        """ Obtain the balance of a specific Asset. This call returns instances of
            :class:`steem.amount.Amount`.
        """
        if isinstance(balances,str):
            if balances == "available":
                balances = self.available_balances
            elif balances == "saving":
                balances = self.saving_balances
            elif balances == "reward":
                balances = self.reward_balances
            elif balances == "total":
                balances = self.total_balances
            else:
                return
        from .amount import Amount
        if isinstance(symbol, dict) and "symbol" in symbol:
            symbol = symbol["symbol"]
        
        for b in balances:
            if b["symbol"] == symbol:
                return b
        return Amount(0, symbol)

    @property
    def is_fully_loaded(self):
        """ Is this instance fully loaded / e.g. all data available?
        """
        return (self.full and "votes" in self)

    def ensure_full(self):
        if not self.is_fully_loaded:
            self.full = True
            self.refresh()

    def history(
        self, first=None,
        limit=100,
        only_ops=[], exclude_ops=[]
    ):
        """ Returns a generator for individual account transactions. The
            latest operation will be first. This call can be used in a
            ``for`` loop.

            :param int first: sequence number of the first
                transaction to return (*optional*)
            :param int limit: limit number of transactions to
                return (*optional*)
            :param array only_ops: Limit generator by these
                operations (*optional*)
            :param array exclude_ops: Exclude thse operations from
                generator (*optional*)
        """
        from steembase.operations import getOperationNameForId
        _limit = 100
        cnt = 0

        mostrecent = self.steem.rpc.get_account_history(
            self["name"],
            -1,
            1
        )
        if not mostrecent:
            return

        if not first:
            # first = int(mostrecent[0].get("id").split(".")[2]) + 1
            first = 9999999999

        while True:
            # RPC call
            txs = self.steem.rpc.get_account_history(
                self["name"],
                first,
                _limit,
            )
            for i in txs:
                if exclude_ops and i[1]["op"][0] in exclude_ops:
                    continue
                if not only_ops or i[1]["op"][0] in only_ops:
                    cnt += 1
                    yield i
                    if limit >= 0 and cnt >= limit:
                        return

            if not txs:
                break
            if len(txs) < _limit:
                break
            # first = int(txs[-1]["id"].split(".")[2])
            first = txs[-1][1]["block"]

    # def upgrade(self):
    #    return self.steem.upgrade_account(account=self)


class AccountUpdate(dict):
    """ This purpose of this class is to keep track of account updates
        as they are pushed through by :class:`steem.notify.Notify`.

        Instances of this class are dictionaries and take the following
        form:

        ... code-block: js

            {'id': '2.6.29',
             'lifetime_fees_paid': '44261516129',
             'most_recent_op': '2.9.0',
             'owner': '1.2.29',
             'pending_fees': 0,
             'pending_vested_fees': 16310,
             'total_core_in_orders': '6788845277634',
             'total_ops': 0}

    """

    def __init__(
        self,
        data,
        steem_instance=None
    ):
        self.steem = steem_instance or shared_steem_instance()

        if isinstance(data, dict):
            super(AccountUpdate, self).__init__(data)
        else:
            account = Account(data, steem_instance=self.steem)
            update = self.steem.rpc.get_objects([
                "2.6.%s" % (account["id"].split(".")[2])
            ])[0]
            super(AccountUpdate, self).__init__(update)

    @property
    def account(self):
        """ In oder to obtain the actual
            :class:`steem.account.Account` from this class, you can
            use the ``account`` attribute.
        """
        account = Account(self["owner"])
        account.refresh()
        return account

    def __repr__(self):
        return "<AccountUpdate: {}>".format(self["owner"])
