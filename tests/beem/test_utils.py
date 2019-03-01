from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import unittest
from datetime import datetime, date, timedelta
from beem.utils import (
    formatTimedelta,
    assets_from_string,
    resolve_authorperm,
    resolve_authorpermvoter,
    construct_authorperm,
    construct_authorpermvoter,
    sanitize_permlink,
    derive_permlink,
    resolve_root_identifier,
    make_patch,
    remove_from_dict,
    formatToTimeStamp,
    formatTimeString,
    addTzInfo,
    derive_beneficiaries,
    derive_tags,
    seperate_yaml_dict_from_body
)


class Testcases(unittest.TestCase):
    def test_constructAuthorperm(self):
        self.assertEqual(construct_authorperm("A", "B"), "@A/B")
        self.assertEqual(construct_authorperm({'author': "A", 'permlink': "B"}), "@A/B")

    def test_resolve_root_identifier(self):
        self.assertEqual(resolve_root_identifier("/a/@b/c"), ("@b/c", "a"))

    def test_constructAuthorpermvoter(self):
        self.assertEqual(construct_authorpermvoter("A", "B", "C"), "@A/B|C")
        self.assertEqual(construct_authorpermvoter({'author': "A", 'permlink': "B", 'voter': 'C'}), "@A/B|C")
        self.assertEqual(construct_authorpermvoter({'authorperm': "A/B", 'voter': 'C'}), "@A/B|C")

    def test_assets_from_string(self):
        self.assertEqual(assets_from_string('USD:BTS'), ['USD', 'BTS'])
        self.assertEqual(assets_from_string('BTSBOTS.S1:BTS'), ['BTSBOTS.S1', 'BTS'])

    def test_authorperm_resolve(self):
        self.assertEqual(resolve_authorperm('https://d.tube/#!/v/pottlund/m5cqkd1a'),
                         ('pottlund', 'm5cqkd1a'))
        self.assertEqual(resolve_authorperm("https://steemit.com/witness-category/@gtg/24lfrm-gtg-witness-log"),
                         ('gtg', '24lfrm-gtg-witness-log'))
        self.assertEqual(resolve_authorperm("@gtg/24lfrm-gtg-witness-log"),
                         ('gtg', '24lfrm-gtg-witness-log'))
        self.assertEqual(resolve_authorperm("https://busy.org/@gtg/24lfrm-gtg-witness-log"),
                         ('gtg', '24lfrm-gtg-witness-log'))
        self.assertEqual(resolve_authorperm('https://dlive.io/livestream/atnazo/61dd94c1-8ff3-11e8-976f-0242ac110003'),
                         ('atnazo', '61dd94c1-8ff3-11e8-976f-0242ac110003'))

    def test_authorpermvoter_resolve(self):
        self.assertEqual(resolve_authorpermvoter('theaussiegame/cryptokittie-giveaway-number-2|test'),
                         ('theaussiegame', 'cryptokittie-giveaway-number-2', 'test'))
        self.assertEqual(resolve_authorpermvoter('holger80/virtuelle-cloud-mining-ponzi-schemen-auch-bekannt-als-hypt|holger80'),
                         ('holger80', 'virtuelle-cloud-mining-ponzi-schemen-auch-bekannt-als-hypt', 'holger80'))

    def test_sanitizePermlink(self):
        self.assertEqual(sanitize_permlink("aAf_0.12"), "aaf-0-12")
        self.assertEqual(sanitize_permlink("[](){}|"), "")

    def test_derivePermlink(self):
        self.assertEqual(derive_permlink("Hello World"), "hello-world")
        self.assertEqual(derive_permlink("aAf_0.12"), "aaf-0-12")
        self.assertEqual(derive_permlink("[](){}"), "")
        self.assertEqual(len(derive_permlink("", parent_permlink=256 * "a")), 256)
        self.assertEqual(len(derive_permlink("", parent_permlink=256 * "a", parent_author="test")), 256)

    def test_patch(self):
        self.assertEqual(make_patch("aa", "ab"), '@@ -1 +1 @@\n-aa\n+ab\n')
        self.assertEqual(make_patch("Hello!\n Das ist ein Test!\nEnd.\n", "Hello!\n This is a Test\nEnd.\n"),
                         '@@ -1,3 +1,3 @@\n Hello!\n- Das ist ein Test!\n+ This is a Test\n End.\n')

    def test_formatTimedelta(self):
        now = datetime.now()
        self.assertEqual(formatTimedelta(now - now), '0:00:00')

    def test_remove_from_dict(self):
        a = {'a': 1, 'b': 2}
        b = {'b': 2}
        self.assertEqual(remove_from_dict(a, ['b'], keep_keys=True), {'b': 2})
        self.assertEqual(remove_from_dict(a, ['a'], keep_keys=False), {'b': 2})
        self.assertEqual(remove_from_dict(b, ['b'], keep_keys=True), {'b': 2})
        self.assertEqual(remove_from_dict(b, ['a'], keep_keys=False), {'b': 2})
        self.assertEqual(remove_from_dict(b, [], keep_keys=True), {})
        self.assertEqual(remove_from_dict(a, ['a', 'b'], keep_keys=False), {})

    def test_formatDateTimetoTimeStamp(self):
        t = "1970-01-01T00:00:00"
        t = formatTimeString(t)
        timestamp = formatToTimeStamp(t)
        self.assertEqual(timestamp, 0)
        t2 = "2018-07-10T10:08:39"
        timestamp = formatToTimeStamp(t2)
        self.assertEqual(timestamp, 1531217319)
        t3 = datetime(2018, 7, 10, 10, 8, 39)
        timestamp = formatToTimeStamp(t3)
        self.assertEqual(timestamp, 1531217319)

    def test_formatTimeString(self):
        t = "2018-07-10T10:08:39"
        t = formatTimeString(t)
        t2 = addTzInfo(datetime(2018, 7, 10, 10, 8, 39))
        self.assertEqual(t, t2)

    def test_derive_beneficiaries(self):
        t = "holger80:10"
        b = derive_beneficiaries(t)
        self.assertEqual(b, [{"account": "holger80", "weight": 1000}])
        t = "holger80"
        b = derive_beneficiaries(t)
        self.assertEqual(b, [{"account": "holger80", "weight": 10000}])
        t = "holger80:30,beembot:40"
        b = derive_beneficiaries(t)
        self.assertEqual(b, [{"account": "beembot", "weight": 4000}, {"account": "holger80", "weight": 3000}])
        t = "holger80:30,beembot"
        b = derive_beneficiaries(t)
        self.assertEqual(b, [{"account": "beembot", "weight": 7000}, {"account": "holger80", "weight": 3000}])
        t = ["holger80:30", "beembot"]
        b = derive_beneficiaries(t)
        self.assertEqual(b, [{"account": "beembot", "weight": 7000}, {"account": "holger80", "weight": 3000}])        

    def test_derive_tags(self):
        t = "test1,test2"
        b = derive_tags(t)
        self.assertEqual(b, ["test1", "test2"])
        t = "test1, test2"
        b = derive_tags(t)
        self.assertEqual(b, ["test1", "test2"])
        t = "test1 test2"
        b = derive_tags(t)
        self.assertEqual(b, ["test1", "test2"])

    def test_seperate_yaml_dict_from_body(self):
        t = "---\npar1: data1\npar2: data2\npar3: 3\n---\n test ---"
        body, par = seperate_yaml_dict_from_body(t)
        self.assertEqual(par, {"par1": "data1", "par2": "data2", "par3": 3})
        self.assertEqual(body, "\n test ---")
        t = "---\npar1:data1\npar2:data2\npar3:3\n---\n test ---"
        body, par = seperate_yaml_dict_from_body(t)
        self.assertEqual(par, {"par1": "data1", "par2": "data2", "par3": 3})
        self.assertEqual(body, "\n test ---")
