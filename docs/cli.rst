beempy CLI
~~~~~~~~~~
`beempy` is a convenient CLI utility that enables you to manage your wallet, transfer funds, check
balances and more.

Using the Wallet
----------------
`beempy` lets you leverage your BIP38 encrypted wallet to perform various actions on your accounts.

The first time you use `beempy`, you will be prompted to enter a password. This password will be used to encrypt
the `beempy` wallet, which contains your private keys.

You can change the password via `changewalletpassphrase` command.

::

    beempy changewalletpassphrase


From this point on, every time an action requires your private keys, you will be prompted ot enter
this password (from CLI as well as while using `steem` library).

To bypass password entry, you can set an environment variable ``UNLOCK``.

::

    UNLOCK=mysecretpassword beempy transfer <recipient_name> 100 STEEM

Using a key json file
---------------------

A key_file.json can be used to provide private keys to beempy:
::

    {
        "account_a": {"posting": "5xx", "active": "5xx"},
        "account_b": {"posting": "5xx"},
    }

with

::

    beempy --keys key_file.json command

When set, the wallet cannot be used.

Common Commands
---------------
First, you may like to import your Steem account:

::

    beempy importaccount


You can also import individual private keys:

::

   beempy addkey <private_key>

Listing accounts:

::

   beempy listaccounts

Show balances:

::

   beempy balance account_name1 account_name2

Sending funds:

::

   beempy transfer --account <account_name> <recipient_name> 100 STEEM memo

Upvoting a post:

::

   beempy upvote --account <account_name> https://steemit.com/funny/@mynameisbrian/the-content-stand-a-comic


Setting Defaults
----------------
For a more convenient use of ``beempy`` as well as the ``beem`` library, you can set some defaults.
This is especially useful if you have a single Steem account.

::

   beempy set default_account test
   beempy set default_vote_weight 100

   beempy config
    +---------------------+--------+
    | Key                 | Value  |
    +---------------------+--------+
    | default_account     | test   |
    | default_vote_weight | 100    |
    +---------------------+--------+

If you've set up your `default_account`, you can now send funds by omitting this field:

::

    beempy transfer <recipient_name> 100 STEEM memo

Commands
--------

.. click:: beem.cli:cli
    :prog: beempy
    :show-nested:

beempy --help
-------------
You can see all available commands with ``beempy --help``

::

    ~ % beempy --help
   Usage: beempy [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

   Options:
     -n, --node TEXT        URL for public Steem API (e.g.
                            https://api.steemit.com)
     -o, --offline          Prevent connecting to network
     -d, --no-broadcast     Do not broadcast
     -p, --no-wallet        Do not load the wallet
     -x, --unsigned         Nothing will be signed
     -l, --create-link      Creates hivesigner links from all broadcast
                            operations
     -s, --steem            Connect to the Steem blockchain
     -h, --hive             Connect to the Hive blockchain
     -k, --keys TEXT        JSON file that contains account keys, when set, the
                            wallet cannot be used.
     -u, --use-ledger       Uses the ledger device Nano S for signing.
     --path TEXT            BIP32 path from which the keys are derived, when not
                            set, default_path is used.
     -t, --token            Uses a hivesigner token to broadcast (only broadcast
                            operation with posting permission)
     -e, --expires INTEGER  Delay in seconds until transactions are supposed to
                            expire (defaults to 60)
     -v, --verbose INTEGER  Verbosity
     --version              Show the version and exit.
     --help                 Show this message and exit.

   Commands:
     about                   About beempy
     addkey                  Add key to wallet When no [OPTION] is given,...
     addtoken                Add key to wallet When no [OPTION] is given, a...
     allow                   Allow an account/key to interact with your...
                             account...
     approvewitness          Approve a witnesses
     balance                 Shows balance
     beneficiaries           Set beneficaries
     broadcast               broadcast a signed transaction
     buy                     Buy STEEM/HIVE or SBD/HBD from the internal
                             market...
     cancel                  Cancel order in the internal market
     changekeys              Changes all keys for the specified account Keys...
     changerecovery          Changes the recovery account with the owner key...
     changewalletpassphrase  Change wallet password
     claimaccount            Claim account for claimed account creation.
     claimreward             Claim reward balances By default, this will...
     config                  Shows local configuration
     convert                 Convert SBD/HBD to Steem/Hive (takes a week to...
     createpost              Creates a new markdown file with YAML header
     createwallet            Create new wallet with a new password
     curation                Lists curation rewards of all votes for
                             authorperm...
     currentnode             Sets the currently working node at the first...
     customjson              Broadcasts a custom json First parameter is the...
     decrypt                 decrypt a (or more than one) decrypted memo/file...
     delegate                Delegate (start delegating VESTS to another...
     delete                  delete a post/comment POST is @author/permlink
     delkey                  Delete key from the wallet PUB is the public...
     delprofile              Delete a variable in an account's profile
     delproxy                Delete your witness/proposal system proxy
     deltoken                Delete name from the wallet name is the public...
     disallow                Remove allowance an account/key to interact...
     disapprovewitness       Disapprove a witnesses
     download                Download body with yaml header
     downvote                Downvote a post/comment POST is @author/permlink
     draw                    Generate pseudo-random numbers based on trx id,...
     encrypt                 encrypt a (or more than one) memo text/file with...
     featureflags            Get the account's feature flags.
     follow                  Follow another account
     follower                Get information about followers
     following               Get information about following
     followlist              Get information about followed lists follow_type...
     history                 Returns account history operations as table
     importaccount           Import an account using a passphrase
     info                    Show basic blockchain info General...
     interest                Get information about interest payment
     keygen                  Creates a new random BIP39 key or password based...
     listaccounts            Show stored accounts Can be used with the ledger...
     listkeys                Show stored keys
     listtoken               Show stored token
     message                 Sign and verify a message
     mute                    Mute another account
     muter                   Get information about muter
     muting                  Get information about muting
     newaccount              Create a new account
     nextnode                Uses the next node in list
     notifications           Show notifications of an account
     openorders              Show open orders
     orderbook               Obtain orderbook of the internal market
     parsewif                Parse a WIF private key without importing
     pending                 Lists pending rewards
     permissions             Show permissions of an account
     pingnode                Returns the answer time in milliseconds
     post                    broadcasts a post/comment.
     power                   Shows vote power and bandwidth
     powerdown               Power down (start withdrawing VESTS from...
     powerdownroute          Setup a powerdown route
     powerup                 Power up (vest STEEM/HIVE as STEEM/HIVE POWER)
     pricehistory            Show price history
     reblog                  Reblog an existing post
     reply                   replies to a comment
     rewards                 Lists received rewards
     sell                    Sell STEEM/HIVE or SBD/HBD from the internal...
     set                     Set default_account, default_vote_weight or...
     setprofile              Set a variable in an account's profile
     setproxy                Set your witness/proposal system proxy
     sign                    Sign a provided transaction with available and...
     stream                  Stream operations
     ticker                  Show ticker
     tradehistory            Show price history
     transfer                Transfer SBD/HBD or STEEM/HIVE
     unfollow                Unfollow/Unmute another account
     updatememokey           Update an account's memo key
     updatenodes             Update the nodelist from @fullnodeupdate
     uploadimage
     upvote                  Upvote a post/comment POST is @author/permlink
     userdata                Get the account's email address and phone number.
     verify                  Returns the public signing keys for a block
     votes                   List outgoing/incoming account votes
     walletinfo              Show info about wallet
     witness                 List witness information
     witnesscreate           Create a witness
     witnessdisable          Disable a witness
     witnessenable           Enable a witness
     witnesses               List witnesses
     witnessfeed             Publish price feed for a witness
     witnessproperties       Update witness properties of witness WITNESS with...
     witnessupdate           Change witness properties
