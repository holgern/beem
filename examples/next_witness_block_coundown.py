#!/usr/bin/python
import sys
from beem import Steem
from beem.witness import Witness, WitnessesRankedByVote
from time import sleep


def convert_block_diff_to_time_string(block_diff_est):
    next_block_s = int(block_diff_est) * 3
    next_block_min = next_block_s / 60
    next_block_h = next_block_min / 60
    next_block_d = next_block_h / 24
    time_diff_est = ""
    if next_block_d > 1:
        time_diff_est = "%.2f days" % next_block_d
    elif next_block_h > 1:
        time_diff_est = "%.2f hours" % next_block_h
    elif next_block_min > 1:
        time_diff_est = "%.2f minutes" % next_block_min
    else:
        time_diff_est = "%.2f seconds" % next_block_s
    return time_diff_est


if __name__ == "__main__":
    if len(sys.argv) != 2:
        witness = "holger80"
    else:
        witness = sys.argv[1]
    stm = Steem()
    witness = Witness(witness, steem_instance=stm)

    witness_schedule = stm.get_witness_schedule()
    config = stm.get_config()
    if "VIRTUAL_SCHEDULE_LAP_LENGTH2" in config:
        lap_length = int(config["VIRTUAL_SCHEDULE_LAP_LENGTH2"])
    else:
        lap_length = int(config["STEEM_VIRTUAL_SCHEDULE_LAP_LENGTH2"])
    witnesses = WitnessesRankedByVote(limit=250, steem_instance=stm)
    vote_sum = witnesses.get_votes_sum()

    virtual_time_to_block_num = int(witness_schedule["num_scheduled_witnesses"]) / (lap_length / (vote_sum + 1))
    while True:
        witness.refresh()
        witness_schedule = stm.get_witness_schedule(use_stored_data=False)

        witness_json = witness.json()
        virtual_diff = int(witness_json["virtual_scheduled_time"]) - int(witness_schedule['current_virtual_time'])
        block_diff_est = virtual_diff * virtual_time_to_block_num

        time_diff_est = convert_block_diff_to_time_string(block_diff_est)

        sys.stdout.write("\r Next block for %s in %s" % (witness["owner"], time_diff_est))
        sleep(30)
