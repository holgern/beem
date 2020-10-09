# -*- coding: utf-8 -*-
import beem


class SharedInstance(object):
    """Singelton for the Steem Instance"""
    instance = None
    config = {}


def shared_blockchain_instance():
    """ This method will initialize ``SharedInstance.instance`` and return it.
        The purpose of this method is to have offer single default
        steem instance that can be reused by multiple classes.

        .. code-block:: python

            from beem.account import Account
            from beem.instance import shared_steem_instance

            account = Account("test")
            # is equivalent with
            account = Account("test", blockchain_instance=shared_steem_instance())

    """
    if not SharedInstance.instance:
        clear_cache()
        from beem.storage import get_default_config_store
        default_chain = get_default_config_store()["default_chain"]
        if default_chain == "steem":
            SharedInstance.instance = beem.Steem(**SharedInstance.config)
        else:
            SharedInstance.instance = beem.Hive(**SharedInstance.config)
    return SharedInstance.instance


def set_shared_blockchain_instance(blockchain_instance):
    """ This method allows us to override default steem instance for all users of
        ``SharedInstance.instance``.

        :param Steem blockchain_instance: Steem instance
    """
    clear_cache()
    SharedInstance.instance = blockchain_instance


def shared_steem_instance():
    """ This method will initialize ``SharedInstance.instance`` and return it.
        The purpose of this method is to have offer single default
        steem instance that can be reused by multiple classes.

        .. code-block:: python

            from beem.account import Account
            from beem.instance import shared_steem_instance

            account = Account("test")
            # is equivalent with
            account = Account("test", blockchain_instance=shared_steem_instance())

    """
    if not SharedInstance.instance:
        clear_cache()
        SharedInstance.instance = beem.Steem(**SharedInstance.config)
    return SharedInstance.instance


def set_shared_steem_instance(steem_instance):
    """ This method allows us to override default steem instance for all users of
        ``SharedInstance.instance``.

        :param Steem steem_instance: Steem instance
    """
    clear_cache()
    SharedInstance.instance = steem_instance


def shared_hive_instance():
    """ This method will initialize ``SharedInstance.instance`` and return it.
        The purpose of this method is to have offer single default
        steem instance that can be reused by multiple classes.

        .. code-block:: python

            from beem.account import Account
            from beem.instance import shared_hive_instance

            account = Account("test")
            # is equivalent with
            account = Account("test", blockchain_instance=shared_hive_instance())

    """
    if not SharedInstance.instance:
        clear_cache()
        SharedInstance.instance = beem.Hive(**SharedInstance.config)
    return SharedInstance.instance


def set_shared_hive_instance(hive_instance):
    """ This method allows us to override default steem instance for all users of
        ``SharedInstance.instance``.

        :param Hive hive_instance: Hive instance
    """
    clear_cache()
    SharedInstance.instance = hive_instance


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
    SharedInstance.config.update(config)
    # if one is already set, delete
    if SharedInstance.instance:
        clear_cache()
        SharedInstance.instance = None
