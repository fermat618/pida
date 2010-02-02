==================
Service Components
==================

myservice.py
============

This is the file containing the Python code for the service. It is a Python
module and should contain an attribute ``Service``, which is the Class which
will be instantiated as the service.

The service class has a number of class attributes which describe its
behaviour. These behaviours are:

  - Configuration
  - Commands
  - Events
  - Features
  - Actions

Configuration
  This is the global configuration options for the service.

Commands
  Commands are the external interface for the service. They can be called by any other service, and this decoupling is cleaner than expecting, and calling an actual method on a service.

Events
  Events are an asynchronous call back for the service. Any other service can subscribe to an event explicitly, and by subscribing is notified when an event occurs.

Features
  Features are behaviours that a service expects other services to provide for it. If this makes no sense, imagine a situation in which a file-manager service expects any service to subscribe to its right-click menu on a file. In this way, the actions provided on that right-click menu are decentralized from the menu itself, and can be provided anywhere. This is very similar to a classical (e.g. Trac) *extension point*.

Actions
  Actions are gtk.Actions and are used in the user interface. An action maps directly to a single toolbar and menu action, and contains the necessary information to create this user interface item from it, including label, stock image etc.

Other files and directories
===========================

:file:`__init__.py`
  This file is required so that Python recognises the directory as a legitimate Python package.

:file:`service.pida`
  This empty file is just present to identify the package as a PIDA service.

data/
  This directory should contain any data files for the service that are not included in the other resource directories.

glade/
  This directory contains the glade files for the service's views. Although views can be created using Python-only, it is recommended for more detailed plugin views that they use glade.

pixmaps/
  This directory should contain any custom pixmaps for the service. These can be used in any way.

uidef/
  This directory should contain the UI Definition XML files for the service.  These are gtk.UIManager XML files, and define the menu bar and toolbar items for the service. The file myservice.xml is automatically loaded by PIDA, but others can exist in this directory and could be used to populate popup menus or to be further merged with the standard UI defnition.


