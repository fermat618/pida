
Service Options
===============

Options are currently stored in json data files.
They are registered at activation time of the service.
Each service has its own config file within `~/.pida2`.
On registering the options, if they do notexist,
they are set to the default value.

Service options are defined in the service's OptionsConfig.
This class MUST be the options_config attribute of the service class,
and should subclass :class:`pida.options.OptionsConfig`.

The OptionsConfig has a method named create_options, which is called on service
activation. This method should contain the calls to create_option to create the
options. The signature for create_option is::

    create_option(name, label, type, default, documentation)

For example::

    class MyServiceOptions(OptionsConfig):

        def create_options(self):
            self.create_option(
                'myoption',
                'myoption label',
                str,
                'default_value',
                'A string describing the option',
            )


    class MyService(Service):

        options_config = MyServiceOptions


