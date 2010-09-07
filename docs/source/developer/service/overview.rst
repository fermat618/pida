
Service Overview
================

A service is comprised of a directory on the file system. This directory is a
Python package with data.

The structure of this directory is like so for a service named "myservice"::

    myservice/
        __init__.py
        myservice.py
        service.pida
        test_myservice.py
        data/
        glade/
        pixmaps/
        uidef/
            myservice.xml



PIDA Plugin Authoring Guide
----------------------------


PIDA plugins are very much identical to Services. Anything you can do in a
Service, you can also do in a Plugin. There are however a few minor
differences, based on the facts that:

1. Plugins can be loaded and unlaoded at runtime
2. Plugins can be published on the PIDA community and installed

PIDA uses Plugins for all non-core funcitonality, and we have been quite
strict about this, so that we can maintain a different release schedule for
the core, and individual plugins. Because of this, Plugins which you might
expect to find in a standard IDE or a standard Python IDE must be installed.
Fortunately this is a matter of a single click.

The service.pida file
---------------------

The service.pida file in Plugins is in the _ini_ format with themetadata under
the [plugin] tag. It contains metadata that is used by the
installer and by the community website. This metadata includes:

-------------  ---------------------------------------------------------------
Attribute       Description
-------------  ----------------------------------------------------------------
plugin *        Technical name of plugin (only `[a-z0-9_]` name)
name *          Long name of plugin
version *       Version of plugin
author *        Name of author <email>
require_pida *  Version of PIDA
category *      Category of plugins
depends         List of dependencies
lastupdate      Date of last update 	
website         Website of plugin
-------------  -----------------------------------------------------------------

`*` These fields are mandatory

An example service.pida file::
  [plugin]
  plugin = snippets
  name = Snippets
  author = Ali Afshar <aafshar@gmail.com>
  version = 0.1
  require_pida = 0.5
  depends = ""
  category = code
  description = Snippets: automatically enter repetitive text
