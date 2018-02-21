import unittest
import mock
from steempy import Steem
from steempy.message import Message
from steempy.account import Account
from steempy.instance import set_shared_steem_instance

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
core_unit = "STM"
nodes = ["wss://steemd.pevo.science", "wss://gtg.steem.house:8090", "wss://rpc.steemliberator.com", "wss://rpc.buildteam.io",
         "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://node.steem.ws", "wss://steemd.steemgigs.org", "wss://steemd.steemit.com",
         "wss://steemd.minnowsupportproject.org"]


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bts = Steem(
            nodes,
            nobroadcast=True,
            wif=[wif]
        )
        set_shared_steem_instance(self.bts)

    def test_sign_message(self):
        def new_refresh(self):
            dict.__init__(
                self, {
                "identifier": "test",
                "name": "test",
                "id_item": "name",
                "memo_key": "STM6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"
                })

        with mock.patch(
            "steempy.account.Account.refresh",
            new=new_refresh
        ):
            account = Account("test")
            account["memo_key"] = "STM6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"
            p = Message("message foobar").sign(account=account)
            Message(p).verify(account=account)

    def test_verify_message(self):
        def new_refresh(self):
            dict.__init__(
                self, {
                "identifier": "test",
                "name": "test",
                "id_item": "name",
                "memo_key": "STM6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"
                })

        with mock.patch(
            "steempy.account.Account.refresh",
            new=new_refresh
        ):
            Message(
                "-----BEGIN STEEM SIGNED MESSAGE-----\n"
                "message foobar\n"
                "-----BEGIN META-----\n"
                "account=test\n"
                "memokey=STM6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV\n"
                "block=19902522\n"
                "timestamp=2018-02-15T22:00:54\n"
                "-----BEGIN SIGNATURE-----\n"
                "20093ef63f375b9aa8570188cae3aad953bf6393d43ce6f03bbbd1b429e48c6a587dc012922515f6d327158df5081ea2d595888225f9f1c6c3028781c8f9451fde\n"
                "-----END STEEM SIGNED MESSAGE-----\n"
            ).verify()

            Message(
                "-----BEGIN STEEM SIGNED MESSAGE-----"
                "message foobar\n"
                "-----BEGIN META-----"
                "account=test\n"
                "memokey=STM6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV\n"
                "block=19902522\n"
                "timestamp=2018-02-15T22:00:54\n"
                "-----BEGIN SIGNATURE-----"
                "20093ef63f375b9aa8570188cae3aad953bf6393d43ce6f03bbbd1b429e48c6a587dc012922515f6d327158df5081ea2d595888225f9f1c6c3028781c8f9451fde\n"
                "-----END STEEM SIGNED MESSAGE-----"
            ).verify()
