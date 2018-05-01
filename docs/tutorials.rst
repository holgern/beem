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
A block can only include one vote operation and
one comment operation from each sender.

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

Batch api calls on AppBase
--------------------------

Batch api calls are possible with AppBase RPC nodes.
If you call a Api-Call with add_to_queue=True it is not submitted but stored in rpc_queue.
When a call with add_to_queue=False (default setting) is started,
the complete queue is sended at once to the node. The result is a list with replies.

.. code-block:: python

    from beem import Steem
    stm = Steem("https://api.steemit.com")
    stm.rpc.get_config(add_to_queue=True)
    stm.rpc.rpc_queue

.. code-block:: python

    [{'method': 'condenser_api.get_config', 'jsonrpc': '2.0', 'params': [], 'id': 6}]

.. code-block:: python

    result = stm.rpc.get_block({"block_num":1}, api="block", add_to_queue=False)
    len(result)

.. code-block:: python

    2


Account history
---------------
Lets calculate the curation reward from the last 7 days:

.. code-block:: python

    from datetime import datetime, timedelta
    from beem.account import Account
    from beem.amount import Amount
    
    acc = Account("gtg")
    stop = datetime.utcnow() - timedelta(days=7)
    reward_vests = Amount("0 VESTS")
    for reward in acc.history_reverse(stop=stop, only_ops=["curation_reward"]):
                reward_vests += Amount(reward['reward'])
    curation_rewards_SP = acc.steem.vests_to_sp(reward_vests.amount)
    print("Rewards are %.3f SP" % curation_rewards_SP)

Transactionbuilder
------------------
Sign transactions with beem without using the wallet and build the transaction by hand.
Example without using the wallet:

.. code-block:: python

    from beem import Steem
    from beem.transactionbuilder import TransactionBuilder
    stm = Steem()
    tx = TransactionBuilder(steem_instance=stm)
    tx.appendOps(Transfer(**{"from": 'user_a',
                             "to": 'user_b',
                             "amount": '1.000 SBD',
                             "memo": 'test 2'}))
    tx.appendWif('5.....') # `user_a`
    tx.sign()
    tx.broadcast()

Example with using the wallet:

.. code-block:: python

    from beem.transactionbuilder import TransactionBuilder
    from beem import Steem
    stm = Steem()
    stm.wallet.unlock("secret_password")
    tx = TransactionBuilder(steem_instance=stm)
    tx.appendOps(Transfer(**{"from": 'user_a',
                             "to": 'user_b',
                             "amount": '1.000 SBD',
                             "memo": 'test 2'}))
    tx.appendSigner('user_a', 'active')
    tx.sign()
    tx.broadcast()
