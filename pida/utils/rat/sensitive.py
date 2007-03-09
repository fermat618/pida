"""
This module exposes a common pattern on developing HIG applications, you often
have more then one condtions affecting a widget's sensitive state, worst
sometimes these conditions are not centralised and may even be created by
plugins. To help solve this problem you can use a
L{SensitiveController} or a L{SignalBind}.
"""
__license__ = "MIT <http://www.opensource.org/licenses/mit-license.php>"
__author__ = "Tiago Cogumbreiro <cogumbreiro@users.sf.net>"
__copyright__ = "Copyright 2005, Tiago Cogumbreiro"

import gobject
import weakref

class SensitiveClient:
    """
    The L{SensitiveClient} can affect the widget's target state by changing the
    method L{SensitiveClient.set_sensitive}.
    
    When no references exist to this client it's unregistred from its
    controller.
    """
    def __init__(self, counter):
        self.counter = counter
        self._sensitive = True
    
    def set_sensitive(self, sensitive):
        """
        Set this client's sensitive state.
        """
        if self._sensitive == sensitive:
            return
        
        self._sensitive = sensitive
        
        if sensitive:
            self.counter.dec()
        else:
            self.counter.inc()
        
    def __del__(self):
        # unregister from parent
        self.counter.dec()

class _Counter:
    """
    The Counter object uses a weakref to the callback, so if you by any chance
    loose its reference the Counter object will no longer use it.
    """
    def __init__(self, callback = None):
        self.__count = 0
        if self.__callback is not None:
            self.__callback = callback
        
    def __callback(self, amount):
        """This is a no-op"""
    
    def inc(self):
        self.__count += 1
        self.__callback(self.__count)
    
    def dec(self):
        self.__count -= 1
        self.__callback(self.__count)
    
    
class SensitiveController:
    """
    The L{SensitiveController} is the class responsible for maintaining
    the widget sensitive state. Whenever you want to add a new condition that
    affects your widget you create a new client and then use that client as if
    it was your condition::
        lbl = gtk.Label("My widget")
        cnt = SensitiveController(lbl)
        client = cnt.create_client()
        client.set_sensitive(len(lbl.get_text()) > 0)
    
    If you create more clients in your controller your widget will only be
    sensitive when B{all} its clients are set to C{True}, if one is set to
    insensitive the widget will be insensitive as well.

    When this object has no references back it will make the widget sensitive.
    """
    class _Callback:
        def __init__(self, widget):
            self.widget = widget
        
        def callback(self, counter):
            assert counter >= 0
            self.widget.set_sensitive(counter <= 0)
        
    def __init__(self, widget):
        self.widget = widget
        cb = self._Callback(widget)
        self.__counter = _Counter(cb.callback)
        widget.set_sensitive(True)
    
    def __on_change(self, counter):
        assert counter >= 0
        self.widget.set_sensitive(counter <= 0)
    
    def create_client(self):
        """
        It will create one more client to the controller.
        
        @rtype: L{SensitiveClient}
        """
        return SensitiveClient(self.__counter)

    def __del__(self):
        self.widget.set_sensitive(True)
        
class SignalBind(object):
    """
    The L{SignalBind} helps you connect a signal from a widget that
    will affect the sensitive state of your target widget. For example if we want
    a button the be sensitive only when a text entry has some text in it we do the
    following::
        btn = gtk.Button()
        cnt = rat.sensitive.SensitiveController(btn)
        entry = gtk.Entry()
        sig_bind = rat.sensitive.SignalBind(cnt)
        sig_bind.bind(entry, "text", "changed", lambda txt: len(txt) > 0)
    
    Summing it up, the L{SignalBind} connects a property and a signal
    of a certain widget to a controller.
    
    Reference counting is thought of, this means that if the L{SignalBind}
    has not references back to it it will call the L{SignalBind.unbind} method.
    
    
    """
    class _Callback:
        """
        The callback object is used to remove circular dependencies.
        It exists for private use only.
        """
        def __init__(self, affecter, property, condition, client):
            self.property  = property
            self.condition = condition
            self.client    = weakref.ref(client)
            self.__call__(affecter)

        def __call__(self, src, *args):
            value = self.condition(src.get_property(self.property))
            self.client().set_sensitive(value)
            
    def __init__(self, controller):
        self.controller = controller
        self.source     = None
        self.client     = None
    
    def bind(self, affecter, property, signal, condition):
        """
        Connects the affecter through a certain signal to the sensitive binder.
        
        @param affecter: the widget that has a certain property, which will be
            triggered by a certain signal.
        @param property: the property which will be evaluated by the condition
            when the signal is called
        @param signal: the signal that is triggered when the property is changed
        @param condition: the condition is a function that accepts one value
            which is the property's value.
        """
        
        assert self.source is None, "call unbind() before bind()"
        
        self.client = self.controller.create_client()
        cb = self._Callback(affecter, property, condition, self.client)
        self.source = affecter.connect(signal, cb.__call__)
    
    def unbind(self):
        """
        Calling the unbind method will remove the L{SensitiveController}
        registration and the source associated with the signal it's
        listening to.
        """
        assert self.source is not None, "bind() must be called before unbind()"
        assert self.client is not None, "There's a bug in this program"
        gobject.source_remove(self.source)

        self.source = None
        self.client = None
        
        
    def __del__(self):
        if self.source is not None:
            self.unbind()
