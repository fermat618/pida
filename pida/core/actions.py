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

(
TYPE_RADIO,
TYPE_TOGGLE,
TYPE_NORMAL,
TYPE_MENUTOOL,
) = range(4)


class AccelMixin(object):

    def __init__(self):
        self.__keyval = None
        self.__modmask = None

    def set_accel_key(self, keyval, modmask):
        self.__keyval = keyval
        self.__modmask = modmask

    def set_accel(self, accel_string):
        self.set_accel_key(*gtk.accelerator_parse(accel_string))

    def bind_accel(self, accelgroup):
        self.set_accel_group(accelgroup)
        self.set_accel_path(self.accel_path)
        self.connect_accelerator()
        self.set_accel_keymap()

    def set_accel_keymap(self):
        if self.__keyval:
            gtk.accel_map_change_entry(self.accel_path, self.__keyval,
                                       self.__modmask, True)

    def build_accel_path(self):
        return '<Actions>/%s' % self.get_name()

    accel_path = property(build_accel_path)

    def get_keyval(self):
        return self.__keyval

    keyval = property(get_keyval)

    def get_modmask(self):
        return self.__keyval
    
    modmask = property(get_modmask)


class PidaAction(gtk.Action, AccelMixin):
    
    def __init__(self, *args, **kw):
        AccelMixin.__init__(self)
        gtk.Action.__init__(self, *args, **kw)


class PidaToggleAction(gtk.ToggleAction, AccelMixin):
    def __init__(self, *args, **kw):
        AccelMixin.__init__(self)
        gtk.ToggleAction.__init__(self, *args, **kw)
        
class PidaRadioAction(gtk.RadioAction, AccelMixin):
    def __init__(self, *args, **kw):
        AccelMixin.__init__(self)
        gtk.RadioAction.__init__(self, *args, **kw)

class PidaMenuToolAction(gtk.Action, AccelMixin):

    __gtype_name__ = "PidaMenuToolAction"

    def __init__(self, *args, **kw):
        AccelMixin.__init__(self)
        gtk.Action.__init__(self, *args, **kw)
        self.set_tool_item_type(gtk.MenuToolButton)


_ACTIONS = {
    TYPE_NORMAL: PidaAction,
    TYPE_TOGGLE: PidaToggleAction,
    TYPE_RADIO: PidaRadioAction,
    TYPE_MENUTOOL: PidaMenuToolAction,
}


class ActionsConfig(BaseConfig):

    def create(self):
        self._actions = gtk.ActionGroup(self.svc.get_name())
        self.create_actions()
        self.svc.boss.add_action_group_and_ui(
            self._actions,
            '%s.xml' % self.svc.get_name()
        )

    def create_actions(self):
        """Create your actions here"""

    def create_action(self, name, atype, label, tooltip, stock_id, callback=None):
        aclass = _ACTIONS[atype]
        act = aclass(name=name, label=label, tooltip=tooltip, stock_id=stock_id)
        self._actions.add_action(act)
        if callback is None:
            callback = getattr(self, 'act_%s' % name, None)
        if callback is not None:
            act.connect('activate', callback)

    def get_action(self, name):
        return self._actions.get_action(name)

    def get_action_group(self):
        return self._actions

        
