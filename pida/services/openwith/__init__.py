import glob

class OpenWithItem(object):

    def __init__(self, section=None):
        if section is not None:
            self.name = section['name']
            self.command = section['command']
            self.glob = section['glob']
            if section.has_key('terminal'):
                # the bad guy saves a boolean as text in openwith.ini but 
                # cannot restore it as a boolean later
                if (isinstance(section['terminal'], str)):
                    self.terminal = section['terminal'] == 'True'
                else:
                    self.terminal = section['terminal']
            else:
                # if ini is from an older version without terminal property
                self.terminal = True
        else:
            self.name = _('unnamed')
            self.command = ''
            self.glob = '*'
            self.terminal = True

    def as_dict(self):
        return dict(
            name=self.name,
            command=self.command,
            glob=self.glob,
            terminal=self.terminal,
        )

    def match(self, file_name):
        if file_name is None:
            return False
        return glob.fnmatch.fnmatch(file_name, self.glob)
