# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

# stdlib
import sys, compiler, os.path, keyword, re

# gtk
import gtk

# PIDA Imports

# core
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig, TYPE_NORMAL
from pida.core.options import OptionsConfig

from pida.core.languages import (LanguageService, Validator)
from pida.utils.languages import (LANG_COMPLETER_TYPES,
    LANG_VALIDATOR_TYPES, LANG_VALIDATOR_SUBTYPES, LANG_PRIO,
   Definition, Suggestion, Documentation, ValidationError)

# locale
from pida.core.locale import Locale
locale = Locale('skeleton')
_ = locale.gettext

try:
    import pylint
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

class PythonError(ValidationError):
    def get_markup(self):
        if self.message_args:
            if isinstance(self.message_args, (list, tuple)):
                args = [('<b>%s</b>' % arg) for arg in self.message_args]
                message_string = self.message % tuple(args)
            else:
                args = '<b>%s</b>' % self.message_args
                message_string = self.message % args
                
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
    """>:<span style="italic">%(subtype)s</span>\n%(message)s""" % 
                      {'lineno':self.lineno, 
                      'type':_(LANG_VALIDATOR_TYPES.whatis(self.type_).capitalize()),
                      'subtype':_(LANG_VALIDATOR_SUBTYPES.whatis(
                                    self.subtype).capitalize()),
                      'message':message_string,
                      'linecolor': linecolor,
                      'typec': typec,
                      })
        return markup
    markup = property(get_markup)


from logilab.common.ureports import TextWriter
# import thread

class PidaLinter(PyLinter):
    def __init__(self, *args, **kwargs):
        self._output = []
        self.running = True
        return super(PidaLinter, self).__init__(*args, **kwargs)

    def check(self, *args, **kwargs):
        self._output = []
        self.running = True
        return super(PidaLinter, self).check(*args, **kwargs)

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
            ty = LANG_VALIDATOR_TYPES.WARNING
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
                            lineno = line or 1
                          )
        self._output.append(cmsg)
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
    
    def __init__(self, *args, **kwargs):
        self.reporter = PidaReporter(self)
        Validator.__init__(self, *args, **kwargs)

    def get_validations(self):
        if self.document.filename:
            self.linter = PidaLinter(options=(), reporter=self.reporter, option_groups=(),
                 pylintrc=None)
            from pylint import checkers
            checkers.initialize(self.linter)
            self.linter.check((self.document.filename,))
            while True:
                if not self.linter.running and not len(self.linter._output):
                    return
                if len(self.linter._output):
                    one = self.linter._output.pop()
                    yield one
                else:
                    yield
        else:
            return



class PythonLintService(LanguageService):

    language_name = 'Python'
    validator_factory = PylintValidator

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

    def start(self):
        pass
        
    def stop(self):
        pass


# Required Service attribute for service loading
Service = PythonLintService



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
