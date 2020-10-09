# -*- coding: utf-8 -*-
import logging
from events import Events
from beemapi.websocket import NodeWebsocket
from beem.instance import shared_blockchain_instance
from beem.blockchain import Blockchain
from beem.price import Order, FilledOrder
log = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)


class Notify(Events):
    """ Notifications on Blockchain events.

        This modules allows yout to be notified of events taking place on the
        blockchain.

        :param fnt on_block: Callback that will be called for each block received
        :param Steem blockchain_instance: Steem instance

        **Example**

        .. code-block:: python

            from pprint import pprint
            from beem.notify import Notify

            notify = Notify(
                on_block=print,
            )
            notify.listen()

    """

    __events__ = [
        'on_block',
    ]

    def __init__(
        self,
        # accounts=[],
        on_block=None,
        only_block_id=False,
        blockchain_instance=None,
        keep_alive=25,
        **kwargs
    ):
        # Events
        Events.__init__(self)
        self.events = Events()

        # Steem instance
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.blockchain = blockchain_instance or shared_blockchain_instance()

        # Callbacks
        if on_block:
            self.on_block += on_block

        # Open the websocket
        self.websocket = NodeWebsocket(
            urls=self.blockchain.rpc.nodes,
            user=self.blockchain.rpc.user,
            password=self.blockchain.rpc.password,
            only_block_id=only_block_id,
            on_block=self.process_block,
            keep_alive=keep_alive
        )

    def reset_subscriptions(self, accounts=[]):
        """Change the subscriptions of a running Notify instance
        """
        self.websocket.reset_subscriptions(accounts)

    def close(self):
        """Cleanly close the Notify instance
        """
        self.websocket.close()

    def process_block(self, message):
        self.on_block(message)

    def listen(self):
        """ This call initiates the listening/notification process. It
            behaves similar to ``run_forever()``.
        """
        self.websocket.run_forever()
