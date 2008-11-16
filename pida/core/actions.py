# -*- coding: utf-8 -*- 
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
"""
    Action support for PIDA services.

    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

# gtk import(s)
import gtk
import gobject

# pida core import(s)
from pida.core.base import BaseConfig
from pida.core.options import OptionsConfig
import warnings

# kiwi imports
from pida.ui.dropdownmenutoolbutton import DropDownMenuToolButton



class PidaMenuToolAction(gtk.Action):
    """
    Custom gtk.Action subclass for handling toolitems with a dropdown menu
    attached.
    """

    __gtype_name__ = "PidaMenuToolAction"

    def __init__(self, *args, **kw):
        gtk.Action.__init__(self, *args, **kw)
        self.set_tool_item_type(gtk.MenuToolButton)

class PidaDropDownMenuToolAction(gtk.Action):
    """
    Custom gtk.Action subclass for handling toolitems with a dropdown menu
    attached.
    """

    __gtype_name__ = "PidaDropDownMenuToolAction"

    def __init__(self, *args, **kw):
        gtk.Action.__init__(self, *args, **kw)
        self.set_tool_item_type(DropDownMenuToolButton)
        self._set_arrow = ((kw['label'] == None) or (kw['label'] == '')) and \
                          (kw['stock_id'] == None)

    def create_tool_item(self):
        toolitem = gtk.Action.create_tool_item(self)
        if (self._set_arrow == True):
            toolitem.set_arrow()
        return toolitem


class PidaRememberToggle(gtk.ToggleAction):
    """Remembers the state of the toggle on restart"""

    __gtype_name__ = "PidaRememberToggle"

    def __init__(self, *args, **kw):
        gtk.ToggleAction.__init__(self, *args, **kw)


TYPE_NORMAL = gtk.Action
TYPE_TOGGLE = gtk.ToggleAction
TYPE_REMEMBER_TOGGLE = PidaRememberToggle
TYPE_RADIO = gtk.RadioAction
TYPE_MENUTOOL = PidaMenuToolAction
TYPE_DROPDOWNMENUTOOL = PidaDropDownMenuToolAction


accelerator_group = gtk.AccelGroup()

class ActionsConfig(OptionsConfig):
    # this inherits from options in order to ease storing the mapping betwen
    # actions and accels (keyboard shortcuts)
    """
    The base action configurator.

    Services using actions should subclass this, and set their actions_config
    class attribute to the class. It will be instantiated on service activation
    with the service instance passed as the parameter to the constructor. The
    service will be available as the svc attribute in the configurator
    instance.
    """
    name = '%s.keys.json'
    dbus_path = "actions"
    accelerator_group = accelerator_group

    def create(self):
        """
        Called to initialize this configurator.

        Will initialise attributes, call create_actions, then register the
        actions and the ui definitions with the Boss.
        """
        OptionsConfig.create(self)
        self._actions = gtk.ActionGroup(self.svc.get_name())
        self._keyboard_options = {}
        self.create_actions()
        # call the real register_options after creating all actions
        OptionsConfig.register_options(self)
        if self.svc.boss is not None:
            self.ui_merge_id = self.svc.boss.add_action_group_and_ui(
                self._actions,
                '%s.xml' % self.svc.get_name()
            )

    def create_actions(self):
        """
        Called to create the actions.

        Create your service actions actions here. Each action should be created
        with a call to create_action. These actions will be added to the action
        group for the service, and can be used for any purpose.
        """

    def remove_actions(self):
        self.svc.boss.remove_action_group_and_ui(self._actions, self.ui_merge_id)

    def register_options(self):
        # disable this one so we can invoke it after the actions are created
        pass

    def _emit_change_notification(self, option):
        # disable options notification for the buildin way of action
        # notifications
        pass

    def create_action(self, name, atype, label, tooltip, stock_id,
                      callback=None, accel=None):
        """
        Create an action for this service.

        :param name:
            The unique name for the action. This must be unique for the
            service, so choose names wisely. For example:
            `show_project_properties`
        :param atype:
            This is the type of action, and maps directly to a type of
            gtk.Action. Types include:
            - TYPE_NORMAL: A normal gtk.Action
            - TYPE_TOGGLE: A gtk.ToggleAction
            - TYPE_RADIO: A gtk.RadioAction
            - TYPE_MENUTOOL: A custom Action which contains a dropdown menu
              when rendered as a tool item
            - TYPE_REMEMBER_TOGGLE: Toggle that will be remembered
        :param label:
            The label to display on proxies of the action.
        :param toolip:
            The tool tip to display on proxies of the action.
        :param stock_id:
            The stock id of the icon to display on proxies of the action.
        :param callback:
            The callback function to be called when the action is activated.
            This function should take the action as a parameter.
        :param accel:
            The accelerator string set as the default accelerator for this
            action, or `None` for actions that do not need an accelerator.
            To be used these actions must be proxied as items in one of the
            menus or toolbars.
        """
        act = atype(name=name, label=label, tooltip=tooltip, stock_id=stock_id)
        self._actions.add_action(act)
        if callback is not None:
            act.connect('activate', callback)

        if accel is not None:
            self._create_key_option(act, name, label, tooltip, accel)

        return act

    def _create_key_option(self, act, name, label, tooltip, accel):
        opt = self.create_option(name,
                         label, str,
                         accel, tooltip,
                         self._set_action_keypress_from_option)
        opt.action = act
        opt.stock_id = act.get_property('stock-id')
        self._keyboard_options[name] = opt
        act.opt = opt
        act.set_accel_group(self.accelerator_group)
        act.set_accel_path(self._create_accel_path(name))
        act.connect_accelerator()

    def get_action(self, name):
        """
        Get the named action
        """
        return self._actions.get_action(name)

    def get_action_group(self):
        """
        Get the action group
        """
        return self._actions

    def get_keyboard_options(self):
        """
        Get the keyboard options.
        """
        return self._keyboard_options

    def _create_accel_path(self, name):
        return '<Actions>/%s' % name

    def _set_action_keypress(self, name, accel_string):
        keyval, modmask = gtk.accelerator_parse(accel_string)
        gtk.accel_map_change_entry(self._create_accel_path(name),
            keyval, modmask, True)

    def _set_action_keypress_from_option(self, option):
        self._set_action_keypress(option.name, option.value)

    def subscribe_keyboard_shortcuts(self):
        """
        Set the keyboard shortcuts for the actions with keyboard shortcuts
        enabled.
        """
        self.register_options() #XXX: hack
        for opt in self:
            self._set_action_keypress_from_option(opt)

    def export_option(self, option):
        pass

    def list_actions(self):
        """
        iterate the optionsitems
        """
        for action in self._actions.list_actions():
            yield action
