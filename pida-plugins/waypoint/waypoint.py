# -*- coding: utf-8 -*-
"""
    :copyright: 2005-2008 by The PIDA Project
    :license: GPL 2 or later (see README/COPYING/LICENSE)
"""

# gtk
import gtk, gobject
import time

# PIDA Imports

# core
from pida.core.service import Service
from pida.core.events import EventsConfig
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.actions import ActionsConfig, TYPE_NORMAL, TYPE_MENUTOOL
from pida.core.options import OptionsConfig
from pida.core.pdbus import DbusConfig, EXPORT
from pida.core.document import Document

# locale
from pida.core.locale import Locale
locale = Locale('waypoint')
_ = locale.gettext


LEXPORT = EXPORT(suffix='buffer')

class WayPoint(object):
    """
    Represents a single point of the waypoint history
    """
    def __init__(self, document, line, time_=None):
        self.document = document
        self.line = line
        self.time = time_ or time.time()

    def __repr__(self):
        return '<WayPoint %s %s @ %s>' %(self.document, self.line, self.time)
    

class WayStack(list):
    """
    Object to stores the waypoint's
    """
    def __init__(self, threshold = 30, max_length = 30, timespan=8,
                       docswitch=False):
        """
        Makes a new instance of WayStack.
        
        :param threshold - lines that must be changed befor beeing a new point
        :max_length - max numbers of point in path
        """
        self.threshold  = threshold
        self.timespan = timespan
        self.max_length = max_length
        self.docswitch = docswitch
        self.current_point = None
        self._considered = []
        self._last_document = None
        self._last_line = None

    def notify_change(self, document, line, force=False, time_=None):
        """
        Adds the document waypoint to the 
        """
        # jumping in the history should not change it
        #for point in self:
        #    if point.document == document and point.line == line:
        #        return
        
        is_good = None

        wpoint = WayPoint(document, line, time_=time_)
        ctime = wpoint.time
        self._considered.insert(0, wpoint)
        # cap considered stack
        del self._considered[20:]

        first = time.time()

        if force:
            self._addpoint(wpoint)
            return

        for check in self._considered[1:]:
            if document == check.document:
                if check.line < line + self.threshold  and \
                   check.line > line - self.threshold and \
                   check.time + self.timespan  <= ctime:
                    fuzz = self.get_fuzzy(wpoint)
                    if fuzz:
                        # we update the line of the fuzzy match so
                        # have the point near bye when jumping back
                        fuzz.line = line
                    else:
                        self._addpoint(wpoint)
                        del self._considered[:]
            elif self.docswitch and document != check.document:
                # if the document changes, we don't need checking anymore
                self._addpoint(wpoint)
                del self._considered[:]
            else:
                break

    def _addpoint(self, point):
        #if self.current_point:
        #    cpoint = self.index(self.current_point)
        #    if cpoint:
        #        # delete all entries befor the current_point
        #        del self[0:cpoint]
        self.insert(0, point)
        self.current_point = point
        del self[self.max_length:]
        #self._last_line = line
        #self._last_document = document

        #self._last_document = document
        #self._last_line = line

    def __contains__(self, element):
        if not isinstance(element, WayPoint):
            return list.__contains__(element)
        for i in self:
            if element.line == i.line and element.document == i.document:
                return True
        return False


    def has_fuzzy(self, element):
        """
        Tests if a element of roughly the props is in the stack
        """
        if not isinstance(element, WayPoint):
            return list.__contains__(element)
        for i in self:
            if element.document == i.document and \
               (i.line - self.threshold) < element.line and \
               (i.line + self.threshold) > element.line:
                return True
        return False

    def get_fuzzy(self, document, line=0):
        """
        Returns the first fuzzy matched element from the Stack
        """
        if isinstance(document, WayPoint):
            line = document.line
            document = document.document
        
        best = None
        for i in self:
            if document == i.document and \
               (i.line - self.threshold) < line and \
               (i.line + self.threshold) > line:
                # we can simply return the exact match
                if i.line == line:
                    return i
                if not best or abs(best.line - line) > abs(i.line - line):
                    best = i
        return best


    def clear(self):
        """
        Clear the WayStack list
        """
        del self[:]
        self.current_point = None
        self._last_document = None
        self._last_line = None

    def jump(self, steps):
        """
        Jumps n steps forward or backward in history and returns the WayPoint.
        
        If steps would break the Borders of the Path, min or max point is 
        returned.
        """
        if not len(self):
            return
        try:
            nindex = min(max(self.index(self.current_point)+steps, 0), len(self)-1)
        except (IndexError, ValueError):
            # the current waypoint was deleted for example
            nindex = 0
        self.current_point = self[nindex]
        self._last_line = self.current_point.line
        self._last_document = self.current_point.document
        return self.current_point

    def remove_waypoint(self, document, line):
        best = self.get_fuzzy(document, line)
        if best and line == best.line:
            self.remove(best)
            if self.current_point == best:
                self.current_point = len(self) and self[0] or None

    def remove_waypoints_of_document(self, document):
        rmlst = []

        for i in self:
            if i.document == document:
                rmlst.append(i)
        for i in rmlst:
            self.remove(i)

        if self.current_point in rmlst:
            self.current_point = None



class WaypointEventsConfig(EventsConfig):
    def subscribe_all_foreign(self):
        self.subscribe_foreign('buffer', 'document-changed',
                    self.on_document_changed)
        self.subscribe_foreign('buffer', 'document-closed',
                    self.on_document_closed)
        self.subscribe_foreign('buffer', 'document-goto',
                    self.on_document_goto)

    def on_document_changed(self, document):
        self.svc.notify_change(document,
                               self.svc.boss.editor.get_current_line())

    def on_document_goto(self, document, line):
        self.svc.notify_change(document, line)

    def on_document_closed(self, document):
        if self.svc.opt('rm_on_close'):
            self.svc.remove_waypoints_of_document(document)

class WaypointFeaturesConfig(FeaturesConfig):

    def subscribe_all_foreign(self):
        pass


class WaypointOptionsConfig(OptionsConfig):

    def create_options(self):
        self.create_option(
            'timespan',
            _('Timespan'),
            int,
            8,
            _('After how man seconds a groups of lines (in the threshold) '
              'is considered a waypoint'),
            self.on_update
        )

        self.create_option(
            'threshold',
            _('Threshold'),
            int,
            30,
            _('After how many lines set a new waypoint'),
            self.on_update
        )

        self.create_option(
            'docswitch',
            _('Waypoint on document change'),
            bool,
            False,
            _('Should a new waypoint be generated if the document switches'),
            self.on_update
        )

        self.create_option(
            'max_entries',
            _('Max Entries'),
            int,
            30,
            _('Who many entries to have'),
            self.on_update
        )

        self.create_option(
            'rm_on_close',
            _('Remove on close'),
            bool,
            True,
            _('Remove entries when a document is closed')
        )

    def on_update(self, *args):
        self.svc.update_stack()


class WaypointCommandsConfig(CommandsConfig):

    def notifiy_change(self, document=None, line=None):
        if document is not None and line is not None:
            self.svc.notifiy_change(document, line)


class BufferDbusConfig(DbusConfig):
    
    @LEXPORT(in_signature='ii')
    def notifiy_change(self, document_id, line):
        doc = self.boss.cmd('buffer', 'get_document_by_id', 
                            document_id=document_id)
        if doc and line:
            self.svc.notifiy_change(doc, line)

class WaypointActionsConfig(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'clear_waypoints',
            TYPE_NORMAL,
            _('Clear Waypoints'),
            _('Clear your waypoint list'),
            gtk.STOCK_CLEAR,
            self.on_clear_waypoints,
        )
        self.create_action(
            'WaypointMenu',
            TYPE_MENUTOOL,
            _('Waypoint_s'),
            _('Show Waypoint List'),
            '',
            self.on_menu,
        )

        self.create_action(
            'force_waypoint',
            TYPE_NORMAL,
            _('Add Waypoint'),
            _('Forces a new Waypoint'),
            '',
            self.on_force_waypoint,
            ''
        )

        self.create_action(
            'remove_waypoint',
            TYPE_NORMAL,
            _('Remove Waypoint'),
            _('Remove current waypoint'),
            '',
            self.on_remove_waypoint,
            ''
        )

        self.create_action(
            'jump_waypoint_back',
            TYPE_NORMAL,
            _('Jump Waypoint Back'),
            _('Jump next waypoint back'),
            '',
            self.on_jump_back,
            '<Shift><Control>Up'
        )

        self.create_action(
            'jump_waypoint_forward',
            TYPE_NORMAL,
            _('Jump Waypoint Forward'),
            _('Jump next waypoint forward'),
            '',
            self.on_jump_next,
            '<Shift><Control>Down'
        )

    def on_jump_back(self, action):
        self.svc.jump(1)

    def on_jump_next(self, action):
        self.svc.jump(-1)

    def on_clear_waypoints(self, action):
        #self.svc.execute_current_document()
        self.svc._stack.clear()

    def on_force_waypoint(self, action):
        self.svc.notify_change(None, None, force=True)

    def on_remove_waypoint(self, action):
        document = self.svc.boss.cmd('buffer', 'get_current')
        line = self.svc.boss.editor.get_current_line()
        if document and line:
            self.svc.remove_waypoint(document, line)

    def on_menu(self, action):
        self.svc.create_waypoint_menu()


class Waypoint(Service):

    features_config = WaypointFeaturesConfig
    actions_config = WaypointActionsConfig
    options_config = WaypointOptionsConfig
    events_config = WaypointEventsConfig
    commands_config = WaypointCommandsConfig

    def pre_start(self):
        self._stack = WayStack(self.opt('threshold'), self.opt('max_entries'),
                               self.opt('timespan'), self.opt('docswitch'))

    def update_stack(self):
        """
        Update the stack to reflect new preferences
        """
        self._stack.threshold = self.opt('threshold')
        self._stack.max_length = self.opt('max_entries')
        self._stack.timespan = self.opt('timespan')
        self._stack.docswitch = self.opt('docswitch')

    def remove_waypoint(self, document, line, fuzzy=False):
        self._stack.remove_waypoint(document, line)

    def remove_waypoints_of_document(self, document):
        self._stack.remove_waypoints_of_document(document)


    def notify_change(self, document, line, force=False):
        """Notify of a document, and line number change"""

        if document is None:
            document = self.boss.cmd('buffer', 'get_current')
            line = self.boss.editor.get_current_line()
            if not document or not line:
                return

        if not isinstance(document, Document):
            import traceback
            print "Not a document"
            traceback.print_stack()
            return
        if not line:
            line = 1
        self._stack.notify_change(document, line, force=force)

    def jump(self, steps):
        """
        jump n positions in the stack
        """
        npoint = self._stack.jump(steps)
        self.boss.cmd('buffer', 'open_file', 
                          document=npoint.document, line=npoint.line)

    def _update_waypoints(self):
        self.notify_change(None, None)
        return True

    def start(self):
        self._window_list_id = self.boss.window.create_merge_id()
        self._action_group = gtk.ActionGroup('window_list')
        self.boss.window._uim._uim.insert_action_group(self._action_group, -1)
        self._timeout = gobject.timeout_add(2000, self._update_waypoints)

    def stop(self):
        self.boss.window._uim._uim.remove_action_group(self._action_group)
        if self._timeout:
            gobject.source_remove(self._timeout)

    def _on_waypoint(self, action, waypoint):
        self.boss.get_service('buffer').view_document(
                                document=waypoint.document,
                                line=waypoint.line)

    def create_waypoint_menu(self):
        # update the window menu list
        # clean up the old list
        self.boss.window.remove_uidef(self._window_list_id)
        for action in self._action_group.list_actions():
            self._action_group.remove_action(action)

        i = 0
        # add panels to list. they are sorted after the paned positions and
        # therefor good
        for wpoint in self._stack:
            action_name = "go_waypoint_%s" %i
            title = u"%s   %s" %(unicode(wpoint.document), wpoint.line)
            act = gtk.Action(action_name,
                title,
                '',
                '')
            act.connect('activate', self._on_waypoint, wpoint)
            self._action_group.add_action(act)
            self.boss.window._uim._uim.add_ui(
                self._window_list_id,
                "ui/menubar/AddMenu/WaypointMenu/waypoint_list", 
                title, 
                action_name, 
                gtk.UI_MANAGER_MENUITEM, 
                False)            #mi = act.create_menu_item()
            i += 1
        return None

# Required Service attribute for service loading
Service = Waypoint



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
