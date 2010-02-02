PIDA Coding Style Guidelines
=============================

First read :pep:`008` (the PEP on how to write readable Python code). The PEP gives
a number of good insights. The PEP gives a few options on things, and I shall
try to clarify what I prefer here. Where this document differs from :pep:`008`, you
should use what is presented here, unless you are a zealot in which case you
should listen to the Python people (who are cleverer than me anyway). Also
read :pep:`020` while you are at it.

Indenting
~~~~~~~~~

4 Spaces, no tabs ever ever. This is not negotiable. Emacs users please check
your settings, somehow tabs creep into emacs-written code.

Line Width
~~~~~~~~~~

79 characters, perhaps 78 to be safe. This is negotiable, and there are times
when 83 character lines are acceptable. You can be the judge. I am not sure
many people use 80-character terminals these days, so we can be a bit less
hard-line than the PEP.

You can split lines however you wish. I personally use 3 different forms of
splitting depending on the purpose.

Long lists, dicts, or many paramteres to a function::

  service_base_classes =  [
      OptionsMixin,
      commands_mixin,
      events_mixin,
      bindings_mixin,
  ]

  def really_long_method_or_function_name(first_parameter, second_paramater,
                                          third_parameter)

It all depends on the use at the time, and we should remember to keep it
readable.

Blank Lines
~~~~~~~~~~~

As :pep:`008` for 2 lines between top-level classes and functions, with one line
between methods.

Extra blank line "to indicate logical blocks" should be avoided at all costs
in my opinion. Real logical blocks should be used to indicate logical blocks!
If you have to do this, a comment is better than a blank line.

Imports
~~~~~~~~

Only import the function or class you want to use, for example::

  from pida.ui.views import PidaView, BaseView

There are a few common exceptions like::

  import gtk

Multiple top-level imports are fine too if you like, but best grouped by where
they are comming from::

  import os, sys
  import gtk, gobject, pango

Remember to import in this order:

1. standard library imports
2. related third party imports
3. PIDA application/library specific imports

Whitespace
~~~~~~~~~~

Yes::

  def foo(blah, baz):

No::

  def foo ( blah , baz ):
  def foo(blah,baz):

(that space after a comma is basic punctuation)

:pep:`008` has oodles on this.

Docstrings
~~~~~~~~~~~


I like having the triple quotes as doubles, and for them to be on empty lines,
like so::

  def foo():
      """
      This is the single-line docstring
      """

Docstrings are plain nice, so please try to use them for all functions. I am
guilty of being lazy, so I can't blame anyone. Also we use API generation
which uses these doc strings, so it all helps.

Strings
~~~~~~~

Single quoted, unless you need single quotes in them, in which case use double
quotes::
  my_string = 'I am a banana'
  my_other_string = "I am a banana's uncle"

Naming
~~~~~~~

- Modules as lowercase single words with no underscores, except test modules
  which should start with `test_`.
- Functions as lower_case_with_underscores.
- Classes is CamelCase. (Note: I hate camel case, but it is useful, even
  in Python to know the difference between a class and a function. Why?
  You can subclass a class.)
- Module-level constants all in UPPERCASE_WITH_UNDERSCORES.

Conditional blocks
~~~~~~~~~~~~~~~~~~~

This is fine::

  if blah:
      baz = 1
  else:
      baz = 2

And better than::

    baz = 2
    if blah:
        baz = 1

But I am not going to argue, needs can force you into a certain style.
Remember, readability is key.

Magic
~~~~~

.. note::

  this is ali's war on weird magic

I hate magic, perhaps because I am dumb. I am really wary of using some of
Python's shoot-me-in-the-foot techniques because I have to maintain the code,
so. I have made these mistakes myself, and have (hopefully learned from the
mistakes. So.

Meta classes
    Never! I have yet to see a use-case for metaclasses which did not
    relate to perverting some other library or external class. I am happy
    to be enlightened.

Decorators
    Make perfect sense in some cases, but have the danger of being over
    used, so please think carefully whether you are using them to decorate
    behaviour, or just using them for the sake of it.

Inner classes
    I have yet to see a use-case that requires these.


