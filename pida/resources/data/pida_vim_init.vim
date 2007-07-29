
""""""""""""""""""""""""""""""""""""""""
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

""""""""""""""""""""""""""""""""""""""""
" PIDA Auto commands

:silent augroup pida
:silent au! pida
:silent au pida BufEnter * silent call Async_event("bufferchange", getcwd(), bufname('%'), bufnr('%'))
:silent au pida BufDelete * silent call Async_event("bufferunload", expand('<amatch>'))
:silent au pida VimLeave * silent call Async_event("shutdown", "")
:silent au pida VimEnter * silent call Pida_Started()
:silent au pida BufWritePost * silent call Async_event("filesave", "")
:silent au pida CursorMovedI * silent call Async_event("cursor_move", line('.'))
:silent au pida CursorMoved * silent call Async_event("cursor_move", line('.'))

"""""""""""""""""""""""""""""""""
" Completion
"

silent function! Find_Start()
    let line = getline('.')
    let idx = col('.')
    while idx > 0
        let idx -= 1
        let c = line[idx]
        "if c =~ '\w'
        "    continue
        if ! c =~ '\.'
            let idx = -1
            break
        else
            break
        endif
    endwhile
    return idx
endfunction


:silent function! Pida_Complete(findstart, base)
    " locate the start of the word
    let start_idx = Find_Start()
    if a:findstart
	    return start_idx
    else
        let buffer_lines = getline(1, '$')
        let tempfile = tempname()
        call writefile(buffer_lines, tempfile)
        let buffer_offset = line2byte('.') + col('.') - 1
        call Async_event("complete", tempfile, buffer_offset)
        let completion_time = 0
        while completion_time < 500
            sleep 100m
            let completion_time = completion_time + 100
            if complete_check()
                break
            endif
        endwhile
        return []
    endif
:endfunction

:silent function! Pida_Stop_Completing()
    let g:completing = 1
:endfunction
set completefunc=Pida_Complete

:function InsertTabWrapper()
    echo pumvisible()
    let col = col('.') - 1
    if pumvisible()
        return "\<C-N>"
    elseif !col || getline('.')[col - 1] !~ '\.'
        return "\<tab>"
    else
        return "\<C-X>\<C-U>"
    endif
:endfunction

inoremap <silent><tab> <c-r>=InsertTabWrapper()<cr>
inoremap <expr> <Esc> pumvisible()?"\<C-E>":"\<Esc>"

"""""""""""""""""""""""""""""""""
" Some basic options
:silent set guioptions-=T
:silent set guioptions-=m

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
