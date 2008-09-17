# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, 
# Boston, MA 02111-1307, USA.
"""
Language Support Superclasses

:license: GPL3 or later
:copyright:
    * 2008 Daniel Poelzleithner
    * 2006 Frederic Back (fredericback@gmail.com)
"""

UNKNOWN, INFO, WARNING, ERROR = 0, 1, 2, 3

class ValidationError(object):
    message = ''
    message_args = ()
    type = UNKNOWN
    filename = None
    ineno = None

    def __init__(self, filename, lineno):
        self.filename = filename
        self.lineno = lineno

    def __str__(self):
        return '%s:%s: %s' % (self.filename, self.lineno, self.message % self.message_args)

    @staticmethod
    def from_exception(exc):
        """Returns a new Message from a python exception"""
        # FIXME
        pass


class Validator(object):

    def __init__(self, svc, view):
        """Instances a new Validator
        
        svc - Languages Service
        view - ErrorView instance
        """
        self.svc = svc
        self.view = view
        pass

    def set_current_document(self, document):
        """Sets the current document on the Validator"""
        raise NotImplemented

    def refresh_view(self):
        """Refreshes the current document"""
        raise NotImplemented

    def check_current(self):
        """Checks the current document for errors"""
        return self.check(self._current)

    def check(self, document):
        """
        This is function does the actual work.
        
        Returns a list of ValidationError objects.
        Empty list means no error occured
        
        """
        return []

    def set_view_items(self, items):
        self.view.set_items(items)

    def get_view(self):
        return self.view

    def set_view(self, view):
        self.view = view


class Outliner(object):
    """ An abstract interface for class parsers.

    A class parser monitors gedit documents and provides a gtk.TreeModel
    that contains the browser tree. Elements in the browser tree are reffered
    to as 'tags'.

    There is always only *one* active instance of each parser. They are created
    at startup (in __init__.py).

    The best way to implement a new parser is probably to store custom python
    objects in a gtk.treestore or gtk.liststore, and to provide a cellrenderer
    to render them.
    """

    #------------------------------------- methods that *have* to be implemented

    def __init__(self, document):
        """
        Constructs a new Outliner object for a Document
        
        document - pida.core.document.Document object
        """
        pass


    def parse(self): 
        """ 
        Parse a Document
        """
        pass        


    def cellrenderer(self, treeviewcolumn, cellrenderertext, treemodel, it):
        """ A cell renderer callback function that controls what the text label
        in the browser tree looks like.
        See gtk.TreeViewColumn.set_cell_data_func for more information. """
        pass

    #------------------------------------------- methods that can be implemented

    def pixbufrenderer(self, treeviewcolumn, cellrendererpixbuf, treemodel, it):
        """ A cell renderer callback function that controls what the pixmap next
        to the label in the browser tree looks like.
        See gtk.TreeViewColumn.set_cell_data_func for more information. """
        cellrendererpixbuf.set_property("pixbuf",None)


    def get_tag_position(self, path):
        """ Return the position of a tag in a file. This is used by the browser
        to jump to a symbol's position.
        
        Returns a tuple with the full file uri of the source file and the line
        number of the tag or None if the tag has no correspondance in a file.
        
        path -- a tuple containing the treepath
        """
        pass


    def get_menu(self, path):
        """ Return a list of gtk.Menu items for the specified tag. 
        Defaults to an empty list
        
        path -- a tuple containing the treepath
        """
        return []


    def current_line_changed(self, line):
        """ Called when the cursor points to a different line in the document.
        Can be used to monitor changes in the document.
        
        model -- a gtk.TreeModel (previously provided by parse())
        doc -- a gedit document
        line -- int
        """
        pass


    def get_tag_at_line(self, linenumber):
        """ Return a treepath to the tag at the given line number, or None if a
        tag can't be found.
        
        model -- a gtk.TreeModel (previously provided by parse())
        doc -- a gedit document
        linenumber -- int
        """
        pass


class Autocompleter(object):
    """
    The Autocompleter class is used to send autocompletion informations
    to PIDA
    """

    def __init__(self, document):
        """
        
        """
        self.document = document


    def parse(self)
        """
        Parse the document.
        """
        pass

    def current_line_changed(self, line):
        """ Called when the cursor points to a different line in the document.
        Can be used to monitor changes in the document.

        model -- a gtk.TreeModel (previously provided by parse())
        doc -- a gedit document
        line -- int
        """
        pass

    def get_model(self):
        """
        Gets a gtk.TreeModel for the document valid on the line.
        """
        pass

    def input_event(self, event):
        """
        Keystroke events get passed here.
        This allows a performant way to adjust the internal filter when the user
        types further.
        """
        pass

    def cursor_changed(self, line, column, charcount):
        """
        Updates the internal model, most likely the visibilty function's state
        for the current cursor position.
        """
        pass


from pida.core.service import Service


class LanguageService(Service):
    """
    Base class for easily implementing a language service
    """

    language_name = None
    autocompleter_factory = None
    outliner_factory = None
    validator_factory = None

    def pre_start(self):
        if self.language_name is None:
            raise NotImplementedError('Language services must specify a language.')


