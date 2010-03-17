# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2009 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import gtk
from pida.ui.views import PidaGladeView
from pygtkhelpers.ui.objectlist import Column

# locale
from pida.core.locale import Locale
locale = Locale('core')
_ = locale.gettext


class Category(object):
    """Abstract class to implement a category list"""

    customized = False
    
    temporary_list = None
    display_info = None

    @property
    def has_subcategories(self):
        return any(self.get_subcategories())

    def get_subcategories(self):
        """
        Returns a list of Category objects
        """
        return []

    @property
    def has_entries(self):
        return any(self.get_entries())

    def get_entries(self, default=False):
        """
        Returns a list of Entry objects to be displayed 
        in the Priority list

        @default: return the list in the uncustomized order
        """
        return []

    def commit_list(self, lst):
        """
        Update the entries list
        """
        pass

class Entry(object):
    """
    Entries are listed in the priority list
    """

    uid = None
    display = ""
    plugin = ""
    description = ""

    def __init__(self, **kwargs):
        for key,value in kwargs.iteritems():
            setattr(self, key, value)

def display_or_repr(obj):
    if hasattr(obj, 'display'):
        return obj.display
    return unicode(obj)


def edited(obj):
    return 'edited' if obj else 'unedited'


class PriorityEditorView(PidaGladeView):
    gladefile = 'priority_editor'
    locale = locale

    def __init__(self, *args, **kwargs):
        self._current_selection = None
        self._root_category = None
        self.simple = kwargs.pop('simple', False)
        super(PriorityEditorView, self).__init__(*args, **kwargs)

    def create_ui(self):

        self.selection_tree.set_columns([
            Column('customized', title=' ',
                   format_func=edited,
                   use_stock=True,
                   justify=gtk.JUSTIFY_RIGHT,
                   ),
            Column('display', title=_('Category'), 
                   expand=True,
                   searchable=True,
                   sorted=True,
                   )])
        self.priority_list.set_columns([
            Column('display', title=_('Name'), width=125),
            Column('plugin', title=_('Plugin')),
            Column('description', title=_('Description'), 
                   expand=True)])

        if self.simple:
            self.category_splitter.set_position(0)
            self.selection_tree.hide()
        else:
            self.selection_tree.show()

    def set_category_root(self, root):
        """
        Sets the value list for a entry. If display is not None,
        the string representation of entry is displayed in the category.

        In simple mode, entry and display is ignored.

        @tree: list of entries to display
        @category: category to set. can be Category object or string
        """
        self._root_category = root
        self.selection_tree.clear()
        self.priority_list.clear()

        def add_sub(root, sub):
            self.selection_tree.append(sub, parent=root)
            for ssub in sub.get_subcategories():
                add_sub(sub, ssub)

        for sub in root.get_subcategories():
            add_sub(None, sub)

        #assert(tree, 

    def on_selection_tree__selection_changed(self, *args):
        self.save_list()
        cur = self.selection_tree.selected_item
        # we have to update the priority list only if the customize checkbox
        # does not change
        if not cur:
            return
        #update_prio = self.customize_button.get_active() == cur.customized
        if cur.display_info:
            self.info.set_markup(cur.display_info)
            self.info.props.visible = True
        else:
            self.info.props.visible = False

        self.customize_button.set_active(cur.customized)
        #if update_prio:
        self.update_priority_list()
        self.customize_button.set_sensitive(len(self.priority_list))
        # open the submenu
        self.selection_tree.expand_item(cur, open_all=True)

    def save_list(self):
        if self._current_selection:
            if self.customize_button.get_active():
                self._current_selection.temporary_list = list(self.priority_list)
            else:
                self._current_selection.temporary_list = None

    def update_priority_list(self, default=False):
        self.priority_list.clear()
        cur = self.selection_tree.selected_item
        self._current_selection = cur
        if cur:
            if cur.temporary_list is not None and not default:
                self.priority_list.clear()
                self.priority_list.extend(cur.temporary_list)
            else:
                if default or not cur.customized:
                    default = True
                self.priority_list.extend(cur.get_entries(default=default))


    def on_customize_button__toggled(self, action):
        cur = self.selection_tree.selected_item
        customized = False
        if cur:
            cur.customized = customized = self.customize_button.get_active()
        for wid in [self.button_move_up, self.button_move_down, 
                    self.priority_list]:
            wid.set_sensitive(customized)
        if cur:
            self.selection_tree.update(cur)
        #self.priority_list.set_sensitive(True)
        self.update_priority_list()
        #self.priority_list.set_sensitive(cur.customized)

    def on_all_languages__toggled(self, action):
        self.set_category_root(self._root_category)

    def on_button_move_up__clicked(self, action):
        self.priority_list.move_item_up(self.priority_list.selected_item)

    def on_button_move_down__clicked(self, action):
        self.priority_list.move_item_down(self.priority_list.selected_item)

    def on_button_reset__clicked(self, action):
        #self.reset_caches()
        self.update_priority_list(default=True)

    def on_button_close__clicked(self, action):
        self.reset_caches()

    def on_button_apply__clicked(self, action):
        self.save_list()
        def save(root):
            for cat in self.selection_tree.get_descendants(root):
                #if cat.temporary_list != None:
                cat.commit_list(cat.temporary_list or [])
        for cat in self.selection_tree:
            save(cat)

    def reset_caches(self):
        for item in self.selection_tree:
            # we set a [] here, because it's not None and will
            item.temporary_list = None


if __name__ == "__main__":
    from pida.core import environment
    from tests.ui.test_priorityeditor import TestRootCategory
    import sys
    environment.parse_args(sys.argv)
    twin = gtk.Window()
    twin.connect('delete-event', gtk.main_quit)
    twin.resize(550, 350)
    pe = PriorityEditorView(None)
    tr = TestRootCategory()
    pe.set_category_root(tr)
    twin.add(pe.get_toplevel())
    twin.show()

    gtk.mainloop()
