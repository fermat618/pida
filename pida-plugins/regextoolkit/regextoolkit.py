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
from regextoolkitlib import flags_from_dict, all_matches, capture_groups
import re
import gtk
import gobject
import pango
import itertools

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
            
        #FIXME: coloring: humm, totally messed with various styles <what should we do?>    
        self.txtInput.get_buffer().create_tag("red_fg", foreground="red") #,size=15*pango.SCALE)
        self.txtInput.get_buffer().create_tag("blue_fg", foreground="blue") #,  size=15*pango.SCALE)
        self.txtInput.get_buffer().create_tag("green_fg", foreground="green") #, size=15*pango.SCALE)
        self.txtInput.get_buffer().create_tag("darkred_bg", foreground="#BB0A0A") #, size=15*pango.SCALE )
        self.txtInput.get_buffer().create_tag("lightbr_fg", foreground="#DBD39C") #, size=15*pango.SCALE )
        self.txtInput.get_buffer().create_tag("vi_fg", foreground="#5F4E84") #, size=15*pango.SCALE )
        
        self.buf_tags=["red_fg", "blue_fg", "green_fg", "lightbr_fg", "vi_fg", "darkred_fg"]
        
        #TreeView columns.
        midcell=gtk.CellRendererText()
        midcol=gtk.TreeViewColumn("#mid", midcell, text=0)
        self.tvResult.append_column(midcol)
        
        
    def update_flags(self):
        for k, v in self.flagsdict.items():
            if not v:
                del self.flagsdict[k]
                
        self.flags=flags_from_dict(self.flagsdict) if self.flagsdict else 0
        #print self.flags
    def get_text_from_buffer(self, buffer):
        siter=buffer.get_start_iter()
        eiter=buffer.get_end_iter()
        return buffer.get_text(siter, eiter)

    def highlightmatch(self, ms):

        buf = self.txtInput.get_buffer()
        buf.remove_all_tags(buf.get_start_iter(), buf.get_end_iter())
        tagscycle=itertools.cycle(self.buf_tags)
        for m in ms:
            for idx in range(len(m.groups())):
                pos = idx+1
                tag = idx%len(self.buf_tags)

                istart=buf.get_iter_at_offset(m.start(pos))
                iend=buf.get_iter_at_offset(m.end(pos))
                buf.apply_tag_by_name(tagscycle.next(), istart, iend)

    def on_btnExecute_clicked(self, widget, *args):

        regex = self.get_text_from_buffer(self.txtRegex.get_buffer())
        inp = self.get_text_from_buffer(self.txtInput.get_buffer())
       
        ms=all_matches(regex, inp)
        if len(ms): 
            self.statusbar.push(1, "[+]MATCH")
            self._prep_tv_for_matches(ms)
            self.highlightmatch(ms)
        else:
            self.statusbar.push(1, "[-]NO MATCH")
            self.tvResult.set_model(None) #remove the model

    def _prep_tv_for_matches(self, ms):
        #self._remove_columns()
        reg=re.compile(self.get_text_from_buffer(self.txtRegex.get_buffer()))
        namedgroupsdict={}
        #print "REG GIDX: ", reg.groupindex
        for gname, idx  in reg.groupindex.items():
            namedgroupsdict[idx]=gname
        #tstore=gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING) #mid, gid, name, match 
        tstore=gtk.TreeStore(gobject.TYPE_STRING)
        miter = tstore.get_iter_first()
        for mid, m in enumerate(ms):

            miter=tstore.append(None, ["Match#"+str(mid)])

            #citer = tstore.iter_children(miter)
            groups=capture_groups(m)
            #for gi, gval in enumerate(groups):(?P<name>\w+?)(\d+)
            #interested in first match...
            for gi in range(len(groups)+1):
                gval=m.group(gi)
                tstore.append(miter, ["%d: %s (%s)"%(gi , gval, namedgroupsdict.get(gi, "Anonymouse") )])


        self.tvResult.set_model(tstore)

    def on_chk_toggled(self, widget, *args):
        self.flagsdict[widget.get_label().upper()]=widget.get_active()
        self.update_flags()

    def _remove_columns(self):
        colslist=self.tvResult.get_columns()
        map(self.tvResult.remove_column, colslist)

    def on_btnRegexLib_clicked(self, widget, *args):
        pass

    def remove_columns(self):
        colslist=self.tvResult.get_columns()
        map(self.tvResult.remove_column, colslist)


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
