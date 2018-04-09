from __future__ import print_function
import sys
from datetime import datetime, timedelta
import time
import io
import re
import gzip
import json
from beem.blockchain import Blockchain
from beem.comment import Comment
from beem.account import Account
from beem.utils import parse_time, construct_authorperm
from beem import exceptions
import logging
from binascii import hexlify, unhexlify
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

try:
    from cPickle import dumps, loads
except ImportError:
    from pickle import dumps, loads


def s_dump_text(elt_to_pickle, file_obj):
    '''dumps one element to file_obj, a file opened in write mode'''
    pickled_elt_str = dumps(elt_to_pickle)
    file_obj.write(hexlify(pickled_elt_str).decode("utf-8"))
    # record separator is a blank line
    file_obj.write('\n')


def s_dump_binary(elt_to_pickle, file_obj):
    '''dumps one element to file_obj, a file opened in binary write mode'''
    pickled_elt_str = dumps(elt_to_pickle)
    file_obj.write(hexlify(pickled_elt_str))
    # record separator is a blank line
    file_obj.write(bytes('\n'.encode("latin1")))


def s_load_text(file_obj):
    '''load contents from file_obj, returning a generator that yields one
    element at a time'''
    for line in file_obj:
        elt = loads(unhexlify(line[:-1].encode("latin")))
        yield elt


def s_load_binary(file_obj):
    '''load contents from file_obj, returning a generator that yields one
    element at a time'''
    for line in file_obj:
        elt = loads(unhexlify(line[:-1]))
        yield elt


if __name__ == "__main__":

    blockchain = Blockchain()
    threading = True
    thread_num = 8
    cur_block = blockchain.get_current_block()
    stop = cur_block.identifier
    startdate = cur_block.time() - timedelta(seconds=3600)
    start = blockchain.get_estimated_block_num(startdate, accurate=True)
    outf = gzip.open('blocks1.pkl', 'w')
    blocks = 0
    for block in blockchain.stream(opNames=[], start=start, stop=stop, threading=threading, thread_num=thread_num):
        s_dump_binary(block, outf)
        blocks = blocks + 1
        if blocks % 200 == 0:
            print(blocks, "blocks streamed")
    outf.close()

    for block in s_load_binary(gzip.open('blocks1.pkl')):
        print(block)
