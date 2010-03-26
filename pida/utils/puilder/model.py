
# Very basic build system. Designed to be friendly for UI generation.

from pida.utils.serialize import dumps, loads

def dump(data):
    return dumps(data, sort_keys=False, indent=2, separators=(',',':'))

class Build(object):
    """A single build file"""
    def __init__(self):
        self.targets = []
        self.options = {}

    def for_serialize(self):
        sopt = self.options.copy()
        if 'default' in sopt:
            # we only save the target name as default option, not the reference
            try:
                sopt['default'] = sopt['default'].name
            except:
                # this should happen but may happen due data inconsistency.
                # better remove
                if 'default' in sopt:
                    del sopt['default']
        return {
            'targets': [t.for_serialize() for t in self.targets],
            'options': sopt,
        }

    @classmethod
    def from_serialize(cls, data):
        b = Build()
        for d in data['targets']:
            b.targets.append(Target.from_serialize(d))
        b.options.update(data['options'])
        if 'default' in b.options:
            b.default = b.options['default']
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
        return dump(self.for_serialize())

    def dumpf(self, filename):
        f = open(filename, 'w')
        f.write(self.dumps())
        f.close()

    def create_new_target(self, name='', actions=()):
        t = Target()
        t.name = name
        t.actions = list(actions)
        #t.dependencies = list(dependencies)
        self.targets.append(t)
        return t

    def get_default(self):
        if 'default' in self.options:
            return self.options['default']
        else:
            # if not a default is defined, we return a target named default
            # as a fallback
            for target in self.targets:
                if target.name == "default":
                    return target

    def set_default(self, target):
        if not isinstance(target, Target) :
            for ctar in self.targets:
                ctar.is_default = False
                if ctar.name == target:
                    ctar.is_default = True
                    target = ctar
        else:
            for ctar in self.targets:
                ctar.is_default = target is ctar

        if target is None:
            try:
                del self.options['default']
            except KeyError: 
                pass
        else:
            self.options['default'] = target

    default = property(get_default, set_default)

class Target(object):
    """A single target"""

    def __init__(self):
        self.name = ''
        self.is_default = False
        self.actions = []
        #self.dependencies = []

    def for_serialize(self):
        return {
            'actions': [a.for_serialize() for a in self.actions],
            #'dependencies': [d.for_serialize() for d in self.dependencies],
            'name': self.name,
        }

    @classmethod
    def from_serialize(cls, data):
        t = Target()
        t.name = data.get('name', 'unnamed')
        for act in data.get('actions', ()):
            t.actions.append(Action.from_serialize(act))
        return t

    def create_new_action(self):
        act = Action()
        act.type = 'shell'
        self.actions.append(act)
        return act


    @property
    def action_count(self):
        return len(self.actions)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Target %s>' %self.name

class Action(object):
    """A single action"""
    
    def __repr__(self):
        return '<puild-action %s %r>' % (self.type, self.value)

    def __init__(self):
        self.type = ''
        self.value = ''
        self.options = {
            'ignore_fail': False,
        }

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
    ('shell', 'Shell Command'),
    ('python', 'Python Script'),
    ('target', 'Existing Target'),
    ('external', 'External Build')
]



if __name__ == '__main__':
    b = get_test_build()
    b.options['name'] = 'foo'
    #b.targets[0].create_new_dependency('moo')
    print b.dumps()

