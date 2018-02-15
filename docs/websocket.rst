******************
BitSharesWebsocket
******************

This class allows subscribe to push notifications from the BitShares
node.

.. code-block:: python

    from pprint import pprint
    from steemapi.websocket import BitSharesWebsocket

    ws = BitSharesWebsocket(
        "wss://node.testnet.steem.eu",
        markets=[["1.3.0", "1.3.172"]],
        accounts=["xeroc"],
        objects=["2.0.x", "2.1.x"],
        on_market=pprint,
        on_account=print,
    )

    ws.run_forever()

Defintion
=========
.. autoclass:: steemapi.websocket.BitSharesWebsocket
    :members:
    :undoc-members:
    :private-members:
    :special-members:
