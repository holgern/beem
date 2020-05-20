Quickstart
==========

Hive/Steem blockchain
---------------------

Nodes for using beem with the Hive blockchain can be set by the command line tool with:

.. code-block:: bash

   beempy updatenodes --hive

Nodes for the Hive blockchain are set with

.. code-block:: bash

   beempy updatenodes


Hive nodes can be set in a python script with

.. code-block:: python

   from beem import Hive
   from beem.nodelist import NodeList
   nodelist = NodeList()
   nodelist.update_nodes()
   nodes = nodelist.get_hive_nodes()
   hive = Hive(node=nodes)
   print(hive.is_hive)

Steem nodes can be set in a python script with

.. code-block:: python

   from beem import Steem
   from beem.nodelist import NodeList
   nodelist = NodeList()
   nodelist.update_nodes()
   nodes = nodelist.get_steem_nodes()
   hive = Steem(node=nodes)
   print(hive.is_hive)


Hive
----
The hive object is the connection to the Hive blockchain.
By creating this object different options can be set.

.. note:: All init methods of beem classes can be given
          the ``blockchain_instance=`` parameter to assure that
          all objects use the same steem object. When the
          ``blockchain_instance=`` parameter is not used, the 
          steem object is taken from get_shared_blockchain_instance().

          :func:`beem.instance.shared_blockchain_instance` returns a global instance of steem.
          It can be set by :func:`beem.instance.set_shared_blockchain_instance` otherwise it is created
          on the first call.

.. code-block:: python

   from beem import Hive
   from beem.account import Account
   hive = Hive()
   account = Account("test", blockchain_instance=hive)

.. code-block:: python

   from beem import Hive
   from beem.account import Account
   from beem.instance import set_shared_blockchain_instance
   hive = Hive()
   set_shared_blockchain_instance(hive)
   account = Account("test")

Wallet and Keys
---------------
Each account has the following keys:

* Posting key (allows accounts to post, vote, edit, resteem and follow/mute)
* Active key (allows accounts to transfer, power up/down, voting for witness, ...)
* Memo key (Can be used to encrypt/decrypt memos)
* Owner key (The most important key, should not be used with beem)

Outgoing operation, which will be stored in the steem blockchain, have to be
signed by a private key. E.g. Comment or Vote operation need to be signed by the posting key
of the author or upvoter. Private keys can be provided to beem temporary or can be
stored encrypted in a sql-database (wallet).

.. note:: Before using the wallet the first time, it has to be created and a password has
          to set. The wallet content is available to beempy and all python scripts, which have
          access to the sql database file.

Creating a wallet
~~~~~~~~~~~~~~~~~
``hive.wallet.wipe(True)`` is only necessary when there was already an wallet created.

.. code-block:: python

   from beem import Hive
   hive = Hive()
   hive.wallet.wipe(True)
   hive.wallet.unlock("wallet-passphrase")

Adding keys to the wallet
~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: python

   from beem import Steem
   hive = Hive()
   hive.wallet.unlock("wallet-passphrase")
   hive.wallet.addPrivateKey("xxxxxxx")
   hive.wallet.addPrivateKey("xxxxxxx")

Using the keys in the wallet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from beem import Hive
   hive = Hive()
   hive.wallet.unlock("wallet-passphrase")
   account = Account("test", blockchain_instance=hive)
   account.transfer("<to>", "<amount>", "<asset>", "<memo>")

Private keys can also set temporary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from beem import Hive
   hive = Hive(keys=["xxxxxxxxx"])
   account = Account("test", blockchain_instance=hive)
   account.transfer("<to>", "<amount>", "<asset>", "<memo>")

Receiving information about blocks, accounts, votes, comments, market and witness
---------------------------------------------------------------------------------

Receive all Blocks from the Blockchain

.. code-block:: python

   from beem.blockchain import Blockchain
   blockchain = Blockchain()
   for op in blockchain.stream():
       print(op)

Access one Block

.. code-block:: python

   from beem.block import Block
   print(Block(1))

Access an account

.. code-block:: python

   from beem.account import Account
   account = Account("test")
   print(account.balances)
   for h in account.history():
       print(h)

A single vote

.. code-block:: python

   from beem.vote import Vote
   vote = Vote(u"@gtg/ffdhu-gtg-witness-log|gandalf")
   print(vote.json())

All votes from an account

.. code-block:: python

   from beem.vote import AccountVotes
   allVotes = AccountVotes("gtg")

Access a post

.. code-block:: python

   from beem.comment import Comment
   comment = Comment("@gtg/ffdhu-gtg-witness-log")
   print(comment["active_votes"])

Access the market

.. code-block:: python

   from beem.market import Market
   market = Market("HBD:HIVE")
   print(market.ticker())

Access a witness

.. code-block:: python

   from beem.witness import Witness
   witness = Witness("gtg")
   print(witness.is_active)

Sending transaction to the blockchain
-------------------------------------

Sending a Transfer

.. code-block:: python

   from beem import Hive
   hive = Hive()
   hive.wallet.unlock("wallet-passphrase")
   account = Account("test", blockchain_instance=hive)
   account.transfer("null", 1, "SBD", "test")

Upvote a post

.. code-block:: python

   from beem.comment import Comment
   from beem import Hive
   hive = Hive()
   hive.wallet.unlock("wallet-passphrase")
   comment = Comment("@gtg/ffdhu-gtg-witness-log", blockchain_instance=hive)
   comment.upvote(weight=10, voter="test")

Publish a post to the blockchain

.. code-block:: python

   from beem import Hive
   hive = Hive()
   hive.wallet.unlock("wallet-passphrase")
   hive.post("title", "body", author="test", tags=["a", "b", "c", "d", "e"], self_vote=True)

Sell HIVE on the market

.. code-block:: python

   from beem.market import Market
   from beem import Hive
   hive.wallet.unlock("wallet-passphrase")
   market = Market("HBD:HIVE", blockchain_instance=hive)
   print(market.ticker())
   market.hive.wallet.unlock("wallet-passphrase")
   print(market.sell(300, 100))  # sell 100 HIVE for 300 HIVE/HBD
