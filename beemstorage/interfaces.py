# -*- coding: utf-8 -*-
# Inspired by https://raw.githubusercontent.com/xeroc/python-graphenelib/master/graphenestorage/interfaces.py
class StoreInterface(dict):

    """ The store interface is the most general store that we can have.

        It inherits dict and thus behaves like a dictionary. As such any
        key/value store can be used as store with or even without an adaptor.

        .. note:: This class defines ``defaults`` that are used to return
            reasonable defaults for the library.

        .. warning:: If you are trying to obtain a value for a key that does
            **not** exist in the store, the library will **NOT** raise but
            return a ``None`` value. This represents the biggest difference to
            a regular ``dict`` class.

        Methods that need to be implemented:

          * ``def setdefault(cls, key, value)``
          * ``def __init__(self, *args, **kwargs)``
          * ``def __setitem__(self, key, value)``
          * ``def __getitem__(self, key)``
          * ``def __iter__(self)``
          * ``def __len__(self)``
          * ``def __contains__(self, key)``


        .. note:: Configuration and Key classes are subclasses of this to allow
            storing keys separate from configuration.

    """

    defaults = {}

    @classmethod
    def setdefault(cls, key, value):
        """ Allows to define default values
        """
        cls.defaults[key] = value

    def __init__(self, *args, **kwargs):
        pass

    def __setitem__(self, key, value):
        """ Sets an item in the store
        """
        return dict.__setitem__(self, key, value)

    def __getitem__(self, key):
        """ Gets an item from the store as if it was a dictionary

            .. note:: Special behavior! If a key is not found, ``None`` is
                returned instead of raising an exception, unless a default
                value is found, then that is returned.
        """
        if key in self:
            return dict.__getitem__(self, key)
        elif key in self.defaults:
            return self.defaults[key]
        else:
            return None

    def __iter__(self):
        """ Iterates through the store
        """
        return dict.__iter__(self)

    def __len__(self):
        """ return lenght of store
        """
        return dict.__len__(self)

    def __contains__(self, key):
        """ Tests if a key is contained in the store.
        """
        return dict.__contains__(self, key)

    def items(self):
        """ Returns all items off the store as tuples
        """
        return dict.items(self)

    def get(self, key, default=None):
        """ Return the key if exists or a default value
        """
        return dict.get(self, key, default)

    # Specific for this library
    def delete(self, key):
        """ Delete a key from the store
        """
        raise NotImplementedError

    def wipe(self):
        """ Wipe the store
        """
        raise NotImplementedError


class KeyInterface(StoreInterface):
    """ The KeyInterface defines the interface for key storage.

        .. note:: This class inherits
            :class:`beemstorage.interfaces.StoreInterface` and defines
            additional key-specific methods.
    """

    def is_encrypted(self):
        """ Returns True/False to indicate required use of unlock
        """
        return False

    # Interface to deal with encrypted keys
    def getPublicKeys(self):
        """ Returns the public keys stored in the database
        """
        raise NotImplementedError

    def getPrivateKeyForPublicKey(self, pub):
        """ Returns the (possibly encrypted) private key that
            corresponds to a public key

           :param str pub: Public key

           The encryption scheme is BIP38
        """
        raise NotImplementedError

    def add(self, wif, pub=None):
        """ Add a new public/private key pair (correspondence has to be
            checked elsewhere!)

           :param str pub: Public key
           :param str wif: Private key
        """
        raise NotImplementedError

    def delete(self, pub):
        """ Delete a pubkey/privatekey pair from the store

           :param str pub: Public key
        """
        raise NotImplementedError


class EncryptedKeyInterface(KeyInterface):
    """ The EncryptedKeyInterface extends KeyInterface to work with encrypted
        keys
    """

    def is_encrypted(self):
        """ Returns True/False to indicate required use of unlock
        """
        return True

    def unlock(self, password):
        """ Tries to unlock the wallet if required

           :param str password: Plain password
        """
        raise NotImplementedError

    def locked(self):
        """ is the wallet locked?
        """
        return False

    def lock(self):
        """ Lock the wallet again
        """
        raise NotImplementedError


class ConfigInterface(StoreInterface):
    """ The BaseKeyStore defines the interface for key storage

        .. note:: This class inherits
            :class:`beemstorage.interfaces.StoreInterface` and defines
            **no** additional configuration-specific methods.
    """

    pass


class TokenInterface(StoreInterface):
    """ The TokenInterface defines the interface for token storage.

        .. note:: This class inherits
            :class:`beemstorage.interfaces.StoreInterface` and defines
            additional key-specific methods.
    """

    def is_encrypted(self):
        """ Returns True/False to indicate required use of unlock
        """
        return False

    # Interface to deal with encrypted keys
    def getPublicKeys(self):
        """ Returns the public keys stored in the database
        """
        raise NotImplementedError

    def getPrivateKeyForPublicKey(self, pub):
        """ Returns the (possibly encrypted) private key that
            corresponds to a public key

           :param str pub: Public key

           The encryption scheme is BIP38
        """
        raise NotImplementedError

    def add(self, wif, pub=None):
        """ Add a new public/private key pair (correspondence has to be
            checked elsewhere!)

           :param str pub: Public key
           :param str wif: Private key
        """
        raise NotImplementedError

    def delete(self, pub):
        """ Delete a pubkey/privatekey pair from the store

           :param str pub: Public key
        """
        raise NotImplementedError


class EncryptedTokenInterface(TokenInterface):
    """ The EncryptedKeyInterface extends KeyInterface to work with encrypted
        tokens
    """

    def is_encrypted(self):
        """ Returns True/False to indicate required use of unlock
        """
        return True

    def unlock(self, password):
        """ Tries to unlock the wallet if required

           :param str password: Plain password
        """
        raise NotImplementedError

    def locked(self):
        """ is the wallet locked?
        """
        return False

    def lock(self):
        """ Lock the wallet again
        """
        raise NotImplementedError
