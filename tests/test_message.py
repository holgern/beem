import unittest
import mock
from steempy import Steem
from steempy.message import Message
from steempy.instance import set_shared_steem_instance

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
core_unit = "PPY"


class Testcases(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bts = Steem(
            nobroadcast=True,
            wif=[wif]
        )
        set_shared_steem_instance(self.bts)

    def test_sign_message(self):
        def new_refresh(self):
            dict.__init__(
                self, {
                    "name": "test",
                    "memo_key": "STM6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"
                    })

        with mock.patch(
            "steempy.account.Account.refresh",
            new=new_refresh
        ):
            p = Message("message foobar").sign()
            Message(p).verify()

    def test_verify_message(self):
        def new_refresh(self):
            dict.__init__(
                self, {
                    "name": "test",
                    "memo_key": "STM6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV"
                    })

        with mock.patch(
            "steempy.account.Account.refresh",
            new=new_refresh
        ):
            Message(
                "-----BEGIN BITSHARES SIGNED MESSAGE-----\n"
                "message foobar\n"
                "-----BEGIN META-----\n"
                "account=test\n"
                "memokey=STM6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV\n"
                "block=19902522\n"
                "timestamp=2018-02-15T22:00:54\n"
                "-----BEGIN SIGNATURE-----\n"
                "20093ef63f375b9aa8570188cae3aad953bf6393d43ce6f03bbbd1b429e48c6a587dc012922515f6d327158df5081ea2d595888225f9f1c6c3028781c8f9451fde\n"
                "-----END BITSHARES SIGNED MESSAGE-----\n"
            ).verify()

            Message(
                "-----BEGIN BITSHARES SIGNED MESSAGE-----"
                "message foobar\n"
                "-----BEGIN META-----"
                "account=test\n"
                "memokey=STM6MRyAjQq8ud7hVNYcfnVPJqcVpscN5So8BhtHuGYqET5GDW5CV\n"
                "block=19902522\n"
                "timestamp=2018-02-15T22:00:54\n"
                "-----BEGIN SIGNATURE-----"
                "20093ef63f375b9aa8570188cae3aad953bf6393d43ce6f03bbbd1b429e48c6a587dc012922515f6d327158df5081ea2d595888225f9f1c6c3028781c8f9451fde\n"
                "-----END BITSHARES SIGNED MESSAGE-----"
            ).verify()
