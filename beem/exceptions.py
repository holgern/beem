# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class WalletExists(Exception):
    """ A wallet has already been created and requires a password to be
        unlocked by means of :func:`steem.wallet.unlock`.
    """
    pass


class WalletLocked(Exception):
    """ Wallet is locked
    """
    pass


class RPCConnectionRequired(Exception):
    """ An RPC connection is required
    """
    pass


class OfflineHasNoRPCException(Exception):
    """ When in offline mode, we don't have RPC
    """
    pass


class AccountExistsException(Exception):
    """ The requested account already exists
    """
    pass


class AccountDoesNotExistsException(Exception):
    """ The account does not exist
    """
    pass


class AssetDoesNotExistsException(Exception):
    """ The asset does not exist
    """
    pass


class InvalidAssetException(Exception):
    """ An invalid asset has been provided
    """
    pass


class InsufficientAuthorityError(Exception):
    """ The transaction requires signature of a higher authority
    """
    pass


class VotingInvalidOnArchivedPost(Exception):
    """ The transaction requires signature of a higher authority
    """
    pass


class MissingKeyError(Exception):
    """ A required key couldn't be found in the wallet
    """
    pass


class InvalidWifError(Exception):
    """ The provided private Key has an invalid format
    """
    pass


class BlockDoesNotExistsException(Exception):
    """ The block does not exist
    """
    pass


class NoWalletException(Exception):
    """ No Wallet could be found, please use :func:`steem.wallet.create` to
        create a new wallet
    """
    pass


class WitnessDoesNotExistsException(Exception):
    """ The witness does not exist
    """
    pass


class ContentDoesNotExistsException(Exception):
    """ The content does not exist
    """
    pass


class VoteDoesNotExistsException(Exception):
    """ The vote does not exist
    """
    pass


class WrongMasterPasswordException(Exception):
    """ The password provided could not properly unlock the wallet
    """
    pass


class VestingBalanceDoesNotExistsException(Exception):
    """ Vesting Balance does not exist
    """
    pass


class ObjectNotInProposalBuffer(Exception):
    """ Object was not found in proposal
    """
    pass


class InvalidMessageSignature(Exception):
    """ The message signature does not fit the message
    """
    pass


class KeyNotFound(Exception):
    """ Key not found
    """
    pass
