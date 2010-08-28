
Service Events
==============

The events are asynchronous call back for the service. So any other service can
subscribe its call back to an event, and it will get called back once the event
occurs.

.. note::

  plugins should avoid publishing own services
  due to the lack of plugin dependencies




Events definition
-----------------

To create a new event, like earlier, you just need to create a new class
that you can call 'MyServiceEvents', and you bind it to your 'MyService'
class doing 'events_config = MyServiceEvents'::

    class MyServiceEvents(EventsConfig):
        def create_events(self):
            [...]
        def subscribe_foreign_events(self):
            [...]

    class MyService(Service):
        events_config = MyServiceEvents

So in that example code, you can notice the two methods you need to implement
to manage your own events. You have to define in create_events all the events
your service is about to use, and in subscribe_foreign_events all the events
from other services your service needs.


Create your own new events
--------------------------

So, once you have your 'EventsConfig' ready, you need to implement the
create_events method so you can have your own new events.::

        def create_events(self):
            self.publish('myevent')                     # (1)
            self.subscribe('myevent', self.on_myevent) # (2)
            self.publish('my_foreign_event')

        def on_myevent(self, param=None):                     # (3)
            print 'myevent receipt'
            if param != None:
                print 'with param:', param

Three steps are needed to create and use an event :

    (1) You call self.publish(event_name)e
    (2) You subscribe a new callback to the event you just made
    (3) You implement the new event's callback so it acts when it is emitted.


Subscribe to other services' events
-----------------------------------

We have seen how we can bind callbacks to events you created in
your own service. But you often need to interact with other services
as well. To do so, you need to implement the subscribe_foreign_events()
method the following way::

        def subscribe_all_foreign(self):
            self.subscribe_foreign('editor', 'started',
                                         self.on_editor_startup)

for each event you want to bind a call back, you need to call the
subscribe_foreign method. In the example above, when the editor
service launches the started event, self.on_editor_startup() gets called.::

    self.subscribe_foreign(service_name, event_name, callback)

where *serice_name* is the destination service, *event_name* the event to bind to,
*callback* the function to be called when the event is emitted.

Now suppose you want to give other services' programmers an event of your own 
service. To do so, you need to call create_event() in create_events() with the
name of your event (ie see 'my_foreign_event' above).

Then in the foreign service, in the subscribe_foreign_events() method you just
need to subscribe to the event::

    def subscribe_all_foreign(self):
        self.subscribe_foreign('myservice', 'my_foreign_event',
                                self.on_myservice_foreign_event)

and finally define your callback.


Emitting Events
---------------

Now you have defined and bound all your events in your service and all
you need is to emit them when you need them to be executed. Well, it's
fairly simple, just call the emit() method.

.. XXX outdated


.. code-block::

        [...]
        self.emit('myevent')
        self.emit('myevent', param='hello world')
        self.emit('my_foreign_event')
        [...]
        self.get_service('myservice').emit('myevent')
        self.get_service('myservice').emit('myevent', param='hello from some other place')
        self.get_service('myservice').emit('my_foreign_event')
        [...]

As you can see in the examples above, emit can be used in different contexts
and with or without parameters. As a rule, every event defined can be called
using the emit() method either from your own service (ie in 'MyService') or
from someone else's service (then you use get_service().emit()).

If your callback function needs parameters, you need to give the options to
the emit method. You can also use, as in the above example, non-mandatory 
parameters.

