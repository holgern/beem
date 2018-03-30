from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import re
from beemgrapheneapi.graphenerpc import RPCError


def decodeRPCErrorMsg(e):
    """ Helper function to decode the raised Exception and give it a
        python Exception class
    """
    found = re.search(
        (
            "(10 assert_exception: Assert Exception\n|"
            "3030000 tx_missing_posting_auth)"
            ".*: (.*)\n"
        ),
        str(e),
        flags=re.M)
    if found:
        return found.group(2).strip()
    else:
        return str(e)


class MissingRequiredActiveAuthority(RPCError):
    pass


class NoMethodWithName(RPCError):
    pass


class NoApiWithName(RPCError):
    pass


class UnhandledRPCError(RPCError):
    pass


class NoAccessApi(RPCError):
    pass


class NumRetriesReached(Exception):
    pass


class InvalidEndpointUrl(Exception):
    pass
