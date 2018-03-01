beem - Unofficial Python Library for Steem
===============================================

!!!Alpha-State, be carefull!!!

beem is an unofficial python library for steem, which is created new from scratch from `python-bitshares`_
The library name is derived from a beam maschine, similar to the analogy between steem and steam. beem includes `python-graphenelib`_.

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

.. image:: https://codecov.io/gh/holgern/beem/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/holgern/beem
  
.. image:: https://readthedocs.org/projects/beem/badge/?version=latest
  :target: http://beem.readthedocs.org/en/latest/?badge=latest

Installation
============
The minimal working python version is 2.7.x. or 3.4.x

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

    pkg install clang openssl-dev python-dev
    
Install beem by pip::

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

Installing beem from the conda-forge channel can be achieved by adding conda-forge to your channels with:

    conda config --add channels conda-forge
    
Once the conda-forge channel has been enabled, beem can be installed with:

    conda install beem

CLI tool bundled
----------------
I started to work on a CLI tool:

    beempy

Documentation
=============
Documentation is available at http://beem.readthedocs.io/en/latest/

Changelog
=========
0.19.8
------
* bug fixes
* CLI tool added
* beem added to conda-forge
* more unittests

0.19.7
------
* works on python 2.7
* can be installed besides steem-python
* graphenelib included
* unit tests added
* comment and account improved
* timezone added
* Delete_comment added

0.19.6
------
* Small bug-fix

0.19.5
------
* Market fixed
* Account, Comment, Discussion and Witness class improved
* Bug fixes

0.19.4
------
* New library name is now beem
* Upstream fixes from https://github.com/xeroc/python-bitshares
* Improved Docu

0.19.3
------
* Add Comment/Post
* Add Witness
* Several bugfixes
* Added all transactions that are supported from steem-python
* New library name planned: beem

0.19.2
------
* Notify and websocket fixed
* Several fixes

0.19.1
------
* Imported from https://github.com/xeroc/python-bitshares 
* Replaced all BitShares by Steem
* Flake8 fixed
* Unit tests are working
* renamed to beem
* Docs fixed
* Signing fixed
* pysteem: Account, Amount, Asset, Block, Blockchain, Instance, Memo, Message, Notify, Price, Steem, Transactionbuilder, Vote, Witness are working


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
