******************
SteemWebsocket
******************

This class allows subscribe to push notifications from the Steem
node.

.. code-block:: python

    from pprint import pprint
    from steempyapi.websocket import SteemWebsocket

    ws = SteemWebsocket(
        "wss://gtg.steem.house:8090",
        accounts=["test"],
        # on_market=pprint,
        # on_block=print,
        on_account=print,
    )

    ws.run_forever()

Defintion
=========
.. autoclass:: steempyapi.websocket.SteemWebsocket
    :members:
    :undoc-members:
    :private-members:
    :special-members:
