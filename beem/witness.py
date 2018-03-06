# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from beem.instance import shared_steem_instance
from beemgraphenebase.py23 import bytes_types, integer_types, string_types, text_type
from .account import Account
from .amount import Amount
from .exceptions import WitnessDoesNotExistsException
from .blockchainobject import BlockchainObject
from .utils import formatTimeString
from datetime import datetime, timedelta
from beembase import transactions, operations
from beembase.account import PrivateKey, PublicKey
import pytz


class Witness(BlockchainObject):
    """ Read data about a witness in the chain

        :param str account_name: Name of the witness
        :param steem steem_instance: Steem() instance to use when
               accesing a RPC

        .. code-block:: python

           from beem.witness import Witness
           Witness("gtg")

    """
    type_id = 3

    def __init__(
        self,
        owner,
        full=False,
        lazy=False,
        steem_instance=None
    ):
        self.full = full
        super(Witness, self).__init__(
            owner,
            lazy=lazy,
            full=full,
            id_item="owner",
            steem_instance=steem_instance
        )

    def refresh(self):
        if not self.identifier:
            return
        if self.steem.rpc.get_use_appbase():
            witness = self.steem.rpc.find_witnesses({'owners': [self.identifier]}, api="database")['witnesses']
            if len(witness) > 0:
                witness = witness[0]
        else:
            witness = self.steem.rpc.get_witness_by_account(self.identifier)
        if not witness:
            raise WitnessDoesNotExistsException
        super(Witness, self).__init__(witness, id_item="owner", steem_instance=self.steem)
        self.identifier = self["owner"]

    @property
    def account(self):
        return Account(self["owner"], steem_instance=self.steem)

    def feed_publish(self,
                     base,
                     quote="1.000 STEEM",
                     account=None):
        """ Publish a feed price as a witness.
            :param float base: USD Price of STEEM in SBD (implied price)
            :param float quote: (optional) Quote Price. Should be 1.000, unless
            we are adjusting the feed to support the peg.
            :param str account: (optional) the source account for the transfer
            if not self["owner"]
        """
        if not account:
            account = self["owner"]
        if not account:
            raise ValueError("You need to provide an account")

        account = Account(account, steem_instance=self.steem)
        if isinstance(base, Amount):
            base = Amount(base, steem_instance=self.steem)
        elif isinstance(base, string_types):
            base = Amount(base, steem_instance=self.steem)
        else:
            base = Amount(base, "SBD", steem_instance=self.steem)

        if isinstance(quote, Amount):
            quote = Amount(quote, steem_instance=self.steem)
        elif isinstance(quote, string_types):
            quote = Amount(quote, steem_instance=self.steem)
        else:
            quote = Amount(quote, "STEEM", steem_instance=self.steem)

        if not base.symbol == "SBD":
            raise AssertionError()
        if not quote.symbol == "STEEM":
            raise AssertionError()

        op = operations.Feed_publish(
            **{
                "publisher": account["name"],
                "exchange_rate": {
                    "base": base,
                    "quote": quote,
                },
                "prefix": self.steem.prefix,
            })
        return self.steem.finalizeOp(op, account, "active")

    def update(self, signing_key, url, props, account=None):
        """ Update witness
            :param pubkey signing_key: Signing key
            :param str url: URL
            :param dict props: Properties
            :param str account: (optional) witness account name
             Properties:::
                {
                    "account_creation_fee": x,
                    "maximum_block_size": x,
                    "sbd_interest_rate": x,
                }
        """
        if not account:
            account = self["owner"]
        if not account:
            raise ValueError("You need to provide an account")

        account = Account(account, steem_instance=self.steem)

        try:
            PublicKey(signing_key)
        except Exception as e:
            raise e

        op = operations.Witness_update(
            **{
                "owner": account["name"],
                "url": url,
                "block_signing_key": signing_key,
                "props": props,
                "fee": "0.000 STEEM",
                "prefix": self.steem.prefix,
            })
        return self.steem.finalizeOp(op, account, "active")


class WitnessesObject(list):
    def printAsTable(self, sort_key="votes", reverse=True):
        utc = pytz.timezone('UTC')
        if sort_key == 'base':
            sortedList = sorted(self, key=lambda self: self['sbd_exchange_rate']['base'], reverse=reverse)
        elif sort_key == 'quote':
            sortedList = sorted(self, key=lambda self: self['sbd_exchange_rate']['quote'], reverse=reverse)
        elif sort_key == 'last_sbd_exchange_update':
            sortedList = sorted(self, key=lambda self: (utc.localize(datetime.now()) - formatTimeString(self['last_sbd_exchange_update'])).total_seconds(), reverse=reverse)
        elif sort_key == 'account_creation_fee':
            sortedList = sorted(self, key=lambda self: self['props']['account_creation_fee'], reverse=reverse)
        elif sort_key == 'sbd_interest_rate':
            sortedList = sorted(self, key=lambda self: self['props']['sbd_interest_rate'], reverse=reverse)
        elif sort_key == 'maximum_block_size':
            sortedList = sorted(self, key=lambda self: self['props']['maximum_block_size'], reverse=reverse)
        elif sort_key == 'votes':
            sortedList = sorted(self, key=lambda self: int(self[sort_key]), reverse=reverse)
        else:
            sortedList = sorted(self, key=lambda self: self[sort_key], reverse=reverse)
        for witness in sortedList:
            outstr = ''
            outstr += witness['owner'][:15].ljust(15) + " \t " + str(round(int(witness['votes']) / 1e15, 2)).ljust(5) + " PV - " + str(witness['total_missed']).ljust(5)
            outstr += " missed - feed:" + witness['sbd_exchange_rate']['base'] + "/" + witness['sbd_exchange_rate']['quote']
            td = utc.localize(datetime.now()) - formatTimeString(witness['last_sbd_exchange_update'])
            outstr += " " + str(td.days) + " days " + str(td.seconds // 3600) + ":" + str((td.seconds // 60) % 60) + " \t "
            outstr += str(witness['props']['account_creation_fee']) + " " + str(witness['props']['maximum_block_size']) + " Blocks "
            outstr += str(witness['props']['sbd_interest_rate']) + " \t " + witness['running_version']
            print(outstr)


class Witnesses(WitnessesObject):
    """ Obtain a list of **active** witnesses and the current schedule

        :param steem steem_instance: Steem() instance to use when
            accesing a RPC
    """
    def __init__(self, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        if self.steem.rpc.get_use_appbase():
            self.active_witnessess = self.steem.rpc.find_witnesses(api="database")['witnesses']
            self.schedule = self.steem.rpc.get_witness_schedule(api="database")
        else:
            self.active_witnessess = self.steem.rpc.get_active_witnesses()
            self.schedule = self.steem.rpc.get_witness_schedule()
            self.witness_count = self.steem.rpc.get_witness_count()

        super(Witnesses, self).__init__(
            [
                Witness(x, lazy=True, steem_instance=self.steem)
                for x in self.active_witnessess
            ]
        )


class WitnessesVotedByAccount(WitnessesObject):
    """ Obtain a list of witnesses which have been voted by an account

        :param str account: Account name
        :param steem steem_instance: Steem() instance to use when
            accesing a RPC
    """
    def __init__(self, account, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        self.account = Account(account, full=True)
        if "witness_votes" not in self.account:
            return
        witnessess = self.account["witness_votes"]

        super(WitnessesVotedByAccount, self).__init__(
            [
                Witness(x, lazy=True, steem_instance=self.steem)
                for x in witnessess
            ]
        )


class WitnessesRankedByVote(WitnessesObject):
    """ Obtain a list of witnesses ranked by Vote

        :param str from_account: Witness name
        :param steem steem_instance: Steem() instance to use when
            accesing a RPC
    """
    def __init__(self, from_account="", limit=100, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        witnessList = []
        last_limit = limit
        last_account = from_account
        if limit > 100:
            while last_limit > 100:
                tmpList = WitnessesRankedByVote(last_account, 100)
                if (last_limit < limit):
                    witnessList.extend(tmpList[1:])
                    last_limit -= 99
                else:
                    witnessList.extend(tmpList)
                    last_limit -= 100
                last_account = witnessList[-1]["owner"]
        if (last_limit < limit):
            last_limit += 1
        if self.steem.rpc.get_use_appbase():
            witnessess = self.steem.rpc.list_witness_votes({'start': last_account, 'limit': last_limit, 'order': 'by_votes'}, api="database")['votes']
        else:
            witnessess = self.steem.rpc.get_witnesses_by_vote(last_account, last_limit)
        # self.witness_count = len(self.voted_witnessess)
        if (last_limit < limit):
            witnessess = witnessess[1:]
        if len(witnessess) > 0:
            for x in witnessess:
                witnessList.append(Witness(x, lazy=True, steem_instance=self.steem))
        if len(witnessList) == 0:
            return
        super(WitnessesRankedByVote, self).__init__(witnessList)


class ListWitnesses(WitnessesObject):
    """ Obtain a list of witnesses which have been voted by an account

        :param str from_account: Account name
        :param steem steem_instance: Steem() instance to use when
            accesing a RPC
    """
    def __init__(self, from_account, limit, steem_instance=None):
        self.steem = steem_instance or shared_steem_instance()
        if self.steem.rpc.get_use_appbase():
            witnessess = self.steem.rpc.list_witnesses({'start': from_account, 'limit': limit, 'order': 'by_name'}, api="database")['witnesses']
        else:
            witnessess = self.steem.rpc.lookup_witness_accounts(from_account, limit)
        if len(witnessess) == 0:
            return
        super(ListWitnesses, self).__init__(
            [
                Witness(x, lazy=True, steem_instance=self.steem)
                for x in witnessess
            ]
        )
