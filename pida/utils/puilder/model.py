
# Very basic build system. Designed to be friendly for UI generation.

from simplejson import dumps, loads


class Build(object):
    """A single build file"""
    def __init__(self):
        self.targets = []
        self.options = {}

    def for_serialize(self):
        return {
            'targets': [t.for_serialize() for t in self.targets],
            'options': self.options,
        }

    @classmethod
    def from_serialize(cls, data):
        b = Build()
        for d in data['targets']:
            b.targets.append(Target.from_serialize(d))
        b.options.update(data['options'])
        return b

    @classmethod
    def loads(cls, s):
        return cls.from_serialize(loads(s))

    @classmethod
    def loadf(cls, filename):
        f = open(filename)
        s = cls.loads(f.read())
        f.close()
        return s

    def dumps(self):
        return dumps(self.for_serialize(), sort_keys=False, indent=2)

    def dumpf(self, filename):
        f = open(filename, 'w')
        f.write(self.dumps())
        f.close()

    def create_new_target(self, name='', actions=(), dependencies=()):
        t = Target()
        t.name = name
        t.actions = list(actions)
        t.dependencies = list(dependencies)
        self.targets.append(t)
        return t

class Dependency(object):

    def __init__(self):
        self.name = ''

    def for_serialize(self):
        return self.name

    @classmethod
    def from_serialize(cls, s):
        d = Dependency()
        d.name = s
        return d

class Target(object):
    """A single target"""

    def __init__(self):
        self.name = ''
        self.actions = []
        self.dependencies = []

    def for_serialize(self):
        return {
            'actions': [a.for_serialize() for a in self.actions],
            'dependencies': [d.for_serialize() for d in self.dependencies],
            'name': self.name,
        }

    @classmethod
    def from_serialize(cls, data):
        t = Target()
        t.name = data['name']
        for act in data.get('actions', ()):
            t.actions.append(Action.from_serialize(act))
        for dep in data.get('dependencies', ()):
            t.dependencies.append(Dependency.from_serialize(dep))
        return t

    def create_new_action(self):
        act = Action()
        act.type = 'shell'
        self.actions.append(act)
        return act

    def create_new_dependency(self, name):
        dep = Dependency()
        dep.name = name
        self.dependencies.append(dep)
        return dep


    @property
    def action_count(self):
        return len(self.actions)

    def __str__(self):
        return self.name


class Action(object):
    """A single action"""

    def __init__(self):
        self.type = ''
        self.value = ''
        self.options = {}

    def for_serialize(self):
        return {
            'type': self.type,
            'value': self.value,
            'options': self.options,
        }

    @classmethod
    def from_serialize(cls, data):
        a = Action()
        a.type = data['type']
        a.value = data['value']
        a.options = data.get('options', {})
        return a


action_types = [
    ('Shell Command', 'shell'),
    ('Python Script', 'python'),
    ('External Build', 'external')
]


t = dict(
    targets = [
        dict(
            name = 'test',
            actions = [
                dict(type='shell', value='blah', options={})
            ],
            dependencies = ['moo'],
        )
    ],
    options = {}
)

def get_test_build():
    json = dumps(t, sort_keys=True, indent=4)
    return Build.loads(json)

def test_basic():
    json = dumps(t, sort_keys=True, indent=4)


    back = Build.loads(json)
    assert back.dumps() == json
    raise

if __name__ == '__main__':
    b = get_test_build()
    b.options['name'] = 'foo'
    b.targets[0].create_new_dependency('moo')
    print b.dumps()
