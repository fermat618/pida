class BaseTextView(object):
    """
    Api is as in gtk.TextView, additional here
    """
    has_syntax_highlighting = False
    _doctype = None
    
    def get_doctype(self):
        """
        Returns the pida.core.doctype.DocType object assigned to this
        view
        """
        return self._doctype

    def set_doctype(self, doctype):
        """
        Sets the doctype for this View

        @param doctype: pida.core.doctypes.DocType instance
        """
        self._doctype = doctype

    def set_syntax_highlight(self, status):
        """
        Sets the syntax highlighting on/off
        """
        pass

    def get_syntax_highlight(self):
        """
        Returns the status of the syntax highlighting
        """
        return None

    def set_show_line_numbers(self, value):
        """
        Sets if the line numbers should be shown
        """
        pass

    def get_show_line_numbers(self):
        """
        Sets if the line numbers should be shown
        """
        return False