beem - Unofficial Python Library for HIVE and STEEM
===================================================

beem is an unofficial python library for steem and HIVE, which is created new from scratch from `python-bitshares`_
The library name is derived from a beam machine, similar to the analogy between steem and steam. beem includes `python-graphenelib`_.

.. image:: https://img.shields.io/pypi/v/beem.svg
    :target: https://pypi.python.org/pypi/beem/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/pyversions/beem.svg
    :target: https://pypi.python.org/pypi/beem/
    :alt: Python Versions


.. image:: https://anaconda.org/conda-forge/beem/badges/version.svg
    :target: https://anaconda.org/conda-forge/beem


.. image:: https://anaconda.org/conda-forge/beem/badges/downloads.svg
    :target: https://anaconda.org/conda-forge/beem


Current build status
--------------------

.. image:: https://travis-ci.org/holgern/beem.svg?branch=master
    :target: https://travis-ci.org/holgern/beem

.. image:: https://ci.appveyor.com/api/projects/status/ig8oqp8bt2fmr09a?svg=true
    :target: https://ci.appveyor.com/project/holger80/beem

.. image:: https://circleci.com/gh/holgern/beem.svg?style=svg
    :target: https://circleci.com/gh/holgern/beem

.. image:: https://readthedocs.org/projects/beem/badge/?version=latest
  :target: http://beem.readthedocs.org/en/latest/?badge=latest

.. image:: https://api.codacy.com/project/badge/Grade/e5476faf97df4c658697b8e7a7efebd7
    :target: https://www.codacy.com/app/holgern/beem?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=holgern/beem&amp;utm_campaign=Badge_Grade

.. image:: https://pyup.io/repos/github/holgern/beem/shield.svg
     :target: https://pyup.io/repos/github/holgern/beem/
     :alt: Updates

.. image:: https://api.codeclimate.com/v1/badges/e7bdb5b4aa7ab160a780/test_coverage
   :target: https://codeclimate.com/github/holgern/beem/test_coverage
   :alt: Test Coverage

Support & Documentation
=======================
You may find help in the  `beem-discord-channel`_. The discord channel can also be used to discuss things about beem.

A complete library documentation is available at  `beem.readthedocs.io`_.

About beem
==========

* High unit test coverage
* Support for websocket nodes
* Native support for new Appbase calls
* Node error handling and automatic node switching
* Usage of pycryptodomex instead of the outdated pycrypto
* Complete documentation of beempy and all classes including all functions
* hivesigner/steemconnect integration
* Works on read-only systems
* Own BlockchainObject class with cache
* Contains all broadcast operations
* Estimation of virtual account operation index from date or block number
* the command line tool beempy uses click and has more commands
* SteemNodeRPC can be used to execute even not implemented RPC-Calls
* More complete implemention

Installation
============
The minimal working python version is 2.7.x. or 3.5.x

beem can be installed parallel to python-steem.

For Debian and Ubuntu, please ensure that the following packages are installed:

.. code:: bash

    sudo apt-get install build-essential libssl-dev python-dev

For Fedora and RHEL-derivatives, please ensure that the following packages are installed:

.. code:: bash

    sudo yum install gcc openssl-devel python-devel

For OSX, please do the following::

    brew install openssl
    export CFLAGS="-I$(brew --prefix openssl)/include $CFLAGS"
    export LDFLAGS="-L$(brew --prefix openssl)/lib $LDFLAGS"

For Termux on Android, please install the following packages:

.. code:: bash

    pkg install clang openssl python

Signing and Verify can be fasten (200 %) by installing cryptography:

.. code:: bash

    pip install -U cryptography

or:

.. code:: bash

    pip install -U secp256k1prp

Install or update beem by pip::

    pip install -U beem

You can install beem from this repository if you want the latest
but possibly non-compiling version::

    git clone https://github.com/holgern/beem.git
    cd beem
    python setup.py build

    python setup.py install --user

Run tests after install::

    pytest


Installing beem with conda-forge
--------------------------------

Installing beem from the conda-forge channel can be achieved by adding conda-forge to your channels with::

    conda config --add channels conda-forge

Once the conda-forge channel has been enabled, beem can be installed with::

    conda install beem

Signing and Verify can be fasten (200 %) by installing cryptography::

    conda install cryptography

beem can be updated by::

    conda update beem

CLI tool beempy
---------------
A command line tool is available. The help output shows the available commands:

    beempy --help

Stand alone version of CLI tool beempy
--------------------------------------
With the help of pyinstaller, a stand alone version of beempy was created for Windows, OSX and linux.
Each version has just to be unpacked and can be used in any terminal. The packed directories
can be found under release. Each release has a hash sum, which is created directly in the build-server
before transmitting the packed file. Please check the hash-sum after downloading.

Changelog
=========
Can be found in CHANGELOG.rst.

License
=======
This library is licensed under the MIT License.

Acknowledgements
================
`python-bitshares`_ and `python-graphenelib`_ were created by Fabian Schuh (xeroc).


.. _python-graphenelib: https://github.com/xeroc/python-graphenelib
.. _python-bitshares: https://github.com/xeroc/python-bitshares
.. _Python: http://python.org
.. _Anaconda: https://www.continuum.io
.. _beem.readthedocs.io: http://beem.readthedocs.io/en/latest/
.. _beem-discord-channel: https://discord.gg/4HM592V
