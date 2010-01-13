TODO, roughly in order of priority
==================================

Must Have
---------

* persistent, project specific configuration (necessary for using Sphinx)
* GUI for setting this configurations
* Option to use docutils only, or in other words: use docutils only per default,
  checkflag to activate Sphinx. As soon as you activate Sphnix you must set some
  config values like the location of the conf.py file, etc.

Nice to Have
------------

* Always fall back to plain docutils if a document not below the sphinx srcdir
  is opened
* Expand the outliner per default (option)
* Option to have the *full* Sphinx hierarchy in the outliner (not only the
  current document)
* Performance improvements (doctree caching!)
* Maybe an option to not show the title of a document in the outliner (already
  true if only plain docutils is used)

