# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

# stdlib
import sys, os.path 

from threading import Semaphore
import thread

# PIDA Imports

# core
from pida.core import environment
#from pida.core.service import Service
#from pida.core.events import EventsConfig
#from pida.core.actions import ActionsConfig, TYPE_NORMAL
from pida.core.options import OptionsConfig
from pida.core.log import Log

from pida.core.languages import (LanguageService, Validator, External)
from pida.utils.languages import (LANG_PRIO,
   Definition, Suggestion, Documentation, ValidationError)

# locale
from pida.core.locale import Locale
locale = Locale('skeleton')
_ = locale.gettext

# log
import logging
log = logging.getLogger('python_lint')

try:
    #import pylint
    from pylint.reporters import BaseReporter
    from pylint.lint import PyLinter
    from pylint.interfaces import IReporter
    from pylint.utils import MSG_TYPES, get_module_and_frameid

except ImportError:
    pylint = None
    BaseReporter = object


SUBTYPE_MAPPING = {
    'W0511': 'fixme',
    'W0622': 'redefined',
    'W0611': 'unused',
    'W0612': 'unused',
    'E1101': 'undefined',
    'W0201': 'undefined',
    'W0212': 'protection',
    'W0703': 'dangerous',
    'W0107': 'unused',
}


class PythonError(ValidationError, Log):
    """
    Validator class for PyLint errrors
    """
    def markup_args(self):
        if self.message_args:
            try:
                if isinstance(self.message_args, (list, tuple)):
                    args = [('<b>%s</b>' % arg) for arg in self.message_args]
                    message_string = self.message % tuple(args)
                else:
                    args = '<b>%s</b>' % self.message_args
                    message_string = self.message % args
            except TypeError, e:
                self.log.warning("Can't convert arguments %s : %s" %(
                                    self.message, self.message_args))
                message_string = self.message
        else:
            message_string = self.message
        mapping = ValidationError.markup_args(self)
        mapping['message'] = message_string
        return mapping

from logilab.common.ureports import TextWriter
from logilab.common.textutils import get_csv
# import thread

class PidaLinter(PyLinter, Log):

    def __init__(self, *args, **kwargs):
        self.sema = Semaphore(0)
        self._output = []
        self.running = True
        self._plugins = []
        pylintrc = kwargs.pop('pylintrc', None)
        super(PidaLinter, self).__init__(*args, **kwargs)
        #self.load_plugin_modules(self._plugins)
        from pylint import checkers
        checkers.initialize(self)

        #self._rcfile = 
        gconfig = os.path.join(
                    environment.get_plugin_global_settings_path('python_lint'),
                    'pylintrc')
        if os.path.exists(gconfig):
            self.read_config_file(gconfig)
        if pylintrc and os.path.exists(pylintrc):
            self.read_config_file(pylintrc)
        config_parser = self._config_parser
        if config_parser.has_option('MASTER', 'load-plugins'):
            plugins = get_csv(config_parser.get('MASTER', 'load-plugins'))
            self.load_plugin_modules(plugins)
        try:
            self.load_config_file()
        except Exception, e:
            log.exception(e)
            log.error(_("pylint couldn't load your config file: %s") %e)
        self.set_reporter(kwargs['reporter'])
        # now we can load file config and command line, plugins (which can
        # provide options) have been registered
        #self.load_config_file()

    def check(self, *args, **kwargs):
        self._output = []
        self.running = True
        try:
            super(PidaLinter, self).check(*args, **kwargs)
        except:
            self.log.debug('Error in PidaLinter check')

        self.running = False
        # for ensurance :-)
        self.sema.release()
        self.sema.release()

    def add_message(self, msg_id, line=None, node=None, args=None):
        """add the message corresponding to the given id.

        If provided, msg is expanded using args
        
        astng checkers should provide the node argument, raw checkers should
        provide the line argument.
        """
        if line is None and node is not None:
            line = node.fromlineno#lineno or node.statement().lineno
            #if not isinstance(node, Module):
            #    assert line > 0, node.__class__
        # should this message be displayed
        if not self.is_message_enabled(msg_id, line):
            return        
        # update stats
        if msg_id[0] == 'I':
            ty = 'info'
            sty = 'unknown'
        elif msg_id[0] == 'C':
            ty = 'info'
            sty = 'badstyle'
        elif msg_id[0] == 'R':
            ty = 'info'
            sty = 'badstyle'
        elif msg_id[0] == 'W':
            ty = 'warning'
            sty = 'unknown'
        elif msg_id[0] == 'E':
            ty = 'error'
            sty = 'unknown'
        elif msg_id[0] == 'F':
            ty = 'fatal'
            sty = 'unknown'
        else:
            ty = 'unknown'
            sty = 'unknown'

        #msg_cat = MSG_TYPES[msg_id[0]]
        #self.stats[msg_cat] += 1
        #self.stats['by_module'][self.current_name][msg_cat] += 1
        #try:
        #    self.stats['by_msg'][msg_id] += 1
        #except KeyError:
        #    self.stats['by_msg'][msg_id] = 1
        if SUBTYPE_MAPPING.has_key(msg_id):
            sty = SUBTYPE_MAPPING[msg_id]

        msg = self._messages[msg_id].msg
        # expand message ?
        #if args:
        #    msg %= args
        # get module and object
        if node is None:
            module, obj = self.current_name, ''
            path = self.current_file
        else:
            module, obj = get_module_and_frameid(node)
            path = node.root().file
        # add the message
        cmsg = PythonError( message = msg,
                            level = ty,
                            kind = sty,
                            filename = path,
                            message_args = args or (),
                            lineno = line or 1,
                            msg_id = msg_id
                          )
        self._output.append(cmsg)
        self.sema.release()
        #self._output.append((msg_id, (path, module, obj, line or 1), msg))
        #self.reporter.add_message(msg_id, (path, module, obj, line or 1), msg)

    def set_current_module(self, modname, filepath=None):
        """set the name of the currently analyzed module and
        init statistics for it
        """
        if not modname and filepath is None:
            self.running = False
        return super(PidaLinter, self).set_current_module(modname, filepath)

class PidaReporter(BaseReporter):
    """reports messages and layouts in plain text
    """
    
    __implements__ = IReporter
    extension = 'txt'
    
    def __init__(self, validator, output=sys.stdout):
        BaseReporter.__init__(self, output)
        self._modules = {}

    def add_message(self, msg_id, location, msg):
        pass

    def _display(self, layout):
        pass
        #print "DISPLAY"
        #"""launch layouts display"""
        #print >> self.out 
        #TextWriter().format(layout, self.out)




class PylintValidator(Validator):

    priority = LANG_PRIO.VERY_GOOD
    name = "pylint"
    plugin = "python_lint"
    description = _("A very good customizable, but slow validator")

    def __init__(self, *args, **kwargs):
        self.reporter = PidaReporter(self)
        Validator.__init__(self, *args, **kwargs)

    def run(self):
        if self.document.filename:
            pylintrc = None
            if self.document.project:
                pylintrc = os.path.join(
                            self.document.project.get_meta_dir('python_lint'),
                            'pylintrc')

            self.linter = PidaLinter(options=(), reporter=self.reporter, option_groups=(),
                 pylintrc=pylintrc)
            #from pylint import checkers
            #checkers.initialize(self.linter)

            thread.start_new_thread(self.linter.check, ((self.document.filename,),))

            while True:
                self.linter.sema.acquire()
                if not self.linter.running and not len(self.linter._output):
                    return
                yield self.linter._output.pop()
        else:
            return

class PythonLintExternal(External):
    validator = PylintValidator


class PythonLintService(LanguageService):

    language_name = 'Python'
    validator_factory = PylintValidator

    external = PythonLintExternal
#    features_config = SkeletonFeaturesConfig
#    actions_config = SkeletonActionsConfig
#    options_config = SkeletonOptionsConfig
#    events_config = SkeletonEventsConfig

    def pre_start(self):
        try:
            import pylint
        except ImportError:
            self.notify_user('You need to install pylint')
            raise


# Required Service attribute for service loading
Service = PythonLintService



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
