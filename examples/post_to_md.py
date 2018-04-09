#!/usr/bin/env python

import argparse
import sys
import pytz
import markdown
from datetime import datetime, timedelta
from beem.blockchain import Blockchain
from beem.comment import Comment
from beem.utils import formatTimeString, formatTimedelta, remove_from_dict, reputation_to_score, parse_time
import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def parse_args(args=None):
    d = 'Save post as markdown.'
    parser = argparse.ArgumentParser(description=d)
    parser.add_argument('authorperm', type=str, nargs='?',
                        default=sys.stdin,
                        help='Authorperm to read. Defaults to stdin.')
    parser.add_argument('-o', '--out', type=argparse.FileType('w'),
                        default=sys.stdout,
                        help='Output file name. Defaults to stdout.')
    return parser.parse_args(args)


def main(args=None):
    """pandoc -s test.md  --from markdown-blank_before_header-blank_before_blockquote+lists_without_preceding_blankline    -o test.pdf"""
    args = parse_args(args)
    authorperm = args.authorperm
    comment = Comment(authorperm)
    title = comment["title"]
    author = comment["author"]
    rep = reputation_to_score(comment["author_reputation"])
    time_created = comment["created"]
    if True:
        md = '% Title:\t ' + title + '\n'
        md += '% Author:\t' + author + '(%.2f) ' % (rep) + '\n'
        md += '% Date:\t' + time_created.strftime("%d.%m.%Y") + '\n'
        md += '% Comment:\n'
    else:
        md = '# ' + title + '\n'
        md += author + '(%.2f) ' % (rep) + ' ' + time_created.strftime("%d.%m.%Y") + '\n\n'
    md += comment["body"]

    args.out.write(md)


if __name__ == '__main__':
    sys.exit(main())
