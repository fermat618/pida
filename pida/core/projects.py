"""Project features for PIDA"""

import os
from weakref import proxy

from pida.utils.configobj import ConfigObj

# locale
from pida.core.locale import Locale
locale = Locale('pida')
_ = locale.gettext


class ProjectControllerMananger(object):
    """
    Manager to know about all controller types, and load them for projects.

    Controller types are registered with the manager, and provided to projects
    as they are loaded. This object knows about the boss, and allows the boss to
    be given to the projects and controllers.
    """

    def __init__(self, boss=None):
        self.boss = boss
        self._controller_types = {}

    def register_controller(self, controller):
        # XXX: fix to raise error if already exists
        self._controller_types[controller.name] = controller

    def get_controller_type(self, name):
        return self._controller_types.get(name, None)

    def create_project(self, project_file):
        project = Project(self, project_file)
        return project


class Project(object):
    """
    A PIDA project.

    This is essentially a bag for the options and controllers contained by the
    project.
    """

    def __init__(self, manager, project_file):
        self.manager = manager
        self.boss = self.manager.boss
        self.project_file = project_file
        self.source_directory = os.path.dirname(self.project_file)
        self.name = os.path.basename(self.source_directory)
        self._create_options()
        self._create_controllers()

    def _create_controllers(self):
        self.controllers = []
        for section in self.options.sections:
            controller_name = self.options.get(section).get('controller', None)
            if controller_name is not None:
                controller_type = self.manager.get_controller_type(controller_name)
                if controller_type is not None:
                    self.controllers.append(controller_type(self, section))
                else:
                    self.boss.log.debug(_('no controller type for %s') %
                                        controller_name)
            else:
                self.boss.log.debug(_('no controller defined for %s') % section)

    def _create_options(self):
        self.options = ConfigObj(self.project_file)

    def add_controller(self, controller_type, section_name = None):
        # first get a free section name
        if section_name is None:
            cnum = 0
            for controller in self.controllers:
                if controller.name == controller_type.name:
                    cnum += 1
            section_name = '%s.%s' % (controller_type.name, cnum)
        self.options[section_name] = {}
        self.options[section_name]['controller'] = controller_type.name
        controller = controller_type(self, section_name)
        if not len(self.controllers):
            self.options[section_name]['default'] = 'True'
        self.controllers.append(controller)
        self.save()
        return controller

    def remove_controller(self, controller):
        self.controllers.remove(controller)
        del self.options[controller.config_section]
        default = self.get_default_controller()
        if default is None:
            if len(self.controllers):
                self.controllers[0].default = True
        self.save()

    def get_default_controller(self):
        for controller in self.controllers:
            if controller.default:
                return controller

    def save(self):
        self.options.write()

    def _get_actions(self):
        actions = []
        for controller in self.controllers:
            actions.extend(controller.get_actions())
        return actions

    def _get_actions_of_kind(self, kind):
        actions = []
        for controller in self.controllers:
            actions.extend([(controller, action) for action in
                controller.get_actions_of_kind(kind)])
        return actions

    def set_option(self, section, name, value):
        self.options[section][name] = value
        self.options.write()

    def get_markup(self):
        return '<b>%s</b>\n%s' % (self.name, self.source_directory)

    markup = property(get_markup)

    def save_section(self, section_name, section):
        self.options[section_name] = section
        self.save()

    def get_section(self, section_name):
        return self.options.get(section_name, None)



class ProjectKeyDefinition(object):
    """
    Project attribute definition.

    An attribute shoulf have a name, a label and whether it is required by the
    project's execute action in order to perform its task.
    """

    def __init__(self, name, label, required=False):
        self.name = name
        self.label = label
        self.required = required


class ProjectKeyItem(object):
    """
    Helper to allow project attributes to be displayed.

    Changing the value attribute will cause the project that the attribute is
    part of to be updated and saved. This is useful for the kiwi objectlist.
    """

    def __init__(self, definition, project, controller):
        self.required = definition.required
        if self.required:
            self.label = '<b>%s</b>' % definition.label
        else:
            self.label = definition.label
        self.name = definition.name
        self._project = project
        self._controller = controller

    def get_value(self):
        return self._controller.get_option(self.name)

    def set_value(self, value):
        self._controller.set_option(self.name, value)
        self._project.save()

    value = property(get_value, set_value)


class ProjectController(object):
    """
    Project Controller.

    A project may have any number of controllers. Each type of controller should
    override the execute method, which will be called when the controller is
    executed. The attributes list is a list of options that can be graphically
    changed by the user. Each attribute should be of type ProjectKeyDefinition.
    The controller should also define a name (a unique key) and a label (for
    user interface display).
    """

    name = ''

    label = ''

    attributes = [
        ProjectKeyDefinition('cwd', _('Working Directory'), False),
        ProjectKeyDefinition('env', _('Environment Variables'), False),
    ]

    def __init__(self, project, config_section):
        self.project = proxy(project)
        self.boss = self.project.boss
        self.config_section = config_section
        self._default = False

    def execute(self):
        """Execute this controller, for overriding"""

    def get_options(self):
        return self.project.options.get(self.config_section)

    def get_option(self, name):
        return self.get_options().get(name, None)

    def set_option(self, name, value):
        if self.get_options() is not None:
            self.get_options()[name] = value
        else:
            self.boss.log.debug('Deleted controller attempting to set value')

    def get_project_option(self, name):
        return self.project.options.get(name, None)

    def execute_commandargs(self, args, env=None, cwd=None):
        #TODO: Bad dependency
        self.boss.cmd('commander', 'execute',
            commandargs=args,
            env=env or self.get_env(),
            cwd=cwd or self.get_cwd(),
            title=self.config_section,
            icon='gtk-execute',
        )

    def execute_commandline(self, command, env=None, cwd=None):
        self.boss.cmd('commander', 'execute',
            commandargs=['bash', '-c', command],
            env=env or self.get_env(),
            cwd=cwd or self.get_cwd(),
            title=self.config_section,
            icon='gtk-execute',
        )

    def create_key_items(self):
        for attr in self.attributes:
            yield ProjectKeyItem(attr, self.project, self)

    def get_markup(self):
        return ('<b>%s</b>\n<span foreground="#0000c0">%s</span>' %
            (self.config_section, self.label))

    markup = property(get_markup)

    def set_default(self, value):
        aval = (value and 'True') or ''
        self.set_option('default', aval)
        self.project.save()

    def get_default(self):
        if self.get_option('default') is None:
            self.set_option('default', '')
        return bool(self.get_option('default'))

    default = property(get_default, set_default)

    def get_cwd(self):
        cwd = self.get_option('cwd')
        if cwd is None:
            return self.project.source_directory
        elif os.path.isabs(cwd):
            return cwd
        else:
            return os.path.join(self.project.source_directory, cwd)

    def get_env(self):
        env = self.get_option('env')
        if env is None:
            return []
        else:
            return env.split()



