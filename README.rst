Electrum-Scribe - Lightweight Scribe client
=====================================

::

  Licence: MIT Licence
  Author: Thomas Voegtlin
  Port Maintainer: WakiyamaP (Electrum-Scribe)
  Language: Python (>= 3.6)
  Homepage: https://scribe.network/


.. image:: https://travis-ci.org/wakiyamap/electrum-scribe.svg?branch=master
    :target: https://travis-ci.org/wakiyamap/electrum-scribe
    :alt: Build Status
.. image:: https://coveralls.io/repos/github/wakiyamap/electrum-scribe/badge.svg?branch=master
    :target: https://coveralls.io/github/wakiyamap/electrum-scribe?branch=master
    :alt: Test coverage statistics





Getting started
===============

Electrum-Scribe is a pure python application. If you want to use the
Qt interface, install the Qt dependencies::

    sudo apt-get install python3-pyqt5

If you downloaded the official package (tar.gz), you can run

Electrum-Scribe from its root directory without installing it on your
system; all the python dependencies are included in the 'packages'
directory. To run Electrum-Scribe from its root directory, just do::

    ./run_electrum

You can also install Electrum-Scribe on your system, by running this command::

    sudo apt-get install python3-setuptools
    python3 -m pip install .[fast]

This will download and install the Python dependencies used by
Electrum-Scribe instead of using the 'packages' directory.
The 'fast' extra contains some optional dependencies that we think
are often useful but they are not strictly needed.

If you cloned the git repository, you need to compile extra files
before you can run Electrum-Scribe. Read the next section, "Development
Version".



Development version
===================

Check out the code from GitHub::

    git clone https://github.com/wakiyamap/electrum-scribe.git
    cd electrum-scribe
    git submodule update --init

Need lyra2rev2_hash::

    pip3 install lyra2re2-hash

Run install (this should install dependencies)::

    python3 -m pip install .[fast]

Compile the protobuf description file::

    sudo apt-get install protobuf-compiler
    protoc --proto_path=electrum_scribe --python_out=electrum_scribe electrum_scribe/paymentrequest.proto

Create translations (optional)::

    sudo apt-get install python-requests gettext
    ./contrib/pull_locale




Creating Binaries
=================

Linux (tarball)
---------------

See :code:`contrib/build-linux/README.md`.


Linux (AppImage)
----------------

See :code:`contrib/build-linux/appimage/README.md`.


Mac OS X / macOS
----------------

See :code:`contrib/osx/README.md`.


Windows
-------

See :code:`contrib/build-wine/README.md`.


Android
-------

See :code:`electrum_scribe/gui/kivy/Readme.md`.
