# -*- coding: utf-8 -*-


STEEM_100_PERCENT = 10000
STEEM_1_PERCENT = 100
STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF21 = 300
STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF20 = 900
STEEM_REVERSE_AUCTION_WINDOW_SECONDS_HF6 = 1800
STEEM_CONTENT_REWARD_PERCENT_HF16 = 7500
STEEM_CONTENT_REWARD_PERCENT_HF21 = 6500
STEEM_DOWNVOTE_POOL_PERCENT_HF21 = 2500
STEEM_VOTE_REGENERATION_SECONDS = 432000
STEEM_VOTING_MANA_REGENERATION_SECONDS = 432000
STEEM_VOTE_DUST_THRESHOLD = 50000000
STEEM_ROOT_POST_PARENT = ''
STEEM_RC_REGEN_TIME = 60 * 60 * 24 * 5

HIVE_100_PERCENT = 10000
HIVE_1_PERCENT = 100
HIVE_REVERSE_AUCTION_WINDOW_SECONDS_HF21 = 300
HIVE_REVERSE_AUCTION_WINDOW_SECONDS_HF20 = 900
HIVE_REVERSE_AUCTION_WINDOW_SECONDS_HF6 = 1800
HIVE_CONTENT_REWARD_PERCENT_HF16 = 7500
HIVE_CONTENT_REWARD_PERCENT_HF21 = 6500
HIVE_DOWNVOTE_POOL_PERCENT_HF21 = 2500
HIVE_VOTE_REGENERATION_SECONDS = 432000
HIVE_VOTING_MANA_REGENERATION_SECONDS = 432000
HIVE_VOTE_DUST_THRESHOLD = 50000000
HIVE_ROOT_POST_PARENT = ''
HIVE_RC_REGEN_TIME = 60 * 60 * 24 * 5

STATE_BYTES_SCALE = 10000
STATE_TRANSACTION_BYTE_SIZE = 174
STATE_TRANSFER_FROM_SAVINGS_BYTE_SIZE = 229
STATE_LIMIT_ORDER_BYTE_SIZE = 1940
EXEC_FOLLOW_CUSTOM_OP_SCALE = 20
RC_DEFAULT_EXEC_COST = 100000
STATE_COMMENT_VOTE_BYTE_SIZE = 525

CURVE_CONSTANT = 2000000000000
CURVE_CONSTANT_X4 = 4 * CURVE_CONSTANT
SQUARED_CURVE_CONSTANT = CURVE_CONSTANT * CURVE_CONSTANT

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
                          'comment_vote_object_base_size': 47 * STATE_COMMENT_VOTE_BYTE_SIZE,
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

resource_execution_time = {"account_create_operation_exec_time": 57700,
                           "account_create_with_delegation_operation_exec_time": 57700,
                           "account_update_operation_exec_time": 14000,
                           "account_witness_proxy_operation_exec_time": 117000,
                           "account_witness_vote_operation_exec_time": 23000,
                           "cancel_transfer_from_savings_operation_exec_time": 11500,
                           "change_recovery_account_operation_exec_time": 12000,
                           "claim_account_operation_exec_time": 10000,
                           "claim_reward_balance_operation_exec_time": 50300,
                           "comment_operation_exec_time": 114100,
                           "comment_options_operation_exec_time": 13200,
                           "convert_operation_exec_time": 15700,
                           "create_claimed_account_operation_exec_time": 57700,
                           "custom_operation_exec_time": 11400,
                           "custom_json_operation_exec_time": 11400,
                           "custom_binary_operation_exec_time": 11400,
                           "decline_voting_rights_operation_exec_time": 5300,
                           "delegate_vesting_shares_operation_exec_time": 19900,
                           "delete_comment_operation_exec_time": 51100,
                           "escrow_approve_operation_exec_time": 9900,
                           "escrow_dispute_operation_exec_time": 11500,
                           "escrow_release_operation_exec_time": 17200,
                           "escrow_transfer_operation_exec_time": 19100,
                           "feed_publish_operation_exec_time": 6200,
                           "limit_order_cancel_operation_exec_time": 9600,
                           "limit_order_create_operation_exec_time": 31700,
                           "limit_order_create2_operation_exec_time": 31700,
                           "request_account_recovery_operation_exec_time": 54400,
                           "set_withdraw_vesting_route_operation_exec_time": 17900,
                           "transfer_from_savings_operation_exec_time": 17500,
                           "transfer_operation_exec_time": 9600,
                           "transfer_to_savings_operation_exec_time": 6400,
                           "transfer_to_vesting_operation_exec_time": 44400,
                           "vote_operation_exec_time": 26500,
                           "withdraw_vesting_operation_exec_time": 10400,
                           "witness_set_properties_operation_exec_time": 9500,
                           "witness_update_operation_exec_time": 9500}

operation_exec_info = {}
