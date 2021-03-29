# -*- coding: utf-8 -*-
import logging
import json
import io
import collections
import hashlib
from binascii import hexlify, unhexlify
import requests
from .instance import shared_blockchain_instance
from beem.account import Account
from beemgraphenebase.py23 import integer_types, string_types, text_type, py23_bytes
from beemgraphenebase.account import PrivateKey
from beemgraphenebase.ecdsasig import sign_message, verify_message


class ImageUploader(object):
    def __init__(
        self,
        base_url="https://steemitimages.com",
        challenge="ImageSigningChallenge",
        blockchain_instance=None,
        **kwargs
    ):
        self.challenge = challenge
        self.base_url = base_url
        if blockchain_instance is None:
            if kwargs.get("steem_instance"):
                blockchain_instance = kwargs["steem_instance"]
            elif kwargs.get("hive_instance"):
                blockchain_instance = kwargs["hive_instance"]        
        self.steem = blockchain_instance or shared_blockchain_instance()
        if self.steem.is_hive and base_url == "https://steemitimages.com":
            self.base_url = "https://images.hive.blog"

    def upload(self, image, account, image_name=None):
        """ Uploads an image

            :param image: path to the image or image in bytes representation which should be uploaded
            :type image: str, bytes
            :param str account: Account which is used to upload. A posting key must be provided.
            :param str image_name: optional

            .. code-block:: python

                from beem import Steem
                from beem.imageuploader import ImageUploader
                stm = Steem(keys=["5xxx"]) # private posting key
                iu = ImageUploader(blockchain_instance=stm)
                iu.upload("path/to/image.png", "account_name") # "private posting key belongs to account_name

        """
        account = Account(account, blockchain_instance=self.steem)
        if "posting" not in account:
            account.refresh()
        if "posting" not in account:
            raise AssertionError("Could not access posting permission")
        for authority in account["posting"]["key_auths"]:
            posting_wif = self.steem.wallet.getPrivateKeyForPublicKey(authority[0])

        if isinstance(image, string_types):
            image_data = open(image, 'rb').read()
        elif isinstance(image, io.BytesIO):
            image_data = image.read()
        else:
            image_data = image

        message = py23_bytes(self.challenge, "ascii") + image_data
        signature = sign_message(message, posting_wif)
        signature_in_hex = hexlify(signature).decode("ascii")

        files = {image_name or 'image': image_data}
        url = "%s/%s/%s" % (
            self.base_url,
            account["name"],
            signature_in_hex
        )
        r = requests.post(url, files=files)
        return r.json()
