raise ImportError # does not do highlighting yet. reason unknown

import moo
import gtk

from .base import BaseTextView

from pida.services.language import DOCTYPES

MAPPINGS = {}

def build_mapping():
    global MAPPINGS, LANG_MANAGER
    for lang in moo.edit.lang_mgr_default().get_available_langs():
        best = DOCTYPES.get_fuzzy(lang.props.name)
        if best:
            MAPPINGS[best.internal] = lang

build_mapping()
EDITOR_INSTANCE = moo.edit.create_editor_instance()
moo.edit.plugin_read_dirs()
moo.utils.PrefsPage()
#import os
#from pida.core.environment import pida_home
#script_path = os.path.join(pida_home, 'pida_mooedit.rc')
#_state_path = os.path.join(pida_home, 'pida_mooedit.state')
#moo.utils.prefs_load(sys_files=None, file_rc=script_path, file_state=_state_path)


class MooTextView(BaseTextView, moo.edit.TextView):
    """
    Simple gtk.TextView based Field without syntax highlighting
    """
    has_syntax_highlighting = True

#    def __new__(cls, *args, **kwargs):
#        print cls, args, kwargs
#        ed = EDITOR_INSTANCE.new_doc()
#        #for i in cls.__dict__:
#        #    if i[:2] != "__":
#        #        setattr(ed, i, cls.__dict__[i])
#        super(MooTextView, cls).__new__(ed)
#        return ed

#    def __init__(self):
#        moo.edit.Edit.__init__(self, editor=EDITOR_INSTANCE)
#        #self = EDITOR_INSTANCE

    def set_doctype(self, doctype):
        print "do set_doctype"
        self._doctype = doctype
        self.set_lang(MAPPINGS.get(doctype.internal, None))
        self.props.enable_highlight = True
        print self.props.enable_highlight
        self.props.draw_tabs = True
        print self.get_buffer().get_lang()
        print self.get_style()
        #buffer_.set_highlight(True)

    def set_show_line_numbers(self, value):
        self.props.show_line_numbers = value

    def get_show_line_numbers(self, value):
        return self.props.show_line_numbers