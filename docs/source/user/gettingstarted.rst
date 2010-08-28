.. include:: ../links.rst

Getting Started
===============

.. insert image of getting_started_wizard

First run wizard
~~~~~~~~~~~~~~~~

.. note:: This feature is planned for a future version of PIDA_, which is still undetermined yet.

.. getting_started_window

The PIDA window
~~~~~~~~~~~~~~~

Like any other IDE, PIDA provides in one window all the tools you need to edit your files,
compile your programs, invoke external tools, explore a project space or a file hierarchy, and so on.
The PIDA window is organized with a menu, a toolbar, multiple views and a status bar.
Many of these elements are optional and can be hidden or displayed at will.

The menu bar
^^^^^^^^^^^^

File
  This menu offers all file related operations,
  like creating, saving, or closing a document,
  but also all version control operations.
  PIDA also provides sessions management, 
  and the *File* menu permits to save the current session or load a previous one.

Edit
  This menu serves two purposes.
  
  First, it provides facilities to search documents throughout a project, or directories.
  But PIDA preferences and shortcuts settings are also modifiable from here.

Project
  This menu provides version control at project level.
  From there, it is also possible to modify the properties of a project 
  and to start the configured targets.

Tools
  Additional utilities, like a terminal and a Python shell for PIDA introspection.

View
  The PIDA window can be customized from there,
  displaying or hiding special views or elements like the menu bar or the tool bar.
  This menu also provides shortcuts to access quickly the most important views of the window,
  like the file manager.

Help
  Provides only the credits window for now.

The status bar
^^^^^^^^^^^^^^

The status bar provides live information on

- The current project.
- The current directory browsed in the file manager.
- Information on t file currently edited, like its name, encoding and size.

The editor
^^^^^^^^^^

The editor is the core element of PIDA.
All other views only provide utilities to fill the missing features of the editor 
or integrate important accessories -- like a debugger -- 
or give a quick access to external tools -- like a terminal.
The editor is also the central view of PIDA.
All other views can be moved around it.

PIDA can support any editor.
Editor shortcuts and features directly depend on what editor you prefer.
It is possible that some features of the chosen editor and PIDA features overlap.
In this case, both can be used,
but the feature implemented by PIDA will 
certainly provide better integration with the other tools of the IDE.

.. Insert image of getting_started_window_views 

Views
^^^^^

All elements in the PIDA window, except the editor, the menu bar, the toolbar and status bar, 
can be moved (remember that the menu bar and the toolbar can be hidden though).

FIXME: must choose carefully the vocabulary for elements of the views and keep them consistent.

.. getting_started_configuration

PIDA configuration
~~~~~~~~~~~~~~~~~~

FIXME: gconf, .pida

.. insert image of services

Core services
~~~~~~~~~~~~~

FIXME.

.. === Editor

.. ==== Vim

FIXME.

.. ==== Emacs

FIXME.

File Manager
~~~~~~~~~~~~

FIXME.

.. Insert image of service_project_manager

Project Manager
~~~~~~~~~~~~~~~

FIXME.

.. Insert image of service_terminal

Terminal
~~~~~~~~

FIXME.

.. service_version_control

Version Control
~~~~~~~~~~~~~~~

FIXME.

Preferences
~~~~~~~~~~~

FIXME.


.. Insert image: plugins

Plug-ins
~~~~~~~~

FIXME.

Bookmark
~~~~~~~~

Manage bookmark (files, directories...)

Checklist
~~~~~~~~~

FIXME.

GTags
~~~~~

GNU Global Integration » Build global index, search through database

Library
~~~~~~~

FIXME.

Man
~~~

Search and browse man page

PasteBin
~~~~~~~~

Send code to a pastebin service
 
Python
~~~~~~

Show class/function from python file, and show compilation errors

RFC
~~~

Download RFC index, search and view RFC pages inside PIDA

TODO
~~~~

Manage a personal todo list per project

Trac
~~~~

View bugs from Trac project inside PIDA

