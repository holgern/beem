beemapi\.websocket
==================

This class allows subscribe to push notifications from the Steem
node.

.. code-block:: python

    from pprint import pprint
    from beemapi.websocket import NodeWebsocket

    ws = NodeWebsocket(
        "wss://gtg.steem.house:8090",
        accounts=["test"],
        on_block=print,
    )

    ws.run_forever()


.. autoclass:: beemapi.websocket.NodeWebsocket
    :members:
    :undoc-members:
    :private-members:
    :special-members:


