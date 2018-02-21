.. python-steem documentation master file, created by
   sphinx-quickstart on Fri Jun  5 14:06:38 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. http://sphinx-doc.org/rest.html
   http://sphinx-doc.org/markup/index.html
   http://sphinx-doc.org/markup/para.html
   http://openalea.gforge.inria.fr/doc/openalea/doc/_build/html/source/sphinx/rest_syntax.html
   http://rest-sphinx-memo.readthedocs.org/en/latest/ReST.html

Welcome to beem's documentation!
===============================================

Steem is a blockchain-based rewards platform for publishers to monetize 
content and grow community.

It is based on *Graphene* (tm), a blockchain technology stack (i.e.
software) that allows for fast transactions and ascalable blockchain
solution. In case of Steem, it comes with decentralized publishing of
content.

About this Library
------------------

The purpose of *beem* is to simplify development of products and
services that use the Steem blockchain. It comes with

* it's own (bip32-encrypted) wallet
* RPC interface for the Blockchain backend
* JSON-based blockchain objects (accounts, blocks, prices, markets, etc)
* a simple to use yet powerful API
* transaction construction and signing
* push notification API
* *and more*

Quickstart
----------

.. note:: All methods that construct and sign a transaction can be given
          the ``account=`` parameter to identify the user that is going
          to affected by this transaction, e.g.:
          
          * the source account in a transfer
          * the accout that buys/sells an asset in the exchange
          * the account whos collateral will be modified

         **Important**, If no ``account`` is given, then the
         ``default_account`` according to the settings in ``config`` is
         used instead.

.. code-block:: python

   from beem import Steem
   steem = Steem()
   steem.wallet.unlock("wallet-passphrase")
   steem.transfer("<to>", "<amount>", "<asset>", "<memo>", account="<from>")

.. code-block:: python

   from beem.blockchain import Blockchain
   blockchain = Blockchain()
   for op in Blockchain.ops():
       print(op)

.. code-block:: python

   from beem.block import Block
   print(Block(1))

.. code-block:: python

   from beem.account import Account
   account = Account("test")
   print(account.balances)
   for h in account.history():
       print(h)

.. code-block:: python

   from beem.market import Market
   # Not working at the moment
   # market = Market("STEEM:SBD")
   # print(market.ticker())
   # market.steem.wallet.unlock("wallet-passphrase")
   # print(market.sell(300, 100)  # sell 100 STEEM for 300 STEEM/SBD

.. code-block:: python

   from beem.dex import Dex
   # not working at the moment
   # dex = Dex()
   # dex.steem.wallet.unlock("wallet-passphrase")
   

General
-------------------------
.. toctree::
   :maxdepth: 1

   installation
   quickstart
   tutorials
   configuration
   contribute
   support

beem Libraries
--------------------------

.. toctree::
   :maxdepth: 1

   steem
   instances
   account
   amount
   asset
   block
   blockchain
   exceptions
   dex
   market
   notify
   price
   vesting
   witness

Low Level Classes
-----------------

.. toctree::
   :maxdepth: 1

   storage
   utils
   transactionbuilder
   wallet
   websocket
   websocketrpc
   transactions
   memo

Glossary
========

.. toctree::
   :maxdepth: 1


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
