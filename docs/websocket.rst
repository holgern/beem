******************
SteemWebsocket
******************

This class allows subscribe to push notifications from the Steem
node.

.. code-block:: python

    from pprint import pprint
    from beemapi.websocket import SteemWebsocket

    ws = SteemWebsocket(
        "wss://gtg.steem.house:8090",
        accounts=["test"],
        on_block=print,
    )

    ws.run_forever()

Defintion
=========
.. autoclass:: beemapi.websocket.SteemWebsocket
    :members:
    :undoc-members:
    :private-members:
    :special-members:
