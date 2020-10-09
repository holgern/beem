# -*- coding: utf-8 -*-
import json
import re
import time
import logging
from .exceptions import (
    UnauthorizedError, RPCConnection, RPCError, NumRetriesReached, CallRetriesReached
)
log = logging.getLogger(__name__)


class Node(object):
    def __init__(
        self,
        url
    ):
        self.url = url
        self.error_cnt = 0
        self.error_cnt_call = 0

    def __repr__(self):
        return self.url


class Nodes(list):
    """Stores Node URLs and error counts"""
    def __init__(self, urls, num_retries, num_retries_call):
        self.set_node_urls(urls)
        self.num_retries = num_retries
        self.num_retries_call = num_retries_call

    def set_node_urls(self, urls):
        if isinstance(urls, str):
            url_list = re.split(r",|;", urls)
            if url_list is None:
                url_list = [urls]
        elif isinstance(urls, Nodes):
            url_list = [urls[i].url for i in range(len(urls))]
        elif isinstance(urls, (list, tuple, set)):
            url_list = urls
        elif urls is not None:
            url_list = [urls]
        else:
            url_list = []        
        super(Nodes, self).__init__([Node(x) for x in url_list])
        self.current_node_index = -1
        self.freeze_current_node = False        

    def __iter__(self):
        return self

    def __next__(self):
        next_node_count = 0
        if self.freeze_current_node:
            return self.url
        while next_node_count == 0 and (self.num_retries < 0 or self.node.error_cnt < self.num_retries):
            self.current_node_index += 1
            if self.current_node_index >= self.working_nodes_count:
                self.current_node_index = 0
            next_node_count += 1
            if next_node_count > self.working_nodes_count + 1:
                raise StopIteration
        return self.url

    next = __next__  # Python 2

    def export_working_nodes(self):
        nodes_list = []
        for i in range(len(self)):
            if self.num_retries < 0 or self[i].error_cnt <= self.num_retries:
                nodes_list.append(self[i].url)
        return nodes_list

    def __repr__(self):
        nodes_list = self.export_working_nodes()
        return str(nodes_list)

    @property
    def working_nodes_count(self):
        n = 0
        if self.freeze_current_node:
            i = self.current_node_index
            if self.current_node_index < 0:
                i = 0
            if self.num_retries < 0 or self[i].error_cnt <= self.num_retries:
                n += 1
            return n
        for i in range(len(self)):
            if self.num_retries < 0 or self[i].error_cnt <= self.num_retries:
                n += 1
        return n

    @property
    def url(self):
        if self.node is None:
            return ''
        return self.node.url

    @property
    def node(self):
        if self.current_node_index < 0:
            return self[0]
        return self[self.current_node_index]

    @property
    def error_cnt(self):
        if self.node is None:
            return 0
        return self.node.error_cnt

    @property
    def error_cnt_call(self):
        if self.node is None:
            return 0
        return self.node.error_cnt_call

    @property
    def num_retries_call_reached(self):
        return self.error_cnt_call >= self.num_retries_call

    def disable_node(self):
        """Disable current node"""
        if self.node is not None and self.num_retries_call >= 0:
            self.node.error_cnt_call = self.num_retries_call

    def increase_error_cnt(self):
        """Increase node error count for current node"""
        if self.node is not None:
            self.node.error_cnt += 1

    def increase_error_cnt_call(self):
        """Increase call error count for current node"""
        if self.node is not None:
            self.node.error_cnt_call += 1

    def reset_error_cnt_call(self):
        """Set call error count for current node to zero"""
        if self.node is not None:
            self.node.error_cnt_call = 0

    def reset_error_cnt(self):
        """Set node error count for current node to zero"""
        if self.node is not None:
            self.node.error_cnt = 0

    def sleep_and_check_retries(self, errorMsg=None, sleep=True, call_retry=False, showMsg=True):
        """Sleep and check if num_retries is reached"""
        if errorMsg:
            log.warning("Error: {}".format(errorMsg))
        if call_retry:
            cnt = self.error_cnt_call
            if (self.num_retries_call >= 0 and self.error_cnt_call > self.num_retries_call):
                raise CallRetriesReached()
        else:
            cnt = self.error_cnt
            if (self.num_retries >= 0 and self.error_cnt > self.num_retries):
                raise NumRetriesReached()

        if showMsg:
            if call_retry:
                log.warning("Retry RPC Call on node: %s (%d/%d) \n" % (self.url, cnt, self.num_retries_call))
            else:
                log.warning("Lost connection or internal error on node: %s (%d/%d) \n" % (self.url, cnt, self.num_retries))
        if not sleep:
            return
        if cnt < 1:
            sleeptime = 0
        elif cnt < 10:
            sleeptime = (cnt - 1) * 1.5 + 0.5
        else:
            sleeptime = 10
        if sleeptime:
            log.warning("Retrying in %d seconds\n" % sleeptime)
            time.sleep(sleeptime)
