from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import str
from .account import Account
from beembase.objects import Operation
from beembase.account import PrivateKey, PublicKey
from beembase.signedtransactions import Signed_Transaction
from beembase import transactions, operations
from .exceptions import (
    InsufficientAuthorityError,
    MissingKeyError,
    InvalidWifError,
    WalletLocked
)
from beem.instance import shared_steem_instance
import logging
log = logging.getLogger(__name__)


class TransactionBuilder(dict):
    """ This class simplifies the creation of transactions by adding
        operations and signers.
        To build your own transactions and sign them

        .. code-block:: python

           from beem.transactionbuilder import TransactionBuilder
           from beembase.operations import Transfer
           tx = TransactionBuilder()
           tx.appendOps(Transfer(**{
                    "from": "test",
                    "to": "test1",
                    "amount": "1 STEEM",
                    "memo": ""
                }))
           tx.appendSigner("test", "active")
           tx.sign()
           tx.broadcast()

    """
    def __init__(
        self,
        tx={},
        proposer=None,
        expiration=None,
        steem_instance=None
    ):
        self.steem = steem_instance or shared_steem_instance()
        self.clear()
        if tx and isinstance(tx, dict):
            super(TransactionBuilder, self).__init__(tx)
            # Load operations
            self.ops = tx["operations"]
            self._require_reconstruction = False
        else:
            self._require_reconstruction = True
        self.set_expiration(expiration)

    def set_expiration(self, p):
        self.expiration = p

    def is_empty(self):
        return not (len(self.ops) > 0)

    def list_operations(self):
        return [Operation(o) for o in self.ops]

    def _is_signed(self):
        return "signatures" in self and self["signatures"]

    def _is_constructed(self):
        return "expiration" in self and self["expiration"]

    def _is_require_reconstruction(self):
        return self._require_reconstruction

    def _set_require_reconstruction(self):
        self._require_reconstruction = True

    def _unset_require_reconstruction(self):
        self._require_reconstruction = False

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str(self.json())

    def __getitem__(self, key):
        if key not in self:
            self.constructTx()
        return dict(self).__getitem__(key)

    def get_parent(self):
        """ TransactionBuilders don't have parents, they are their own parent
        """
        return self

    def json(self):
        """ Show the transaction as plain json
        """
        if not self._is_constructed() or self._is_require_reconstruction():
            self.constructTx()
        return dict(self)

    def appendOps(self, ops, append_to=None):
        """ Append op(s) to the transaction builder

            :param list ops: One or a list of operations
        """
        if isinstance(ops, list):
            self.ops.extend(ops)
        else:
            self.ops.append(ops)
        self._set_require_reconstruction()

    def appendSigner(self, account, permission):
        """ Try to obtain the wif key from the wallet by telling which account
            and permission is supposed to sign the transaction
        """
        assert permission in ["active", "owner", "posting"], "Invalid permission"
        account = Account(account, steem_instance=self.steem)
        if permission not in account:
            account = Account(account, steem_instance=self.steem, lazy=False, full=True)
            account.clear_cache()
            account.refresh()
        if permission not in account:
            account = Account(account, steem_instance=self.steem)
        assert permission in account, "Could not access permission"

        required_treshold = account[permission]["weight_threshold"]

        if self.steem.wallet.locked():
            raise WalletLocked()

        def fetchkeys(account, perm, level=0):
            if level > 2:
                return []
            r = []
            for authority in account[perm]["key_auths"]:
                try:
                    wif = self.steem.wallet.getPrivateKeyForPublicKey(
                        authority[0])
                    r.append([wif, authority[1]])
                except Exception:
                    pass

            if sum([x[1] for x in r]) < required_treshold:
                # go one level deeper
                for authority in account[perm]["account_auths"]:
                    auth_account = Account(
                        authority[0], steem_instance=self.steem)
                    r.extend(fetchkeys(auth_account, perm, level + 1))

            return r

        if account not in self.signing_accounts:
            # is the account an instance of public key?
            if isinstance(account, PublicKey):
                self.wifs.add(
                    self.steem.wallet.getPrivateKeyForPublicKey(
                        str(account)
                    )
                )
            else:
                if isinstance(account, str):
                    account = Account(account, steem_instance=self.steem)
                assert permission in account, "Could not access permission"
                required_treshold = account[permission]["weight_threshold"]
                keys = fetchkeys(account, permission)
                if permission != "owner":
                    keys.extend(fetchkeys(account, "owner"))
                for x in keys:
                    self.wifs.add(x[0])

            self.signing_accounts.append(account)

    def appendWif(self, wif):
        """ Add a wif that should be used for signing of the transaction.
        """
        if wif:
            try:
                PrivateKey(wif)
                self.wifs.add(wif)
            except:
                raise InvalidWifError

    def constructTx(self):
        """ Construct the actual transaction and store it in the class's dict
            store
        """
        ops = list()
        for op in self.ops:
            # otherwise, we simply wrap ops into Operations
            ops.extend([Operation(op)])

        # We no wrap everything into an actual transaction
        # ops = transactions.addRequiredFees(self.steem.rpc, ops)
        expiration = transactions.formatTimeFromNow(
            self.expiration or self.steem.expiration
        )
        ref_block_num, ref_block_prefix = transactions.getBlockParams(
            self.steem.rpc)
        self.tx = Signed_Transaction(
            ref_block_prefix=ref_block_prefix,
            expiration=expiration,
            operations=ops,
            ref_block_num=ref_block_num
        )
        super(TransactionBuilder, self).update(self.tx.json())
        self._unset_require_reconstruction()

    def sign(self):
        """ Sign a provided transaction witht he provided key(s)

            :param dict tx: The transaction to be signed and returned
            :param string wifs: One or many wif keys to use for signing
                a transaction. If not present, the keys will be loaded
                from the wallet as defined in "missing_signatures" key
                of the transactions.
        """
        self.constructTx()

        if "operations" not in self or not self["operations"]:
            return

        # Legacy compatibility!

        # We need to set the default prefix, otherwise pubkeys are
        # presented wrongly!
        if self.steem.rpc:
            operations.default_prefix = (
                self.steem.rpc.chain_params["prefix"])
        elif "blockchain" in self:
            operations.default_prefix = self["blockchain"]["prefix"]

        try:
            signedtx = Signed_Transaction(**self.json())
        except:
            raise ValueError("Invalid TransactionBuilder Format")

        if not any(self.wifs):
            raise MissingKeyError

        signedtx.sign(self.wifs, chain=self.steem.rpc.chain_params)
        self["signatures"].extend(signedtx.json().get("signatures"))

    def verify_authority(self):
        """ Verify the authority of the signed transaction
        """
        try:
            if not self.steem.rpc.verify_authority(self.json()):
                raise InsufficientAuthorityError
        except Exception as e:
            raise e

    def broadcast(self):
        """ Broadcast a transaction to the steem network

            :param tx tx: Signed transaction to broadcast
        """
        # Cannot broadcast an empty transaction
        if not self._is_signed():
            self.sign()

        if "operations" not in self or not self["operations"]:
            return

        ret = self.json()

        if self.steem.nobroadcast:
            log.warning("Not broadcasting anything!")
            self.clear()
            return ret
        self.steem.register_apis(["network_broadcast"])
        # Broadcast
        try:
            if self.steem.blocking:
                ret = self.steem.rpc.broadcast_transaction_synchronous(
                    ret, api="network_broadcast")
                ret.update(**ret["trx"])
            else:
                self.steem.rpc.broadcast_transaction(
                    ret, api="network_broadcast")
        except Exception as e:
            raise e

        self.clear()
        return ret

    def clear(self):
        """ Clear the transaction builder and start from scratch
        """
        self.ops = []
        self.wifs = set()
        self.signing_accounts = []
        # This makes sure that _is_constructed will return False afterwards
        self["expiration"] = None
        super(TransactionBuilder, self).__init__({})

    def addSigningInformation(self, account, permission):
        """ This is a private method that adds side information to a
            unsigned/partial transaction in order to simplify later
            signing (e.g. for multisig or coldstorage)

            FIXME: Does not work with owner keys!
        """
        self.constructTx()
        self["blockchain"] = self.steem.rpc.chain_params

        if isinstance(account, PublicKey):
            self["missing_signatures"] = [
                str(account)
            ]
        else:
            accountObj = Account(account)
            authority = accountObj[permission]
            # We add a required_authorities to be able to identify
            # how to sign later. This is an array, because we
            # may later want to allow multiple operations per tx
            self.update({"required_authorities": {
                accountObj["name"]: authority
            }})
            for account_auth in authority["account_auths"]:
                account_auth_account = Account(account_auth[0])
                self["required_authorities"].update({
                    account_auth[0]: account_auth_account.get(permission)
                })

            # Try to resolve required signatures for offline signing
            self["missing_signatures"] = [
                x[0] for x in authority["key_auths"]
            ]
            # Add one recursion of keys from account_auths:
            for account_auth in authority["account_auths"]:
                account_auth_account = Account(account_auth[0])
                self["missing_signatures"].extend(
                    [x[0] for x in account_auth_account[permission]["key_auths"]]
                )

    def appendMissingSignatures(self):
        """ Store which accounts/keys are supposed to sign the transaction

            This method is used for an offline-signer!
        """
        missing_signatures = self.get("missing_signatures", [])
        for pub in missing_signatures:
            wif = self.steem.wallet.getPrivateKeyForPublicKey(pub)
            if wif:
                self.appendWif(wif)
