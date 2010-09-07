
" Vim Remote Communication
" Requires +python PyGTK and Python DBUS

set nocompatible

silent function! VimSignal(name, ...)
    python getattr(service, vim.eval('a:name'))(*clean_signal_args(vim.eval('a:000')))
endfunction


python << endpython
# Do this before we even breath
import vim

import os
import sys
# just in case, our pida might not be in the default path
path = os.environ['PIDA_BASE']
sys.path.insert(0, path)

from pida.editors.vim.server import VimDBUSService, get_offset, clean_signal_args
from pida.utils.pdbus import PidaRemote

uid = os.environ['PIDA_DBUS_UUID']
service = VimDBUSService(uid)
client = PidaRemote(uid)

endpython



" Now the vim events
silent augroup VimCommsDBus
silent au! VimCommsDBus
silent au VimCommsDBus BufEnter * silent call VimSignal('BufEnter', expand('<abuf>'), expand('<amatch>'))
silent au VimCommsDBus BufNew * silent call VimSignal('BufNew', expand('<abuf>'))
silent au VimCommsDBus BufNewFile * silent call VimSignal('BufNewFile', expand('<abuf>'))

silent au VimCommsDBus BufReadPre * silent call VimSignal('BufReadPre', expand('<abuf>'))
silent au VimCommsDBus BufReadPost * silent call VimSignal('BufReadPost', expand('<abuf>'))

silent au VimCommsDBus BufWritePre * silent call VimSignal('BufWritePre', expand('<abuf>'))
silent au VimCommsDBus BufWritePost * silent call VimSignal('BufWritePost', expand('<abuf>'))

silent au VimCommsDBus BufAdd * silent call VimSignal('BufAdd', expand('<abuf>'))
silent au VimCommsDBus BufDelete * silent call VimSignal('BufDelete', expand('<abuf>'))
silent au VimCommsDBus BufUnload * silent call VimSignal('BufUnload', expand('<abuf>'))
silent au VimCommsDBus BufUnload * silent call VimSignal('BufHidden', expand('<abuf>'))
silent au VimCommsDBus BufWipeout * silent call VimSignal('BufWipeout', expand('<abuf>'))

silent au VimCommsDBus VimLeave * silent call VimSignal('VimLeave')
silent au VimCommsDBus VimEnter * silent call VimSignal('VimEnter')
silent au VimCommsDBus CursorMovedI,CursorMoved * silent call VimSignal('CursorMoved')
silent au VimCommsDBus SwapExists * let v:swapchoice='d'

set hidden

" Some UI Stuffs
set nomore
set guioptions-=T
set guioptions-=m
set guioptions+=c


