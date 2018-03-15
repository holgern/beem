..  -*- rst -*-

===============
beem benchmarks
===============

Benchmarking beem with Airspeed Velocity.


Usage
-----

Airspeed Velocity manages building and Python virtualenvs (or conda
environments) by itself, unless told otherwise.

First navigate to the benchmarks subfolder of the repository.

    cd benchmarks

To run all benchmarks once against the current build of beem::

    asv run --python=same --quick

To run all benchmarks more than once against the current build of beem::

    asv run --python=same

The following notation (tag followed by ^!) can be used to run only on a
specific tag or commit.  (In this case, a python version for the virtualenv
must be provided)

    asv run --python=3.6 --quick v0.19.16^!

To record the results use:

    asv publish

And to see the results via a web broweser, run:

    asv preview

More on how to use ``asv`` can be found in `ASV documentation`_
Command-line help is available as usual via ``asv --help`` and
``asv run --help``.

.. _ASV documentation: https://asv.readthedocs.io/
