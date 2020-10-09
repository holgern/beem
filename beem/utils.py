# -*- coding: utf-8 -*-
import re
import json
import time as timenow
import math
from datetime import datetime, tzinfo, timedelta, date, time
import pytz
import difflib
import yaml

timeFormat = "%Y-%m-%dT%H:%M:%S"
# https://github.com/matiasb/python-unidiff/blob/master/unidiff/constants.py#L37
# @@ (source offset, length) (target offset, length) @@ (section header)
RE_HUNK_HEADER = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))?\ @@[ ]?(.*)$", flags=re.MULTILINE
)


def formatTime(t):
    """ Properly Format Time for permlinks
    """
    if isinstance(t, float):
        return datetime.utcfromtimestamp(t).strftime("%Y%m%dt%H%M%S%Z")
    if isinstance(t, (datetime, date, time)):
        return t.strftime("%Y%m%dt%H%M%S%Z")


def addTzInfo(t, timezone="UTC"):
    """Returns a datetime object with tzinfo added"""
    if t and isinstance(t, (datetime, date, time)) and t.tzinfo is None:
        utc = pytz.timezone(timezone)
        t = utc.localize(t)
    return t


def formatTimeString(t):
    """ Properly Format Time for permlinks
    """
    if isinstance(t, (datetime, date, time)):
        return t.strftime(timeFormat)
    return addTzInfo(datetime.strptime(t, timeFormat))


def formatToTimeStamp(t):
    """ Returns a timestamp integer

        :param datetime t: datetime object
        :return: Timestamp as integer
    """
    if isinstance(t, (datetime, date, time)):
        t = addTzInfo(t)
    else:
        t = formatTimeString(t)
    epoch = addTzInfo(datetime(1970, 1, 1))
    return int((t - epoch).total_seconds())


def formatTimeFromNow(secs=0):
    """ Properly Format Time that is `x` seconds in the future

        :param int secs: Seconds to go in the future (`x>0`) or the
                         past (`x<0`)
        :return: Properly formated time for Graphene (`%Y-%m-%dT%H:%M:%S`)
        :rtype: str

    """
    return datetime.utcfromtimestamp(timenow.time() + int(secs)).strftime(timeFormat)


def formatTimedelta(td):
    """Format timedelta to String
    """
    if not isinstance(td, timedelta):
        return ""
    days, seconds = td.days, td.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return "%d:%s:%s" % (hours, str(minutes).zfill(2), str(seconds).zfill(2))


def parse_time(block_time):
    """Take a string representation of time from the blockchain, and parse it
       into datetime object.
    """
    utc = pytz.timezone("UTC")
    return utc.localize(datetime.strptime(block_time, timeFormat))


def assets_from_string(text):
    """Correctly split a string containing an asset pair.

    Splits the string into two assets with the separator being on of the
    following: ``:``, ``/``, or ``-``.
    """
    return re.split(r"[\-:\/]", text)


def sanitize_permlink(permlink):
    permlink = permlink.strip()
    permlink = re.sub(r"_|\s|\.", "-", permlink)
    permlink = re.sub(r"[^\w-]", "", permlink)
    permlink = re.sub(r"[^a-zA-Z0-9-]", "", permlink)
    permlink = permlink.lower()
    return permlink


def derive_permlink(title, parent_permlink=None, parent_author=None,
                    max_permlink_length=256, with_suffix=True):
    """Derive a permlink from a comment title (for root level
    comments) or the parent permlink and optionally the parent
    author (for replies).

    """
    suffix = "-" + formatTime(datetime.utcnow()) + "z"
    if parent_permlink and parent_author:
        prefix = "re-" + sanitize_permlink(parent_author) + "-"
        if with_suffix:
            rem_chars = max_permlink_length - len(suffix) - len(prefix)
        else:
            rem_chars = max_permlink_length - len(prefix)
        body = sanitize_permlink(parent_permlink)[:rem_chars]
        if with_suffix:
            return prefix + body + suffix
        else:
            return prefix + body
    elif parent_permlink:
        prefix = "re-"
        if with_suffix:
            rem_chars = max_permlink_length - len(suffix) - len(prefix)
        else:
            rem_chars = max_permlink_length - len(prefix)
        body = sanitize_permlink(parent_permlink)[:rem_chars]
        if with_suffix:
            return prefix + body + suffix
        else:
            return prefix + body
    else:
        if with_suffix:
            rem_chars = max_permlink_length - len(suffix)
        else:
            rem_chars = max_permlink_length
        body = sanitize_permlink(title)[:rem_chars]
        if len(body) == 0:  # empty title or title consisted of only special chars
            return suffix[1:]  # use timestamp only, strip leading "-"
        if with_suffix:
            return body + suffix
        else:
            return body


def resolve_authorperm(identifier):
    """Correctly split a string containing an authorperm.

    Splits the string into author and permlink with the
    following separator: ``/``.

    Examples:

        .. code-block:: python

            >>> from beem.utils import resolve_authorperm
            >>> author, permlink = resolve_authorperm('https://d.tube/#!/v/pottlund/m5cqkd1a')
            >>> author, permlink = resolve_authorperm("https://steemit.com/witness-category/@gtg/24lfrm-gtg-witness-log")
            >>> author, permlink = resolve_authorperm("@gtg/24lfrm-gtg-witness-log")
            >>> author, permlink = resolve_authorperm("https://busy.org/@gtg/24lfrm-gtg-witness-log")

    """
    # without any http(s)
    match = re.match(r"@?([\w\-\.]*)/([\w\-]*)", identifier)
    if hasattr(match, "group"):
        return match.group(1), match.group(2)
    # dtube url
    match = re.match(r"([\w\-\.]+[^#?\s]+)/#!/v/?([\w\-\.]*)/([\w\-]*)", identifier)
    if hasattr(match, "group"):
        return match.group(2), match.group(3)
    # url
    match = re.match(r"([\w\-\.]+[^#?\s]+)/@?([\w\-\.]*)/([\w\-]*)", identifier)
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
    username_prefix = "@"
    if len(args) == 1:
        op = args[0]
        author, permlink = op["author"], op["permlink"]
    elif len(args) == 2:
        author, permlink = args
    else:
        raise ValueError("construct_identifier() received unparsable arguments")

    fields = dict(prefix=username_prefix, author=author, permlink=permlink)
    return "{prefix}{author}/{permlink}".format(**fields)


def resolve_root_identifier(url):
    m = re.match(r"/([^/]*)/@([^/]*)/([^#]*).*", url)
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
    return author, permlink, identifier[pos + 1 :]


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
    username_prefix = "@"
    if len(args) == 1:
        op = args[0]
        if "authorperm" in op:
            authorperm, voter = op["authorperm"], op["voter"]
            [author, permlink] = resolve_authorperm(authorperm)
        else:
            author, permlink, voter = op["author"], op["permlink"], op["voter"]
    elif len(args) == 2:
        authorperm, voter = args
        [author, permlink] = resolve_authorperm(authorperm)
    elif len(args) == 3:
        author, permlink, voter = args
    else:
        raise ValueError("construct_identifier() received unparsable arguments")

    fields = dict(prefix=username_prefix, author=author, permlink=permlink, voter=voter)
    return "{prefix}{author}/{permlink}|{voter}".format(**fields)


def reputation_to_score(rep):
    """Converts the account reputation value into the reputation score"""
    if isinstance(rep, str):
        rep = int(rep)
    if rep == 0:
        return 25.0
    score = max([math.log10(abs(rep)) - 9, 0])
    if rep < 0:
        score *= -1
    score = (score * 9.0) + 25.0
    return score


def remove_from_dict(obj, keys=list(), keep_keys=True):
    """ Prune a class or dictionary of all but keys (keep_keys=True).
        Prune a class or dictionary of specified keys.(keep_keys=False).
    """
    if type(obj) == dict:
        items = list(obj.items())
    elif isinstance(obj, dict):
        items = list(obj.items())
    else:
        items = list(obj.__dict__.items())
    if keep_keys:
        return {k: v for k, v in items if k in keys}
    else:
        return {k: v for k, v in items if k not in keys}


def make_patch(a, b, n=3):
    # _no_eol = '\n' + "\ No newline at end of file" + '\n'
    _no_eol = "\n"
    diffs = difflib.unified_diff(a.splitlines(True), b.splitlines(True), n=n)
    try:
        _, _ = next(diffs), next(diffs)
        del _
    except StopIteration:
        pass
    return "".join([d if d[-1] == "\n" else d + _no_eol for d in diffs])


def findall_patch_hunks(body=None):
    return RE_HUNK_HEADER.findall(body)


def derive_beneficiaries(beneficiaries):
    beneficiaries_list = []
    beneficiaries_accounts = []
    beneficiaries_sum = 0
    if not isinstance(beneficiaries, list):
        beneficiaries = beneficiaries.split(",")

    for w in beneficiaries:
        account_name = w.strip().split(":")[0]
        if account_name[0] == "@":
            account_name = account_name[1:]
        if account_name in beneficiaries_accounts:
            continue
        if w.find(":") == -1:
            percentage = -1
        else:
            percentage = w.strip().split(":")[1]
            if "%" in percentage:
                percentage = percentage.strip().split("%")[0].strip()
            percentage = float(percentage)
            beneficiaries_sum += percentage
        beneficiaries_list.append(
            {"account": account_name, "weight": int(percentage * 100)}
        )
        beneficiaries_accounts.append(account_name)

    missing = 0
    for bene in beneficiaries_list:
        if bene["weight"] < 0:
            missing += 1
    index = 0
    for bene in beneficiaries_list:
        if bene["weight"] < 0:
            beneficiaries_list[index]["weight"] = int(
                (int(100 * 100) - int(beneficiaries_sum * 100)) / missing
            )
        index += 1
    sorted_beneficiaries = sorted(
        beneficiaries_list, key=lambda beneficiaries_list: beneficiaries_list["account"]
    )
    return sorted_beneficiaries


def derive_tags(tags):
    tags_list = []
    if len(tags.split(",")) > 1:
        for tag in tags.split(","):
            tags_list.append(tag.strip())
    elif len(tags.split(" ")) > 1:
        for tag in tags.split(" "):
            tags_list.append(tag.strip())
    elif len(tags) > 0:
        tags_list.append(tags.strip())
    return tags_list


def seperate_yaml_dict_from_body(content):
    parameter = {}
    body = ""
    if len(content.split("---\n")) > 1:
        body = content[content.find("---\n", 1) + 4 :]
        yaml_content = content[content.find("---\n") + 4 : content.find("---\n", 1)]
        parameter = yaml.load(yaml_content, Loader=yaml.FullLoader)
        if not isinstance(parameter, dict):
            parameter = yaml.load(yaml_content.replace(":", ": ").replace("  ", " "), Loader=yaml.FullLoader)
    else:
        body = content
    return body, parameter

    
def load_dirty_json(dirty_json):
    regex_replace = [(r"([ \{,:\[])(u)?'([^']+)'", r'\1"\3"'), (r" False([, \}\]])", r' false\1'), (r" True([, \}\]])", r' true\1')]
    for r, s in regex_replace:
        dirty_json = re.sub(r, s, dirty_json)
    clean_json = json.loads(dirty_json)
    return clean_json    
