from beem.account import Account
from beem.comment import Comment
from beem.utils import addTzInfo, resolve_authorperm, formatTimeString
from datetime import datetime
import sys


if __name__ == "__main__":
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        # print("ERROR: command line parameter mismatch!")
        # print("usage: %s [account]" % (sys.argv[0]))
        account = "holger80"
    elif len(sys.argv) == 2:
        account = sys.argv[1]
        n_blogs = 100
    else:
        account = sys.argv[1]
        n_blogs = int(sys.argv[2])
    account = Account(account)
    print("Reading followers of %s" % account["name"])
    followers = account.get_followers(raw_name_list=False)
    blog = []
    all_received_votes = {}
    all_received_replies = {}
    for b in account.get_blog(limit=n_blogs):
        print("check blog nr %d/%d" % (len(blog) + 1, n_blogs))
        if b["authorperm"] != '@/':
            blog.append(b)
            c = Comment(b)
            c.refresh()
            for v in c.get_votes():
                if v["voter"] in all_received_votes:
                    all_received_votes[v["voter"]].append(v)
                else:
                    all_received_votes[v["voter"]] = [v]
                    
            for c in c.get_all_replies():
                if c["author"] in all_received_replies:
                    all_received_replies[c["author"]].append(c)
                else:
                    all_received_replies[c["author"]] = [c]
    n_votes = 0
    n_replies = 0
    for a in all_received_votes:
        n_votes += len(all_received_votes[a])
    for a in all_received_replies:
        n_replies += len(all_received_replies[a])
    own_mvest = []
    eff_hp = []
    rep = []
    last_vote_h = []
    last_post_d = []
    no_vote = 0
    no_post = 0
    last_votes = []
    last_posts = []
    last_comments = []
    returned_rshares = []
    returned_votes = []
    returned_replies = []
    for f in followers:
        if (len(rep) + 1) % 50 == 0:
            print("check follower %d/%d" % (len(rep) + 1, len(followers)))
        rep.append(f.rep)
        own_mvest.append(f.balances["available"][2].amount / 1e6)
        eff_hp.append(f.get_token_power())
        last_votes.append((addTzInfo(datetime.utcnow()) - (f["last_vote_time"])).total_seconds() / 60 / 60 / 24)
        last_posts.append((addTzInfo(datetime.utcnow()) - (f["last_root_post"])).total_seconds() / 60 / 60 / 24)
        last_comments.append((addTzInfo(datetime.utcnow()) - (f["last_post"])).total_seconds() / 60 / 60 / 24)
        returned_vote = 0
        returned_rshare = 0
        if f["name"] in all_received_votes:
            for v in all_received_votes[f["name"]]:
                returned_vote += 1
                returned_rshare += v["rshares"]
        returned_rshares.append(returned_rshare)
        returned_votes.append(returned_vote)
        returned_reply = 0
        if f["name"] in all_received_replies:
            for c in all_received_replies[f["name"]]:
                returned_reply += 1
        returned_replies.append(returned_reply)
                
    ghost_followers = 0
    dead_followers = 0
    active_followers = 0
    active_rep = 0
    active_hp = 0
    for i in range(len(followers)):
        if returned_votes[i] == 0 and returned_replies[i] == 0:
            ghost_followers += 1
            
        if last_votes[i] > 30 and last_posts[i] > 30 and last_comments[i] > 30:
            dead_followers += 1
        elif returned_votes[i] > 0 or returned_replies[i] > 0:
            active_hp += eff_hp[i]
            active_rep += rep[i]
            active_followers += 1
    print("\n\n")
    print("%s has %d (%d active, %d ghosts and %d dead) followers." % (account["name"], len(followers), active_followers, ghost_followers, dead_followers))
    print("%.2f %% are active (not ghost or dead)." % (active_followers / len(followers) * 100))
    print("%.2f %% of the last %d votes are from followers." % (sum(returned_votes) / n_votes * 100, n_votes))
    print("%.2f %% of the last %d replies are from followers." % (sum(returned_replies) / n_replies * 100, n_replies))
    print("%.2f %% of all effective HP owned by followers are from active followers." % (active_hp / sum(eff_hp) * 100))
    print("Effective HP owned by active followers: %.2f HP" % (active_hp))
    print("The mean reputation of the active followers is: %.2f" % (active_rep/active_followers))
