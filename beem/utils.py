# This Python file uses the following encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import next
import re
import time
import math
from datetime import datetime, tzinfo, timedelta
import pytz
import difflib
from .exceptions import ObjectNotInProposalBuffer

timeFormat = '%Y-%m-%dT%H:%M:%S'
# https://github.com/matiasb/python-unidiff/blob/master/unidiff/constants.py#L37
# @@ (source offset, length) (target offset, length) @@ (section header)
RE_HUNK_HEADER = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))?\ @@[ ]?(.*)$",
    flags=re.MULTILINE)


def formatTime(t):
    """ Properly Format Time for permlinks
    """
    if isinstance(t, float):
        return datetime.utcfromtimestamp(t).strftime("%Y%m%dt%H%M%S%Z")
    if isinstance(t, datetime):
        return t.strftime("%Y%m%dt%H%M%S%Z")


def formatTimeString(t):
    """ Properly Format Time for permlinks
    """
    if isinstance(t, datetime):
        return t.strftime(timeFormat)
    utc = pytz.timezone('UTC')
    return utc.localize(datetime.strptime(t, timeFormat))


def addTzInfo(t, timezone='UTC'):
    """Returns a datetime object with tzinfo added"""
    if t and isinstance(t, datetime) and t.tzinfo is None:
        utc = pytz.timezone(timezone)
        t = utc.localize(t)
    return t


def formatTimeFromNow(secs=0):
    """ Properly Format Time that is `x` seconds in the future

        :param int secs: Seconds to go in the future (`x>0`) or the
                         past (`x<0`)
        :return: Properly formated time for Graphene (`%Y-%m-%dT%H:%M:%S`)
        :rtype: str

    """
    return datetime.utcfromtimestamp(
        time.time() + int(secs)).strftime(timeFormat)


def formatTimedelta(td):
    """Format timedelta to String
    """
    if not isinstance(td, timedelta):
        return ""
    days, seconds = td.days, td.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return "%d:%s:%s" % (hours, str(minutes).zfill(2), str(seconds).zfill(2))


def parse_time(block_time):
    """Take a string representation of time from the blockchain, and parse it
       into datetime object.
    """
    utc = pytz.timezone('UTC')
    return utc.localize(datetime.strptime(block_time, timeFormat))


def assets_from_string(text):
    """Correctly split a string containing an asset pair.

    Splits the string into two assets with the separator being on of the
    following: ``:``, ``/``, or ``-``.
    """
    return re.split(r'[\-:/]', text)


def sanitize_permlink(permlink):
    permlink = permlink.strip()
    permlink = re.sub("_|\s|\.", "-", permlink)
    permlink = re.sub("[^\w-]", "", permlink)
    permlink = re.sub("[^a-zA-Z0-9-]", "", permlink)
    permlink = permlink.lower()
    return permlink


def derive_permlink(title, parent_permlink=None, parent_author=None):
    permlink = ""

    if parent_permlink and parent_author:
        permlink += "re-"
        permlink += parent_author.replace("@", "")
        permlink += "-"
        permlink += parent_permlink
        permlink += "-" + formatTime(time.time()) + "z"
    elif parent_permlink:
        permlink += "re-"
        permlink += parent_permlink
        permlink += "-" + formatTime(time.time()) + "z"
    else:
        permlink += title

    return sanitize_permlink(permlink)


def resolve_authorperm(identifier):
    """Correctly split a string containing an authorperm.

    Splits the string into author and permlink with the
    following separator: ``/``.
    """
    match = re.match("@?([\w\-\.]*)/([\w\-]*)", identifier)
    if hasattr(match, "group"):
        return match.group(1), match.group(2)
    match = re.match("([\w\-\.]+[^#?\s]+)/@?([\w\-\.]*)/([\w\-]*)", identifier)
    if not hasattr(match, "group"):
        raise ValueError("Invalid identifier")
    return match.group(2), match.group(3)


def construct_authorperm(*args):
    """ Create a post identifier from comment/post object or arguments.
    Examples:

        .. code-block:: python

            >>> from beem.utils import construct_authorperm
            >>> print(construct_authorperm('username', 'permlink'))
            @username/permlink
            >>> print(construct_authorperm({'author': 'username', 'permlink': 'permlink'}))
            @username/permlink

    """
    username_prefix = '@'
    if len(args) == 1:
        op = args[0]
        author, permlink = op['author'], op['permlink']
    elif len(args) == 2:
        author, permlink = args
    else:
        raise ValueError(
            'construct_identifier() received unparsable arguments')

    fields = dict(prefix=username_prefix, author=author, permlink=permlink)
    return "{prefix}{author}/{permlink}".format(**fields)


def resolve_root_identifier(url):
    m = re.match("/([^/]*)/@([^/]*)/([^#]*).*", url)
    if not m:
        return "", ""
    else:
        category = m.group(1)
        author = m.group(2)
        permlink = m.group(3)
        return construct_authorperm(author, permlink), category


def resolve_authorpermvoter(identifier):
    """Correctly split a string containing an authorpermvoter.

    Splits the string into author and permlink with the
    following separator: ``/`` and ``|``.
    """
    pos = identifier.find("|")
    if pos < 0:
        raise ValueError("Invalid identifier")
    [author, permlink] = resolve_authorperm(identifier[:pos])
    return author, permlink, identifier[pos + 1:]


def construct_authorpermvoter(*args):
    """ Create a vote identifier from vote object or arguments.
    Examples:

        .. code-block:: python

            >>> from beem.utils import construct_authorpermvoter
            >>> print(construct_authorpermvoter('username', 'permlink', 'voter'))
            @username/permlink|voter
            >>> print(construct_authorpermvoter({'author': 'username', 'permlink': 'permlink', 'voter': 'voter'}))
            @username/permlink|voter

    """
    username_prefix = '@'
    if len(args) == 1:
        op = args[0]
        if "authorperm" in op:
            authorperm, voter = op['authorperm'], op['voter']
            [author, permlink] = resolve_authorperm(authorperm)
        else:
            author, permlink, voter = op['author'], op['permlink'], op['voter']
    elif len(args) == 2:
        authorperm, voter = args
        [author, permlink] = resolve_authorperm(authorperm)
    elif len(args) == 3:
        author, permlink, voter = args
    else:
        raise ValueError(
            'construct_identifier() received unparsable arguments')

    fields = dict(prefix=username_prefix, author=author, permlink=permlink, voter=voter)
    return "{prefix}{author}/{permlink}|{voter}".format(**fields)


def reputation_to_score(rep):
    """Converts the account reputation value into the reputation score"""
    if isinstance(rep, str):
        rep = int(rep)
    if rep == 0:
        return 25.
    score = max([math.log10(abs(rep)) - 9, 0])
    if rep < 0:
        score *= -1
    score = (score * 9.) + 25.
    return score


def remove_from_dict(obj, keys=list(), keep_keys=True):
    """ Prune a class or dictionary of all but keys (keep_keys=True).
        Prune a class or dictionary of specified keys.(keep_keys=False).
    """
    if type(obj) == dict:
        items = list(obj.items())
    else:
        items = list(obj.__dict__.items())
    if keep_keys:
        return {k: v for k, v in items if k in keys}
    else:
        return {k: v for k, v in items if k not in keys}


def make_patch(a, b, n=3):
    # _no_eol = '\n' + "\ No newline at end of file" + '\n'
    _no_eol = '\n'
    diffs = difflib.unified_diff(a.splitlines(True), b.splitlines(True), n=n)
    try:
        _, _ = next(diffs), next(diffs)
        del _
    except StopIteration:
        pass
    return ''.join([d if d[-1] == '\n' else d + _no_eol for d in diffs])


def findall_patch_hunks(body=None):
    return RE_HUNK_HEADER.findall(body)


def get_node_list(appbase=False, testing=False):
    """Returns node list"""
    if appbase:
        node_list = ["https://api.steemit.com", "wss://appbasetest.timcliff.com", "https://api.steem.house"]
        if testing:
            node_list = ["https://api.steemitdev.com", "https://api.steemitstage.com"] + node_list
        return node_list
    else:
        return ["wss://steemd.privex.io", "wss://steemd.pevo.science", "wss://rpc.buildteam.io", "wss://rpc.steemliberator.com", "wss://gtg.steem.house:8090",
                "wss://rpc.steemviz.com", "wss://seed.bitcoiner.me", "wss://steemd.steemgigs.org", "wss://steemd.minnowsupportproject.org", "https://rpc.buildteam.io",
                "https://steemd.minnowsupportproject.org", "https://steemd.pevo.science", "https://rpc.steemviz.com", "https://seed.bitcoiner.me",
                "https://rpc.steemliberator.com", "https://steemd.privex.io", "https://gtg.steem.house:8090",
                "https://rpc.curiesteem.com", "https://steemd.steemgigs.org"]
