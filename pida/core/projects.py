"""Project features for PIDA"""

import os
from weakref import proxy

from configobj import ConfigObj


class ProjectControllerMananger(object):

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
                    print 'no controller type for %s' % controller_name
            else:
                print 'no controller defined for %s' % section

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

def project_action(kind):
    def project_action_decorator(f):
        f.__kind__ = kind
        f.__action__ = True
        return f
    return project_action_decorator


class ExecutionActionType(object):
    """A controller for execution"""

class BuildActionType(object):
    """A controller action for building"""

class TestActionType(object):
    """A controller action for testing"""

class ProjectKeyDefinition(object):

    def __init__(self, name, label, required=False):
        self.name = name
        self.label = label
        self.required = required

class ProjectKeyItem(object):

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

    name = ''

    keys = []

    label = ''

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
        self.get_options()[name] = value

    def get_project_option(self, name):
        return self.project.options.get(name, None)

    def execute_commandargs(self, args, cwd, env):
        #TODO: Bad dependency
        self.boss.cmd('commander', 'execute',
            commandargs=args,
            env=env,
            cwd=cwd,
        )

    def execute_commandline(self, command, cwd, env):
        self.boss.cmd('commander', 'execute',
            commandargs=['bash', '-c', command],
            env=env,
            cwd=cwd,
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



# an example controller



