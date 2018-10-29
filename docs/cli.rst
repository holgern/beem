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
   Usage: cli.py [OPTIONS] COMMAND1 [ARGS]... [COMMAND2 [ARGS]...]...

   Options:
     -n, --node TEXT        URL for public Steem API (e.g.
                            https://api.steemit.com)
     -o, --offline          Prevent connecting to network
     -d, --no-broadcast     Do not broadcast
     -p, --no-wallet        Do not load the wallet
     -x, --unsigned         Nothing will be signed
     -e, --expires INTEGER  Delay in seconds until transactions are supposed to
                            expire (defaults to 60)
     -v, --verbose INTEGER  Verbosity
     --version              Show the version and exit.
     --help                 Show this message and exit.

   Commands:
     addkey                  Add key to wallet When no [OPTION] is given,...
     allow                   Allow an account/key to interact with your...
     approvewitness          Approve a witnesses
     balance                 Shows balance
     broadcast               broadcast a signed transaction
     buy                     Buy STEEM or SBD from the internal market...
     cancel                  Cancel order in the internal market
     changewalletpassphrase  Change wallet password
     claimreward             Claim reward balances By default, this will...
     config                  Shows local configuration
     convert                 Convert STEEMDollars to Steem (takes a week...
     createwallet            Create new wallet with a new password
     currentnode             Sets the currently working node at the first...
     delkey                  Delete key from the wallet PUB is the public...
     delprofile              Delete a variable in an account's profile
     disallow                Remove allowance an account/key to interact...
     disapprovewitness       Disapprove a witnesses
     downvote                Downvote a post/comment POST is...
     follow                  Follow another account
     follower                Get information about followers
     following               Get information about following
     importaccount           Import an account using a passphrase
     info                    Show basic blockchain info General...
     interest                Get information about interest payment
     listaccounts            Show stored accounts
     listkeys                Show stored keys
     mute                    Mute another account
     muter                   Get information about muter
     muting                  Get information about muting
     newaccount              Create a new account
     nextnode                Uses the next node in list
     openorders              Show open orders
     orderbook               Obtain orderbook of the internal market
     parsewif                Parse a WIF private key without importing
     permissions             Show permissions of an account
     pingnode                Returns the answer time in milliseconds
     power                   Shows vote power and bandwidth
     powerdown               Power down (start withdrawing VESTS from...
     powerdownroute          Setup a powerdown route
     powerup                 Power up (vest STEEM as STEEM POWER)
     pricehistory            Show price history
     resteem                 Resteem an existing post
     sell                    Sell STEEM or SBD from the internal market...
     set                     Set default_account, default_vote_weight or...
     setprofile              Set a variable in an account's profile
     sign                    Sign a provided transaction with available...
     ticker                  Show ticker
     tradehistory            Show price history
     transfer                Transfer SBD/STEEM
     unfollow                Unfollow/Unmute another account
     updatememokey           Update an account's memo key
     upvote                  Upvote a post/comment POST is...
     votes                   List outgoing/incoming account votes
     walletinfo              Show info about wallet
     witnesscreate           Create a witness
     witnesses               List witnesses
     witnessupdate           Change witness properties
