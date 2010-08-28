
Service Views
=============

Service views are almost anything that appears visually in PIDA (apart from the
main toolbar and menubar). All of these views belong to a service.


Creating Views
--------------

Views may be designed in Glade3, or in pure :ref:`PyGTK`.
Each method of view creation has its advantages and disadvantages,
and these are discussed below.

.. note::

  the sematics of views are affected by the recent pygtkhelpers refactoring


Glade3 Views
------------

Views created with Glade3 have the following advantages:

    - Better maintainability
    - Automatic signal callback connection

The glade-file itself should be places in the directory glade/ in the service
directory, and should be named appropriately so as not to conflict with any
other service glade file. The extension `.glade` is preferred. So, for example a
well named glade file is `project-properties-editor.glade`.

This glade file is used by subclassing `pida.ui.views.PidaGladeView` and setting
the gladefile attribute on the class, for example for the glade file above::

    from pida.ui.views import PidaGladeView

    class ProjectPropertiesView(PidaGladeView):
        """A view for project properties"""

        gladefile = 'project-properties-editor'

.. note::
The glade file attribute omits the extension part of the file name.

The glade-file should contain a single top-level container (usually a
`gtk.Window`), and this *must have the same name as the glade file (without
extension*.

The widget inside this container will be taken out of the Window and
incorporated into Pida's view.

All widgets in the glade view, are attached to the view instances namespace, so
that they can be accessed from the instance, for example if there is a text entry called
`name_entry`, the attribute `self.name_entry` or `my_view.name_entry` would
reference that entry.

Signals of items in the glade view are automatically connected if you provide
the correct method on the glade view. These methods are named as
`on_<widget_name>__<signal_name>`. For example, if there is a button on the
view called `close_button`, and you wish to connect to it's `clicked` signal,
you would provide the following method in order to automatically connect the
signal for the widget::

    def on_close_button__clicked(self, button):
        print '%s was clicked!' % button

Pure PyGTK Views
----------------

These views should subclass `pida.ui.views.PidaView` and should create the
necessary widgets by overriding the create_ui method. The widgets can be added
to the view by using the `view.add_main_widget(widget, expand=True, fill=True)`.
The widgets will be added to the top-level VBox in the view.

There is no signal autoconnection, and widgets behave exactly as if they had
been created with PyGTK in any other circumstance.

Instantiating views
-------------------

The service can instantiate its views at any time. They should pass the instance
of the service as the first parameter to the View constructor. The service will
then be stored as the `svc` attribute on the view.


Adding Views to PIDA
--------------------

Views are displayed at runtime by calling the 'window' service's command
'add_view'. The required paned must be passed as well as the view itself.

The paned attribute to the command should be one of:

    - `Buffer`
    - `Plugin`
    - `Terminal`

The buffer paned is the left sidebar, the plugin paned is the right sidebar, and
the terminal paned is the bottom bar. In general the guidelines for which paned
to add views to are:

    - Permanent views should be added to the Buffer paned
    - Views relating to the current document should be added to the Buffer or
      Plugin paned
    - Configuration or property views should be added to the Plugin paned
    - Multiple view (eg terminal emulators, diffs, and web browsers), or those
      with a lot of data should be added to the Terminal paned.

An example of adding a view of type `MyServiceView` to the Terminal paned is as
follows::

    # Override the start method as a hook to when the service starts
    def start(self):
        view = MyServiceView(self)
        self.boss.cmd('window', 'add_view', paned='Terminal', view=view)

Numerous other examples are available in almost every service in `pida.services`.

View icons and labels
---------------------

View icons (the image displayed on the paned button) are referred to by their
stock ID, and set as a class attribute on the view `icon_name`. Similarly, the
text associating the icon is set as a class attribute on the view called
'label_text`.

Additionally, an `icon_name` and/or a `label_text` attribute can be passed to
the view constructor, and these will be displayed as the view's label and icon
when it is added to the PIDA main view.


Using custom pixmaps in services
--------------------------------

Any pixmap placed in the pixmaps directory in the service (`myservice/pixmaps`)
will automatically be added as a stock image and can be used by the service
using its name (without extension) for View icons or for gtk.Buttons or
gtk.Images or any other widget which take a stock_id as an argument.

