# -*- coding: utf-8 -*- 
from mock import Mock
from .pastebin import PastebinEditorView, PasteHistoryView, pastebin_types
from .pastebin import LodgeIt

from pygtkhelpers.utils import refresh_gui

def test_paste_view():
    mock = Mock(name='svc')
    mock.get_pastebin_types.return_value = pastebin_types
    view = PastebinEditorView(mock)

    view.paste_proxy.update(LodgeIt)
    #XXX: more
    refresh_gui()

def test_hist_view():
    view = PasteHistoryView(Mock())
    #XXX: more



# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
