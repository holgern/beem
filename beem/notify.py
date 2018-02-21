import logging
from events import Events
from beemapi.websocket import SteemWebsocket
from beem.instance import shared_steem_instance
from beem.blockchain import Blockchain
from beem.price import Order, FilledOrder, UpdateCallOrder
from beem.account import AccountUpdate
log = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)


class Notify(Events):
    """ Notifications on Blockchain events.

        :param list accounts: Account names/ids to be notified about when changing
        :param fnt on_tx: Callback that will be called for each transaction received
        :param fnt on_block: Callback that will be called for each block received
        :param fnt on_account: Callback that will be called for changes of the listed accounts
        :param beem.steem.Steem steem_instance: Steem instance

        **Example**

        .. code-block:: python

            from pprint import pprint
            from beem.notify import Notify

            notify = Notify(
                accounts=["test"],
                on_block=print,
            )
            notify.listen()


    """

    __events__ = [
        'on_block',
    ]

    def __init__(
        self,
        accounts=[],
        on_block=None,
        only_block_id=False,
        steem_instance=None,
    ):
        # Events
        super(Notify, self).__init__()
        self.events = Events()

        # Steem instance
        self.steem = steem_instance or shared_steem_instance()
        # Callbacks

        if on_block:
            self.on_block += on_block

        # Open the websocket
        self.websocket = SteemWebsocket(
            urls=self.steem.rpc.urls,
            user=self.steem.rpc.user,
            password=self.steem.rpc.password,
            only_block_id=only_block_id,
            on_block=self.process_block,
        )

    def process_account(self, message):
        """ This is used for processing of account Updates. It will
            return instances of :class:beem.account.AccountUpdate`
        """
        self.on_account(AccountUpdate(
            message,
            steem_instance=self.steem
        ))

    def process_block(self, message):
        self.on_block(message)

    def listen(self):
        """ This call initiates the listening/notification process. It
            behaves similar to ``run_forever()``.
        """
        self.websocket.run_forever()
