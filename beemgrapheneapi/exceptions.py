from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


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
    """CallRetriesReached Exception."""

    pass
