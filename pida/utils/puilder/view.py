
import gtk

from kiwi.environ import Library

lib = Library('pida.utils.puilder', root='.')
lib.add_global_resources(glade='glade')

from kiwi.ui.delegates import GladeDelegate, GladeSlaveDelegate

from kiwi.ui.objectlist import Column
from kiwi.ui.dialogs import yesno
from kiwi.utils import gsignal

from pida.utils.puilder.model import action_types
from pida.utils.gthreads import gcall

import gettext
gettext.install('pida.puild')

def start_editing_tv(tv):
    def _start(tv=tv):
        v = tv.get_treeview()
        path, col = v.get_cursor()
        v.set_cursor(path, col, start_editing=True)
    gcall(_start)


def create_source_tv(tv):
    b = tv.get_buffer()

    tt = b.create_tag('tt', family='Monospace')

    def on_changed(tv):
        b.remove_all_tags(b.get_start_iter(), b.get_end_iter())
        b.apply_tag(tt, b.get_start_iter(), b.get_end_iter())

    tv.connect('content-changed', on_changed)


class PuilderView(GladeSlaveDelegate):

    gladefile = 'puild_properties'

    parent_window = None

    gsignal('cancel-request')

    def __init__(self, *args, **kw):
       GladeSlaveDelegate.__init__(self, *args, **kw)
       self.create_ui()

    def create_ui(self):
        def format_default(obj):
            return obj and _('<i>default</i>') or ''
    
        self.targets_list.set_columns([
            Column('name', editable=True, expand=True),
            Column('is_default', format_func=format_default, 
                                 use_markup=True, title='Default'),
            Column('action_count', title='Actions'),
        ])
        self.targets_list.set_headers_visible(False)

        self.acts_list.set_columns([
            Column('type', expand=False),
            Column('value', expand=True, ellipsize=True),
        ])
        self.acts_list.set_headers_visible(False)

        self.acts_type.prefill(action_types)

        self.target_changed(None)
        self.action_changed(None)

        self.action_views = {}
        self.create_action_views()

        m = self._create_menu(self.TargetMenu, self.AddTarget,
                              None, self.AddShellTarget,
                              self.AddPythonTarget, None,
                              self.AddImportTarget, None,
                              self.ExecuteTargets)
        self.menu.add(m)

        for mi in self.AddImportTarget.get_proxies():
            menu = gtk.Menu()
            for (name, key) in external_system_types:
                m = gtk.MenuItem(name)
                menu.append(m)
                m.connect('activate', self._on_import_target_activate, key)
            menu.show_all()
            mi.set_submenu(menu)

        m = self._create_menu(self.ActsMenu, self.AddActs)
        self.menu.add(m)

        self.menu.show_all()

    def _on_import_target_activate(self, menuitem, type):
        t = self.build.create_new_target()
        t.name = 'External Build'
        self.targets_list.append(t, select=True)
        a = t.create_new_action()
        a.type = 'external'
        a.options['system'] = type
        self.acts_list.append(a, select=True)

    def set_execute_method(self, f):
        self.execute_method = f

    def on_SetDefault__activate(self, action):
        t = self.targets_list.get_selected()
        self.build.default = t
        self.targets_list.refresh()

    def on_ExecuteTargets__activate(self, action):
        t = self.targets_list.get_selected()
        if t is not None:
            self.execute_method(t, self.project)


    def _create_menu(self, base_act, *actions):
        newitem = base_act.create_menu_item()
        newitem.show()

        newmenu = gtk.Menu()
        newmenu.show()

        for act in actions:
            if act is None:
                m = gtk.SeparatorMenuItem()
            else:
                m = act.create_menu_item()
            m.show_all()
            newmenu.add(m)

        newitem.set_submenu(newmenu)

        return newitem


    def _create_popup(self, event, *actions):
        menu = gtk.Menu()
        for act in actions:
            if act is not None:
                mi = act.create_menu_item()
            else:
                mi = gtk.SeparatorMenuItem()
            menu.add(mi)
        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)


    def on_targets_list__right_click(self, ol, target, event):
        self._create_popup(event, self.AddTarget, None, self.SetDefault, 
                           self.ExecuteTargets, None, self.DelCurrentTarget)

    def on_acts_list__right_click(self, ol, action, event):
        self.act_up_act.set_sensitive(self.acts_list.index(action) > 0)
        self.act_down_act.set_sensitive(
            self.acts_list.index(action) < (len(self.acts_list) - 1))
        self._create_popup(event, self.AddActs, None, self.act_up_act,
                           self.act_down_act, None, self.DelCurrentActs)

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
        self.acts_type.update(name)

    def set_build(self, build):
        self.build = build
        self.targets_list.add_list(self.build.targets, clear=True)
        if len(self.targets_list):
            self.targets_list.select(self.targets_list[0])

        for v in self.action_views.values():
            v.build = build

    def set_project(self, project):
        self.project = project
        self.project_label.set_markup(project.markup)
        self.project_name_entry.set_text(project.display_name)

    def target_changed(self, target):
        selected = target is not None
        self.DelCurrentTarget.set_sensitive(selected)
        self.action_holder.set_sensitive(selected)
        self.acts_list.set_sensitive(selected)

        if selected:
            self.acts_list.add_list(target.actions, clear=True)

            if len(self.acts_list):
                self.acts_list.select(self.acts_list[0])

        else:
            self.acts_list.clear()

    def action_changed(self, action):
        selected = action is not None
        self.action_holder.set_sensitive(selected)
        self.DelCurrentActs.set_sensitive(selected)
        #self.up_ac.set_sensitive(selected)
        #self.down_acts.set_sensitive(selected)

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

    def revert(self):
        self.project.reload()
        self.set_project(self.project)
        self.set_build(self.project.build)

    def on_save_button__clicked(self, button):
        self.build.dumpf(self.project.project_file)

    def on_close_button__clicked(self, button):
        self.revert()
        self.emit('cancel-request')

    def on_revert_button__clicked(self, button):
        self.revert()

    def on_targets_list__selection_changed(self, ol, target):
        self.target_changed(target)

    def on_AddTarget__activate(self, button):
        t = self.build.create_new_target('New Target')
        self.targets_list.append(t, select=True)
        start_editing_tv(self.targets_list)

    def on_AddPythonTarget__activate(self, action):
        t = self.build.create_new_target('New Target')
        self.targets_list.append(t, select=True)
        a = t.create_new_action()
        a.type = 'python'
        self.acts_list.append(a, select=True)

    def on_AddShellTarget__activate(self, action):
        t = self.build.create_new_target('New Target')
        self.targets_list.append(t, select=True)
        a = t.create_new_action()
        self.acts_list.append(a, select=True)

    def on_DelCurrentTarget__activate(self, button):
        t = self.targets_list.get_selected()
        if self.confirm('Are you sure you want to delete target "%s"' % t.name):
            self.build.targets.remove(t)
            self.targets_list.remove(t)

    def on_AddActs__activate(self, button):
        target = self.targets_list.get_selected()
        if target is None:
            return
        act = target.create_new_action()
        self.acts_list.append(act, select=True)

    def on_DelCurrentActs__activate(self, button):
        act = self.acts_list.get_selected()
        target = self.targets_list.get_selected()
        if act is None or target is None:
            return
        if self.confirm('Are you sure you want to remove this action?'):
            target.actions.remove(act)
            self.acts_list.remove(act)

    def on_act_up_act__activate(self, action):
        pass

    def on_act_down_act__activate(self, action):
        pass

    def on_acts_list__selection_changed(self, ol, act):
        self.action_changed(act)

    def on_acts_type__content_changed(self, cmb):
        act = self.acts_list.get_selected()
        if not act:
            return
        name = cmb.read()
        act.type = name
        self.action_type_changed(act)

    def on_name_edit_button__clicked(self, button):
        if self.project is None:
            return
        if button.get_label() == gtk.STOCK_EDIT:
            self.project_name_entry.set_sensitive(True)
            button.set_label(gtk.STOCK_OK)
            self.project_name_entry.grab_focus()
        else:
            display_name = self.project_name_entry.get_text()
            if display_name:
                self.project.set_display_name(display_name)
                self.project_label.set_markup(self.project.markup)
                self.project_name_entry.set_sensitive(False)
                button.set_label(gtk.STOCK_EDIT)
            else:
                self.project_name_entry.set_text(self.project.display_name)
                self.project_name_entry.grab_focus()
                self.svc.error_dlg(_('Do not set empty project names'))

    def confirm(self, question):
        return yesno(question, parent=self.parent_window)


class ActionView(GladeSlaveDelegate):

    def __init__(self, *args, **kw):
        GladeSlaveDelegate.__init__(self)
        self.action = None
        self.create_ui()

    def _set_action(self, action):
        self.action = action
        if action is not None:
            self.set_action(action)

    def set_action(self, action):
        raise NotImplementedError

    def create_ui(self):
        raise NotImplementedError




class ShellActionView(ActionView):

    gladefile = 'action_shell'

    def create_ui(self):
        #self.env_list.set_columns([
        #    Column('name', expand=True),
        #    Column('value', expand=True),
        #])
        pass

    def set_action(self, action):
        self.command.set_text(action.value)
        if action.options.has_key('cwd') and action.options['cwd']:
            self.cwd.set_current_folder(action.options['cwd'])
            self.cwd_on.props.active = True
        else:
            self.cwd_on.props.active = False

    def on_cwd_on__toggled(self, entry):
        self.cwd.props.sensitive = entry.props.active
        if not entry.props.active:
            del self.action.options['cwd']
        else:
            self.action.options['cwd'] = self.cwd.get_current_folder()

    def on_cwd__file_set(self, entry):
        #FIXME: use uri here when gio lands
        self.action.options['cwd'] = self.cwd.get_current_folder()

    def on_command__changed(self, entry):
        if self.action is None:
            return
        t = entry.get_text()
        if self.action.value != t:
            self.action.value = t

class PythonActionView(ActionView):

    gladefile = 'action_python'

    def create_ui(self):
        create_source_tv(self.text)

    def set_action(self, action):
        self.text.update(action.value)

    def on_text__content_changed(self, textview):
        self.action.value = self.text.read()


external_system_types = [
    ('Make', 'make'),
    ('Vellum', 'vellum'),
]

class ExternalActionView(ActionView):

    gladefile = 'action_external'

    def create_ui(self):
        self.action = None
        self.system_types.prefill(external_system_types)

    def set_action(self, action):
        self.system_types.update(action.options.get('system', 'make'))
        self.external_name.set_text(action.value)
        self.build_args.set_text(action.options.get('build_args', ''))

    def on_system_types__content_changed(self, cmb):
        if self.action is None:
            return
        self.action.options['system'] = cmb.read()

    def on_external_name__changed(self, entry):
        self.action.value = entry.get_text()

    def on_build_args__changed(self, entry):
        self.action.options['build_args'] = entry.get_text()


class TargetActionView(ActionView):

    gladefile = 'action_target'

    def create_ui(self):
        self.block = False

    def set_action(self, action):
        self.block = True
        items = [('', None)] + [(t.name, t.name) for t in self.build.targets]
        self.targets_combo.prefill(items)
        try:
            self.targets_combo.update(action.value)
        except KeyError:
            self.targets_combo.update(None)
        self.block = False

    def on_targets_combo__content_changed(self, cmb):
        if self.action is None:
            return
        if self.block:
            return
        print ['chann', cmb.read()]
        self.action.value = cmb.read()

action_views = {
    'shell': ShellActionView,
    'python': PythonActionView,
    'external': ExternalActionView,
    'target': TargetActionView,
}

if __name__ == '__main__':
    v = PuilderView()
    v.show_and_loop()
