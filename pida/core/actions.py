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
import base
import string


(
TYPE_RADIO,
TYPE_TOGGLE,
TYPE_NORMAL
) = range(3)

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

_ACTIONS = {
    TYPE_NORMAL: PidaAction,
    TYPE_TOGGLE: PidaToggleAction,
    TYPE_RADIO: PidaRadioAction
}



def split_function_name(name):
    return name.split('_', 1)[-1]

def create_actions(meths, action_prefix, *action_args):
    '''This function grabs a list of methods and an 'action_prefix' and
    returns a list of actions.
    
    Accepted method properties are:
    
     * 'name', sets the action's 'name' property
     * 'label', sets the action's 'label' property
     * 'stock_id', sets the action's 'stock-id' property
     * 'type', on of TYPE_NORMAL, TYPE_TOGGLE and TYPE_RADIO.
       Defaults to TYPE_NORMAL
     * 'value', only used on TYPE_RADIO. Sets the gtk.RadioAction's value
     * 'group', only used on TYPE_RADIO. Sets the gtk.RadioAction's group
     * 'is_important', sets the action's 'is-important' property
     
    '''
    
    radio_elements = {}
    actions = []
    
    for meth in meths:
        name = split_function_name(meth.__name__)
        
        actname = "%s+%s" % (action_prefix, name)
        actname = getattr(meth, "name", actname)
        
        name = getattr(meth, "name", name)
        assert name is not None
        words = map(string.capitalize, name.split('_'))
        label = " ".join(words)
        label = getattr(meth, "label", label)
        stock_id = "gtk-%s%s" % (words[0][0].lower(), words[0][1:])
        stock_id = getattr(meth, "stock_id", stock_id)
        doc = meth.func_doc
        action_type = getattr(meth, "type", TYPE_NORMAL)
        action_factory = _ACTIONS[action_type]
        
        args = ()
        # gtk.RadioAction has one more argument in the constructor
        if action_type == TYPE_RADIO:
            args = [getattr(meth, "value")]
        
        action = action_factory(actname, label, doc, stock_id, *args)

        # set up the accel
        key_mod = getattr(meth, 'default_accel', None)
        if key_mod is not None:
            if isinstance(key_mod, tuple):
                action.set_accel_key(*key_mod)
            else:
                action.set_accel(key_mod)

        # gtk.RadioAction has an important property that needs to be set
        if action_type == TYPE_RADIO:
            radio_elements[name] = (action, getattr(meth, "group", None))
        
        action.set_property("is-important", getattr(meth, "is_important", False))
            
        action.connect("activate", meth, *action_args)
        actions.append(action)
    
    # Now we create the radio groups
    for name, (action, group) in radio_elements.iteritems():
        if group is None:
            continue
            
        group = radio_elements[group][0]
        action.set_group(group)

    return actions

def decorate_action(meth, **kwargs):
    '''This function is used to decorate methods, it is *not* a python decorator
    to use it you just need to do::
    
        class MyService(service.service):
            def act_my_action(self, action):
                """My tooltip text"""
            
            decorate_action(act_my_action, label="A cool label")
    
    So it is used to decorate the function and returns nothing.
    It accepts the same keyword arguments as the 'create_action' function.
    '''
            
    for key, val in kwargs.iteritems():
        setattr(meth, key, val)

def action(**kwargs):
    '''This is a python decorator to add metadata to your action methods.
    Its usage is very simple::
    
        class MyService(service.service):
            
            # A simple gtk.Action
            @action(stock_id=gtk.STOCK_GO_FORWARD, label="My Action")
            def act_my_action(self, action):
                """The tooltip text"""
                print "i'm on the activate callback"
            
            # A gtk.ToggleAction
            @action(stock_id=gtk.STOCK_GO_BACK, label="My Toggle Action",
                    type=TYPE_TOGGLE)
            def act_my_toggle_action(self, action):
                """Tooltip text for a toggle action"""
                print "i'm the activate callback"
            
            
            # A gtk.RadioAction. The 'group' argument is optional.
            @action(stock_id=gtk.STOCK_GO_DOWN, label="Second Radio Action",
                    value="bar", type="radio")
            def act_foo_bar(self, action):
                """This is the first element of the group"""
                print "I'm the activate callback" 

            # In this case the 'my_radio_action' is connected to 'foo_bar'
            # action.
            @action(stock_id=gtk.STOCK_GO_UP, label="My Radio Action",
                    value="foo", group="foo_bar", type=TYPE_RADIO)
            def act_my_radio_action(self, action):
                """Tooltip text for a radio action"""
                print "I'm the activate callback"
                
            # You can even change the action name
            @action(name="ACoolName", type=TYPE_RADIO, value=0)
            def act_this_name_is_ignored(self, action):
                pass
            
            # But when you refer to it you use the full name:
            @action(type=TYPE_RADIO, group="ACoolName", value=1)
            def act_something_cool(self, action):
                pass
    '''
    def wrapper(meth):
        for key, val in kwargs.iteritems():
            setattr(meth, key, val)
        return meth
    return wrapper

class action_handler(base.pidacomponent):

    type_name = 'action-handler'

    def __init__(self, service, *action_args):
        self.__service = service
        self.__init_actiongroup(*action_args)
        self.action_args = action_args
        self.init()

    def init(self):
        pass

    def __init_actiongroup(self, *action_args):
        agname = "%s+%s" % (self.__service.NAME, self.type_name)
        self.__action_group = gtk.ActionGroup(agname)
        
        methods = [getattr(self, attr) \
                   for attr in dir(self) \
                   if attr.startswith("act_")]

        add_action = self.__action_group.add_action
        map(add_action, create_actions(methods, agname, *action_args))
        

    def get_action_group(self):
        return self.__action_group
    action_group = property(get_action_group)

    def get_service(self):
        return self.__service
    service = property(get_service)

    def get_menu_definition(self):
        return """
                <menubar>
                <menu name="base_file" action="base_file_menu">
                </menu>
                <menu name="base_edit" action="base_edit_menu">
                </menu>
                <menu name="base_project" action="base_project_menu">
                </menu>
                <menu name="base_tools" action="base_tools_menu">
                </menu>
                </menubar>
                """
