# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


STEEM_100_PERCENT = 10000
STEEM_1_PERCENT = 100
STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF20 = 900
STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF6 = 1800
STEEM_VOTE_REGENERATION_SECONDS = 432000
STEEM_VOTING_MANA_REGENERATION_SECONDS = 432000
STEEM_VOTE_DUST_THRESHOLD = 50000000
STEEM_ROOT_POST_PARENT = ''

STATE_BYTES_SCALE = 10000
STATE_TRANSACTION_BYTE_SIZE = 174
STATE_TRANSFER_FROM_SAVINGS_BYTE_SIZE = 229
STATE_LIMIT_ORDER_BYTE_SIZE = 1940
RC_DEFAULT_EXEC_COST = 100000
STEEM_RC_REGEN_TIME = 60 * 60 * 24 * 5

state_object_size_info = {'authority_base_size': 4 * STATE_BYTES_SCALE,
                          'authority_account_member_size': 18 * STATE_BYTES_SCALE,
                          'authority_key_member_size': 35 * STATE_BYTES_SCALE,
                          'account_object_base_size': 480 * STATE_BYTES_SCALE,
                          'account_authority_object_base_size': 40 * STATE_BYTES_SCALE,
                          'account_recovery_request_object_base_size': 32 * STATE_BYTES_SCALE,
                          'comment_object_base_size': 201 * STATE_BYTES_SCALE,
                          'comment_object_permlink_char_size': 1 * STATE_BYTES_SCALE,
                          'comment_object_parent_permlink_char_size': 2 * STATE_BYTES_SCALE,
                          'comment_object_beneficiaries_member_size': 18 * STATE_BYTES_SCALE,
                          'comment_vote_object_base_size': 47 * STATE_BYTES_SCALE,
                          'convert_request_object_base_size': 48 * STATE_BYTES_SCALE,
                          'decline_voting_rights_request_object_base_size': 28 * STATE_BYTES_SCALE,
                          'escrow_object_base_size': 119 * STATE_BYTES_SCALE,
                          'limit_order_object_base_size': 76 * STATE_LIMIT_ORDER_BYTE_SIZE,
                          'savings_withdraw_object_byte_size': 64 * STATE_TRANSFER_FROM_SAVINGS_BYTE_SIZE,
                          'transaction_object_base_size': 35 * STATE_TRANSACTION_BYTE_SIZE,
                          'transaction_object_byte_size': 1 * STATE_TRANSACTION_BYTE_SIZE,
                          'vesting_delegation_object_base_size': 60 * STATE_BYTES_SCALE,
                          'vesting_delegation_expiration_object_base_size': 44 * STATE_BYTES_SCALE,
                          'withdraw_vesting_route_object_base_size': 43 * STATE_BYTES_SCALE,
                          'witness_object_base_size': 266 * STATE_BYTES_SCALE,
                          'witness_object_url_char_size': 1 * STATE_BYTES_SCALE,
                          'witness_vote_object_base_size': 40 * STATE_BYTES_SCALE}

operation_exec_info = {}
