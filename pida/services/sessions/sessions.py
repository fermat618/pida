# -*- coding: utf-8 -*- 

# Copyright (c) 2007 The PIDA Project

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

import os
import gtk
import gobject

from configobj import ConfigObj
from tempfile import mkstemp

# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE

from pida.ui.views import PidaGladeView


class SessionObject(object):
    """
    Represents a session

    name - the name of the session
    files - a list of files to open into the buffers
    project - the currently opened project
    path - the path to the session file

    """

    def new(self, session_path, files, project=None):
        """
        create a new session
        """
        self.name, self._path = self._parse_session_path(session_path)
        self._files = files
#        self._project = project
        self._config = ConfigObj()
        self._config.filename = self._path

    def save(self):
        """
        write this session out to a file
        """
        self._config['name'] = self.name
        self._config['files'] = self._files
#        self._config['project'] = self._project
        self._config.write()
    
    def load(self, session_path):
        """
        load a session file
        """
        self._path = session_path
        self._config = ConfigObj(self._path)
        self.name = self._config['name']
        self._files = self._config['files']
#        self._project = self._config['project']

    def _parse_session_path(self, path):
        base_name = os.path.basename(path).split(".")
        name = base_name[0]
        ext = base_name[-1]
        if ext != "session":
            path = path + ".session"
        return (name, path,)
        
    def get_files(self):
        return self._files

    def set_files(self, files):
        self._files = files


class SessionsActionsConfig(ActionsConfig):
    def create_actions(self):
        self.create_action(
            'load_session',
            TYPE_NORMAL,
            'Load Session',
            'Load a saved session',
            None,
            self.on_load_session,
            ''
        )

        self.create_action(
            'save_session',
            TYPE_NORMAL,
            'Save Session',
            'Save your current session',
            None,
            self.on_save_session,
            ''
        )

    def on_load_session(self, action):
        file_name = self.svc.boss.window.open_dlg(folder = self.svc.sessions_dir)
        self.svc.load_session(file_name)

    def on_save_session(self, action):
        if self.svc.current_session:
            name = self.svc.current_session.name + ".session" 
            file_path = self.svc.boss.window.save_dlg(current_name = name, folder = self.svc.sessions_dir) 
        else:
            file_path = self.svc.boss.window.save_dlg(folder = self.svc.sessions_dir)

        self.svc.save_current_session(file_path)
        return

class SessionsPropertyView(PidaGladeView):

    gladefile = 'sessions-properties'
    label_text = 'Sessions Properties'
    icon_name = 'package_utilities'

    def create_ui(self):
        pass



class Sessions(Service):
    """
    Store opened buffers for later use.

    Session is a tool to save and restore the state of pida at any given
    point in time. This should include 1) opened buffers, 2) FileManager
    locations, possibly more.

    should allow for multiple sessions to be saved and restored
    always save the last session

    get the buffer service
    buffer = boss.get_service('buffer')
    get the list of buffers
    # added this function to the buffer service
    current_buffers = buffer.get_documents()
    files = [buffer.filename for buffer in current_buffers]
    """
    # TODO - Make Sessions align with Pida style guide
    # TODO - Create the Pida Prefrences Gui
    # TODO - Save the last session on close
    # TODO - Allow restoring of last session on startup


    actions_config = SessionsActionsConfig

    def pre_start(self):
        self.sessions_dir = os.path.join(self.boss.get_pida_home(), 'sessions')
        if not os.path.exists(self.sessions_dir):
            os.mkdir(sessions_dir)
        self.current_session = None

    def load_session(self, file_path):
        """
        load the saved session file from disk
        """
        self.current_session = SessionObject()
        self.current_session.load(file_path)
        self.load_buffers(self.current_session.get_files())

    def save_current_session(self, file_path):
        if not self.current_session:
            self.current_session = SessionObject()
            self.current_session.new(file_path, files = self._get_current_bufferes())
        else:
            self.current_session.set_files(self._get_current_buffers())
        self.current_session.save()

    def _get_current_buffers(self):
        """
        retrieve the list of currently opened buffers from the buffer manager.
        """
        documents = self.boss.cmd('buffer', 'get_documents')
        files = []
        for buffer, file in documents.iteritems():
            files.append(file.filename)
        return files

    def load_buffers(self, files):
        """
        load each file in self.buffers into the buffer manager
        """
        if len(files):
            self.boss.cmd('buffer', 'open_file', file_name=files.pop())
        else:
            return
        gobject.timeout_add(1000, self.load_buffers, files)

# Required Service attribute for service loading
Service = Sessions


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
