
import gtk

from kiwi.environ import Library

lib = Library('pida.utils.puilder', root='.')
lib.add_global_resources(glade='glade')

from kiwi.ui.delegates import GladeDelegate, GladeSlaveDelegate

from kiwi.ui.objectlist import Column
from kiwi.ui.dialogs import yesno

from pida.utils.puilder.model import action_types

def start_editing_tv(tv):
    v = tv.get_treeview()
    path, col = v.get_cursor()
    v.set_cursor(path, col, start_editing=True)

class PuilderView(GladeSlaveDelegate):

    gladefile = 'puild_properties'

    parent_window = None

    def __init__(self, *args, **kw):
       GladeSlaveDelegate.__init__(self, *args, **kw)
       self.create_ui()

    def create_ui(self):
        self.targets_list.set_columns([
            Column('name', editable=True, expand=True),
            Column('action_count', title='Actions'),
        ])

        self.acts_list.set_columns([
            Column('type', width=50),
            Column('one_liner', title='Content', expand=True),
        ])

        self.deps_list.set_columns([
            Column('name', title='Target name', expand=True),
        ])

        self.acts_type.prefill(action_types)

        self.target_changed(None)
        self.action_changed(None)

        self.action_views = {}
        self.create_action_views()

    def create_action_views(self):
        for name in action_views:
            v = self.action_views[name] = action_views[name]()
            self.acts_holder.append_page(v.get_toplevel())

        noview = gtk.Label()
        self.acts_holder.append_page(noview)
        self.action_views['noview'] = noview

    def switch_action_view(self, name):
        n = self.acts_holder.page_num(self.action_views[name].get_toplevel())
        self.acts_holder.set_current_page(n)

    def set_build(self, build):
        self.build = build
        self.targets_list.add_list(self.build.targets, clear=True)
        if len(self.targets_list):
            self.targets_list.select(self.targets_list[0])

    def set_project(self, project):
        self.project = project

    def target_changed(self, target):
        selected = target is not None
        self.up_target.set_sensitive(selected)
        self.down_target.set_sensitive(selected)
        self.del_target.set_sensitive(selected)
        self.acts_book.set_sensitive(selected)

        if selected:
            self.target_label.set_text(target.name)
            self.acts_list.add_list(target.actions, clear=True)
            self.deps_list.add_list(target.dependencies, clear=True)

            if len(self.acts_list):
                self.acts_list.select(self.acts_list[0])

        else:
            self.target_label.set_text('None Selected')
            self.acts_list.clear()
            self.deps_list.clear()

    def action_changed(self, action):
        selected = action is not None
        self.action_holder.set_sensitive(selected)
        self.del_acts.set_sensitive(selected)
        self.up_acts.set_sensitive(selected)
        self.down_acts.set_sensitive(selected)

        if selected:
            self.action_type_changed(action)

    def action_type_changed(self, action):
        self.action_views[action.type]._set_action(action)
        self.switch_action_view(action.type)
        self.acts_list.update(action)

    def _clear_acts_holder(self):
        children = self.acts_holder.get_children()
        for c in children:
            self.acts_holder.remove(c)

    def on_save_button__clicked(self, button):
        f = open('test', 'w')
        f.write(self.build.dumps())
        f.close()
        print 'saved'
        print self.build.dumpf(self.project.project_file)

    def on_targets_list__selection_changed(self, ol, target):
        self.target_changed(target)

    def on_add_target__clicked(self, button):
        t = self.build.create_new_target('New Target')
        self.targets_list.append(t, select=True)
        start_editing_tv(self.targets_list)

    def on_del_target__clicked(self, button):
        t = self.targets_list.get_selected()
        if self.confirm('Are you sure you want to delete target "%s"' % t.name):
            self.build.targets.remove(t)
            self.targets_list.remove(t)

    def on_add_acts__clicked(self, button):
        target = self.targets_list.get_selected()
        if target is None:
            return
        act = target.create_new_action()
        self.acts_list.append(act, select=True)

    def on_del_acts__clicked(self, button):
        act = self.acts_list.get_selected()
        target = self.targets_list.get_selected()
        if act is None or target is None:
            return
        if self.confirm('Are you sure you want to remove this action?'):
            target.actions.remove(act)
            self.acts_list.remove(act)

    def on_acts_list__selection_changed(self, ol, act):
        self.action_changed(act)

    def on_acts_type__content_changed(self, cmb):
        act = self.acts_list.get_selected()
        if not act:
            return
        name = cmb.read()
        act.type = name
        self.action_type_changed(act)

    def confirm(self, question):
        return yesno(question, parent=self.parent_window)


class ActionView(GladeSlaveDelegate):

    def __init__(self, *args, **kw):
        GladeSlaveDelegate.__init__(self)

    def _set_action(self, action):
        self.action = action
        self.set_action(action)

    def set_action(self, action):
        raise NotImplementedError

    def create_ui(self):
        raise NotImplementedError




class ShellActionView(ActionView):

    gladefile = 'action_shell'

    def create_ui(self):
        self.env_list.set_columns([
            Column('name', expand=True),
            Column('value', expand=True),
        ])

    def set_action(self, action):
        self.command.set_text(action.value)

    def on_command__changed(self, entry):
        t = entry.get_text()
        print t
        if self.action.value != t:
            self.action.value = t

class PythonActionView(ActionView):

    gladefile = 'action_python'

    def create_ui(self):
        pass

    def set_action(self, action):
        self.text.update(action.value)

    def on_text__content_changed(self, textview):
        self.action.value = self.text.read()

action_views = {
    'shell': ShellActionView,
    'python': PythonActionView,
}

if __name__ == '__main__':
    v = PuilderView()
    v.show_and_loop()
