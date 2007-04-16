# -*- coding: utf-8 -*- 

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
#Copyright (c) 2005-2006 The PIDA Project

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

# gtk import(s)
import gtk

# pida core import(s)
from pida.core.base import BaseConfig
from pida.core.options import OptionItem, manager, OTypeString

(
TYPE_RADIO,
TYPE_TOGGLE,
TYPE_NORMAL,
TYPE_MENUTOOL,
) = range(4)



class PidaMenuToolAction(gtk.Action):

    __gtype_name__ = "PidaMenuToolAction"

    def __init__(self, *args, **kw):
        gtk.Action.__init__(self, *args, **kw)
        self.set_tool_item_type(gtk.MenuToolButton)


_ACTIONS = {
    TYPE_NORMAL: gtk.Action,
    TYPE_TOGGLE: gtk.ToggleAction,
    TYPE_RADIO: gtk.RadioAction,
    TYPE_MENUTOOL: PidaMenuToolAction,
}


accelerator_group = gtk.AccelGroup()

class ActionsConfig(BaseConfig):

    accelerator_group = accelerator_group

    def create(self):
        self._actions = gtk.ActionGroup(self.svc.get_name())
        self._keyboard_options = {}
        self.create_actions()
        if self.svc.boss is not None:
            self.svc.boss.add_action_group_and_ui(
                self._actions,
                '%s.xml' % self.svc.get_name()
            )

    def create_actions(self):
        """Create your actions here"""

    def create_action(self, name, atype, label, tooltip, stock_id,
                      callback=None, accel_string=''):
        aclass = _ACTIONS[atype]
        act = aclass(name=name, label=label, tooltip=tooltip, stock_id=stock_id)
        self._actions.add_action(act)
        if callback is None:
            callback = getattr(self, 'act_%s' % name, None)
        if callback is not None:
            act.connect('activate', callback)
        self._create_key_option(act, name, label, tooltip, accel_string)

    def _create_key_option(self, act, name, label, tooltip, accel_string):
        opt = OptionItem(self._get_group_name(), name, label, OTypeString,
                         accel_string, tooltip, self._on_shortcut_notify)
        opt.action = act
        self._keyboard_options[name] = opt
        manager.register_option(opt)
        act.set_accel_group(self.accelerator_group)
        act.set_accel_path(self._create_accel_path(name))
        act.connect_accelerator()

    def _get_shortcut_gconf_key(self, name):
        return '/app/pida/keyboard_shortcuts/%s/%s' % (self.svc.get_name(),
                                                       name)

    def _get_group_name(self):
        return 'keyboard_shortcuts/%s' % self.svc.get_name()

    def get_action(self, name):
        return self._actions.get_action(name)

    def get_action_group(self):
        return self._actions

    def get_keyboard_options(self):
        return self._keyboard_options

    def _create_accel_path(self, name):
        return '<Actions>/%s' % name

    def _set_action_keypress(self, name, accel_string):
        keyval, modmask = gtk.accelerator_parse(accel_string)
        gtk.accel_map_change_entry(self._create_accel_path(name),
            keyval, modmask, True)

    def _set_action_keypress_from_option(self, option):
        self._set_action_keypress(option.name, manager.get_value(option))

    def _on_shortcut_notify(self, client, id, entry, option, *args):
        self._set_action_keypress_from_option(option)

    def subscribe_keyboard_shortcuts(self):
        for name, opt in self._keyboard_options.items():
            self._set_action_keypress_from_option(opt)


        

        
