.. vim: display+=lastline linebreak
.. include:: ../links.rst

Installation
============

This document describes:

  - How to get PIDA
  - How to meet the requirements and dependencies
  - How to install PIDA

Distribution packages
---------------------

Though there is still a long way before PIDA can be considered mature, it is already packaged by several Linux and BSD(FIXME?) distributions.  Use the guidelines of your distribution to install or remove PIDA from your system.  The following table outlines the distributions known to provide PIDA and the version they include.


============== ===================== ============
Distribution   Distribution version  PIDA version
============== ===================== ============
Debian         Etch (stable)         0.3.1
Debian         Lenny (testing)       0.5.1
Debian         Sid (unstable)        0.5.1
Gentoo                               0.5.1
Fedora         10                    0.5.1
Ubuntu         Breezy Badger         0.2.2
Ubuntu         Dapper Drake          0.2.2
Ubuntu         Edgy Eft              0.3.1
Ubuntu         Feisty Fawn           0.3.1
Ubuntu         Gutsy Gibbon          0.4.4
Ubuntu         Hardy Heron           0.5.1
Ubuntu         Intrepid Ibex         0.5.1-5
============== ===================== ============

.. note:: There are chances that the version packaged is a bit outdated.  Please consider trying to install the most recent version before reporting a bug.  You can either compile pida from sources or try to use a package prepared for a more recent version of your distribution.

Dependencies
------------

Because of the nature of PIDA there are a number of tools that may optionally be used; they are not absolutely required.  The list of requirements is therefore split into mandatory and optional dependencies.  

Mandatory Dependencies
~~~~~~~~~~~~~~~~~~~~~~

**Python**
  Python is the programming language PIDA is written in.  At the time of this writing, PIDA works on version 2.5.  Python is available from the `Python Web Site`_.  Most Linux Distributions come with Python pre-installed.

**PyGTK**
  PyGTK includes the Python bindings for the GTK toolkit.  Note that you will also need to have GTK installed for them to work.  These are available from the `PyGTK Web Site`_ and the `GTK Web Site`_.  They have likely been packaged for your Linux distribution.

**Kiwi**
  Kiwi is a helper library for PyGTK. It was decided a while ago that there should not be a duplication in effort in creating common widgets and patterns withing PyGTK programs.  For this reason common things exist in Kiwi, and PIDA developers contribute fixes back upstream to Kiwi. Kiwi is available in the contrib directory of the source code. It is recommended to use this version if at all possible.  It contains no changes from the original, but it is ensured to have all the latest fixes.

**VTE**
  VTE is a GTK terminal widget that is used by gnome-terminal.  PIDA uses this for many things, and since it is in most distributions that Gnome is in, we have made it an absolute requirement.

**gazpacho**
  gazpacho is a gtk ui designer, it is needed for some glade-extensions, 
  we hope to phase it out in a future release.

In the Ubuntu and Debian distributions, you should install the mandatory dependencies.  This is only necessary if you do not use the distribution version::

  sudo apt-get install gvim python-gnome2 python-gnome2-extras \
  python-gtk2 python-vte python-kiwi python-setuptools python-glade2 librsvg2-common gazpacho

Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~

The following requirements are necessary *only* if you intend to build PIDA from source.  Thus, if you are using your distribution's version of PIDA, these are not necessary.

**Python development headers**
  These are usually available in your distribution as python-dev.  They are the headers required for building python extensions.

**PyGTK development headers**
  These are required to build the external moo_stub extension; these are usually available in your distribution as pygtk-dev or pygtk-devel packages.

In Ubuntu and Debian, run the following::

  sudo apt-get install python-dev python-gtk2-dev

Latest Stable Version
---------------------

The latest stable release is available on our Downloads_ page.

In order to install the stable version of PIDA, make sure you have installed all the dependencies.  This includes the compilation dependencies.  Extract the downloaded tarball to a working directory::

  tar xzvvf PIDA-0.5.1.tar.gz /home/your_user_name/pida

Cutting Edge
------------

PIDA is still not considered final by its authors.  The most recent version is in our Mercurial repository.  

Pick somewhere to put all of it, for example: ``/home/user/src``. In order to obtain the latest developer sources using Mercurial_, run the following::

  hg clone http://www.bitbucket.org/aafshar/pida-main/ pida

Now update the external software::

  cd pida/tools/
  ./update_externals.sh

Building PIDA
-------------

The build step is necessary even when running from source so as to ensure that the extensions are built::

  python setup.py build

or to be more precise::

  python setup.py build_ext -i

.. .. note:: 

..  Debian Users
..    Due to the location of headers on Debian, users must first:
..    export PKG_CONFIG_PATH=/usr/lib/pkgconfig/python2

Installation from Source
------------------------

.. note::
  Installation is the recommended method of running PIDA for users.
  Running from source should be reserved for people 
  intending to develop pida itself or a plugion.

To install PIDA, the following command should be run as root (or using sudo) if you are installing to a global location.  This command is run from the PIDA directory either created from the Mercurial checkout, or the stable tarball::

    python setup.py install

You also need to install anyvc and rope::

    python tools/externals/src/anyvc/setup.py install
    python tools/externals/src/rope/setup.py install

Run from source
---------------

It is necessary to invoke `python setup.py build_ext -i` 
in order to get a c-written ui extension compiled + placed in the source path.

.. note::

    Running from source is generally reserved for developers of PIDA
    or those people who really know what they are doing.
    It is very useful to be able to make a change and test it immediately.
    It is not recommended to use this as a general execution method.

To run PIDA directly from the source, run::

    ./run-pida.py

.. note::

   `run-pida.py` will add the plugins in the checkout to the plugin-search-path,
   the installed executables wont do that.

MS Windows
----------

Some pointers on how to install PIDA dependencies 
and perform a `Windows Installation`_ can be found on the Trac_.

Due to lack of developers on Win32 we can't maintain official support.


Mac OS X
--------

No official support yet,
but planned support for pida with gtk based embedded editors (medit and gtksourceview).
