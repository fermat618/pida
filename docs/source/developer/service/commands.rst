================
Service Commands
================

Commands are the external interface for a service. This interface is specifically provided to other services for use of service activities.

Defining Commands
=================

Commands are defined as methods on the `commands_config` attribute of the Service class. This attribute should reference a subclass of `pida.core.commands.CommandsConfig` class. Any method defined on that class will be available as a command on the service.


Calling service commands
========================

Commands are called on a service using the `cmd` method of a service. Calling commands on other services must be performed through the Boss' `cmd` method which takes as an additional parameter then name of the target service.

For example, execute a shell from a service::

    self.boss.cmd(
        'commander',        #<1>
        'execute_shell',    #<2>
    )

1. The target service name
2. The target service command

Using arguments on service commands
===================================

All arguments to service commands must be passed as keyword arguments. Because
of this, they can be passed in any order after the servicename, and commandname
parameters.

For example, execute a shell from a service starting in an explicit directory::

    self.boss.cmd(
        'commander',
        'execute_shell',
        cwd = '/',
    )

