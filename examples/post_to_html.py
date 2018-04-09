#!/usr/bin/env python

import argparse
import sys
import jinja2
import markdown
import pytz
from datetime import datetime, timedelta
from beem.blockchain import Blockchain
from beem.comment import Comment
from beem.utils import formatTimeString, formatTimedelta, remove_from_dict, reputation_to_score, parse_time
import logging
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <link href="http://netdna.bootstrapcdn.com/twitter-bootstrap/2.3.0/css/bootstrap-combined.min.css" rel="stylesheet">
    <style>
        body {
            font-family: sans-serif;
        }
        code, pre {
            font-family: monospace;
        }
        h1 code,
        h2 code,
        h3 code,
        h4 code,
        h5 code,
        h6 code {
            font-size: inherit;
        }
    </style>
    <title>{{title}}</title>
</head>
<body>
<div class="container">
{{content}}
</div>
</body>
</html>
"""


def parse_args(args=None):
    d = 'Make a complete, styled HTML document from a Markdown file.'
    parser = argparse.ArgumentParser(description=d)
    parser.add_argument('authorperm', type=str, nargs='?',
                        default=sys.stdin,
                        help='Authorperm to read. Defaults to stdin.')
    parser.add_argument('-o', '--out', type=argparse.FileType('w'),
                        default=sys.stdout,
                        help='Output file name. Defaults to stdout.')
    return parser.parse_args(args)


def main(args=None):
    args = parse_args(args)
    authorperm = args.authorperm
    comment = Comment(authorperm)
    title = comment["title"]
    author = comment["author"]
    rep = reputation_to_score(comment["author_reputation"])
    time_created = comment["created"]
    utc = pytz.timezone('UTC')
    td_created = utc.localize(datetime.utcnow()) - time_created
    md = '# ' + title + '\n' + author
    md += '(%.2f) ' % (rep)
    md += formatTimedelta(td_created) + '\n\n'
    md += comment["body"]
    extensions = ['extra', 'smarty']
    html = markdown.markdown(md, extensions=extensions, output_format='html5')
    doc = jinja2.Template(TEMPLATE).render(content=html, title=title)
    args.out.write(doc)


if __name__ == '__main__':
    sys.exit(main())
