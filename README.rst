beem - Unofficial Python Library for Steem
===============================================

beem is an unofficial python library for steem, which is created new from scratch from `python-bitshares`_
The library name is derived from a beam maschine, similar to the analogy between steem and steam. beem includes `python-graphenelib`_.

.. image:: https://img.shields.io/pypi/v/beem.svg
    :target: https://pypi.python.org/pypi/beem/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/beem.svg
    :target: https://pypi.python.org/pypi/beem/
    :alt: Python Versions


.. image:: https://anaconda.org/conda-forge/beem/badges/version.svg
    :target: https://anaconda.org/conda-forge/beem


.. image:: https://anaconda.org/conda-forge/beem/badges/downloads.svg
    :target: https://anaconda.org/conda-forge/beem


Current build status
--------------------

.. image:: https://travis-ci.org/holgern/beem.svg?branch=master
    :target: https://travis-ci.org/holgern/beem

.. image:: https://ci.appveyor.com/api/projects/status/ig8oqp8bt2fmr09a?svg=true
    :target: https://ci.appveyor.com/project/holger80/beem

.. image:: https://circleci.com/gh/holgern/beem.svg?style=svg
    :target: https://circleci.com/gh/holgern/beem

.. image:: https://readthedocs.org/projects/beem/badge/?version=latest
  :target: http://beem.readthedocs.org/en/latest/?badge=latest

.. image:: https://api.codacy.com/project/badge/Grade/e5476faf97df4c658697b8e7a7efebd7
    :target: https://www.codacy.com/app/holgern/beem?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=holgern/beem&amp;utm_campaign=Badge_Grade

.. image:: https://pyup.io/repos/github/holgern/beem/shield.svg
     :target: https://pyup.io/repos/github/holgern/beem/
     :alt: Updates

.. image:: https://api.codeclimate.com/v1/badges/e7bdb5b4aa7ab160a780/test_coverage
   :target: https://codeclimate.com/github/holgern/beem/test_coverage
   :alt: Test Coverage

Support & Documentation
=======================
You may find help in the  `beem-discord-channel`_. The discord channel can also be used to discuss things about beem.

A complete library documentation is available at  `beem.readthedocs.io`_.

Advantages over the official steem-python library
=================================================

* High unit test coverage
* Support for websocket nodes
* Native support for new Appbase calls
* Node error handling and automatic node switching
* Usage of pycryptodomex instead of the outdated pycrypto
* Complete documentation of beempy and all classes including all functions
* steemconnect integration
* Works on read-only systems
* Own BlockchainObject class with cache
* Contains all broadcast operations
* Estimation of virtual account operation index from date or block number
* the command line tool beempy uses click and has more commands
* SteemNodeRPC can be used to execute even not implemented RPC-Calls
* More complete implemention

Installation
============
The minimal working python version is 2.7.x. or 3.4.x

beem can be installed parallel to python-steem.

For Debian and Ubuntu, please ensure that the following packages are installed:

.. code:: bash

    sudo apt-get install build-essential libssl-dev python-dev

For Fedora and RHEL-derivatives, please ensure that the following packages are installed:

.. code:: bash

    sudo yum install gcc openssl-devel python-devel

For OSX, please do the following::

    brew install openssl
    export CFLAGS="-I$(brew --prefix openssl)/include $CFLAGS"
    export LDFLAGS="-L$(brew --prefix openssl)/lib $LDFLAGS"

For Termux on Android, please install the following packages:

.. code:: bash

    pkg install clang openssl-dev python-dev

Signing and Verify can be fasten (200 %) by installing cryptography:

.. code:: bash

    pip install -U cryptography

Install beem by pip::

    pip install -U beem

You can install beem from this repository if you want the latest
but possibly non-compiling version::

    git clone https://github.com/holgern/beem.git
    cd beem
    python setup.py build

    python setup.py install --user

Run tests after install::

    pytest


Installing beem with conda-forge
--------------------------------

Installing beem from the conda-forge channel can be achieved by adding conda-forge to your channels with::

    conda config --add channels conda-forge

Once the conda-forge channel has been enabled, beem can be installed with::

    conda install beem

Signing and Verify can be fasten (200 %) by installing cryptography::

    conda install cryptography


CLI tool beempy
---------------
A command line tool is available. The help output shows the available commands:

    beempy --help

Stand alone version of CLI tool beempy
--------------------------------------
With the help of pyinstaller, a stand alone version of beempy was created for Windows, OSX and linux.
Each version has just to be unpacked and can be used in any terminal. The packed directories
can be found under release. Each release has a hash sum, which is created directly in the build-server
before transmitting the packed file. Please check the hash-sum after downloading.

Changelog
=========
0.19.50
-------
* Class to access Steemit Conveyor instances added by crokkon
* Option added to loed custom chains into the Steem object

0.19.49
-------
* add get_parent() to comment
* fix for beempy reward
* fix #46 (used power calculation may treat downvotes incorrectly) by crokkon
* fix #49 (discussions: set steem inst. as keyword argument) by crokkon
* Fix issue #51 (Discussions.get_discussions("blog", ...) returns the same two comments over and over)
* Fix #52 discussions.Replies_by_last_update() by crokkon
* Some bug fixes for Discussions
* Fix #54 (discussions may fail to handle empty responses correctly) by crokkon
* Snapshot improved
* Unit tests fixed
* Examples account_vp_over_time, account_reputation_by_SP 
* Spelling errors fix by crokkon
* Adding account methods for feed, blog, comments and replies by crokkon
* Fix #57 (SteemConnect expects double quotes in JSON)
* Improved handling of "Client returned invalid format. Expected JSON!" erros

0.19.48
-------
* Fix issue #45 (upvote() and downvote() of a pending post/comment without vote did not work)
* fix Amount for condenser broadcast ops on appbase nodes (fixes transfer broadcast for example)
* Added get_all_replies() to Comment for fetching all replies to a post
* bemepy claimreward improved
* Amount handling in Account improved
* upvote and downvote in beempy fixed
* update_vote and build_vp_arrays added to AccountSnapshot for showing vote power history
* account_vp_over_time added to examples

0.19.47
-------
* Some bug fixes
* Unit tests using testnet fixed
* beem.snapshot improved
* Example account_sp_over_time added
* Example account_curation_per_week_and_1k_sp added
* Add block_number check to wait_for_and_get_block

0.19.46
-------
* Force refresh of chain_params on node switch
* Replace recursive call in _get_followers
* Nodelist updated and bitcoiner.me node disabled
* First testing version of beem.snapshot with example added (thanks to crokkon for his example)

0.19.45
-------
* Add RLock to ObjectCache (ObjectCache is threadsafe now)
* Fix Blockchain Version comparison
* Add support for RPC Nodes below 0.19.5
* Add Example for measuring objectcache performance

0.19.44
-------
* Fix start and datetime in history_reverse
* add lazy option to all Discussion classes
* VIT and SMT testnet added to chains
* estimate_virtual_op_num improved by crokkon (fixes issue #36)

0.19.43
-------
* Fix minimal version in known_chains from 0.0.0 to 0.19.5

0.19.42
-------
* improve parse_body for post()
* Add conversion of datetime objects to timestamp in get_steem_per_mvest
* Fix beem for steem update 0.19.5 and 0.19.10

0.19.41
-------
* Issue #34 fixed thanks to crokkon
* "Bad or missing upstream response" is handled
* Use thread_num - 1 instances for blocks with threading
* Fix missing repsonses in market
* add parse_body to post() (thanks to crokkon)
* Examples added to all Discussions classes
* Discussions added for fetch more than 100 posts

0.19.40
-------
* Improvement of blocks/stream with threading (issue #32 fixed)
* Remove 5 tag limit
* Empty answer fixed for discussions
* Add fallback to condenser api for appbase nodes

0.19.39
-------
* get_feed_entries, get_blog_authors, get_savings_withdrawals, get_escrow, verify_account_authority, get_expiring_vesting_delegations, get_vesting_delegations, get_tags_used_by_author added to Account
* get_account_reputations, get_account_count added to Blockchain
* Replies_by_last_update, Trending_tags, Discussions_by_author_before_date
* ImageUploader class added
* Score calculation improved in update_nodes
* apidefinitions added to docs, which includes a complete condenser API call list.

0.19.38
-------
* Bug fixes
* Bool variables for SteemConnect link creation fixed
* Account handling in beem.account is improved
* json_metadata property added to beem.account
* missing addTzInfo added to beem.blockchain
* json_metadata update for comment edit improved
* use_stored_data option added to steem.info()
* poloniex removed and huobi and ubpit added to steem_btc_ticker()
* Add timeout to websocket connections
* Documentation improved by crokkon
* "time", "reputation" and "rshares" are parsed from string in all vote objects and inside all active_votes from a comment object
* lazy and full properly passed
* "votes", "virtual_last_update", "virtual_position", "virtual_scheduled_time",
    "created", "last_sbd_exchange_update", "hardfork_time_vote" are properly casted in all witness objects
* "time" and "expiration" are parsed to a datetime object inside all block objects
* The json() function returns the original not parsed json dict. It is available for Account, Block, BlockHeader, Comment, Vote and Witness
* json_transactions and json_operations added to Block, for returning all dates as string
* Issues #27 and #28 fixed (thanks to crokkon for reporting)
* Thread and Worker class for blockchain.blocks(threading=True)

0.19.37
-------
* Bug fixes
* Fix handling of empty json_metadata
* Prepare broadcasting in new appbase format
* Condenser API handling improved
* Condenser API forced for Broadcast operation on appbase-nodes

0.19.36
-------
* Several bug fixes
* Account features + some fixes and refactorings by crokkon
* blockchain.awaitTxConfirmation() fix timeout by crokkon
* beempy updatenodes added, this command can be used to update the nodes list
* NodeList.update_nodes() added, this command reads the metadata from fullnodeupdate, which contain newest nodes information
* add option wss and https for NodeList.get_nodes
* updatenodes is used in all tests
* add witnessenable, witnessdisable, witnessfeed and witness
* time_diff_est and block_diff_est added to witness for next block producing estimation
* btc_usd_ticker, steem_btc_ticker, steem_usd_implied and _weighted_average added to Market
* beempy witnesses uses the proxy name when set
* beempy keygen added, for creating a witness signing key
* beempy parsewif improved

0.19.35
-------
* Several bug fixes (including issue #18 and #20)
* fix get_config and get_blockchain_version
* fix get_network

0.19.34
-------
* Several bug fixes (including issue #17)
* missing steem_instance fixed
* update_account_profile fixed
* update_account_metadata added

0.19.33
-------
* Several bug fixes (including issue #13 and #16)
* steemconnect v2 integration added
* token storage added to wallet
* add setToken, clear_local_token, encrypt_token, decrypt_token,
  addToken, getTokenForAccountName, removeTokenFromPublicName, getPublicNames added to the wallet class
* url_from_tx add to steemconnect for creating a URL from any operation
* login demo add added
* add -l option to beempy for creating URL from any operation
* add -s option to beempy for broadcasting via steemconnect
* addtoken, deltoken and listtoken added to beempy

0.19.32
-------
* bug fix and improvements for beempy curation

0.19.31
-------
* datetime.date is also supported
* beempy curation improved
* owner key is used, when provided and when no other permission is given
* active key is used, when provided and when no posting key is given (post, vote, ...)
* MissingKeyError is raised when a wrong key is set by Steem(keys=[])

0.19.30
-------
* get_replies() for comments added
* Account_witness_proxy added
* Custom added
* Custom_binary added
* Prove_authority added
* Limit_order_create2 added
* Request_account_recovery added
* Recover_account added
* Escrow_transfer added
* Escrow_dispute added
* Escrow_release added
* Escrow_approve added
* Decline_voting_rights added
* Export option for votes and curation command under beempy added
* getOwnerKeysForAccount, getActiveKeysForAccount, getPostingKeysForAccount added
* Node Class and Nodelist added

0.19.29
-------
* Several bug fixes
* CLI improved
* wait_for_and_get_block refactoring (Thanks to crokkon)
* Bug fix for blockchain.stream(), raw_ops added
* Fix and improve estimate_virtual_op_num
* Support for New Appbase Operations format

0.19.28
-------
* Improve rewards command in beempy
* estimate_virtual_op_num improved and small bug fixed
* SBD value in Comment always converted to Amount
* accuracy renamed to stop_diff
* Doku of estimate_virtual_op_num improved
* Unit test for estimate_virtual_op_num added
* beempy rewards command renamed to pending
* new beempy command: rewards shows now the received rewards

0.19.27
-------
* Block have only_ops and only_virtual_ops as parameter
* transactions and operations property added to Block
* entryId changed to start_entry_id in get_feed, get_blog_entries and get_blog
* estimate_virtual_op_num() added to Account, can be used to fastly get account op numbers from dates or blocknumbers
* history and history_reverse uses estimate_virtual_op_num()
* blockchain.ops() is obsolete
* only_ops and only_virtual_ops added to blockchain.get_current_block(), blockchain.blocks() and blockchain.stream()
* reward, curation, verify added to cli
* new curation functions added to the Comment class
* Signed_Transaction.verify() fixed, by trying all recover_parameter from 0 to 3
* get_potential_signatures, get_transaction_hex and get_required_signatures added to Transactionbuilder
* KeyNotFound is replaced by MissingKeyError and KeyNotFound is removed

0.19.26
-------
* Several small bugs fixed
* cache which stores blockchainobjects is now autocleaned
* requests.session is now a shared instance
* websocket will be created again for each Steem instance
* A node benchmark which uses threads added to examples
* Documentation improved
* Optional threading added to beempy pingnode (use --threading with --sort)

0.19.25
-------
* bug fix release

0.19.24
-------
* AsciiChart for beempy: pricehistory, tradehistory and orderbook
* Sort nodes regarding their ping times (beempy ping --sort --remove)
* currentnode and nextnode skip not working nodes
* Memory consumption fer requests and websocket reduced when creating more instances of steem
* trade_history added to market
* Issue #4 fixed
* Steem(use_condenser=True) activates condenser_api calls for 19.4 nodes

0.19.23
-------
* new function for beempy added: power, follower, following, muter, muting, mute, nextnode, pingnode, currentnode
* support for read-only systems added
* more unit tests
* Several improvements and bug fixes

0.19.22
-------
* beempy (command line tool) improved and all missing functions which are available in steempy are added
* new functions to beempy added: witnesses, walletinfo, openorders, orderbook and claimreward
* unit tests for cli added

0.19.21
-------
* Transactionbuilder and Wallet improved
* Accounts with more than one authority can be used for signing
* Examples added
* reconstruct_tx added to sign and addSigningInformation
* proposer from Transactionbuilder removed, as it had no function
* rshares_to_vote_pct added

0.19.20
-------
* serveral bug fixes and improvements
* coverage improved
* rpc improvements
* Native appbase support for broadcasting transactions added
* Native appbase support for Transfer added

0.19.19
-------
* serveral bug fixes and improvements
* coverage improved
* steem.get_blockchain_version added
* post and comment_options moved from beem.commment to beem.steem
* wait_for_and_get_block improved
* num_retries handling improved
* block_numbers can be set as start and stop in account.history and account.history_reverse, when use_block_num=True (default)

0.19.18
-------
* bug fix release

0.19.17
-------
* GOLOS chain added
* Huge speed improvements for all sign/verify operations (around 200%) when secp256k1 can not be installed and cryptography is installed
* benchmark added
* Example for speed comparison with steem-python added
* Several bug fixes and improvements

0.19.16
-------
* rename wallet.purge() and wallet.purgeWallet() to wallet.wipe()
* Handle internal node errors
* Account class improved
* Several improvements

0.19.15
-------
* bugfixes for testnet operations
* refactoring

0.19.14
-------
* batched api calls possible
* Threading added for websockets
* bug fixes

0.19.13
-------
* beem is now in the beta state, as now 270 unit tests exists
* unit tests added for appbase
* bug fixes for appbase-api calls

0.19.12
-------
* bug fix release for condenser_api

0.19.11
-------
* beem is appbase ready
* more examples added
* print_appbase_calls added
* https nodes can be used

0.19.10
-------
* Memo encryption/decryption fixed

0.19.9
------
* CLI tool improved
* bug fixes
* more unittests

0.19.8
------
* bug fixes
* CLI tool added
* beem added to conda-forge
* more unittests

0.19.7
------
* works on python 2.7
* can be installed besides steem-python
* graphenelib included
* unit tests added
* comment and account improved
* timezone added
* Delete_comment added

0.19.6
------
* Small bug-fix

0.19.5
------
* Market fixed
* Account, Comment, Discussion and Witness class improved
* Bug fixes

0.19.4
------
* New library name is now beem
* Upstream fixes from https://github.com/xeroc/python-bitshares
* Improved Docu

0.19.3
------
* Add Comment/Post
* Add Witness
* Several bugfixes
* Added all transactions that are supported from steem-python
* New library name planned: beem

0.19.2
------
* Notify and websocket fixed
* Several fixes

0.19.1
------
* Imported from https://github.com/xeroc/python-bitshares
* Replaced all BitShares by Steem
* Flake8 fixed
* Unit tests are working
* renamed to beem
* Docs fixed
* Signing fixed
* pysteem: Account, Amount, Asset, Block, Blockchain, Instance, Memo, Message, Notify, Price, Steem, Transactionbuilder, Vote, Witness are working


License
=======
This library is licensed under the MIT License.

Acknowledgements
================
`python-bitshares`_ and `python-graphenelib`_ were created by Fabian Schuh (xeroc).


.. _python-graphenelib: https://github.com/xeroc/python-graphenelib
.. _python-bitshares: https://github.com/xeroc/python-bitshares
.. _Python: http://python.org
.. _Anaconda: https://www.continuum.io
.. _beem.readthedocs.io: http://beem.readthedocs.io/en/latest/
.. _beem-discord-channel: https://discord.gg/4HM592V
