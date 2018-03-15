# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import object
import beem as stm


class SharedInstance(object):
    instance = None
    config = {}


def shared_steem_instance():
    """ This method will initialize ``SharedInstance.instance`` and return it.
        The purpose of this method is to have offer single default
        steem instance that can be reused by multiple classes.

        .. code-block:: python

            from beem.account import Account
            from beem.instance import shared_steem_instance

            account = Account("test")
            # is equivalent with
            account = Account("test", steem_instance=shared_steem_instance())

    """
    if not SharedInstance.instance:
        clear_cache()
        SharedInstance.instance = stm.Steem(**SharedInstance.config)
    return SharedInstance.instance


def set_shared_steem_instance(steem_instance):
    """ This method allows us to override default steem instance for all users of
        ``SharedInstance.instance``.

        :param steem.steem.Steem steem_instance: Steem instance
    """
    clear_cache()
    SharedInstance.instance = steem_instance


def clear_cache():
    """ Clear Caches
    """
    from .blockchainobject import BlockchainObject
    BlockchainObject.clear_cache()


def set_shared_config(config):
    """ This allows to set a config that will be used when calling
        ``shared_steem_instance`` and allows to define the configuration
        without requiring to actually create an instance
    """
    if not isinstance(config, dict):
        raise AssertionError()
    SharedInstance.config = config
