from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
import re


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


class UnauthorizedError(Exception):
    """UnauthorizedError Exception."""

    pass


class RPCConnection(Exception):
    """RPCConnection Exception."""

    pass


class RPCError(Exception):
    """RPCError Exception."""

    pass


class RPCErrorDoRetry(Exception):
    """RPCErrorDoRetry Exception."""

    pass


class NumRetriesReached(Exception):
    """NumRetriesReached Exception."""

    pass


class CallRetriesReached(Exception):
    """CallRetriesReached Exception. Only for internal use"""

    pass


class MissingRequiredActiveAuthority(RPCError):
    pass


class UnkownKey(RPCError):
    pass


class NoMethodWithName(RPCError):
    pass


class NoApiWithName(RPCError):
    pass


class ApiNotSupported(RPCError):
    pass


class UnhandledRPCError(RPCError):
    pass


class NoAccessApi(RPCError):
    pass


class InvalidEndpointUrl(Exception):
    pass


class UnnecessarySignatureDetected(Exception):
    pass


class WorkingNodeMissing(Exception):
    pass


class TimeoutException(Exception):
    pass
