

" Asynchronous PIDA events
:silent function! Async_event(...)
    let client = '"'.expand('<client>').'"'
    let server = v:servername
    let command_args = '"'.v:servername.':'.join(a:000, "").'"'
    let command_start = "silent call server2client("
    let command_end = ")"
    let command = command_start.client.",".command_args.command_end
    try
        exec command
    catch /.*/
        echo command
    endtry
:endfunction

:silent function! Pida_Started()
    silent call Async_event("filesave")
    echo "PIDA connected"
:endfunction

:silent sign define break text=!B
:silent augroup pida
:silent set guioptions-=T
:silent set guioptions-=m
:silent au! pida
:silent au pida BufEnter * silent call Async_event("bufferchange", getcwd(), bufname('%'), bufnr('%'))
:silent au pida BufDelete * silent call Async_event("bufferunload", expand('<amatch>'))
:silent au pida VimLeave * silent call Async_event("shutdown")
:silent au pida VimEnter * silent call Pida_Started()
:silent au pida BufWritePost * silent call Async_event("filesave")
:silent au pida CursorMovedI * silent call Async_event("cursor_move", line('.'))
:silent au pida CursorMoved * silent call Async_event("cursor_move", line('.'))

:silent function! Pida_Complete2(findstart, base)
    " locate the start of the word
    let line = getline('.')
    let start = col('.') - 1
    while start > 0 && line[start - 1] =~ '\a'
        let start -= 1
    endwhile
    if a:findstart
        let g:completing = 1
	    return start
    else
        silent! call Async_event(v:servername.":complete".a:findstart."".a:base."".line."".start)
        let completion_time = 0
        while g:completing && completion_time < 500
            sleep 100m
            let completion_time = completion_time + 100
            "if complete_check()
            "    break
            "endif
        endwhile
        return []
    endif
:endfunction

:silent function! Pida_Complete(findstart, base)
    " locate the start of the word
    let line = getline('.')
    let start = col('.') - 1
    while start > 0 && line[start - 1] =~ '\a'
        let start -= 1
    endwhile
    if a:findstart
        let g:completing = 1
	    return start
    else
        let buffer_lines = getline(1, '$')
        let tempfile = tempname()
        call writefile(buffer_lines, tempfile)
        let buffer_offset = line2byte('.') + col('.') - 1
        call Async_event(v:servername.":complete".a:findstart."".a:base."".line."".start."".tempfile."".buffer_offset)
        let completion_time = 0
        while g:completing && completion_time < 500
            sleep 100m
            let completion_time = completion_time + 100
            "if complete_check()
            "    break
            "endif
        endwhile
        return []
    endif
:endfunction

:silent function! Pida_Stop_Completing()
    let g:completing = 1
:endfunction
set completefunc=Pida_Complete

:function InsertTabWrapper()
      let col = col('.') - 1
      if !col || getline('.')[col - 1] !~ '\k'
          return "\<tab>"
      else
          return "\<c-p>"
      endif
:endfunction


"""""""""""""""""""""""""""""""""
" Depracated things

" depracated
:silent function! Bufferlist()
let i = 1
    let max = bufnr('$') + 1
    let lis = ""
    while i < max
        if bufexists(i)
            let lis = lis.";".i.":".bufname(i)
        endif
        let i = i + 1
    endwhile
    return lis
:endfunction

" depracated
:silent function! BreakPoint(l)
    call Async_event(v:servername.":set_breakpoint,".a:l)
:endfunction

" depracated
:silent function! Yank_visual()
    y
    return @"
:endfunction

"""""""""""""""""""""""""""""""""
