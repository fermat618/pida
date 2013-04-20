#!/usr/bin/python

import re
import vim


def vim_quote(s):
    """
    quote python objects as vim string

    used in `:echo %s` and `:call foo(%s)`
    """

    table = dict()

    def add_to_table(t):
        def result(fun):
            table[t] = fun
            return fun
        return result

    @add_to_table(str)
    def quote_str(s):
        d = {
                "\n": r"\n",
                "\\": r"\\",
                "\"": r"\""
                }
        p = r'\n|\\|"'
        return '"' + re.sub(p, lambda x: d[x.group(0)], s) + '"'

    @add_to_table(int)
    def quote_int(s):
        return str(s)

    @add_to_table(bool)
    def quote_bool(s):
        return '1' if s else '0'

    @add_to_table(float)
    def quote_float(s):
        return str(s)

    @add_to_table(list)
    def quote_list(s):
        return "[" + ', '.join(map(vim_quote, s)) + "]"

    @add_to_table(dict)
    def quote_dict(s):
        return "{" + ', '.join(map(
            lambda w: vim_quote(w[0]) + ': ' + vim_quote(w[1]),
            s.items())) + "}"

    def quote_error(s):
        raise TypeError("vim_quote(): Don't know how to quote type {}.".format(type(s)))

    return table.get(type(s), quote_error)(s)


def vim_call(*args):
    def pairit(it):
        return '(' + ', '.join(map(vim_quote, it)) + ')'
    return vim.eval(args[0] + pairit(args[1:]))


def vim_fnameescape(s):
    """
    escape string in vim command

    used in `:edit %s`

    ref: vim document :help fnameescape()

    escape following characters

    " \t\n*?[{`$\\%#'\"|!<"

    and leading '+', '>'
    """
    mid_d = {c: '\\' + c for c in ''' *?[{`$%#'|!<\t\n\\\"'''}
    start_d = {c: '\\' + c for c in '+>'}
    start_d.update(mid_d)
    return start_d.get(s[0], s[0]) + ''.join(mid_d.get(c, c) for c in s[1:])


def vim_cmd_with_esc(fmt, *args, **kwargs):
    args = [vim_fnameescape(str(x)) for x in args]
    kwargs = {key: vim_fnameescape(str(val)) for (key, val) in kwargs.items()}
    vim.command(fmt.format(*args, **kwargs))
