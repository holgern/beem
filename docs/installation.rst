Installation
============
The minimal working python version is 3.5.x

beem can be installed parallel to python-steem.

For Debian and Ubuntu, please ensure that the following packages are installed:
        
.. code:: bash

    sudo apt-get install build-essential libssl-dev python-dev curl

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

Install pip (https://pip.pypa.io/en/stable/installing/):

.. code:: bash

   curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
   
   python get-pip.py

Signing and Verify can be fasten (200 %) by installing cryptography. Install cryptography with pip:

.. code:: bash

    pip install -U cryptography
    
Install beem with pip:

.. code:: bash

    pip install -U beem

Sometimes this does not work. Please try::

    pip3 install -U beem

or::

    python -m pip install beem

Manual installation
-------------------
    
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

Enable Logging
--------------

Add the following for enabling logging in your python script::

    import logging
    log = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

When you want to see only critical errors, replace the last line by::

    logging.basicConfig(level=logging.CRITICAL)
