Installation
============
Warning: install beem will install pycrytodome which is not compatible to pycryto which is need for python-steem.
At the moment, either beem or steem can be install at one maschine!

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

Manual installation:
--------------------

::

    $ git clone https://github.com/holgern/beem/
    $ cd beem
    $ python setup.py build
    $ python setup.py install --user

Upgrade
-------

::

   $ pip install --user --upgrade
