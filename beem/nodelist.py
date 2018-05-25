# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import next
import re
import time
import math


class NodeList(list):
    def __init__(self):
        nodes = [
            {
                "url": "https://api.steemit.com",
                "version": "0.19.4",
                "type": "appbase",
                "owner": "steemit",
                "score": 100
            },
            {
                "url": "wss://appbasetest.timcliff.com",
                "version": "0.19.4",
                "type": "appbase",
                "owner": "timcliff",
                "score": 20
            },
            {
                "url": "https://appbasetest.timcliff.com",
                "version": "0.19.4",
                "type": "appbase",
                "owner": "timcliff",
                "score": 10
            },
            {
                "url": "https://api.steem.house",
                "version": "0.19.4",
                "type": "appbase",
                "owner": "gtg",
                "score": 90
            },
            {
                "url": "https://api.steemitdev.com",
                "version": "0.19.4",
                "type": "appbase-dev",
                "owner": "steemit",
                "score": 100
            },
            {
                "url": "https://api.steemitstage.com",
                "version": "0.19.4",
                "type": "appbase-dev",
                "owner": "steemit",
                "score": 110
            },
            {
                "url": "wss://rpc.steemviz.com",
                "version": "0.19.3",
                "type": "normal",
                "owner": "ausbitbank",
                "score": 175
            },
            {
                "url": "https://rpc.steemviz.com",
                "version": "0.19.3",
                "type": "normal",
                "owner": "ausbitbank",
                "score": 80
            },
            {
                "url": "wss://steemd.privex.io",
                "version": "0.19.3",
                "type": "normal",
                "owner": "privex",
                "score": 90
            },
            {
                "url": "https://steemd.privex.io",
                "version": "0.19.3",
                "type": "normal",
                "owner": "privex",
                "score": 50
            },
            {
                "url": "wss://rpc.buildteam.io",
                "version": "0.19.3",
                "type": "normal",
                "owner": "themarkymark",
                "score": 165
            },
            {
                "url": "https://rpc.buildteam.io",
                "version": "0.19.3",
                "type": "normal",
                "owner": "themarkymark",
                "score": 120
            },
            {
                "url": "wss://gtg.steem.house:8090",
                "version": "0.19.3",
                "type": "normal",
                "owner": "gtg",
                "score": 75
            },
            {
                "url": "https://gtg.steem.house:8090",
                "version": "0.19.3",
                "type": "normal",
                "owner": "gtg",
                "score": 80
            },
            {
                "url": "wss://steemd.pevo.science",
                "version": "0.19.3",
                "type": "normal",
                "owner": "pharesim",
                "score": 170
            },
            {
                "url": "https://steemd.pevo.science",
                "version": "0.19.3",
                "type": "normal",
                "owner": "pharesim",
                "score": 30
            },
            {
                "url": "wss://rpc.steemliberator.com",
                "version": "0.19.3",
                "type": "normal",
                "owner": "netuoso",
                "score": 20
            },
            {
                "url": "https://rpc.steemliberator.com",
                "version": "0.19.3",
                "type": "normal",
                "owner": "netuoso",
                "score": 10
            },
            {
                "url": "wss://seed.bitcoiner.me",
                "version": "0.19.3",
                "type": "normal",
                "owner": "bitcoiner",
                "score": 1
            },
            {
                "url": "https://seed.bitcoiner.me",
                "version": "0.19.3",
                "type": "normal",
                "owner": "bitcoiner",
                "score": 1
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
                "version": "0.19.3",
                "type": "normal",
                "owner": "curie",
                "score": 50
            },
            {
                "url": "wss://testnet.steem.vc",
                "version": "0.19.2",
                "type": "testnet",
                "owner": "almost-digital",
                "score": 1
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
                "score": 1
            },
            {
                "url": "http://testnet.steem.vc",
                "version": "0.19.2",
                "type": "testnet",
                "owner": "almost-digital",
                "score": 5
            }]
        super(NodeList, self).__init__(nodes)

    def get_nodes(self, normal=True, appbase=True, dev=False, testnet=False):
        """ Returns nodes as list

            :param bool normal: when True, nodes with version 0.19.2 or 0.19.3 are included
            :param bool appbase: when True, nodes with version 0.19.4 are included
            :param bool dev: when True, dev nodes with version 0.19.4 are included
            :param bool testnet: when True, testnet nodes are included

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
        for node in self:
            if node["type"] in node_type_list:
                node_list.append(node)
        return [node["url"] for node in sorted(node_list, key=lambda self: self['score'], reverse=True)]

    def get_testnet(self):
        """Returns testnet nodes"""
        return self.get_nodes(normal=False, appbase=False, testnet=True)
