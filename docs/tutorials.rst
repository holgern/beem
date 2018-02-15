*********
Tutorials
*********

Bundle Many Operations
----------------------

With BitShares, you can bundle multiple operations into a single
transactions. This can be used to do a multi-send (one sender, multiple
receivers), but it also allows to use any other kind of operation. The
advantage here is that the user can be sure that the operations are
executed in the same order as they are added to the transaction.

.. code-block:: python

  from pprint import pprint
  from steem import BitShares

  testnet = BitShares(
      "wss://node.testnet.steem.eu",
      nobroadcast=True,
      bundle=True,
  )

  testnet.wallet.unlock("supersecret")

  testnet.transfer("init0", 1, "TEST", account="xeroc")
  testnet.transfer("init1", 1, "TEST", account="xeroc")
  testnet.transfer("init2", 1, "TEST", account="xeroc")
  testnet.transfer("init3", 1, "TEST", account="xeroc")

  pprint(testnet.broadcast())


Proposing a Transaction
-----------------------

In BitShares, you can propose a transactions to any account. This is
used to facilitate on-chain multisig transactions. With
python-steem, you can do this simply by using the ``proposer``
attribute:

.. code-block:: python

  from pprint import pprint
  from steem import BitShares

  testnet = BitShares(
      "wss://node.testnet.steem.eu",
      proposer="xeroc"
  )
  testnet.wallet.unlock("supersecret")
  pprint(testnet.transfer("init0", 1, "TEST", account="xeroc"))

Simple Sell Script
------------------

.. code-block:: python

    from steem import BitShares
    from steem.market import Market
    from steem.price import Price
    from steem.amount import Amount

    #
    # Instanciate BitShares (pick network via API node)
    #
    steem = BitShares(
        "wss://node.testnet.steem.eu",
        nobroadcast=True   # <<--- set this to False when you want to fire!
    )

    #
    # Unlock the Wallet
    #
    steem.wallet.unlock("<supersecret>")

    #
    # This defines the market we are looking at.
    # The first asset in the first argument is the *quote*
    # Sell and buy calls always refer to the *quote*
    #
    market = Market(
        "GOLD:USD",
        steem_instance=steem
    )

    #
    # Sell an asset for a price with amount (quote)
    #
    print(market.sell(
        Price(100.0, "USD/GOLD"),
        Amount("0.01 GOLD")
    ))


Sell at a timely rate
---------------------

.. code-block:: python

    import threading
    from steem import BitShares
    from steem.market import Market
    from steem.price import Price
    from steem.amount import Amount


    def sell():
        """ Sell an asset for a price with amount (quote)
        """
        print(market.sell(
            Price(100.0, "USD/GOLD"),
            Amount("0.01 GOLD")
        ))

        threading.Timer(60, sell).start()


    if __name__ == "__main__":
        #
        # Instanciate BitShares (pick network via API node)
        #
        steem = BitShares(
            "wss://node.testnet.steem.eu",
            nobroadcast=True   # <<--- set this to False when you want to fire!
        )

        #
        # Unlock the Wallet
        #
        steem.wallet.unlock("<supersecret>")

        #
        # This defines the market we are looking at.
        # The first asset in the first argument is the *quote*
        # Sell and buy calls always refer to the *quote*
        #
        market = Market(
            "GOLD:USD",
            steem_instance=steem
        )

        sell()
