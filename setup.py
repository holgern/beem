#!/usr/bin/env python3

from setuptools import setup

# Work around mbcs bug in distutils.
# http://bugs.python.org/issue10945
import codecs
try:
    codecs.lookup('mbcs')
except LookupError:
    ascii = codecs.lookup('ascii')
    codecs.register(lambda name, enc=ascii: {True: enc}.get(name == 'mbcs'))

VERSION = '0.18.1'

setup(
    name='steemi',
    version=VERSION,
    description='Unofficial Python library for STEEM',
    long_description=open('README.rst').read(),
    download_url='https://github.com/holgern/pySteemi/tarball/' + VERSION,
    author='Holger Nahrstaedt',
    author_email='holger@nahrstaedt.de',
    maintainer='Holger Nahrstaedt',
    maintainer_email='holger@nahrstaedt.de',
    url='http://www.github.com/holgern/pySteemi',
    keywords=['steem', 'library', 'api', 'rpc'],
    packages=[
        "steem",
        "steemapi",
        "steembase"
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Topic :: Office/Business :: Financial',
    ],
    install_requires=[
        "graphenelib>=0.5.9",
        "websockets",
        "appdirs",
        "Events",
        "scrypt",
        "pycryptodomex",  # for AES, installed through graphenelib already
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    include_package_data=True,
)
