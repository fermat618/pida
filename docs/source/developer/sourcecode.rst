=========================
Obtaining The Source Code
=========================

The current development version of pida has various experimental changes which aren't yet ready for the main repo; most of the development happens on the DeveloperRepos.

First, obtain a fresh::

  hg clone http://www.bitbucket.org/aafshar/pida-main/

This repository aggregates the current experimental development.

Installing the Dependencies
===========================

The easy unix way
-----------------

Run:: 

  cd YOUR/pida-main
  ./tools/update_externals.sh

The custom way
--------------

Get this::
  
  hg clone http://www.bitbucket.org/RonnyPfannschmidt/anyvc/

This is our vcs-abstraction lib, we extracted it to ease development.

And this::

  hg clone http://www.bitbucket.org/agr/rope/
 
This is a Python refactoring library.  We use it for code-analysis.  Refactoring is planned.

The new development version *completely* breaks backward compatibility for project files and project metadata.

We started using vellum to get project metadata and a task based command system with dependency handling.

The basic integration of vellum is done but some shipped plugins are broken because they used to store metadata in project files.

Publishing your work
====================

The most easy way is to set up an bitbucket account, create a public fork, and start pushing to it.  That way we get notified about it and can just grab it if you send us a pull request.

It is recommended to chat with us at the irc channel at irc://irc.freenode.org/pida or start a discussion on our moderated google group at http://groups.google.com/group/pida.


