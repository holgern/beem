from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import bytes
from builtins import chr
from builtins import range
from builtins import super
import random
import unittest
from pprint import pprint
from binascii import hexlify
from collections import OrderedDict

from beembase import (
    transactions,
    memo,
    operations,
    objects
)
from beembase.objects import Operation
from beembase.signedtransactions import Signed_Transaction
from beemgraphenebase.account import PrivateKey
from beemgraphenebase import account
from beembase.operationids import getOperationNameForId
from beemgraphenebase.py23 import py23_bytes, bytes_types
from beem.amount import Amount
from beem.asset import Asset
from beem.steem import Steem


TEST_AGAINST_CLI_WALLET = False

prefix = u"STEEM"
default_prefix = u"STM"
wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
ref_block_num = 34294
ref_block_prefix = 3707022213
expiration = "2016-04-06T08:29:27"


class Testcases(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.stm = Steem(
            offline=True
        )

    def doit(self, printWire=False, ops=None):
        if ops is None:
            ops = [Operation(self.op)]
        tx = Signed_Transaction(ref_block_num=ref_block_num,
                                ref_block_prefix=ref_block_prefix,
                                expiration=expiration,
                                operations=ops)
        tx = tx.sign([wif], chain=prefix)
        tx.verify([PrivateKey(wif, prefix=u"STM").pubkey], prefix)
        txWire = hexlify(py23_bytes(tx)).decode("ascii")
        if printWire:
            print()
            print(txWire)
            print()
        self.assertEqual(self.cm[:-130], txWire[:-130])

        if TEST_AGAINST_CLI_WALLET:
            from grapheneapi.grapheneapi import GrapheneAPI
            rpc = GrapheneAPI("localhost", 8092)
            self.cm = rpc.serialize_transaction(tx.json())
            # print("soll: %s" % self.cm[:-130])
            # print("ist:  %s" % txWire[:-130])
            # print(txWire[:-130] == self.cm[:-130])
            self.assertEqual(self.cm[:-130], txWire[:-130])

    def test_Empty_Op(self):
        self.cm = (u"f68585abf4dce7c8045700000120020c2218cd5bcbaf3bdaba2f192a7"
                   "a69cb2307fcc6be2c09e45e204d175fc5fb715df86fcccfa1235babe6"
                   "09461cc9fdfadbae06381d711576fb4265bd832008")
        self.doit(ops=[])

    def test_Transfer(self):
        self.op = operations.Transfer(**{
            "from": "foo",
            "to": "baar",
            "amount": Amount("111.110 STEEM", steem_instance=self.stm),
            "memo": "Fooo",
            "prefix": default_prefix
        })
        self.cm = (u"f68585abf4dce7c80457010203666f6f046261617206b201000000"
                   "000003535445454d000004466f6f6f00012025416c234dd5ff15d8"
                   "b45486833443c128002bcafa57269cada3ad213ef88adb5831f63a"
                   "58d8b81bbdd92d494da01eeb13ee1786d02ce075228b25d7132f8f"
                   "3e")
        self.doit()

    def test_create_account(self):
        self.op = operations.Account_create(
            **{
                'creator':
                'xeroc',
                'fee':
                '10.000 STEEM',
                'json_metadata':
                '',
                'memo_key':
                'STM6zLNtyFVToBsBZDsgMhgjpwysYVbsQD6YhP3kRkQhANUB4w7Qp',
                'new_account_name':
                'fsafaasf',
                'owner': {
                    'account_auths': [],
                    'key_auths': [[
                        'STM5jYVokmZHdEpwo5oCG3ES2Ca4VYz'
                        'y6tM8pWWkGdgVnwo2mFLFq', 1
                    ], [
                        'STM6zLNtyFVToBsBZDsgMhgjpwysYVb'
                        'sQD6YhP3kRkQhANUB4w7Qp', 1
                    ]],
                    'weight_threshold':
                    1
                },
                'active': {
                    'account_auths': [],
                    'key_auths': [[
                        'STM6pbVDAjRFiw6fkiKYCrkz7PFeL7'
                        'XNAfefrsREwg8MKpJ9VYV9x', 1
                    ], [
                        'STM6zLNtyFVToBsBZDsgMhgjpwysYV'
                        'bsQD6YhP3kRkQhANUB4w7Qp', 1
                    ]],
                    'weight_threshold':
                    1
                },
                'posting': {
                    'account_auths': [],
                    'key_auths': [[
                        'STM8CemMDjdUWSV5wKotEimhK6c4d'
                        'Y7p2PdzC2qM1HpAP8aLtZfE7', 1
                    ], [
                        'STM6zLNtyFVToBsBZDsgMhgjpwys'
                        'YVbsQD6YhP3kRkQhANUB4w7Qp', 1
                    ], [
                        'STM6pbVDAjRFiw6fkiKYCrkz7PFeL'
                        '7XNAfefrsREwg8MKpJ9VYV9x', 1
                    ]],
                    'weight_threshold':
                    1
                },
                "prefix": default_prefix
            })

        self.cm = (u"f68585abf4dce7c804570109102700000000000003535445454d000"
                   "0057865726f63086673616661617366010000000002026f6231b8ed"
                   "1c5e964b42967759757f8bb879d68e7b09d9ea6eedec21de6fa4c40"
                   "1000314aa202c9158990b3ec51a1aa49b2ab5d300c97b391df3beb3"
                   "4bb74f3c62699e010001000000000202fe8cc11cc8251de6977636b"
                   "55c1ab8a9d12b0b26154ac78e56e7c4257d8bcf6901000314aa202c"
                   "9158990b3ec51a1aa49b2ab5d300c97b391df3beb34bb74f3c62699"
                   "e010001000000000302fe8cc11cc8251de6977636b55c1ab8a9d12b"
                   "0b26154ac78e56e7c4257d8bcf6901000314aa202c9158990b3ec51"
                   "a1aa49b2ab5d300c97b391df3beb34bb74f3c62699e010003b453f4"
                   "6013fdbccb90b09ba169c388c34d84454a3b9fbec68d5a7819a734f"
                   "ca001000314aa202c9158990b3ec51a1aa49b2ab5d300c97b391df3"
                   "beb34bb74f3c62699e0000012031827ea70b06e413d124d14ed8db3"
                   "99597fa5f94566e031b706533a9090395be1c0ed317c8af01d12ca7"
                   "9258ac4d800adff92a84630b567e5ff48cd4b5f716d6")
        self.doit()

    def test_Transfer_to_vesting(self):
        self.op = operations.Transfer_to_vesting(**{
            "from": "foo",
            "to": "baar",
            "amount": "111.110 STEEM",
            "prefix": default_prefix
        })

        self.cm = (u"f68585abf4dce7c80457010303666f6f046261617206b201000000"
                   "000003535445454d00000001203a34cd45fb4a2585514614be2c1"
                   "ba2365257ce5470d20c6c6abda39204eeba0b7e057d889ca8b1b1"
                   "406f1441520a25d32df2ab9fdb532c3377dc66d0fe41bb3d")
        self.doit()

    def test_withdraw_vesting(self):
        self.op = operations.Withdraw_vesting(**{
            "account": "foo",
            "vesting_shares": "100 VESTS",
            "prefix": default_prefix
        })

        self.cm = (
            u"f68585abf4dce7c80457010403666f6f00e1f5050000000006564553545300000"
            "00120772da57b15b62780ee3d8afedd8d46ffafb8c62788eab5ce01435df99e1d"
            "36de549f260444866ff4e228cac445548060e018a872e7ee99ace324af9844f4c"
            "50a")
        self.doit()

    def test_Comment(self):
        self.op = operations.Comment(
            **{
                "parent_author": "foobara",
                "parent_permlink": "foobarb",
                "author": "foobarc",
                "permlink": "foobard",
                "title": "foobare",
                "body": "foobarf",
                "json_metadata": {
                    "foo": "bar"
                },
                "prefix": default_prefix
            })

        self.cm = (u"f68585abf4dce7c80457010107666f6f6261726107666f6f626172620"
                   "7666f6f6261726307666f6f6261726407666f6f6261726507666f6f62"
                   "6172660e7b22666f6f223a2022626172227d00011f34a882f3b06894c"
                   "29f52e06b8a28187b84b817c0e40f124859970b32511a778736d682f2"
                   "4d3a6e6da124b340668d25bbcf85ffa23ca622b307ffe10cf182bb82")
        self.doit()

    def test_Vote(self):
        self.op = operations.Vote(
            **{
                "voter": "foobara",
                "author": "foobarc",
                "permlink": "foobard",
                "weight": 1000,
                "prefix": default_prefix
            })
        self.cm = (u"f68585abf4dce7c80457010007666f6f6261726107666f6f62617263"
                   "07666f6f62617264e8030001202e09123f732a438ef6d6138484d7ad"
                   "edfdcf4a4f3d171f7fcafe836efa2a3c8877290bd34c67eded824ac0"
                   "cc39e33d154d0617f64af936a83c442f62aef08fec")
        self.doit()

    def test_Transfer_to_savings(self):
        self.op = operations.Transfer_to_savings(
            **{
                "from": "testuser",
                "to": "testuser",
                "amount": "1.000 STEEM",
                "memo": "testmemo",
                "prefix": default_prefix
            })
        self.cm = (
            u"f68585abf4dce7c804570120087465737475736572087465737475736572e8030"
            "0000000000003535445454d000008746573746d656d6f00011f4df74457bf8824"
            "c02da6a722a7c604676c97aad1a51ebcfb7086b0b7c1f19f9257388a06b3c24ae"
            "51d97c9eee5e0ecb7b6c32a29af6f56697f0c7516e70a75ce")
        self.doit()

    def test_Transfer_from_savings(self):
        self.op = operations.Transfer_from_savings(
            **{
                "from": "testuser",
                "request_id": 9001,
                "to": "testser",
                "amount": "100.000 SBD",
                "memo": "memohere",
                "prefix": default_prefix
            })
        self.cm = (
            u"f68585abf4dce7c804570121087465737475736572292300000774657374736"
            "572a0860100000000000353424400000000086d656d6f6865726500012058760"
            "45f4869b6459438019d71d25bdea461899e0a96635c05f19caf424fa1453fc1fe"
            "103d9ca6470d629b9971adddf757c829bb47cc96b29662f294bebb4fb2")
        self.doit()

    def test_Cancel_transfer_from_savings(self):
        self.op = operations.Cancel_transfer_from_savings(**{
            "from": "tesuser",
            "request_id": 9001,
            "prefix": default_prefix
        })

        self.cm = (
            u"f68585abf4dce7c8045701220774657375736572292300000001200942474f672"
            "3937b88e19fb8cade26cc97f68cb626362d0764d134fe837df5262200b5e71bec"
            "13a0673995a584a47674897e959d8c1f83389505895fb64ceda5")
        self.doit()

    def test_order_create(self):
        self.op = operations.Limit_order_create(
            **{
                "owner": "",
                "orderid": 0,
                "amount_to_sell": "0.000 STEEM",
                "min_to_receive": "0.000 STEEM",
                "fill_or_kill": False,
                "expiration": "2016-12-31T23:59:59",
                "prefix": default_prefix
            })

        self.cm = (u"f68585abf4dce7c8045701050000000000000000000000000003535"
                   "445454d0000000000000000000003535445454d0000007f46685800"
                   "011f28a2fc52dcfc19378c5977917b158dfab93e7760259aab7ecdb"
                   "cb82df7b22e1a5527e02fd3aab7d64302ec550c3edcbba29d73226c"
                   "f088273e4fafda89eb7de8")
        self.doit()

    def test_order_create2(self):
        self.op = operations.Limit_order_create2(
            **{
                "owner": "alice",
                "orderid": 492991,
                "amount_to_sell": ["1", 3, "@@000000013"],
                "exchange_rate": {
                    "base": ["1", 3, "@@000000013"],
                    "quote": ["10", 3, "@@000000021"]
                },
                "fill_or_kill": False,
                "expiration": "2017-05-12T23:11:13",
                "prefix": default_prefix,
            })

        self.cm = ('f68585abf4dce7c80457011505616c696365bf85070001000000000000'
                   '0003404030303030303030313300010000000000000003404030303030'
                   '30303031330a0000000000000003404030303030303030323111411659'
                   '0001205533a7f4eb0be6e5d1db4a67d7bfa693b7b81aa0aba01726b609'
                   '01364785388440a8c5baf2a94c99465447af7a615ec9898d269560fa3a'
                   'e56ed8f73e12411acf')
        self.doit()

    def test_account_update(self):
        self.op = operations.Account_update(
            **{
                "account":
                "streemian",
                "posting": {
                    "weight_threshold":
                    1,
                    "account_auths": [["xeroc", 1], ["fabian", 1]],
                    "key_auths": [[
                        "STM6KChDK2sns9MwugxkoRvPEnyju"
                        "TxHN5upGsZ1EtanCffqBVVX3", 1
                    ], [
                        "STM7sw22HqsXbz7D2CmJfmMwt9ri"
                        "mtk518dRzsR1f8Cgw52dQR1pR", 1
                    ]]
                },
                "owner": {
                    "weight_threshold":
                    1,
                    "account_auths": [],
                    "key_auths": [[
                        "STM7sw22HqsXbz7D2CmJfmMwt9r"
                        "imtk518dRzsR1f8Cgw52dQR1pR", 1
                    ], [
                        "STM6KChDK2sns9MwugxkoRvPEn"
                        "yjuTxHN5upGsZ1EtanCffqBVVX3", 1
                    ]]
                },
                "active": {
                    "weight_threshold":
                    2,
                    "account_auths": [],
                    "key_auths": [[
                        "STM6KChDK2sns9MwugxkoRvPEnyju"
                        "TxHN5upGsZ1EtanCffqBVVX3", 1
                    ], [
                        "STM7sw22HqsXbz7D2CmJfmMwt9ri"
                        "mtk518dRzsR1f8Cgw52dQR1pR", 1
                    ]]
                },
                "memo_key":
                "STM728uLvStTeAkYJsQefks3FX8yfmpFHp8wXw3RY3kwey2JGDooR",
                "json_metadata":
                "",
                "prefix": default_prefix
            })

        self.cm = (u"f68585abf4dce7c80457010a0973747265656d69616e01010000"
                   "00000202bbcf38855c9ae9d55704ee50ff56552af1242266c105"
                   "44a75b61005e17fa78a601000389d28937022880a7f0c7deaa6f"
                   "46b4d87ce08bd5149335cb39b5a8e9b04981c201000102000000"
                   "000202bbcf38855c9ae9d55704ee50ff56552af1242266c10544"
                   "a75b61005e17fa78a601000389d28937022880a7f0c7deaa6f46"
                   "b4d87ce08bd5149335cb39b5a8e9b04981c20100010100000002"
                   "0666616269616e0100057865726f6301000202bbcf38855c9ae9"
                   "d55704ee50ff56552af1242266c10544a75b61005e17fa78a601"
                   "000389d28937022880a7f0c7deaa6f46b4d87ce08bd5149335cb"
                   "39b5a8e9b04981c201000318c1ae46b3e98b26684c87737a04ec"
                   "b1a390efdc7671ced448a92b745372deff000001206a8896c0ce"
                   "0c949d901c44232694252348004cf9a74ec2f391c0e0b7a4108e"
                   "7f71522c186a92c17e23a07cdb108a745b9760316daf16f20434"
                   "53fbeccb331067")
        self.doit()

    def test_order_cancel(self):
        self.op = operations.Limit_order_cancel(**{
            "owner": "",
            "orderid": 2141244,
            "prefix": default_prefix
        })

        self.cm = (u"f68585abf4dce7c804570106003cac20000001206c9888d0c2c3"
                   "1dba1302566f524dfac01a15760b93a8726241a7ae6ba00edfd"
                   "e5b83edaf94a4bd35c2957ded6023576dcbe936338fb9d340e2"
                   "1b5dad6f0028f6")
        self.doit()

    def test_set_route(self):
        self.op = operations.Set_withdraw_vesting_route(
            **{
                "from_account": "xeroc",
                "to_account": "xeroc",
                "percent": 1000,
                "auto_vest": False,
                "prefix": default_prefix
            })

        self.cm = (u"f68585abf4dce7c804570114057865726f63057865726f63e803"
                   "0000011f12d2b8f93f9528f31979e0e1f59a6d45346a88c02ab2"
                   "c4115b10c9e273fc1e99621af0c2188598c84762b7e99ca63f6b"
                   "6be6fca318dd85b0d7a4f09f95579290")
        self.doit()

    def test_convert(self):
        self.op = operations.Convert(**{
            "owner": "xeroc",
            "requestid": 2342343235,
            "amount": "100.000 SBD",
            "prefix": default_prefix
        })

        self.cm = (u"f68585abf4dce7c804570108057865726f6343529d8ba0860100000"
                   "00000035342440000000000011f3d22eb66e5cddcc90f5d6ca0bd7a"
                   "43e0ab811ecd480022af8a847c45eac720b342188d55643d8cb1711"
                   "f516e9879be2fa7dfa329b518f19df4afaaf4f41f7715")
        self.doit()

    def test_utf8tests(self):
        self.op = operations.Comment(
            **{
                "parent_author": "",
                "parent_permlink": "",
                "author": "a",
                "permlink": "a",
                "title": "-",
                "body": "".join([chr(i) for i in range(0, 2048)]),
                "json_metadata": {},
                "prefix": default_prefix
            })

        self.cm = (u"f68585abf4dce7c804570101000001610161012dec1f75303030307"
                   "5303030317530303032753030303375303030347530303035753030"
                   "3036753030303762090a7530303062660d753030306575303030667"
                   "5303031307530303131753030313275303031337530303134753030"
                   "3135753030313675303031377530303138753030313975303031617"
                   "5303031627530303163753030316475303031657530303166202122"
                   "232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3"
                   "e3f404142434445464748494a4b4c4d4e4f50515253545556575859"
                   "5a5b5c5d5e5f606162636465666768696a6b6c6d6e6f70717273747"
                   "5767778797a7b7c7d7e7fc280c281c282c283c284c285c286c287c2"
                   "88c289c28ac28bc28cc28dc28ec28fc290c291c292c293c294c295c"
                   "296c297c298c299c29ac29bc29cc29dc29ec29fc2a0c2a1c2a2c2a3"
                   "c2a4c2a5c2a6c2a7c2a8c2a9c2aac2abc2acc2adc2aec2afc2b0c2b"
                   "1c2b2c2b3c2b4c2b5c2b6c2b7c2b8c2b9c2bac2bbc2bcc2bdc2bec2"
                   "bfc380c381c382c383c384c385c386c387c388c389c38ac38bc38cc"
                   "38dc38ec38fc390c391c392c393c394c395c396c397c398c399c39a"
                   "c39bc39cc39dc39ec39fc3a0c3a1c3a2c3a3c3a4c3a5c3a6c3a7c3a"
                   "8c3a9c3aac3abc3acc3adc3aec3afc3b0c3b1c3b2c3b3c3b4c3b5c3"
                   "b6c3b7c3b8c3b9c3bac3bbc3bcc3bdc3bec3bfc480c481c482c483c"
                   "484c485c486c487c488c489c48ac48bc48cc48dc48ec48fc490c491"
                   "c492c493c494c495c496c497c498c499c49ac49bc49cc49dc49ec49"
                   "fc4a0c4a1c4a2c4a3c4a4c4a5c4a6c4a7c4a8c4a9c4aac4abc4acc4"
                   "adc4aec4afc4b0c4b1c4b2c4b3c4b4c4b5c4b6c4b7c4b8c4b9c4bac"
                   "4bbc4bcc4bdc4bec4bfc580c581c582c583c584c585c586c587c588"
                   "c589c58ac58bc58cc58dc58ec58fc590c591c592c593c594c595c59"
                   "6c597c598c599c59ac59bc59cc59dc59ec59fc5a0c5a1c5a2c5a3c5"
                   "a4c5a5c5a6c5a7c5a8c5a9c5aac5abc5acc5adc5aec5afc5b0c5b1c"
                   "5b2c5b3c5b4c5b5c5b6c5b7c5b8c5b9c5bac5bbc5bcc5bdc5bec5bf"
                   "c680c681c682c683c684c685c686c687c688c689c68ac68bc68cc68"
                   "dc68ec68fc690c691c692c693c694c695c696c697c698c699c69ac6"
                   "9bc69cc69dc69ec69fc6a0c6a1c6a2c6a3c6a4c6a5c6a6c6a7c6a8c"
                   "6a9c6aac6abc6acc6adc6aec6afc6b0c6b1c6b2c6b3c6b4c6b5c6b6"
                   "c6b7c6b8c6b9c6bac6bbc6bcc6bdc6bec6bfc780c781c782c783c78"
                   "4c785c786c787c788c789c78ac78bc78cc78dc78ec78fc790c791c7"
                   "92c793c794c795c796c797c798c799c79ac79bc79cc79dc79ec79fc"
                   "7a0c7a1c7a2c7a3c7a4c7a5c7a6c7a7c7a8c7a9c7aac7abc7acc7ad"
                   "c7aec7afc7b0c7b1c7b2c7b3c7b4c7b5c7b6c7b7c7b8c7b9c7bac7b"
                   "bc7bcc7bdc7bec7bfc880c881c882c883c884c885c886c887c888c8"
                   "89c88ac88bc88cc88dc88ec88fc890c891c892c893c894c895c896c"
                   "897c898c899c89ac89bc89cc89dc89ec89fc8a0c8a1c8a2c8a3c8a4"
                   "c8a5c8a6c8a7c8a8c8a9c8aac8abc8acc8adc8aec8afc8b0c8b1c8b"
                   "2c8b3c8b4c8b5c8b6c8b7c8b8c8b9c8bac8bbc8bcc8bdc8bec8bfc9"
                   "80c981c982c983c984c985c986c987c988c989c98ac98bc98cc98dc"
                   "98ec98fc990c991c992c993c994c995c996c997c998c999c99ac99b"
                   "c99cc99dc99ec99fc9a0c9a1c9a2c9a3c9a4c9a5c9a6c9a7c9a8c9a"
                   "9c9aac9abc9acc9adc9aec9afc9b0c9b1c9b2c9b3c9b4c9b5c9b6c9"
                   "b7c9b8c9b9c9bac9bbc9bcc9bdc9bec9bfca80ca81ca82ca83ca84c"
                   "a85ca86ca87ca88ca89ca8aca8bca8cca8dca8eca8fca90ca91ca92"
                   "ca93ca94ca95ca96ca97ca98ca99ca9aca9bca9cca9dca9eca9fcaa"
                   "0caa1caa2caa3caa4caa5caa6caa7caa8caa9caaacaabcaaccaadca"
                   "aecaafcab0cab1cab2cab3cab4cab5cab6cab7cab8cab9cabacabbc"
                   "abccabdcabecabfcb80cb81cb82cb83cb84cb85cb86cb87cb88cb89"
                   "cb8acb8bcb8ccb8dcb8ecb8fcb90cb91cb92cb93cb94cb95cb96cb9"
                   "7cb98cb99cb9acb9bcb9ccb9dcb9ecb9fcba0cba1cba2cba3cba4cb"
                   "a5cba6cba7cba8cba9cbaacbabcbaccbadcbaecbafcbb0cbb1cbb2c"
                   "bb3cbb4cbb5cbb6cbb7cbb8cbb9cbbacbbbcbbccbbdcbbecbbfcc80"
                   "cc81cc82cc83cc84cc85cc86cc87cc88cc89cc8acc8bcc8ccc8dcc8"
                   "ecc8fcc90cc91cc92cc93cc94cc95cc96cc97cc98cc99cc9acc9bcc"
                   "9ccc9dcc9ecc9fcca0cca1cca2cca3cca4cca5cca6cca7cca8cca9c"
                   "caaccabccacccadccaeccafccb0ccb1ccb2ccb3ccb4ccb5ccb6ccb7"
                   "ccb8ccb9ccbaccbbccbcccbdccbeccbfcd80cd81cd82cd83cd84cd8"
                   "5cd86cd87cd88cd89cd8acd8bcd8ccd8dcd8ecd8fcd90cd91cd92cd"
                   "93cd94cd95cd96cd97cd98cd99cd9acd9bcd9ccd9dcd9ecd9fcda0c"
                   "da1cda2cda3cda4cda5cda6cda7cda8cda9cdaacdabcdaccdadcdae"
                   "cdafcdb0cdb1cdb2cdb3cdb4cdb5cdb6cdb7cdb8cdb9cdbacdbbcdb"
                   "ccdbdcdbecdbfce80ce81ce82ce83ce84ce85ce86ce87ce88ce89ce"
                   "8ace8bce8cce8dce8ece8fce90ce91ce92ce93ce94ce95ce96ce97c"
                   "e98ce99ce9ace9bce9cce9dce9ece9fcea0cea1cea2cea3cea4cea5"
                   "cea6cea7cea8cea9ceaaceabceacceadceaeceafceb0ceb1ceb2ceb"
                   "3ceb4ceb5ceb6ceb7ceb8ceb9cebacebbcebccebdcebecebfcf80cf"
                   "81cf82cf83cf84cf85cf86cf87cf88cf89cf8acf8bcf8ccf8dcf8ec"
                   "f8fcf90cf91cf92cf93cf94cf95cf96cf97cf98cf99cf9acf9bcf9c"
                   "cf9dcf9ecf9fcfa0cfa1cfa2cfa3cfa4cfa5cfa6cfa7cfa8cfa9cfa"
                   "acfabcfaccfadcfaecfafcfb0cfb1cfb2cfb3cfb4cfb5cfb6cfb7cf"
                   "b8cfb9cfbacfbbcfbccfbdcfbecfbfd080d081d082d083d084d085d"
                   "086d087d088d089d08ad08bd08cd08dd08ed08fd090d091d092d093"
                   "d094d095d096d097d098d099d09ad09bd09cd09dd09ed09fd0a0d0a"
                   "1d0a2d0a3d0a4d0a5d0a6d0a7d0a8d0a9d0aad0abd0acd0add0aed0"
                   "afd0b0d0b1d0b2d0b3d0b4d0b5d0b6d0b7d0b8d0b9d0bad0bbd0bcd"
                   "0bdd0bed0bfd180d181d182d183d184d185d186d187d188d189d18a"
                   "d18bd18cd18dd18ed18fd190d191d192d193d194d195d196d197d19"
                   "8d199d19ad19bd19cd19dd19ed19fd1a0d1a1d1a2d1a3d1a4d1a5d1"
                   "a6d1a7d1a8d1a9d1aad1abd1acd1add1aed1afd1b0d1b1d1b2d1b3d"
                   "1b4d1b5d1b6d1b7d1b8d1b9d1bad1bbd1bcd1bdd1bed1bfd280d281"
                   "d282d283d284d285d286d287d288d289d28ad28bd28cd28dd28ed28"
                   "fd290d291d292d293d294d295d296d297d298d299d29ad29bd29cd2"
                   "9dd29ed29fd2a0d2a1d2a2d2a3d2a4d2a5d2a6d2a7d2a8d2a9d2aad"
                   "2abd2acd2add2aed2afd2b0d2b1d2b2d2b3d2b4d2b5d2b6d2b7d2b8"
                   "d2b9d2bad2bbd2bcd2bdd2bed2bfd380d381d382d383d384d385d38"
                   "6d387d388d389d38ad38bd38cd38dd38ed38fd390d391d392d393d3"
                   "94d395d396d397d398d399d39ad39bd39cd39dd39ed39fd3a0d3a1d"
                   "3a2d3a3d3a4d3a5d3a6d3a7d3a8d3a9d3aad3abd3acd3add3aed3af"
                   "d3b0d3b1d3b2d3b3d3b4d3b5d3b6d3b7d3b8d3b9d3bad3bbd3bcd3b"
                   "dd3bed3bfd480d481d482d483d484d485d486d487d488d489d48ad4"
                   "8bd48cd48dd48ed48fd490d491d492d493d494d495d496d497d498d"
                   "499d49ad49bd49cd49dd49ed49fd4a0d4a1d4a2d4a3d4a4d4a5d4a6"
                   "d4a7d4a8d4a9d4aad4abd4acd4add4aed4afd4b0d4b1d4b2d4b3d4b"
                   "4d4b5d4b6d4b7d4b8d4b9d4bad4bbd4bcd4bdd4bed4bfd580d581d5"
                   "82d583d584d585d586d587d588d589d58ad58bd58cd58dd58ed58fd"
                   "590d591d592d593d594d595d596d597d598d599d59ad59bd59cd59d"
                   "d59ed59fd5a0d5a1d5a2d5a3d5a4d5a5d5a6d5a7d5a8d5a9d5aad5a"
                   "bd5acd5add5aed5afd5b0d5b1d5b2d5b3d5b4d5b5d5b6d5b7d5b8d5"
                   "b9d5bad5bbd5bcd5bdd5bed5bfd680d681d682d683d684d685d686d"
                   "687d688d689d68ad68bd68cd68dd68ed68fd690d691d692d693d694"
                   "d695d696d697d698d699d69ad69bd69cd69dd69ed69fd6a0d6a1d6a"
                   "2d6a3d6a4d6a5d6a6d6a7d6a8d6a9d6aad6abd6acd6add6aed6afd6"
                   "b0d6b1d6b2d6b3d6b4d6b5d6b6d6b7d6b8d6b9d6bad6bbd6bcd6bdd"
                   "6bed6bfd780d781d782d783d784d785d786d787d788d789d78ad78b"
                   "d78cd78dd78ed78fd790d791d792d793d794d795d796d797d798d79"
                   "9d79ad79bd79cd79dd79ed79fd7a0d7a1d7a2d7a3d7a4d7a5d7a6d7"
                   "a7d7a8d7a9d7aad7abd7acd7add7aed7afd7b0d7b1d7b2d7b3d7b4d"
                   "7b5d7b6d7b7d7b8d7b9d7bad7bbd7bcd7bdd7bed7bfd880d881d882"
                   "d883d884d885d886d887d888d889d88ad88bd88cd88dd88ed88fd89"
                   "0d891d892d893d894d895d896d897d898d899d89ad89bd89cd89dd8"
                   "9ed89fd8a0d8a1d8a2d8a3d8a4d8a5d8a6d8a7d8a8d8a9d8aad8abd"
                   "8acd8add8aed8afd8b0d8b1d8b2d8b3d8b4d8b5d8b6d8b7d8b8d8b9"
                   "d8bad8bbd8bcd8bdd8bed8bfd980d981d982d983d984d985d986d98"
                   "7d988d989d98ad98bd98cd98dd98ed98fd990d991d992d993d994d9"
                   "95d996d997d998d999d99ad99bd99cd99dd99ed99fd9a0d9a1d9a2d"
                   "9a3d9a4d9a5d9a6d9a7d9a8d9a9d9aad9abd9acd9add9aed9afd9b0"
                   "d9b1d9b2d9b3d9b4d9b5d9b6d9b7d9b8d9b9d9bad9bbd9bcd9bdd9b"
                   "ed9bfda80da81da82da83da84da85da86da87da88da89da8ada8bda"
                   "8cda8dda8eda8fda90da91da92da93da94da95da96da97da98da99d"
                   "a9ada9bda9cda9dda9eda9fdaa0daa1daa2daa3daa4daa5daa6daa7"
                   "daa8daa9daaadaabdaacdaaddaaedaafdab0dab1dab2dab3dab4dab"
                   "5dab6dab7dab8dab9dabadabbdabcdabddabedabfdb80db81db82db"
                   "83db84db85db86db87db88db89db8adb8bdb8cdb8ddb8edb8fdb90d"
                   "b91db92db93db94db95db96db97db98db99db9adb9bdb9cdb9ddb9e"
                   "db9fdba0dba1dba2dba3dba4dba5dba6dba7dba8dba9dbaadbabdba"
                   "cdbaddbaedbafdbb0dbb1dbb2dbb3dbb4dbb5dbb6dbb7dbb8dbb9db"
                   "badbbbdbbcdbbddbbedbbfdc80dc81dc82dc83dc84dc85dc86dc87d"
                   "c88dc89dc8adc8bdc8cdc8ddc8edc8fdc90dc91dc92dc93dc94dc95"
                   "dc96dc97dc98dc99dc9adc9bdc9cdc9ddc9edc9fdca0dca1dca2dca"
                   "3dca4dca5dca6dca7dca8dca9dcaadcabdcacdcaddcaedcafdcb0dc"
                   "b1dcb2dcb3dcb4dcb5dcb6dcb7dcb8dcb9dcbadcbbdcbcdcbddcbed"
                   "cbfdd80dd81dd82dd83dd84dd85dd86dd87dd88dd89dd8add8bdd8c"
                   "dd8ddd8edd8fdd90dd91dd92dd93dd94dd95dd96dd97dd98dd99dd9"
                   "add9bdd9cdd9ddd9edd9fdda0dda1dda2dda3dda4dda5dda6dda7dd"
                   "a8dda9ddaaddabddacddadddaeddafddb0ddb1ddb2ddb3ddb4ddb5d"
                   "db6ddb7ddb8ddb9ddbaddbbddbcddbdddbeddbfde80de81de82de83"
                   "de84de85de86de87de88de89de8ade8bde8cde8dde8ede8fde90de9"
                   "1de92de93de94de95de96de97de98de99de9ade9bde9cde9dde9ede"
                   "9fdea0dea1dea2dea3dea4dea5dea6dea7dea8dea9deaadeabdeacd"
                   "eaddeaedeafdeb0deb1deb2deb3deb4deb5deb6deb7deb8deb9deba"
                   "debbdebcdebddebedebfdf80df81df82df83df84df85df86df87df8"
                   "8df89df8adf8bdf8cdf8ddf8edf8fdf90df91df92df93df94df95df"
                   "96df97df98df99df9adf9bdf9cdf9ddf9edf9fdfa0dfa1dfa2dfa3d"
                   "fa4dfa5dfa6dfa7dfa8dfa9dfaadfabdfacdfaddfaedfafdfb0dfb1"
                   "dfb2dfb3dfb4dfb5dfb6dfb7dfb8dfb9dfbadfbbdfbcdfbddfbedfb"
                   "f0000011f45c8e1ed9289f5ec7d4f6d7ce891a30ede7470e28d4639"
                   "8e0dc15c41c784b1862f132378382230d68b59e3592e72a32f310f8"
                   "8ea4baddb361a3709b664ba7375")
        self.doit()

    def test_feed_publish(self):
        self.op = operations.Feed_publish(
            **{
                "publisher": "xeroc",
                "exchange_rate": {
                    "base": "1.000 SBD",
                    "quote": "4.123 STEEM"
                },
                "prefix": default_prefix
            })

        self.cm = (u"f68585abf4dce7c804570107057865726f63e803000000000"
                   "00003534244000000001b1000000000000003535445454d00"
                   "000001203847a02aa76964cacfb41565c23286cc64b18f6bb"
                   "9260832823839b3b90dff18738e1b686ad22f79c42fca73e6"
                   "1bf633505a2a66cac65555b0ac535ca5ee5a61")
        self.doit()

    def test_delete_comment(self):
        self.op = operations.Delete_comment(
            **{
                "author": "turbot",
                "permlink": "testpost",
                "prefix": default_prefix
            })

        self.cm = (u"f68585abf4dce7c80457011106747572626f740874657374706f73"
                   "7400011f0d413176d24455d6d9b5b9416384fcf63f080a70d8b243"
                   "c579f996ce8c116ce0583b433d4ce9107438b72d39eb6195027880"
                   "54b97abc20bf86b17a11d3eb8351")
        self.doit()

    def test_witness_update(self):
        self.op = operations.Witness_update(
            **{
                "owner":
                "xeroc",
                "url":
                "foooobar",
                "block_signing_key":
                "STM6zLNtyFVToBsBZDsgMhgjpwysYVbsQD6YhP3kRkQhANUB4w7Qp",
                "props": {
                    "account_creation_fee": "10.000 STEEM",
                    "maximum_block_size": 1111111,
                    "sbd_interest_rate": 1000
                },
                "fee":
                "10.000 STEEM",
                "prefix": default_prefix
            })

        self.cm = (u"f68585abf4dce7c80457010b057865726f6308666f6f6f6f6261"
                   "720314aa202c9158990b3ec51a1aa49b2ab5d300c97b391df3be"
                   "b34bb74f3c62699e102700000000000003535445454d000047f4"
                   "1000e803102700000000000003535445454d00000001206adca4"
                   "bebc872e8d792caeb3b729e9a5e8af90c07ab3f744fb4d0f19d5"
                   "7b3bec32f5a43f5acdfc065f0227e45e599745c46e41c023d69f"
                   "b9f2405478badadb4c")
        self.doit()

    def test_witness_vote(self):
        self.op = operations.Account_witness_vote(**{
            "account": "xeroc",
            "witness": "chainsquad",
            "approve": True,
            "prefix": default_prefix,
        })

        self.cm = (u"f68585abf4dce7c80457010c057865726f630a636"
                   "861696e73717561640100011f16b43411e11f4739"
                   "4c1624a3c4d3cf4daba700b8690f494e6add7ad9b"
                   "ac735ce7775d823aa66c160878cb3348e6857c531"
                   "114d229be0202dc0857f8f03a00369")
        self.doit()

    def test_witness_proxy(self):
        self.op = operations.Account_witness_proxy(**{
            "account": "alice",
            "proxy": "bob",
            "prefix": default_prefix,
        })

        self.cm = ('f68585abf4dce7c80457010d05616c69636503626f6'
                   '20001202b1c0a06e514fd39d52138b08fe7e6736592'
                   '5891b0ed0839686ed900adf33aa9281e95ee1e50184'
                   'a3b41b7acab0456c83243ebdccfd17e10e7ab94e09fb'
                   '96309')
        self.doit()

    def test_custom(self):
        self.op = operations.Custom(
            **{
                "required_auths": ["bytemaster"],
                "id": 777,
                "data": '0a627974656d617374657207737465656d697402a3d1389'
                        '7d82114466ad87a74b73a53292d8331d1bd1d3082da6bfbc'
                        'ff19ed097029db013797711c88cccca3692407f9ff9b9ce72'
                        '21aaa2d797f1692be2215d0a5f6d2a8cab6832050078bc5729'
                        '201e3ea24ea9f7873e6dbdc65a6bd9899053b9acda876dc69f1'
                        '1a13df9ca8b26b6',
                "prefix": default_prefix,
            })

        self.cm = ('f68585abf4dce7c80457010f010a627974656d6173746572090384023'
                   '061363237393734363536643631373337343635373230373733373436'
                   '353635366436393734303261336431333839376438323131343436366'
                   '164383761373462373361353332393264383333316431626431643330'
                   '383264613662666263666631396564303937303239646230313337393'
                   '737313163383863636363613336393234303766396666396239636537'
                   '323231616161326437393766313639326265323231356430613566366'
                   '432613863616236383332303530303738626335373239323031653365'
                   '613234656139663738373365366462646336356136626439383939303'
                   '533623961636461383736646336396631316131336466396361386232'
                   '3662360001203f60bbd0d7595c1e5cf7a6314a14117a94898121b28f1'
                   '5992820e0fae14188ac0d352b7d96aba83ea808329afedddc1e3d7c43'
                   '85d23fb9331a68795ba9e7ed08')
        self.doit()

    def test_custom_json(self):
        self.op = operations.Custom_json(
            **{
                "json": [
                    "reblog",
                    OrderedDict(
                        [  # need an ordered dict to keep order for the test
                            ("account", "xeroc"), ("author", "chainsquad"), (
                                "permlink", "streemian-com-to-open-its-doors-"
                                "and-offer-a-20-discount")
                        ])
                ],
                "required_auths": [],
                "required_posting_auths": ["xeroc"],
                "id":
                "follow",
                "prefix": default_prefix
            })

        self.cm = (u"f68585abf4dce7c8045701120001057865726f6306666f6c6c"
                   "6f777f5b227265626c6f67222c207b226163636f756e74223a"
                   "20227865726f63222c2022617574686f72223a202263686169"
                   "6e7371756164222c20227065726d6c696e6b223a2022737472"
                   "65656d69616e2d636f6d2d746f2d6f70656e2d6974732d646f"
                   "6f72732d616e642d6f666665722d612d32302d646973636f75"
                   "6e74227d5d00011f0cffad16cfd8ea4b84c06d412e93a9fc10"
                   "0bf2fac5f9a40d37d5773deef048217db79cabbf15ef29452d"
                   "e4ed1c5face51d998348188d66eb9fc1ccef79a0c0d4")
        self.doit()

    def test_comment_options(self):
        self.op = operations.Comment_options(
            **{
                "author":
                "xeroc",
                "permlink":
                "piston",
                "max_accepted_payout":
                "1000000.000 SBD",
                "percent_steem_dollars":
                10000,
                "allow_votes":
                True,
                "allow_curation_rewards":
                True,
                "beneficiaries": [{
                    "weight": 2000,
                    "account": "good-karma"
                }, {
                    "weight": 5000,
                    "account": "null"
                }],
                "prefix": default_prefix
            })

        self.cm = (u"f68585abf4dce7c804570113057865726f6306706973746f6e"
                   "00ca9a3b000000000353424400000000102701010100020a67"
                   "6f6f642d6b61726d61d007046e756c6c881300011f59634e65"
                   "55fec7c01cb7d4921601c37c250c6746022cc35eaefdd90405"
                   "d7771b2f65b44e97b7f3159a6d52cb20640502d2503437215f"
                   "0907b2e2213940f34f2c")
        self.doit()

    def test_change_recovery_account(self):
        self.op = operations.Change_recovery_account(
            **{
                "account_to_recover": "barrie",
                "extensions": [],
                "new_recovery_account": "boombastic",
                "prefix": default_prefix,
            })

        self.cm = ('f68585abf4dce7c80457011a066261727269650a626f6f6d6261'
                   '737469630000011f5513c021e89be2c4d8a725dc9b89334ffcde'
                   '6a9535487f4b6d42f93de1722c251fd9d4ec414335dc41ea081a'
                   'a7a4d27b179b1a07d3415f7e0a6190852b86ecde')
        self.doit()

    def test_request_account_recovery(self):
        self.op = operations.Request_account_recovery(
            **{
                "recovery_account": "steem",
                "account_to_recover": "alice",
                "new_owner_authority": {
                    "weight_threshold": 1,
                    "account_auths": [],
                    "key_auths": [
                        [
                            "STM6LYxj96zdypHYqgDdD6Nyh2NxerN3P1Mp3ddNm7gci63nfrSuZ",
                            1
                        ]
                    ]
                },
                "extensions": [],
                "prefix": default_prefix,
            })

        self.cm = ('f68585abf4dce7c80457011805737465656d05616c69636501000000000102'
                   'bedf9f3cf1655dc635d2b7fd43e1d0ab6eafbc443f6fd013de0cb2e8a11fbc'
                   '8901000000011f7a23a45fe0d5824201cf4fad0bcc5c3564156c0d4217df10'
                   'acd544786e3f407d38b149afc41387090ef95b719bc5264954011ddf21e861'
                   'be37f29998286e55e5')
        self.doit()

    def test_recover_account(self):
        self.op = operations.Recover_account(
            **{
                "account_to_recover": "alice",
                "new_owner_authority": {
                    "weight_threshold": 1,
                    "account_auths": [],
                    "key_auths": [
                        [
                            "STM7j3nhkhHTpXqLEvdx2yEGhQeeorTcxSV6WDL2DZGxwUxYGrHvh",
                            1
                        ]
                    ]
                },
                "recent_owner_authority": {
                    "weight_threshold": 1,
                    "account_auths": [],
                    "key_auths": [
                        [
                            "STM78Xth94gNxp8nmByFV2vNAhg9bsSdviJ6fQXUTFikySLK3uTxC",
                            1
                        ]
                    ]
                },
                "extensions": [],
                "prefix": default_prefix,
            })
        self.cm = ('f68585abf4dce7c80457011905616c6963650100000000010375a6dfff76'
                   '49647cc074d86386862087a154088d952da64af9dac429559a8d0c010001'
                   '0000000001032747c05d4aa44704a196493e1fa0c26137abfca64991a9b9'
                   'faeb9204ee9897ef01000000011f31e1794992a1573c3d2909cd10405d0f'
                   'ea3c5dd77aac04391af76bd51becee7360775fa79f23e898ceebaae74e8c'
                   'a079ba7a6bef2c359bb349033dff9a0ccc26')

        self.doit()

    def test_escrow_transfer(self):
        self.op = operations.Escrow_transfer(
            **{
                "from": "alice",
                "to": "bob",
                "sbd_amount": ["1000", 3, "@@000000013"],
                "steem_amount": ["0", 3, "@@000000021"],
                "escrow_id": 23456789,
                "agent": "charlie",
                "fee": ["100", 3, "@@000000013"],
                "json_meta": "{}",
                "ratification_deadline": "2017-02-26T11:22:39",
                "escrow_expiration": "2017-02-28T11:22:39",
                "prefix": default_prefix,
            })

        self.cm = ('f68585abf4dce7c80457011b05616c69636503626f6207636861726c69'
                   '6515ec6501e80300000000000003404030303030303030313300000000'
                   '0000000003404030303030303030323164000000000000000340403030'
                   '303030303031337fbab2587f5db558027b7d0001203010ea007a004440'
                   '5789923653541fafb0e72c9f5f14cff24307d9fc68d3e3914bd0eca8d7'
                   'ab62a9c639a49594dd35dc06d361ac1e4aea5f9536fc3c9315a5db')
        self.doit()

    def test_escrow_dispute(self):
        self.op = operations.Escrow_dispute(
            **{
                "from": "alice",
                "to": "bob",
                "who": "alice",
                "escrow_id": 72526562,
                "prefix": default_prefix,
            })

        self.cm = ('f68585abf4dce7c80457011c05616c69636503626f6205616c696365e2'
                   'aa520400012009742d35b45cbd9b9612429dda6873ac1d8bab66066e66'
                   '01858cde0adf55cfb445d6a8be7a400a594e0d4e603af932a6b610087a'
                   '30129b8682631ca9d6571714')
        self.doit()

    def test_escrow_release(self):
        self.op = operations.Escrow_release(
            **{
                "from": "alice",
                "to": "bob",
                "who": "charlie",
                "escrow_id": 72526562,
                "sbd_amount": ["5000", 3, "@@000000013"],
                "steem_amount": ["0", 3, "@@000000021"],
                "prefix": default_prefix,
            })

        self.cm = ('f68585abf4dce7c80457011d05616c69636503626f6207636861726c69'
                   '65e2aa5204881300000000000003404030303030303030313300000000'
                   '000000000340403030303030303032310001201bcc5cb0f6bc1083dd24'
                   'ddcd7415d69a57d54b065c9e6c96ebc04a68ed709758438b226ee19cca'
                   '39b6df49406f029f61d59a29f9cd14bc081a551fd19df199f1')
        self.doit()

    def test_escrow_approve(self):
        self.op = operations.Escrow_approve(
            **{
                "from": "alice",
                "to": "bob",
                "agent": "charlie",
                "who": "charlie",
                "escrow_id": 59102208,
                "approve": True,
                "prefix": default_prefix,
            })

        self.cm = ('f68585abf4dce7c80457011f05616c69636503626f6207636861726c69'
                   '6507636861726c696500d485030100012054baed32863a307ed68c3af8'
                   '6f42608ef35c24c3a82c12d9baaa854345f4812a048fdc819ec7e01b0f'
                   '28f6eb8357de1cb8127df29b255fa78fa1bdd267e7d5fc')
        self.doit()

    def test_decline_voting_rights(self):
        self.op = operations.Decline_voting_rights(
            **{
                "account": "judy",
                "decline": True,
                "prefix": default_prefix,
            })

        self.cm = ('f68585abf4dce7c804570124046a7564790100011f5bedbccb7042c5ab'
                   '8d6debf579bca485a4cc8f95c64515d1885339c416a64d9f26fac5f01c'
                   'c3f248297cb3af921103777638bb727f5ef9bd3c3f66953167ee42')
        self.doit()

    def test_claim_reward_balance(self):
        self.op = operations.Claim_reward_balance(
            **{
                "account": "alice",
                "reward_steem": ["17", 3, "@@000000021"],
                "reward_sbd": ["11", 3, "@@000000013"],
                "reward_vests": ["185025103", 6, "@@000000037"],
                "prefix": default_prefix,
            })

        self.cm = ('f68585abf4dce7c80457012705616c6963651100000000000000034040'
                   '3030303030303032310b00000000000000034040303030303030303133'
                   '4f42070b000000000640403030303030303033370001205caa9ba8b92b'
                   '814f3d1ecfb581d8d98f898b4c174200ee9bc5c9fb9c98b0e6672fbb67'
                   'cccc2fe64df386285270b9a1f67b2d1a69883a11ce9197b52f0c227649')
        self.doit()

    def test_delegate_vesting_shares(self):
        self.op = operations.Delegate_vesting_shares(
            **{
                "delegator": "alice",
                "delegatee": "bob",
                "vesting_shares": ["94599167138276", 6, "@@000000037"],
                "prefix": default_prefix,
            })

        self.cm = ('f68585abf4dce7c80457012805616c69636503626f62e4d9c095095600'
                   '0006404030303030303030333700011f4573eaedaff15f6398cdb12a44'
                   '252ef484b163e5e426b6c777005484d3c6c2aa137b9d4a1265d7360192'
                   'be339d281c7725f0087ae39bd9acd0f2aa3a7fd96369')
        self.doit()

    def test_account_create_with_delegation(self):
        self.op = operations.Account_create_with_delegation(
            **{
                "fee": ["3000", 3, "@@000000021"],
                "delegation": ["0", 6, "@@000000037"],
                "creator": "steemit",
                "new_account_name": "alice",
                "owner": {
                    "weight_threshold": 1,
                    "account_auths": [],
                    "key_auths": [
                        [
                            "STM5Tki3ecCdCCHCjhhwvQvXuKryL2s34Ma6CXsRzntSUTYVYxCQ9",
                            1
                        ]
                    ]
                },
                "active": {
                    "weight_threshold": 1,
                    "account_auths": [],
                    "key_auths": [
                        [
                            "STM6LUoAA8gCL9tHRz7v9xcwR4ZWD3KDRHP5t1U7UAZHdfanLxyBE",
                            1
                        ]
                    ]
                },
                "posting": {
                    "weight_threshold": 1,
                    "account_auths": [],
                    "key_auths": [
                        [
                            "STM8anmpHdfVE4AmwsDpcSXpRsydHysEbv6vGJkRQy1d1CC83zeTA",
                            1
                        ]
                    ]
                },
                "memo_key": "STM67RYDyEkP1Ja1jFehJ45BFGA9oHHUnRnYbxKJEtMhVQiHW3S3k",
                "json_metadata": "{}",
                "extensions": [],
                "prefix": default_prefix,
            })

        self.cm = ('f68585abf4dce7c804570129b80b000000000000034040303030303030'
                   '303231000000000000000006404030303030303030333707737465656d'
                   '697405616c696365010000000001024b881ad188574738041f9ad6621f'
                   '5fd784d51ce19e8379285d800aff65ef72db010001000000000102beb5'
                   'e1610bde9c7c7f91d181356653981a60de0c5753f88bc31b29e6853866'
                   'c2010001000000000103e6985b4e8884a4a225030a8521c688a1c7c4ef'
                   '2fcfc0398e1a7024b0544e6c7b010002a1109a3fdce014bb6a720432f7'
                   '4e38731b420cbd2ac6137de140904b142da2d4027b7d0000011f7fa92a'
                   '03a864d9bef607e31c4bdf9611e3500acf3d2be60f464f9ecd6d407117'
                   '76e0971c759b0b7ce84539716f74e17dad1634aff527151a2ee030675f'
                   'a866eb')
        self.doit()


"""
    def test_limit_order_create(self):
        self.op = operations.Limit_order_create(**{
            "fee": {"amount": 100,
                    "asset_id": "1.3.0"
                    },
            "seller": "1.2.29",
            "amount_to_sell": {"amount": 100000,
                               "asset_id": "SBD"
                               },
            "min_to_receive": {"amount": 10000,
                               "asset_id": "SBD"
                               },
            "expiration": "2016-05-18T09:22:05",
            "fill_or_kill": False,
            "extensions": []
        })
        self.cm = ("f68585abf4dce7c8045701016400000000000000001da08601000"
                   "0000000001027000000000000693d343c57000000011f75cbfd49"
                   "ae8d9b04af76cc0a7de8b6e30b71167db7fe8e2197ef9d858df18"
                   "77043493bc24ffdaaffe592357831c978fd8a296b913979f106de"
                   "be940d60d77b50")
        self.doit()

    def test_transfer(self):
        pub = format(account.PrivateKey(wif).pubkey, prefix)
        from_account_id = "test"
        to_account_id = "test1"
        amount = 1000000
        asset_id = "SBD"
        message = "abcdefgABCDEFG0123456789"
        nonce = "5862723643998573708"

        fee = objects.Asset(amount=0, asset_id="SBD")
        amount = objects.Asset(amount=int(amount), asset_id=asset_id)
        encrypted_memo = memo.encode_memo(
            account.PrivateKey(wif),
            account.PublicKey(pub, prefix=prefix),
            nonce,
            message
        )
        memoStruct = {
            "from": pub,
            "to": pub,
            "nonce": nonce,
            "message": encrypted_memo,
        }
        memoObj = objects.Memo(**memoStruct)
        self.op = operations.Transfer(**{
            "fee": fee,
            "from": from_account_id,
            "to": to_account_id,
            "amount": amount,
            "memo": memoObj,
            "prefix": prefix
        })
        self.cm = ("f68585abf4dce7c804570100000000000000000000000140420"
                   "f0000000000040102c0ded2bc1f1305fb0faac5e6c03ee3a192"
                   "4234985427b6167ca569d13df435cf02c0ded2bc1f1305fb0fa"
                   "ac5e6c03ee3a1924234985427b6167ca569d13df435cf8c94d1"
                   "9817945c5120fa5b6e83079a878e499e2e52a76a7739e9de409"
                   "86a8e3bd8a68ce316cee50b210000011f39e3fa7071b795491e"
                   "3b6851d61e7c959be92cc7deb5d8491cf1c3c8c99a1eb44553c"
                   "348fb8f5001a78b18233ac66727e32fc776d48e92d9639d64f6"
                   "8e641948")
        self.doit()


    def self.cmConstructedTX(self):
        self.maxDiff = None
        self.op = operations.Bid_collateral(**{
            'fee': {'amount': 100,
                    'asset_id': '1.3.0'},
            'additional_collateral': {
                'amount': 10000,
                'asset_id': '1.3.22'},
            'debt_covered': {
                'amount': 100000000,
                'asset_id': '1.3.0'},
            'bidder': '1.2.29',
            'extensions': []
        })
        ops = [Operation(self.op)]
        tx = Signed_Transaction(
            ref_block_num=ref_block_num,
            ref_block_prefix=ref_block_prefix,
            expiration=expiration,
            operations=ops
        )
        tx = tx.sign([wif], chain=prefix)
        tx.verify([PrivateKey(wif).pubkey], prefix)
        txWire = hexlify(bytes(tx)).decode("ascii")
        print("=" * 80)
        pprint(tx.json())
        print("=" * 80)

        from grapheneapi.grapheneapi import GrapheneAPI
        rpc = GrapheneAPI("localhost", 8092)
        self.cm = rpc.serialize_transaction(tx.json())
        print("soll: %s" % self.cm[:-130])
        print("ist:  %s" % txWire[:-130])
        print(txWire[:-130] == self.cm[:-130])
        self.assertEqual(self.cm[:-130], txWire[:-130])


if __name__ == '__main__':
    t = Testcases()
    t.self.cmConstructedTX()
"""
