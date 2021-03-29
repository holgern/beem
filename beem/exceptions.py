# -*- coding: utf-8 -*-


class WalletExists(Exception):
    """ A wallet has already been created and requires a password to be
        unlocked by means of :func:`beem.wallet.Wallet.unlock`.
    """
    pass


class RPCConnectionRequired(Exception):
    """ An RPC connection is required
    """
    pass


class InvalidMemoKeyException(Exception):
    """ Memo key in message is invalid
    """
    pass


class WrongMemoKey(Exception):
    """ The memo provided is not equal the one on the blockchain
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
    """ No Wallet could be found, please use :func:`beem.wallet.Wallet.create` to
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


class InvalidMessageSignature(Exception):
    """ The message signature does not fit the message
    """
    pass


class NoWriteAccess(Exception):
    """ Cannot store to sqlite3 database due to missing write access
    """
    pass


class BatchedCallsNotSupported(Exception):
    """ Batch calls do not work
    """
    pass


class BlockWaitTimeExceeded(Exception):
    """ Wait time for new block exceeded
    """
    pass
