
Introduction
============

There are many IDE around, and some are very good. But lots of them are also
_closed_ in the sense that they are limited in terms of extensibility or
communication with other tools. On the other hand, some of you may want to
change your editor for anything else, even if you have to rely on external tools
to complete its features.

PIDA was designed with these problems in mind. PIDA's _motto_ is to reuse the
tools that proved to be useful and solid, and to provide the glue for them. PIDA
is written in Python with *PyGTK*, is easily extensible through plug-ins and can
embed any editor provided someone writes an adapter for it.

PIDA has a number of unique features, such as

- Embedding Vim, Emacs or any editor.
footnote:[Of course, the editor has to provide a way to communicate with for
external programs. *Moo*, *Scite*, and probably *GEdit* could be candidates]
- Using any version control system.
