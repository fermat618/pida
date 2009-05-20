# -*- coding: utf-8 -*- 

# Copyright (c) 2009 The PIDA Project

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




# PIDA Imports
from pida.core.service import Service
from pida.core.features import FeaturesConfig
from pida.core.commands import CommandsConfig
from pida.core.events import EventsConfig
from pida.core.actions import ActionsConfig
from pida.core.options import OptionsConfig
from pida.core.actions import TYPE_NORMAL, TYPE_MENUTOOL, TYPE_RADIO, TYPE_TOGGLE, TYPE_REMEMBER_TOGGLE

from pida.ui.views import PidaGladeView
from regextoolkitlib import *
import gtk
import gobject

# locale
from pida.core.locale import Locale
locale = Locale('regextoolkit')
_ = locale.gettext


class RegextoolkitView(PidaGladeView):
    key="gregextoolkitwindow.form"
    gladefile="gregextoolkitwindow"
    locale = locale
    label_text = _('RegexToolkit')
    #icon_name = 'search'
    running = False

    def create_ui(self):
        #self.gregextoolkitwindow.show()
        
        self.btnRegexLib.set_sensitive(False)
        self.flags=0
        self.flagsdict={}
        self.chks=[self.chkMULTILINE, self.chkVERBOSE, self.chkDOTALL, self.chkIGNORECASE, self.chkLOCALE, self.chkUNICODE]
        
        
        for chk in self.chks:
            self.flagsdict[chk.get_label()]=True

    def get_dialog(self):
        return self.regextoolkitdialog
    def update_flags(self):
        for k, v in self.flagsdict.items():
            if not v:
                del self.flagsdict[k]
                
        self.flags=flags_from_dict(self.flagsdict) if self.flagsdict else 0
        print self.flags
        
    def get_text_from_buffer(self, buffer):
        siter=buffer.get_start_iter()
        eiter=buffer.get_end_iter()
        return buffer.get_text(siter, eiter)
        
    def on_btnExecute_clicked(self, widget, *args):

        regex, inp=self.get_text_from_buffer(self.txtRegex.get_buffer()), self.get_text_from_buffer(self.txtInput.get_buffer())
        if match(regex, inp):
            self.statusbar.push(1, "[+]MATCH")
        else:
            self.statusbar.push(1, "[-]NO MATCH")
            return
        #(?P<name>\w+?)(?P<num>\d+)
        namedgroups=capture_named_groups(match(regex, inp))
        if namedgroups:
            self._prep_tv_for_named_groups(namedgroups)
        else:
            groups=capture_groups(match(regex, inp))
            if groups:
                self._prep_tv_for_anonymouse_groups(groups)
            
    def _prep_tv_for_named_groups(self, namedgroups):
        self._remove_columns()
        lstore=gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING) #id, name, match 
    
        for i, gname in enumerate(namedgroups.keys()):
            iter=lstore.append([str(i), gname, namedgroups[gname]])
    
        #return lstore
        idcell=gtk.CellRendererText()
        idcol=gtk.TreeViewColumn("#", idcell, text=0)
    
    
        namecell=gtk.CellRendererText()
        namecol=gtk.TreeViewColumn("Name", namecell, text=1)
    
        matchcell=gtk.CellRendererText()
        matchcol=gtk.TreeViewColumn("Match", matchcell, text=2)
    
        map(self.tvResult.append_column,[idcol, namecol, matchcol])
        self.tvResult.set_model(lstore)
        
    
    def _prep_tv_for_anonymouse_groups(self, groups):
        self._remove_columns()
        lstore=gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
    
        for i, group in enumerate(groups):
            iter=lstore.append([str(i), group])

        #return lstore
        idcell=gtk.CellRendererText()
        idcol=gtk.TreeViewColumn("#", idcell, text=0)
        groupcell=gtk.CellRendererText()
        groupcol=gtk.TreeViewColumn("Match", groupcell, text=1)
        map(self.tvResult.append_column,[idcol, groupcol])
        
        self.tvResult.set_model(lstore)
        
    def on_chk_toggled(self, widget, *args):
        if widget.get_active():
            print widget.get_label() + " is checked.."
            self.flagsdict[widget.get_label()]=True
        else:
            self.flagsdict[widget.get_label()]=False
        self.update_flags()

    
    def _remove_columns(self):
        colslist=self.tvResult.get_columns()
        map(self.tvResult.remove_column, colslist)


    def on_btnRegexLib_clicked(self, widget, *args):
        pass


class RegextoolkitActions(ActionsConfig):

    def create_actions(self):
        self.create_action(
            'show_regextoolkit',
            TYPE_REMEMBER_TOGGLE,
            _('RegexToolkit'),
            _('Show regextoolkit'),
            '',
            self.on_show_regextoolkit,
            '',
        )

    def on_show_regextoolkit(self, action):
        if action.get_active():
            self.svc.show_regextoolkit()
        else:
            self.svc.hide_regextoolkit()
            
class RegextoolkitOptions(OptionsConfig):

    pass

# Service class
class Regextoolkit(Service):
    """Describe your Service Here""" 
    actions_config = RegextoolkitActions
    #options_config = RegextoolkitOptions 
    
    def pre_start(self):
        self._view=RegextoolkitView(self)
        
    def start(self):

        acts = self.boss.get_service('window').actions
        #acts.register_window(self._view.key, self._view.label_text)
    
    def show_regextoolkit(self):
        self.boss.cmd('window', 'add_view', paned='Plugin', view=self._view)
        
    def hide_regextoolkit(self):
        self.boss.cmd('window', 'remove_view', view=self._view)
        
# Required Service attribute for service loading
Service = Regextoolkit



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
