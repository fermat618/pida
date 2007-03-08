# -*- coding: utf-8 -*- 

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
#Copyright (c) 2005 Ali Afshar aafshar@gmail.com

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

import time

class Event(object):

    """
    An event dispatcher is the central events object. To use it you must first
    create an event with the ``create_event`` method, this will return an
    event source which is basically the function you'll use to trigger the
    event. After that you register the callbacks. Its usage follows:
    
    >>> dispatcher = EventDispatcher()
    >>> evt_src = dispatcher.create_event ("on-ring-event")
    >>> 
    >>> def callback1 ():
    >>>     print "riiiing!"
    >>> 
    >>> dispatcher.register_callback ("on-ring-event", callback1)
    >>> 
    >>> evt_src ()
    riiing
    >>> 
    """
    def __init__(self):
        self.__events = {}
        
    def create_event (self, event_name):
        self.__events[event_name] = []
        def event_source (*args, **kwargs):
            for callback in self.__events[event_name]:
                callback(*args, **kwargs)
        return event_source
    
    def create_events (self, event_names, event_sources = None):
        """
        This is a utility method that creates or fills a dict-like object
        and returns it. The keys are the event names and the values are the
        event sources.
        """
        if event_sources is None:
            event_sources = {}
            
        for evt_name in event_names:
            event_sources[evt_name] = self.create_event(evt_name)
        return event_sources
    
    def has_event(self, event_name):
        return event_name in self.__events
    
    def register (self, event_name, callback):
        assert self.has_event(event_name)
        self.__events[event_name].append(callback)

    def unregister (self, event_name, callback):
        self.__events.remove (callback)

    def emit(self, event_name, **kw):
        for callback in self.__events.get(event_name):
            # TODO: remove this after profilling is done 
            current_time = time.time()
            callback(**kw)
            elapsed = time.time() - current_time
            if elapsed >= 0.001:
                try:
                    classname = callback.im_self.__class__.__name__
                    kind = callback.im_self.__class__.__module__
                    
                    # im within pida - strip useless extra informations
                    if kind.startswith("pida"): 
                        kind = kind.split('.')[1]

                    self.log.debug( "%s: %f -- %s: %s" % ( 
                          event_name, elapsed, kind, classname))
                except AttributeError, v:
                    self.log.debug(
                    "Error couldnt extract callback informations - %s"%v)
                    self.log.debug(
                        "%s: %f -- %r" % (event_name, elapsed, callback))

    def get(self, event_name):
        return self.__events[event_name]

    def list_events(self):
        return self.__events.keys()


