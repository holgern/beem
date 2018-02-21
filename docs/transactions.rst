***********************************************
Manual Constructing and Signing of Transactions
***********************************************

.. warning:: This is a low level class. Do not use this class unless you
             know what you are doing!

.. note:: This class is under development and meant for people that are
          looking into the low level construction and signing of various
          transactions.

Loading Transactions Class
##########################

We load the class for manual transaction construction via:

.. code-block:: python

    from beembase import transactions, operations

Construction
############

Now we can use the predefined transaction formats, e.g. ``Transfer`` or
``limit_order_create`` as follows:

1. define the expiration time
2. define a JSON object that contains all data for that transaction
3. load that data into the corresponding **operations** class
4. collect multiple operations
5. get some blockchain parameters to prevent replay attack
6. Construct the actual **transaction** from the list of operations
7. sign the transaction with the corresponding private key(s)

**Example A: Transfer**

.. code-block:: python

        expiration = transactions.formatTimeFromNow(60)
        op = operations.Transfer(**{
            "from": "test",
            "to": "test1",
            "amount": "1.000 SBD",
            "memo": ""
        })
        ops    = [transactions.Operation(op)]
        ref_block_num, ref_block_prefix = transactions.getBlockParams(rpc)
        tx     = transactions.Signed_Transaction(ref_block_num=ref_block_num,
                                                 ref_block_prefix=ref_block_prefix,
                                                 expiration=expiration,
                                                 operations=ops)
        tx = tx.sign([wif])


Broadcasting
############

For broadcasting, we first need to convert the transactions class into a
JSON object. After that, we can broadcast this to the network:

.. code-block:: python

    # Broadcast JSON to network
    rpc.broadcast_transaction(tx.json(), api="network_broadcast"):
