import re
import time
from datetime import datetime
import difflib
from .exceptions import ObjectNotInProposalBuffer

timeFormat = '%Y-%m-%dT%H:%M:%S'


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
    return datetime.strptime(t, timeFormat)


def formatTimeFromNow(secs=0):
    """ Properly Format Time that is `x` seconds in the future

        :param int secs: Seconds to go in the future (`x>0`) or the
                         past (`x<0`)
        :return: Properly formated time for Graphene (`%Y-%m-%dT%H:%M:%S`)
        :rtype: str

    """
    return datetime.utcfromtimestamp(
        time.time() + int(secs)).strftime(timeFormat)


def parse_time(block_time):
    """Take a string representation of time from the blockchain, and parse it
       into datetime object.
    """
    return datetime.strptime(block_time, timeFormat)


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
    if not hasattr(match, "group"):
        raise ValueError("Invalid identifier")
    return match.group(1), match.group(2)


def construct_authorperm(*args, username_prefix='@'):
    """ Create a post identifier from comment/post object or arguments.
    Examples:
        ::
            construct_authorperm('username', 'permlink')
            construct_authorperm({'author': 'username',
                'permlink': 'permlink'})
    """
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


def construct_authorpermvoter(*args, username_prefix='@'):
    """ Create a vote identifier from vote object or arguments.
    Examples:
        ::
            construct_authorpermvoter('username', 'permlink', 'voter')
            construct_authorpermvoter({'author': 'username',
                'permlink': 'permlink', 'voter': 'voter'})
    """
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


def test_proposal_in_buffer(buf, operation_name, id):
    from .transactionbuilder import ProposalBuilder
    from peerplaysbase.operationids import operations
    assert isinstance(buf, ProposalBuilder)

    operationid = operations.get(operation_name)
    _, _, j = id.split(".")

    ops = buf.list_operations()
    if (len(ops) <= int(j)):
        raise ObjectNotInProposalBuffer(
            "{} with id {} not found".format(
                operation_name,
                id
            )
        )
    op = ops[int(j)].json()
    if op[0] != operationid:
        raise ObjectNotInProposalBuffer(
            "{} with id {} not found".format(
                operation_name,
                id
            )
        )


def keep_in_dict(obj, allowed_keys=list()):
    """ Prune a class or dictionary of all but allowed keys.
    """
    if type(obj) == dict:
        items = obj.items()
    else:
        items = obj.__dict__.items()

    return {k: v for k, v in items if k in allowed_keys}


def remove_from_dict(obj, remove_keys=list()):
    """ Prune a class or dictionary of specified keys.
    """
    if type(obj) == dict:
        items = obj.items()
    else:
        items = obj.__dict__.items()

    return {k: v for k, v in items if k not in remove_keys}


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
