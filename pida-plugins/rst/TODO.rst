TODO, roughly in order of priority
==================================

Must Have
---------

* persistent, project specific configuration (necessary for using Sphinx)
* GUI for setting this configurations
* Option to use docutils only, or in other words: use docutils only per default,
  checkflag to activate Sphinx. As soon as you activate Sphinx you must set some
  config values like the location of the conf.py file, etc.

Nice to Have
------------

* tests!!
* Expand the outliner per default (option)
* catch Sphinx errors/warnings that are not included in the doctree
  parse_messages
* Option to have the *full* Sphinx hierarchy in the outliner (not only the
  current document)
* Maybe an option to hide a certain number of levels in the outliner. Both for
  upper level as for leaves
* Performance improvements (doctree caching!)

Known Bugs
----------

* Headings with "&" in it do not work! They show up in the outliner with the
  same name than the previous heading

