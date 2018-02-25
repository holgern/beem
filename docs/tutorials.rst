*********
Tutorials
*********

Bundle Many Operations
----------------------

With Steem, you can bundle multiple operations into a single
transactions. This can be used to do a multi-send (one sender, multiple
receivers), but it also allows to use any other kind of operation. The
advantage here is that the user can be sure that the operations are
executed in the same order as they are added to the transaction.

.. code-block:: python

  from pprint import pprint
  from beem import Steem

  testnet = Steem(
      nobroadcast=True,
      bundle=True,
  )

  testnet.wallet.unlock("supersecret")

  testnet.transfer("test1", 1, "STEEM", account="test")
  testnet.transfer("test1", 1, "STEEM", account="test")
  testnet.transfer("test1", 1, "STEEM", account="test")
  testnet.transfer("test1", 1, "STEEM", account="test")

  pprint(testnet.broadcast())


Proposing a Transaction
-----------------------

In Steem, you can propose a transactions to any account. This is
used to facilitate on-chain multisig transactions. With
python-steem, you can do this simply by using the ``proposer``
attribute:

.. code-block:: python

  from pprint import pprint
  from beem import Steem

  testnet = Steem(
      proposer="test"
  )
  testnet.wallet.unlock("supersecret")
  pprint(testnet.transfer("tst1", 1, "STEEM", account="test"))

Simple Sell Script
------------------

.. code-block:: python

    from beem import Steem
    from beem.market import Market
    from beem.price import Price
    from beem.amount import Amount

    #
    # Instanciate Steem (pick network via API node)
    #
    steem = Steem(
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
        steem_instance=steem
    )

    #
    # Sell an asset for a price with amount (quote)
    #
    print(market.sell(
        Price(100.0, "STEEM/SBD"),
        Amount("0.01 STEEM")
    ))


Sell at a timely rate
---------------------

.. code-block:: python

    import threading
    from beem import Steem
    from beem.market import Market
    from beem.price import Price
    from beem.amount import Amount


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
        # Instanciate Steem (pick network via API node)
        #
        steem = Steem(
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
            steem_instance=steem
        )

        sell()
