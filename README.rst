steempy - Unofficial Python 3 Library for Steem
=====================================

!!!NOT WORKING AT THE MOMENT - DO NOT USE!!!

steemi is an unofficial python 3 library for steem, which is created new from scratch from https://github.com/xeroc/python-bitshares.

.. image:: https://travis-ci.org/holgern/steempy.svg?branch=master
    :target: https://travis-ci.org/holgern/steempy

.. image:: https://ci.appveyor.com/api/projects/status/3mnnhx4vo240mb4g?svg=true
    :target: https://ci.appveyor.com/project/holger80/steempy

.. image:: https://codecov.io/gh/holgern/steempy/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/holgern/steempy

Installation
============
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
    
You can install py-scrypt from this repository if you want the latest
but possibly non-compiling version::

    git clone https://github.com/holgern/steempy.git
    cd steempy
    python setup.py build
    
    python setup.py install --user

Run tests after install::

    python setup.py test

Changelog
=========
0.18.1
-----

* Replaced all BitShares by Steem
* Flake8 fixed
* Unit tests are working
* renamed to steempy