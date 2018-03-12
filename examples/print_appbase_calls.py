from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import int, str
import sys
from datetime import timedelta
import time
import io
from beem.steem import Steem
import logging
from prettytable import PrettyTable
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    stm = Steem(node="https://api.steemitstage.com")
    # stm = Steem(node="wss://appbasetest.timcliff.com")
    all_calls = stm.rpc.get_methods(api="jsonrpc")
    t = PrettyTable(["method", "args", "ret"])
    t.align = "l"
    include_condenser_methods = False
    for call in all_calls:
        if include_condenser_methods or "condenser" not in call:
            ret = stm.rpc.get_signature({'method': call}, api="jsonrpc")
            t.add_row([
                call,
                ret['args'],
                ret['ret']
            ])
    print(t)
    with open('print_appbase.txt', 'w') as w:
        w.write(str(t))
    with open('print_appbase.html', 'w') as w:
        w.write(str(t.get_html_string()))
