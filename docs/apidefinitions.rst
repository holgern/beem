Api Definitions
===============

condenser_api
-------------

broadcast_block
~~~~~~~~~~~~~~~
not implemented

broadcast_transaction
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.transactionbuilder import TransactionBuilder
    t = TransactionBuilder()
    t.broadcast()

broadcast_transaction_synchronous
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.transactionbuilder import TransactionBuilder
    t = TransactionBuilder()
    t.broadcast()

get_account_bandwidth
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    account = Account("test")
    account.get_account_bandwidth()

get_account_count
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.blockchain import Blockchain
    b = Blockchain()
    b.get_account_count()

get_account_history
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("steemit")
    for h in acc.get_account_history(1,0):
        print(h)

get_account_reputations
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.blockchain import Blockchain
    b = Blockchain()
    for h in b.get_account_reputations():
        print(h)

get_account_votes
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    for h in acc.get_account_votes():
        print(h)

get_active_votes
~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.vote import ActiveVotes
    acc = Account("gtg")
    post = acc.get_feed(0,1)[0]
    a = ActiveVotes(post["authorperm"])
    a.printAsTable()

get_active_witnesses
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.witness import Witnesses
    w = Witnesses()
    w.printAsTable()

get_block
~~~~~~~~~

.. code-block:: python

    from beem.block import Block
    print(Block(1))

get_block_header
~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.block import BlockHeader
    print(BlockHeader(1))

get_blog
~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    for h in acc.get_blog():
        print(h)

get_blog_authors
~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    for h in acc.get_blog_authors():
        print(h)

get_blog_entries
~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    for h in acc.get_blog_entries():
        print(h)

get_chain_properties
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem import Steem
    stm = Steem()
    print(stm.get_chain_properties())

get_comment_discussions_by_payout
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Comment_discussions_by_payout
    q = Query(limit=10)
    for h in Comment_discussions_by_payout(q):
        print(h)

get_config
~~~~~~~~~~

.. code-block:: python

    from beem import Steem
    stm = Steem()
    print(stm.get_config())

get_content
~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    from beem.comment import Comment
    acc = Account("gtg")
    post = acc.get_feed(0,1)[0]
    print(Comment(post["authorperm"]))
    

get_content_replies
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    from beem.comment import Comment
    acc = Account("gtg")
    post = acc.get_feed(0,1)[0]
    c = Comment(post["authorperm"])
    for h in c.get_replies():
        print(h)

get_conversion_requests
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    print(acc.get_conversion_requests())

get_current_median_history_price
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem import Steem
    stm = Steem()
    print(stm.get_current_median_history())


get_discussions_by_active
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Discussions_by_active
    q = Query(limit=10)
    for h in Discussions_by_active(q):
        print(h)

get_discussions_by_author_before_date
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Discussions_by_author_before_date
    for h in Discussions_by_author_before_date(limit=10, author="gtg"):
        print(h)

get_discussions_by_blog
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Discussions_by_blog
    q = Query(limit=10)
    for h in Discussions_by_blog(q):
        print(h)

get_discussions_by_cashout
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Discussions_by_cashout
    q = Query(limit=10)
    for h in Discussions_by_cashout(q):
        print(h)

get_discussions_by_children
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Discussions_by_children
    q = Query(limit=10)
    for h in Discussions_by_children(q):
        print(h)

get_discussions_by_comments
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Discussions_by_comments
    q = Query(limit=10, start_author="steemit", start_permlink="firstpost")
    for h in Discussions_by_comments(q):
        print(h)

get_discussions_by_created
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Discussions_by_created
    q = Query(limit=10)
    for h in Discussions_by_created(q):
        print(h)

get_discussions_by_feed
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Discussions_by_feed
    q = Query(limit=10, tag="steem")
    for h in Discussions_by_feed(q):
        print(h)

get_discussions_by_hot
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Discussions_by_hot
    q = Query(limit=10, tag="steem")
    for h in Discussions_by_hot(q):
        print(h)

get_discussions_by_promoted
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Discussions_by_promoted
    q = Query(limit=10, tag="steem")
    for h in Discussions_by_promoted(q):
        print(h)

get_discussions_by_trending
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Discussions_by_trending
    q = Query(limit=10, tag="steem")
    for h in Discussions_by_trending(q):
        print(h)

get_discussions_by_votes
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Discussions_by_votes
    q = Query(limit=10)
    for h in Discussions_by_votes(q):
        print(h)

get_dynamic_global_properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem import Steem
    stm = Steem()
    print(stm.get_dynamic_global_properties())

get_escrow
~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    print(acc.get_escrow())

get_expiring_vesting_delegations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    print(acc.get_expiring_vesting_delegations())

get_feed
~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    for f in acc.get_feed():
        print(f)

get_feed_entries
~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    for f in acc.get_feed_entries():
        print(f)

get_feed_history
~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem import Steem
    stm = Steem()
    print(stm.get_feed_history())
    
get_follow_count
~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    print(acc.get_follow_count())

get_followers
~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    for f in acc.get_followers():
        print(f)

get_following
~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    for f in acc.get_following():
        print(f)

get_hardfork_version
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem import Steem
    stm = Steem()
    print(stm.get_hardfork_properties()["hf_version"])

get_key_references
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    from beem.wallet import Wallet
    acc = Account("gtg")
    w = Wallet()
    print(w.getAccountFromPublicKey(acc["posting"]["key_auths"][0][0]))

get_market_history
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.market import Market
    m = Market()
    for t in m.market_history():
        print(t)

get_market_history_buckets
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.market import Market
    m = Market()
    for t in m.market_history_buckets():
        print(t)

get_next_scheduled_hardfork
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem import Steem
    stm = Steem()
    print(stm.get_hardfork_properties())

get_open_orders
~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.market import Market
    m = Market()
    print(m.accountopenorders(account="gtg"))

get_ops_in_block
~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.block import Block
    b = Block(2e6, only_ops=True)
    print(b)

get_order_book
~~~~~~~~~~~~~~

.. code-block:: python

    from beem.market import Market
    m = Market()
    print(m.orderbook())

get_owner_history
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    print(acc.get_owner_history())

get_post_discussions_by_payout
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Post_discussions_by_payout
    q = Query(limit=10)
    for h in Post_discussions_by_payout(q):
        print(h)

get_potential_signatures
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.transactionbuilder import TransactionBuilder
    from beem.blockchain import Blockchain
    b = Blockchain()
    block = b.get_current_block()
    trx = block.json()["transactions"][0]
    t = TransactionBuilder(trx)
    print(t.get_potential_signatures())


get_reblogged_by
~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    from beem.comment import Comment
    acc = Account("gtg")
    post = acc.get_feed(0,1)[0]
    c = Comment(post["authorperm"])
    for h in c.get_reblogged_by():
        print(h)

get_recent_trades
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.market import Market
    m = Market()
    for t in m.recent_trades():
        print(t)

get_recovery_request
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    print(acc.get_recovery_request())

get_replies_by_last_update
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Replies_by_last_update
    q = Query(limit=10, start_author="steemit", start_permlink="firstpost")
    for h in Replies_by_last_update(q):
        print(h)

get_required_signatures
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.transactionbuilder import TransactionBuilder
    from beem.blockchain import Blockchain
    b = Blockchain()
    block = b.get_current_block()
    trx = block.json()["transactions"][0]
    t = TransactionBuilder(trx)
    print(t.get_required_signatures())

get_reward_fund
~~~~~~~~~~~~~~~

.. code-block:: python

    from beem import Steem
    stm = Steem()
    print(stm.get_reward_funds())

get_savings_withdraw_from
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    print(acc.get_savings_withdrawals(direction="from"))

get_savings_withdraw_to
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    print(acc.get_savings_withdrawals(direction="to"))

get_state
~~~~~~~~~

.. code-block:: python

    from beem.comment import RecentByPath
    for p in RecentByPath(path="promoted"):
        print(p)

get_tags_used_by_author
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    print(acc.get_tags_used_by_author())

get_ticker
~~~~~~~~~~

.. code-block:: python

    from beem.market import Market
    m = Market()
    print(m.ticker())

get_trade_history
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.market import Market
    m = Market()
    for t in m.trade_history():
        print(t)

get_transaction
~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.blockchain import Blockchain
    b = Blockchain()
    print(b.get_transaction("6fde0190a97835ea6d9e651293e90c89911f933c"))

get_transaction_hex
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.blockchain import Blockchain
    b = Blockchain()
    block = b.get_current_block()
    trx = block.json()["transactions"][0]
    print(b.get_transaction_hex(trx))

get_trending_tags
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.discussions import Query, Trending_tags
    q = Query(limit=10, start_tag="steemit")
    for h in Trending_tags(q):
        print(h)

get_version
~~~~~~~~~~~
not implemented

get_vesting_delegations
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    for v in acc.get_vesting_delegations():
        print(v)

get_volume
~~~~~~~~~~

.. code-block:: python

    from beem.market import Market
    m = Market()
    print(m.volume24h())

get_withdraw_routes
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    print(acc.get_withdraw_routes())

get_witness_by_account
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.witness import Witness
    w = Witness("gtg")
    print(w)

get_witness_count
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.witness import Witnesses
    w = Witnesses()
    print(w.witness_count)

get_witness_schedule
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem import Steem
    stm = Steem()
    print(stm.get_witness_schedule())

get_witnesses
~~~~~~~~~~~~~
not implemented
    
get_witnesses_by_vote
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.witness import WitnessesRankedByVote
    for w in WitnessesRankedByVote():
        print(w)

lookup_account_names
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg", full=False)
    print(acc.json())

lookup_accounts
~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.account import Account
    acc = Account("gtg")
    for a in acc.get_similar_account_names(limit=100):
        print(a)

lookup_witness_accounts
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.witness import ListWitnesses
    for w in ListWitnesses():
        print(w)

verify_account_authority
~~~~~~~~~~~~~~~~~~~~~~~~
disabled and not implemented

verify_authority
~~~~~~~~~~~~~~~~

.. code-block:: python

    from beem.transactionbuilder import TransactionBuilder
    from beem.blockchain import Blockchain
    b = Blockchain()
    block = b.get_current_block()
    trx = block.json()["transactions"][0]
    t = TransactionBuilder(trx)
    t.verify_authority()
    print("ok")
