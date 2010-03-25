# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

import os
import gtk
import string
import pida.utils.serialize as simplejson
from functools import partial

# PIDA Imports
from pida.core.service import Service
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.options import OptionsConfig, Color
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_TOGGLE, TYPE_REMEMBER_TOGGLE, TYPE_MENUTOOL
from pida.core.document import Document
from pida.core.features import FeaturesConfig
from pida.core.environment import workspace_name, settings_dir

# locale
from pida.core.locale import Locale
locale = Locale('window')
_ = locale.gettext



class ActionWindowMapping(list):
    """
    Specialised mapping for persitant shortcuts on plugin windows
    """
    def __init__(self, svc):
        self.svc = svc
        self._actions = {}
        super(ActionWindowMapping, self).__init__()

    @staticmethod
    def _genkey(key):
        """Returns the key for a action"""
        return 'window_config_%s' %key.replace(".", "_")

    def add(self, config):
        """
        Add a new shortcut for focusing a window.
        Get the shorcut from the window-config
        """
        self.append(config)
        keya = self._genkey(config.key)
        curshort = self.svc.actions.get_extra_value('window-config').\
                                                                get(keya, '')

        act = self.svc.actions.create_action(
            keya,
            TYPE_NORMAL,
            "Focus %s" %_(config.label_text),
            config.description or _('Focus %s window') %_(config.label_text),
            "",
            self.svc.actions.on_focus_window,
            config.default_shortcut,
            global_=True
        )
        act.key = config.key
        act.visible_action = config.action
        self._actions[config.key] = act
        self.svc.actions.set_value(keya, curshort)
        # make the shortcuts update to reflect change
        self.svc.boss.get_service('shortcuts').update()

    def remove(self, config):
        """Unregister a WindowConfig"""
        # unregister action
        self.svc.actions.remove_action(self._actions[config.key])

        del self._actions[config.key]
        opt = self.svc.actions.get_option(self._genkey(config.key))
        self.svc.actions.remove_option(opt)
        #self.remove(config)
        self.svc.boss.get_service('shortcuts').update()


class WindowCommandsConfig(CommandsConfig):

    def add_view(self, paned, view, removable=True, present=True, detachable=True):
        self.svc.window.add_view(paned, view, removable, present, detachable=detachable)
        self.svc.save_state()

    def add_detached_view(self, paned, view, size=(500,400)):
        self.add_view(paned, view)
        self.detach_view(view, size)
        self.svc.save_state()

    def close_focus_pane(self):
        pane = self.svc.window.get_focus_pane()
        if pane:
            if pane.view.can_be_closed() and pane.view:
                self.remove_view(pane.view)

    def toggle_sticky_pane(self):
        pane = self.svc.window.get_focus_pane()
        if pane:
            self.svc.window.paned.set_params(
                    pane, 
                    keep_on_top=not pane.get_params().keep_on_top)

    def remove_view(self, view):
        self.svc.window.remove_view(view)
        self.svc.save_state()

    def detach_view(self, view, size):
        self.svc.window.detach_view(view, size)
        self.svc.save_state()

    def present_view(self, view):
        self.svc.window.present_view(view)
        self.svc.save_state()

    def is_added(self, view):
        return view in self.svc.window

class WindowActionsConfig(ActionsConfig):

    def create_actions(self):
        self.register_extra_option('window-config', safe=False, notify=True,
                                   default={}, workspace=False)

        self.create_action(
            'show_toolbar',
            TYPE_TOGGLE,
            _('Show Toolbar'),
            _('Toggle the visible state of the toolbar'),
            'face-glasses',
            self.on_show_ui,
            '<Shift><Control>l',
        )

        self.create_action(
            'show_menubar',
            TYPE_TOGGLE,
            _('Show _Menubar'),
            _('Toggle the visible state of the menubar'),
            'face-glasses',
            self.on_show_ui,
            '<Shift><Control>u',
        )

        self.create_action(
            'fullscreen',
            TYPE_TOGGLE,
            _('F_ullscreen'),
            _('Toggle the fullscreen mode'),
            gtk.STOCK_FULLSCREEN,
            self.on_fullscreen,
            '<Shift>F11',
        )

        self.create_action(
            'max_editor',
            TYPE_TOGGLE,
            _('M_aximize Editor'),
            _('Maximizes the editor by hiding panels'),
            gtk.STOCK_FULLSCREEN,
            self.on_max_editor,
            'F11',
        )


        self.create_action(
            'switch_next_term',
            TYPE_NORMAL,
            _('Next _terminal'),
            _('Switch to the next terminal'),
            gtk.STOCK_GO_FORWARD,
            self.on_switch_next_term,
            '<Alt>Right',
            global_=True
        )

        self.create_action(
            'switch_prev_term',
            TYPE_NORMAL,
            _('Previous te_rminal'),
            _('Switch to the previous terminal'),
            gtk.STOCK_GO_BACK,
            self.on_switch_prev_term,
            '<Alt>Left',
            global_=True
        )

        self.create_action(
            'focus_terminal',
            TYPE_NORMAL,
            _('F_ocus terminal'),
            _('Focus terminal pane terminal'),
            'terminal',
            self.on_focus_terminal,
            '<Shift><Control>i',
            global_=True
        )

        self.create_action(
            'close_pane',
            TYPE_NORMAL,
            _('Close Pane'),
            _('Close the current active pane'),
            gtk.STOCK_CLOSE,
            self.on_close_pane,
            '<Control>F4',
            global_=True
        )

        self.create_action(
            'toggle_sticky',
            TYPE_NORMAL,
            _('Toggle sticky'),
            _('Toggle the sticky button on current pane'),
            'pin',
            self.on_toggle_sticky,
            '',
            global_=True
        )

        self.create_action(
            'WindowMenu',
            TYPE_MENUTOOL,
            _('Win_dows'),
            _('Show window list'),
            'package_utilities',
            self.on_windows,
        )

    def on_focus_window(self, action):
        if action.visible_action and isinstance(action.visible_action, 
                                          (TYPE_TOGGLE, TYPE_REMEMBER_TOGGLE)):
                action.visible_action.set_active(True)
        self.svc.present_key_window(action.key)

    def on_windows(self, action):
        self.svc.create_window_list()

    def on_focus_terminal(self, action):
        self.svc.window.present_paned('Terminal')

    def on_switch_next_term(self, action):
        self.svc.window.switch_next_view('Terminal')

    def on_switch_prev_term(self, action):
        self.svc.window.switch_prev_view('Terminal')

    def on_close_pane(self, action):
        self.svc.cmd('close_focus_pane')

    def on_toggle_sticky(self, action):
        self.svc.cmd('toggle_sticky_pane')

    def on_fullscreen(self, action):
        self.svc.set_fullscreen(action.get_active())

    def on_max_editor(self, action):
        self.svc.set_max_editor(action.get_active())

    def on_show_ui(self, action):
        val = action.get_active()
        self.svc.set_opt(action.get_name(), val)
        getattr(self.svc, action.get_name())(val)

    def _on_option_change(self, option):
        # hacky highjacking to put the options into a extra config :-)
        self.svc.actions.get_extra_value('window-config')[option.name] = \
            option.value
        self.svc.actions.set_extra_value('window-config', 
            self.svc.actions.get_extra_value('window-config'))
        # call normal callback
        self._set_action_keypress_from_option(option)

    def _create_key_option(self, act, name, label, tooltip, accel, global_=False):
        opt = super(WindowActionsConfig, self)._create_key_option(act, 
                                            name, label, tooltip, accel, global_=global_)

        if name[:14] == 'window_config_':
            # we highjack the callback on the external defined options
            # so we can set the extra option value so it gets persistent saved
            opt.callback = self._on_option_change

class WindowEvents(EventsConfig):

    def subscribe_all_foreign(self):
        self.subscribe_foreign('buffer', 'document-changed',
            self.on_document_changed)
        self.subscribe_foreign('editor', 'started',
            self.on_editor_started)

    def on_document_changed(self, document):
        self.svc.update_title(document=document)

    def on_editor_started(self):
        self.svc.boss.hide_splash()
        self.svc.window.show()


class WindowFeatures(FeaturesConfig):
    def create(self):
        nmapping = partial(ActionWindowMapping, self.svc)
        self.publish_special(
            nmapping,
            'window-config',
        )


        #self.publish('window-config')
        #self.subscribe('window-config', self.on_window_config)



class WindowOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'show_toolbar',
            _('Show the toolbar'),
            bool,
            True,
            _('Whether the main toolbar will be shown'),
            self.on_show_ui,
        )

        self.create_option(
            'show_menubar',
            _('Show the menubar'),
            bool,
            True,
            _('Whether the main menubar will be shown'),
            self.on_show_ui,
        )

        self.create_option(
            'window_title',
            _('Window title'),
            str,
            'Pida - $workspace - $filepath',
            _('Title template for the pida window.\n'
              '$basename : Filename of Document - $filepath : Full filepath \n'
              '$directory : Directory if file - $workspace : Workspace name \n'
              '$project_path - $project_name'),
            self.on_title_change,
        )

        self.create_option(
            'project_color',
            _('Project color'),
            Color,
            '#600060',
            _('The color projects shall have in PIDA'),
            self.on_color_change,
        )

        self.create_option(
            'no_project_color',
            _('No project color'),
            Color,
            '#CB4444',
            _('The color projects shall have in PIDA'),
            self.on_color_change,
        )

        self.create_option(
            'directory_color',
            _('Directory color'),
            Color,
            '#0000c0',
            _('The color directories shall have in PIDA'),
            self.on_color_change,
        )

    def on_show_ui(self, option):
        self.svc.get_action(option.name).set_active(option.value)

    def on_color_change(self, option):
        self.svc.update_colors()

    def on_title_change(self, *args):
        self.svc._title_template = None
        self.svc.update_title()

# Service class
class Window(Service):
    """The PIDA Window Manager"""

    commands_config = WindowCommandsConfig
    options_config = WindowOptionsConfig
    actions_config = WindowActionsConfig
    events_config = WindowEvents
    features_config = WindowFeatures

    def pre_start(self):
        self._title_template = None
        self._last_focus = None
        super(Window, self).pre_start()
        self.update_colors()
        self.restore_state(pre=True)

    @property
    def state_config(self):
        return os.path.join(settings_dir, 'workspaces', workspace_name(), "window.state.json")

    def start(self):
        # Explicitly add the permanent views
        for service in ['project', 'filemanager', 'buffer']:
            view = self.boss.cmd(service, 'get_view')
            self.cmd('add_view', paned='Buffer', view=view, removable=False, present=False)
        self._fix_visibilities()
        self.update_colors()
        self._window_list_id = self.boss.window.create_merge_id()
        self._action_group = gtk.ActionGroup('window_list')
        self.boss.window._uim._uim.insert_action_group(self._action_group, -1)
        self.restore_state()
        self.window.paned.connect('config-changed', self.save_state)
        self.window.paned.connect('pane-attachment-changed', self._on_pane_detachment)

    def pre_stop(self):
        self.save_state()
        return True

    def stop(self):
        self.save_state()

    def restore_state(self, pre=False):
        try:
            fp = open(self.state_config, "r")
        except (OSError, IOError), e:
            self.log.warning("Can't open window state file %s",
                                    self.state_config)
            return
        data = simplejson.load(fp)

        if pre:
            # in pre mode we restore the paned config and the window position/size, etc
            self.boss.window.paned.set_config(data.get('panedstate', ''))
            # restore window size and position
            if data.has_key('pida_main_window'):
                cdata = data['pida_main_window']
                # test if data is valid. we don't place the window where it
                # is not fully visible
                try:
                    height = max(int(cdata['height']), 100)
                    width = max(int(cdata['width']), 100)
                    x = max(int(cdata['x']), 0)
                    y = max(int(cdata['y']), 0)
                    if x + width <= gtk.gdk.screen_width() and \
                       y + height <= gtk.gdk.screen_height():
                        self.boss.window.resize(width, height)
                        self.boss.window.move(x, y)
                    else:
                        self.log.debug("Won't restore window size outside screen")
                except (ValueError, KeyError):
                    pass
            return

        for service in self.boss.get_services():
            name = service.get_name()
            info = data.get(name, {})

            if not info:
                continue
            for action in service.actions.list_actions():
                if isinstance(action, TYPE_REMEMBER_TOGGLE):
                    if action.get_name() in info:
                        action.set_active(data[name][action.get_name()])

    def save_state(self, *args):
        if not self.started:
            return
        data = {}
        data['panedstate'] = self.boss.window.paned.get_config()
        # save window size and position
        size = self.boss.window.get_size()
        pos = self.boss.window.get_position()
        data['pida_main_window'] = {
            "width": size[0],
            "height": size[1],
            "x": pos[0],
            "y": pos[1],
        }
        for service in self.boss.get_services():
            cur = {}
            if not hasattr(service, "actions"):
                continue
            for action in service.actions.list_actions():
                if isinstance(action, TYPE_REMEMBER_TOGGLE):
                    cur[action.get_name()] = action.props.active
            if cur:
                data[service.get_name()] = cur
        
        try:
            fp = open(self.state_config, "w")
            simplejson.dump(data, fp, indent=4)
        except (OSError, IOError), e:
            self.log.warning("Can't open state file %s" %self.state_config)

    def _on_pane_detachment(self, bigpaned, pane, detached):
        if detached:
            # thanks gtk for not letting me test if accel is already added
            win = pane.get_child().get_toplevel()
            if not getattr(win, '_pida_accel_added', False):
                win.add_accel_group(self.actions.global_accelerator_group)
                win._pida_accel_added = True

    def update_colors(self):
        # set the colors of Document
        Document.markup_directory_color = self.opt('directory_color')
        Document.markup_project_color = self.opt('project_color')
        Document.markup_color_noproject = self.opt('no_project_color')

    def update_title(self, document=None):
        if self._title_template is None:
            self._title_template = string.Template(self.opt('window_title'))
        if document is None:
            document = self.boss.cmd('buffer', 'get_current')
        
        subs = {'basename': document.basename or _('New Document'),
                'filepath': document.filename or _('New Document'),
                'directory': document.directory or '',
                'workspace': workspace_name(),
                'project_path': document.project and document.project.data_dir or '',
                'project_name': document.project_name
               }
        
        self.window.set_title(self._title_template.safe_substitute(subs))
        

    def _fix_visibilities(self):
        for name in ['show_toolbar', 'show_menubar']:
            val = self.opt(name)
            self.get_action(name).set_active(val)
            getattr(self, name)(val)

    def show_toolbar(self, visibility):
        self.window.set_toolbar_visibility(visibility)

    def show_menubar(self, visibility):
        self.window.set_menubar_visibility(visibility)

    def set_fullscreen(self, var):
        if var:
            self.boss.window.fullscreen()
        else:
            self.window.unfullscreen()


    def set_max_editor(self, var):
        if var:
            # shall we do a weak ref here ?
            self._last_focus = self.boss.window.get_focus()
            self.window.set_fullscreen(var)
            self.boss.editor.cmd('grab_focus')
        else:
            self.window.set_fullscreen(var)
            if self._last_focus:
                try:
                    # this maight fail due various reasons, like
                    # the window was destroyed etc
                    self._last_focus.grab_focus()
                except: 
                    pass

    def get_fullscreen(self, var):
        return self.window.get_fullscreen()

    def _on_window_action(self, action, view):
        self.boss.window.present_view(view)

    def _on_doc_action(self, action, doc):
        self.boss.get_service('buffer').view_document(doc)

    def present_key_window(self, key):
        for pane in self.boss.window.paned.list_panes(every=True):
            if pane.key == key:
                self.cmd('present_view', view=pane)
                return

    def create_window_list(self):
        # update the window menu list
        # clean up the old list
        self.boss.window.remove_uidef(self._window_list_id)
        for action in self._action_group.list_actions():
            self._action_group.remove_action(action)

        i = 0
        # add panels to list. they are sorted after the paned positions and
        # therefor good
        for pane in self.boss.window.paned.list_panes(every=True):
            action_name = "show_window_%s" %i
            act = gtk.Action(action_name,
                "_%s" %pane.label_text,
                '',
                '')
            act.connect('activate', self._on_window_action, pane)
            self._action_group.add_action(act)
            self.boss.window._uim._uim.add_ui(
                self._window_list_id,
                "ui/menubar/AddMenu/WindowMenu/window_list", 
                "_%s" %pane.label_text, 
                action_name, 
                gtk.UI_MANAGER_MENUITEM, 
                False)            #mi = act.create_menu_item()
            i += 1
        # add documents to list
        docs = list(self.boss.get_service('buffer').get_documents().itervalues())
        # we sort the docs list alphabeticly as its easier for the eye to navigate
        docs.sort(lambda x,y: cmp(unicode(x).lower(), unicode(y).lower()))
        for doc in docs:
            action_name = "show_window_%s" %i
            act = gtk.Action(action_name,
                unicode(doc),
                '',
                '')
            act.connect('activate', self._on_doc_action, doc)
            self._action_group.add_action(act)
            self.boss.window._uim._uim.add_ui(
                self._window_list_id,
                "ui/menubar/AddMenu/WindowMenu/buffer_list", 
                unicode(doc), 
                action_name, 
                gtk.UI_MANAGER_MENUITEM, 
                False)
            i += 1
        return None

# Required Service attribute for service loading
Service = Window



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
