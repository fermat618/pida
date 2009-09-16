# -*- coding: utf-8 -*- 
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""


import os
import threading, thread
import subprocess
import gobject
from . import ostools

class AsyncTask(object):
    """
    AsyncTask is used to help you perform lengthy tasks without delaying
    the UI loop cycle, causing the app to look frozen. It is also assumed
    that each action that the async worker performs cancels the old one (if
    it's still working), thus there's no problem when the task takes too long.
    You can either extend this class or pass two callable objects through its
    constructor.
    
    The first on is the 'work_callback' this is where the lengthy
    operation must be performed. This object may return an object or a group
    of objects, these will be passed onto the second callback 'loop_callback'.
    You must be aware on how the argument passing is done. If you return an
    object that is not a tuple then it's passed directly to the loop callback.
    If you return `None` no arguments are supplied. If you return a tuple
    object then these will be the arguments sent to the loop callback.
    
    The loop callback is called inside Gtk+'s main loop and it's where you
    should stick code that affects the UI.
    """
    def __init__(self, work_callback=None, loop_callback=None, daemon=True):
        self.counter = 0
        
        self.daemon = daemon

        if work_callback is not None:
            self.work_callback = work_callback
        if loop_callback is not None:
            self.loop_callback = loop_callback
    
    def start(self, *args, **kwargs):
        """
        Please note that start is not thread safe. It is assumed that this
        method is called inside gtk's main loop there for the lock is taken
        care there.
        """
        args = (self.counter,) + args
        thread = threading.Thread(
                target=self._work_callback,
                args=args, kwargs=kwargs
                )
        thread.setDaemon(self.daemon)
        thread.start()
    
    def work_callback(self):
        pass
    
    def loop_callback(self):
        pass
    
    def _work_callback(self, counter, *args, **kwargs):
        ret = self.work_callback(*args, **kwargs)
        if self.loop_callback != AsyncTask.loop_callback:
            # we don't have to jump into the gtk thread if loop_callback
            # was not set
            gobject.idle_add(self._loop_callback, (counter, ret))

    def _loop_callback(self, vargs):
        counter, ret = vargs
        if counter != self.counter:
            return
        
        if ret is None:
            ret = ()
        if not isinstance(ret, tuple):
            ret = (ret,)

        self.loop_callback(*ret)


class GeneratorTask(AsyncTask):
    """
    The diference between this task and AsyncTask is that the 'work_callback'
    returns a generator. For each value the generator yields the loop_callback
    is called inside Gtk+'s main loop.
    
    @work_callback: callback that returns results
    @loop_callback: callback inside the gtk thread
    @priority: gtk priority the loop callback will have
    @pass_generator: will pass the generator instance as generator_task to the 
                     worker callback. This is usefull to test and give up work 
                     when the generator task was stopped.

    A simple example::

        def work():
            for i in range(10000):
                yield i

        def loop(val):
            print val

        gt = GeneratorTask(work, loop)
        gt.start()
        import gtk
        gtk.main()
    """
    def __init__(self, work_callback, loop_callback, complete_callback=None,
                 priority=gobject.PRIORITY_DEFAULT_IDLE,
                 pass_generator=False):
        AsyncTask.__init__(self, work_callback, loop_callback)
        self.priority = priority
        self._complete_callback = complete_callback
        self._pass_generator = pass_generator

    def _work_callback(self, counter, *args, **kwargs):
        self._stopped = False
        if self._pass_generator:
            kwargs = kwargs.copy()
            kwargs['generator_task'] = self
        for ret in self.work_callback(*args, **kwargs):
            if self._stopped:
                thread.exit()
            gobject.idle_add(self._loop_callback, (counter, ret),
                             priority=self.priority)
        if self._complete_callback is not None:
            gobject.idle_add(self._complete_callback,
                             priority=self.priority)

    def stop(self):
        self._stopped = True

    @property
    def is_stopped(self):
        return self._stopped


class GeneratorSubprocessTask(GeneratorTask):
    """
    A Generator Task for launching a subprocess

    An example (inside thread_inited gtk main loop):
        def output(line):
            print line
        task = GeneratorSubprocessTask(output)
        task.start(['ls', '-al'])
    """
    def __init__(self, stdout_callback, complete_callback=None):
        GeneratorTask.__init__(self, self.start_process, stdout_callback,
                               complete_callback)

    def start_process(self, commandargs, **spargs):
        self._process = subprocess.Popen(
            commandargs,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True,
            **spargs
        )
        for line in self._process.stdout:
            yield line.strip()

    def stop(self):
        GeneratorTask.stop(self)
        try:
            if hasattr(self, '_process'):
                ostools.kill_pid(self._process.pid)
        except OSError:
            pass



def locked(lockname): 
    '''
    Call this decorator with the name of the lock. The decorated method
    will be wrapped with an acquire()/lock().

    Example of usage::
        
        import threading
        
        class Foo(object) :
            def __init__(self):
                self.lock = threading.Lock()
                
            @locked("lock")
            def meth1(self):
                self.critical_value = 1

            @locked("lock")
            def meth2(self):
                self.critical_value = 2
                return self.critical_value
    
    Both 'meth1' and 'meth2' will be wrapped with a 'lock.acquire()'
    and a 'lock.release()'.
    '''

def locked(lock_name):
    """This is a factory of decorators. The decorator
    wraps an acquire() and release() around the decorated
    method. The lock name is the name of the attribute
    containing the lock."""
    
    if not isinstance(lock_name, basestring):
        raise TypeError("'lock_name' must be a string")
    
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            lock = getattr(self, lock_name)
            lock.acquire()

            # Make sure an exception does not break
            # the lock
            try:
                ret = func(self, *args, **kwargs)
            except:
                lock.release()
                raise
            
            lock.release()
            return ret

        return wrapper

    return decorator

def gcall(func, *args, **kwargs):
    """
    Calls a function, with the given arguments inside Gtk's main loop.
    Example::
        gcall(lbl.set_text, "foo")

    If this call would be made in a thread there could be problems, using
    it inside Gtk's main loop makes it thread safe.
    """
    return gobject.idle_add(lambda: (func(*args, **kwargs) or False))


