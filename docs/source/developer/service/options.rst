
Service Options
===============

Options are currently stored in the GConf database. They are registered at
activation time of the service. Each service has its own directory in the GConf
database at /apps/pida/service_name. On registering the options, if they do not
exist, they are set to the default value.

Service options are defined in the service's OptionsConfig. This class should be
the options_config attribute of the service class, and should subclass
pida.options.OptionsConfig.

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
                OTypeString,
                'default_value',
                'A string describing the option',
            )


    class MyService(Service):

        options_config = MyServiceOptions


