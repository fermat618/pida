.. vim: display+=lastline linebreak
.. include:: ../links.rst

Installation
============

This document describes:

  - How to get PIDA
  - How to meet the requirements and dependencies
  - How to install PIDA
  - How to run PIDA without installing it

Requirements
------------

Because of the nature of PIDA there are a number of tools that may optionally be used; they are not absolutely required. The list of requirements is therefore split into absolute and relative requirements.

Absolute Requirements
~~~~~~~~~~~~~~~~~~~~~

**Python**
  Python is the programming language PIDA is written in.  PIDA requires any version of Python greater than or equal to 2.4.  Python is available from the `Python Web Site`_ or more likely packaged for your distribution.  Most desktop Linuxes come with Python preinstalled.

**PyGTK**
  PyGTK are the Python bindings for the GTK toolkit.  Note that you will also need to have GTK installed for them to work.  These are available from the `PyGTK Web Site`_ and the `GTK Web Site`_ or more likely packaged by your Linux distribution.

**Kiwi**
  Kiwi is a helper library for PyGTK. It was decided a while ago that there should not be a duplication in effort in creating common widgets and patterns withing PyGTK programs.  For this reason common things exist in Kiwi, and PIDA developers contribute fixes back upstream to Kiwi. Kiwi is available in the contrib directory of the source code. It is recommended to use this version if at all possible.  It contains no changes from the original, but it is ensured to have all the latest fixes.

**VTE**
  VTE is a GTK terminal widget that is used by gnome-terminal.  PIDA uses this for many things, and since it is in most distributions that Gnome is in, we have made it an absolute requirement.

Compilation Requirements
~~~~~~~~~~~~~~~~~~~~~~~~

Python development headers:
  These are usually available in your distribution as python-dev.  They are the headers required for building python extensions.

PyGTK development headers:
  These are required to build the external moo_stub extension, and are usually available in your distribution as pygtk-dev or pygtk-devel etc. packages.

Installation
------------

The latest stable release is available on our Downloads_ page.

PIDA is still not considered final by its authors.  The most recent version is in our Mercurial repository; milestones are available though that provide a snapshot of the development to the less adventurous.

In order to obtain the latest developer sources using Mercurial_ run the following using the terminal::

  hg clone http://www.bitbucket.org/aafshar/pida-main/

Compilation from sources
~~~~~~~~~~~~~~~~~~~~~~~~

.. note:: The source code comes with a standard Python installation method.

Build
+++++

The build step is necessary even when running from source so as to ensure that the extensions are built::

  python setup.py build

or to be more precise::

  python setup.py build_ext -i


.. note:: 

  Debian Users
    Due to the location of headers on Debian, users must first:
    export PKG_CONFIG_PATH=/usr/lib/pkgconfig/python2

Install
+++++++

Installation is the recommended method of running PIDA.  Running from source should be reserved for people who know what they are doing.

To install PIDA, run::

    python setup.py install

.. note::

    you may need to use sudo or equivalent to obtain superuser access if you are installing to a global location.

Run from source
+++++++++++++++

First copy the moo_stub.so (that was built in the build stage) from the build/ directory somewhere into PYTHONPATH or the working directory.  Then execute:

.. note::

    Running from source is generally reserved for developers of PIDA, or those people who really know what they are doing. It is very useful to be able to make a change and test it immediately. It is not recommended to use this as a general running method.

To run PIDA directly from the source, run::

    ./run-pida.py

.. note::

   This will handle your Python PATH, and will automatically link all the plugins available in the pida-plugins directory

Distribution packages
~~~~~~~~~~~~~~~~~~~~~

Though there is still a long way before PIDA can be considered mature, it is already packaged by several Linux and BSD(FIXME?) distributions.  Use the guidelines of your distribution to install or remove PIDA from your system.


============== ===================== ============
Known Distributions that provide PIDA
-------------------------------------------------
Distribution   Distribution version  PIDA version
============== ===================== ============
Debian         Etch (_stable_)       0.3.1
Debian         Lenny (_testing_)     0.5.1
Debian         Sid (_unstable_)      0.5.1
Gentoo                               0.5.1
Fedora         8                     0.5.1
Ubuntu         Breezy Badger         0.2.2
Ubuntu         Dapper Drake          0.2.2
Ubuntu         Edgy Eft              0.3.1
Ubuntu         Feisty Fawn           0.3.1
Ubuntu         Gutsy Gibbon          0.4.4
Ubuntu         Hardy Heron           0.5.1
============== ===================== ============

IMPORTANT: There are chances that the version packaged is a bit outdated.  Please consider trying to install the most recent version before reporting a bug.  You can either compile pida from sources or try to use a package prepared for a more recent version of your distribution.

MS Windows
~~~~~~~~~~
FIXME.

Some pointers on how to install PIDA dependencies can be found on the Wiki_.

Mac OS X
~~~~~~~~
FIXME.

