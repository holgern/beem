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
                "version": "0.19.10",
                "type": "appbase",
                "owner": "steemit",
                "score": 100
            },
            {
                "url": "wss://appbasetest.timcliff.com",
                "version": "0.19.10",
                "type": "appbase",
                "owner": "timcliff",
                "score": 20
            },
            {
                "url": "https://appbasetest.timcliff.com",
                "version": "0.19.10",
                "type": "appbase",
                "owner": "timcliff",
                "score": 10
            },
            {
                "url": "https://api.steem.house",
                "version": "0.19.10",
                "type": "appbase",
                "owner": "gtg",
                "score": 90
            },
            {
                "url": "https://api.steemitdev.com",
                "version": "0.19.10",
                "type": "appbase-dev",
                "owner": "steemit",
                "score": 100
            },
            {
                "url": "https://api.steemitstage.com",
                "version": "0.19.10",
                "type": "appbase-dev",
                "owner": "steemit",
                "score": 110
            },
            {
                "url": "wss://rpc.steemviz.com",
                "version": "0.19.3",
                "type": "normal",
                "owner": "ausbitbank",
                "score": 1
            },
            {
                "url": "https://rpc.steemviz.com",
                "version": "0.19.3",
                "type": "normal",
                "owner": "ausbitbank",
                "score": 1
            },
            {
                "url": "wss://steemd.privex.io",
                "version": "0.19.5",
                "type": "normal",
                "owner": "privex",
                "score": 150
            },
            {
                "url": "https://steemd.privex.io",
                "version": "0.19.5",
                "type": "normal",
                "owner": "privex",
                "score": 50
            },
            {
                "url": "wss://rpc.buildteam.io",
                "version": "0.19.5",
                "type": "normal",
                "owner": "themarkymark",
                "score": 165
            },
            {
                "url": "https://rpc.buildteam.io",
                "version": "0.19.5",
                "type": "normal",
                "owner": "themarkymark",
                "score": 120
            },
            {
                "url": "wss://appbase.buildteam.io",
                "version": "0.19.10",
                "type": "appbase",
                "owner": "themarkymark",
                "score": 165
            },
            {
                "url": "https://appbase.buildteam.io",
                "version": "0.19.10",
                "type": "appbase",
                "owner": "themarkymark",
                "score": 120
            },
            {
                "url": "wss://gtg.steem.house:8090",
                "version": "0.19.5",
                "type": "normal",
                "owner": "gtg",
                "score": 75
            },
            {
                "url": "https://gtg.steem.house:8090",
                "version": "0.19.5",
                "type": "normal",
                "owner": "gtg",
                "score": 80
            },
            {
                "url": "wss://steemd.pevo.science",
                "version": "0.19.2",
                "type": "normal",
                "owner": "pharesim",
                "score": 10
            },
            {
                "url": "https://steemd.pevo.science",
                "version": "0.19.3",
                "type": "normal",
                "owner": "pharesim",
                "score": 10
            },
            {
                "url": "wss://rpc.steemliberator.com",
                "version": "0.19.5",
                "type": "normal",
                "owner": "netuoso",
                "score": 50
            },
            {
                "url": "https://rpc.steemliberator.com",
                "version": "0.19.5",
                "type": "normal",
                "owner": "netuoso",
                "score": 20
            },
            {
                "url": "wss://seed.bitcoiner.me",
                "version": "0.19.3",
                "type": "normal",
                "owner": "bitcoiner",
                "score": -10
            },
            {
                "url": "https://seed.bitcoiner.me",
                "version": "0.19.3",
                "type": "normal",
                "owner": "bitcoiner",
                "score": -10
            },
            {
                "url": "wss://steemd.steemgigs.org",
                "version": "0.19.3",
                "type": "normal",
                "owner": "steemgigs",
                "score": 10
            },
            {
                "url": "https://steemd.steemgigs.org",
                "version": "0.19.3",
                "type": "normal",
                "owner": "steemgigs",
                "score": 10
            },
            {
                "url": "wss://steemd.minnowsupportproject.org",
                "version": "0.19.3",
                "type": "normal",
                "owner": "followbtcnews",
                "score": 10
            },
            {
                "url": "https://steemd.minnowsupportproject.org",
                "version": "0.19.3",
                "type": "normal",
                "owner": "followbtcnews",
                "score": 10
            },
            {
                "url": "https://rpc.curiesteem.com",
                "version": "0.19.5",
                "type": "normal",
                "owner": "curie",
                "score": 50
            },
            {
                "url": "wss://testnet.steem.vc",
                "version": "0.19.2",
                "type": "testnet",
                "owner": "almost-digital",
                "score": 20
            },
            {
                "url": "ws://testnet.steem.vc",
                "version": "0.19.2",
                "type": "testnet",
                "owner": "almost-digital",
                "score": 5
            },
            {
                "url": "https://testnet.steem.vc",
                "version": "0.19.2",
                "type": "testnet",
                "owner": "almost-digital",
                "score": 10
            },
            {
                "url": "http://testnet.steem.vc",
                "version": "0.19.2",
                "type": "testnet",
                "owner": "almost-digital",
                "score": 5
            },
            {
                "url": "https://testnet.steemitdev.com",
                "version": "0.21.0",
                "type": "testnet-dev",
                "owner": "steemit",
                "score": 5
            }]
        super(NodeList, self).__init__(nodes)

    def update_nodes(self, weights=None, steem_instance=None):
        """ Reads metadata from fullnodeupdate and recalculates the nodes score

            :params list/dict weight: can be used to weight the different benchmarks

            .. code-block:: python
                from beem.nodelist import NodeList
                nl = NodeList()
                weights = [0, 0.1, 0.2, 1]
                nl.update_nodes(weights)
                weights = {'block': 0.1, 'history': 0.1, 'apicall': 1, 'config': 1}
                nl.update_nodes(weights)
        """
        steem = steem_instance or shared_steem_instance()
        account = Account("fullnodeupdate", steem_instance=steem)
        metadata = json.loads(account["json_metadata"])
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

    def get_nodes(self, normal=True, appbase=True, dev=False, testnet=False, testnetdev=False, wss=True, https=True):
        """ Returns nodes as list

            :param bool normal: when True, nodes with version 0.19.5 are included
            :param bool appbase: when True, nodes with version 0.19.10 are included
            :param bool dev: when True, dev nodes with version 0.19.10 are included
            :param bool testnet: when True, testnet nodes are included
            :param bool testnetdev: When True, testnet-dev nodes are included

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
        for node in self:
            if node["type"] in node_type_list and node["score"] >= 0:
                if not https and node["url"][:5] == 'https':
                    continue
                if not wss and node["url"][:3] == 'wss':
                    continue
                node_list.append(node)

        return [node["url"] for node in sorted(node_list, key=lambda self: self['score'], reverse=True)]

    def get_testnet(self, testnet=True, testnetdev=False):
        """Returns testnet nodes"""
        return self.get_nodes(normal=False, appbase=False, testnet=testnet, testnetdev=testnetdev)
