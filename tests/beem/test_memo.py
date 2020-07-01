from builtins import super
import unittest
import mock
from beem import Hive
from beem.message import Message
from beem.account import Account
from beem.memo import Memo
import random
import shutil, tempfile
import os
from beem.instance import set_shared_steem_instance
from beem.nodelist import NodeList

wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
core_unit = "STM"


class Testcases(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        nodelist = NodeList()
        nodelist.update_nodes(steem_instance=Hive(node=nodelist.get_hive_nodes(), num_retries=10))
        cls.bts = Hive(
            node=nodelist.get_nodes(exclude_limited=True),
            nobroadcast=True,
            keys=[wif],
            num_retries=10
        )
        set_shared_steem_instance(cls.bts)

    def test_decryt_encrypt(self):
        memo = Memo(from_account=wif, to_account="beembot")
        base_string_length = [1, 2, 3, 4, 5, 7, 8, 9, 15, 16, 17, 32, 63, 64, 65, 127, 255, 511, 1023, 2047, 4095]
        for n in base_string_length:
            test_string = str(random.getrandbits(n))
            ret = memo.encrypt(test_string)
            ret_string = memo.decrypt(ret["message"])
            self.assertEqual(test_string, ret_string[1:])

    def test_decrypt_encrypt_file(self):
       
        test_dir = tempfile.mkdtemp()
        outfile = os.path.join(test_dir, 'test.txt')
        outfile_enc = os.path.join(test_dir, 'test_enc.txt')
        test_string = str(random.getrandbits(1000))
        with open(outfile, 'w') as f:
            f.write(test_string)
        memo = Memo(from_account=wif, to_account="beembot")
        memo.encrypt_binary(outfile, outfile_enc)
        memo.decrypt_binary(outfile_enc, outfile)
        with open(outfile, 'r') as f:
            content = f.read()
        self.assertEqual(test_string, content)
        shutil.rmtree(test_dir)
