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
from pida.utils.languages import (LANG_COMPLETER_TYPES,
    LANG_VALIDATOR_TYPES, LANG_VALIDATOR_SUBTYPES, LANG_PRIO,
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

# class SkeletonEventsConfig(EventsConfig):
#
#     def subscribe_all_foreign(self):
#         self.subscribe_foreign('buffer', 'document-changed',
#                     self.on_document_changed)
#
#     def on_document_changed(self, document):
#         pass
#
#
# class SkeletonFeaturesConfig(FeaturesConfig):
#
#     def subscribe_all_foreign(self):
#         pass
#
#
# class SkeletonOptionsConfig(OptionsConfig):
#
#     def create_options(self):
#         self.create_option(
#             'Skeleton_for_executing',
#             _('Skeleton Executable for executing'),
#             str,
#             'Skeleton',
#             _('The Skeleton executable when executing a module'),
#         )
#
#
# class SkeletonActionsConfig(ActionsConfig):
#
#     def create_actions(self):
#         self.create_action(
#             'execute_Skeleton',
#             TYPE_NORMAL,
#             _('Execute Skeleton Module'),
#             _('Execute the current Skeleton module in a shell'),
#             gtk.STOCK_EXECUTE,
#             self.on_Skeleton_execute,
#         )
#
#     def on_Skeleton_execute(self, action):
#         #self.svc.execute_current_document()
#         pass

SUBTYPE_MAPPING = {
'W0511': LANG_VALIDATOR_SUBTYPES.FIXME,
'W0622': LANG_VALIDATOR_SUBTYPES.REDEFINED,
'W0611': LANG_VALIDATOR_SUBTYPES.UNUSED,
'W0612': LANG_VALIDATOR_SUBTYPES.UNUSED,
'E1101': LANG_VALIDATOR_SUBTYPES.UNDEFINED,
'W0201': LANG_VALIDATOR_SUBTYPES.UNDEFINED,
'W0212': LANG_VALIDATOR_SUBTYPES.PROTECTION,
'W0703': LANG_VALIDATOR_SUBTYPES.DANGEROUS,
'W0107': LANG_VALIDATOR_SUBTYPES.UNUSED,

}


class PythonError(ValidationError, Log):
    """
    Validator class for PyLint errrors
    """
    def get_markup(self):
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
        if self.type_ == LANG_VALIDATOR_TYPES.ERROR:
            typec = self.lookup_color('pida-val-error')
        elif self.type_ == LANG_VALIDATOR_TYPES.INFO:
            typec = self.lookup_color('pida-val-info')
        elif self.type_ == LANG_VALIDATOR_TYPES.WARNING:
            typec = self.lookup_color('pida-val-warning')
        else:
            typec = self.lookup_color('pida-val-def')
        if typec:
            typec = typec.to_string()
        else:
            linecolor = "black"
        linecolor = self.lookup_color('pida-lineno')
        if linecolor:
            linecolor = linecolor.to_string()
        else:
            linecolor = "black"
        markup = ("""<tt><span color="%(linecolor)s">%(lineno)s</span> </tt>"""
    """<span foreground="%(typec)s" style="italic" weight="bold">%(type)s</span"""
    """>:<span style="italic">%(subtype)s</span>  -  """
    """<span size="small" style="italic">%(msg_id)s</span>\n%(message)s""" % 
                      {'lineno':self.lineno,
                      'type':_(LANG_VALIDATOR_TYPES.whatis(self.type_).capitalize()),
                      'subtype':_(LANG_VALIDATOR_SUBTYPES.whatis(
                                    self.subtype).capitalize()),
                      'message':message_string,
                      'linecolor': linecolor,
                      'typec': typec,
                      'msg_id': self.msg_id
                      })
        return markup
    markup = property(get_markup)


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
            ty = LANG_VALIDATOR_TYPES.INFO
            sty = LANG_VALIDATOR_SUBTYPES.UNKNOWN
        elif msg_id[0] == 'C':
            ty = LANG_VALIDATOR_TYPES.INFO
            sty = LANG_VALIDATOR_SUBTYPES.BADSTYLE
        elif msg_id[0] == 'R':
            ty = LANG_VALIDATOR_TYPES.WARNING
            sty = LANG_VALIDATOR_SUBTYPES.BADSTYLE
        elif msg_id[0] == 'W':
            ty = LANG_VALIDATOR_TYPES.WARNING
            sty = LANG_VALIDATOR_SUBTYPES.UNKNOWN
        elif msg_id[0] == 'E':
            ty = LANG_VALIDATOR_TYPES.ERROR
            sty = LANG_VALIDATOR_SUBTYPES.UNKNOWN
        elif msg_id[0] == 'F':
            ty = LANG_VALIDATOR_TYPES.FATAL
            sty = LANG_VALIDATOR_SUBTYPES.UNKNOWN
        else:
            ty = LANG_VALIDATOR_TYPES.UNKNOWN
            sty = LANG_VALIDATOR_SUBTYPES.UNKNOWN

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
                            type_ = ty,
                            subtype = sty,
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

    def get_validations(self):
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
