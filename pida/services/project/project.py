# -*- coding: utf-8 -*- 
"""
    Service project
    ~~~~~~~~~~~~~~~

    This service handles manging Projects

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later
"""
from __future__ import with_statement
import os, sys, os.path

import gtk

from kiwi.ui.objectlist import Column

from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.options import OptionsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_MENUTOOL, \
    TYPE_TOGGLE
from pida.core.projects import Project
from pida.ui.views import PidaGladeView, PidaView
from pida.ui.objectlist import AttrSortCombo
from pida.core.pdbus import DbusConfig, EXPORT
from pida.core import environment

from pida.utils.puilder.view import PuilderView

# locale
from pida.core.locale import Locale
locale = Locale('project')
_ = locale.gettext

LEXPORT = EXPORT(suffix='project')

def open_directory_dialog(parent, title, folder=''):
    filechooser = gtk.FileChooserDialog(title,
                                        parent,
                                        gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    filechooser.set_default_response(gtk.RESPONSE_OK)

    if folder:
        filechooser.set_current_folder(folder)

    response = filechooser.run()
    if response != gtk.RESPONSE_OK:
        filechooser.destroy()
        return

    path = filechooser.get_filename()
    if path and os.access(path, os.R_OK):
        filechooser.destroy()
        return path


class ProjectListView(PidaGladeView):

    key = 'project.list'

    gladefile = 'project_list'
    locale = locale
    label_text = _('Projects')

    icon_name = 'package_utilities'

    def create_ui(self):
        self.project_ol.set_headers_visible(False)
        self.project_ol.set_columns([Column('markup', use_markup=True)])
        self._sort_combo = AttrSortCombo(self.project_ol,
            [
                ('display_name', 'Name'),
                ('source_directory', 'Full Path'),
                ('name', 'Directory Name'),
            ],
            'display_name'
        )
        self._sort_combo.show()
        self.main_vbox.pack_start(self._sort_combo, expand=False)

    def on_project_ol__selection_changed(self, ol, project):
        self.svc.set_current_project(project)

    def on_project_ol__double_click(self, ol, project):
        self.svc.boss.cmd('filemanager', 'browse', new_path=project.source_directory)
        self.svc.boss.cmd('filemanager', 'present_view')

    def on_project_ol__right_click(self, ol, project, event):
        self.svc.boss.cmd('contexts', 'popup_menu', context='dir-menu',
            dir_name=project.source_directory, event=event,
            project=project)

    def set_current_project(self, project):
        self.project_ol.select(project)

    def update_project(self, project):
        self.project_ol.update(project)

    def can_be_closed(self):
        self.svc.get_action('project_properties').set_active(False)

class ProjectSetupView(PidaView):

    key = 'project.editor'

    label_text = _('Project Properties')

    def create_ui(self):
        self.script_view = PuilderView()
        self.script_view.show()
        self.script_view.set_execute_method(self.test_execute)
        self.script_view.connect('cancel-request',
                                 self._on_script_view__cancel_request)
        self.add_main_widget(self.script_view.get_toplevel())

    def test_execute(self, target, project):
        self.svc.execute_target(None, target, project)

    def set_project(self, project):
        #XXX: should we have more than one project viev ?
        #     for different projects each
        #XXX: ask on case of unsaved changes?
        self.project = project
        #self.script_view.load_script(
        #        os.path.join(
        #            project.source_directory,
        #            'build.vel'
        #            )
        #        )
        self.script_view.set_build(project.build)
        self.script_view.set_project(project)

    def _on_script_view__cancel_request(self, script_view):
        self.svc.get_action('project_properties').set_active(False)

    def can_be_closed(self):
        self.svc.get_action('project_properties').set_active(False)


class ProjectEventsConfig(EventsConfig):

    def create(self):
        self.publish('project_switched', 'loaded')

    def subscribe_all_foreign(self):
        self.subscribe_foreign('editor', 'started',
            self.editor_started)
        self.subscribe_foreign('contexts', 'show-menu', self.show_menu)
        self.subscribe_foreign('contexts', 'menu-deactivated',
            self.menu_deactivated)

    def editor_started(self):
        self.svc.set_last_project()

    def show_menu(self, menu, context, **kw):
        if (context == 'dir-menu'):
            is_project = 'project' in kw
            for a in ['project_properties', 'project_add',
                      'project_remove_directory']:
                self.svc.get_action(a).set_visible(is_project)
            for a in ['project_add_directory']:
                self.svc.get_action(a).set_visible(not is_project)

    def menu_deactivated(self, menu, context, **kw):
        if (context == 'dir-menu'):
            for a in ['project_properties', 'project_add', 'project_remove',
                      'project_add_directory']:
                self.svc.get_action(a).set_visible(True)


class ProjectActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'project_add',
            TYPE_NORMAL,
            _('_Add New Project'),
            _('Adds a new project'),
            gtk.STOCK_ADD,
            self.on_project_add,
        )

        self.create_action(
            'project_execute',
            TYPE_MENUTOOL,
            _('_Execute Default'),
            _('Execute the project'),
            'package_utilities',
            self.on_project_execute,
            ''
        )

        self.create_action(
            'project_execute_last',
            TYPE_MENUTOOL,
            _('Execute _last Controller'),
            _('Execute last Controller'),
            'package_utilities',
            self.on_project_execute_last,
            ''
        )

        self.create_action(
            'project_remove',
            TYPE_NORMAL,
            _('Remove from workspace'),
            _('Remove the current project from the workspace'),
            gtk.STOCK_DELETE,
            self.on_project_remove,
        )

        self.create_action(
            'project_properties',
            TYPE_TOGGLE,
            _('Project _Properties'),
            _('Show the project property editor'),
            'settings',
            self.on_project_properties,
        )

        self.create_action(
            'project_execution_menu',
            TYPE_NORMAL,
            _('Execution Controllers'),
            _('Configurations with which to execute the project'),
            gtk.STOCK_EXECUTE,
            self.on_project_execution_menu,
        )

        self.create_action(
            'project_add_directory',
            TYPE_NORMAL,
            _('Add Directory as Project'),
            _('Add this directory as a project in the workspace'),
            gtk.STOCK_ADD,
            self.on_project_add_directory,
        )

        self.create_action(
            'project_remove_directory',
            TYPE_NORMAL,
            _('Remove from workspace'),
            _('Remove the project from the workspace'),
            gtk.STOCK_DELETE,
            self.on_project_remove_directory,
        )

    def on_project_remove(self, action):
        self.svc.remove_current_project()

    def on_project_add(self, action):
        folder = self.svc.opt('project_root')
        if self.svc.opt('use_filemanager_path'):
            folder = self.svc.boss.cmd('filemanager', 'get_browsed_path')
        if folder:
            folder = os.path.expanduser(folder)
        path = open_directory_dialog(
            self.svc.window,
            _('Select a directory to add'),
            folder=folder
        )
        if path:
            self.svc.add_directory(path)

    def on_project_execute(self, action):
        default = self.svc._current.build.get_default()
        if default is not None:
            self.svc.execute_target(None, default)
        else:
            self.svc.error_dlg(
                _('This project has no default controller'))

    def on_project_execute_last(self, action):
        self.svc.execute_last()

    def on_project_properties(self, action):
        self.svc.show_properties(action.get_active())

    def on_project_execution_menu(self, action):
        menuitem = action.get_proxies()[0]
        #menuitem.remove_submenu()                    # gtk2.12 or higher
        #menuitem.set_submenu(self.svc.create_menu()) # gtk2.12 or higher
        submenu = menuitem.get_submenu()
        for child in submenu.get_children():
            submenu.remove(child)
        submenu_new =   self.svc.create_menu()
        for child in submenu_new.get_children():
            submenu_new.remove(child)
            submenu.append(child)

    def on_project_add_directory(self, action):
        path = action.contexts_kw.get('dir_name')
        self.svc.add_directory(path)

    def on_project_remove_directory(self, action):
        project = action.contexts_kw.get('project')
        self.svc.remove_project(project)

class ProjectFeaturesConfig(FeaturesConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('contexts', 'dir-menu',
            (self.svc.get_action_group(), 'project-dir-menu.xml'))


class ProjectOptions(OptionsConfig):

    def create_options(self):
        self.create_option(
            'project_root',
            _('Project Directories'),
            unicode,
            "~",
            _('The current directories in the workspace'),
            safe=False
        )

        self.create_option(
            'use_filemanager_path',
            _('Use Filemanager Path'),
            bool,
            True,
            _('Use the current filemanager path as startpoint')
        )

        self.create_option(
            'project_dirs',
            _('Project Directories'),
            list,
            [],
            _('The current directories in the workspace'),
            safe=False
        )

        self.create_option(
            'last_project',
            _('Last Project'),
            file,
            '',
            (_('The last project selected. ') +
            _('(Do not change this unless you know what you are doing)')),
            safe=False,
            workspace=True
        )



class ProjectCommandsConfig(CommandsConfig):

    def add_directory(self, project_directory):
        self.svc.add_directory(project_directory)

    def get_view(self):
        return self.svc.get_view()

    def get_current_project(self):
        return self.svc._current

    def get_project_for_document(self, document):
        return self.svc.get_project_for_document(document)

class ProjectDbusConfig(DbusConfig):

    @LEXPORT(in_signature='s')
    def add_directory(self, project_directory):
        self.svc.add_directory(project_directory)
        
    @LEXPORT(out_signature='s')
    def get_current_project_name(self):
        if self.svc._current:
            return self.svc._current.name
        return None
        
    @LEXPORT(out_signature='s')
    def get_current_project_source_directory(self):
        if self.svc._current:
            return self.svc._current.source_directory
        return None


# Service class
class ProjectService(Service):
    """The project manager service"""

    features_config = ProjectFeaturesConfig
    commands_config = ProjectCommandsConfig
    events_config = ProjectEventsConfig
    actions_config = ProjectActionsConfig
    options_config = ProjectOptions
    dbus_config = ProjectDbusConfig

    def pre_start(self):
        self._current = None

    def start(self):
        self._projects = []
        self.set_current_project(None)
        ###
        self.project_list = ProjectListView(self)
        self.project_properties_view = ProjectSetupView(self)
        self._read_options()

        acts = self.boss.get_service('window').actions

        acts.register_window(self.project_list.key,
                             self.project_list.label_text)


    def _read_options(self):
        for dirname in self.opt('project_dirs'):
            dirname = os.path.realpath(dirname)
            if not os.path.exists(dirname):
                self.log("%s does not exist", dirname)
                continue
            try:
                self._load_project(dirname)
            except Exception, e: #XXX: specific?!
                self.log("couldn't load project from %s", dirname)
                self.log.exception(e)

    def _save_options(self):
        self.set_opt('project_dirs', [p.source_directory for p in self._projects])

    def get_view(self):
        return self.project_list

    def add_directory(self, project_directory):
        # Add a directory to the project list
        project_directory = os.path.realpath(project_directory)
        project_file = Project.data_dir_path(project_directory, 'project.json')
        if not os.path.exists(project_file):

        #XXX: this should ask for the project name
        #     and a way to figure the branch name
            if self.boss.window.yesno_dlg(
                _('The directory does not contain a project file, ') +
                _('do you want to create one?')
            ):
                self.create_project_file(project_directory)
            else:
                return
        self.load_and_set_project(project_directory)
        self._save_options()

    def create_project_file(self, project_directory):
        project_name = os.path.basename(project_directory)
        Project.create_blank_project_file(project_name, project_directory)

    def set_current_project(self, project):
        self._current = project
        self.get_action('project_remove').set_sensitive(project is not None)
        self.get_action('project_execute').set_sensitive(project is not None)
        self.get_action('project_properties').set_sensitive(project is not None)
        self.get_action('project_execution_menu').set_sensitive(project is not None)
        if project is not None:
            project.reload()
            self.emit('project_switched', project=project)
            toolitem = self.get_action('project_execute').get_proxies()[0]
            toolitem.set_menu(self.create_menu())
            self.project_properties_view.set_project(project)
            self.get_action('project_execute').set_sensitive(bool(project.targets))
            self.set_opt('last_project', project.source_directory)
            self.boss.editor.set_path(project.source_directory)
            self._target_last = project.options.get('default')
            self.actions.get_action('project_execute_last').props.label = \
                _('Execute Last Controller')

    def set_last_project(self):
        last = self.opt('last_project')
        if last:
            for project in self._projects:
                if project.source_directory == last:
                    self.set_current_project(project)
                    self.project_list.set_current_project(project)

    def load_and_set_project(self, project_file):
        self.set_current_project(self._load_project(project_file))

    def _load_project(self, project_path):
        if not os.path.isdir(project_path):
            self.log(_("Can't load project. Path does not exist: %s") %project_path)
            return None
        try:
            project = Project(project_path)
        except (IOError, OSError), e:
            self.log(_("Can't load project. %s") % e)
            return None
        if project not in self._projects:
            self._projects.append(project)
            self.project_list.project_ol.append(project)
        self.emit('loaded', project=project)
        return project

    def remove_current_project(self):
        if self.remove_project(self._current):
            self.set_current_project(None)

    def remove_project(self, project):
        if self.boss.window.yesno_dlg(
            _('Are you sure you want to remove project "%s" from the workspace?')
            % project.name
        ):
            self._projects.remove(project)
            self.project_list.project_ol.remove(project, select=True)
            self._save_options()
            return True

    def execute_target(self, action, target, project=None):

        if project is None:
            project = self._current

        self.actions.get_action('project_execute_last').props.label = \
            _('Execute: %s') %target.name
        self._target_last = target

        script = environment.get_data_path('project_execute.py')

        env = ['PYTHONPATH=%s%s%s' %(environment.pida_root_path ,os.pathsep,
                                    os.environ.get('PYTHONPATH', sys.path[0]))]

        self.boss.cmd('commander', 'execute',
                commandargs=[
                    'python', script,
                    '--directory', project.source_directory,
                    '--target', target.name
                ],
                cwd=project.source_directory,
                title=_('%s:%s') % (project.name, target.name),
                env=env,
                )

    def execute_last(self):
        if self._target_last:
            self.execute_target(None, self._target_last)

    def create_menu(self):
        if self._current is not None:
            menu = gtk.Menu()
            for target in self._current.targets:
                act = gtk.Action(target,
                    target,
                    target, gtk.STOCK_EXECUTE)
                act.connect('activate', self.execute_target, target)
                mi = act.create_menu_item()
                menu.add(mi)
            menu.show_all()
            return menu

    def show_properties(self, visible):
        if visible:
            self.boss.cmd('window', 'add_detached_view', paned='Plugin',
                view=self.project_properties_view)
        else:
            self.boss.cmd('window', 'remove_view',
                view=self.project_properties_view)

    def get_project_for_document(self, document):
        matches = []
        match = None
        for project in self._projects:
            match = project.get_relative_path_for(document.filename)
            if match is not None:
                matches.append((project, match))
        if not matches:
            return match
        else:
            shortest = min(matches, key=lambda x:len(x[1]))
            return shortest[0], os.sep.join(shortest[1][-3:-1])
    
    def get_project_name(self):
        if self._current:
            return self._current.name
        return None
        


# Required Service attribute for service loading
Service = ProjectService



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
