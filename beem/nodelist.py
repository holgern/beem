# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import next
import re
import time
import math
import json
from beem.instance import shared_steem_instance
from beem.account import Account
import logging
log = logging.getLogger(__name__)


class NodeList(list):
    """ Returns a node list

        .. code-block:: python

            from beem.nodelist import NodeList
            n = NodeList()
            nodes_urls = n.get_nodes()

    """
    def __init__(self):
        nodes = [
            {
                "url": "https://api.steemit.com",
                "version": "0.20.2",
                "type": "appbase-limited",
                "owner": "steemit",
                "hive": False,
                "score": 50
            },
            {
                "url": "https://api.justyy.com",
                "version": "0.20.2",
                "type": "appbase",
                "owner": "justyy",
                "hive": False,
                "score": 20
            },
            {
                "url": "https://api.steemitdev.com",
                "version": "0.19.11",
                "type": "appbase-dev",
                "owner": "steemit",
                "hive": False,
                "score": 10
            },
            {
                "url": "https://api.steemitstage.com",
                "version": "0.19.11",
                "type": "appbase-dev",
                "owner": "steemit",
                "hive": False,
                "score": 10
            },
            {
                "url": "wss://steemd.privex.io",
                "version": "0.20.2",
                "type": "appbase",
                "owner": "privex",
                "hive": False,
                "score": -10
            },
            {
                "url": "https://steemd.privex.io",
                "version": "0.20.2",
                "type": "appbase",
                "owner": "privex",
                "hive": False,
                "score": 50
            },
            {
                "url": "https://steemd.minnowsupportproject.org",
                "version": "0.19.12",
                "type": "appbase",
                "owner": "followbtcnews",
                "hive": False,
                "score": 100
            },
            {
                "url": "https://anyx.io",
                "version": "0.23.0",
                "type": "appbase",
                "owner": "anyx",
                "hive": True,
                "score": 80
            },
            {
                "url": "http://anyx.io",
                "version": "0.23.0",
                "type": "appbase",
                "owner": "anyx",
                "hive": True,
                "score": 50
            },            
            {
                "url": "wss://testnet.steem.vc",
                "version": "0.19.2",
                "type": "testnet",
                "owner": "almost-digital",
                "hive": False,
                "score": 20
            },
            {
                "url": "ws://testnet.steem.vc",
                "version": "0.19.2",
                "type": "testnet",
                "owner": "almost-digital",
                "hive": False,
                "score": 5
            },
            {
                "url": "https://testnet.steem.vc",
                "version": "0.19.2",
                "type": "testnet",
                "owner": "almost-digital",
                "hive": False,
                "score": 10
            },
            {
                "url": "http://testnet.steem.vc",
                "version": "0.19.2",
                "type": "testnet",
                "owner": "almost-digital",
                "hive": False,
                "score": 5
            },
            {
                "url": "https://testnet.steemitdev.com",
                "version": "0.21.0",
                "type": "testnet-dev",
                "owner": "steemit",
                "hive": False,
                "score": 5
            },
            {
                "url": "https://api.hivekings.com",
                "version": "0.23.0",
                "type": "appbase",
                "owner": "drakos",
                "hive": True,
                "score": 50
            },
            {
                "url": "https://api.hive.blog",
                "version": "0.23.0",
                "type": "appbase",
                "owner": "hive",
                "hive": True,
                "score": 50
            },
            {
                "url": "https://api.openhive.network",
                "version": "0.23.0",
                "type": "appbase",
                "owner": "gtg",
                "hive": True,
                "score": 20
            },
            {
                "url": "https://techcoderx.com",
                "version": "0.23.0",
                "type": "appbase",
                "owner": "techcoderx",
                "hive": True,
                "score": 10
            },
            {
                "url": "https://steem.61bts.com",
                "version": "0.22.5",
                "type": "appbase",
                "owner": "",
                "hive": False,
                "score": 10
            },
            {
                "url": "https://steem.bts.tw",
                "version": "0.22.5",
                "type": "appbase",
                "owner": "",
                "hive": False,
                "score": 10
            },
            {
                "url": "https://rpc.esteem.app",
                "version": "0.23.0",
                "type": "appbase",
                "owner": "good-karma",
                "hive": True,
                "score": 10
            },
            {
                "url": "https://hived.privex.io",
                "version": "0.23.0",
                "type": "appbase",
                "owner": "someguy123",
                "hive": True,
                "score": 10
            }]
        super(NodeList, self).__init__(nodes)

    def update_nodes(self, weights=None, steem_instance=None):
        """ Reads metadata from fullnodeupdate and recalculates the nodes score

            :param list/dict weight: can be used to weight the different benchmarks
            :type weight: list, dict

            .. code-block:: python

                from beem.nodelist import NodeList
                nl = NodeList()
                weights = [0, 0.1, 0.2, 1]
                nl.update_nodes(weights)
                weights = {'block': 0.1, 'history': 0.1, 'apicall': 1, 'config': 1}
                nl.update_nodes(weights)
        """
        steem = steem_instance or shared_steem_instance()
        metadata = None
        account = None
        cnt = 0
        while metadata is None and cnt < 5:
            cnt += 1
            try:
                account = Account("fullnodeupdate", steem_instance=steem)
                metadata = json.loads(account["json_metadata"])
            except:
                steem.rpc.next()
                account = None
                metadata = None
        if metadata is None:
            return
        report = metadata["report"]
        failing_nodes = metadata["failing_nodes"]
        parameter = metadata["parameter"]
        benchmarks = parameter["benchmarks"]
        if weights is None:
            weights_dict = {}
            for benchmark in benchmarks:
                weights_dict[benchmark] = (1. / len(benchmarks))
        elif isinstance(weights, list):
            weights_dict = {}
            i = 0
            weight_sum = 0
            for w in weights:
                weight_sum += w
            for benchmark in benchmarks:
                if i < len(weights):
                    weights_dict[benchmark] = weights[i] / weight_sum
                else:
                    weights_dict[benchmark] = 0.
                i += 1
        elif isinstance(weights, dict):
            weights_dict = {}
            i = 0
            weight_sum = 0
            for w in weights:
                weight_sum += weights[w]
            for benchmark in benchmarks:
                if benchmark in weights:
                    weights_dict[benchmark] = weights[benchmark] / weight_sum
                else:
                    weights_dict[benchmark] = 0.

        max_score = len(report) + 1
        new_nodes = []
        for node in self:
            new_node = node.copy()
            for report_node in report:
                if node["url"] == report_node["node"]:
                    new_node["version"] = report_node["version"]
                    scores = []
                    for benchmark in benchmarks:
                        result = report_node[benchmark]
                        rank = result["rank"]
                        if not result["ok"]:
                            rank = max_score + 1
                        score = (max_score - rank) / (max_score - 1) * 100
                        weighted_score = score * weights_dict[benchmark]
                        scores.append(weighted_score)
                    sum_score = 0
                    for score in scores:
                        sum_score += score
                    new_node["score"] = sum_score
            for node_failing in failing_nodes:
                if node["url"] == node_failing:
                    new_node["score"] = -1
            new_nodes.append(new_node)
        super(NodeList, self).__init__(new_nodes)

    def get_nodes(self, hive=False, exclude_limited=False, dev=False, testnet=False, testnetdev=False, wss=True, https=True, not_working=False, normal=True, appbase=True):
        """ Returns nodes as list

            :param bool hive: When True, only HIVE nodes will be returned
            :param bool exclude_limited: When True, limited nodes are excluded
            :param bool dev: when True, dev nodes with version 0.19.11 are included
            :param bool testnet: when True, testnet nodes are included
            :param bool testnetdev: When True, testnet-dev nodes are included
            :param bool not_working: When True, all nodes including not working ones will be returned
            :param bool normal: deprecated
            :param bool appbase: deprecated

        """
        node_list = []
        node_type_list = []
        if normal:
            node_type_list.append("normal")
        if appbase:
            node_type_list.append("appbase")
        if dev:
            node_type_list.append("appbase-dev")
        if testnet:
            node_type_list.append("testnet")
        if testnetdev:
            node_type_list.append("testnet-dev")
        if not exclude_limited:
            node_type_list.append("appbase-limited")
        for node in self:
            if node["type"] in node_type_list and (node["score"] >= 0 or not_working):
                if hive != node["hive"]:
                    continue
                if not https and node["url"][:5] == 'https':
                    continue
                if not wss and node["url"][:3] == 'wss':
                    continue
                node_list.append(node)

        return [node["url"] for node in sorted(node_list, key=lambda self: self['score'], reverse=True)]

    def get_testnet(self, testnet=True, testnetdev=False):
        """Returns testnet nodes"""
        return self.get_nodes(normal=False, appbase=False, testnet=testnet, testnetdev=testnetdev)
