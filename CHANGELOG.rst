Changelog
=========
0.20.13
-------
* beempy post improved
* beempy ImageUploader added
* issues #125 and #126 fixed
* VotedBeforeWaitTimeReached exception added

0.20.12
-------
* pep8 formating improved
* Too Many Requests error handled
* different limit handling in WLS fixed for account history
* percent-steem-dollars and max-accepted-payout added to beempy post

0.20.10
-------
* update_account_keys added for changing account keys
* comment, witness, account classes fixed for chains without SBD
* RC costs adapted on changes from 0.20.6
* VIT chain fixed
* update_account_keys function added to account
* beempy commands for post, reply and beneficiaries added

0.20.9
------
* add missing scrypt to the pyinstaller
* prepare for removed witness api in rpc nodes

0.20.8
------
* fix hardfork property in steem
* Fix resource_market_bytes calculation
* Adding additional parameter to recharge time calculations by flugschwein (PR #103)
* fix Comment reward calculations by crokkon (PR #105)
* Fix typo in witness update feed
* Fix appveyor CI

0.20.7
------
* Fix issue #97 `get_discussions()` does not finish if discussions are empty by espoem
* Fix issue #99 DivisionByZero Error in Account.get_rc_manabar() by crokkon
* Add claimaccount to beempy and some improvements for steem.sbd_symbol
* newaccount adapted for HF20 and can be used to create claimed account
* Correct operationids for WLS
* Improve steem.refresh_data() reading
* Set network prefix in Signed_Transaction and Operation for using the correct operationids
* Fix test_block unit test

0.20.6
------
* fix issue #93 - Wrong input parameters for `Discussions_by_author_before_date` in Docstring and `get_discussions` by espoem
* Add support for whaleshares (WLS) and Financial Transparency Gateway (EFTG)
* Using generic asset symbols  by crokkon
* Bug fixes for python 2.7
* Fix for witness update

0.20.5
------
* fix get_effective_vesting_shares()

0.20.4
------
* get_effective_vesting_shares() added to calculated max_mana correctly
* dict key words adapted to steemd for get_manabar() and get_rc_manabar()
* Voting mana fixed for 0 SP accounts
* comment_benefactor_reward adapted for snapshot
* Custom_json RC costs added to print_info

0.20.3
------
* add RC class to calculate RC costs of operations
* add comment, vote, transfer RC costs in account.print_info() and beempy power
* Shows number of possible comments, votes, tranfers with available RCs in account.print_info() and beempy power
* get_rc_cost was added to steem to calculation RC costs from resource count
* bug regarding new amount format in witness update fixed (also for beempy witnessenable and witnessdisable)

0.20.2
------
* estimated_mana is now capped by estimated_max
* print_info fixed()
* get_api_methods() and get_apis() added to Steem

0.20.1
------
* Improved get_rc_manabar(), get_manabar() output
* get_voting_power() fixed again
* print_info for account improved
* get_manabar_recharge_time_str(), get_manabar_recharge_timedelta() and get_manabar_recharge_time() added
* https://steemd-appbase.steemit.com added to nodelist

0.20.0
------
* Fully supporting hf20
* add get_resource_params(), get_resource_pool(), claim_account(), create_claimed_account() to Steem
* fix 30x fee for create_account
* add find_rc_accounts() to Blockchain
* get_rc(), get_rc_manabar(), get_manabar() added to Account
* get_voting_power() fixed

0.19.57
--------
* last hf19 release
* working witness_set_properties  operation
* witness_set_properties() added to steem
* beempy witnessproperties added
* beempy pricefeed uses witnessproperties  when witness wif is provided

0.19.56
-------
* adding methods to claim and create discounted accouts (PR #84) by crokkon
* Make vote rshare calculations HF20 ready (PR #85) by flugschwein
* Issue #80 fixed
* Fix some Warnings
* Blockchain.stream() improved for appbase format
* All unit tests are fixed and non-appbase related tests were removed

0.19.55
-------
* Issue #72 fixed by crokkon
* Improved Docu by jrswab
* Add get_vote_pct_for_SBD, sbd_to_vote_pct and sbd_to_rshares by flugschwein
* beembase/objects: fix serialization of appbase trx by crokkon
* Fix many documentation errors (based on error messages when building) by flugschwein
* Appbase detection fixed
* Unit tests fixed

0.19.54
-------
* Issue #69 fixed
* bug in batched streaming + cli fixed
* Nodelist updated
* unit tests improved
* Add last_current_block_num parameter to wait_for_and_get_block for reducing the number of api calls
* not_broadcasted_vote parameter added for improving vote calculation accuracy thanks to flugschwein

0.19.53
-------
* Add userdata and featureflags to beempy
* steemd.pevo.science and steemd.steemgigs.org removed from Nodelist
* bug fixed in allow and disallow for CLI
* Issue #52 closed thanks to crokkon
* Issue #64 fixed
* Issue #66 fixed thanks to flugschwein

0.19.52
-------
* appbase.buildtime.io node added
* history is made ready for appbase
* account refresh fixed
* fix ops_statistics for new appase nodes

0.19.51
-------
* Add missing trx_num to streamed block operation
* Add d.tube format to resolve_authorperm
* disable_chain_detection added to graphenerpc (for testing hivemind e.g.)
* set_next_node_on_empty_reply added to some appbase rpc calls

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
