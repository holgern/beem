# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import pytest
import unittest
from beemgraphenebase.ecdsasig import (
    sign_message,
    verify_message
)


wif = "5J4KCbg1G3my9b9hCaQXnHSm6vrwW9xQTJS6ZciW2Kek7cCkCEk"


class Testcases(unittest.TestCase):

    # Ignore warning:
    # https://www.reddit.com/r/joinmarket/comments/5crhfh/userwarning_implicit_cast_from_char_to_a/
    @pytest.mark.filterwarnings()
    def test_sign_message(self):
        signature = sign_message("Foobar", wif)
        self.assertTrue(verify_message("Foobar", signature))


if __name__ == '__main__':
    unittest.main()
