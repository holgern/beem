Transaction Builder
~~~~~~~~~~~~~~~~~~~

To build your own transactions and sign them

.. code-block:: python

   from steempy.transactionbuilder import TransactionBuilder
   from steempybase.operations import Transfer
   tx = TransactionBuilder()
   tx.appendOps(Transfer(**{
            "from": "test",
            "to": "test1",
            "amount": "1 STEEM",
            "memo": ""
        }))
   tx.appendSigner("test", "active")
   tx.sign()
   tx.broadcast()

.. autoclass:: steempy.transactionbuilder.TransactionBuilder
   :members:
