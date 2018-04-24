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
  from beem.account import Account
  from beem.comment import Comment
  from beem.instance import set_shared_steem_instance

  # Only for testing not a real working key
  wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"

  # set nobroadcast always to True, when testing
  testnet = Steem(
      nobroadcast=True,
      bundle=True,
      keys=[wif],
  )
  # Set testnet as shared instance
  set_shared_steem_instance(testnet)

  # Account and Comment will use now testnet
  account = Account("test")

  # Post 
  c = Comment("@gtg/witness-gtg-log")

  account.transfer("test1", 1, "STEEM")
  account.transfer("test2", 1, "STEEM")
  account.transfer("test3", 1, "SBD")
  # Upvote post with 25%
  c.upvote(25, voter=account)

  pprint(testnet.broadcast())


Simple Sell Script
------------------

.. code-block:: python

    from beem import Steem
    from beem.market import Market
    from beem.price import Price
    from beem.amount import Amount
    
    # Only for testing not a real working key
    wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"
  
    #
    # Instanciate Steem (pick network via API node)
    #
    steem = Steem(
        nobroadcast=True,   # <<--- set this to False when you want to fire!
        keys=[wif]          # <<--- use your real keys, when going live!
    )

    #
    # This defines the market we are looking at.
    # The first asset in the first argument is the *quote*
    # Sell and buy calls always refer to the *quote*
    #
    market = Market("SBD:STEEM",
        steem_instance=steem
    )

    #
    # Sell an asset for a price with amount (quote)
    #
    print(market.sell(
        Price(100.0, "STEEM/SBD"),
        Amount("0.01 SBD")
    ))


Sell at a timely rate
---------------------

.. code-block:: python

    import threading
    from beem import Steem
    from beem.market import Market
    from beem.price import Price
    from beem.amount import Amount

    # Only for testing not a real working key
    wif = "5KQwrPbwdL6PhXujxW37FSSQZ1JiwsST4cqQzDeyXtP79zkvFD3"

    def sell():
        """ Sell an asset for a price with amount (quote)
        """
        print(market.sell(
            Price(100.0, "SBD/STEEM"),
            Amount("0.01 STEEM")
        ))

        threading.Timer(60, sell).start()


    if __name__ == "__main__":
        #
        # Instanciate Steem (pick network via API node)
        #
        steem = Steem(
            nobroadcast=True,   # <<--- set this to False when you want to fire!
            keys=[wif]          # <<--- use your real keys, when going live!
        )

        #
        # This defines the market we are looking at.
        # The first asset in the first argument is the *quote*
        # Sell and buy calls always refer to the *quote*
        #
        market = Market("STEEM:SBD",
            steem_instance=steem
        )

        sell()
