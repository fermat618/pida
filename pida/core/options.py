from pida.core.base import BaseConfig


class OptionItem(object):

    def __init__(self, group, name, label, rtype, default, doc):
        self.name = name
        self.label = label
        self.rtype = rtype
        self.doc = doc
        self.default = default
        self.value = default


class OptionsConfig(BaseConfig):

    def create(self):
        self._options = {}
        self.create_options()

    def create_options(self):
        """Create the options here"""

    def create_option(self, name, label, rtype, default, doc):
        opt = OptionItem(self, name, label, rtype, default, doc)
        self.add_option(opt)
        return opt

    def add_option(self, option):
        self._options[option.name] = option

    def get_option(self, optname):
        return self._options[optname]
